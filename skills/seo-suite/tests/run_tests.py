#!/usr/bin/env python3
"""seo-suite golden 用例测试层(stdlib unittest,合成数据,零网络)。
每个脚本 2-3 个固定输入→期望输出断言;`python3 tests/run_tests.py` 运行,
全绿退出码 0,任何失败非零(被 scripts/self_check.py 以 subprocess 消费)。
grid_rank 无独立脚本——按 references/monitoring/local-grid-ranking.md 的
源码级口径实现被测函数,并钉死该文档自带的 3×3 算例(ARP=2.2/ATRP=8.4/SoLV=55.6)。"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


class TextMetricsTests(unittest.TestCase):
    """中文营销词检出 / em-dash 计数 / 水印字符(+--scrub 清除)"""

    def test_zh_slop_detected(self):
        r = run_script("text_metrics.py", stdin="我们赋能企业打造卓越体验,提供一站式服务,坚持匠心精神。")
        self.assertIn("中文营销词 4 个", r.stderr)
        self.assertIn("赋能", r.stderr)
        self.assertIn("一站式", r.stderr)

    def test_em_dash_count(self):
        r = run_script("text_metrics.py", stdin="第一段内容—继续—再来–结束。")
        self.assertIn("em/en-dash 3 次", r.stderr)

    def test_watermark_chars_and_scrub(self):
        text = "纯净文本\u200b中间水印\u200b结束。"
        r = run_script("text_metrics.py", stdin=text)
        self.assertIn("Unicode 水印字符", r.stderr)
        self.assertIn("U+200B", r.stderr)
        rs = run_script("text_metrics.py", ["--scrub"], stdin=text)
        self.assertEqual(rs.stdout, "纯净文本中间水印结束。")


class KeywordVariantsTests(unittest.TestCase):
    """阿文 أ/ا 归组(含 ة→ه/tatweel)/ 全半角 NFKC / 土耳其 İ"""

    def test_arabic_ortho_grouping(self):
        import keyword_variants as kv
        self.assertEqual(kv.canon("أحمد")[0], "احمد")
        self.assertEqual(kv.canon("احمد")[0], "احمد")
        self.assertEqual(kv.canon("مكـة")[0], "مكه")   # tatweel 去除 + ة→ه
        self.assertIn("ar-ortho", kv.canon("أحمد")[1])

    def test_fullwidth_nfkc(self):
        import keyword_variants as kv
        c, rules = kv.canon("ＳＥＯ")
        self.assertEqual(c, "seo")
        self.assertIn("fullwidth/halfwidth(NFKC)", rules)

    def test_turkish_dotted_i(self):
        import keyword_variants as kv
        c, rules = kv.canon("İstanbul")
        self.assertEqual(c, "istanbul")
        self.assertNotIn("\u0307", c)          # 不得残留组合点
        self.assertIn("tr-İ", rules)

    def test_grouping_end_to_end(self):
        r = run_script("keyword_variants.py", stdin="قهوة\nقهوه\nİstanbul\nISTANBUL\n")
        self.assertIn("4 词 → 2 组(2 处合并)", r.stdout)


class GscMiningTests(unittest.TestCase):
    """striking distance 过滤 / CTR 期望曲线 / parse_ctr 双格式"""

    def test_expected_ctr_curve(self):
        import gsc_mining as g
        self.assertEqual(g.expected_ctr(1), 0.28)
        self.assertEqual(g.expected_ctr(2), 0.15)
        self.assertEqual(g.expected_ctr(4), 0.07)   # 3<p<=5 档
        self.assertEqual(g.expected_ctr(5), 0.07)
        self.assertEqual(g.expected_ctr(6), 0.03)   # 5<p<=10 档
        self.assertEqual(g.expected_ctr(15), 0.01)
        self.assertEqual(g.expected_ctr(50), 0.005)  # >20 尾档

    def test_parse_ctr_formats(self):
        import gsc_mining as g
        self.assertAlmostEqual(g.parse_ctr("3.2%"), 0.032)
        self.assertAlmostEqual(g.parse_ctr("0.032"), 0.032)
        self.assertEqual(g.parse_ctr(""), 0.0)

    def test_striking_distance_filter(self):
        import gsc_mining as g
        csv = ("Query,Clicks,Impressions,CTR,Position\n"
               "cheap flights,10,500,2%,6.2\n"      # 命中 5-20 且曝光≥20
               "head term,50,5000,5%,4.0\n"         # pos<5 排除
               "page2 term,2,80,1%,18.0\n"          # 命中
               "low impr,0,10,0%,8.0\n"             # 曝光<20 排除
               "too far,1,60,0.5%,22.0\n"           # pos>20 排除
               "quick win,0,100,0%,12.0\n"          # 命中 SD;CTR 差 1pp<2pp 不进低CTR
               "neg ctr,0,100,-10%,11.0\n")         # 命中 SD;CTR 差>2pp 进低CTR
        p = tmp_file(csv)
        r = run_script("gsc_mining.py", [p])
        self.assertIn("striking distance(pos5-20, 曝光≥20): 4 词", r.stdout)
        self.assertIn("cheap flights", r.stdout)
        self.assertNotIn("head term", r.stdout)
        self.assertIn("低CTR机会(期望-实际>2pp): 1 词", r.stdout)
        os.unlink(p)


class GridRankTests(unittest.TestCase):
    """3×3 合成网格(含未找到点)的 ARP/ATRP/SoLV 数值断言。
    口径钉死 references/monitoring/local-grid-ranking.md:
    ARP=Σrank(命中)/|H|;ATRP=Σ(rank??21)/N;SoLV=count(rank≤3)/N×100;均 1 位小数。"""

    @staticmethod
    def arp(ranks):
        h = [r for r in ranks if r is not None]
        return round(sum(h) / len(h), 1) if h else None

    @staticmethod
    def atrp(ranks):
        return round(sum(r if r is not None else 21 for r in ranks) / len(ranks), 1)

    @staticmethod
    def solv(ranks):
        return round(sum(1 for r in ranks if r is not None and r <= 3) / len(ranks) * 100, 1)

    def test_doc_worked_example(self):
        grid = [1, 2, 4, None, 1, 3, 2, None, None]   # 文档算例:6 命中/3 未找到
        self.assertEqual(self.arp(grid), 2.2)
        self.assertEqual(self.atrp(grid), 8.4)
        self.assertEqual(self.solv(grid), 55.6)
        self.assertEqual(sum(1 for r in grid if r is not None), 6)      # found_in 6/9
        self.assertEqual(round(self.atrp(grid) - self.arp(grid), 1), 6.2)  # 盲区代理

    def test_all_found(self):
        grid = [1, 1, 1, 2, 2, 3, 3, 5, 7]
        self.assertEqual(self.arp(grid), 2.8)
        self.assertEqual(self.atrp(grid), 2.8)   # 无盲区 → 两值相等
        self.assertEqual(self.solv(grid), 77.8)

    def test_none_found(self):
        grid = [None] * 9
        self.assertIsNone(self.arp(grid))        # |H|=0 → null
        self.assertEqual(self.atrp(grid), 21.0)  # 全按 21 计
        self.assertEqual(self.solv(grid), 0.0)


class SerpOverlapTests(unittest.TestCase):
    """四档判据:7-10 同文 / 4-6 同簇 / 2-3 互链 / 0-1 分开;0 共享不出对"""

    def test_four_tiers(self):
        csv = ("kwA,u1;u2;u3;u4;u5;u6;u7;u8\n"
               "kwB,u1;u2;u3;u4;u5;u6;u7;u9\n"
               "kwC,u1;u2;u3;u4;x1;x2\n"
               "kwD,u1;y1;y2\n"
               "kwE,u2;u3;e1\n")
        p = tmp_file(csv)
        r = run_script("serp_overlap.py", [p])
        self.assertIn("同一篇文章", r.stdout)   # A×B 共享 7
        self.assertIn("同簇(一页可服务)", r.stdout)  # A×C 共享 4
        self.assertIn("互链", r.stdout)         # A×E 共享 2
        self.assertIn("分开", r.stdout)         # A×D 共享 1
        os.unlink(p)

    def test_zero_shared_pair_omitted(self):
        csv = "kwF,z1;z2\nkwG,w1;w2\n"
        p = tmp_file(csv)
        r = run_script("serp_overlap.py", [p])
        self.assertNotIn("kwF", r.stdout.replace("关键词对", ""))
        self.assertNotIn("kwG", r.stdout.replace("关键词对", ""))
        os.unlink(p)

    def test_shared_one_verdict_line(self):
        csv = "kwH,a;b;c\nkwI,a;d;e\n"
        p = tmp_file(csv)
        r = run_script("serp_overlap.py", [p])
        self.assertIn("kwH × kwI", r.stdout)
        self.assertIn("分开", r.stdout)
        os.unlink(p)


class MarketLintTests(unittest.TestCase):
    """日文全角 title 超限→CRITICAL/exit 1;半角 0.5 计权;阿文 RTL 提示"""

    def test_ja_fullwidth_over_limit(self):
        p = tmp_file("ラ" * 40 + "\n" + "ラ" * 40 + "\nこれはテストです。\n")
        r = run_script("market_lint.py", ["--market", "ja", p])
        self.assertIn("[CRITICAL] title 40/32 fullwidth(40) 超限,超出 8", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_ja_halfwidth_counts_half(self):
        p = tmp_file("ラ" * 30 + "ab\n" + "ラ" * 40 + "\nこれはテストです。\n")
        r = run_script("market_lint.py", ["--market", "ja", p])
        self.assertIn("✓ title 31/32 fullwidth(32)", r.stdout)   # 30 全角 + 2 半角×0.5
        self.assertEqual(r.returncode, 0)

    def test_arabic_rtl_direction(self):
        html = ('<html dir="rtl" lang="ar"><head><title>متجر الإلكترونيات</title>'
                '<meta name="description" content="تخفيضات كبيرة"></head>'
                '<body>هذا المنتج(تخفيض) رائع جدا</body></html>')
        p = tmp_file(html)
        r = run_script("market_lint.py", ["--market", "ar", p])
        self.assertIn('dir="rtl" 在场', r.stdout)      # HTML 才能机检方向位
        self.assertIn("阿文语境裸 LTR 标点 2 处", r.stdout)   # ج( 与 ض) 相邻 → 裸标点
        self.assertIn("U+2066", r.stdout)
        self.assertEqual(r.returncode, 0)
        os.unlink(p)

    def test_arabic_plaintext_rtl_is_manual(self):
        p = tmp_file("متجر الإلكترونيات\nتخفيضات كبيرة\nهذا المنتج(تخفيض) رائع جدا\n")
        r = run_script("market_lint.py", ["--market", "ar", p])
        self.assertIn("纯文本无 dir 属性可检", r.stdout)   # 纯文本降级 MANUAL
        self.assertIn("阿文语境裸 LTR 标点", r.stdout)
        os.unlink(p)


class LlmstxtValidateTests(unittest.TestCase):
    """validate:H1 缺失告警 / 链接<3 / 合规件通过"""

    def test_missing_h1(self):
        p = tmp_file("> summary\n\n- [a](https://x.com/a): d\n- [b](https://x.com/b): d\n- [c](https://x.com/c): d\n")
        r = run_script("llmstxt.py", ["validate", p])
        self.assertIn("缺 H1(唯一必需元素)", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_fewer_than_three_links(self):
        p = tmp_file("# Title\n\n> summary\n\n- [a](https://x.com/a): d\n- [b](https://x.com/b): d\n")
        r = run_script("llmstxt.py", ["validate", p])
        self.assertIn("链接仅 2 条(<3,指南建议 10-30)", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_valid_file_passes(self):
        p = tmp_file("# Title\n\n> summary\n\n## Pages\n\n"
                     "- [a](https://x.com/a): d\n- [b](https://x.com/b): d\n- [c](https://x.com/c): d\n")
        r = run_script("llmstxt.py", ["validate", p])
        self.assertIn("链接 3", r.stdout)
        self.assertEqual(r.returncode, 0)


class RobotsPostureTests(unittest.TestCase):
    """parse_groups:allow/disallow 解析、注释剥离、键大小写不敏感"""

    def test_multi_group_parse(self):
        import robots_posture as rp
        txt = "User-agent: *\nDisallow: /admin\nDisallow: /tmp\n\nUser-agent: GPTBot\nAllow: /\n"
        groups, order = rp.parse_groups(txt)
        self.assertEqual(groups, {"*": {"allow": [], "disallow": ["/admin", "/tmp"]},
                                  "GPTBot": {"allow": ["/"], "disallow": []}})
        self.assertEqual(order, ["*", "GPTBot"])

    def test_comments_stripped(self):
        import robots_posture as rp
        txt = "# robots\nUser-agent: PerplexityBot # search bot\nDisallow: /private # keep out\n"
        groups, _ = rp.parse_groups(txt)
        self.assertEqual(groups["PerplexityBot"]["disallow"], ["/private"])

    def test_lowercase_keys_and_value_case_kept(self):
        import robots_posture as rp
        txt = "user-agent: ClaudeBot\nallow: /blog\n"
        groups, order = rp.parse_groups(txt)
        self.assertIn("ClaudeBot", groups)          # 值保留原大小写(供 bot 名精确匹配)
        self.assertEqual(groups["ClaudeBot"]["allow"], ["/blog"])
        self.assertEqual(order, ["ClaudeBot"])


class PaymentIntentTests(unittest.TestCase):
    """OXXO→MX 标注 / 变音符折叠 dólar→AR / 无命中词输出 -"""

    def test_oxxo_maps_to_mx(self):
        r = run_script("payment_intent.py", stdin="zapatos oxxo\n")
        self.assertIn("payment:mx:oxxo", r.stdout)

    def test_efectivo_and_dollar_folding(self):
        r = run_script("payment_intent.py", stdin="pago en efectivo\ndólar blue\n")
        self.assertIn("payment:mx:efectivo", r.stdout)
        self.assertIn("payment:ar:dólar", r.stdout)   # dólar 折叠后仍标原词形

    def test_no_hit_and_summary(self):
        r = run_script("payment_intent.py", stdin="running shoes\nzapatos oxxo\n")
        self.assertRegex(r.stdout, r"running shoes\s+→ -")
        self.assertIn("1/2 关键词带支付意图信号", r.stdout)


class LocalFormatTests(unittest.TestCase):
    """de:英式千分位逆序告警(✗/exit 1)/ 德式通过 / 无数字跳过"""

    def test_english_order_flagged(self):
        r = run_script("local_format.py", ["--market", "de", "Preis 1,234.56 und 2,499.99"])
        self.assertIn("英式千分位", r.stdout)
        self.assertIn("2,499.99", r.stdout)
        self.assertIn("✗", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_german_format_passes(self):
        r = run_script("local_format.py", ["--market", "de", "Preis 1.234,56"])
        self.assertIn("符合德式 1.000,00", r.stdout)
        self.assertEqual(r.returncode, 0)

    def test_no_thousands_number(self):
        r = run_script("local_format.py", ["--market", "de", "Der Preis beträgt 12 Euro"])
        self.assertIn("未检出千分位数字", r.stdout)
        self.assertEqual(r.returncode, 0)


class SiteAuditTests(unittest.TestCase):
    """S2 实测修复回归:title 不吞 head 内 script/JSON-LD;泰文字素/天城文/拉丁扩展/
    土耳其 İ 词数;--market 接线 markets.json 阈值单位。零网络——直接测纯函数。"""

    def test_title_excludes_script_and_jsonld(self):
        import site_audit as sa
        html = ('<html lang="ja"><head><title>テストサイトのタイトル</title>'
                '<script type="application/ld+json">{"@context":"https://schema.org","name":"大"}</script>'
                '<script>var x=1;console.log("junk junk junk");</script>'
                '<style>body{color:red}</style></head><body><h1>見出し</h1></body></html>')
        p = sa.Page(); p.feed(html)
        self.assertEqual(p.title[0].strip(), "テストサイトのタイトル")   # 假 title 不再产生
        self.assertEqual(p.jsonld, 1)                                  # JSON-LD 仍被计数
        self.assertIn("schema.org", "".join(p.ld_buf))                  # ld 缓冲正常

    def test_wc_script_aware(self):
        import site_audit as sa
        # 6+ 站触发数十万字符假 title 的形态:title 后跟巨型 JSON-LD
        html = "<html><head><title>Good Title Here</title><script>{\"" + "a" * 500000 + "\"}</script></head></html>"
        p = sa.Page(); p.feed(html)
        self.assertEqual(p.title[0].strip(), "Good Title Here")

    def test_wc_thai_grapheme(self):
        import site_audit as sa
        t = "สวัสดีครับ"                       # 10 码点,3 个组合标记(Mn)
        self.assertEqual(sa.wc(t), 7)            # 字素近似:泰文不再计 0/不按码点高估
        self.assertEqual(sa.unit_len(t, "grapheme"), 7)
        self.assertEqual(len(t), 10)             # 旧口径(码点)确实高估 30%+

    def test_wc_devanagari_not_zero(self):
        import site_audit as sa
        self.assertGreater(sa.wc("यह एक हिन्दी वाक्य है"), 0)   # 天城文块逐字计——此前恒 0

    def test_wc_latin_extended_words_not_split(self):
        import site_audit as sa
        self.assertEqual(sa.wc("thời trang nam giảm giá"), 5)   # 越南 0x1EA0-1EF9
        self.assertEqual(sa.wc("żółć źrebię gęśl"), 3)          # 波兰 0x0100-0x017F
        self.assertEqual(sa.wc("çalışma özellikleri"), 2)       # 土耳其/西欧变音

    def test_wc_other_alphabetic_scripts(self):
        import site_audit as sa
        self.assertEqual(sa.wc("اليوم السابع أخبار مصر"), 4)      # 阿文——youm7 验证站
        self.assertEqual(sa.wc("Привет мир как дела"), 4)         # 西里尔
        self.assertEqual(sa.wc("SEO工具で分析"), 6)                # 混排:1 拉丁词+5 CJK 字

    def test_wc_turkish_dotted_i(self):
        import site_audit as sa
        self.assertEqual(sa.wc("İstanbul haritası"), 2)
        self.assertEqual(sa.wc("I\u0307stanbul haritası"), 2)   # 分解形 İ 不拆词(U+0307 清洗)

    def test_market_thresholds_from_markets_json(self):
        import site_audit as sa
        ja = sa.load_market("ja")
        self.assertEqual((ja["title_limit"]["value"], ja["title_limit"]["unit"]), (32, "fullwidth"))
        self.assertEqual(sa.unit_len("ラ" * 30 + "ab", "fullwidth"), 31)  # 30 全角+2 半角×0.5
        th = sa.load_market("th")
        self.assertEqual(th["title_limit"]["unit"], "grapheme")
        self.assertEqual(sa.load_market("en")["desc_limit"]["value"], 155)

    def test_unknown_market_rejected(self):
        r = run_script("site_audit.py", ["https://example.com", "--market", "xx"])
        self.assertIn("未知市场 xx", r.stdout + r.stderr)

    def test_fullwidth_ja_title_over_limit_offline(self):
        import site_audit as sa
        t = "ラ" * 40
        tl = sa.load_market("ja")["title_limit"]
        self.assertGreater(sa.unit_len(t, tl["unit"]), tl["value"])   # 40 全角 > 32


class HeadCheckChineseScopeTests(unittest.TestCase):
    """itemprop 微信/QQ 三件套 WARN 只对中文场景报(zh 市场/中文内容),
    日文(假名)页不再产生跨市场噪音。stdin 输入,零网络。"""

    @staticmethod
    def run_head(html, *extra):
        return run_script("head_check.py", ["-", *extra], stdin=html)

    def test_english_page_no_wechat_warn(self):
        html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<title>Example Domain</title><meta name="viewport" content="width=device-width">'
                '<meta property="og:image" content="https://example.com/i.png"></head>'
                '<body><h1>Example</h1></body></html>')
        r = self.run_head(html)
        self.assertIn("itemprop 三件套跳过", r.stdout)
        self.assertNotIn("微信/QQ 分享 itemprop", r.stdout)

    def test_chinese_page_reports_itemprop(self):
        html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<title>示例站点首页标题</title><meta name="viewport" content="width=device-width">'
                '<meta property="og:image" content="https://example.com/i.png"></head>'
                '<body><p>这是中文正文内容示例页面。</p></body></html>')
        r = self.run_head(html)
        self.assertIn("微信/QQ 分享 itemprop 三件套缺失", r.stdout)

    def test_japanese_kana_page_no_wechat_warn(self):
        html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
                '<title>日本語のページタイトルです</title><meta name="viewport" content="width=device-width">'
                '<meta property="og:image" content="https://example.com/i.png"></head>'
                '<body><p>これは日本語の本文です。ひらがなとカタカナがある。</p></body></html>')
        r = self.run_head(html)
        self.assertIn("itemprop 三件套跳过", r.stdout)
        self.assertNotIn("微信/QQ 分享 itemprop", r.stdout)   # 汉字(kanji)≠中文——kana 判日文

    def test_market_zh_forces_report(self):
        html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<title>English Page Title</title><meta name="viewport" content="width=device-width">'
                '<meta property="og:image" content="https://example.com/i.png"></head>'
                '<body><p>plain english</p></body></html>')
        r = self.run_head(html, "--market", "zh")
        self.assertIn("微信/QQ 分享 itemprop 三件套缺失", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
