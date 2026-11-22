#!/usr/bin/env python3
"""成熟度判级的证据:product_scan.py 的页面归类、lifecycle.py 的 GSC 页数和「没有站点」(stdlib unittest,零外网)。

期望值的来源(不从实现反推):评测出题人写的答案表 tools/evals/onboarding/answers/*.json 里的 maturity 和
maturity_why(出题人按 data/lifecycle.json 逐级判,不看实现):
- launched「L2 核心页(3 个产品页、订阅页);L3 编辑类只有 3 篇冲煮指南 <10 → 2」;
- mature「L2 /pro/ 定价核心页;L3 36 篇文章;L4 4 篇 vs 对比页 ≥3,GSC 两期都有 ≥10 个非首页拿到点击 → 4」;
- idea「没有站点时,signals.* 一律按「未达到」处理(没有站点本身就是确定证据,不算未知)」;
  同一条判法:「证据缺失、判不了」才写未知。
输入是 tools/testsites/lifecycle_sites.py 造的合成站(评测里被测会话读的同一批站)。
修之前这几处判错:launched、mature 的内容维都只到 1 级(/shop/、/subscription/、/pro/ 没算核心页,
/blog/ 下的 a-vs-b 没算对比页,「拿到点击的非首页页数」没有代码算);idea 的技术、内容、AI 可见度记成「未知」,
外链与品牌拿产品名算成 1 级。
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
ROOT = os.path.dirname(os.path.dirname(BASE))
SITES = os.path.join(ROOT, "tools", "testsites", "lifecycle_sites.py")
ANSWERS = os.path.join(ROOT, "tools", "evals", "onboarding", "answers")
sys.path.insert(0, SCRIPTS)

import lifecycle as LC  # noqa: E402
import product_scan as ps  # noqa: E402


def answer(product, key="maturity"):
    with open(os.path.join(ANSWERS, "%s.json" % product), encoding="utf-8") as f:
        return json.load(f)[key]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _SiteCase(unittest.TestCase):
    """造站 → 本机起服务 → product_scan 读一遍(和开局第 1 环同一个入口)。"""
    product = ""

    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="maturity_%s_" % cls.product))
        port = free_port()
        cls.base = "http://127.0.0.1:%d" % port
        cls.out = os.path.join(cls.tmp, cls.product)
        subprocess.run([sys.executable, SITES, "build", "--product", cls.product, "--out", cls.out, "--base", cls.base],
                       check=True, capture_output=True)
        cls.srv = subprocess.Popen([sys.executable, SITES, "serve", "--dir", os.path.join(cls.out, "site"),
                                    "--port", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while True:
            try:
                urllib.request.urlopen(cls.base + "/", timeout=2).read(100)
                break
            except OSError:
                if time.time() - t0 > 15:
                    cls.tearDownClass()
                    raise
                time.sleep(0.2)
        scan_file = os.path.join(cls.tmp, "scan.json")
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "product_scan.py"), "--site", cls.base, "--allow-local",
                        "--no-wayback", "--out", scan_file], check=True, capture_output=True)
        with open(scan_file, encoding="utf-8") as f:
            cls.scan = json.load(f)
        cls.ws = os.path.join(cls.tmp, "seo-ops")            # GSC 导出放在工作区旁的 data/(和开局时一样)
        if os.path.isdir(os.path.join(cls.out, "gsc")):
            shutil.copytree(os.path.join(cls.out, "gsc"), os.path.join(cls.tmp, "data"))

    @classmethod
    def tearDownClass(cls):
        cls.srv.terminate()
        cls.srv.wait(timeout=10)
        shutil.rmtree(cls.tmp, True)

    def content(self):
        metrics, _src = LC.data_metrics(self.ws)
        return LC.diagnose(self.scan, None, metrics)["maturity"]["content"]


class LaunchedShopTests(_SiteCase):
    product = "launched"

    def test_shop_and_subscription_pages_are_core(self):
        for path in ("/shop/ethiopia-guji/", "/shop/colombia-huila/", "/shop/kenya-nyeri/", "/subscription/"):
            self.assertEqual(ps.classify_url(self.base + path)[1], "product", path)
        self.assertNotEqual(ps.classify_url(self.base + "/shipping/")[1], "product")

    def test_content_level_matches_answer(self):
        c = self.content()
        self.assertEqual(c["level"], answer("launched")["content"], c)

    def test_product_lines_still_named_from_shop_section(self):
        lines = next(f["value"] for f in self.scan["facts"] if f["key"] == "product.lines")
        self.assertTrue(any("bean" in x.lower() for x in lines), lines)
        self.assertTrue(any("gear" in x.lower() for x in lines), lines)

    def test_shipping_prices_do_not_make_a_pricing_page(self):
        moved = [m["url"] for m in self.scan["site_scan"].get("page_types_by_content") or []]
        self.assertFalse([u for u in moved if "/shipping/" in u], moved)


class MatureContentTests(_SiteCase):
    product = "mature"

    def test_vs_pages_under_blog_are_compare(self):
        self.assertEqual(self.scan["site_scan"]["page_types"].get("compare"), 4, self.scan["site_scan"]["page_types"])

    def test_pro_page_with_monthly_price_is_pricing(self):
        moved = self.scan["site_scan"].get("page_types_by_content") or []
        self.assertEqual([m["url"] for m in moved], [self.base + "/pro/"], moved)

    def test_pages_with_clicks_from_gsc_export(self):
        n = LC.pages_with_clicks(self.ws)
        self.assertGreaterEqual(n, 10)
        got = LC.gsc_export_metrics(self.ws)
        self.assertEqual(got["metrics"]["pages_with_clicks"], n)

    def test_content_level_matches_answer(self):
        c = self.content()
        self.assertEqual(c["level"], answer("mature")["content"], c)


class NoSiteTests(unittest.TestCase):
    def ws_with(self, stage, site=None):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="maturity_nosite_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        ws = os.path.join(tmp, "seo-ops")
        os.makedirs(os.path.join(ws, "context"))
        prof = {"site": site, "stage": {"value": stage, "confirmed": True},
                "rings": {"1": {"status": "confirmed", "answers": {}}}}
        with open(os.path.join(ws, "context", "profile.json"), "w", encoding="utf-8") as f:
            json.dump(prof, f)
        scan = {"site": site, "repo": tmp, "site_scan": None, "repo_scan": {}, "signals": {"repo_public_routes": 0},
                "facts": [{"key": "product.name", "value": "PetLedger", "kind": "fact"}]}
        return scan, ws

    def test_idea_without_site_is_level_0_not_unknown(self):
        scan, ws = self.ws_with(0)
        mat = LC.diagnose(scan, ws)["maturity"]
        want = answer("idea")
        for dim in ("technical", "content", "authority", "geo", "measurement"):
            self.assertNotEqual(mat[dim]["status"], "unknown", (dim, mat[dim]))
            self.assertEqual(mat[dim]["level"], want[dim], (dim, mat[dim]))

    def test_missing_site_evidence_after_idea_stays_unknown(self):
        scan, ws = self.ws_with(1)                           # 不是想法阶段:没读到站点只是证据缺失
        self.assertEqual(LC.diagnose(scan, ws)["maturity"]["technical"]["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
