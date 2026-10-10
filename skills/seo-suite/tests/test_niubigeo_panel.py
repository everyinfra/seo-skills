#!/usr/bin/env python3
"""citation_panel.py v4 扩展测试(借鉴 niubigeo;出处逐条标注
references/research/niubigeo-deep-read.md §3"值得抄 Top 10"):

  N1 提及检测: URL 掩码 + 实体词表(引用链接里的域名不算正文提及)/
      rank_position(全部实体按 first index 排序)/count/context(240/520 句边界内收)/
      sentiment 恒 neutral/record --answer-file 自动填 mentioned/rank(人工列优先)/
      report 提及检测标注节
  N2 指标切片: prompt.branded 两栏分报 {numerator,denominator,value}
      (分母=0 → null 永不报 0%)/交叉错配对(mentioned_without_official_citation ×
      cited_without_prose_mention)/无标注自动判定 + report --brand 覆盖
  N5 意图冻结分母: init 冻结 denominator_freeze + intents 非空校验/
      coverage_frozen 只数 eligible prompt/面板与 run 两级漂移警示
  N6 配对差分: record 存探针指纹 fingerprint/只对同 prompt×engine 且同指纹的
      配对算 Δ/未配对单列不入 Δ/跨引擎与跨指纹强制标注不可比

standalone(自带 run_script 助手,合成 panel.json 数据,零网络):
python3 tests/test_niubigeo_panel.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
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


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def res(mentioned=0, cited=0, urls=(), state=None, rank=None, detection=None):
    """与 normalize_result 同构的最小 cell(detection=record --answer-file 写入的
    mention_detection 扩展键)。"""
    if state is None:
        state = "cited_brand" if cited else ("name_only_mention" if mentioned else "brand_absent")
    r = {"state": state, "mentioned": mentioned, "cited": cited, "cited_urls": list(urls)}
    if rank is not None:
        r["rank"] = rank
    if detection is not None:
        r["mention_detection"] = detection
    return r


def make_run(engine, date, results, run_id=None, brand="Acme",
             fingerprint=None, dz_hash=None):
    run = {"run_id": run_id or "%s-%s" % (engine, date[:10]), "engine": engine,
           "date": date, "brand": brand, "results": results}
    if fingerprint is not None:
        run["fingerprint"] = fingerprint
    if dz_hash is not None:
        run["denominator_freeze_hash"] = dz_hash
    return run


def _write(tmp, name, content):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def setup_panel(tmp, panel):
    path = os.path.join(tmp, "panel.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel, f, ensure_ascii=False, indent=2)
    return path


PANEL = {"brand": "Acme", "domain": "acme.ai", "aliases": [], "engines": ["chatgpt"],
         "created": "2026-10-01T00:00:00", "runs": []}


class MentionDetectionTests(unittest.TestCase):
    """N1: URL 掩码 / 实体词表 / rank_position / context / record --answer-file。"""

    def test_url_mask_blocks_citation_domains(self):
        """引用链接里的域名不算正文提及(掩码后子串匹配);裸域无路径=行文提及。"""
        panel = {"brand": "Acme", "domain": "acme.ai", "aliases": []}
        det = cp.detect_mentions(
            "Great options at https://acme.ai/guide and www.acme.io/pricing today.",
            panel)
        self.assertEqual(det["mentioned"], 0)          # 链接域名全被掩掉
        self.assertEqual(det["urls_masked"], 2)
        self.assertEqual(det["terms_hit"], [])
        self.assertEqual(det["sentiment"], "neutral")  # 宁缺勿猜,恒 neutral
        det2 = cp.detect_mentions("Acme is a solid choice. Details: https://acme.ai/g",
                                  panel)
        self.assertEqual(det2["mentioned"], 1)         # 正文品牌名仍命中
        self.assertEqual(det2["count"], 1)
        det3 = cp.detect_mentions("I liked acme.ai overall.", panel)
        self.assertEqual(det3["mentioned"], 1)         # 裸域无路径 → 完整域名实体命中

    def test_entity_terms_rank_position_context(self):
        """实体词表(品牌/完整域/域名根≥3/别名)+ 竞品域进 rank_position +
        context 命中点前 240/后 520 且句边界内收(残句被截)。"""
        panel = {"brand": "Acme", "domain": "acme.ai", "aliases": ["Acme CRM"],
                 "competitors": ["comp.com"]}
        # 竞品在正文先现 + 品牌两次 + 尾部链接(链接域名被掩,不参与正文命中)
        det = cp.detect_mentions(
            "comp.com ranks first for most teams. Acme CRM is cheaper. "
            "Acme support is great. See https://comp.com/x for more", panel)
        self.assertEqual(det["mentioned"], 1)
        terms = {h["term"]: h for h in det["terms_hit"]}
        self.assertIn("Acme", terms)                    # 品牌名(域名根 "acme" 亦命中)
        self.assertIn("Acme CRM", terms)                # 别名
        self.assertGreaterEqual(det["count"], 2)
        self.assertEqual(det["rank_position"], 2)       # comp.com 正文首现更早
        self.assertEqual(det["urls_masked"], 1)
        self.assertIn("Acme CRM is cheaper", det["context"])
        # context 后窗: 首命中 +520 之外、末句边界之后的残句被截
        long_tail = ("comp.com leads. Acme CRM is cheaper. Acme support is great. "
                     + "Filler. " * 80 + "hanging tail")
        det_tail = cp.detect_mentions(long_tail, panel)
        self.assertIn("Acme CRM is cheaper", det_tail["context"])
        self.assertNotIn("hanging tail", det_tail["context"])
        # context 前窗: 首命中 −240 之前的内容内收到句边界(残句头部被截)
        lead = "no boundary junk " * 20 + ". Then Acme appears."
        det_lead = cp.detect_mentions(lead, panel)
        self.assertEqual(det_lead["context"], "Then Acme appears.")
        # 域名根过短(<3)不入词表
        self.assertNotIn("ai", cp.entity_terms(panel))

    def test_record_answer_file_autofill_and_manual_priority(self):
        """record --answer-file: 空缺 mentioned 自动填(含 rank)/人工显式列优先并
        告警差异/no_answer 有文本告警/写回 mention_detection 扩展键。"""
        tmp = tempfile.mkdtemp(prefix="nb_n1_")
        panel_path = os.path.join(tmp, "panel.json")
        prompts_csv = _write(tmp, "prompts.csv",
                             "prompt\nwhat is Acme crm\nbest crm for teams\n")
        self.assertEqual(run_script("citation_panel.py", [
            "init", "--brand", "Acme", "--domain", "acme.ai",
            "--prompts-file", prompts_csv, "--panel", panel_path]).returncode, 0)
        run_csv = _write(tmp, "run1.csv",
                         "prompt,mentioned,cited,cited_urls,state\n"
                         "what is Acme crm,,,,\n"          # 空缺 → 自动填 1
                         "best crm for teams,1,0,,\n")     # 人工 1,检测 0 → 人工优先
        answers = _write(tmp, "answers.csv",
                         'prompt,answer\n'
                         '"what is Acme crm","Acme is a CRM. See https://acme.ai/docs"\n'
                         '"best crm for teams","Zoho and HubSpot are popular."\n')
        r = run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file", run_csv,
            "--answer-file", answers, "--date", "2026-10-01T00:00:00",
            "--panel", panel_path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("掩码检测自动填 mentioned=1", r.stdout)
        self.assertIn("以人工列为准", r.stdout)
        with open(panel_path, encoding="utf-8") as f:
            panel = json.load(f)
        run = panel["runs"][0]
        c1 = run["results"]["what is Acme crm"]
        self.assertEqual((c1["mentioned"], c1["state"]), (1, "name_only_mention"))
        self.assertEqual(c1["rank"], 1)                  # 无竞品先现 → rank 自动填 1
        self.assertIn("mention_detection", c1)
        self.assertEqual(c1["mention_detection"]["mentioned"], 1)
        c2 = run["results"]["best crm for teams"]
        self.assertEqual((c2["mentioned"], c2["state"]), (1, "name_only_mention"))
        self.assertEqual(c2["mention_detection"]["mentioned"], 0)   # 检测差异留档
        # report 出 N1 标注节(旧面板无 detection 时整节不出现)
        rep = run_script("citation_panel.py", ["report", "--panel", panel_path])
        self.assertIn("提及检测(URL 掩码自动判定;niubigeo-deep-read.md N1", rep.stdout)
        self.assertIn("urls_masked=1", rep.stdout)

    def test_record_answer_file_state_guard_and_json_form(self):
        """failed/no_answer cell 有回答文本 → 告警不覆盖;JSON answer-file 同样支持。"""
        tmp = tempfile.mkdtemp(prefix="nb_n1b_")
        panel_path = setup_panel(tmp, dict(
            PANEL, prompts=["q1", "q2"],
            runs=[]))
        run_csv = _write(tmp, "run.csv",
                         "prompt,mentioned,cited,cited_urls,state\n"
                         "q1,0,0,,no_answer\n"
                         "q2,,,,\n")
        answers = _write(tmp, "answers.json", json.dumps(
            {"q1": "Acme answered after all.", "q2": "No brands here."}))
        r = run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file", run_csv,
            "--answer-file", answers, "--date", "2026-10-02T00:00:00",
            "--panel", panel_path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("state=no_answer 但 answer-file 有该 prompt 的回答文本", r.stdout)
        with open(panel_path, encoding="utf-8") as f:
            panel = json.load(f)
        results = panel["runs"][0]["results"]
        self.assertEqual(results["q1"]["state"], "no_answer")      # 不被检测覆盖
        self.assertNotIn("mention_detection", results["q1"])
        self.assertEqual(results["q2"]["state"], "brand_absent")   # 空缺自动填 0
        self.assertEqual(results["q2"]["mention_detection"]["mentioned"], 0)


class TargetingSliceTests(unittest.TestCase):
    """N2: branded/unbranded 两栏分报 + 交叉错配 + 自动判定/--brand 覆盖。"""

    @staticmethod
    def _panel():
        prompts = [{"text": "acme vs hubspot", "branded": True},
                   {"text": "acme pricing", "branded": True},
                   {"text": "best crm", "branded": False},
                   {"text": "best helpdesk", "branded": False}]
        results = {"acme vs hubspot": res(1, 1, ["https://acme.ai/a"], rank=1),
                   "acme pricing": res(1, 0),                    # name_only → 错配
                   "best crm": res(1, 0),
                   "best helpdesk": res(0, 0)}
        panel = dict(PANEL, prompts=prompts, competitors=["hub.com"], runs=[
            make_run("chatgpt", "2026-10-01T00:00:00", results)])
        return panel

    def test_branded_unbranded_split(self):
        """两栏各出全套指标(显式 branded 标注;品牌词与中性词不混分)。"""
        st = cp.compute_stats(self._panel())
        tgt = st["targeting"]
        self.assertEqual((tgt["basis_counts"].get("explicit", 0),
                          tgt["basis_counts"].get("auto", 0)), (4, 0))
        b = tgt["slices"]["branded_or_direct"]
        u = tgt["slices"]["organic_unbranded"]
        self.assertEqual((b["prompts"], b["denominator"]), (2, 2))
        self.assertEqual(b["mention_rate"], {"numerator": 2, "denominator": 2, "value": 1.0})
        self.assertEqual(b["citation_rate"], {"numerator": 1, "denominator": 2, "value": 0.5})
        self.assertEqual(b["first_position_rate"]["value"], 1.0)
        self.assertEqual(b["mentioned_without_official_citation"], 1)
        self.assertEqual(u["prompts"], 2)
        self.assertEqual(u["mention_rate"]["value"], 0.5)
        self.assertEqual(u["cited_cells"], 0)
        # 旧口径键与新切片并存且互不污染
        self.assertAlmostEqual(st["coverage"], 0.75)
        report = cp.render_report(self._panel(), st)
        self.assertIn("指标切片: prompt_targeting(niubigeo-deep-read.md N2", report)
        self.assertIn("[branded_or_direct] prompts=2 cells=2(成功分母 2)", report)
        self.assertIn("mention_rate   = 2/2 = 100.0%", report)

    def test_denominator_zero_null_and_cross_mismatch_with_detection(self):
        """分母=0 → value None 永不报 0%;cited_without_prose_mention 只数
        有掩码检测证据的 cell(无检测数据恒 0)。"""
        prompts = [{"text": "acme deep dive", "branded": True}]
        det = {"mentioned": 0, "terms_hit": [], "rank_position": None, "count": 0,
               "context": "", "urls_masked": 1, "sentiment": "neutral",
               "rules": cp.MENTION_RULES_VERSION}
        results = {"acme deep dive": res(1, 1, ["https://acme.ai/a"],
                                         detection=det)}   # 被引但正文没提
        panel = dict(PANEL, prompts=prompts, runs=[
            make_run("chatgpt", "2026-10-01T00:00:00", results)])
        st = cp.compute_stats(panel)
        u = st["targeting"]["slices"]["organic_unbranded"]
        self.assertEqual(u["cells"], 0)
        self.assertIsNone(u["mention_rate"]["value"])       # 永不报 0%
        self.assertEqual(u["mention_rate"]["denominator"], 0)
        b = st["targeting"]["slices"]["branded_or_direct"]
        self.assertEqual(b["cited_without_prose_mention"], 1)   # N1 检测 × N2 错配
        self.assertEqual(b["mentioned_without_official_citation"], 0)
        report = cp.render_report(panel, st)
        self.assertIn("null(分母=0 → null,永不报 0%)", report)
        self.assertIn("cited_without_prose_mention=1", report)
        # 无 detection 的同款 cell(旧数据)→ 恒 0
        panel2 = dict(PANEL, prompts=prompts, runs=[
            make_run("chatgpt", "2026-10-01T00:00:00",
                     {"acme deep dive": res(1, 1, ["https://acme.ai/a"])})])
        st2 = cp.compute_stats(panel2)
        self.assertEqual(
            st2["targeting"]["slices"]["branded_or_direct"]["cited_without_prose_mention"], 0)

    def test_auto_detection_and_brand_override(self):
        """无 branded 标注按"prompt 含品牌名"自动判定;report --brand 覆盖自动判定
        (显式标注不受影响)。"""
        prompts = [{"text": "is Acme worth it"}, {"text": "top crm tools"},
                   {"text": "acme setup", "branded": False}]
        panel = dict(PANEL, prompts=prompts, runs=[
            make_run("chatgpt", "2026-10-01T00:00:00",
                     {p["text"]: res(0, 0) for p in prompts})])
        st = cp.compute_stats(panel)
        self.assertEqual(st["targeting"]["basis_counts"], {"explicit": 1, "auto": 2})
        self.assertEqual(st["targeting"]["slices"]["branded_or_direct"]["prompts"], 1)
        self.assertEqual(st["targeting"]["slices"]["organic_unbranded"]["prompts"], 2)
        # --brand 覆盖: 用 Zoho 判定 → "is Acme worth it" 不再 branded
        st2 = cp.compute_stats(panel, brand_override="Zoho")
        self.assertEqual(st2["targeting"]["brand_used"], "Zoho")
        self.assertEqual(st2["targeting"]["slices"]["branded_or_direct"]["prompts"], 0)
        self.assertEqual(st2["targeting"]["slices"]["organic_unbranded"]["prompts"], 3)
        tmp = tempfile.mkdtemp(prefix="nb_n2_")
        path = setup_panel(tmp, panel)
        rep = run_script("citation_panel.py", ["report", "--brand", "Zoho",
                                               "--panel", path])
        self.assertEqual(rep.returncode, 0, rep.stderr)
        self.assertIn("品牌名=Zoho", rep.stdout)


class FrozenDenominatorTests(unittest.TestCase):
    """N5: init 冻结 + intents 非空校验 + coverage_frozen + 两级漂移警示。"""

    def test_init_freezes_and_validates_intents(self):
        """init 写 panel['denominator_freeze'](eligible/ineligible/frozen_at);
        带档案字段但 intents 为空 → 整批拒绝退出 1。"""
        tmp = tempfile.mkdtemp(prefix="nb_n5_")
        panel_path = os.path.join(tmp, "panel.json")
        bank = _write(tmp, "bank.md",
                      "| text | intents | candidate_applicable |\n"
                      "|---|---|---|\n"
                      "| best crm | recommendation;comparison | true |\n"
                      "| acme setup | product_usage | false |\n"
                      "| crm pricing | pricing | true |\n")
        r = run_script("citation_panel.py", [
            "init", "--brand", "Acme", "--domain", "acme.ai",
            "--prompts-file", bank, "--panel", panel_path])
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(panel_path, encoding="utf-8") as f:
            panel = json.load(f)
        frz = panel["denominator_freeze"]
        self.assertEqual(frz["version"], cp.DENOM_FREEZE_VERSION)
        self.assertEqual(len(frz["freeze_hash"]), 16)
        self.assertEqual(frz["ineligible_prompts"], ["acme setup"])
        self.assertEqual(len(frz["eligible_prompts"]), 2)
        self.assertIn("frozen_at", frz)
        stored = {p["text"]: p for p in panel["prompts"]}
        self.assertEqual(stored["best crm"]["intents"], ["recommendation", "comparison"])
        self.assertIs(stored["acme setup"]["candidate_applicable"], False)
        # 空 intents + 档案字段 → 拒绝(基线冻结不许空标签)
        bad = _write(tmp, "bad.md",
                     "| text | intents | candidate_applicable |\n"
                     "|---|---|---|\n"
                     "| broken q |  | true |\n")
        r2 = run_script("citation_panel.py", [
            "init", "--brand", "Acme", "--prompts-file", bad,
            "--panel", os.path.join(tmp, "p2.json")])
        self.assertEqual(r2.returncode, 1)
        self.assertIn("intents 为空", r2.stderr)
        self.assertIn("niubigeo-deep-read.md", r2.stderr)

    def test_coverage_frozen_excludes_ineligible_and_drift(self):
        """coverage_frozen 只数 eligible prompt 的成功 cell;面板 prompts 漂移与
        run 时点漂移均在 report 警示(答案结果不改变分母成员)。"""
        prompts = [{"text": "k1", "candidate_applicable": True},
                   {"text": "k2", "candidate_applicable": True},
                   {"text": "retired", "candidate_applicable": False}]
        results = {"k1": res(1, 0), "k2": res(0, 0), "retired": res(1, 0)}
        run = make_run("chatgpt", "2026-10-01T00:00:00", results)
        panel = dict(PANEL, prompts=prompts, runs=[run])
        st = cp.compute_stats(panel)
        self.assertEqual(st["frozen"]["eligible_count"], 2)
        self.assertEqual(st["frozen"]["ineligible_prompts"], ["retired"])
        # coverage=2/3(旧口径含 retired);coverage_frozen=1/2(仅 eligible)
        self.assertAlmostEqual(st["coverage"], 2 / 3)
        self.assertEqual(st["frozen"]["mention_rate"],
                         {"numerator": 1, "denominator": 2, "value": 0.5})
        self.assertIs(st["frozen"]["drift"], False)      # legacy 面板无存储档案
        # 面板级漂移: 存了档案但 prompts 之后被改 → drift=True + report 警示;
        # run 级漂移: 某 run 采样时点 hash ≠ 面板冻结档案 hash
        frz = cp.denominator_freeze(panel)
        panel["denominator_freeze"] = dict(frz, freeze_hash="deadbeefdeadbeef")
        run2 = dict(run, run_id="chatgpt-late",
                    denominator_freeze_hash="cafebabecafebabe")
        panel["runs"] = [run, run2]
        st2 = cp.compute_stats(panel)
        self.assertIs(st2["frozen"]["drift"], True)
        self.assertEqual(st2["frozen"]["run_hash_drift"], ["chatgpt-late"])
        report = cp.render_report(panel, st2)
        self.assertIn("意图冻结分母(niubigeo-deep-read.md N5", report)
        self.assertIn("分母漂移: 面板 prompts 与冻结档案不一致", report)
        self.assertIn("run 漂移: chatgpt-late", report)

    def test_record_stores_freeze_hash_and_legacy_parity(self):
        """record 写 run['denominator_freeze_hash'](面板时点快照);
        全 eligible 的 legacy 面板 coverage_frozen == coverage。"""
        tmp = tempfile.mkdtemp(prefix="nb_n5c_")
        panel_path = os.path.join(tmp, "panel.json")
        self.assertEqual(run_script("citation_panel.py", [
            "init", "--brand", "Acme", "--domain", "acme.ai",
            "--prompts-file", _write(tmp, "p.csv", "prompt\nk1\nk2\n"),
            "--panel", panel_path]).returncode, 0)
        run_csv = _write(tmp, "r.csv",
                         "prompt,mentioned,cited,cited_urls\nk1,1,0,\nk2,0,0,\n")
        self.assertEqual(run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file", run_csv,
            "--date", "2026-10-01T00:00:00", "--panel", panel_path]).returncode, 0)
        with open(panel_path, encoding="utf-8") as f:
            panel = json.load(f)
        run = panel["runs"][0]
        self.assertEqual(run["denominator_freeze_hash"],
                        panel["denominator_freeze"]["freeze_hash"])
        st = cp.compute_stats(panel)
        self.assertEqual(st["frozen"]["mention_rate"]["value"], st["coverage"])
        report = cp.render_report(panel, st)
        self.assertIn("面板 denominator_freeze 已冻结(init 时点)", report)
        self.assertIn("coverage_frozen", report)
        # 剥掉冻结键模拟 legacy 面板: 现算不回写、不报漂移、口径标注 legacy
        panel.pop("denominator_freeze")
        st2 = cp.compute_stats(panel)
        self.assertIs(st2["frozen"]["drift"], False)
        self.assertEqual(st2["frozen"]["panel_freeze_stored"], None)
        self.assertIn("legacy 面板未冻结", cp.render_report(panel, st2))


class PairedDiffTests(unittest.TestCase):
    """N6: 探针指纹 + 同 prompt×engine 配对门 + 未配对单列不入 Δ。"""

    def test_record_stores_fingerprint(self):
        """record 写 run['fingerprint'];同 engine+brand+prompt 集稳定;
        run 覆盖 prompt 集变化 → 指纹变(prompt 集变的面板变化由 N5 hash 捕获)。"""
        tmp = tempfile.mkdtemp(prefix="nb_n6_")
        panel_path = os.path.join(tmp, "panel.json")
        self.assertEqual(run_script("citation_panel.py", [
            "init", "--brand", "Acme", "--domain", "acme.ai",
            "--prompts-file", _write(tmp, "p.csv", "prompt\nk1\nk2\n"),
            "--panel", panel_path]).returncode, 0)
        csv1 = _write(tmp, "r1.csv", "prompt,mentioned,cited,cited_urls\nk1,1,0,\nk2,0,0,\n")
        self.assertEqual(run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file", csv1, "--date",
            "2026-10-01T00:00:00", "--panel", panel_path]).returncode, 0)
        csv2 = _write(tmp, "r2.csv", "prompt,mentioned,cited,cited_urls\nk1,0,0,\nk2,1,0,\n")
        self.assertEqual(run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file", csv2, "--date",
            "2026-10-08T00:00:00", "--panel", panel_path]).returncode, 0)
        with open(panel_path, encoding="utf-8") as f:
            panel = json.load(f)
        r1, r2 = panel["runs"]
        self.assertEqual(len(r1["fingerprint"]), 16)
        self.assertEqual(r1["fingerprint"], r2["fingerprint"])   # 同 scope → 同指纹
        # 不同 prompt 集 → 指纹变
        ra = make_run("chatgpt", "d", {"k1": res(1, 0)})
        rb = make_run("chatgpt", "d", {"k1": res(1, 0), "k9": res(0, 0)})
        self.assertNotEqual(cp.run_fingerprint(ra), cp.run_fingerprint(rb))
        # 已存指纹直读(不重算)
        self.assertEqual(cp.run_fingerprint(dict(ra, fingerprint="ff"*8)), "ff"*8)

    def test_pairing_gate_engine_and_fingerprint(self):
        """只对同 prompt×engine 且同指纹的配对可比;未配对按原因单列不入 Δ;
        旧 excluded 计数键保留。"""
        ra = make_run("chatgpt", "2026-10-01T00:00:00", {
            "p1": res(1, 0),
            "p2": res(0, 0, state="failed"),          # run1 采集失败
            "p3": res(1, 0)})
        rb = make_run("chatgpt", "2026-10-08T00:00:00", {
            "p1": res(0, 0),
            "p2": res(0, 0),
            "p4": res(1, 0)})                          # 仅 run2 有
        d = cp.diff_runs(ra, rb)
        self.assertEqual(d["paired"], ["p1"])          # 只有 p1 真配对 → Δ 只算 p1
        self.assertEqual(d["k1"], 1)
        self.assertEqual(d["k2"], 0)
        # 旧计数口径: run1 侧排除 = p2(failed)+p4(缺);run2 侧排除 = p3(缺)
        self.assertEqual(d["excluded"], {"missing_in_a": 2, "missing_in_b": 1})
        self.assertEqual(d["unpaired"]["only_in_run1"], ["p3"])
        self.assertEqual(d["unpaired"]["only_in_run2"], ["p4"])
        self.assertEqual(d["unpaired"]["failed_in_run1"], ["p2"])
        self.assertEqual(d["engine_matched"], True)
        self.assertFalse(d["comparable"])              # prompt 集不同 → 指纹不同
        # 同引擎同 prompt 集 → 可比(paired 源自 set 迭代,排序后断言)
        rc = make_run("chatgpt", "2026-10-08T00:00:00",
                      {"p1": res(0, 0), "p2": res(0, 0), "p3": res(0, 0)})
        d2 = cp.diff_runs(ra, rc)
        self.assertTrue(d2["comparable"])
        self.assertEqual(sorted(d2["paired"]), ["p1", "p3"])   # p2 failed 仍单列不入 Δ
        # 跨引擎 → engine_matched=False → 不可比
        d3 = cp.diff_runs(ra, dict(rc, engine="perplexity"))
        self.assertFalse(d3["engine_matched"])
        self.assertFalse(d3["comparable"])
        self.assertTrue(d3["fingerprint_a"] != d3["fingerprint_b"])

    def test_diff_cli_discipline_section(self):
        """CLI diff 输出配对差分纪律节: 可比/不可比标注、指纹一致性、
        未配对单列(不入 Δ);[signal] 行跨口径时带 [不可比]。"""
        tmp = tempfile.mkdtemp(prefix="nb_n6c_")
        prompts = ["p%d" % i for i in range(12)]
        ra = make_run("chatgpt", "2026-10-01T00:00:00",
                      {p: res(1, 0) for p in prompts})
        rb = make_run("chatgpt", "2026-10-08T00:00:00",
                      {p: res(0, 0) for p in prompts})
        panel = dict(PANEL, prompts=prompts, runs=[ra, rb])
        path = setup_panel(tmp, panel)
        r = run_script("citation_panel.py", ["diff", ra["run_id"], rb["run_id"],
                                             "--panel", path])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("配对差分纪律(niubigeo-deep-read.md N6", r.stdout)
        self.assertIn("可比: 是(同引擎+同指纹)", r.stdout)
        self.assertIn("(一致;同指纹≠范围一致", r.stdout)
        self.assertIn("未配对单列(0,不入 Δ): 无", r.stdout)
        # 跨引擎 → 不可比标注 + signal 行带 [不可比]
        rc = make_run("perplexity", "2026-10-08T00:00:00",
                      {p: res(0, 0) for p in prompts})
        path2 = setup_panel(tempfile.mkdtemp(prefix="nb_n6d_"),
                            dict(PANEL, prompts=prompts, runs=[ra, rc]))
        r2 = run_script("citation_panel.py", ["diff", ra["run_id"], rc["run_id"],
                                              "--panel", path2])
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("[!] 不可比(跨引擎", r2.stdout)
        self.assertIn("不下结论", r2.stdout)
        self.assertIn("[不可比]", r2.stdout)
        # 未配对单列: run2 缺 p0(仅 run1)+ p1 在 run2 采集失败
        rd = make_run("chatgpt", "2026-10-08T00:00:00",
                      {p: (res(0, 0, state="failed") if p == "p1" else res(0, 0))
                       for p in prompts[1:]})
        path3 = setup_panel(tempfile.mkdtemp(prefix="nb_n6e_"),
                            dict(PANEL, prompts=prompts, runs=[ra, rd]))
        r3 = run_script("citation_panel.py", ["diff", ra["run_id"], rd["run_id"],
                                              "--panel", path3])
        self.assertEqual(r3.returncode, 0, r3.stderr)
        self.assertIn("未配对单列(2,不入 Δ)", r3.stdout)
        self.assertIn("仅run1=p0", r3.stdout)
        self.assertIn("run2失败=p1", r3.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
