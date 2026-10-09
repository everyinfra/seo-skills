#!/usr/bin/env python3
"""seo-suite golden 用例测试层(stdlib unittest,合成数据,零网络)。
每个脚本 2-3 个固定输入→期望输出断言;`python3 tests/run_tests.py` 运行,
全绿退出码 0,任何失败非零(被 scripts/self_check.py 以 subprocess 消费)。
grid_rank 无独立脚本——按 references/monitoring/local-grid-ranking.md 的
源码级口径实现被测函数,并钉死该文档自带的 3×3 算例(ARP=2.2/ATRP=8.4/SoLV=55.6)。"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta

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


class MarketLintV3Tests(unittest.TestCase):
    """v3 常开机检(⑩)与 special_checks 第二批映射(⑨):格式/语言/robots/内容/结构"""

    def _lint(self, market, content):
        p = tmp_file(content)
        r = run_script("market_lint.py", ["--market", market, p])
        os.unlink(p)
        return r.stdout

    def test_v3_phone_prefix_mismatch(self):
        out = self._lint("zh", "联系我们\n咨询热线说明\n价格 199 元,咨询 +1 555 1234 即可购买下单。")
        self.assertIn("[v3-FAIL] 电话前缀", out)               # +1 而非 +86
        out_ok = self._lint("zh", "联系我们\n咨询热线说明\n价格 199 元,咨询 +86 138 0013 8000 即可购买下单。")
        self.assertIn("电话前缀一致 +86", out_ok)

    def test_v3_date_format_foreign(self):
        out = self._lint("de", "Preisvergleich\nKaufberatung\nStand 10/9/2026 gemäß Studie von 2026.")
        self.assertIn("[v3-FAIL] 日期格式", out)               # de 应为 09.10.2026
        out_ok = self._lint("de", "Preisvergleich\nKaufberatung\nStand 09.10.2026 gemäß Studie von 2026.")
        self.assertIn("市场格式日期在场", out_ok)

    def test_v3_ai_meta_exits_page(self):
        html = ('<html><head><title>Test</title>'
                '<meta name="robots" content="noai,noimageai"></head>'
                '<body>Beispielseite mit Inhalt.</body></html>')
        out = self._lint("en", html)
        self.assertIn("[v3-FAIL] AI 退出 meta", out)
        self.assertIn("noai", out)

    def test_v3_currency_not_localized(self):
        out = self._lint("de", "Produktvergleich\nPreise\nDas Produkt kostet $ 199 laut Hersteller.")
        self.assertIn("[v3-FAIL] 货币符号", out)               # de 期望 €
        out_ok = self._lint("de", "Produktvergleich\nPreise\nDas Produkt kostet 199 € laut Hersteller.")
        self.assertIn("货币符号本地化一致", out_ok)

    def test_v3_sentence_cv_ai_signature(self):
        body = "\n".join("Dieser Satz hat genau neun Worte hier drin." for _ in range(8))
        out = self._lint("de", "Beispielseite\nBeschreibung\n" + body)
        self.assertIn("[v3-FAIL] 句长 CV", out)                # CV=0 → AI 均匀签名

    def test_v3_auto_ratio_line(self):
        out = self._lint("ja", "テストタイトル\n説明文\n本文は短いテストです。")
        self.assertIn("AUTO 比例:", out)
        self.assertIn("v3 常开机检: OK", out)

    def test_ko_nosourceinfo_auto(self):
        html_bad = ('<html><head><title>네이버 블로그</title>'
                    '<meta name="robots" content="nosourceinfo"></head><body>콘텐츠 내용입니다.</body></html>')
        out = self._lint("ko", html_bad)
        self.assertIn("[WARN] [AUTO] nosourceinfo meta 决策记录", out)
        self.assertIn("该页退出 Naver AI Briefing", out)
        html_ok = ('<html><head><title>네이버 블로그</title></head><body>콘텐츠 내용입니다.</body></html>')
        out2 = self._lint("ko", html_ok)
        self.assertIn("未见 nosourceinfo", out2)

    def test_de_werbung_sponsored_disclosure(self):
        base = ('<html><head><title>Test</title></head><body><span class="ad-label">Anzeige</span>'
                ' Dieser Artikel ist gesponsert. Mehr dazu im Beitrag.'
                ' <a href="https://b.de/x">Link</a></body></html>')
        out_bad = self._lint("de", base)
        self.assertIn("[WARN] [AUTO] 软文 Werbung", out_bad)
        self.assertIn("披露半套", out_bad)
        out_ok = self._lint("de", base.replace('<a href="https://b.de/x">', '<a rel="sponsored" href="https://b.de/x">'))
        self.assertIn("双披露在场", out_ok)

    def test_v3_h2_question_ratio(self):
        html = ('<html><head><title>T</title></head><body>'
                '<h2>Was ist SEO?</h2><h2>Wie funktioniert Indexierung?</h2>'
                '<h2>Was kostet SEO?</h2><h2>Historie der Suchmaschinen</h2>'
                '<p>Inhalt mit Beispielen.</p></body></html>')
        out = self._lint("de", html)
        self.assertIn("疑问式 H2 3/4", out)


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


class MonitorHardeningTests(unittest.TestCase):
    """20 路审计融入后的 monitor.py 加固回归(全部离线,合成数据,零网络):
    secret 守卫/visibility unparseable/重定向 SSRF/抑制树/双窗口/SSL 梯度/
    字段级 diff+selector/suppressed 退出码/状态机+quarantine+prune。"""

    @staticmethod
    def _fresh_monitor_dir():
        import monitor as M
        tmp = tempfile.mkdtemp(prefix="mon_hard_")
        mdir = os.path.join(tmp, ".seo-monitor")
        rc = M.cmd_init(M.build_parser().parse_args(
            ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
        assert rc == 0
        return M, mdir

    @staticmethod
    def _insert_run(M, conn, pages=None, robots=None, visibility=None, ssl=None, status="ok",
                    ts_offset_days=0):
        from datetime import datetime, timedelta
        ts = (datetime.now() - timedelta(days=ts_offset_days)).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
            "VALUES(?,?,?,'daily',0,'')", (ts, "daily", status))
        rid = cur.lastrowid
        for check, key, value in [("pages", "/", pages or {}),
                                  ("robots", "robots", robots or {}),
                                  ("visibility", "site", visibility or {}),
                                  ("ssl", "cert", ssl or {})]:
            if value:
                conn.execute(
                    "INSERT INTO snapshots(run_id,ts,\"check\",key,value,hash) VALUES(?,?,?,?,?,?)",
                    (rid, ts, check, key, json.dumps(value), "h%d" % rid))
        conn.commit()
        return rid

    def test_secret_config_rejected(self):
        """P0-6:channels 明文 webhook 拒写;env 引用形态放行。"""
        M, mdir = self._fresh_monitor_dir()
        cfg = M.load_config(mdir)
        self.assertEqual(M.find_config_secrets(cfg), [])
        bad = json.loads(json.dumps(cfg))
        bad["channels"]["slack"]["webhook_url"] = "https://hooks.slack.com/services/T/B/xxx"
        self.assertTrue(M.find_config_secrets(bad))
        with self.assertRaises(SystemExit):
            M.save_config(mdir, bad)
        # 拒写后原 config 未被破坏
        self.assertEqual(M.load_config(mdir)["channels"]["slack"], {"env": "SEO_MONITOR_SLACK_WEBHOOK"})

    def test_visibility_unparseable_when_no_cites(self):
        """P0-7:Bing 200 但解析不出 cite(无 captcha 文案)→ unparseable,不当真 0。"""
        import monitor as M
        orig = M.http_get
        M.http_get = lambda url, timeout=M.FETCH_TIMEOUT: {
            "status": 200, "final_url": url, "elapsed_ms": 10, "body": "<html>redesigned dom</html>"}
        try:
            out = M.check_visibility("https://example.com")
        finally:
            M.http_get = orig
        self.assertEqual(out["state"], "unparseable")
        self.assertNotIn("visible_pages", out["metrics"])

    def test_redirect_ssrf_per_hop(self):
        """P0-5:302 跳到元数据端点/环回/私网必须逐跳拒掉(stub DNS,不受本机 fake-IP 代理影响)。"""
        import monitor as M
        import socket
        orig_getaddrinfo = socket.getaddrinfo

        def fake_getaddrinfo(host, *a, **k):
            return [(2, 1, 6, "", (host, 0))]   # 把 host 本身当解析结果(IP 字面量直通)
        socket.getaddrinfo = fake_getaddrinfo
        M._ssrf_cache.clear()
        try:
            for evil in ("http://169.254.169.254/latest/meta-data", "http://127.0.0.1:8080/x",
                         "http://10.0.0.5/internal", "ftp://example.com/f"):
                with self.assertRaises(M.FetchError):
                    # newurl(第 6 参)是重定向目标——这才是被复查的 URL
                    M._RedirectGuard().redirect_request(
                        None, None, 302, "Found", {}, evil)
        finally:
            socket.getaddrinfo = orig_getaddrinfo
            M._ssrf_cache.clear()

    def test_inhibition_tree(self):
        """P1-10:homepage_down 抑制 key_page_down(替 Top-K)。"""
        import monitor as M
        cfg = {"thresholds": dict(M.DEFAULT_THRESHOLDS)}
        prev = {"pages": {"/": {"status": 200}, "/a": {"status": 200}, "/b": {"status": 200}}}
        curr = {"pages": {"/": {"status": 503}, "/a": {"status": 403}, "/b": {"status": 404}}}
        inhib = []
        alerts = M.compute_alerts(prev, curr, cfg, inhibited_out=inhib)
        codes = {a["code"] for a in alerts}
        self.assertIn("homepage_down", codes)
        self.assertNotIn("key_page_down", codes)
        self.assertEqual({i["inhibited_by"] for i in inhib}, {"homepage_down"})
        # 无根因时页面级告警保留
        curr2 = {"pages": {"/": {"status": 200}, "/a": {"status": 404}}}
        alerts2 = M.compute_alerts(prev, curr2, cfg)
        self.assertIn("key_page_down", {a["code"] for a in alerts2})

    def test_dual_window_downgrade(self):
        """P1-9:7 天基线健康→critical;基线同样异常→降 info。"""
        import monitor as M
        cfg = {"thresholds": dict(M.DEFAULT_THRESHOLDS)}
        prev = {"pages": {"/pricing": {"status": 200}},
                "visibility": {"site": {"visible_pages": 5}},
                "robots": {"robots": {"sitewide_block": False}}}
        curr = {"pages": {"/pricing": {"status": 404}},
                "visibility": {"site": {"visible_pages": 0}},
                "robots": {"robots": {"sitewide_block": True}}}
        healthy_bl = json.loads(json.dumps(prev))
        alerts = M.compute_alerts(prev, curr, cfg, baseline=healthy_bl)
        lv = {a["code"]: a["level"] for a in alerts}
        self.assertEqual(lv["key_page_down"], "critical")
        self.assertEqual(lv["visibility_zero"], "critical")
        self.assertEqual(lv["robots_sitewide_block"], "critical")
        bad_bl = json.loads(json.dumps(prev))
        bad_bl["pages"]["/pricing"]["status"] = 404
        bad_bl["visibility"]["site"]["visible_pages"] = 0
        bad_bl["robots"]["robots"]["sitewide_block"] = True
        alerts2 = M.compute_alerts(prev, curr, cfg, baseline=bad_bl)
        lv2 = {a["code"]: a["level"] for a in alerts2}
        self.assertEqual(lv2["key_page_down"], "info")
        self.assertEqual(lv2["visibility_zero"], "info")
        self.assertEqual(lv2["robots_sitewide_block"], "info")

    def test_ssl_gradient_and_expect_substring(self):
        """P1-15:SSL 30/14/7/0 梯度;expect_substring→content_regression warn。"""
        import monitor as M
        cfg = {"thresholds": dict(M.DEFAULT_THRESHOLDS)}
        for days, level in ((5, "critical"), (12, "warn"), (20, "info"), (-1, "critical")):
            alerts = M.compute_alerts({}, {"ssl": {"cert": {"days_left": days}}}, cfg)
            hits = [a for a in alerts if "ssl_cert" in a["code"]]
            self.assertEqual(len(hits), 1, "days=%d" % days)
            self.assertEqual(hits[0]["level"], level, "days=%d" % days)
        alerts = M.compute_alerts({}, {"pages": {"/": {"status": 200, "expect_ok": False}}}, cfg)
        hit = [a for a in alerts if a["code"] == "content_regression"]
        self.assertEqual(len(hit), 1) and self.assertEqual(hit[0]["level"], "warn")

    def test_field_level_diff_and_selector(self):
        """P1-11:og 提取 + selector 圈定 + title_meta_drift 只报变化的字段。"""
        import monitor as M
        t, md, ca, ogt, ogd = M.extract_head(
            "<title>T</title><meta name='description' content='D'>"
            "<link rel='canonical' href='https://x/c'>"
            "<meta property='og:title' content='OT'><meta property='og:description' content='OD'>")
        self.assertEqual((t, md, ca, ogt, ogd), ("T", "D", "https://x/c", "OT", "OD"))
        html = "<body><h1 id='main'>Hello World</h1><p class='price'>$9</p><p>noise</p></body>"
        self.assertEqual(M.extract_selector(html, "#main"), "Hello World")
        self.assertEqual(M.extract_selector(html, "p.price"), "$9")
        self.assertEqual(M.extract_selector(html, "h1"), "Hello World")
        cfg = {"thresholds": dict(M.DEFAULT_THRESHOLDS)}
        prev = {"pages": {"/": {"title": "A", "meta_desc": "M"}}}
        curr = {"pages": {"/": {"title": "B", "meta_desc": "M"}}}
        drift = [a for a in M.compute_alerts(prev, curr, cfg) if a["code"] == "title_meta_drift"]
        self.assertEqual(drift[0]["details"]["fields"], ["title"])

    def test_suppressed_excluded_from_rc_and_notify_payload(self):
        """P0-1:首 diff critical rc=1;冷却期内重 diff→suppressed→rc=0(不空转触发 notify)。"""
        M, mdir = self._fresh_monitor_dir()
        conn = M.open_db(mdir)
        self._insert_run(M, conn, pages={"status": 200, "latency_ms": 100.0, "title": "T"})
        self._insert_run(M, conn, pages={"status": 404, "latency_ms": 120.0, "title": "T"})
        conn.close()
        out = os.path.join(mdir, "alerts.json")
        a1 = M.build_parser().parse_args(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(M.cmd_diff(a1), 1)
        with open(out, encoding="utf-8") as f:
            p1 = json.load(f)
        self.assertEqual(p1["counts"]["critical"], 1)
        self.assertEqual(p1["alerts"][0]["code"], "homepage_down")
        a2 = M.build_parser().parse_args(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(M.cmd_diff(a2), 0, "suppressed 告警不计入 counts/退出码")
        with open(out, encoding="utf-8") as f:
            p2 = json.load(f)
        self.assertEqual(p2["counts"]["critical"], 0)
        self.assertTrue(all(a.get("suppressed") for a in p2["alerts"]))
        self.assertEqual(p2["suppressed"], ["homepage_down:/"])

    def test_state_machine_quarantine_and_prune(self):
        """P0-4/P1-12:partial 不当基线;quarantine 隔离后 diff 不再用它;prune 裁剪。"""
        M, mdir = self._fresh_monitor_dir()
        conn = M.open_db(mdir)
        r1 = self._insert_run(M, conn, pages={"status": 200, "title": "T"})
        r2 = self._insert_run(M, conn, pages={"status": 404, "title": "T"}, status="partial")
        self.assertEqual(M.latest_run_ids(conn, 5), [r1], "partial 不充当基线")
        # sweep:卡死 running 超 30min → failed
        from datetime import datetime, timedelta
        old = (datetime.now() - timedelta(minutes=31)).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
            "VALUES(?,?, 'running','daily',0,'')", (old, "daily"))
        stale_id = cur.lastrowid
        conn.commit()
        self.assertEqual(M.sweep_stale_runs(conn), 1)
        self.assertEqual(conn.execute("SELECT status FROM runs WHERE id=?", (stale_id,)).fetchone()[0],
                         "failed")
        conn.close()
        # quarantine CLI:r1 隔离后无可对比 ok run,diff rc=4;undo 恢复
        rc = M.cmd_quarantine(M.build_parser().parse_args(["quarantine", str(r1), "--dir", mdir]))
        self.assertEqual(rc, 0)
        conn = M.open_db(mdir)
        self.assertEqual(M.latest_run_ids(conn, 5), [])
        conn.close()
        rc = M.cmd_diff(M.build_parser().parse_args(["diff", "--dir", mdir]))
        self.assertEqual(rc, 4)
        rc = M.cmd_quarantine(M.build_parser().parse_args(["quarantine", str(r1), "--undo", "--dir", mdir]))
        self.assertEqual(rc, 0)
        # prune:只保留最近 N
        conn = M.open_db(mdir)
        for _ in range(5):
            self._insert_run(M, conn, pages={"status": 200, "title": "T"})
        removed = M.prune(conn, mdir, keep=2)
        conn.close()
        self.assertGreaterEqual(removed, 4)
        conn = M.open_db(mdir)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 2)
        conn.close()

    def test_maintenance_window_blocks_diff_alerts(self):
        """P1-15:维护窗口内 diff 只留档不产告警(rc=0,counts 全 0)。"""
        M, mdir = self._fresh_monitor_dir()
        conn = M.open_db(mdir)
        self._insert_run(M, conn, pages={"status": 200, "title": "T"})
        self._insert_run(M, conn, pages={"status": 404, "title": "T"})
        conn.close()
        from datetime import datetime as DT, timedelta as TD
        cfg = M.load_config(mdir)
        cfg["maintenance_windows"] = [
            {"from": (DT.now() - TD(hours=1)).isoformat(timespec="seconds"),
             "to": (DT.now() + TD(hours=1)).isoformat(timespec="seconds"), "reason": "改版"}]
        M.save_config(mdir, cfg)
        out = os.path.join(mdir, "alerts.json")
        rc = M.cmd_diff(M.build_parser().parse_args(["diff", "--dir", mdir, "--out", out]))
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["alerts"], [])
        self.assertIn("maintenance", payload)


class NotifyHardeningTests(unittest.TestCase):
    """notify.py 加固回归:suppressed 剔除/--max-age 陈旧拒发/通用 webhook 抽象/
    URL 脱敏/flush 渠道失败保批/dead_man 停摆检测。全部离线。"""

    @staticmethod
    def _fresh_notify_dir():
        import notify as N
        tmp = tempfile.mkdtemp(prefix="nfy_hard_")
        mdir = os.path.join(tmp, ".seo-monitor")
        os.makedirs(mdir)
        cfg = {"site": "https://example.com", "run_cadence_hours": 24,
               "channels": {"slack": {}, "discord": {}, "telegram": {},
                            "email": {"smtp_host": "", "from": "", "to": []},
                            "webhook": {}}}
        with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        return N, mdir

    @staticmethod
    def _alerts_file(mdir, generated=None, alerts=None):
        path = os.path.join(mdir, "alerts-%d.json" % int(time.time() * 1000))
        payload = {"site": "https://example.com",
                   "generated": generated or datetime.now().isoformat(timespec="seconds"),
                   "alerts": alerts if alerts is not None else [
                       {"level": "critical", "code": "homepage_down", "key": "/",
                        "message": "503", "action": "回滚", "boundary": "auto"}]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return path

    def test_route_alerts_skips_suppressed(self):
        """P0-1:冷却命中的 suppressed 告警不进任何通知路径。"""
        N, mdir = self._fresh_notify_dir()
        st = N.load_state(os.path.join(mdir, N.STATE_FILE))
        alerts = [
            {"level": "critical", "code": "homepage_down", "key": "/", "message": "503(冷却中)",
             "suppressed": True},
            {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"},
        ]
        imm, nw, ni, ns = N.route_alerts(alerts, st)
        self.assertEqual((len(imm), nw, ns), (0, 1, 1))
        self.assertEqual(len(st["pending_warn"]), 1)

    def test_max_age_rejects_stale_alerts(self):
        """P0-2:陈旧 alerts.json 拒发 rc=4;--max-age 0 关闭检查。"""
        N, mdir = self._fresh_notify_dir()
        stale = self._alerts_file(mdir, generated="2020-01-01T00:00:00")
        rc = N.cmd_notify(N.build_parser().parse_args(["run", "--dir", mdir, "--alerts", stale]))
        self.assertEqual(rc, 4)
        rc = N.cmd_notify(N.build_parser().parse_args(
            ["run", "--dir", mdir, "--alerts", stale, "--max-age", "0"]))
        self.assertEqual(rc, 0)

    def test_generic_webhook_schemes(self):
        """P1-14:Apprise 式 scheme→载荷形态映射(jsons/form/texts)。"""
        import notify as N
        calls = []
        orig_json, orig_raw = N._post_json, N._post_raw
        N._post_json = lambda url, payload, timeout=15: (calls.append(("json", url, payload)) or (200, "ok"))
        N._post_raw = lambda url, data, ct, timeout=15: (calls.append(("raw", url, data)) or (200, "ok"))
        try:
            N.send_generic_webhook("jsons://hooks.example.test/abc", "hello")
            self.assertEqual(calls[-1], ("json", "https://hooks.example.test/abc", {"text": "hello"}))
            N.send_generic_webhook("form://h.test/p", "a=b")
            self.assertEqual(calls[-1][2], b"text=a%3Db")
            N.send_generic_webhook("texts://h.test/t", "plain")
            self.assertEqual(calls[-1][2], b"plain")
            N.send_generic_webhook("https://plain.example/x", "m")
            self.assertEqual(calls[-1][0], "json")  # 裸 https 默认 JSON
        finally:
            N._post_json, N._post_raw = orig_json, orig_raw

    def test_redact_keeps_host_hides_token(self):
        """P1-14:异常 detail 脱敏——host 可见,token 段打码。"""
        import notify as N
        out = N.redact("HTTP Error: url=https://api.telegram.org/bot12345:AAFF-xyz/sendMessage failed")
        self.assertIn("api.telegram.org", out)
        self.assertNotIn("12345:AAFF-xyz", out)

    def test_flush_keeps_pending_on_channel_failure(self):
        """P1-14(audit 05-§3 反向问题):渠道发送失败时 pending 保留,不丢告警。"""
        N, mdir = self._fresh_notify_dir()
        st = N.load_state(os.path.join(mdir, N.STATE_FILE))
        imm, nw, ni, ns = N.route_alerts(
            [{"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"}], st)
        N.save_state(os.path.join(mdir, N.STATE_FILE), st)
        fresh = self._alerts_file(mdir)
        orig_targets = N.channel_targets
        N.channel_targets = lambda cfg: [("slack", lambda msg: (_ for _ in ()).throw(IOError("boom")))]
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", fresh, "--flush", "warn"]))
        finally:
            N.channel_targets = orig_targets
        self.assertEqual(rc, 1)
        st2 = N.load_state(os.path.join(mdir, N.STATE_FILE))
        self.assertEqual(len(st2["pending_warn"]), 1, "渠道失败时 warn 批必须保留")

    def test_dead_man_alert_on_stale_runs(self):
        """P1-8:距上次成功 run 超 2×周期 → dead_man 告警;新鲜 run → None。"""
        N, mdir = self._fresh_notify_dir()
        self.assertIsNone(N.dead_man_alert(mdir, {"run_cadence_hours": 24}))  # 无 db
        import sqlite3
        conn = sqlite3.connect(os.path.join(mdir, "monitor.db"))
        conn.execute("CREATE TABLE runs(id INTEGER PRIMARY KEY, ts TEXT, kind TEXT, status TEXT)")
        conn.execute("INSERT INTO runs(ts,kind,status) VALUES(?,?,?)",
                     ((datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds"),
                      "daily", "ok"))
        conn.commit()
        cfg = json.load(open(os.path.join(mdir, "config.json"), encoding="utf-8"))
        self.assertIsNone(N.dead_man_alert(mdir, cfg))          # 1h < 48h
        conn.execute("UPDATE runs SET ts=?",
                     ((datetime.now() - timedelta(hours=72)).isoformat(timespec="seconds"),))
        conn.commit()
        conn.close()
        dm = N.dead_man_alert(mdir, cfg)
        self.assertIsNotNone(dm)
        self.assertEqual((dm["code"], dm["level"]), ("dead_man", "warn"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
