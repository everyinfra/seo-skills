#!/usr/bin/env python3
"""内链三件套 golden 用例(stdlib unittest,合成 crawl.json,零网络)。
规格 references/overview/pipeline-completeness.md R3-4/5/6:
  link_graph.py —— PageRank 数值(2-环精确值/链星形图解析不动点+独立参照实现交叉
  验证)/深度直方图(>3 层占比)/入链 0/1 清单(零入链排除首页·sitemap-only·死页,
  --include-sitemap-only 可配回)/锚文本审计(精确匹配域名占比 >60% 过度优化警告
  阈值上下沿/泛化锚清单/旧数据 anchor 键缺省兼容)。
  orphan_fix.py —— 同目录候选源页(入链降序,每孤儿 ≤3 候选)/无同主题不硬配/
  建议锚文本(title 品牌前缀 + 路径末段人类化回退)/--max 截断。
  site_crawl.py 锚文本采集 e2e —— 小 fixture HTML 打桩 http_fetch/DNS/延时
  (同 test_site_crawl 手法):锚文本配对进 edges {src,dst,anchor},短锚不落盘。
独立可运行:python3 tests/test_link_tools.py;也被 tests/run_tests.py 自动发现。"""
import argparse
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import link_graph as lg    # noqa: E402
import orphan_fix as ofx   # noqa: E402
import site_crawl as sc    # noqa: E402


