#!/usr/bin/env python3
"""评分模型契约测试(borrow-specs E8:geo-optimizer 的版本化与契约模式直译)。

四层契约,全部零网络、合成输入、确定性(PYTHONHASHSEED 无关):
  1. 权重守恒:content_score 双轨 / site_audit AI_HEALTH_WEIGHTS 的权重和必须守恒,
     改权重必炸本测试(E8 "改权重必炸测试" 语义);
  2. health_score 的 area→类别映射完备:site_audit 源码可产出的每个 area 都必须落进
     MAPPING 的某类,或走显式 unmapped 兜底(计主分不计类别分),任何 area 不允许 KeyError;
  3. schema_version:三脚本 --json 输出必须带 schema_version(版本化契约);
  4. 冻结 fixture:tests/fixtures/scoring_v1.json 钉住合成健康样本(主分>=70)的两份
     --json 输出,逐键比对(浮点 tol 1e-9)。

防静默漂移机制说明(为什么要有冻结 fixture):fixture 是评分口径的"指纹"。任何人对
权重、公式、N/A 语义、映射表的改动——哪怕只动一个系数——都会让当前输出与 fixture
失配,本测试立即变红,迫使改动者(a) bump 对应脚本的 schema_version,(b) 用
`python3 tests/test_scoring_contracts.py --regenerate` 重生成 fixture,从而在 diff 里
留下可审查的口径变更记录。没有 fixture,计分语义的漂移只能靠人肉 code review 发现。

fixture 头部 _contract 字段写明契约:"改口径必须 bump schema_version 并重生成 fixture"。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
FIXTURES = os.path.join(BASE, "tests", "fixtures")
FIXTURE = os.path.join(FIXTURES, "scoring_v1.json")
FLOAT_TOL = 1e-9

sys.path.insert(0, SCRIPTS)

# ---------------------------------------------------------------- 合成健康样本(零网络,确定性)
# health_score 输入:site_audit --json 形状。5 个可评分 URL + 1 个拒审(refused);
# 1 个 CRITICAL → 主分 4/5×100=80.0(Good 档,健康样本 >=70);
# docs 与 blog 同 title 钉住 duplicate_title 派生;zz-unmapped-sample 钉住 unmapped 兜底。
HEALTHY_AUDIT = {
    "audited": 6, "critical": 1,
    "results": {
        "https://h.com/": {"verdict": "pass", "findings": [],
                           "meta": {"title": "露营装备首页"}},
        "https://h.com/guide": {"verdict": "pass", "findings": [
            {"severity": "WARN", "area": "a11y", "message": "html 无 lang"},
            {"severity": "WARN", "area": "og", "message": "og:image 缺失"}],
            "meta": {"title": "露营选购指南"}},
        "https://h.com/pricing": {"verdict": "pass", "findings": [
            {"severity": "WARN", "area": "headings", "message": "跳级 h2→h4"},
            {"severity": "INFO", "area": "semantic-html", "message": "语义比值 8% <10%"}],
            "meta": {"title": "定价页"}},
        "https://h.com/docs": {"verdict": "pass", "findings": [
            {"severity": "WARN", "area": "zz-unmapped-sample",
             "message": "site_audit 未来新增检查的样本(钉 unmapped 兜底)"}],
            "meta": {"title": "资源中心"}},
        "https://h.com/blog": {"verdict": "fail", "findings": [
            {"severity": "CRITICAL", "area": "h1", "message": "无 H1"},
            {"severity": "INFO", "area": "bluf", "message": "BLUF 密度不足"}],
            "meta": {"title": "资源中心"}},
        "https://h.com/legacy": {"verdict": "refused", "findings": [
            {"severity": "SKIP", "area": "fetch guard",
             "message": "likely challenge page; refusing to audit"}],
            "meta": {}},
    },
}

CONTENT_KEYWORD = "露营装备清单"
# 三个不同来源竞品(结构对齐健康草稿:10 段、词数接近),术语提取自它们。
CONTENT_COMPETITORS = [
    "露营装备清单怎么准备是新手第一问,答案是按睡眠、厨房、照明、安全四大系统配置。\n\n"
    "帐篷选双层三季款,空间按人数加一选;睡袋按温标选舒适温-5度,怕冷加一条抓绒内胆。\n\n"
    "防潮垫选R值4以上的充气垫,隔凉保暖;地布防扎,帐篷钉与防风绳配套。\n\n"
    "头灯每人一盏备足电池,营地灯选充电式暖光,夜里低亮档省电。\n\n"
    "炉具用分体气炉火力稳定,锅具按人数配,保温箱夏季装食材,冻饮用水当冰袋。\n\n"
    "急救包放止血带、消毒片、创可贴与个人药品,户外安全第一课是会包扎。\n\n"
    "背包按容量60升选,背负系统要合身;折叠桌椅选轻量化铝合金,收纳体积小。\n\n"
    "防晒霜SPF50两小时补涂,驱蚊液含避蚊胺,营地选背风向水处。\n\n"
    "充电宝2万毫安加太阳能板,离线地图提前下载,纸质地图作备份。\n\n"
    "装备清单出发前逐项打勾,回来后清点晾晒,损坏件当次登记下次更换。",
    "新手露营装备推荐从睡眠系统起步:先买帐篷与睡袋,再补防潮垫和头灯,预算不足分三批购齐。\n\n"
    "帐篷看防水指数与搭建难度,睡袋温标按零下五度准备,充气垫R值4更保暖。\n\n"
    "照明:头灯解放双手,营地灯选充电式,备用电池按每天一组带。\n\n"
    "厨房:炉具看火力稳定性与防风,锅具套装收纳,保温箱按食材体积选。\n\n"
    "急救包包含止血带消毒片,纱布与烫伤膏分区放,说明书塑封防潮。\n\n"
    "背包60升起步,重物贴背,常用物放顶包;折叠桌椅看重量与展开速度。\n\n"
    "防晒驱蚊不能省:防晒霜SPF50,驱蚊液喷衣物与帐篷口。\n\n"
    "充电宝保持2万毫安,离线地图提前下载,行程留档给家人。\n\n"
    "营地选择:背风、向阳、离水五十米,炊事区与帐篷区分开。\n\n"
    "装备清单打印两份,一份贴箱一份随身,用后即更新。",
    "露营装备完整清单按系统分组:睡眠系统含帐篷睡袋防潮垫,厨房系统含炉具锅具保温箱。\n\n"
    "照明系统含头灯营地灯与备用电池,电力含充电宝2万毫安与线材。\n\n"
    "安全系统:急救包(止血带、消毒片、创可贴)、防晒霜、驱蚊液。\n\n"
    "导航与通讯:离线地图、纸质地图、口哨,信号区外约定报平安时间。\n\n"
    "帐篷选三季双层,睡袋温标负五度,防潮垫R值4,地布与修补贴配套。\n\n"
    "炉具分体气炉火力稳,保温箱夏季必备,食材按餐分装。\n\n"
    "背包与折叠桌椅按人数配,桌椅选铝合金轻量化。\n\n"
    "头灯每人一盏,营地灯挂主帐口,低亮档过夜。\n\n"
    "充电宝三天行程2万毫安起步,低温下贴身存放。\n\n"
    "装备清单按人按箱建卡,出发核对,归档清点。",
]
# 健康草稿:命中大部分维度满分(title/H1 精确、alt 覆盖、内链>=2、加粗术语、
# Article schema、H2 含变体、前三查全过、facts 全覆盖)→ 总分 strong 档(>=67)。
CONTENT_DRAFT = (
    "# 露营装备清单:三天两夜全套配置\n\n"
    "简而言之,**露营装备清单**按睡眠、厨房、照明、安全四大系统准备,三天行程 15 件装备即可出发。\n\n"
    "## 睡眠系统:帐篷、睡袋与防潮垫\n\n"
    "帐篷选双层三季款;睡袋温标按舒适温 **-5 度**准备;防潮垫选 R值4 以上,隔凉保暖;地布与修补贴配套。\n\n"
    "## 厨房系统:炉具与保温箱\n\n"
    "炉具用分体气炉,火力稳定;保温箱夏季装食材,冻饮用水当冰袋;锅具按人数配。\n\n"
    "## 照明与电力:头灯、营地灯、充电宝\n\n"
    "头灯每人一盏备足电池,营地灯选充电式暖光;充电宝 2万毫安 够三天,低温下贴身存放。\n\n"
    "## 安全防护:急救包、防晒、驱蚊、导航\n\n"
    "急救包含止血带与消毒片;**防晒霜**与驱蚊液必带;导航用**离线地图**加纸质备份,口哨挂背包。\n\n"
    "## 露营装备速览与打包\n\n"
    "装备清单按人按箱建卡,出发核对,归档清点;背包 60 升重物贴背,折叠桌椅选铝合金轻量化。\n\n"
    "![装备全景](gear-overview.jpg)\n\n"
    "选型细节见[装备对比表](/gear/compare)与[新手指南](/guide/newbie)。\n\n"
    "<script type=\"application/ld+json\">{\"@type\":\"Article\"}</script>\n")
CONTENT_FACTS = ("帐篷选双层三季款\n睡袋温标按舒适温-5度准备\n防潮垫选R值4以上\n"
                 "急救包含止血带与消毒片\n充电宝2万毫安够三天\n导航用离线地图\n")


# ---------------------------------------------------------------- 运行与归一化助手
def run_script(name, args=()):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def write_inputs(tmpdir):
    """把合成样本落成文件;返回 (paths, tmpdir)——content_score 需要真实文件。"""
    paths = {"draft": os.path.join(tmpdir, "draft.md"),
             "facts": os.path.join(tmpdir, "facts.md"),
             "comps": [os.path.join(tmpdir, "c%d.md" % i)
                       for i in range(1, len(CONTENT_COMPETITORS) + 1)],
             "audit": os.path.join(tmpdir, "audit.json")}
    with open(paths["draft"], "w", encoding="utf-8") as f:
        f.write(CONTENT_DRAFT)
    with open(paths["facts"], "w", encoding="utf-8") as f:
        f.write(CONTENT_FACTS)
    for p, body in zip(paths["comps"], CONTENT_COMPETITORS):
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    with open(paths["audit"], "w", encoding="utf-8") as f:
        json.dump(HEALTHY_AUDIT, f, ensure_ascii=False)
    return paths


def _normalize(payload, tmpdir):
    """把 payload 里的临时目录路径换成 <TMPDIR> 占位——competitor_files 等字段
    含 tmpdir 绝对路径,归一后 fixture 才可跨机器/跨次再生。"""
    return json.loads(json.dumps(payload).replace(tmpdir, "<TMPDIR>"))


def health_payload(paths, tmpdir):
    r = run_script("health_score.py", ["--input", paths["audit"], "--json"])
    if r.returncode != 0:
        raise AssertionError("health_score --json 失败: %s" % r.stderr)
    return json.loads(r.stdout)


def content_payload(paths, tmpdir):
    r = run_script("content_score.py",
                   ["--draft", paths["draft"],
                    "--competitors", ",".join(paths["comps"]),
                    "--keyword", CONTENT_KEYWORD, "--facts", paths["facts"],
                    "--intent", "definition", "--json"])
    if r.returncode != 0:
        raise AssertionError("content_score --json 失败: %s" % r.stderr)
    return _normalize(json.loads(r.stdout), tmpdir)


def site_audit_json_payload():
    """零网络跑 site_audit --json:monkeypatch fetch 返回 <200B 页面 → fetch guard
    拒审该 URL([SKIP]),--json 顶层照常输出(schema_version/audited/critical/results)。"""
    import site_audit as sa

    def fake_fetch(url, timeout=15):
        return 200, {}, "<html><head><title>t</title></head></html>"

    old_fetch, old_argv = sa.fetch, sys.argv
    sa.fetch, sys.argv = fake_fetch, ["site_audit.py", "https://contract.test/", "--json"]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            try:
                sa.main()
            except SystemExit:
                pass
    finally:
        sa.fetch, sys.argv = old_fetch, old_argv
    out = buf.getvalue()
    return json.loads(out[out.rindex("\n{"):])


FIXTURE_CONTRACT_RULE = "改口径必须 bump schema_version 并重生成 fixture"


def build_fixture():
    """REGENERATE 路径:合成样本 → 两份 --json 输出 → 写入 fixtures/scoring_v1.json。"""
    tmpdir = tempfile.mkdtemp(prefix="sc-contract-")
    try:
        paths = write_inputs(tmpdir)
        doc = {
            "_contract": {
                "what": "评分模型冻结 fixture(borrow-specs E8:geo-optimizer 契约模式)",
                "rule": FIXTURE_CONTRACT_RULE,
                "how": "python3 tests/test_scoring_contracts.py --regenerate",
                "sample": "healthy(health_score main_score>=70;content_score total>=67 strong 档)",
                "anti_drift": "fixture 的存在即防静默漂移机制:任何计分语义变化若未 bump "
                              "schema_version 且未重生成 fixture,本契约测试的逐键比对(浮点 "
                              "tol 1e-9)必炸;合成输入定义在 tests/test_scoring_contracts.py 顶部",
                "path_placeholder": "payload 中的 <TMPDIR> 是生成时临时目录的占位,非数据",
                "schema_versions": {"health_score": "1.0", "content_score": "1", "site_audit": 1},
            },
            "health_score": health_payload(paths, tmpdir),
            "content_score": content_payload(paths, tmpdir),
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(FIXTURES, exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return doc


def assert_frozen_equal(tc, expected, actual, path="$"):
    """逐键比对:dict 键集一致/list 等长按序/浮点 tol 1e-9/其余严格相等。"""
    if isinstance(expected, bool) or isinstance(actual, bool):
        tc.assertIs(actual, expected, msg=path)
    elif isinstance(expected, dict):
        tc.assertIsInstance(actual, dict, msg=path)
        tc.assertEqual(sorted(expected), sorted(actual),
                       msg="%s 键集漂移: 仅fixture=%s 仅当前=%s"
                           % (path, set(expected) - set(actual), set(actual) - set(expected)))
        for k in expected:
            assert_frozen_equal(tc, expected[k], actual[k], "%s.%s" % (path, k))
    elif isinstance(expected, list):
        tc.assertIsInstance(actual, list, msg=path)
        tc.assertEqual(len(expected), len(actual), msg=path)
        for i, (e, a) in enumerate(zip(expected, actual)):
            assert_frozen_equal(tc, e, a, "%s[%d]" % (path, i))
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        tc.assertTrue(abs(float(expected) - float(actual)) <= FLOAT_TOL,
                      msg="%s 浮点漂移: fixture=%r 当前=%r" % (path, expected, actual))
    else:
        tc.assertEqual(actual, expected, msg=path)


# ---------------------------------------------------------------- 契约测试
class ScoringContractTests(unittest.TestCase):
    """E8 四层契约:权重守恒 / 映射完备 / schema_version / 冻结 fixture。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="sc-contract-")
        cls.paths = write_inputs(cls.tmpdir)
        cls.hs_payload = health_payload(cls.paths, cls.tmpdir)
        cls.cs_payload = content_payload(cls.paths, cls.tmpdir)
        with open(FIXTURE, encoding="utf-8") as f:
            cls.fixture = json.load(f)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ---- 1. 权重守恒(改权重必炸) ----
    def test_site_audit_ai_health_weights_sum_to_one(self):
        """AI_HEALTH_WEIGHTS 通过率加权和=1.0±0.001(bots 0.40 + 四项 0.15)。"""
        import site_audit as sa
        self.assertLessEqual(abs(sum(sa.AI_HEALTH_WEIGHTS.values()) - 1.0), 0.001,
                             "AI_HEALTH_WEIGHTS 守恒被破坏: %r" % (sa.AI_HEALTH_WEIGHTS,))

    def test_content_score_ai_track_weights_sum_to_one(self):
        """AI 轨(facts_coverage 0.60 + upfront_intent 0.40)标称和=1.0±0.001。"""
        import content_score as cs
        self.assertLessEqual(abs(sum(cs.AI_WEIGHTS.values()) - 1.0), 0.001,
                             "AI_WEIGHTS 守恒被破坏: %r" % (cs.AI_WEIGHTS,))

    def test_content_score_seo_track_weight_contract(self):
        """SEO 轨守恒契约。任务口径是"权重和=1.0(±0.001)";现码标称 0.90 是**有文档
        的刻意设计**:true_density 维度按官方"密度不计分"剔除后保留原比例系数,由
        weighted() 在计分时对非 N/A 维度重归一(脚本 docstring 与行内注释均已注明),
        且该 0.90 被 golden 测试 tests/test_content_score.py::WeightAndCoefficientTests
        钉死(assertAlmostEqual 0.90)——单方面把标称和改成 1.0 会破坏不可改的既有
        测试且改变所有历史分数。因此本测试断言等效守恒,两条都炸才算护住:
          (a) 标称和钉死 0.90(任何系数漂移——包括悄悄"修"成 1.0——必炸);
          (b) 计分对权重全局缩放不变 ⟺ 计分时 SEO 轨有效权重和恰为 1.0。
        """
        import content_score as cs
        # (a) 标称和钉死(0.90 = 1.00 - true_density 0.10,密度维度官方否定后剔除)
        self.assertLessEqual(abs(sum(cs.SEO_WEIGHTS.values()) - 0.90), 0.001,
                             "SEO_WEIGHTS 标称和漂移(应为 0.90=true_density 剔除后口径): %r"
                             % (cs.SEO_WEIGHTS,))
        # (b) 缩放不变性:整体 ×(1/0.9) 归一到和=1.0 后,分数一位小数必须不变
        comp_texts = list(CONTENT_COMPETITORS)
        model = {"terms": cs.extract_terms(comp_texts), "comp_texts": comp_texts,
                 "source": "serp", "n_comps": len(comp_texts),
                 "files": ["c%d.md" % i for i in range(1, 4)]}
        facts = [l for l in CONTENT_FACTS.splitlines() if l.strip()]
        base = cs.score_text(CONTENT_DRAFT, model, CONTENT_KEYWORD, facts)
        # 交叉验证:进程内计分与 CLI fixture 是同一口径(双通道互证)
        self.assertEqual(round(base["seo"], 1), self.fixture["content_score"]["seo"]["score"])
        factor = 1.0 / sum(cs.SEO_WEIGHTS.values())
        orig = dict(cs.SEO_WEIGHTS)
        try:
            cs.SEO_WEIGHTS.update({k: v * factor for k, v in orig.items()})
            self.assertLessEqual(abs(sum(cs.SEO_WEIGHTS.values()) - 1.0), 1e-9)
            rescaled = cs.score_text(CONTENT_DRAFT, model, CONTENT_KEYWORD, facts)
        finally:
            cs.SEO_WEIGHTS.clear()
            cs.SEO_WEIGHTS.update(orig)
        self.assertEqual(round(rescaled["seo"], 1), round(base["seo"], 1),
                         "SEO 轨计分对权重全局缩放不不变 → weighted() 未重归一,有效权重和≠1.0")

    # ---- 2. health_score area→类别映射完备(不允许 KeyError) ----
    def test_health_score_area_mapping_complete(self):
        """site_audit 源码可产出的每个 area 必须落进 MAPPING 某类;运行时全 area +
        未知 area 一起喂 compute() 不抛 KeyError,未知 area 落显式 unmapped 兜底。"""
        import health_score as hs
        with open(os.path.join(SCRIPTS, "site_audit.py"), encoding="utf-8") as f:
            src = f.read()
        literal = set(re.findall(r'\("(?:CRITICAL|WARN|INFO|SKIP)",\s*"([^"]+)"', src))
        # 根文件循环 for path, name in (("/robots.txt","robots"),...):area 是循环变量,
        # 正则抓不到 → 硬编码同步(site_audit 新增根文件检查时这里要加)。
        loop_areas = {"robots", "sitemap", "llms.txt"}
        skip_only = {"fetch guard"}   # SKIP 级:进 refused 分母剔除,不进映射
        known = (literal | loop_areas) - skip_only
        self.assertLessEqual(known, set(hs.MAPPING),
                             "site_audit 产出但 MAPPING 未覆盖的 area: %s"
                             % sorted(known - set(hs.MAPPING)))
        # 运行时兜底:全部已知 area + 一个"未来新增"的未知 area → 无 KeyError,
        # 未知 area 显式进 unmapped(计主分/子分不计类别分),impacts 全落在 MAPPING。
        findings = [{"severity": "WARN", "area": a, "message": "契约探测"}
                    for a in sorted(known)] + \
                   [{"severity": "WARN", "area": "zz-future-check", "message": "未来新增"}]
        audit = {"results": {
            "https://a.com/": {"verdict": "pass", "findings": findings, "meta": {"title": "A"}},
            "https://b.com/": {"verdict": "pass", "findings": [], "meta": {"title": "B"}}}}
        rep = hs.compute(audit, set(), {})   # 本行不抛 KeyError 即映射完备
        self.assertEqual(rep["main_score"], 100.0)   # 全 WARN 不扣主分(Ahrefs 口径)
        self.assertIn("zz-future-check", [d["area"] for d in rep["unmapped"]])
        self.assertEqual(rep["unmapped"][0]["hit_urls"], 1)
        self.assertFalse(set(i["rule"] for i in rep["impacts"]) - set(hs.MAPPING))

    # ---- 3. schema_version(三脚本 --json 必带) ----
    def test_schema_version_in_site_audit_json(self):
        """site_audit --json 顶层必须带 int 型 schema_version(本次契约化补上)。"""
        import site_audit as sa
        payload = site_audit_json_payload()
        self.assertIn("schema_version", payload)
        self.assertIsInstance(payload["schema_version"], int)
        self.assertEqual(payload["schema_version"], sa.SCHEMA_VERSION)
        self.assertEqual(payload["results"]["https://contract.test/"]["verdict"], "refused")

    def test_schema_version_in_health_score_json(self):
        """health_score --json 必带 schema_version。现值 "1.0"(字符串)被 golden
        test_health_score.py::test_coverage_note_always_present 钉死(assertEqual "1.0"),
        单方面改 int 会破坏不可改的既有测试;契约先钉"存在且主版本可解析为 1",
        下次 bump(改计分口径)时协调 golden 一起切 int。"""
        self.assertIn("schema_version", self.hs_payload)
        self.assertEqual(int(str(self.hs_payload["schema_version"]).split(".")[0]), 1)

    def test_schema_version_in_content_score_json(self):
        """content_score --json 必带 schema_version。现值 "1"(字符串)被 golden
        test_content_score.py::DualTrackTests 钉死(assertEqual "1");同上,先钉
        存在性与主版本,下次 bump 时协调 golden 一起切 int。"""
        self.assertIn("schema_version", self.cs_payload)
        self.assertEqual(int(str(self.cs_payload["schema_version"]).split(".")[0]), 1)

    # ---- 4. 冻结 fixture 契约(防静默漂移) ----
    def test_fixture_matches_health_score_output(self):
        """当前 health_score --json 输出与冻结 fixture 逐键一致(浮点 tol 1e-9)。"""
        assert_frozen_equal(self, self.fixture["health_score"], self.hs_payload,
                            path="$.health_score")

    def test_fixture_matches_content_score_output(self):
        """当前 content_score --json 输出与冻结 fixture 逐键一致(浮点 tol 1e-9)。"""
        assert_frozen_equal(self, self.fixture["content_score"], self.cs_payload,
                            path="$.content_score")

    def test_fixture_contract_header(self):
        """fixture 头部 _contract 必须写明契约原文(改口径→bump+重生成)。"""
        c = self.fixture.get("_contract")
        self.assertIsInstance(c, dict)
        self.assertIn(FIXTURE_CONTRACT_RULE, c.get("rule", ""))
        self.assertIn("anti_drift", c)

    def test_calibrated_healthy_sample(self):
        """校准防漂(E8"校准测试"要求):fixture 钉的必须是**健康样本**——
        health_score 主分>=70(Good 档以上),content_score 总分>=67(strong 档)。
        若未来口径变化把健康样本拖到阈值以下,本测试与 fixture 逐键比对一起炸,
        迫使改动者 bump schema_version 并解释——fixture 的存在本身就是防静默漂移
        机制:任何未声明(未 bump 版本/未重生成 fixture)的口径变化都过不了本套件。
        """
        self.assertGreaterEqual(self.fixture["health_score"]["main_score"], 70)
        self.assertIn(self.fixture["health_score"]["band"], ("Good", "Excellent"))
        self.assertGreaterEqual(self.fixture["content_score"]["total"], 67)
        self.assertEqual(self.fixture["content_score"]["band"], "strong")


if __name__ == "__main__":
    if "--regenerate" in sys.argv or os.environ.get("REGENERATE") == "1":
        doc = build_fixture()
        print("fixture 重生成: %s(health main=%s content total=%s)"
              % (FIXTURE, doc["health_score"]["main_score"], doc["content_score"]["total"]))
        sys.exit(0)
    unittest.main(verbosity=1)
