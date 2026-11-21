#!/usr/bin/env python3
"""判分器校准(规则:标准答案必过、原样必不过)。

锁住三件事:
  1. 标准答案(fixtures/gold/*.json,内容取自答案表)全部断言都过;
  2. 裸跑(不停下、不确认、直接给建议)的 process 类断言全不过;
  3. 每条断言各一个刚好不过的反例:只让那一条不过,其余照旧全过。
另有转录解析、驱动取回话的小测试。只用标准库,不调模型:python3 -m unittest tools/evals/onboarding/test_grade.py
"""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, HERE)
sys.path.insert(0, FIX)
import build as B  # noqa: E402
import grade as G  # noqa: E402

ANSWERS = os.path.join(HERE, "answers")
SITE = "http://127.0.0.1:8899"
GOLD = ["idea", "prelaunch", "mature", "change", "calib-correct", "calib-unknown", "calib-skip"]


def run(ex, tmp):
    p = B.materialize(ex, tmp)
    return G.grade(ex["scenario"], p["ws"], p["transcript"], p["driver_log"], scenarios=p["scenarios"],
                   answers_dir=ANSWERS, site=p.get("site"))


def verdict(r):
    return {a["id"]: a["pass"] for a in r["assertions"]}


def ev_text(turn, needle, new):
    for ev in turn["events"]:
        if "text" in ev and needle in ev["text"]:
            ev["text"] = ev["text"].replace(needle, new)
            return
    raise AssertionError("没找到要改的文本:%s" % needle)


# ---------------------------------------------------------------------------
# 反例:(名字, 基于哪份标准答案, 改法, 只该不过的断言)
# ---------------------------------------------------------------------------

def m_facts(ex):
    ex["profile"]["facts"]["product.lines"]["value"] = ["健康提醒(疫苗、驱虫、体检)", "病历档案(拍照存档、OCR 提取指标)"]


def m_stage(ex):
    ex["profile"]["stage"]["id"] = 1


def m_must_do(ex):
    items = ex["plan_json"]["items"]
    for k in (1, 3, 4):
        items[k] = {"title": "写一篇品牌故事", "do": "讲讲创始人为什么做这个 App", "week": 2}


def m_must_not(ex):
    ex["plan_json"]["items"].insert(5, {"title": "外链建设", "do": "去目录站提交、找博主换链接", "week": 5})


def m_stops(ex):
    ex["turns"][2]["reply"]["ring"] = 2          # 驱动把第 3 环那次停下记成了第 2 环 → 第 3 环 0 次


def m_questions(ex):
    ev_text(ex["turns"][2], "2. 搜索结果里的你要我去查吗? A 要 B 不要",
            "2. 搜索结果里的你要我去查吗? A 要 B 不要\n3. 预算多少? A 低 B 高\n4. 团队几个人? A 1 B 2\n5. 有没有域名? A 有 B 没有")


def m_ring1(ex):
    ex["turns"][0]["events"].insert(0, {"bash": "python3 /skill/seo-suite/scripts/onboard.py show --ring 2", "out": "# 第 2 环"})


def m_ring1_pages(ex):
    ex["turns"][0]["events"][0]["out"] = "| product.name | Quillbill | http://127.0.0.1:8899/ |"
    ex["turns"][0]["events"][1]["bash"] = "cat robots.txt"


def m_quote(ex):
    ev = ex["turns"][2]["events"][0]
    assert "--confirm" in ev["bash"]
    ev["bash"] = ev["bash"].split("--quote")[0] + '--quote "用户同意了这一环的内容" --confirm'


def m_no_site_audit(ex):
    ex["turns"][3]["events"].insert(0, {"bash": "curl -sI https://petledger.cn", "out": "HTTP/1.1 404"})


def m_local_only(ex):
    ex["turns"][2]["events"].insert(0, {"bash": "curl -s https://quillbill.com/ | head", "out": "<html>"})


def m_drop(ex):
    ev_text(ex["turns"][3], "1,850", "1,900")
    ev_text(ex["turns"][3], "(-21.6%)", "")


def m_baseline(ex):
    ev = ex["turns"][0]["events"][1]
    ev["out"] = "\n".join(ev["out"].splitlines()[:21])     # 只列 20 个 URL


