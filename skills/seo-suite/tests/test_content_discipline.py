#!/usr/bin/env python3
"""content_score.py / quality_rater.py 纪律层测试(借鉴 niubigeo;出处逐条标注
references/research/niubigeo-deep-read.md §3"值得抄 Top 10"):

  N7 observed-consensus/v1 词筛(content_score): ≥2 独立竞品精确定位才进推荐;
      单竞品独有词单列"低置信"展示不进推荐;四类落选码全留档
      (contains_observed_identity / no_exact_answer_evidence /
       insufficient_independent_association / not_neutral_eligible);
      共识率无候选 → null 不能计算(不报 0%)
  N8 D/K 分报(两脚本): D(点名声明)≠K(中性观察)各留分母、分率永不混算;
      分母=0 → rate/count=null 永不报 0%;pointState=complete/partial/no_data;
      content_score --facts 行首 D:/K: 前缀分级,未标注按 K,两类混入同一
      facts_coverage 分数时发混算警告;quality_rater 证据节 D=引语/链接、
      K=裸数字,引语内数字归 D 不重复计 K("复述已点名的内容不能算中性观察")
  N9 UTF-16 证据核验(quality_rater): 偏移=UTF-16 code unit(BMP=1,增补平面=2);
      核验条件 raw.slice(start,end)===quote,失败 → evidence=null 不虚构偏移;
      同文多次出现取首次精确匹配;recordHash=sha256(无缩进无分隔空格的紧凑 JSON);
      编码级假证据扫描: 孤立代理字符/西里尔·希腊同形拉丁/全角数字·字母——
      同形字对干净源文的 UTF-16 精确匹配必败

向后兼容契约(任务指示:分数不变——新纪律是警告/标注层而非改分):
  * content_score 默认 --json 顶层键集与冻结 fixture(tests/fixtures/scoring_v1.json)
    逐键一致;--discipline 才追加 discipline 键,且 seo/ai/total/term_table/
    missing_terms/notes 与不带开关时逐字节相等;D:/K: 前缀不改变覆盖分数;
  * quality_rater 证据纪律节不改六维分数/critical/publishing_ready/退出码
    (± --evidence-source 输出的评分前缀逐行相等;零 critical 文档带同形字
    风险仍 critical:无、publishing_ready: YES、退出码 0)。

standalone(自带 run_script 助手,合成数据,零网络):
python3 tests/test_content_discipline.py
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

import content_score as cs   # noqa: E402  (需先入 SCRIPTS 路径)
import quality_rater as qr   # noqa: E402


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content, suffix=".md"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---- 中文合成语料: 3 个不同来源竞品 + 1 份有缺口的草稿 ----
KW = "项目管理软件"
C1 = ("项目管理软件是团队协作的核心工具。简而言之,选型先看甘特图与任务分配。\n"
      "2026 年主流工具超过 40 款,资源负载与工时统计决定付费价值。\n")
C2 = ("项目管理软件对比盘点:任务分配、甘特图与时间跟踪是三大主线。\n"
      "工时统计报表支撑成本核算;独家专有词「鲲鹏独门算法」只在本源出现。\n")
C3 = ("如何挑选项目管理软件:先看任务分配与看板,再看甘特图。\n"
      "工时统计与资源负载视图决定成本核算质量。\n")
DRAFT = ("# 协作工具漫谈\n\n"
         "协作工具有很多门道,值得慢慢展开讨论,这里先聊一些背景与想法。\n"
         "下文再谈预算、会议与文档的一些观察,供参考。\n")


def _cs_files():
    return (tmp_file(C1), tmp_file(C2), tmp_file(C3), tmp_file(DRAFT))


# ================================================================ N7 词筛
class ConsensusFilterTests(unittest.TestCase):
    """observed-consensus/v1 边界: 阈值 2/身份子串/零定位/单源低置信/null 共识率"""

    TERMS = [{"term": "工时统计", "importance": 10, "freqs": [1, 1, 1]},
             {"term": "甘特图", "importance": 7, "freqs": [2, 1, 0]},
             {"term": "鲲鹏独门算法", "importance": 4, "freqs": [0, 3, 0]},
             {"term": "外来词", "importance": 5, "freqs": [0, 0, 0]},
             {"term": KW, "importance": 10, "freqs": [1, 1, 1]},
             {"term": KW + "选型", "importance": 10, "freqs": [1, 1, 0]}]
    COMPS = ["项目管理软件看甘特图与工时统计",
             "项目管理软件选型对比,甘特图与鲲鹏独门算法、工时统计",
             "工时统计支撑成本核算"]

    def _filter(self, keyword=KW):
        return cs.observed_consensus(self.TERMS, self.COMPS, keyword)

    def test_threshold_and_exclusion_codes(self):
        """≥2 源进 kept(恰 2 源也算共识);单源 → insufficient_independent_association
        (低置信单列);零定位 → no_exact_answer_evidence;候选与落选全留档。"""
        r = self._filter()
        kept = {k["term"]: k["observed_sources"] for k in r["kept"]}
        self.assertEqual(kept, {"工时统计": 3, "甘特图": 2})
        codes = {e["term"]: e["code"] for e in r["excluded"]}
        self.assertEqual(codes["鲲鹏独门算法"], "insufficient_independent_association")
        self.assertEqual(codes["外来词"], "no_exact_answer_evidence")
        low = {e["term"] for e in r["low_confidence"]}
        self.assertEqual(low, {"鲲鹏独门算法"})            # 单竞品独有 → 低置信单列
        self.assertEqual(r["n_candidates"], len(self.TERMS))
        self.assertEqual(len(r["kept"]) + len(r["excluded"]), r["n_candidates"])

    def test_identity_exclusion_priority(self):
        """与主词全等 → not_neutral_eligible;命中主词子串 → contains_observed_identity
        ——即使该词观察源 ≥2(共识达标)也排除:身份词不是独立观察话题。"""
        r = self._filter()
        codes = {e["term"]: e["code"] for e in r["excluded"]}
        self.assertEqual(codes[KW], "not_neutral_eligible")
        self.assertEqual(codes[KW + "选型"], "contains_observed_identity")
        self.assertNotIn(KW + "选型", [k["term"] for k in r["kept"]])

    def test_consensus_rate_null_semantics(self):
        """N8 null 纪律: 无候选 → consensus_rate=None(不能计算,不报 0%);
        有候选 → float;kept 按观察源数降序。"""
        r = self._filter()
        self.assertIsInstance(r["consensus_rate"], float)
        sources = [k["observed_sources"] for k in r["kept"]]
        self.assertEqual(sources, sorted(sources, reverse=True))
        empty = cs.observed_consensus([], [], KW)
        self.assertIsNone(empty["consensus_rate"])
        self.assertEqual(empty["n_candidates"], 0)

    def test_low_confidence_displayed_not_recommended(self):
        """端到端: 单竞品独有词被识别为低置信、进"低置信"展示、绝不在推荐层;
        多源共识词(草稿缺失)进推荐层;markdown 推荐层区块同样不含低置信词。"""
        a, b, c, d = _cs_files()
        try:
            base = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
            j = json.loads(run_script("content_score.py", base + ["--json", "--discipline"]).stdout)
            disc = j["discipline"]
            low = {e["term"] for e in disc["term_consensus"]["low_confidence"]}
            recs = {r2["term"] for r2 in disc["recommendation"]}
            self.assertIn("鲲鹏独门算法", low)             # 单竞品独有词 → 低置信(单列展示)
            self.assertFalse(low & recs, "低置信词不得进推荐层: %s" % (low & recs))
            self.assertTrue(any(t in recs for t in ("任务分配", "工时统计", "甘特图")))
            r = run_script("content_score.py", base)    # markdown 报告
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("observed-consensus/v1", r.stdout)
            self.assertIn("低置信(单竞品独有", r.stdout)
            self.assertIn("insufficient_independent_association", r.stdout)  # 留档不黑箱
            rec_zone, in_rec = [], False
            for ln in r.stdout.splitlines():
                if "推荐层(仅共识词" in ln:
                    in_rec = True
                    continue
                if in_rec and ln.startswith("- "):
                    break
                if in_rec:
                    rec_zone.append(ln)
            self.assertTrue(rec_zone, "推荐层为空——共识词×草稿缺失应有推荐项")
            self.assertFalse(any(any(t in ln for t in low) for ln in rec_zone),
                             "markdown 推荐层不得出现低置信词")
        finally:
            for p in (a, b, c, d):
                os.unlink(p)

    def test_terms_file_foreign_word_excluded_via_json(self):
        """--terms 外来词(竞品正文零定位)→ no_exact_answer_evidence,
        --discipline JSON 的 excluded 留档可机读。"""
        a, b, c, d = _cs_files()
        tj = tmp_file(json.dumps({"terms": [
            {"term": "甘特图", "importance": 9},
            {"term": "量子涨落虚词", "importance": 5},
            {"term": KW, "importance": 10}]}, ensure_ascii=False), suffix=".json")
        try:
            r = run_script("content_score.py", ["--draft", d, "--competitors", ",".join([a, b, c]),
                            "--terms", tj, "--keyword", KW, "--json", "--discipline"])
            p = json.loads(r.stdout)
            tc = p["discipline"]["term_consensus"]
            codes = {e["term"]: e["code"] for e in tc["excluded"]}
            self.assertEqual(codes["量子涨落虚词"], "no_exact_answer_evidence")
            self.assertEqual(codes[KW], "not_neutral_eligible")
            self.assertIn("甘特图", [k["term"] for k in tc["kept"]])
        finally:
            for p in (a, b, c, d, tj):
                os.unlink(p)


# ================================================================ N8 D/K(content_score)
class FactsDKTests(unittest.TestCase):
    """D/K 事实分级: 行首前缀解析 / 分报各留分母 / null 纪律 / 混算警告 / 分数不变"""

    def test_fact_line_parsing(self):
        """D:/K: 前缀(全角冒号兼容)→ 分级;未标注 → K[推断];空行/注释 → None;
        列表标记剥除后前缀仍识别;前缀剥除不渗入事实文本。"""
        self.assertEqual(cs.parse_fact_line("D: 官方声明工时统计是核心"),
                         ("D", "官方声明工时统计是核心"))
        self.assertEqual(cs.parse_fact_line("K: 中性观察甘特图可视化"),
                         ("K", "中性观察甘特图可视化"))
        self.assertEqual(cs.parse_fact_line("D：全角冒号声明"), ("D", "全角冒号声明"))
        self.assertEqual(cs.parse_fact_line("- 未标注的列表事实"),
                         ("K", "未标注的列表事实"))
        self.assertEqual(cs.parse_fact_line("普通行"), ("K", "普通行"))
        self.assertIsNone(cs.parse_fact_line("# 注释"))
        self.assertIsNone(cs.parse_fact_line("   "))
        self.assertIsNone(cs.parse_fact_line(""))

    def test_dk_split_report_and_mixing_warning(self):
        """D 与 K 混入: stats 两类各留分母、分率分报;pointState=complete;
        混算警告触发(N8:单一 facts_coverage 不拆分是向后兼容,警告即纪律);
        事实覆盖 note 仍为"--facts 清单 N 条"口径(计分未被分级改变)。"""
        a, b, c, d = _cs_files()
        fj = tmp_file("D: 官方声明甘特图可视化里程碑\nK: 工时统计支撑成本核算\n"
                      "未标注中性事实一句\n", suffix=".md")
        try:
            r = run_script("content_score.py", ["--draft", d, "--competitors", ",".join([a, b, c]),
                            "--keyword", KW, "--facts", fj, "--json", "--discipline"])
            p = json.loads(r.stdout)
            fd = p["discipline"]["facts_dk"]
            self.assertEqual(fd["protocol"], "dk-facts/v1")
            self.assertEqual(fd["facts_source"], "explicit")
            self.assertEqual(fd["stats"]["D"]["n"], 1)
            self.assertEqual(fd["stats"]["K"]["n"], 2)   # 未标注按 K
            self.assertEqual(fd["point_state"], "complete")
            self.assertTrue(any("混算" in w for w in fd["warnings"]))
            self.assertIn("--facts 清单 3 条",
                          p["ai"]["dims"]["facts_coverage"]["note"])
        finally:
            for p in (a, b, c, d, fj):
                os.unlink(p)

    def test_dk_null_rate_and_partial_state(self):
        """全 K 清单: D 分母=0 → rate=null(永不报 0%),pointState=partial,
        无混算警告;无 --facts 走代理全 K 并注明。"""
        a, b, c, d = _cs_files()
        fj = tmp_file("甘特图可视化里程碑\n工时统计支撑成本核算\n", suffix=".md")
        try:
            base = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
            p = json.loads(run_script("content_score.py", base + ["--facts", fj, "--json", "--discipline"]).stdout)
            fd = p["discipline"]["facts_dk"]
            self.assertEqual(fd["stats"]["D"], {"n": 0, "covered": 0, "rate": None})
            self.assertEqual(fd["point_state"], "partial")
            self.assertFalse(any("混算" in w for w in fd["warnings"]))
            p2 = json.loads(run_script("content_score.py", base + ["--json", "--discipline"]).stdout)
            fd2 = p2["discipline"]["facts_dk"]
            self.assertEqual(fd2["facts_source"], "proxy")
            self.assertIsNone(fd2["stats"]["D"]["rate"])
            self.assertEqual(fd2["point_state"], "partial")
            self.assertTrue(any("事实代理" in w for w in fd2["warnings"]))
        finally:
            for p in (a, b, c, d, fj):
                os.unlink(p)

    def test_dk_prefix_does_not_change_score(self):
        """分数不变断言: 同一批事实文本,行首加不加 D:/K: 前缀,
        facts_coverage 分数与总分完全一致(前缀剥除不渗入 tokenize)。"""
        a, b, c, d = _cs_files()
        plain = tmp_file("协作工具有很多门道\n甘特图可视化里程碑\n", suffix=".md")
        tagged = tmp_file("D: 协作工具有很多门道\nK: 甘特图可视化里程碑\n", suffix=".md")
        try:
            base = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
            j1 = json.loads(run_script("content_score.py", base + ["--facts", plain, "--json"]).stdout)
            j2 = json.loads(run_script("content_score.py", base + ["--facts", tagged, "--json"]).stdout)
            self.assertEqual(j1["ai"]["dims"]["facts_coverage"]["score"],
                             j2["ai"]["dims"]["facts_coverage"]["score"])
            self.assertEqual(j1["total"], j2["total"])
            self.assertEqual(j1["seo"]["score"], j2["seo"]["score"])
        finally:
            for p in (a, b, c, d, plain, tagged):
                os.unlink(p)


# ================================================================ 向后兼容契约(content_score)
class DisciplineBackcompatTests(unittest.TestCase):
    """默认 --json 与冻结 fixture 键集一致;--discipline 只增不改且分数逐字节不变"""

    FIXTURE_TOP_KEYS = {"schema_version", "keyword", "intent", "intent_coefficient",
                        "intent_note", "density_scored", "term_model", "seo", "ai",
                        "total", "band", "band_range", "target", "term_table",
                        "missing_terms", "notes"}

    def test_default_json_unchanged_discipline_optin(self):
        """默认 --json: 无 discipline 键、顶层键集与 fixture 冻结键集一致;
        --discipline 才追加(只增不改)。"""
        a, b, c, d = _cs_files()
        try:
            base = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
            p1 = json.loads(run_script("content_score.py", base + ["--json"]).stdout)
            self.assertNotIn("discipline", p1)
            self.assertEqual(set(p1), self.FIXTURE_TOP_KEYS)
            p2 = json.loads(run_script("content_score.py", base + ["--json", "--discipline"]).stdout)
            self.assertEqual(set(p2), self.FIXTURE_TOP_KEYS | {"discipline"})
            self.assertEqual(sorted(p2["discipline"]),
                             ["facts_dk", "recommendation", "term_consensus"])
        finally:
            for p in (a, b, c, d):
                os.unlink(p)

    def test_discipline_flag_score_invariance(self):
        """分数不变断言: ± --discipline 的 seo/ai/total/term_table/missing_terms/
        notes/target 逐字节相等(标注层不碰计分)。"""
        a, b, c, d = _cs_files()
        try:
            base = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
            p1 = json.loads(run_script("content_score.py", base + ["--json"]).stdout)
            p2 = json.loads(run_script("content_score.py", base + ["--json", "--discipline"]).stdout)
            for k in ("seo", "ai", "total", "band", "term_table", "missing_terms",
                      "notes", "target", "term_model"):
                self.assertEqual(p1[k], p2[k], "discipline 开关改变了 %s" % k)
        finally:
            for p in (a, b, c, d):
                os.unlink(p)


# ================================================================ N9 UTF-16(quality_rater)
class UTF16EvidenceTests(unittest.TestCase):
    """UTF-16 code unit 偏移 / 首次精确匹配 / 不虚构偏移 / recordHash 紧凑 JSON 口径"""

    def test_utf16_unit_len_and_slice(self):
        """BMP=1 单元、增补平面=2 单元;切片按 code unit;越界 → None;
        切在代理对中间得到孤立代理字符(JS 同口径)→ 与正常引语 === 比较必败。"""
        self.assertEqual(qr.utf16_unit_len("汉a"), 2)
        self.assertEqual(qr.utf16_unit_len("a\U0001F600b"), 4)      # emoji=2 单元
        self.assertEqual(qr.utf16_slice("a\U0001F600b", 1, 3), "\U0001F600")
        self.assertEqual(qr.utf16_slice("汉字ab", 0, 2), "汉字")
        self.assertIsNone(qr.utf16_slice("ab", 0, 5))               # 越界不虚构
        self.assertIsNone(qr.utf16_slice("ab", 2, 1))               # end<start
        mid_pair = qr.utf16_slice("a\U0001F600b", 1, 2)             # 切在代理对中间
        self.assertIsNotNone(mid_pair)
        self.assertNotEqual(mid_pair, "\U0001F600")

    def test_verify_and_locate_first_evidence(self):
        """核验条件 slice(start,end)===quote;失败 → None(evidence=null 不虚构偏移);
        同文多次出现取首次精确匹配;增补平面文本偏移按 code unit 换算。"""
        raw = "前言。专家指出「工具决定效率」,后文又引「工具决定效率」收尾。"
        start, end = qr.locate_first_evidence(raw, "「工具决定效率」")
        self.assertEqual(qr.verify_evidence_location(raw, start, end, "「工具决定效率」"),
                         "「工具决定效率」")
        self.assertIn("指出", qr.utf16_slice(raw, 0, start))        # 首次: 偏移在前半文
        self.assertIsNone(qr.verify_evidence_location(raw, start, end, "「别的引语」"))
        self.assertIsNone(qr.locate_first_evidence(raw, "「不存在引语」"))
        raw2 = "\U0001F600 报告称「增长 30%」"
        s2, e2 = qr.locate_first_evidence(raw2, "「增长 30%」")
        self.assertEqual(qr.utf16_slice(raw2, s2, e2), "「增长 30%」")

    def test_record_hash_compact_json(self):
        """recordHash=sha256(JSON.stringify(value)): 无缩进、无分隔空格、无末尾换行;
        ensure_ascii=False(非 ASCII 不转义);稳定可复算、与缩进口径可区分。"""
        import hashlib
        val = {"text": "「增长 30%」", "start": 5, "end": 13}
        expected = hashlib.sha256(
            '{"text":"「增长 30%」","start":5,"end":13}'.encode("utf-8")).hexdigest()
        self.assertEqual(qr.record_hash(val), expected)
        self.assertEqual(qr.record_hash(dict(val)), qr.record_hash(val))
        indented = hashlib.sha256(
            json.dumps(val, ensure_ascii=False, indent=1).encode("utf-8")).hexdigest()
        self.assertNotEqual(qr.record_hash(val), indented)


# ================================================================ N8+N9 证据纪律节(quality_rater)
class EvidenceDisciplineTests(unittest.TestCase):
    """D/K 证据分级 / 同形字与代理字符检出 / 源文核验 / 标注层不改分数与退出码"""

    def test_homoglyph_and_surrogate_scan(self):
        """全角数字 → fullwidth_digit(同形对象逐字留档,重复字符去重);
        西里尔同形拉丁 → confusable_script;孤立代理字符 → lone_surrogate;
        干净元素零风险。"""
        fw = qr.scan_evidence_risks("１００")           # １ 与 ０(重复字符去重)
        self.assertEqual([r["code"] for r in fw],
                         ["fullwidth_digit", "fullwidth_digit"])
        self.assertEqual([r["resembles"] for r in fw], ["1", "0"])
        self.assertEqual([r["code"] for r in qr.scan_evidence_risks("https://аpple.com")],
                         ["confusable_script"])          # 西里尔 а 同形 a
        self.assertEqual([r["code"] for r in qr.scan_evidence_risks("wоrd")],
                         ["confusable_script"])          # 西里尔 о 同形 o
        self.assertEqual([r["code"] for r in qr.scan_evidence_risks("\ud800x")],
                         ["lone_surrogate"])             # 代理字符不可编码 UTF-8
        self.assertEqual(qr.scan_evidence_risks("100% normal 汉字"), [])
        self.assertEqual(qr.scan_evidence_risks("ＡＰＩ")[0]["code"], "fullwidth_letter")

    def test_evidence_dk_classification_and_point_state(self):
        """引语/链接 → D;裸数字 → K;引语内数字归 D 不重复计 K;pointState 三态。"""
        ev = qr.build_evidence_discipline(
            "专家指出「增长 30%」;细节见 https://e.com/a 。主流工具 40 款,均价 15 元。")
        self.assertEqual(ev["dk"]["D"]["n"], 2)          # 引语 + 链接
        self.assertEqual(ev["dk"]["K"]["n"], 2)          # 40 / 15(30% 在引语内归 D)
        self.assertEqual(ev["point_state"], "complete")
        only_k = qr.build_evidence_discipline("增长 30%,共 40 款。")
        self.assertEqual(only_k["dk"]["D"]["n"], 0)
        self.assertEqual(only_k["dk"]["K"]["n"], 2)
        self.assertEqual(only_k["point_state"], "partial")
        none = qr.build_evidence_discipline("没有任何证据元素的一句话。")
        self.assertEqual(none["point_state"], "no_data")
        self.assertIsNone(none["verification"])         # 无源文 → 跳过定位核验

    def test_verification_against_source(self):
        """同形字假证据对干净源文定位必败(evidence=null 不虚构偏移);
        干净引语/数字定位精确并带 record_hash 与 UTF-16 偏移;
        孤立代理字符元素同样不定位、不虚构。"""
        src = "调研原始记录:增长 30%,共 40 款。「工具决定效率」出自访谈。"
        draft = "报告称增长 3０%(全角零),共 40 款,专家说「工具决定效率」。"
        ev = qr.build_evidence_discipline(draft, source_text=src)
        v = ev["verification"]
        self.assertEqual(v["n"], 4)                      # K: "3"/"０"/"40" + D: 引语
        recs = {(r["kind"], r["text"]) for r in v["records"]}
        self.assertIn(("quote", "「工具决定效率」"), recs)
        self.assertIn(("number", "40"), recs)
        self.assertIn(("number", "3"), recs)             # "3" 是 "30%" 的子串,可首次定位
        self.assertEqual({u["text"] for u in v["unverified"]}, {"０"})
        for r in v["records"]:
            self.assertTrue(r["record_hash"])
            self.assertLessEqual(r["start"], r["end"])
            self.assertEqual(qr.utf16_slice(src, r["start"], r["end"]), r["text"])
        # 孤立代理字符: 源文必无此串 → not_located, 不虚构偏移
        ev3 = qr.build_evidence_discipline("声称「数据\ud800０可信」", source_text=src)
        self.assertEqual(ev3["verification"]["verified"], 0)
        self.assertTrue(all(u["reason"] == "not_located"
                            for u in ev3["verification"]["unverified"]))

    def test_cli_flag_score_invariance(self):
        """分数不变断言: ± --evidence-source 两次运行, 评分部分(至 publishing_ready 行)
        逐行相同、退出码相同;证据纪律节只在评分之后追加。"""
        d = tmp_file("项目管理软件选型\n工时统计显示 40 款工具,「效率决定交付」。\n"
                     "见 https://e.com/a 与 https://e.com/b 。\n", suffix=".txt")
        s = tmp_file("原始记录:40 款工具。「效率决定交付」见 https://e.com/a 。\n",
                     suffix=".txt")
        try:
            r1 = run_script("quality_rater.py",
                            [d, "--market", "zh", "--keyword", "项目管理软件"])
            r2 = run_script("quality_rater.py",
                            [d, "--market", "zh", "--keyword", "项目管理软件",
                             "--evidence-source", s])
            self.assertEqual(r1.returncode, r2.returncode)
            self.assertEqual(r1.stdout.split("publishing_ready:")[0],
                             r2.stdout.split("publishing_ready:")[0])
            self.assertIn("publishing_ready:", r1.stdout)
            self.assertIn("证据纪律节", r1.stdout)       # 无源文也恒出证据节
            self.assertIn("未提供 --evidence-source", r1.stdout)
            self.assertIn("UTF-16 定位核验", r2.stdout)
            self.assertIn("record_hash=", r2.stdout)
        finally:
            os.unlink(d)
            os.unlink(s)

    def test_annotation_never_touches_critical_or_exit(self):
        """零六维 critical 的文档带同形字/西里尔链接风险: critical:无、
        publishing_ready: YES、退出码 0——风险只出现在证据纪律节(标注层)。"""
        title = ("项目管理软件选型指南" * 8)[:55]        # 55 字符 → meta 满分区间
        parts = ["项目管理软件的选型直接影响团队交付节奏。"]
        fillers = ["团队协作效率取决于工具链与流程的清晰程度。",
                   "预算规划应覆盖许可证费用与培训成本两部分。",
                   "数据迁移前要完成字段映射评审与回滚预案。"]
        for i in range(1, 6):
            parts.append("## 选型维度%d" % i)
            for j in range(28):
                parts.append(fillers[(i + j) % 3])
        parts.append("- 预算分三批购齐,先核心后外围")
        parts.append("行业暗线称 ２０２６ 年渗透率 １００%(全角数字)值得关注。")
        parts.append("仿冒链接 https://аpple.com/example 与 https://e.com/a "
                     "以及 https://e.com/b 仅供参考。")
        d = tmp_file(title + "\n" + "\n".join(parts) + "\n", suffix=".txt")
        try:
            r = run_script("quality_rater.py",
                           [d, "--market", "zh", "--keyword", "项目管理软件"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("critical: 无", r.stdout)
            self.assertIn("publishing_ready: YES", r.stdout)
            self.assertIn("证据纪律节", r.stdout)
            self.assertIn("全角数字", r.stdout)          # 风险只在标注层出现(标签为中文)
            self.assertIn("同形拉丁", r.stdout)
            crit_zone = r.stdout.split("critical")[1].split("publishing_ready")[0]
            self.assertNotIn("同形字", crit_zone)
            self.assertNotIn("代理字符", crit_zone)
        finally:
            os.unlink(d)

    def test_safe_text_escapes_lone_surrogates(self):
        """展示层防御: 孤立代理字符转义为 \\uXXXX(print 到 UTF-8 stdout 不炸)。"""
        self.assertEqual(qr._safe_text("数据\ud800可信"), "数据\\ud800可信")
        self.assertEqual(qr._safe_text("正常汉字ab"), "正常汉字ab")


if __name__ == "__main__":
    unittest.main(verbosity=1)
