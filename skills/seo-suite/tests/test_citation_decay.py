#!/usr/bin/env python3
"""citation_panel.py v2 扩展测试: decay 子命令(Profound 官方方法论)/ diff signals
(Scrunch 口径)/ 指标族(Peec 官方公式)/ prompts 对象化(B3)。
standalone(自带 run_script 助手,合成 panel.json 数据,零网络):
python3 tests/test_citation_decay.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

合成数据口径: 序列值 y=被引(0/1);等距采样;面板首 run 日期=面板窗起点。
所有期望值均按"7 点滚动均值(暖机期不计)+ 半衰=peak 后首触 ≤50%peak 且
此后 14 天无反弹"手工推导后在断言中钉死。"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import citation_panel as cp  # noqa: E402  (需先入 SCRIPTS 路径)

D0 = datetime(2026, 1, 1)


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def res(mentioned=0, cited=0, urls=(), state=None, rank=None):
    """与 normalize_result 同构的最小 cell 结果。"""
    if state is None:
        state = "cited_brand" if cited else ("name_only_mention" if mentioned else "brand_absent")
    r = {"state": state, "mentioned": mentioned, "cited": cited, "cited_urls": list(urls)}
    if rank is not None:
        r["rank"] = rank
    return r


def make_run(engine, date, results):
    return {"run_id": "%s-%s" % (engine, date), "engine": engine, "date": date,
            "brand": "Acme", "results": results}


def panel_from_series(series_map, engine="chatgpt", start=D0, extra=None):
    """{prompt: [(day_offset, y)]} → panel dict(y=1→cited_brand, y=0→brand_absent;
    runs 按日期聚合)。extra 附加面板字段(competitors 等)。"""
    by_date = {}
    for prompt, pts in series_map.items():
        for off, y in pts:
            by_date.setdefault(off, {})[prompt] = res(mentioned=int(y), cited=int(y))
    runs = [make_run(engine, (start + timedelta(days=off)).isoformat(), by_date[off])
            for off in sorted(by_date)]
    panel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
             "prompts": sorted(series_map), "engines": [engine], "runs": runs}
    panel.update(extra or {})
    return panel


def series(step, n_ones, n_total, start=D0):
    """等距采样: 前 n_ones 个 y=1,其余 y=0。"""
    return [(start + timedelta(days=step * i), 1.0 if i < n_ones else 0.0)
            for i in range(n_total)]


class DecayTests(unittest.TestCase):
    """decay: 半衰判定 / 闸门剔除 / holding 右删失 / 重写队列排序。"""

    def test_clear_half_drop_decayed(self):
        """10 个 1 → 13 个 0(2 天采样,44 天窗):peak=1.0@day12;
        day26 首触 3/7≤0.5 且此后 14 天无反弹 → decayed,半衰=14 天。"""
        cell = cp.eval_decay_cell(series(2, 10, 23), panel_start=D0)
        self.assertEqual(cell["status"], "decayed")
        self.assertEqual(cell["half_life_days"], 14)
        self.assertEqual(cell["days_to_half"], 0)
        self.assertEqual(cell["peak"], 1.0)
        self.assertEqual(cell["peak_date"], (D0 + timedelta(days=12)).isoformat())
        self.assertEqual(cell["n_samples"], 23)

    def test_gates_exclude_cells(self):
        """4 道资格闸门: 观察窗<28 / 首采距窗起点>30 / 峰值≤0 / 峰值窗采样<5。"""
        short = cp.eval_decay_cell(series(1, 4, 4), panel_start=D0)
        self.assertEqual(short["status"], "excluded")
        self.assertIn("观察窗", short["exclude_reason"])
        late = cp.eval_decay_cell(series(1, 40, 40, start=D0 + timedelta(days=31)),
                                 panel_start=D0)
        self.assertEqual(late["status"], "excluded")
        self.assertIn("首采距面板窗起点 31 天>30", late["exclude_reason"])
        zero = cp.eval_decay_cell(series(1, 0, 30), panel_start=D0)
        self.assertEqual(zero["status"], "excluded")
        self.assertIn("峰值≤0", zero["exclude_reason"])
        sparse = cp.eval_decay_cell(series(20, 8, 8), panel_start=D0)   # 20 天间距
        self.assertEqual(sparse["status"], "excluded")
        self.assertIn("峰值窗", sparse["exclude_reason"])

    def test_holding_right_censored(self):
        """11 个 1 → 5 个 0(2 天采样,30 天窗):day28 首触 ≤半,但确认窗
        day42 超出观察末尾 day30 → holding 右删失(不丢弃,仍在 cells 里)。"""
        samples = series(2, 11, 16)
        cell = cp.eval_decay_cell(samples, panel_start=D0)
        self.assertEqual(cell["status"], "holding")
        self.assertIn("右删失", cell["note"])
        out = cp.analyze_decay(panel_from_series({"H": [(2 * i, 1 if i < 11 else 0)
                                                       for i in range(16)]}))
        holding = [c for c in out["cells"] if c["prompt"] == "H"]
        self.assertEqual(len(holding), 1)                     # 不被丢弃
        self.assertEqual(holding[0]["status"], "holding")
        self.assertEqual(out["rewrite_queue"], [])            # holding 不进重写队列

    def test_rewrite_queue_order(self):
        """队列 = 状态∈{decaying,decayed} × 距半衰剩余天数升序:
        A(decayed,剩余 0) < C(decaying,≈3 天) < B(decaying,≈11 天);
        holding/excluded 不进队列。"""
        panel = panel_from_series({
            "A": [(2 * i, 1 if i < 10 else 0) for i in range(23)],   # decayed
            "C": [(3 * i, 1 if i < 10 else 0) for i in range(13)],   # decaying ≈3 天
            "B": [(3 * i, 1 if i < 10 else 0) for i in range(12)],   # decaying ≈11 天
            "H": [(2 * i, 1 if i < 11 else 0) for i in range(16)],   # holding
            "X": [(i, 1) for i in range(4)],                         # excluded(窗<28)
        })
        out = cp.analyze_decay(panel)
        queue = out["rewrite_queue"]
        self.assertEqual([c["prompt"] for c in queue], ["A", "C", "B"])
        self.assertEqual(queue[0]["status"], "decayed")
        self.assertEqual(queue[0]["days_to_half"], 0)
        self.assertEqual(queue[1]["status"], "decaying")
        self.assertEqual(queue[2]["status"], "decaying")
        self.assertLess(queue[1]["days_to_half"], queue[2]["days_to_half"])
        self.assertGreater(queue[1]["days_to_half"], 0)
        status = {c["prompt"]: c["status"] for c in out["cells"]}
        self.assertEqual(status["H"], "holding")
        self.assertEqual(status["X"], "excluded")

    def test_decay_cli_markdown_and_json(self):
        """CLI: decay 默认 markdown(脚注+官方常数行),--json 可解析且队列对齐。"""
        tmp = tempfile.mkdtemp(prefix="decay_cli_")
        path = os.path.join(tmp, "panel.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(panel_from_series({
                "A": [(2 * i, 1 if i < 10 else 0) for i in range(23)],
                "H": [(2 * i, 1 if i < 11 else 0) for i in range(16)],
            }), f, ensure_ascii=False)
        md = run_script("citation_panel.py", ["decay", "--panel", path])
        self.assertEqual(md.returncode, 0)
        self.assertIn("重写队列", md.stdout)
        self.assertIn("跨引擎相关仅 0.03-0.09,分引擎独立判定(Profound 官方)", md.stdout)
        self.assertIn("中位半衰期 11 天", md.stdout)
        self.assertIn("78% 页两周内掉半", md.stdout)
        js = run_script("citation_panel.py", ["decay", "--panel", path, "--json"])
        self.assertEqual(js.returncode, 0)
        payload = json.loads(js.stdout)
        self.assertEqual(payload["rewrite_queue"][0]["prompt"], "A")
        self.assertEqual(payload["rewrite_queue"][0]["status"], "decayed")
        self.assertEqual(payload["rewrite_queue"][0]["half_life_days"], 14)
        status = {c["prompt"]: c["status"] for c in payload["cells"]}
        self.assertEqual(status["A"], "decayed")
        self.assertEqual(status["H"], "holding")


class SignalTests(unittest.TestCase):
    """diff signals(Scrunch 口径): 5pp+n≥10 门限 / fingerprint / 消失贡献排序。"""

    @staticmethod
    def _panel_runs():
        crm = ["crm %d" % i for i in range(6)]
        bill = ["bill %d" % i for i in range(10)]
        prompts = ([{"text": t, "topic": "crm"} for t in crm]
                   + [{"text": t, "topic": "billing"} for t in bill])
        ra = make_run("chatgpt", "2026-09-01T00:00:00",
                      {t: res(1, 0) for t in crm}
                      | {t: (res(1, 0) if i < 5 else res(0, 0)) for i, t in enumerate(bill)})
        rb = make_run("chatgpt", "2026-09-08T00:00:00",
                      {t: res(0, 0) for t in crm}
                      | {t: (res(1, 0) if i < 5 else res(0, 0)) for i, t in enumerate(bill)})
        panel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
                 "prompts": prompts, "engines": ["chatgpt"], "runs": [ra, rb]}
        return panel, ra, rb

    def test_signal_gate_5pp_and_n10(self):
        """|Δ|≥5pp 且配对 n≥10 才报;topic 粒度 n<10 列"样本不足";
        |Δ|<5pp 且 n≥10 计 stable 不报。"""
        panel, ra, rb = self._panel_runs()
        d = cp.diff_runs(ra, rb)
        sig = cp.diff_signals(ra, rb, d, panel)
        self.assertEqual(len(d["paired"]), 16)
        # 整体 mention: k1=11 → k2=5,Δ=-6/16=-37.5pp,n=16 → 报
        overall = [s for s in sig["signals"] if s["topic"] == "(整体)"]
        self.assertEqual(len(overall), 1)
        self.assertEqual(overall[0]["metric"], "mention")
        self.assertAlmostEqual(overall[0]["delta_pp"], -37.5)
        self.assertEqual(overall[0]["n"], 16)
        self.assertEqual(overall[0]["status"], "reported")
        # crm topic n=6 <10 → 样本不足,不入 signals
        self.assertFalse(any(s["topic"] == "crm" for s in sig["signals"]))
        crm_ins = [s for s in sig["insufficient"] if s["topic"] == "crm"]
        self.assertTrue(crm_ins)
        self.assertEqual(crm_ins[0]["status"], "insufficient_n")
        self.assertEqual(crm_ins[0]["n"], 6)
        # billing n=10 但 Δ=0(mention),整体 citation Δ=0 → stable 不报
        self.assertFalse(any(s["topic"] == "billing" for s in sig["signals"]))
        self.assertGreaterEqual(sig["stable_count"], 2)

    def test_fingerprint_stable(self):
        """fingerprint=sha1(metric+engine+topic)[:10]: 稳定、可复算、区分 topic。"""
        fp = cp.signal_fingerprint("mention", "chatgpt", "crm")
        self.assertEqual(fp, cp.signal_fingerprint("mention", "chatgpt", "crm"))
        self.assertEqual(len(fp), 10)
        int(fp, 16)                                              # 十六进制
        self.assertNotEqual(fp, cp.signal_fingerprint("mention", "chatgpt", "billing"))
        self.assertNotEqual(fp, cp.signal_fingerprint("citation", "chatgpt", "crm"))

    def test_disappeared_ranked_by_contribution(self):
        """消失 prompt 按贡献排序: 贡献 = −前期均值/配对 n×100(pp)。"""
        runs = [
            make_run("chatgpt", "2026-09-0%dT00:00:00" % i, {   # 前期历史(d5-d8)
                "P1": res(1, 0),
                "P2": res(1 if i == 5 else 0, 0),
                "P3": res(1 if i == 5 else 0, 0),
            }) for i in range(5, 9)
        ]
        ra = make_run("chatgpt", "2026-09-10T00:00:00",
                      {t: res(1, 0) for t in ("P1", "P2", "P3", "P4")})
        rb = make_run("chatgpt", "2026-09-20T00:00:00",
                      {t: res(0, 0) for t in ("P1", "P2", "P3", "P4")})
        panel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
                 "prompts": ["P1", "P2", "P3", "P4"], "engines": ["chatgpt"],
                 "runs": runs + [ra, rb]}
        d = cp.diff_runs(ra, rb)
        self.assertEqual(sorted(d["disappeared"]), ["P1", "P2", "P3", "P4"])
        sig = cp.diff_signals(ra, rb, d, panel)
        ranked = sig["disappeared_ranked"]
        # 前期均值: P1=1.0(4 历史全 1 + run1),P4 无历史→退回 run1 值 1.0,
        # P2=(1+0+0+0+1)/5=0.4,P3 同 0.4 → 贡献 -25/-25/-10/-10pp,n=4
        self.assertEqual({r[0] for r in ranked[:2]}, {"P1", "P4"})
        self.assertEqual({r[0] for r in ranked[2:]}, {"P2", "P3"})
        self.assertAlmostEqual(ranked[0][1], 1.0)
        self.assertAlmostEqual(ranked[2][2], -0.4 / 4 * 100)
        self.assertAlmostEqual(ranked[0][2], -1.0 / 4 * 100)
        # 贡献按绝对值降序
        contribs = [abs(r[2]) for r in ranked]
        self.assertEqual(contribs, sorted(contribs, reverse=True))


class PromptObjectTests(unittest.TestCase):
    """prompts 对象化: 字符串自动升级 / 表格解析 / persona fanout / stage-mix。"""

    def test_prompt_objectification_compat(self):
        """旧字符串读取时自动升级为 {text:...};对象字段规范化;
        record 成员检查按 text 命中对象形态面板。"""
        self.assertEqual(cp.prompt_obj("旧字符串 prompt"), {"text": "旧字符串 prompt", "tags": []})
        o = cp.prompt_obj({"text": "q", "stage": "Awareness ", "tags": "a;b",
                           "branded": "yes", "topic": "crm", "region": "us", "lang": "en"})
        self.assertEqual(o["stage"], "awareness")
        self.assertEqual(o["tags"], ["a", "b"])
        self.assertTrue(o["branded"])
        self.assertEqual(o["topic"], "crm")
        tmp = tempfile.mkdtemp(prefix="pobj_")
        csv_path = os.path.join(tmp, "run.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("prompt,mentioned,cited,cited_urls\nq,1,0,\nstranger,1,0,\n")
        panel = {"brand": "B", "prompts": [{"text": "q", "topic": "crm"}], "runs": []}
        results, warnings = cp.read_run_csv(csv_path, panel)
        self.assertIn("q", results)                       # 对象形态命中
        self.assertTrue(any("stranger" in w for w in warnings))
        # 旧 --prompts 路径仍产字符串形态(冻结行为)
        pcsv = os.path.join(tmp, "p.csv")
        with open(pcsv, "w", encoding="utf-8") as f:
            f.write("prompt\nlegacy one\nlegacy two\n")
        ppath = os.path.join(tmp, "panel.json")
        args = cp.build_parser().parse_args(
            ["init", "--brand", "B", "--prompts", pcsv, "--panel", ppath])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cp.cmd_init(args), 0)
        with open(ppath, encoding="utf-8") as f:
            stored = json.load(f)["prompts"]
        self.assertEqual(stored, ["legacy one", "legacy two"])

    def test_prompts_file_persona_fanout_stage_mix(self):
        """--prompts-file 吃 markdown 表格/带表头 CSV/纯文本;persona 前缀+
        固定后缀变体;--stage-mix 打印 Scrunch 官方配方。"""
        tmp = tempfile.mkdtemp(prefix="pfile_")
        md = os.path.join(tmp, "prompt-bank.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write("# Prompt Bank\n\n<!-- 注释行跳过 -->\n\n"
                    "| prompt | stage | topic | tags |\n|---|---|---|---|\n"
                    "| best crm for small business | awareness | crm | b2b;saas |\n"
                    "| crm pricing compared | consideration | crm | b2b |\n\n"
                    "- bullet style prompt\nplain style prompt\n")
        objs = cp.read_prompts_file(md)
        self.assertEqual(objs[0], {"text": "best crm for small business",
                                   "stage": "awareness", "topic": "crm",
                                   "tags": ["b2b", "saas"]})
        texts = [o["text"] for o in objs]
        self.assertIn("bullet style prompt", texts)
        self.assertIn("plain style prompt", texts)
        csvf = os.path.join(tmp, "bank.csv")
        with open(csvf, "w", encoding="utf-8") as f:
            f.write("prompt,stage\nq1,awareness\nq2,decision\n")
        csv_objs = cp.read_prompts_file(csvf)
        self.assertEqual([o["stage"] for o in csv_objs], ["awareness", "decision"])
        # prompt-bank.md 中文列别名: 漏斗列→stage(认知/比较/决策映射),模板列→text
        zh = os.path.join(tmp, "zh.md")
        with open(zh, "w", encoding="utf-8") as f:
            f.write("| 编号 | 漏斗 | 模板(整句) |\n|---|---|---|\n"
                    "| A1 | 认知 | What are the best CRMs? Include sources. |\n"
                    "| D1 | 决策 | Acme vs Comp: which to buy? Cite your sources. |\n")
        zh_objs = cp.read_prompts_file(zh)
        self.assertEqual(zh_objs[0]["text"], "What are the best CRMs? Include sources.")
        self.assertEqual(zh_objs[0]["stage"], "awareness")
        self.assertEqual(zh_objs[1]["stage"], "decision")
        # persona fanout: 前缀表 + 固定后缀
        self.assertIn("SEO Lead", cp.PERSONA_PREFIXES)
        self.assertIn("PMM", cp.PERSONA_PREFIXES)
        fan = cp.persona_fanout("best CRM", ["CMO", "Founder"], [])
        self.assertEqual(fan[0]["text"],
                         "As a CMO evaluating this for a 50-person team, best CRM"
                         " Respond with sources and direct claims first.")
        self.assertTrue(fan[1]["text"].startswith("As a bootstrapped founder, "))
        self.assertTrue(fan[1]["text"].endswith(cp.FANOUT_SUFFIX))
        self.assertEqual(fan[0]["tags"], ["persona-fanout", "CMO"])
        # CLI: init --prompts-file + --persona-fanout + --stage-mix
        ppath = os.path.join(tmp, "panel.json")
        r = run_script("citation_panel.py",
                       ["init", "--brand", "Acme", "--domain", "acme.ai",
                        "--prompts-file", md, "--stage-mix",
                        "--persona-fanout", "best crm for small business",
                        "--personas", "CMO,Founder", "--panel", ppath])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("5 awareness + 3 consideration + 2 decision", r.stdout)
        self.assertIn("[persona-fanout] 生成 2 条前缀注入变体", r.stdout)
        with open(ppath, encoding="utf-8") as f:
            panel = json.load(f)
        stored = {p["text"]: p for p in panel["prompts"]}
        self.assertIn("best crm for small business", stored)         # 表格行(对象)
        core = "best crm for small business"
        cmo_text = (cp.PERSONA_PREFIXES["CMO"] + core + cp.FANOUT_SUFFIX)
        founder_text = (cp.PERSONA_PREFIXES["Founder"] + core + cp.FANOUT_SUFFIX)
        fan_obj = stored[cmo_text]
        self.assertEqual(fan_obj["stage"], "awareness")               # 继承 core 元数据
        self.assertEqual(fan_obj["topic"], "crm")
        self.assertEqual(fan_obj["tags"], ["persona-fanout", "CMO"])
        self.assertIn(founder_text, stored)
        advice = cp.stage_mix_advice(panel["prompts"])
        self.assertIn("Scrunch 官方初始集配方", advice)
        # awareness=3(表格 1+fanout 继承 2)/consideration=1/decision=0 → 各补 2 条
        self.assertIn("补 2 条 decision", advice)


class MetricFamilyTests(unittest.TestCase):
    """指标族(Peec 官方公式): SoV / win_rate / citation_rate /
    brand_visibility vs source_visibility 差距>20pp 提示。"""

    @staticmethod
    def _panel(with_competitors=True):
        results = {}
        for i in range(10):
            if i < 4:      # 被提+被引(自家域),旁挂第三方引用
                results["p%d" % i] = res(1, 1, ["https://acme.ai/a%d" % i,
                                                 "https://other.org/x"], rank=(1, 1, 2, 3)[i])
            elif i < 8:    # 被提+竞品被引
                results["p%d" % i] = res(1, 0, ["https://comp.com/c"])
            elif i == 8:   # 未提+竞品被引
                results["p%d" % i] = res(0, 0, ["https://comp.com/c"])
            else:          # 被提,无任何引用
                results["p%d" % i] = res(1, 0, [])
        extra = {"competitors": ["comp.com"]} if with_competitors else {}
        return {"brand": "Acme", "domain": "acme.ai", "aliases": [],
                "prompts": ["p%d" % i for i in range(10)],
                "engines": ["chatgpt"],
                "runs": [make_run("chatgpt", "2026-09-01T00:00:00", results)], **extra}

    def test_metric_family_values(self):
        st = cp.compute_stats(self._panel())
        self.assertAlmostEqual(st["coverage"], 0.9)                       # 9/10 被提
        self.assertEqual(st["brand_hits"], 4)
        self.assertAlmostEqual(st["sov"], 4 / (4 + 5))                    # comp 5 个 cell 被引
        self.assertEqual(st["rank_cells"], 4)
        self.assertEqual(st["wins"], 2)
        self.assertAlmostEqual(st["win_rate"], 0.5)
        self.assertEqual(st["answers"], 10)
        self.assertAlmostEqual(st["citation_rate"], (8 + 5) / 10)         # 13 URL/10 答案
        self.assertAlmostEqual(st["source_visibility"], 0.4)
        self.assertAlmostEqual(st["visibility_gap_pp"], 50.0)             # >20pp
        report = cp.render_report(self._panel(), st)
        self.assertIn("SoV = 自身提及/(全部追踪品牌提及) = 4/9 = 44.4%", report)
        self.assertIn("win_rate = 排第一次数/响应数 = 2/4 = 50.0%", report)
        self.assertIn("citation_rate = 被检索时显式引用均次 = 13/10 = 1.30 次/响应", report)
        self.assertIn("品牌关联弱/内容信任不足二选一", report)              # 差距提示行
        self.assertIn("被提不被引=内容不被信任", report)

    def test_sov_na_without_competitor_list(self):
        st = cp.compute_stats(self._panel(with_competitors=False))
        self.assertIsNone(st["sov"])
        report = cp.render_report(self._panel(with_competitors=False), st)
        self.assertIn("SoV = N/A(面板无竞品名单", report)
        # rank 数据仍可算 win_rate(与竞品名单无关)
        self.assertAlmostEqual(st["win_rate"], 0.5)


class FrozenRegressionTests(unittest.TestCase):
    """冻结行为: --self-test 全绿(旧断言原样保留)+ --help 正常。"""

    def test_frozen_self_test_green(self):
        r = run_script("citation_panel.py", ["--self-test"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[self-test] PASS citation_panel", r.stdout)

    def test_help_and_subcommand_help(self):
        for args in (["--help"], ["decay", "--help"], ["init", "--help"],
                     ["diff", "--help"]):
            r = run_script("citation_panel.py", args)
            self.assertEqual(r.returncode, 0, args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