def m_correction(ex):
    ex["profile"]["facts"]["customers"]["value"] = ["一二线城市 22–35 岁养猫狗的上班族", "多宠家庭和刚领养的新手主人"]


def m_unknown(ex):
    ex["profile"]["facts"]["resources.content_capacity"]["status"] = "confirmed"


def m_skip_process(ex):
    ev_text(ex["turns"][1], "第 1 环必须先确认,这一环我只问 3 个,答完后面的按我的猜测补。", "好的,我再问几个。")
    ev_text(ex["turns"][1], "【第 1 环 · 产品是什么】", "【产品】")


def m_skip_outcome(ex):
    ex["plan_md"] = "# 宠账本 SEO 方案\n\n## 路线\n1. 验证需求\n2. 起名和域名\n"


COUNTER = [
    ("facts:漏一条产品线", "idea", m_facts, "facts_error_max"),
    ("stage:档案阶段写错", "idea", m_stage, "stage_correct"),
    ("must_do:前 5 条只对上 3 项", "idea", m_must_do, "must_do_hits_min"),
    ("must_not:前 10 条出现外链建设", "idea", m_must_not, "must_not_hits_max"),
    ("stops:第 3 环没停", "idea", m_stops, "stops_per_ring"),
    ("questions:一次问 5 个", "idea", m_questions, "questions_per_ring_max"),
    ("ring1:第 1 环没确认就看第 2 环", "idea", m_ring1, "ring1_not_skipped"),
    ("ring1:第一次停下前只抓了 1 种页面", "prelaunch", m_ring1_pages, "ring1_not_skipped"),
    ("quote:引文不是用户原话", "idea", m_quote, "quote_before_confirm"),
    ("no_site_audit:想法阶段去抓了域名", "idea", m_no_site_audit, "no_site_audit"),
    ("local_only:请求了 quillbill.com", "prelaunch", m_local_only, "local_only"),
    ("drop_located:两期点击写错", "mature", m_drop, "drop_located"),
    ("baseline_first:写 301 前只抓了 20 个旧 URL", "change", m_baseline, "baseline_first"),
    ("correction:主要客户还是旧的", "calib-correct", m_correction, "correction_applied"),
    ("unknown:不知道的项被标成已确认", "calib-unknown", m_unknown, "unknown_marked"),
    ("skip.process:没说明第 1 环必须确认", "calib-skip", m_skip_process, "skip_handled.process"),
    ("skip.outcome:方案开头没列猜测", "calib-skip", m_skip_outcome, "skip_handled.outcome"),
]


def bare_run():
    """裸跑:想法阶段,一回合直接给建议、写方案、去抓域名,不停下、不确认。"""
    return {"scenario": "onboard-idea", "scenarios": os.path.join(HERE, "scenarios.json"), "site": None,
            "profile": None, "plan_json": {"items": [
                {"title": "做技术审计", "do": "爬站看抓取问题"}, {"title": "提交 sitemap", "do": "去 GSC 提交"},
                {"title": "外链建设", "do": "目录提交"}, {"title": "写博客", "do": "每周 3 篇"},
                {"title": "做多语言", "do": "加 hreflang"}]},
            "turns": [{"events": [
                {"bash": "cat brief.md", "out": "# 宠账本"},
                {"bash": "curl -sI https://petledger.cn", "out": "HTTP/1.1 404"},
                {"tool": "Write", "input": {"file_path": "/ws/seo-ops/plan/plan.json", "content": "{}"}, "out": "ok"},
                {"text": "## 建议\n1. 做技术审计\n2. 提交 sitemap\n3. 外链建设\n\n## 优先级\n先做 1。"}], "reply": None}]}


