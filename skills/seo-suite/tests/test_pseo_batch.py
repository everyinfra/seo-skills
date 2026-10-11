#!/usr/bin/env python3
"""pseo_batch_gate.py golden 用例(stdlib unittest,合成 jsonl,零网络)。
闸门数字钉死 references/technical/programmatic-seo-gates.md:40/30% 唯一度、
100 WARNING/500 STOP、页型地板(product 400/article 800)、批次标题集唯一性
(必须不同区块全同→STOP)、样板≥60%;规格=pipeline-completeness.md R3-2。
覆盖:每闸独立(数据闸/爆炸预警/Simhash 近重复+分桶等价/唯一度三档/样板比/页型地板/
渲染产物)+ 组合与边界(唯一度 40%/30%、警告 99/100/500)+ 大数据集(2103 条>2000
触发签名分桶,band 哈希冲突容忍)+ CJK bigram(中文全同 body 不得漏检——naive \\w+
分词会把中文整句坍缩成单 token,唯一度假高)。
独立可运行:python3 tests/test_pseo_batch.py;也被 run_tests.py 自动发现。"""
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
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "pseo_batch_gate.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_jsonl(recs_or_lines):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for r in recs_or_lines:
        f.write((r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n")
    f.close()
    return f.name


def rec(key, title=None, h1=None, body=None, desc="d", facts=None, axes=None, **kw):
    """合成记录:默认全必填在场、token 级全唯一(唯一度 100%,不污染被测闸)。"""
    r = {"key": key, "axis_values": axes if axes is not None else {},
         "facts": facts if facts is not None else [],
         "title": title if title is not None else "T" + key,
         "desc": desc, "h1": h1 if h1 is not None else "H" + key,
         "body": body if body is not None else " ".join("%sw%d" % (key, i) for i in range(6))}
    r.update(kw)
    return r


def run_json(recs, *extra):
    p = tmp_jsonl(recs)
    r = run_script(["--records", p, "--json", *extra])
    os.unlink(p)
    return r


class TokenizerAndSimhashTests(unittest.TestCase):
    """CJK bigram 分词 / 词数口径(site_audit:拉丁词+CJK 字)/ Simhash 稳定性 / 分桶等价。"""

    def test_cjk_bigram_tokens(self):
        import pseo_batch_gate as gate
        self.assertEqual(gate.tokens("北京最好的烤鸭店"),
                         ["北京", "京最", "最好", "好的", "的烤", "烤鸭", "鸭店"])
        self.assertEqual(gate.tokens("SEO工具で分析"),
                         ["seo", "工具", "具で", "で分", "分析"])
        self.assertEqual(gate.tokens("单"), ["单"])          # 单字 CJK 流保留单字
        self.assertEqual(gate.tokens("Mixed 中英 text"), ["mixed", "text", "中英"])

    def test_wc_cjk_convention(self):
        import pseo_batch_gate as gate
        self.assertEqual(gate.wc("SEO工具で分析"), 6)        # 1 拉丁词 + 5 CJK 字
        self.assertEqual(gate.wc("北京烤鸭 best"), 5)        # 4 字 + 1 词
        self.assertEqual(gate.wc("one two three"), 3)

    def test_simhash_stable_and_latin_punct_insensitive(self):
        import pseo_batch_gate as gate
        a = "How to choose blue widgets for your home office"
        sa = gate.simhash(gate.tokens(a))
        self.assertEqual(sa, gate.simhash(gate.tokens(a)))   # 确定性
        self.assertEqual(gate.hamming(sa, gate.simhash(gate.tokens(a.replace(" ", ", ")))), 0)
        self.assertGreater(gate.hamming(sa, gate.simhash(gate.tokens(
            "Independent review of the red widgets lineup this year"))), 3)

    def test_band_bucketing_equivalent_to_pairwise(self):
        """>2000 的分桶路径与全两两结果一致(鸽笼:hamming≤3 至少共享一个 16bit band);
        band 哈希冲突只产生候选,汉明复核滤掉——不产生假阳性对。"""
        import pseo_batch_gate as gate
        sigs = {}
        for i in range(40):
            sigs["k%02d" % i] = gate.simhash(gate.tokens("word%d filler common stop tokens" % i))
        for j in range(5):                                   # 5 对精确重复
            sigs["dup%02d" % j] = sigs["k%02d" % j]
        expected = sorted(("dup%02d" % j, "k%02d" % j) for j in range(5))
        self.assertEqual(gate.near_dup_pairs(sigs, force_bands=True), expected)
        self.assertEqual(gate.near_dup_pairs(sigs, force_bands=False), expected)


class DataGateTests(unittest.TestCase):
    """①数据闸:key 重复/必填缺失→不生成(非 fatal);fact 缺 source/as_of 剔除;低质警告。"""

    def test_duplicate_key_dropped_nonfatal(self):
        r = run_json([rec("k1"), rec("k1"), rec("k2")], "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)          # 丢弃非 fatal
        rep = json.loads(r.stdout)
        self.assertEqual((rep["verdict"], rep["stats"]["records_kept"],
                          rep["stats"]["records_dropped"]), ("PASS", 2, 1))
        d = rep["dropped_records"][0]
        self.assertEqual((d["key"], d["line"]), ("k1", 2))
        self.assertIn("key 重复", d["reason"])
        self.assertIn("首见行 1", d["reason"])
        self.assertEqual(rep["warnings"], [])

    def test_missing_required_and_bad_lines_dropped(self):
        lines = [rec("k1"), {"key": "k2"}, "{bad json",
                 {"title": "x", "desc": "d", "h1": "h", "body": "b"},   # 缺 key
                 rec("k3", body=""), rec("k4")]
        r = run_json(lines, "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stats"]["records_kept"], 2)     # k1、k4
        got = [(d["key"], d["reason"]) for d in rep["dropped_records"]]
        self.assertEqual(got[0][0], "k2")                      # 行序:先必填缺失后解析失败
        self.assertIn("必填缺失: title", got[0][1])
        self.assertTrue(got[1][1].startswith("JSON 解析失败"))  # 行 3 "{bad json"
        self.assertIsNone(got[1][0])
        self.assertIn("必填缺失: key", got[2][1])
        self.assertIn("必填缺失: body", got[3][1])             # k3
        self.assertEqual([d["line"] for d in rep["dropped_records"]], [2, 3, 4, 5])

    def test_facts_missing_source_or_asof_dropped(self):
        facts = [{"value": "v1", "as_of": "2026-01-01"},      # 缺 source
                 {"value": "v2", "source": "src"}]            # 缺 as_of
        r = run_json([rec("k1", facts=facts)], "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        st = rep["stats"]
        self.assertEqual((st["facts_total"], st["facts_dropped"]), (2, 2))
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertEqual(kinds, ["fact_dropped", "fact_dropped"])
        self.assertIn("v1", rep["warnings"][0]["message"])
        self.assertIn("source", rep["warnings"][0]["message"])
        self.assertIn("v2", rep["warnings"][1]["message"])
        self.assertIn("as_of", rep["warnings"][1]["message"])

    def test_fact_quality_low_warning_and_threshold_override(self):
        facts = [{"value": "v", "source": "s", "as_of": "2026-01-01", "quality_score": 0.5}]
        r = run_json([rec("k1", facts=facts)], "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["fact_quality_low"])
        self.assertEqual(rep["stats"]["facts_dropped"], 0)    # 低质警告但 fact 保留
        r2 = run_json([rec("k1", facts=facts)], "--floor", "product=1",
                      "--min-quality", "0.3")
        self.assertEqual(json.loads(r2.stdout)["warnings"], [])   # 阈值可覆盖


class ExplosionWarningTests(unittest.TestCase):
    """②爆炸预警:组合空间 vs 记录数 >10× 双向(覆盖缺口 / 无差异化重复生成)。"""

    def test_axis_gap_warning_and_control(self):
        recs = [rec("k%d" % i, axes={"tool": "t%d" % i, "industry": "i%d" % i,
                                     "locale": "l%d" % i}) for i in range(4)]
        r = run_json(recs, "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stats"]["axis_space"], 64)      # 4×4×4
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["axis_gap"])
        self.assertIn("64", rep["warnings"][0]["message"])
        self.assertEqual(rep["verdict"], "PASS")              # 1 条警告 <100
        # 对照:两轴 4×4=16 ≤ 10×4 → 不警
        recs2 = [rec("k%d" % i, axes={"tool": "t%d" % i, "industry": "i%d" % i})
                 for i in range(4)]
        rep2 = json.loads(run_json(recs2, "--floor", "product=1").stdout)
        self.assertEqual(rep2["warnings"], [])

    def test_axis_explosion_warning(self):
        recs = [rec("k%02d" % i, axes={"tool": "hammer"}) for i in range(12)]
        r = run_json(recs, "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual((rep["stats"]["axis_space"], rep["verdict"]), (1, "PASS"))
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["axis_explosion"])
        self.assertEqual(r.returncode, 0)


class UniquenessGateTests(unittest.TestCase):
    """③唯一度:必须不同区块全同→STOP / 标题集重复→WARNING / Simhash 近重复 /
    批次唯一度三档(<30 停、30-40 警、40 边界过)/ CJK 全同 body 不漏检。"""

    def test_must_differ_blocks_identical_stop(self):
        body_a = " ".join("aw%d" % i for i in range(20))
        body_b = " ".join("bw%d" % i for i in range(20))
        r = run_json([rec("k1", title="Same Title", h1="Same H1", body=body_a),
                      rec("k2", title="Same Title", h1="Same H1", body=body_b)],
                     "--floor", "product=1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)   # STOP 阻断发布
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "STOP")
        s = rep["stop_items"][0]
        self.assertEqual(s["kind"], "must_differ_duplicate")
        self.assertEqual(s["keys"], ["k1", "k2"])
        self.assertEqual(rep["warnings"], [])                    # 全同对不重复出近重复警告
        self.assertEqual(rep["stats"]["return_to_data"], ["k1", "k2"])   # 退回数据层

    def test_title_dup_with_different_h1_warns_only(self):
        r = run_json([rec("k1", title="Shared Title", h1="H one"),
                      rec("k2", title="Shared Title", h1="H two")],
                     "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "PASS")
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["title_dup"])
        self.assertEqual(rep["warnings"][0]["key"], "k2")        # 首见保留,其余警告

    def test_near_dup_simhash_warning(self):
        """首段仅标点差异 → token 化后同签名(汉明 0)→ 近重复候选;标题集重复同步警告。"""
        para1 = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
        body_a = para1 + "\n\n" + " ".join("au%d" % i for i in range(25))
        body_b = para1.replace(" ", ", ") + ".\n\n" + " ".join("bu%d" % i for i in range(25))
        r = run_json([rec("k1", title="Dup Title Here", h1="H one", body=body_a),
                      rec("k2", title="Dup Title Here", h1="H two", body=body_b)],
                     "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertEqual(kinds, ["title_dup", "near_dup"])
        self.assertIn("k2", rep["warnings"][1]["message"])
        self.assertIn("0", rep["warnings"][1]["message"])       # 汉明距离 0
        self.assertEqual(rep["stats"]["near_dup_pairs"], 1)

    def test_uniqueness_exactly_40_passes(self):
        """边界:批次唯一度恰 40%(4/10 独有 token)→ 不进薄内容档,PASS。
        title 词全部共享(s1 s2 vs s2 s1 字符串不同但 token 同集),h1 同词,body 4/7 独有。"""
        mk = lambda u: [rec("k" + u[0], title="s1 s2", h1="s3",
                            body=" ".join([u + str(i) for i in range(1, 5)])
                                 + " s4 s5 s6"),
                        rec("k" + u[0] + "b", title="s2 s1", h1="s3",
                            body=" ".join([u + "b" + str(i) for i in range(1, 5)])
                                 + " s4 s5 s6")]
        r = run_json(mk("u"), "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stats"]["uniqueness_pct"], 40.0)
        self.assertEqual(rep["verdict"], "PASS")
        self.assertEqual(r.returncode, 0)

    def test_uniqueness_exactly_30_thin_warning(self):
        """边界:恰 30%(3/10 独有)→ 不触发 <30% 硬停,落 30-40% 薄内容档 → WARNING exit 1。"""
        mk = lambda u: [rec("k" + u, title="s1 s2", h1="s3",
                            body=" ".join([u + str(i) for i in range(1, 4)])
                                 + " s4 s5 s6 s7"),
                        rec("k" + u + "b", title="s2 s1", h1="s3",
                            body=" ".join([u + "b" + str(i) for i in range(1, 4)])
                                 + " s4 s5 s6 s7")]
        r = run_json(mk("u"), "--floor", "product=1")
        self.assertEqual(r.returncode, 1, r.stdout)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stats"]["uniqueness_pct"], 30.0)
        self.assertEqual(rep["verdict"], "WARNING")             # 30-40% 即阻断
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["uniqueness_thin"])

    def test_uniqueness_below_30_hard_stop(self):
        mk = lambda u: [rec("k" + u, title="s1 s2", h1="s3",
                            body=" ".join([u + str(i) for i in range(1, 3)])
                                 + " s4 s5 s6 s7 s8"),
                        rec("k" + u + "b", title="s2 s1", h1="s3",
                            body=" ".join([u + "b" + str(i) for i in range(1, 3)])
                                 + " s4 s5 s6 s7 s8")]
        r = run_json(mk("u"), "--floor", "product=1")
        self.assertEqual(r.returncode, 1)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "STOP")
        self.assertEqual(rep["stop_items"][0]["kind"], "uniqueness_hard_stop")
        self.assertEqual(rep["stats"]["return_to_data"], ["ku", "kub"])   # 整批退回

    def test_cjk_identical_body_not_missed(self):
        """CJK 防漏检:三城 body 全同、仅 title/h1 换城 → 唯一度须坍到 <30% 硬停。
        naive \\w+ 分词会把中文 body 坍缩成单 token(且三页相同)→ 唯一度≈75% 假通过;
        bigram 分词按字对重叠计数 → 真实 ~7%。"""
        body = ("我们实地评测了全城三十家烤鸭门店,从鸭皮酥脆度、肉质油润度到蘸酱配方"
                "逐项打分排序,这份榜单每月更新。")
        recs = []
        for city, k in (("北京", "k1"), ("上海", "k2"), ("广州", "k3")):
            recs.append(rec(k, title=city + "烤鸭店排行榜2026版",
                            h1=city + "烤鸭排行榜", body=body))
        r = run_json(recs, "--floor", "product=1")
        self.assertEqual(r.returncode, 1)
        rep = json.loads(r.stdout)
        self.assertLess(rep["stats"]["uniqueness_pct"], 30)     # naive 分词会 ≈75 → 断言失败
        self.assertEqual(rep["verdict"], "STOP")
        self.assertEqual(rep["stop_items"][0]["kind"], "uniqueness_hard_stop")


