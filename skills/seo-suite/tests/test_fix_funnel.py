#!/usr/bin/env python3
"""traffic_funnel.py R5 三修回归(pipeline-completeness.md R5;stdlib unittest,零网络)。
①uniqueness/indexability 依赖上游不导出的字段——site_audit.py --json 的 meta 只出
  title/desc_len/links(int 计数),不出 description 文本与 canonical:有则用,无则降级
  (uniqueness 仅 title 相似度、indexability 跳过 canonical 自指校验)并在阶段 note 注明;
②join 键 scheme 不统一——audit 键 https 而 GSC/CWV 导出 http(或反之)曾致 join 全失败:
  norm_url 去 scheme(host+path+query 为键),deeprank 边匹配同键化(顺带修掉非规范页键
  的尾斜杠/大小写差异 KeyError 隐患);
③参数/输入错误退出码不统一——sys.exit(str) 实为 exit 1:统一 stderr+exit 2
  (套件契约 references/monitoring/ci-gates.md:exit 2=用法错,CI 直接红)。
独立可运行:python3 tests/test_fix_funnel.py;也被 run_tests.py 自动发现。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "traffic_funnel.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".json"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def sa_page(title, findings=None, links=3, canonical=None, description=None):
    """site_audit.py --json 真实形态 entry:verdict/findings/meta{title,title_len,desc_len,
    words,h1,jsonld,links:int 计数};不导出 description 文本与 canonical 字段——
    正是 R5① 的降级场景。canonical/description 仅 BYO audit 显式提供时才有。"""
    entry = {"verdict": "pass", "findings": findings or [],
             "meta": {"title": title, "title_len": "%d chars/60" % len(title),
                      "desc_len": "120 chars/155", "words": 300, "h1": 1,
                      "jsonld": 0, "links": links}}
    if canonical is not None:
        entry["meta"]["canonical"] = canonical
    if description is not None:
        entry["meta"]["description"] = description
    return entry


class UpstreamDegradeTests(unittest.TestCase):
    """R5①:上游未导出 description/canonical → 有则用,无则降级并注明。"""

    def test_real_shape_audit_degrades_with_notes(self):
        """site_audit 真实形态(无 description/canonical 字段):uniqueness 注明
        '仅 title 相似度(上游未导出 description)'(同 title 仍聚类),indexability 注明
        'canonical 自指校验跳过(上游未导出 canonical)';markdown 同步输出 ↳ 声明行。"""
        audit = {"https://example.com/dup-1": sa_page("Blue Widgets Guide"),
                 "https://example.com/dup-2": sa_page("Blue Widgets Guide"),
                 "https://example.com/other": sa_page("Widget History Archive")}
        a = tmp_file(json.dumps({"audited": 3, "critical": 0, "results": audit}))
        r = run_script(["--audit", a, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        by = {s["stage"]: s for s in json.loads(r.stdout)["stages"]}
        self.assertEqual(by["uniqueness"]["note"], "仅 title 相似度(上游未导出 description)")
        self.assertEqual(by["indexability"]["note"], "canonical 自指校验跳过(上游未导出 canonical)")
        # 降级不失效:同 title(仅 title 相似度)仍判重复组,primary 按 URL 序取 dup-1
        self.assertEqual([d["url"] for d in by["uniqueness"]["dropped_urls"]],
                         ["https://example.com/dup-2"])
        self.assertIn("重复组", by["uniqueness"]["dropped_urls"][0]["reason"])
        rm = run_script(["--audit", a])                        # markdown 同步注明
        os.unlink(a)
        self.assertEqual(rm.returncode, 0, rm.stderr)
        self.assertIn("↳ 仅 title 相似度(上游未导出 description)", rm.stdout)
        self.assertIn("↳ canonical 自指校验跳过(上游未导出 canonical)", rm.stdout)

    def test_exported_fields_used_when_present(self):
        """有则用:导出了 description/canonical 时不降级(无 note)——description 参与
        Simhash(同 title 不同 desc 不聚类),canonical 自指校验生效(非自指被拦)。"""
        audit = {
            "https://example.com/self": sa_page("Self Canonical Page",
                                                description="d1", canonical="https://example.com/self"),
            "https://example.com/cross": sa_page("Cross Canonical Page",
                                                 description="d2", canonical="https://example.com/self"),
            # 同 title 不同 description:有 description 时不应聚类(title-only 才会)
            "https://example.com/same-t1": sa_page(
                "Blue Widgets Guide",
                description="How to choose blue widgets for home office and team needs",
                canonical="https://example.com/same-t1"),
            "https://example.com/same-t2": sa_page(
                "Blue Widgets Guide",
                description="Independent review of the red widgets lineup this year",
                canonical="https://example.com/same-t2"),
        }
        a = tmp_file(json.dumps({"results": audit}))
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        by = {s["stage"]: s for s in json.loads(r.stdout)["stages"]}
        self.assertNotIn("note", by["uniqueness"])             # description 全导出 → 不降级
        self.assertNotIn("note", by["indexability"])           # canonical 全导出 → 不降级
        self.assertEqual(by["uniqueness"]["dropped"], 0)       # 同 title 异 desc 未聚类
        self.assertEqual([d["url"] for d in by["indexability"]["dropped_urls"]],
                         ["https://example.com/cross"])        # canonical 非自指被拦(有则用)
        self.assertIn("canonical 非自指", by["indexability"]["dropped_urls"][0]["reason"])

    def test_partial_degradation_counts_pages(self):
        """部分页缺字段:note 附受影响页数(:N/M 页),未缺页仍按全量口径判。"""
        audit = {"https://example.com/with": sa_page(
                    "With Description Page", description="A real exported description",
                    canonical="https://example.com/with"),
                 "https://example.com/without": sa_page("Title Only Page")}
        a = tmp_file(json.dumps({"results": audit}))
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        by = {s["stage"]: s for s in json.loads(r.stdout)["stages"]}
        self.assertEqual(by["uniqueness"]["note"],
                         "仅 title 相似度(上游未导出 description):1/2 页")
        self.assertEqual(by["indexability"]["note"],
                         "canonical 自指校验跳过(上游未导出 canonical):1/2 页")

    def test_page_text_helpers(self):
        """单元:page_text 有则用(title+desc),无则仅 title(不误吞 desc_len 计数串);
        has_description/canonical_of 探测字段可得性。"""
        import traffic_funnel as tf
        real = sa_page("Blue Widgets Guide")                   # 真实形态:只有 desc_len
        self.assertEqual(tf.page_text(real), "Blue Widgets Guide")
        self.assertFalse(tf.has_description(real))
        self.assertIsNone(tf.canonical_of(real))
        rich = sa_page("T", description="D text", canonical="https://example.com/t")
        self.assertEqual(tf.page_text(rich), "T D text")
        self.assertTrue(tf.has_description(rich))
        self.assertEqual(tf.canonical_of(rich), "https://example.com/t")
        self.assertEqual(tf.page_text(sa_page("T", description="")), "T")   # 空串=未得


class SchemeInsensitiveJoinTests(unittest.TestCase):
    """R5②:join 键去 scheme(host+path+query)——http/https 混用不再致 GSC/CWV join
    全失败;deeprank 边匹配按同一 norm 键(含尾斜杠/大小写差异的非规范页键)。"""

    def test_norm_url_strips_scheme(self):
        import traffic_funnel as tf
        self.assertEqual(tf.norm_url("https://example.com/A"), "//example.com/A")
        self.assertEqual(tf.norm_url("http://Example.com/A/"), "//example.com/A")   # 同键
        self.assertEqual(tf.norm_url("https://example.com/a?x=1#frag"), "//example.com/a?x=1")
        for u in ("https://example.com/A", "http://Example.com/A/"):
            self.assertEqual(tf.norm_url(tf.norm_url(u)), tf.norm_url(u))           # 幂等

    def test_gsc_and_cwv_join_survive_scheme_mismatch(self):
        """audit 键 https,GSC/CWV 导出全 http:修复前 join 全失败(全员'不在 GSC 导出'
        假 impressions=0、CWV 全 N/A);修复后正常判——in_serps 只丢真零曝光页。"""
        audit = {"https://example.com/": sa_page("Home", description="home desc"),
                 "https://example.com/hot": sa_page("Hot", description="hot desc"),
                 "https://example.com/cold": sa_page("Cold", description="cold desc")}
        gsc = tmp_file("Page,Clicks,Impressions\n"
                       "http://example.com/,10,100\n"          # scheme 全不匹配
                       "http://example.com/hot,5,50\n"
                       "http://example.com/cold,0,0\n", suffix=".csv")
        cwv = tmp_file("URL,LCP,CLS,DCL\n"
                       "http://example.com/,1.0,0.01,0.9\n"
                       "http://example.com/hot,1.2,0.02,1.0\n", suffix=".csv")
        a = tmp_file(json.dumps({"results": audit}))
        r = run_script(["--audit", a, "--gsc", gsc, "--cwv", cwv, "--json"])
        for p in (a, gsc, cwv):
            os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        by = {s["stage"]: s for s in rep["stages"]}
        serp = by["in_serps"]
        self.assertEqual((serp["pages_in"], serp["pages_through"]), (3, 2))
        self.assertEqual([d["url"] for d in serp["dropped_urls"]], ["https://example.com/cold"])
        self.assertEqual(serp["dropped_urls"][0]["reason"], "GSC impressions=0")  # join 命中
        self.assertNotIn("不在 GSC 导出", serp["dropped_urls"][0]["reason"])
        ux = by["good_ux"]
        self.assertEqual((ux["pages_in"], ux["pages_through"], ux["pages_na"]), (2, 2, 0))
        self.assertEqual(rep["through"], 2)                    # http 行的 CWV 也 join 上

    def test_dual_lookup_keys_in_loaders(self):
        """load_gsc/load_cwv 双轨查键:去 scheme join 键与原始行 URL 均命中(保留
        field_data --as-cwv-csv 契约的带 scheme 查键);GSC 同 URL 异 scheme 行累加互通。"""
        import traffic_funnel as tf
        c = tmp_file("URL,LCP,CLS,DCL\nhttps://example.com/a,1.0,0.05,1.0\n", suffix=".csv")
        cwv = tf.load_cwv(c)
        os.unlink(c)
        m = {"lcp": 1.0, "cls": 0.05, "dcl": 1.0}
        self.assertEqual(cwv["//example.com/a"], m)               # join 键(去 scheme)
        self.assertEqual(cwv["https://example.com/a"], m)         # 原始行 URL 别名
        g = tmp_file("Page,Clicks,Impressions\n"
                     "http://example.com/a,2,20\n"
                     "https://example.com/a,3,30\n", suffix=".csv")
        gsc = tf.load_gsc(g)
        os.unlink(g)
        self.assertEqual(gsc["//example.com/a"], {"clicks": 5.0, "impressions": 50.0})
        self.assertIs(gsc["http://example.com/a"], gsc["//example.com/a"])   # 别名同对象

    def test_deeprank_cross_scheme_link_edge(self):
        """出链写 http:// 而页键 https://:边按去 scheme 键命中,入链提升 DeepRank →
        primary=被 http 内链指向的 /target(修复前边丢失,全员 0 平票按 URL 序误取 /dupe)。"""
        txt = "Duplicate Landing Page Best deals on widgets this season only here"
        audit = {
            "https://example.com/hub": sa_page("Hub", description="hub",
                                               links=["http://example.com/target"]),
            "https://example.com/target": sa_page("Dup", description=txt,
                                                  links=["https://example.com/hub"]),
            "https://example.com/dupe": sa_page("Dup", description=txt),
        }
        a = tmp_file(json.dumps({"results": audit}))
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        uniq = [s for s in json.loads(r.stdout)["stages"] if s["stage"] == "uniqueness"][0]
        self.assertEqual([d["url"] for d in uniq["dropped_urls"]], ["https://example.com/dupe"])
        self.assertIn("primary https://example.com/target=1", uniq["dropped_urls"][0]["reason"])

    def test_deeprank_noncanonical_page_keys_no_crash(self):
        """页键带尾斜杠(非规范形)+ links 列表:修复前 incoming 按原始键建、按 norm 键
        查 → KeyError;修复后同键匹配,环稳态 rank=1。"""
        import traffic_funnel as tf
        ranks = tf.deeprank({
            "https://example.com/x/": {"links": ["https://example.com/y"]},
            "https://example.com/y/": {"links": ["https://example.com/x"]},
        })
        self.assertEqual(ranks, {"https://example.com/x/": 1.0, "https://example.com/y/": 1.0})


class ExitCodeContractTests(unittest.TestCase):
    """R5③:参数/输入错误统一 stderr+exit 2(套件契约 ci-gates:exit 2=用法错直接红;
    修复前 sys.exit(str) 路径退出码 1、文件错误裸 traceback)。"""

    @staticmethod
    def valid_audit():
        p = tmp_file(json.dumps({"results": {
            "https://example.com/": sa_page("Home", description="home desc")}}))
        return p

    def assert_usage_error(self, args, needle):
        r = run_script(args)
        self.assertEqual(r.returncode, 2, "stderr=%r" % r.stderr)
        self.assertTrue(r.stderr.strip(), "错误信息必须进 stderr")
        self.assertIn(needle, r.stderr)
        self.assertNotIn("Traceback", r.stderr)                # 干净报错,不裸崩

    def test_arg_errors_exit_2(self):
        self.assert_usage_error([], "需要 --audit 或 --urls")
        self.assert_usage_error(["--audit"], "usage 错误")
        self.assert_usage_error(["--gsc"], "usage 错误")
        a = self.valid_audit()
        self.assert_usage_error(["--audit", a, "--bogus"], "未知参数")
        self.assert_usage_error(["--audit", a, "--gsc"], "usage 错误")
        os.unlink(a)

    def test_input_file_errors_exit_2(self):
        self.assert_usage_error(["--audit", "/nonexistent/funnel-audit.json"], "无法读取")
        a = self.valid_audit()
        self.assert_usage_error(["--audit", a, "--gsc", "/nonexistent/gsc.csv"], "无法读取")
        self.assert_usage_error(["--audit", a, "--cwv", "/nonexistent/cwv.csv"], "无法读取")
        self.assert_usage_error(["--urls", "/nonexistent/urls.txt"], "无法读取")
        os.unlink(a)

    def test_unparseable_inputs_exit_2(self):
        garbage = tmp_file("this is not json at all\n")
        self.assert_usage_error(["--audit", garbage], "无法解析")
        os.unlink(garbage)
        not_dict = tmp_file("[1, 2, 3]")
        self.assert_usage_error(["--audit", not_dict], "无法解析")
        os.unlink(not_dict)
        a = self.valid_audit()
        bad_gsc = tmp_file("Foo,Bar\n1,2\n", suffix=".csv")
        self.assert_usage_error(["--audit", a, "--gsc", bad_gsc], "缺 Page/Impressions/Clicks")
        os.unlink(bad_gsc)
        bad_cwv = tmp_file("URL,LCP,CLS,DCL\nhttps://example.com/,abc,0.1,1.0\n", suffix=".csv")
        self.assert_usage_error(["--audit", a, "--cwv", bad_cwv], "数值无法解析")
        os.unlink(bad_cwv)
        os.unlink(a)

    def test_valid_run_exits_0(self):
        a = self.valid_audit()
        g = tmp_file("Page,Clicks,Impressions\nhttps://example.com/,3,30\n", suffix=".csv")
        r = run_script(["--audit", a, "--gsc", g, "--json"])
        for p in (a, g):
            os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["entered"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
