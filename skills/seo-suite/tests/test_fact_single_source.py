#!/usr/bin/env python3
"""事实单一来源看门(2026-10-24)。

references/overview/facts.md 收了 11 类在多个文件里反复出现的外部事实(CWV 阈值、
CrUX 窗口、GSC 数据异常期、FAQ/HowTo 富结果退役日期、GSC 生成式 AI 报告日期、
GSC 数据保留期、sitemap 上限、Googlebot 抓取上限、API 配额、IndexNow 单批上限、
搜索引擎份额)。其他文件只链接事实表,不再各写一份数字。

本测试做四件事:
1. 主扫描:SKILL.md、references/**、templates/** 逐行扫,除事实表和 ALLOW 里的文件外,
   命中任一 FACT_PATTERNS 即红,并列出 文件:行号:匹配串。
   例外:搜索引擎份额允许出现在 references/markets/*.md(该市场的明细表)。
2. 正则自检:每条正则命中全部 bad 样例、放过全部 ok 样例(与 test_canonical_facts 同一契约)。
3. 事实表自身:每类都有锚点、值、一手来源 URL、核对日期;别的文件里指向
   facts.md#xxx 的锚点都存在。
4. 一致性:事实表的值与脚本常量相等(field_data、did_attribution、sitemap_audit、
   indexnow、gsc_api);份额值与对应市场文件一致;脚本文字里的 GSC 异常期结束日与表一致。

standalone、零网络:`python3 tests/test_fact_single_source.py`;被 tests/run_tests.py 发现。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(SUITE_ROOT, "scripts")
FACTS_REL = os.path.join("references", "overview", "facts.md")
FACTS = os.path.join(SUITE_ROOT, FACTS_REL)
SCAN_ROOTS = [os.path.join(SUITE_ROOT, p) for p in ("SKILL.md", "references", "templates")]

# 不扫的文件:事实表本身;按当时原文保留的历史核对记录。
ALLOW = {
    FACTS_REL,
    os.path.join("references", "overview", "freshness-log-20261011.md"),
}
MARKETS_DIR = os.path.join("references", "markets") + os.sep
# 别的搜索引擎自己文档写的同值上限(Naver、Yandex 的 sitemap / IndexNow 规则)不是 Google 事实,不拦。
OTHER_ENGINE = re.compile(r"Naver|Yandex|Яндекс|네이버|Search Advisor|searchadvisor|Вебмастер|Webmaster「", re.I)
OTHER_ENGINE_OK = {"sitemap-limits", "indexnow-batch"}
# 引擎名后跟的百分比是检索率、引用率等别的指标时不是份额。
NOT_SHARE = re.compile(r"检索率|引用率|出现率|使用率|触发率|点击率|retrieval rate|citation rate")

_DAY = r"(?:天|日|-day| day|days)"
_MON = r"(?:个月|months?)"

# ------------------------------------------------------------- 正则本体 --
FACT_PATTERNS = {
    "cwv": (
        r"(?:LCP|Largest Contentful Paint)[^\n。|]{0,25}?(?:2\.5 ?(?:s|秒)|2,?500 ?ms|(?<![\d.])4(?:\.0)? ?(?:s|秒))"
        r"|INP[^\n。|]{0,25}?(?<![\d.])(?:200|500) ?(?:ms|毫秒)"
        r"|CLS[^\n。|]{0,25}?(?<![\d.])0\.(?:1|25)(?![\d])"
        r"|≤ ?(?:2,?500 ?ms|2\.5 ?(?:s|秒)|200 ?ms|0\.1(?![\d]))",
        "CWV 阈值只写在事实表 #cwv;引用时写「良好 / 差档(见事实表)」"),
    "crux-window": (
        r"(?:CrUX|Chrome UX|现场数据|field data)[^\n。]{0,40}?28 ?" + _DAY
        + r"|28 ?" + _DAY + r"[^\n。]{0,6}(?:滚动|滑动|rolling)",
        "CrUX 28 天滚动窗口只写在事实表 #crux-window"),
    "gsc-anomaly": (
        r"2025-05-13|2026-04-27",
        "GSC 展示数据异常期只写在事实表 #gsc-anomaly"),
    "rich-results": (
        r"(?:FAQ|富结果|rich result)[^\n。]{0,60}?2026-05-0[78]|2026-05-0[78][^\n。]{0,30}?(?:FAQ|富结果|rich result)"
        r"|FAQ[^\n。]{0,60}?2026-06-15|2023-08-08|(?:HowTo|How-to)[^\n。]{0,60}?2023-09-1[34]|2023-09-1[34][^\n。]{0,30}?(?:HowTo|How-to)"
        r"|(?:FAQ|HowTo|How-to)[^\n。]{0,40}?2023-0?[89]\b",
        "FAQ / HowTo 富结果退役日期只写在事实表 #rich-results"),
    "gsc-genai": (
        r"(?:生成式 ?AI|Generative AI|generative AI|AI 效果报告|AI 表现报告|AI Performance|gen-?AI)"
        r"[^\n。]{0,160}?(?:2026-06-03|2026-08-31)"
        r"|(?:Search Console|GSC|效果报告|帮助页|博文|博客|控制)[^\n。]{0,40}?(?:2026-06-03|2026-08-31)"
        r"|(?:2026-06-03|2026-08-31)[^\n。]{0,40}?(?:生成式|Generative|全球开放|全球上线|全部站点|所有站点|all (?:sites|websites))",
        "GSC 生成式 AI 报告与控制的日期只写在事实表 #gsc-genai"),
    "gsc-retention": (
        r"(?:Search Console|GSC|SC |效果报告|Performance)[^\n。]{0,30}?(?<!\d)16 ?" + _MON
        + r"|(?:保留|最近|Last|last|历史最长|覆盖近|两窗|各取)[^\n。]{0,12}?(?<!\d)16 ?" + _MON,
        "Search Console 16 个月保留期只写在事实表 #gsc-retention"),
    "sitemap-limits": (
        r"(?<![\d,])50,?000 ?(?:个 ?)?(?:URL|条|<loc>)|(?<![\d.])50 ?MB",
        "sitemap 单文件上限只写在事实表 #sitemap-limits"),
    "googlebot-size": (
        r"(?:Googlebot|Google ?抓取)[^\n。]{0,40}?(?<![\d.])2 ?MB|(?<![\d.])2 ?MB[^\n。]{0,30}?(?:Googlebot|索引|截断|index)"
        r"|PDF[^\n。]{0,12}?64 ?MB",
        "Googlebot 抓取上限只写在事实表 #googlebot-size"),
    "api-quotas": (
        r"1,?200 ?(?:QPM|次 ?/ ?分钟|queries per minute)"
        r"|(?<![\d,])150 ?(?:QPM|次 ?/ ?分钟|queries per minute)"
        r"|40,?000 ?(?:QPM|次 ?/ ?分钟)|30,?000,?000|30M ?QPD"
        r"|(?<![\d,])2,?000 ?(?:QPD|次 ?/ ?天)|每天 ?2,?000 ?次|(?<![\d,])600 ?(?:QPM|次 ?/ ?分钟)"
        r"|(?<![\d,])200 ?(?:publish|次)?[^\n。\d]{0,3}(?:/ ?天|per day|/day|每天)"
        r"|(?<![\d,])(?:25|50),?000 ?(?:行|rows)|50K rows"
        r"|(?<![\d,])20 ?(?:次 ?/ ?秒|QPS)|(?<![\d,])200 ?(?:次 ?/ ?分钟|QPM)|100,?000,?000|10,?000,?000 ?(?:次|QPD)"
        r"|15,?000 ?(?:次 ?/ ?分钟|QPM)|(?<![\d,])(?:180|380) ?(?:次 ?)?/ ?分钟",
        "Search Console / Indexing / CrUX API 配额与行数上限只写在事实表 #api-quotas"),
    "indexnow-batch": (
        r"(?:IndexNow|POST)[^\n。]{0,40}?10,?000 ?(?:个 ?)?(?:URL|条)"
        r"|10,?000 ?(?:个 ?)?URL[^\n。]{0,20}?(?:POST|每次|per post)",
        "IndexNow 单次 POST 上限只写在事实表 #indexnow-batch"),
    "search-share": (
        r"(?:Yandex|Яндекс|Naver|Yahoo!?|百度|Baidu|Bing|Google|Seznam|好搜|Haosou) ?"
        r"(?:在[^\n。|]{0,6}?)?(?:约|~|≈)?\d\d?\.\d\d ?%"
        r"|(?:Yandex|Naver)[^\n。|]{0,8}?(?:份额|share)[^\n。|]{0,8}?(?:约|~|≈)? ?\d\d(?:\.\d+)?(?:[–-]\d\d)? ?%"
        r"|StatCounter[^\n。|]{0,12}?(?:约|~|≈) ?\d\d ?%"
        r"|(?:Yandex|Naver) ?在[^\n。|]{0,6}?(?:约|~|≈) ?\d\d ?%",
        "搜索引擎份额只写在事实表 #search-share 和该市场的 markets/*.md"),
}

SELF_CHECK = {
    "cwv": (["LCP ≤2.5s", "LCP ≤2500ms / INP ≤200ms / CLS ≤0.1", "LCP 在 2.5 秒内", "{}ms | ≤2500ms",
             "移动端 LCP > 2.5s", "INP 200–500ms", "CLS 0.1–0.25", "LCP>4s 为差",
             "| INP | 交互到下一帧绘制 | ≤200ms |", "| CLS | 视觉稳定性 | ≤0.1 |"],
            ["LCP 改善 0.8s", "LCP p75 3.1s", "CLS 0.12", "INP 180ms 的页面",
             "LCP、INP、CLS 都在良好档([阈值](facts.md#cwv))"]),
    "crux-window": (["CrUX 是 28 天滑动窗口", "CrUX 28 天 p75", "28 天滚动平均"],
                    ["GSC 近 28 天导出", "改版后 14/28 天对比", "28 天曝光 >0 比例"]),
    "gsc-anomaly": (["2025-05-13 至 2026-04-27 的展示不可比", "断代 2025-05-13~2026-04-30"],
                    ["见[数据异常期](facts.md#gsc-anomaly)", "超过 20 万(2026-04-30)"]),
    "rich-results": (["FAQ 富结果 2026-05-07 起停展", "HowTo 2023-09 移除", "FAQ 文档 2026-06-15 删除", "| 2023-09-14 | 删除 HowTo 文档"],
                     ["FAQ 富结果已停展([日期](facts.md#rich-results))", "2026-05-27 起 AI Mode 可选偏好来源",
                      "Google 2026-06-15 说明 llms.txt 对搜索无影响",
                      "Microsoft 报告 2026-05-07 发布", "PDPL 2023-09-14 生效"]),
    "gsc-genai": (["生成式 AI 效果报告 2026-06-03 公布", "2026-08-31 起全球开放", "[Search Central 博文 2026-06-03](url)",
                   "Search generative AI 控制(2026-08-31 全球上线)"],
                  ["Sitecore 2026-06-03 宣布收购", "生成式 AI 效果报告([日期](facts.md#gsc-genai))"]),
    "gsc-retention": (["Search Console 保留最近 16 个月", "日期选「最近 16 个月」", "SC 数据保留约 16 个月",
                       "品牌筛选历史最长 16 个月", "数据覆盖近 16 个月", "各取 3 个月与 16 个月两窗"],
                      ["法国 AIO 比德国晚约 16 个月", "Bing 历史最长 16 个月", "116 个月"]),
    "sitemap-limits": (["单文件上限 50,000 URL / 50MB", "≤50,000 条", "超过 50MB=fail"],
                       ["40MB=warn", "150,000 URL", "250MB 的日志", "Naver 不能含 50,000 条以上",
                        "Yandex:≤50,000 URL、未压缩 ≤50 MB"]),
    "googlebot-size": (["Googlebot 只抓每个文件的前 2MB", "PDF 前 64MB", "接近 2MB 才有索引截断风险"],
                       ["内存 2 MB、包 32 KB", "disavow 文件 ≤2MB", "12MB 图片"]),
    "api-quotas": (["每站点 1,200 QPM", "CrUX API 150 QPM", "每项目 30,000,000 次/天",
                    "每站点每天 2,000 次", "Indexing API 200 publish/天", "单页 25,000 行", "每天 50,000 行",
                    "每用户 20 次/秒、200 次/分钟", "getMetadata 只读 180/分钟"],
                   ["配额见[事实表](facts.md#api-quotas)", "1,850 次", "前 200 个 URL"]),
    "indexnow-batch": (["每次 POST 最多 10,000 个 URL", "IndexNow 一次最多 10,000 个 URL"],
                       ["10,000 个查询", "100 个好页好过 10000 个薄页"]),
    "search-share": (["Yandex 70.33%", "Naver 43.06%", "百度 46.85%", "Yandex 在土耳其约 26%",
                      "Naver 在韩份额约 63–64%", "StatCounter ~26%"],
                     ["Google 自有站点占前 50 域名引用的 67.8%", "AIO 出现在约 47%",
                      "品牌提及相关系数 0.664", "份额见[事实表](facts.md#search-share)",
                      "触发联网检索率 ChatGPT 98.64%、Google 99.67%"]),
}


def _iter_md_files():
    for root in SCAN_ROOTS:
        if os.path.isfile(root):
            yield root
        elif os.path.isdir(root):
            for dirpath, _d, filenames in os.walk(root):
                for fn in sorted(filenames):
                    if fn.endswith(".md"):
                        yield os.path.join(dirpath, fn)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def load_facts():
    """解析事实表里 ```facts 代码块的 key = value 行。"""
    text = _read(FACTS)
    m = re.search(r"```facts\n(.*?)\n```", text, re.S)
    if not m:
        raise AssertionError("facts.md 缺 ```facts 机器可读块")
    out = {}
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        k, v = (s.strip() for s in line.split("=", 1))
        out[k] = v
    return out