class Calibration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_grade_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sub(self, name):
        d = os.path.join(self.tmp, name.replace(":", "_").replace(" ", "_"))
        os.makedirs(d, exist_ok=True)
        return d

    def test_gold_all_pass(self):
        for g in GOLD:
            with self.subTest(gold=g):
                r = run(B.expand(B.load(g)), self.sub(g))
                bad = [a["id"] for a in r["assertions"] if not a["pass"]]
                self.assertEqual(bad, [], json.dumps([a for a in r["assertions"] if not a["pass"]], ensure_ascii=False)[:1500])
                self.assertEqual(r["driver_problems"], [])
                self.assertEqual(r["maturity"]["same"], r["maturity"]["of"], r["maturity"])

    def test_bare_run_process_all_fail(self):
        r = run(bare_run(), self.sub("bare"))
        proc = [a for a in r["assertions"] if a["kind"] == "process"]
        self.assertGreaterEqual(len(proc), 5)
        self.assertEqual([a["id"] for a in proc if a["pass"]], [])
        oc = {a["id"]: a["pass"] for a in r["assertions"] if a["kind"] == "outcome"}
        self.assertFalse(oc["must_not_hits_max"])     # 裸跑的建议跨阶段
        self.assertFalse(oc["facts_error_max"])       # 没写档案

    def test_each_counterexample_flips_only_its_assertion(self):
        bases = {}
        for name, gold, fn, target in COUNTER:
            with self.subTest(counter=name):
                if gold not in bases:
                    bases[gold] = verdict(run(B.expand(B.load(gold)), self.sub("base-" + gold)))
                ex = B.expand(B.load(gold))
                fn(ex)
                v = verdict(run(ex, self.sub(name)))
                self.assertIn(target, v)
                self.assertFalse(v[target], "%s 应该不过" % target)
                others = {k: x for k, x in v.items() if k != target}
                self.assertTrue(all(others.values()), "只该 %s 不过,实际还有:%s" % (
                    target, [k for k, x in others.items() if not x]))
                self.assertTrue(bases[gold][target])

    def test_every_criterion_has_counterexample(self):
        ids = set()
        for path in (os.path.join(HERE, "scenarios.json"), os.path.join(FIX, "scenarios_calib.json")):
            with open(path, encoding="utf-8") as fh:
                scs = json.load(fh)["scenarios"]
            for s in scs:
                for c in s["criteria"]:
                    ids |= {"skip_handled.process", "skip_handled.outcome"} if c["id"] == "skip_handled" else {c["id"]}
        self.assertEqual(ids - {t for _, _, _, t in COUNTER}, set())
        self.assertEqual(ids - set(G.CRITERIA) - {"skip_handled.process", "skip_handled.outcome"}, set())


class Parsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_parse_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_replays_and_notifications_ignored(self):
        p = B.materialize(B.expand(B.load("idea")), self.tmp)
        tr = G.Transcript(p["transcript"])
        self.assertEqual(len(tr.turns), 7)                               # 6 环各停一次 + 收尾
        ids = [c["id"] for c in tr.calls()]
        self.assertEqual(len(ids), len(set(ids)))                        # api-request-blob 的重放没算第二遍
        self.assertTrue(all(not t["prompt"]["text"].startswith("[SYSTEM") for t in tr.turns))
        self.assertTrue(tr.turns[1]["prompt"]["text"].startswith("对,就是这个产品"))   # coordinator 前缀去掉了

    def test_onboard_call_parsing(self):
        c = {"name": "Bash", "input": {"command": 'cd ws && python3 /s/onboard.py answer --ring 1 --set a="x y" '
                                                    '--quote "对,就是这个产品。" --confirm; python3 /s/onboard.py show --ring=2'}}
        got = G.onboard_calls(c)
        self.assertEqual([(o["sub"], o["ring"], o["confirm"], o["quote"]) for o in got],
                         [("answer", 1, True, "对,就是这个产品。"), ("show", 2, False, None)])

    def test_page_types(self):
        cases = {"/": "首页", "/pricing/": "定价", "/docs/start": "文档", "/llms.txt": "llms.txt",
                 "/sitemap.xml": "sitemap", "/blog/a/": "博客 / 文章", "/features/x/": "产品页", "/robots.txt": "robots.txt",
                 "/about/": None}
        for path, want in cases.items():
            self.assertEqual(G.page_type(path), want, path)

    def test_question_choice(self):
        q = G.question_lines("1. 最想要什么? A 注册 B 首充\n2. 主要客户是谁?\n3. 哪条线?我猜是社交\n4. 阶段?\n   我猜:增长期")
        self.assertEqual([x["has_choice"] for x in q], [True, False, True, True])
        full = G.question_lines("1. 上面这份理解对吗\uff1f\n   选项:都对 | 有几处要改\n2. 最想要什么\uff1f A\uff09注册 B\uff09首充")
        self.assertEqual([x["has_choice"] for x in full], [False, True])     # 全角问号认;「选项:x | y」不算 A/B

    def test_negated_must_not_not_counted(self):
        self.assertTrue(G.negated_everywhere("不跑站点体检,现在没有站点", ["体检"]))
        self.assertFalse(G.negated_everywhere("先跑站点体检", ["体检"]))