class BoilerplateTests(unittest.TestCase):
    """④样板比:跨记录公共 5-gram 占比 >60% → WARNING(样板重的批唯一度同步落 30-40%)。"""

    def test_boilerplate_over_60(self):
        S = ["sv%d" % i for i in range(100)]                  # 三页同序共享样板块
        bodies = {"a": ["au%d" % i for i in range(50)],
                  "b": ["bu%d" % i for i in range(50)],
                  "c": ["cu%d" % i for i in range(50)]}
        titles = {"a": "s1 s2", "b": "s2 s1", "c": "s1 s2 s3"}
        recs = [rec("k" + t, title=titles[t], h1="s3",
                    body=" ".join(S + bodies[t])) for t in ("a", "b", "c")]
        r = run_json(recs, "--floor", "product=1")
        self.assertEqual(r.returncode, 1)
        rep = json.loads(r.stdout)
        boiler = [w for w in rep["warnings"] if w["kind"] == "boilerplate"]
        self.assertEqual(len(boiler), 3)                       # 96/146≈66% >60%,逐页警告
        self.assertGreater(rep["stats"]["boilerplate_pct"], 60)
        self.assertIn("uniqueness_thin", [w["kind"] for w in rep["warnings"]])   # 50/153≈33%
        self.assertEqual(rep["verdict"], "WARNING")

    def test_boilerplate_below_60_silent(self):
        S = ["sv%d" % i for i in range(10)]
        recs = [rec("k" + t, body=" ".join(S + ["%su%d" % (t, i) for i in range(90)]))
                for t in ("a", "b")]
        r = run_json(recs, "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual([w["kind"] for w in rep["warnings"]], [])   # 公共 gram≈6/96<60%
        self.assertLess(rep["stats"]["boilerplate_pct"], 60)
        self.assertEqual(r.returncode, 0)


class PageFloorTests(unittest.TestCase):
    """⑤页型地板:正文词数(CJK 按字计)< 地板 → FAIL(STOP);--floor 覆盖;边界 399/400。"""

    @staticmethod
    def one(words, page_type=None):
        r = rec("k1", body=" ".join("w%d" % i for i in range(words)))
        if page_type:
            r["page_type"] = page_type
        return [r]

    def test_product_399_fail_400_pass(self):
        r = run_json(self.one(399))
        self.assertEqual(r.returncode, 1)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stop_items"][0]["kind"], "page_floor")
        self.assertIn("399", rep["stop_items"][0]["message"])
        self.assertIn("400", rep["stop_items"][0]["message"])
        r2 = run_json(self.one(400))                            # 边界:恰 400 过
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(json.loads(r2.stdout)["stats"]["word_count_min"], 400)

    def test_article_floor_and_override(self):
        r = run_json(self.one(799, "article"))
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stop_items"][0]["kind"], "page_floor")
        self.assertIn("article", rep["stop_items"][0]["message"])
        self.assertEqual(run_json(self.one(800, "article")).returncode, 0)
        r3 = run_json(self.one(799, "article"), "--floor", "article=100")
        self.assertEqual(r3.returncode, 0)                      # 地板可放宽

    def test_cjk_body_word_count_per_char(self):
        cjk = rec("k1", body="鸭" * 450)                        # 450 CJK 字 = 450 词
        short = rec("k2", body="鸭" * 350)
        r = run_json([cjk, short])
        rep = json.loads(r.stdout)
        floors = [s for s in rep["stop_items"] if s["kind"] == "page_floor"]
        self.assertEqual([s["keys"] for s in floors], [["k2"]])  # 仅 350<400 挂


class RenderedDirTests(unittest.TestCase):
    """--rendered:key.html 逐个读;缺文件→警告+按 body 判;词数以渲染产物为准。"""

    def test_missing_file_warns_and_rendered_wordcount_wins(self):
        tmp = tempfile.mkdtemp(prefix="pseo_rendered_")
        with open(os.path.join(tmp, "k1.html"), "w", encoding="utf-8") as f:
            f.write("<html><body>" + " ".join("x%d" % i for i in range(30)) + "</body></html>")
        recs = [rec("k1", body=" ".join("aw%d" % i for i in range(400))),
                rec("k2", body=" ".join("bw%d" % i for i in range(450)))]
        p = tmp_jsonl(recs)
        r = run_script(["--records", p, "--json", "--rendered", tmp])
        os.unlink(p)
        self.assertEqual(r.returncode, 1, r.stdout)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "STOP")
        self.assertEqual(rep["stop_items"][0]["kind"], "page_floor")
        self.assertEqual(rep["stop_items"][0]["keys"], ["k1"])  # 渲染产物 30 词<400
        self.assertIn("rendered", rep["stop_items"][0]["message"])
        self.assertEqual([w["kind"] for w in rep["warnings"]], ["rendered_missing"])
        self.assertEqual(rep["warnings"][0]["key"], "k2")       # k2.html 缺失→警告
        self.assertEqual(rep["stats"]["word_count_min"], 30)    # k1 用渲染词数,k2 用 body(450)