_COMPILED = {fid: re.compile(p) for fid, (p, _why) in FACT_PATTERNS.items()}


def fact_hit(fid, line, rel=""):
    """一行是否硬写了 fid 这类事实;返回匹配串或 None。扫描与自检共用同一判定。"""
    if fid == "search-share" and rel.startswith(MARKETS_DIR):
        return None
    if fid in OTHER_ENGINE_OK and OTHER_ENGINE.search(line):
        return None
    if fid == "search-share" and NOT_SHARE.search(line):
        return None
    if fid == "gsc-retention" and re.search(r"Bing", line):
        return None  # Bing Webmaster Tools 自己的保留期(同为 16 个月)按 Bing 文档写
    m = _COMPILED[fid].search(line)
    return m.group(0) if m else None


def scan_hits():
    compiled = [(fid, None, why) for fid, (_p, why) in FACT_PATTERNS.items()]
    hits = []
    for path in _iter_md_files():
        rel = os.path.relpath(path, SUITE_ROOT)
        if rel in ALLOW:
            continue
        for lineno, line in enumerate(_read(path).splitlines(), 1):
            for fid, _rx, why in compiled:
                got = fact_hit(fid, line, rel)
                if got:
                    hits.append((rel, lineno, fid, got, why))
    return hits


class FactSingleSourceTests(unittest.TestCase):

    def test_scan_scope_resolves(self):
        files = list(_iter_md_files())
        self.assertGreaterEqual(len(files), 100, "扫描范围异常偏少(%d)" % len(files))

    def test_no_hardcoded_fact_outside_table(self):
        hits = scan_hits()
        if hits:
            lines = ["%s:%d: [%s] %r  <- %s" % h for h in hits]
            self.fail("检出 %d 处在事实表以外硬写的事实(改成链接 %s 的对应锚点):\n  "
                      % (len(hits), FACTS_REL) + "\n  ".join(lines))

    def test_self_check_bad_samples_hit(self):
        for fid, (bad, _ok) in SELF_CHECK.items():
            for s in bad:
                self.assertTrue(fact_hit(fid, s), "[%s] 正则漏了 bad 样例 %r" % (fid, s))

    def test_self_check_ok_samples_spared(self):
        for fid, (_bad, ok) in SELF_CHECK.items():
            for s in ok:
                self.assertIsNone(fact_hit(fid, s), "[%s] 正则误伤 ok 样例 %r" % (fid, s))

    def test_every_pattern_has_self_check(self):
        self.assertEqual(set(FACT_PATTERNS), set(SELF_CHECK))


