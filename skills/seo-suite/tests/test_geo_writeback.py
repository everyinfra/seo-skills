#!/usr/bin/env python3
"""citation_panel.py geo 打分写回测试: score 子命令(geo-scoring-rubric 五维打分卡)/
校验器硬规则(3 条硬 cap、枚举、top_pick 佐证降级、字段白名单、越界 clamp)/
report geo 聚合(按引擎分列 + presence 计数 + 分布档 + 反通胀提示行)/ 旧数据兼容
(无 geo 键面板照常;diff 不因 geo 键变化触发信号)。
standalone(自带 run_script 助手,合成 panel.json 数据,零网络):
python3 tests/test_geo_writeback.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

scores.json 形态: {prompt: {geo_score, presence, position, sentiment,
recommendation, competitors[], risks[]}}(references/content/geo-scoring-rubric.md
十一节 schema;geo_score=null 表示缺席不打分)。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import citation_panel as cp  # noqa: E402  (需先入 SCRIPTS 路径)

R1 = "chatgpt-2026-10-01"
R2 = "perplexity-2026-10-02"


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def res(mentioned=0, cited=0, urls=(), state=None, rank=None, geo=None):
    """与 normalize_result 同构的最小 cell 结果(geo 为写回后的扩展键)。"""
    if state is None:
        state = "cited_brand" if cited else ("name_only_mention" if mentioned else "brand_absent")
    r = {"state": state, "mentioned": mentioned, "cited": cited, "cited_urls": list(urls)}
    if rank is not None:
        r["rank"] = rank
    if geo is not None:
        r["geo"] = geo
    return r


def setup_panel(tmp, runs_spec):
    """runs_spec=[(run_id, engine, date, {prompt: res})] → 写 panel.json + runs/*.json
    (与 record 的双写布局一致, score 直接在该布局上回写)。"""
    runs = [{"run_id": rid, "engine": eng, "date": date, "brand": "Acme", "results": results}
            for rid, eng, date, results in runs_spec]
    panel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
             "prompts": sorted({p for _, _, _, rs in runs_spec for p in rs}),
             "engines": sorted({eng for _, eng, _, _ in runs_spec}),
             "created": "2026-10-01T00:00:00", "runs": runs}
    path = os.path.join(tmp, "panel.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel, f, ensure_ascii=False)
    rdir = os.path.join(tmp, "runs")
    os.makedirs(rdir, exist_ok=True)
    for r in runs:
        with open(os.path.join(rdir, r["run_id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False)
    return path


def write_scores(tmp, name, scores):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False)
    return path


def two_run_panel(tmp):
    """标准两 run 两引擎面板: R1(chatgpt, p1 被引/p2 仅提及/p3 未提)、
    R2(perplexity, p1 仅提及/p2 被引)。"""
    return setup_panel(tmp, [
        (R1, "chatgpt", "2026-10-01T00:00:00", {
            "p1": res(1, 1, ["https://acme.ai/guide"]),
            "p2": res(1, 0),
            "p3": res(0, 0)}),
        (R2, "perplexity", "2026-10-02T00:00:00", {
            "p1": res(1, 0),
            "p2": res(1, 1, ["https://acme.ai/x"])})])


def load_panel(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ScoreWritebackTests(unittest.TestCase):
    """score 子命令: --run/--last 定位、双写(panel.json + runs/<id>.json)、原子拒绝。"""

    def test_writeback_by_runid_and_last(self):
        """--run 精确写回目标 run(含 schema 全字段/缺省字段/null 缺席),
        run 文件双写,采集层键原样保留;--last 命中最近一条 run。"""
        tmp = tempfile.mkdtemp(prefix="geo_wb_")
        path = two_run_panel(tmp)
        scores = write_scores(tmp, "scores.json", {
            "p1": {"geo_score": 80, "presence": "cited_brand", "sentiment": 85,
                   "position": {"absolute_rank": 1, "mentions": 5,
                                "first_occurrence_pct": 5},
                   "recommendation": "top_pick",
                   "competitors": [{"brand": "HubSpot", "absolute_rank": 2,
                                    "mentions": 4, "sentiment": 80}],
                   "risks": []},
            "p2": {"geo_score": 45, "presence": "name_only_mention",
                   "position": {"absolute_rank": 3, "mentions": 2},
                   "recommendation": "honorable_mention"},
            "p3": {"geo_score": None, "presence": "brand_absent",
                   "recommendation": "absent"}})
        r = run_script("citation_panel.py",
                       ["score", "--run", R1, "--scores", scores, "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("geo 打分已写回 run %s" % R1, r.stdout)
        self.assertIn("3/3", r.stdout)
        self.assertNotIn("[!]", r.stdout)                # 全合法 → 无警告
        panel = load_panel(path)
        g = panel["runs"][0]["results"]["p1"]["geo"]     # 与 rubric 十一节示例同构
        self.assertEqual(g["geo_score"], 80)
        self.assertEqual(g["presence"], "cited_brand")
        self.assertEqual(g["position"]["absolute_rank"], 1)
        self.assertEqual(g["competitors"][0]["brand"], "HubSpot")
        self.assertEqual(panel["runs"][0]["results"]["p2"]["geo"]["geo_score"], 45)
        self.assertIsNone(panel["runs"][0]["results"]["p3"]["geo"]["geo_score"])
        self.assertNotIn("geo", panel["runs"][1]["results"]["p1"])   # 其他 run 不动
        with open(os.path.join(tmp, "runs", R1 + ".json"), encoding="utf-8") as f:
            runfile = json.load(f)                       # run 文件同步双写
        self.assertEqual(runfile["results"]["p2"]["geo"]["geo_score"], 45)
        self.assertEqual(runfile["results"]["p1"]["state"], "cited_brand")
        self.assertEqual(runfile["results"]["p1"]["cited_urls"], ["https://acme.ai/guide"])
        # --last → 最近一条 run(R2)
        s2 = write_scores(tmp, "s2.json", {
            "p1": {"geo_score": 62, "presence": "name_only_mention",
                   "position": {"absolute_rank": 2, "mentions": 2},
                   "recommendation": "neutral"},
            "p2": {"geo_score": 74, "presence": "cited_brand",
                   "recommendation": "recommended"}})
        r2 = run_script("citation_panel.py",
                        ["score", "--last", "--scores", s2, "--panel", path])
        self.assertEqual(r2.returncode, 0, r2.stderr)
        panel = load_panel(path)
        self.assertEqual(panel["runs"][1]["results"]["p1"]["geo"]["geo_score"], 62)
        self.assertEqual(panel["runs"][0]["results"]["p1"]["geo"]["geo_score"], 80)  # 不回改

    def test_scores_list_form_and_rescore(self):
        """scores.json 列表形态 [{"prompt":..., **geo}] 可读;重复打分覆盖旧 geo。"""
        tmp = tempfile.mkdtemp(prefix="geo_list_")
        path = setup_panel(tmp, [(R1, "chatgpt", "2026-10-01T00:00:00",
                                 {"p1": res(1, 0), "p2": res(0, 0)})])
        sfile = os.path.join(tmp, "list.json")
        with open(sfile, "w", encoding="utf-8") as f:
            json.dump([{"prompt": "p1", "geo_score": 55, "presence": "name_only_mention",
                        "position": {"absolute_rank": 2, "mentions": 2},
                        "recommendation": "neutral"}], f)
        r = run_script("citation_panel.py",
                       ["score", "--run", R1, "--scores", sfile, "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 55)
        self.assertNotIn("geo", load_panel(path)["runs"][0]["results"]["p2"])
        s2 = write_scores(tmp, "s2.json", {
            "p1": {"geo_score": 66, "presence": "name_only_mention",
                   "position": {"absolute_rank": 2, "mentions": 3},
                   "recommendation": "neutral"}})
        r2 = run_script("citation_panel.py",
                        ["score", "--run", R1, "--scores", s2, "--panel", path])
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("重打 1", r2.stdout)
        self.assertEqual(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 66)


class HardCapTests(unittest.TestCase):
    """rubric 第四节硬 cap 机检: 封顶不是扣分,多条命中取最严。"""

    def _score_one(self, tmp, geo, cell):
        path = setup_panel(tmp, [(R1, "chatgpt", "2026-10-01T00:00:00", {"p1": cell})])
        scores = write_scores(tmp, "s.json", {"p1": geo})
        return run_script("citation_panel.py",
                          ["score", "--run", R1, "--scores", scores, "--panel", path]), path

    def test_single_mention_cap(self):
        """仅 1 次提及 → ≤50: 加权 72 记 50(封顶,不是 72−22)。"""
        tmp = tempfile.mkdtemp(prefix="geo_cap1_")
        r, path = self._score_one(
            tmp, {"geo_score": 72, "presence": "name_only_mention",
                  "position": {"absolute_rank": 2, "mentions": 1},
                  "recommendation": "recommended"}, res(1, 0))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("仅 1 次提及", r.stdout)
        self.assertIn("cap 是封顶不是扣分", r.stdout)
        self.assertEqual(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 50)

    def test_echo_only_cap(self):
        """presence=echo_only → ≤10(品牌只出现在复述问题的回声里)。"""
        tmp = tempfile.mkdtemp(prefix="geo_cap2_")
        r, path = self._score_one(
            tmp, {"geo_score": 45, "presence": "echo_only",
                  "recommendation": "absent"}, res(0, 0))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("只出现在问题/回声里", r.stdout)
        self.assertEqual(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 10)

    def test_comparative_negative_cap(self):
        """对比性负面 → ≤35: 机检代理 = discouraged 或 sentiment≤20,两条路都封顶。"""
        tmp = tempfile.mkdtemp(prefix="geo_cap3_")
        r, path = self._score_one(
            tmp, {"geo_score": 60, "presence": "name_only_mention", "sentiment": 55,
                  "position": {"absolute_rank": 2, "mentions": 3},
                  "recommendation": "discouraged"}, res(1, 0))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("对比性负面", r.stdout)
        self.assertEqual(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 35)
        tmp2 = tempfile.mkdtemp(prefix="geo_cap3b_")
        r2, path2 = self._score_one(
            tmp2, {"geo_score": 60, "presence": "name_only_mention", "sentiment": 12,
                   "position": {"absolute_rank": 2, "mentions": 3},
                   "recommendation": "neutral"}, res(1, 0))
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(load_panel(path2)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 35)


class SchemaValidationTests(unittest.TestCase):
    """枚举/白名单/类型/prompt 对齐/failed cell: 硬违例整批原子拒绝,不落盘。"""

    def _score(self, tmp, scores, cells=None):
        path = setup_panel(tmp, [(R1, "chatgpt", "2026-10-01T00:00:00",
                                 cells or {"p1": res(1, 0), "p2": res(0, 0)})])
        sfile = write_scores(tmp, "s.json", scores)
        return run_script("citation_panel.py",
                          ["score", "--run", R1, "--scores", sfile, "--panel", path]), path

    def test_enum_violations_rejected(self):
        """recommendation 六枚举 / presence 枚举 / risks 五型枚举,枚举外值整批拒绝。"""
        tmp = tempfile.mkdtemp(prefix="geo_enum_")
        r, path = self._score(tmp, {"p1": {"geo_score": 55, "presence": "name_only_mention",
                                           "position": {"mentions": 2},
                                           "recommendation": "best_ever"}})
        self.assertEqual(r.returncode, 1)
        self.assertIn("六枚举", r.stderr)
        self.assertIn("整批拒绝", r.stderr)
        r, path = self._score(tmp, {"p1": {"geo_score": 55, "presence": "maybe",
                                           "recommendation": "neutral"}})
        self.assertEqual(r.returncode, 1)
        self.assertIn("presence", r.stderr)
        r, path = self._score(tmp, {"p1": {"geo_score": 55, "presence": "name_only_mention",
                                           "position": {"mentions": 2},
                                           "recommendation": "neutral",
                                           "risks": ["bad_risk"]}})
        self.assertEqual(r.returncode, 1)
        self.assertIn("五型枚举", r.stderr)
        for r_ in (load_panel(path)["runs"][0]["results"].values()):   # 原子: 无 geo 落盘
            self.assertNotIn("geo", r_)

    def test_unknown_field_rejected_atomically(self):
        """未知字段(geo/position/competitor 三层白名单)硬拒绝;同批合法条目也不写。"""
        tmp = tempfile.mkdtemp(prefix="geo_unknown_")
        r, path = self._score(tmp, {
            "p1": {"geo_score": 50, "presence": "name_only_mention",
                   "position": {"mentions": 2}, "recommendation": "neutral",
                   "vibes": "high"},
            "p2": {"geo_score": None, "presence": "brand_absent",
                   "recommendation": "absent"}})
        self.assertEqual(r.returncode, 1)
        self.assertIn("未知字段 vibes", r.stderr)
        self.assertIn("整批拒绝", r.stderr)
        for r_ in load_panel(path)["runs"][0]["results"].values():     # p2 合法也不落盘
            self.assertNotIn("geo", r_)
        r2, _ = self._score(tmp, {"p1": {"geo_score": 50, "presence": "name_only_mention",
                                         "position": {"absolute_rank": 2, "mentions": 2,
                                                      "depth": 3},
                                         "recommendation": "neutral"}})
        self.assertEqual(r2.returncode, 1)
        self.assertIn("position 未知字段 depth", r2.stderr)

    def test_top_pick_requires_rank1_evidence(self):
        """top_pick 无 position 绝对排名 #1 佐证 → 降 honorable_mention + 警告;
        有 absolute_rank=1 → 保持 top_pick。"""
        tmp = tempfile.mkdtemp(prefix="geo_tp_")
        r, path = self._score(
            tmp, {"p1": {"geo_score": 90, "presence": "cited_brand", "sentiment": 88,
                         "position": {"absolute_rank": 3, "mentions": 4},
                         "recommendation": "top_pick"}}, {"p1": res(1, 1, ["https://acme.ai/a"])})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("降级 honorable_mention", r.stdout)
        g = load_panel(path)["runs"][0]["results"]["p1"]["geo"]
        self.assertEqual(g["recommendation"], "honorable_mention")
        self.assertEqual(g["geo_score"], 90)            # 降级只动 rec,不扣分
        tmp2 = tempfile.mkdtemp(prefix="geo_tp2_")
        r2, path2 = self._score(
            tmp2, {"p1": {"geo_score": 90, "presence": "cited_brand", "sentiment": 88,
                          "recommendation": "top_pick"}},              # 连 position 都没有
            {"p1": res(1, 1, ["https://acme.ai/a"])})
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(load_panel(path2)["runs"][0]["results"]["p1"]["geo"]
                         ["recommendation"], "honorable_mention")
        tmp3 = tempfile.mkdtemp(prefix="geo_tp3_")
        r3, path3 = self._score(
            tmp3, {"p1": {"geo_score": 90, "presence": "cited_brand", "sentiment": 88,
                          "position": {"absolute_rank": 1, "mentions": 4},
                          "recommendation": "top_pick"}},
            {"p1": res(1, 1, ["https://acme.ai/a"])})
        self.assertEqual(r3.returncode, 0, r3.stderr)
        self.assertNotIn("降级", r3.stdout)
        self.assertEqual(load_panel(path3)["runs"][0]["results"]["p1"]["geo"]
                         ["recommendation"], "top_pick")

    def test_out_of_range_clamped(self):
        """越界值 clamp + 警告(不整条拒绝): geo_score 120→100、sentiment 150→100、
        absolute_rank 0→1、mentions -3→0、first_occurrence_pct 150→100。"""
        tmp = tempfile.mkdtemp(prefix="geo_clamp_")
        r, path = self._score(
            tmp, {"p1": {"geo_score": 120, "presence": "cited_brand", "sentiment": 150,
                         "position": {"absolute_rank": 0, "mentions": -3,
                                      "first_occurrence_pct": 150},
                         "recommendation": "recommended"}},
            {"p1": res(1, 1, ["https://acme.ai/a"])})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("[!]"), 6)    # 5 处 clamp + 均值>75 反通胀提示
        self.assertIn("geo_score=120.0 越界,已 clamp 到 100", r.stdout)
        self.assertIn("position.absolute_rank=0.0 越界,已 clamp 到 1", r.stdout)
        g = load_panel(path)["runs"][0]["results"]["p1"]["geo"]
        self.assertEqual(g["geo_score"], 100)
        self.assertEqual(g["sentiment"], 100)
        self.assertEqual(g["position"], {"absolute_rank": 1, "mentions": 0,
                                         "first_occurrence_pct": 100})

    def test_failed_cell_and_missing_prompt_rejected(self):
        """state=failed 的 cell 不打分不入分母;prompt 不在 run results 中 → 拒绝。"""
        tmp = tempfile.mkdtemp(prefix="geo_fail_")
        r, path = self._score(
            tmp, {"p1": {"geo_score": 50, "presence": "name_only_mention",
                         "recommendation": "neutral"}},
            {"p1": res(0, 0, state="failed"), "p2": res(0, 0)})
        self.assertEqual(r.returncode, 1)
        self.assertIn("state=failed,不打分", r.stderr)
        r2, _ = self._score(tmp, {"ghost": {"geo_score": 50, "presence": "name_only_mention",
                                            "recommendation": "neutral"}})
        self.assertEqual(r2.returncode, 1)
        self.assertIn("不在 run", r2.stderr)

    def test_absent_presence_nullifies_score(self):
        """refused/no_answer/brand_absent 给了数值 geo_score → 置 null + 警告
        (缺席不是 0 分回答,是没有可打分的呈现)。"""
        tmp = tempfile.mkdtemp(prefix="geo_absent_")
        r, path = self._score(
            tmp, {"p1": {"geo_score": 70, "presence": "brand_absent",
                         "recommendation": "absent"}}, {"p1": res(0, 0)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("已置 null", r.stdout)
        self.assertIsNone(load_panel(path)["runs"][0]["results"]["p1"]["geo"]["geo_score"])
        r2, path2 = self._score(
            tmp, {"p1": {"geo_score": 70, "presence": "no_answer",
                         "recommendation": "absent"}}, {"p1": res(0, 0, state="no_answer")})
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIsNone(load_panel(path2)["runs"][0]["results"]["p1"]["geo"]["geo_score"])


class ReportAggregationTests(unittest.TestCase):
    """report geo 聚合: 按引擎分列不合并 / 分布档 / presence 计数 / 反通胀提示行。"""

    @staticmethod
    def _geo_panel(tmp):
        return setup_panel(tmp, [
            (R1, "chatgpt", "2026-10-01T00:00:00", {
                "a": res(1, 1, geo={"geo_score": 80, "presence": "cited_brand",
                                    "recommendation": "top_pick"}),
                "b": res(1, 0, geo={"geo_score": 60, "presence": "name_only_mention",
                                    "recommendation": "neutral"}),
                "c": res(0, 0, geo={"geo_score": None, "presence": "brand_absent",
                                    "recommendation": "absent"})}),
            (R2, "perplexity", "2026-10-02T00:00:00", {
                "a": res(1, 0, geo={"geo_score": 40, "presence": "name_only_mention",
                                    "recommendation": "honorable_mention"}),
                "b": res(0, 0)})])          # 无 geo 键的 result 不进聚合

    def test_per_engine_means_presence_and_distribution(self):
        """chatgpt 均值=(80+60)/2=70.0 与 perplexity 40.0 分列;null 不入均值;
        presence 枚举计数;分布档;不出现跨引擎合并均值 60.0。"""
        tmp = tempfile.mkdtemp(prefix="geo_agg_")
        r = run_script("citation_panel.py", ["report", "--panel", self._geo_panel(tmp)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("GEO 打分聚合", r.stdout)
        self.assertIn("geo cells=3 scored=2", r.stdout)          # c 为 null 不入 scored
        self.assertIn("presence: brand_absent=1, name_only_mention=1, cited_brand=1", r.stdout)
        self.assertIn("geo_score 均值=70.0", r.stdout)
        self.assertIn("geo_score 均值=40.0", r.stdout)
        self.assertNotIn("均值=60.0", r.stdout)                  # 跨引擎不合并
        self.assertIn("0-35:0 36-55:0 56-75:1 76-100:1", r.stdout)
        self.assertIn("recommendation: top_pick=1, neutral=1, absent=1", r.stdout)
        self.assertIn("分析层扩展键", r.stdout)                    # 口径隔离说明行

    def test_anti_inflation_hint_line(self):
        """引擎均值>75 → 打印反通胀提示行;≤75 不打。"""
        def engine_panel(tmpdir, s1, s2):
            cells = {
                "a": res(1, 1, geo={"geo_score": s1, "presence": "cited_brand",
                                    "recommendation": "recommended"}),
                "b": res(1, 1, geo={"geo_score": s2, "presence": "cited_brand",
                                    "recommendation": "recommended"})}
            return setup_panel(tmpdir, [(R1, "chatgpt", "2026-10-01T00:00:00", cells)])

        tmp = tempfile.mkdtemp(prefix="geo_infl_")
        r = run_script("citation_panel.py", ["report", "--panel", engine_panel(tmp, 80, 82)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("均值=81.0", r.stdout)
        self.assertIn("LLM 系统性打高分,复核是否虚高(rubric 反通胀纪律)", r.stdout)
        tmp2 = tempfile.mkdtemp(prefix="geo_infl2_")
        r2 = run_script("citation_panel.py", ["report", "--panel", engine_panel(tmp2, 50, 60)])
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("均值=55.0", r2.stdout)
        self.assertNotIn("复核是否虚高", r2.stdout)

    def test_report_engine_filter(self):
        """report --engine 只聚合该引擎的 geo,另一引擎不出现。"""
        tmp = tempfile.mkdtemp(prefix="geo_filter_")
        r = run_script("citation_panel.py",
                       ["report", "--engine", "perplexity", "--panel", self._geo_panel(tmp)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("geo_score 均值=40.0", r.stdout)
        self.assertNotIn("geo_score 均值=70.0", r.stdout)
        self.assertNotIn("geo cells=3", r.stdout)

    def test_distribution_band_edges(self):
        """分布档边界: 10/48/70/90 各落一档 0-35/36-55/56-75/76-100。"""
        tmp = tempfile.mkdtemp(prefix="geo_band_")
        cells = {("p%d" % i): res(1, 1, geo={"geo_score": s, "presence": "cited_brand",
                                             "recommendation": "neutral"})
                 for i, s in enumerate((10, 48, 70, 90), 1)}
        path = setup_panel(tmp, [(R1, "chatgpt", "2026-10-01T00:00:00", cells)])
        r = run_script("citation_panel.py", ["report", "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("0-35:1 36-55:1 56-75:1 76-100:1", r.stdout)


class CompatTests(unittest.TestCase):
    """兼容: 旧 panel.json 无 geo 键照常(report 无 geo 节;compute_stats 不破坏);
    diff 不因 geo 键变化触发信号;--rubric standalone;冻结自测保持全绿。"""

    def test_legacy_panel_without_geo(self):
        """无 geo 键的旧面板 report 正常且无 GEO 节;手工加 geo 键后
        compute_stats 全部指标不变(geo 是被忽略的扩展键)。"""
        tmp = tempfile.mkdtemp(prefix="geo_legacy_")
        path = setup_panel(tmp, [(R1, "chatgpt", "2026-10-01T00:00:00", {
            "p1": res(1, 1, ["https://acme.ai/a", "https://other.org/b"]),
            "p2": res(1, 0),
            "p3": res(0, 0)})])
        r = run_script("citation_panel.py", ["report", "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("GEO 打分聚合", r.stdout)
        panel = load_panel(path)
        st_before = cp.compute_stats(panel)
        for run in panel["runs"]:                       # 事后手工塞 geo 键(旧数据+新键混存)
            for cell in run["results"].values():
                cell["geo"] = {"geo_score": 99, "presence": "cited_brand",
                               "recommendation": "recommended"}
        st_after = cp.compute_stats(panel)
        self.assertEqual(st_before["coverage"], st_after["coverage"])
        self.assertEqual(st_before["share"], st_after["share"])
        self.assertEqual(st_before["state_counts"], st_after["state_counts"])
        self.assertEqual(st_before["answers"], st_after["answers"])
        self.assertEqual(st_before["sov"], st_after["sov"])

    def test_diff_ignores_geo_keys(self):
        """两期采集层数据完全一致、仅 geo 键不同 → mention Δ=0,不产生 signal
        (geo 是分析层非采集层,打分变化不触发信号)。"""
        tmp = tempfile.mkdtemp(prefix="geo_diff_")
        path = setup_panel(tmp, [
            (R1, "chatgpt", "2026-10-01T00:00:00", {
                "p1": res(1, 0), "p2": res(1, 1, ["https://acme.ai/a"])}),
            ("chatgpt-2026-10-08", "chatgpt", "2026-10-08T00:00:00", {
                "p1": res(1, 0, geo={"geo_score": 10, "presence": "name_only_mention",
                                     "recommendation": "discouraged"}),
                "p2": res(1, 1, ["https://acme.ai/a"],
                          geo={"geo_score": 90, "presence": "cited_brand",
                               "recommendation": "top_pick"})})])
        r = run_script("citation_panel.py",
                       ["diff", R1, "chatgpt-2026-10-08", "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mention: run1 2/2=100.0% → run2 2/2=100.0%", r.stdout)
        self.assertNotIn("[signal]", r.stdout)

    def test_score_rubric_flag_standalone(self):
        """score --rubric 打印压缩判定要点(常量内嵌),不读面板文件也能出。"""
        tmp = tempfile.mkdtemp(prefix="geo_rubric_")
        r = run_script("citation_panel.py",
                       ["score", "--rubric", "--panel", os.path.join(tmp, "nope.json")])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("geo-scoring-rubric 压缩判定要点", r.stdout)
        for kw in ("硬 cap", "仅 1 次提及 ≤50", "反通胀", "top_pick", "81-100",
                   "outdated_info"):
            self.assertIn(kw, r.stdout)

    def test_help_and_frozen_self_test_green(self):
        """score --help 正常;--self-test 全绿(冻结断言原样保留)。"""
        for args in (["--help"], ["score", "--help"]):
            r = run_script("citation_panel.py", args)
            self.assertEqual(r.returncode, 0, args)
        r = run_script("citation_panel.py", ["--self-test"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[self-test] PASS citation_panel", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