def run_script(name, args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_crawl(obj, name="crawl.json"):
    d = tempfile.mkdtemp(prefix="lg_tool_")
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    return p


def page(url, status=200, title=None, depth=None, inlinks=0, out_internal=0,
         out_external=0, source="crawl"):
    return {"url": url, "status": status, "title": title, "canonical": None,
            "depth": depth, "inlinks": inlinks, "out_internal": out_internal,
            "out_external": out_external, "source": source}


def edge(src, dst, anchor=None):
    e = {"src": src, "dst": dst}
    if anchor:
        e["anchor"] = anchor
    return e


def mk_report(pages, edges, orphans=None, domain="example.com", mode="crawl"):
    return {
        "schema_version": 1, "domain": domain, "subdomains": [],
        "discovery": {"mode": mode, "counts": {"robots": 0, "sitemap": 0,
                                               "crawl": len(pages)}},
        "pages": pages, "edges": edges,
        "orphans": orphans if orphans is not None else [],
        "external_domains": {}, "stats": {}, "warnings": [],
    }


# ---------------------------------------------------------------------------
# ① PageRank 数值
# ---------------------------------------------------------------------------

def _reference_pagerank(urls, edges, iters=20, d=0.85):
    """测试内独立参照实现(dict 口径,与被测 array 口径互为交叉验证)。"""
    n = len(urls)
    pr = {u: 1.0 / n for u in urls}
    out = Counter(s for s, _t in edges)
    ins = defaultdict(list)
    for s, t in edges:
        ins[t].append(s)
    for _ in range(iters):
        dang = sum(pr[u] for u in urls if out[u] == 0)
        pr = {u: (1 - d) / n + d * (dang / n + sum(pr[s] / out[s] for s in ins[u]))
              for u in urls}
    return pr


class PageRankTests(unittest.TestCase):
    """20 轮迭代/阻尼 0.85/dangling 均摊(ΣPR=1);已知图数值钉死。"""

    def test_two_node_cycle_exact_value(self):
        """A↔B 环:一轮后即不动点,PR(A)=PR(B)=0.5;归一 0-10 双 10.0。"""
        urls = ["https://e.com/a", "https://e.com/b"]
        edges = [("https://e.com/a", "https://e.com/b"),
                 ("https://e.com/b", "https://e.com/a")]
        pr = lg.pagerank(urls, edges)
        self.assertAlmostEqual(pr["https://e.com/a"], 0.5, places=9)
        self.assertAlmostEqual(pr["https://e.com/b"], 0.5, places=9)
        norm = lg.normalize_scores(pr)
        self.assertEqual(norm["https://e.com/a"], 10.0)
        self.assertEqual(norm["https://e.com/b"], 10.0)

    def test_hub_spoke_matches_reference_and_analytic(self):
        """链星形图(hub↔3 spokes):与独立参照实现逐位一致,且落在解析不动点
        (hub≈0.4797/spoke≈0.1734)±0.02 内;hub 严格最高。"""
        hub, s1, s2, s3 = ("https://e.com/h", "https://e.com/s1",
                           "https://e.com/s2", "https://e.com/s3")
        urls = [hub, s1, s2, s3]
        edges = [(hub, s) for s in (s1, s2, s3)] + [(s, hub) for s in (s1, s2, s3)]
        pr = lg.pagerank(urls, edges)
        ref = _reference_pagerank(urls, edges)
        for u in urls:
            self.assertAlmostEqual(pr[u], ref[u], places=9, msg=u)
        self.assertAlmostEqual(pr[hub], 0.4797, delta=0.02)
        for s in (s1, s2, s3):
            self.assertAlmostEqual(pr[s], 0.1734, delta=0.02)
            self.assertGreater(pr[hub], pr[s])
        self.assertAlmostEqual(sum(pr.values()), 1.0, places=6)

    def test_chain_ordering_and_conservation(self):
        """A→B→C(C dangling,质量均摊):C>B>A,Σ=1,解析不动点 ±0.01。"""
        a, b, c = "https://e.com/a", "https://e.com/b", "https://e.com/c"
        pr = lg.pagerank([a, b, c], [(a, b), (b, c)])
        self.assertGreater(pr[c], pr[b])
        self.assertGreater(pr[b], pr[a])
        self.assertAlmostEqual(sum(pr.values()), 1.0, places=6)
        self.assertAlmostEqual(pr[a], 0.1844, delta=0.01)
        self.assertAlmostEqual(pr[b], 0.3411, delta=0.01)
        self.assertAlmostEqual(pr[c], 0.4743, delta=0.01)

    def test_empty_and_isolated_pages(self):
        """空图不崩;全孤立页均分 1/N。"""
        self.assertEqual(lg.pagerank([], []), {})
        urls = ["https://e.com/x", "https://e.com/y"]
        pr = lg.pagerank(urls, [])
        self.assertAlmostEqual(pr["https://e.com/x"], 0.5, places=9)

    def test_rank_rows_top_bottom_deterministic(self):
        """排序降序、平局按 URL 字典序;bottom 升序(最低在前);入链/深度随行。"""
        pages = [page("https://e.com/p%d" % i, depth=1, inlinks=i) for i in range(5)]
        edges = [("https://e.com/p%d" % i, "https://e.com/p%d" % j)
                 for i in range(5) for j in range(5) if i != j and j >= i]
        urls = [p["url"] for p in pages]
        pr = lg.pagerank(urls, edges)
        rows = lg.rank_rows(pages, urls, edges, pr)
        self.assertEqual([r["pagerank"] for r in rows],
                         sorted((r["pagerank"] for r in rows), reverse=True))
        self.assertEqual(rows[0]["norm_0_10"], 10.0)                 # 最高归一 10
        payload, rows2 = lg.build_payload(mk_report(pages, [
            edge(s, d) for s, d in edges]))
        top, bottom = payload["pagerank"]["top"], payload["pagerank"]["bottom"]
        self.assertEqual(len(top), 5)
        self.assertEqual(bottom[0]["url"], rows2[-1]["url"])         # 最低在前
        self.assertEqual(top[0]["url"], rows2[0]["url"])
        self.assertEqual(payload["pagerank"]["stats"]["sum"], 1.0)   # ΣPR 守恒


# ---------------------------------------------------------------------------
# ② 深度直方图 / ③ 入链 0/1 清单
# ---------------------------------------------------------------------------

class DepthHistogramTests(unittest.TestCase):

    def test_histogram_buckets_and_deep_pct(self):
        """[0,1,1,2,3,4,None,7] → 桶 {0:1,1:2,2:1,3:1,>3:2,不可达:1},>3 占比 25.0%。"""
        depths = [0, 1, 1, 2, 3, 4, None, 7]
        pages = [page("https://e.com/p%d" % i, depth=d) for i, d in enumerate(depths)]
        hist, deep, pct = lg.depth_histogram(pages)
        self.assertEqual(hist, {"0": 1, "1": 2, "2": 1, "3": 1,
                                ">3": 2, "unreachable": 1})
        self.assertEqual(deep, 2)
        self.assertEqual(pct, 25.0)

    def test_all_shallow_zero_pct(self):
        pages = [page("https://e.com/p%d" % i, depth=d) for i, d in enumerate([0, 1, 2, 3])]
        hist, deep, pct = lg.depth_histogram(pages)
        self.assertEqual((deep, pct), (0, 0.0))
        self.assertEqual(hist["unreachable"], 0)


class InlinkListTests(unittest.TestCase):

    def test_zero_inlink_exclusions(self):
        """零入链清单排除首页/sitemap-only 页/死页;--include-sitemap-only 配回。"""
        pages = [
            page("https://e.com/", depth=0, source="crawl"),
            page("https://e.com/sm-only", source="sitemap"),
            page("https://e.com/real-orphan", source="crawl"),
            page("https://e.com/dead", status=404, source="crawl"),
        ]
        rep = mk_report(pages, [])
        zero, one, excluded, _cnt = lg.inlink_lists(rep)
        self.assertEqual(zero, ["https://e.com/real-orphan"])
        self.assertEqual(one, [])
        self.assertEqual(excluded["home"], ["https://e.com/"])
        self.assertEqual(excluded["sitemap_only"], ["https://e.com/sm-only"])
        self.assertEqual(excluded["dead"], ["https://e.com/dead"])
        zero2, _, excluded2, _ = lg.inlink_lists(rep, include_sitemap_only=True)
        self.assertEqual(zero2, ["https://e.com/sm-only", "https://e.com/real-orphan"])
        self.assertEqual(excluded2["sitemap_only"], [])

    def test_one_inlink_list(self):
        """入链恰 1 的页进 one;0 进 zero;≥2 不进。"""
        a, b, c = "https://e.com/a", "https://e.com/b", "https://e.com/c"
        pages = [page(a), page(b), page(c)]
        edges = [edge(a, b), edge(a, c), edge(b, c)]
        zero, one, _ex, _cnt = lg.inlink_lists(mk_report(pages, edges))
        self.assertEqual(zero, [a])                   # a 零入链
        self.assertEqual(one, [b])                    # b 恰 1;c 有 2 不进


# ---------------------------------------------------------------------------
# ④ 锚文本审计
# ---------------------------------------------------------------------------

class AnchorAuditTests(unittest.TestCase):

    @staticmethod
    def _rep(anchors):
        pages = [page("https://e.com/src%d" % i) for i in range(len(anchors))]
        tgt = ["https://e.com/t%d" % (i % 3) for i in range(len(anchors))]
        return mk_report(pages, [edge(p["url"], t, a)
                                 for p, t, a in zip(pages, tgt, anchors)])

    def test_exact_match_over_threshold_warns(self):
        """8/12=66.7%>60% → 过度优化警告;www/裸域/子域变体全算精确匹配。"""
        anchors = (["Example.com", "www.example.com", "https://example.com/",
                    "blog.example.com"] * 2 + ["best coffee guide", "pricing details"] * 2)
        self.assertEqual(len(anchors), 12)
        out = lg.anchor_audit(self._rep(anchors), "example.com")
        self.assertEqual(out["exact_match"]["count"], 8)
        self.assertEqual(out["exact_match"]["pct"], 66.7)
        self.assertTrue(out["exact_match"]["warn"])
        self.assertTrue(any("过度优化" in w for w in out["warnings"]))

    def test_exact_match_below_threshold_no_warn(self):
        """5/12=41.7%<60% → 不警告;小样本(<10 带锚边)即使 100% 也不警告。"""
        anchors = (["example.com"] * 5 + ["best coffee guide", "pricing details",
                                          "how to brew", "espresso at home",
                                          "grinder review", "beans guide", "read more"])
        self.assertEqual(len(anchors), 12)
        out = lg.anchor_audit(self._rep(anchors), "example.com")
        self.assertEqual(out["exact_match"]["pct"], 41.7)
        self.assertFalse(out["exact_match"]["warn"])
        small = lg.anchor_audit(self._rep(["example.com"] * 3), "example.com")
        self.assertEqual(small["exact_match"]["pct"], 100.0)
        self.assertFalse(small["exact_match"]["warn"])   # 3<10 小样本不告警

    def test_generic_anchors_listed(self):
        out = lg.anchor_audit(self._rep(["Click Here", "click here", "click here",
                                         "read more", "了解更多", "best guide"] * 2),
                              "example.com")
        gen = {g["anchor"]: g["count"] for g in out["generic"]}
        self.assertEqual(gen.get("click here"), 6)     # 大小写不敏感归并(2+4)
        self.assertEqual(gen.get("read more"), 2)
        self.assertEqual(gen.get("了解更多"), 2)
        self.assertNotIn("best guide", gen)

    def test_missing_anchor_edges_compat(self):
        """旧版 crawl.json edges 无 anchor 键:锚审计按 0 带锚边处理,不崩不警告。"""
        a, b = "https://e.com/a", "https://e.com/b"
        rep = mk_report([page(a), page(b)], [{"src": a, "dst": b}])
        out = lg.anchor_audit(rep, "example.com")
        self.assertEqual(out["anchored_edges"], 0)
        self.assertEqual(out["exact_match"]["pct"], 0.0)
        self.assertFalse(out["exact_match"]["warn"])
        self.assertEqual(out["distribution"], [])
        # CLI 全链路同样兼容:rc 0
        r = run_script("link_graph.py", ["--crawl", tmp_crawl(rep)])
        self.assertEqual(r.returncode, 0)
        self.assertIn("带锚边 0/1", r.stdout)


# ---------------------------------------------------------------------------
# site_crawl 锚文本采集 e2e(打桩 http_fetch/DNS/延时,零网络)
# ---------------------------------------------------------------------------

class _MiniWeb:
    """site_crawl.http_fetch 桩:精确路由,一律 200 无重定向。"""

    def __init__(self, routes):
        self.routes = routes

    def __call__(self, url, timeout=10.0, method="GET"):
        body = self.routes.get(url, "")
        return {"status": 200, "final_url": url, "chain": [], "headers": {},
                "body": body, "body_bytes": body.encode("utf-8", "replace")}


@contextlib.contextmanager
def sc_patched(routes):
    orig_fetch, orig_dns, orig_sleep = sc.http_fetch, sc.dns_resolve, sc._sleep
    web = _MiniWeb(routes)
    sc.http_fetch = web
    sc.dns_resolve = lambda host: ["93.184.216.34"]
    sc._sleep = lambda t: None
    sc._ssrf_cache.clear()
    try:
        yield web
    finally:
        sc.http_fetch, sc.dns_resolve, sc._sleep = orig_fetch, orig_dns, orig_sleep
        sc._ssrf_cache.clear()


def sc_ns(**kw):
    d = dict(site="https://example.com", urls=None, max_pages=500, delay=0.0,
             ignore_robots=False, strip_params=False, same_host=False,
             include_subdomains=True, subs="dns", check_external=False,
             timeout=5.0, out="crawl.json", urls_out=None, json=False)
    d.update(kw)
    return argparse.Namespace(**d)


class AnchorCollectionE2ETests(unittest.TestCase):

    def test_anchor_paired_into_edges_end_to_end(self):
        """e2e:锚文本配对进 edges {src,dst,anchor};空白折叠/嵌套标签文本计入;
        短锚(<2 字)不落盘(anchor 键缺省);产物可直接喂 link_graph 锚审计。"""
        home, a = "https://example.com/", "https://example.com/a"
        routes = {
            home: ('<html><head><title>Home</title></head><body>'
                   '<a href="/a">About  Us\n Page</a></body></html>'),
            a: ('<html><head><title>A</title></head><body>'
                '<a href="/b">Best Coffee Guide</a>'
                '<a href="/c">x</a>'                                   # 1 字锚丢弃
                '<a href="/d">Guide to <b>Grinders</b> and \n  Brewers</a>'
                '</body></html>'),
        }
        with sc_patched(routes):
            rep, rc = sc.Crawler(sc_ns()).run()
        self.assertEqual(rc, 0)
        edges = {(e["src"], e["dst"]): e for e in rep["edges"]}
        self.assertEqual(edges[(home, a)]["anchor"], "About Us Page")   # 空白折叠
        self.assertEqual(edges[(a, "https://example.com/b")]["anchor"],
                         "Best Coffee Guide")
        self.assertEqual(edges[(a, "https://example.com/d")]["anchor"],
                         "Guide to Grinders and Brewers")               # 嵌套+换行
        self.assertNotIn("anchor", edges[(a, "https://example.com/c")])  # 短锚无键
        # 管线接线:同一份报告进 link_graph 锚审计
        out = lg.anchor_audit(rep, rep["domain"])
        self.assertEqual(out["anchored_edges"], 3)
        self.assertFalse(out["exact_match"]["warn"])

    def test_anchor_truncated_at_80_and_unclosed_tolerated(self):
        """超长锚截 80 字;未闭合 <a> 不崩(锚留空→不落盘)。"""
        p = sc.PageParser()
        p.feed('<html><body><a href="/x">%s</a><a href="/y">never closed</body></html>'
               % ("word " * 40))
        self.assertEqual(p.hrefs, ["/x", "/y"])
        self.assertEqual(len(p.anchors[0]), 80)          # 200 字 → 截 80
        self.assertTrue(p.anchors[0].startswith("word word"))
        self.assertEqual(p.anchors[1], "")               # 未闭合 → 空,下游按缺省


# ---------------------------------------------------------------------------
# orphan_fix
# ---------------------------------------------------------------------------

class OrphanFixTests(unittest.TestCase):

    @staticmethod
    def _rep():
        pages = [
            page("https://e.com/blog/a", inlinks=5, out_internal=2, title="Guide A"),
            page("https://e.com/blog/b", inlinks=9, out_internal=3, title="Guide B"),
            page("https://e.com/blog/c", inlinks=1, out_internal=1, title="Guide C"),
            page("https://e.com/blog/d", inlinks=3, out_internal=1, title="Guide D"),
            page("https://e.com/news/e", inlinks=99, out_internal=5, title="News E"),
            page("https://e.com/blog/deep", inlinks=0, out_internal=0,
                 title="Deep Dive: Espresso | Acme"),
        ]
        return mk_report(pages, [], orphans=["https://e.com/blog/deep"])

    def test_same_dir_candidates_ranked_max_three(self):
        """同目录(路径首段)已链出页按入链降序,每孤儿最多 3 候选;跨目录不选。"""
        plans, total = ofx.build_plan(self._rep())
        self.assertEqual(total, 1)
        self.assertEqual(len(plans), 1)
        pl = plans[0]
        self.assertEqual(pl["topic"], "blog")
        self.assertEqual([c["url"] for c in pl["candidates"]],
                         ["https://e.com/blog/b", "https://e.com/blog/a",
                          "https://e.com/blog/d"])       # 9/5/3;/blog/c 被 3 上限截掉
        self.assertNotIn("https://e.com/news/e",
                         [c["url"] for c in pl["candidates"]])   # 跨主题不选
        self.assertEqual(pl["suggested_anchor"], "Deep Dive: Espresso")

    def test_no_cross_topic_hard_pairing(self):
        """/zzz 孤儿无同目录候选 → 空候选 + markdown 提示导航/hub,不硬配。"""
        pages = [page("https://e.com/news/a", inlinks=9, out_internal=2),
                 page("https://e.com/zzz/one", title=None)]
        rep = mk_report(pages, [], orphans=["https://e.com/zzz/one"])
        plans, _ = ofx.build_plan(rep)
        self.assertEqual(plans[0]["candidates"], [])
        r = run_script("orphan_fix.py", ["--crawl", tmp_crawl(rep)])
        self.assertEqual(r.returncode, 0)
        self.assertIn("无同主题候选源页", r.stdout)
        self.assertIn("导航级入口", r.stdout)

    def test_suggested_anchor_title_and_path_fallback(self):
        """title 取品牌分隔符前首段截 60;缺 title 回退路径末段人类化。"""
        self.assertEqual(ofx.suggest_anchor("Best Coffee Grinders 2026 | Acme", "u"),
                         "Best Coffee Grinders 2026")
        self.assertEqual(ofx.suggest_anchor(" Acme — 综合咖啡指南 ", "u"), "Acme")
        self.assertEqual(ofx.suggest_anchor(None, "https://e.com/products/coffee-grinder-2026"),
                         "coffee grinder 2026")
        self.assertEqual(len(ofx.suggest_anchor("w " * 50, "u")), 59)   # 99 字截 60(末尾空格 rstrip)
        self.assertTrue(ofx.suggest_anchor("w " * 50, "u").startswith("w w"))
        self.assertTrue(ofx.suggest_anchor(None, "https://e.com/"))   # 根路径也不为空

    def test_max_cap_default_50_and_cli(self):
        """52 孤儿默认处理 50;--max 10 只处理 10(CLI --json 结构一致)。"""
        pages = [page("https://e.com/blog/hub", inlinks=10, out_internal=5)]
        pages += [page("https://e.com/blog/o%02d" % i) for i in range(52)]
        rep = mk_report(pages, [], orphans=[p["url"] for p in pages[1:]])
        plans, total = ofx.build_plan(rep)
        self.assertEqual((total, len(plans)), (52, 50))
        r = run_script("orphan_fix.py", ["--crawl", tmp_crawl(rep), "--max", "10", "--json"])
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertEqual((payload["orphans_total"], payload["processed"]), (52, 10))
        self.assertEqual(len(payload["plans"]), 10)
        self.assertEqual(payload["plans"][0]["candidates"][0]["url"],
                         "https://e.com/blog/hub")     # blog 目录唯一已链出活页

    def test_markdown_rows_and_orphan_self_excluded(self):
        """markdown 呈现"源页 → 孤儿页 → 建议锚文本";孤儿自身/死页不作候选。"""
        pages = [
            page("https://e.com/blog/hub", inlinks=7, out_internal=4),
            page("https://e.com/blog/dead", status=404, inlinks=6, out_internal=2),
            page("https://e.com/blog/other-orphan", inlinks=0, out_internal=0),
            page("https://e.com/blog/orphan", title="Orphan Target Page | Acme"),
        ]
        rep = mk_report(pages, [], orphans=["https://e.com/blog/orphan",
                                            "https://e.com/blog/other-orphan"])
        r = run_script("orphan_fix.py", ["--crawl", tmp_crawl(rep)])
        self.assertEqual(r.returncode, 0)
        self.assertIn('源页 https://e.com/blog/hub(入链 7)→ 孤儿 '
                      'https://e.com/blog/orphan → 建议锚文本 "Orphan Target Page"',
                      r.stdout)
        # 死页/另一孤儿都不在候选里:第二个孤儿(同为 blog 目录)唯一候选仍是 hub
        payload = json.loads(run_script("orphan_fix.py",
                                        ["--crawl", tmp_crawl(rep), "--json"]).stdout)
        for pl in payload["plans"]:
            cands = [c["url"] for c in pl["candidates"]]
            self.assertEqual(cands, ["https://e.com/blog/hub"])
            self.assertNotIn(pl["orphan"], cands)


# ---------------------------------------------------------------------------
# CLI:--help / 输入校验 / --json
# ---------------------------------------------------------------------------

class CliTests(unittest.TestCase):

    def test_help_both_scripts(self):
        for name in ("link_graph.py", "orphan_fix.py"):
            r = run_script(name, ["--help"])
            self.assertEqual(r.returncode, 0, name)
            self.assertIn("usage:", r.stdout)
            self.assertIn("退出码", r.stdout)

    def test_bad_input_exit_2(self):
        """文件缺失/非 JSON/缺键 → 退出码 2(两脚本同口径)。"""
        for name in ("link_graph.py", "orphan_fix.py"):
            self.assertEqual(run_script(name, ["--crawl", "/nonexistent/c.json"]).returncode,
                             2, name)
            notjson = tmp_crawl({}) and None
            f = os.path.join(tempfile.mkdtemp(prefix="bad_"), "c.json")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write("not json at all{")
            self.assertEqual(run_script(name, ["--crawl", f]).returncode, 2, name)
            self.assertEqual(run_script(name, ["--crawl", tmp_crawl({"pages": 1})]).returncode,
                             2, name)
            self.assertEqual(run_script("link_graph.py", ["--crawl", "x", "--top", "0"]).returncode,
                             2)

    def test_link_graph_cli_json_and_warn_exit_code(self):
        """--json 全量结构;过度优化触发时 CLI 退出码 1。"""
        anchors = ["example.com"] * 8 + ["best guide", "read more", "how to", "details"]
        pages = [page("https://e.com/src%d" % i) for i in range(12)]
        tgt = ["https://e.com/t%d" % (i % 3) for i in range(12)]
        rep = mk_report(pages, [edge(p["url"], t, a)
                                for p, t, a in zip(pages, tgt, anchors)])
        p = tmp_crawl(rep)
        r = run_script("link_graph.py", ["--crawl", p, "--json"])
        self.assertEqual(r.returncode, 1)                       # 警告 → 退出码 1
        payload = json.loads(r.stdout)
        for key in ("site", "input", "pagerank", "depth", "inlinks", "anchors", "warnings"):
            self.assertIn(key, payload)
        self.assertEqual(payload["pagerank"]["iterations"], 20)
        self.assertEqual(payload["pagerank"]["damping"], 0.85)
        self.assertTrue(payload["anchors"]["exact_match"]["warn"])
        md = run_script("link_graph.py", ["--crawl", p])
        self.assertIn("PageRank", md.stdout)
        self.assertIn("深度直方图", md.stdout)
        self.assertIn("过度优化", md.stdout)
        self.assertIn("泛化锚", md.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