class FactTableTests(unittest.TestCase):

    def test_table_has_anchor_source_and_date_per_fact(self):
        text = _read(FACTS)
        for fid in FACT_PATTERNS:
            m = re.search(r'<a id="%s"></a>(.*?)(?=<a id="|\Z)' % re.escape(fid), text, re.S)
            self.assertIsNotNone(m, "事实表缺锚点 #%s" % fid)
            body = m.group(1)
            self.assertRegex(body, r"https?://", "#%s 缺一手来源 URL" % fid)
            self.assertRegex(body, r"核对 ?20\d\d-\d\d-\d\d", "#%s 缺核对日期" % fid)

    def test_links_to_fact_anchors_resolve(self):
        anchors = set(re.findall(r'<a id="([^"]+)"></a>', _read(FACTS)))
        bad = []
        for path in _iter_md_files():
            rel = os.path.relpath(path, SUITE_ROOT)
            for m in re.finditer(r"facts\.md#([\w-]+)", _read(path)):
                if m.group(1) not in anchors:
                    bad.append("%s -> #%s" % (rel, m.group(1)))
        self.assertEqual(bad, [], "指向事实表的锚点不存在")


class FactConsistencyTests(unittest.TestCase):
    """事实表的值必须与脚本常量、市场文件一致(两边不一致 = 有一边过期)。"""

    @classmethod
    def setUpClass(cls):
        cls.f = load_facts()

    def _src(self, name):
        return _read(os.path.join(SCRIPTS, name))

    def test_field_data_thresholds(self):
        m = re.search(r"THRESHOLDS = \{(.*?)\}", self._src("field_data.py"), re.S)
        body = m.group(1)
        for metric, good, poor in (("LCP", "cwv.lcp.good_ms", "cwv.lcp.poor_ms"),
                                   ("INP", "cwv.inp.good_ms", "cwv.inp.poor_ms"),
                                   ("CLS", "cwv.cls.good", "cwv.cls.poor")):
            mm = re.search(r'"%s": \(([\d.]+), ([\d.]+)\)' % metric, body)
            self.assertEqual((float(mm.group(1)), float(mm.group(2))),
                             (float(self.f[good]), float(self.f[poor])), metric)

    def test_gsc_anomaly_in_scripts(self):
        s, e = self.f["gsc.anomaly.start"], self.f["gsc.anomaly.end"]
        m = re.search(r"EPOCH_START, EPOCH_END = date\((\d+), (\d+), (\d+)\), date\((\d+), (\d+), (\d+)\)",
                      self._src("did_attribution.py"))
        got = ["%04d-%02d-%02d" % tuple(int(x) for x in m.groups()[i:i + 3]) for i in (0, 3)]
        self.assertEqual(got, [s, e])
        # 脚本里任何「start~结束日」文字都必须写对结束日
        bad = []
        for fn in sorted(os.listdir(SCRIPTS)):
            if fn.endswith(".py"):
                for m in re.finditer(re.escape(s) + r" ?[~至到-] ?(\d{4}-\d\d-\d\d)", self._src(fn)):
                    if m.group(1) != e:
                        bad.append("%s: %s" % (fn, m.group(0)))
        self.assertEqual(bad, [], "脚本文字里的 GSC 异常期结束日与事实表不一致")

    def test_sitemap_limits(self):
        src = self._src("sitemap_audit.py")
        self.assertIn("FIFTY_K = %s" % self.f["sitemap.max_urls"], src)
        self.assertEqual(50 * 1024 * 1024, int(self.f["sitemap.max_bytes"]))
        self.assertIn("FIFTY_MB = 50 * 1024 * 1024", src)

    def test_indexnow_batch(self):
        self.assertIn("BATCH_LIMIT = %s" % self.f["indexnow.max_urls_per_post"], self._src("indexnow.py"))

    def test_gsc_api_rows(self):
        self.assertIn("ROW_LIMIT_MAX = %s" % self.f["gsc.api.rows_per_request"], self._src("gsc_api.py"))

    def test_shares_match_market_files(self):
        for key, val in self.f.items():
            if not key.startswith("share."):
                continue
            market = key.split(".")[1]
            body = _read(os.path.join(SUITE_ROOT, "references", "markets", market + ".md"))
            self.assertRegex(body, r"(?<![\d.])%s(?![\d])" % re.escape(val),
                             "%s=%s 在 markets/%s.md 里读不到(两边要同批改)" % (key, val, market))


if __name__ == "__main__":
    unittest.main(verbosity=1)