class VerdictScaleTests(unittest.TestCase):
    """⑥判定边界:警告 99→PASS / 100→WARNING / 500→STOP(硬停);大数据集分桶正确性。"""

    @staticmethod
    def batch(n):
        return [rec("q%03d" % i,
                    facts=[{"value": "v%d" % i, "source": "s", "as_of": "2026-01-01",
                            "quality_score": 0.5}],                      # 每条 1 个低质警告
                    body="q%03dw1 q%03dw2 q%03dw3 s1 s2 s3" % (i, i, i))
                for i in range(n)]

    def test_warning_count_boundaries(self):
        r99 = run_json(self.batch(99), "--floor", "product=1")
        self.assertEqual(r99.returncode, 0, r99.stderr)
        rep = json.loads(r99.stdout)
        self.assertEqual((rep["verdict"], rep["stats"]["warnings"]), ("PASS", 99))
        r100 = run_json(self.batch(100), "--floor", "product=1")
        self.assertEqual(r100.returncode, 1)
        rep = json.loads(r100.stdout)
        self.assertEqual((rep["verdict"], rep["stats"]["warnings"]), ("WARNING", 100))
        r500 = run_json(self.batch(500), "--floor", "product=1")
        self.assertEqual(r500.returncode, 1)
        rep = json.loads(r500.stdout)
        self.assertEqual(rep["verdict"], "STOP")                # 500+ 硬停
        self.assertEqual(rep["stop_items"][-1]["kind"], "warning_overload_500")
        self.assertEqual(rep["stats"]["warnings"], 500)
        self.assertEqual(rep["stats"]["return_to_data"],
                         sorted("q%03d" % i for i in range(500)))   # 整批退回数据层

    def test_large_batch_bucketing_finds_all_dup_pairs(self):
        """>2000 条走分桶:3 对精确重复(title+首段同,h1 异→不触发必须不同区块 STOP)
        全部检出;band 哈希冲突被汉明复核滤掉(近重复对恰 3,无假阳性)。"""
        recs = [rec("r%04d" % i, body="r%04dw1 r%04dw2 r%04dw3 r%04dw4 r%04dw5 r%04dw6"
                    % (i, i, i, i, i, i)) for i in range(2100)]
        for j in range(3):
            src = recs[1000 + j]
            recs.append({"key": "d%04d" % j, "axis_values": {}, "facts": [],
                         "title": src["title"], "desc": "d", "h1": "Hd%04d" % j,
                         "body": src["body"]})
        self.assertEqual(len(recs), 2103)                       # >2000 → 分桶路径
        r = run_json(recs, "--floor", "product=1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["stats"]["records_kept"], 2103)
        self.assertEqual(rep["stats"]["near_dup_pairs"], 3)      # 冲突容忍:不漏不假阳
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertEqual(kinds.count("near_dup"), 3)
        self.assertEqual(kinds.count("title_dup"), 3)
        self.assertEqual(rep["verdict"], "PASS")
        self.assertGreater(rep["stats"]["uniqueness_pct"], 90)  # 均值不被 6 条低唯页拖垮


class OutputContractTests(unittest.TestCase):
    """--json schema / markdown 渲染 / --help / 用法错误 exit 2(套件契约)。"""

    def test_json_schema_and_markdown(self):
        r = run_json([rec("k1"), rec("k2")], "--floor", "product=1")
        rep = json.loads(r.stdout)
        self.assertEqual(set(rep), {"verdict", "stats", "stop_items",
                                    "warnings", "dropped_records"})
        self.assertEqual(rep["verdict"], "PASS")
        p = tmp_jsonl([rec("k1"), rec("k2")])
        rm = run_script(["--records", p, "--floor", "product=1"])
        os.unlink(p)
        self.assertEqual(rm.returncode, 0, rm.stderr)
        self.assertIn("## pSEO 批次闸门:PASS", rm.stdout)
        self.assertIn("唯一度", rm.stdout)

    def test_help_and_usage_errors(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout)
        self.assertIn("唯一度", r.stdout)
        self.assertIn("500", r.stdout)
        p = tmp_jsonl([rec("k1")])
        for args in ([], ["--bogus"], ["--records"], ["--records", "/nonexistent/x.jsonl"],
                     ["--records", p, "--rendered", "/nonexistent/dir"],
                     ["--records", p, "--floor", "bad"],
                     ["--records", p, "--min-quality", "abc"]):
            self.assertEqual(run_script(args).returncode, 2, args)
        os.unlink(p)


if __name__ == "__main__":
    unittest.main(verbosity=1)