class Driver(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_drive_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_next_picks_ring_and_reply(self):
        ex = B.expand(B.load("idea"))
        full = copy.deepcopy(ex)
        ex["turns"] = ex["turns"][:2]
        ex["turns"][1]["reply"] = None
        p = B.materialize(ex, self.tmp)
        os.remove(p["driver_log"])
        # 第 1 回合已回过:先补一行,再让 next 判第 2 回合
        with open(p["driver_log"], "w", encoding="utf-8") as f:
            f.write(json.dumps({"turn": 1, "ring": 1, "user_text": full["turns"][0]["reply"]["text"],
                                "source": "script", "at": "x"}, ensure_ascii=False) + "\n")
        r = G.drive_next("onboard-idea", p["ws"], p["transcript"], p["driver_log"])
        self.assertEqual((r["action"], r["ring"], r["source"]), ("reply", 2, "script"))
        self.assertEqual(r["user_text"], full["turns"][1]["reply"]["text"])
        self.assertTrue(os.path.isfile(r["profile_snapshot"]))
        again = G.drive_next("onboard-idea", p["ws"], p["transcript"], p["driver_log"])
        self.assertEqual(again["action"], "error")                       # 同一回合不回两次

    def test_next_ends_when_no_question(self):
        ex = B.expand(B.load("idea"))
        ex["turns"] = [{"events": [{"text": "方案写好了。"}], "reply": None}]
        p = B.materialize(ex, self.tmp)
        self.assertEqual(G.drive_next("onboard-idea", p["ws"], p["transcript"], p["driver_log"])["action"], "end")

    def test_ring_of(self):
        self.assertEqual(G.ring_of("第 1 环确认了。\n\n【第 2 环 · 客户】\n1. 谁在搜?", self.tmp)[0], 2)
        self.assertEqual(G.ring_of("Ring 4 · Assets\n1. How many posts?", self.tmp)[0], 4)
        self.assertEqual(G.ring_of("1. 什么?", self.tmp)[0], None)
        # R32:提到不止一个环号
        self.assertEqual(G.ring_of("第 2 环第 1 问已记下。第 2 环还差两问,也还没进第 3 环。\n\n2. 最常问什么?　A. 我写", self.tmp)[0], 2)
        self.assertEqual(G.ring_of("第 2 环已确认,现在进入第 3 环。\n\n**第 3 环的问题**\n1. 竞品是谁?", self.tmp)[0], 3)
        os.makedirs(os.path.join(self.tmp, "seo-ops", "context"), exist_ok=True)
        with open(os.path.join(self.tmp, "seo-ops", "context", "profile.json"), "w", encoding="utf-8") as f:
            json.dump({"current_ring": 3}, f)
        self.assertEqual(G.ring_of("第 2 环做完了,第 3 环的问题见下。\n1. 竞品是谁?", self.tmp), (3, "text+profile.current_ring"))
        self.assertEqual(G.ring_of("1. 竞品是谁?", self.tmp), (3, "profile.current_ring"))
        self.assertEqual(G.ring_of("第 5 环\n1. 语言?", self.tmp), (5, "text"))

    def test_report_gap_only_outcome(self):
        d = os.path.join(self.tmp, "res")
        os.makedirs(d)
        mk = lambda arm, o, p: {"scenario": "s", "product": "idea", "arm": arm, "void": None,  # noqa: E731
                                 "maturity": {"same": 1, "of": 5},
                                 "assertions": [{"id": "a", "kind": "outcome", "pass": o},
                                                {"id": "b", "kind": "process", "pass": p}]}
        for i, r in enumerate([mk("skill", True, True), mk("baseline", False, True)]):
            with open(os.path.join(d, "%d.json" % i), "w") as f:
                json.dump(r, f)
        rep = G.report(d)
        self.assertEqual(rep["products"]["idea"]["outcome_gap_pp"]["skill_vs_baseline"], 100.0)
        self.assertEqual(rep["products"]["idea"]["process"]["baseline"]["b"]["pass"], 1)


if __name__ == "__main__":
    unittest.main()
