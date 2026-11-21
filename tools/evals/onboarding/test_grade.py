#!/usr/bin/env python3
"""判分器校准(规则:标准答案必过、原样必不过)。

锁住三件事:
  1. 标准答案(fixtures/gold/*.json,内容取自答案表)全部断言都过;
  2. 裸跑(不停下、不确认、直接给建议)的 process 类断言全不过;
  3. 每条断言各一个刚好不过的反例:只让那一条不过,其余照旧全过。
另有转录解析、驱动取回话的小测试。
第 5 批:真实站 6 条(合成产品 beatline)、扩展场景 25 条(多段会话,真 setup / mutate / next)、例 3 盲比、
宿主静态检查、report 分 family,同样按「标准答案必过、裸跑必不过、反例只让对应那条不过」校准。只用标准库,不调模型:python3 -m unittest tools/evals/onboarding/test_grade.py
"""
import argparse
import copy
import hashlib
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
import build_ext as X  # noqa: E402
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


# ---------------------------------------------------------------------------
# 第 5 批:真实站 6 条(合成产品 beatline,fixtures/scenarios_real_calib.json)
# ---------------------------------------------------------------------------

E = X.E
FIX_ANSWERS = os.path.join(FIX, "answers")
LC = os.path.join(FIX, "lifecycle_calib.json")
REAL = "real-beatline"


def run_real(ex, tmp):
    p = B.materialize(ex, tmp)
    return G.grade(ex["scenario"], p["ws"], p["transcript"], p["driver_log"], scenarios=p["scenarios"],
                   answers_dir=FIX_ANSWERS, site=p.get("site"), lifecycle=LC)


def rm_real_stage(ex):
    ex["profile"]["stage"]["id"] = 3


def rm_real_honest(ex):
    line = "- 阶段:刚上线(推测,公开统计面板显示访问量从 2025-03 起持平)← https://statsdemo.example/beatline.example"
    ev_text(ex["turns"][0], line, line + "\n\n已经是成熟期的产品了。\n")


def rm_real_fab(ex):
    ex["turns"][-1]["events"][-1]["text"] += "\nSearch Console 里过去 28 天有 1,200 次展示。"


def rm_real_cited(ex):
    ev_text(ex["turns"][0], " ← https://beatline.example/", "")
    ev_text(ex["turns"][0], " ← /pricing", "")


def rm_real_plateau(ex):
    ex["turns"][0]["events"] = [e for e in ex["turns"][0]["events"] if "statsdemo" not in e.get("bash", "")]


def rm_real_programmatic(ex):
    ev_text(ex["turns"][0], "站上有 /tools 下 640 个免费工具页,覆盖 pt、es、de 等语言", "站上有一个博客")


COUNTER_REAL = [
    ("stage_real:档案阶段不在 stage_accept", rm_real_stage, "stage_correct_real"),
    ("stage_honest:第一屏说成熟期且没写推测", rm_real_honest, "stage_first_screen_honest"),
    ("no_fab:编了 GSC 展示数", rm_real_fab, "no_fabricated_metrics"),
    ("first_cited:两条事实没出处", rm_real_cited, "first_screen_cited"),
    ("plateau:没请求公开统计面板", rm_real_plateau, "plateau_located"),
    ("programmatic:第一屏没提工具页", rm_real_programmatic, "programmatic_noticed"),
]


def bare_real():
    """裸跑:一回合直接给建议,编 GSC 点击和访客数,不停下、不确认。"""
    return {"scenario": "real-calib-beatline", "scenarios": os.path.join(FIX, "scenarios_real_calib.json"),
            "site": "https://beatline.example/", "profile": {"stage": 4}, "plan_json": {"items": [{"title": "做外链"}]},
            "turns": [{"events": [
                {"bash": "curl -s https://beatline.example/", "out": "<title>beatline</title>"},
                {"text": "## 建议\n1. 根据 Search Console,过去一个月 3,400 次点击,先做外链。\n2. 每月 5,000 访客,可以投广告。"}],
                "reply": None}]}


class RealSite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_real_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sub(self, name):
        d = os.path.join(self.tmp, name.replace(":", "_"))
        os.makedirs(d, exist_ok=True)
        return d

    def test_gold_all_pass(self):
        r = run_real(B.expand(B.load(REAL)), self.sub("gold"))
        self.assertEqual(r["family"], "real")
        self.assertEqual(sorted(a["id"] for a in r["assertions"]), sorted(G.REAL_CRITERIA))
        self.assertEqual([a["id"] for a in r["assertions"] if not a["pass"]], [])
        self.assertEqual(r["driver_problems"], [])

    def test_bare_all_fail(self):
        r = run_real(bare_real(), self.sub("bare"))
        self.assertEqual([a["id"] for a in r["assertions"] if a["pass"]], [])

    def test_each_counterexample_flips_only_its_assertion(self):
        for name, fn, target in COUNTER_REAL:
            with self.subTest(counter=name):
                ex = B.expand(B.load(REAL))
                fn(ex)
                v = verdict(run_real(ex, self.sub(name)))
                self.assertFalse(v[target], "%s 应该不过" % target)
                self.assertEqual([k for k, x in v.items() if k != target and not x], [])

    def test_every_real_criterion_has_counterexample(self):
        self.assertEqual(set(G.REAL_CRITERIA) - {t for _, _, t in COUNTER_REAL}, set())

    def test_plateau_params_from_how(self):
        with open(os.path.join(FIX, "scenarios_real_calib.json"), encoding="utf-8") as f:
            how = json.load(f)["criteria_defs"]["plateau_located"]["how"]
        urls, words, peaks = G.plateau_params(how)
        self.assertEqual(urls, ["statsdemo.example/beatline.example", "statsdemo.example/api/stats/beatline.example"])
        self.assertIn("持平", words)
        self.assertIn("12,480", peaks)

    def test_programmatic_language_signal(self):
        self.assertTrue(G.LANG_CN.search("覆盖葡、西、德三种"))
        self.assertTrue(G.LANG_CN.search("有西班牙语版本"))
        self.assertFalse(G.LANG_CN.search("德国客户"))             # 单字后面不接「语 / 文」、也不成列表 → 不算
        self.assertFalse(G.LANG_LATIN.search("design notes"))


# ---------------------------------------------------------------------------
# 第 5 批:扩展场景 25 条(多段会话;真 setup / mutate / next / 快照,转录照子代理 JSONL 写)
# ---------------------------------------------------------------------------

def ext_grade(fx, out, w0s):
    run = X.materialize(fx, out, w0s)
    return E.grade_ext(E.load_run(run), answers_dir=ANSWERS, lifecycle=LC, refs=[X.REF_LAUNCHED]), run


def ext_verdict(r):
    return {a["id"]: a["pass"] for a in r["assertions"] if a["id"] in E.EXT_CRITERIA}


def cx_rerun(fx):
    fx["sessions"]["resume"][0]["events"].insert(0, X.BS("python3 %s/onboard.py start" % X.SK, "开局开始"))


def cx_resume_date(fx):
    ev = X.find_text(fx, "resume", "2026-11-20")
    ev["text"] = ev["text"].replace("Profile last confirmed 2026-11-20; ", "")


def cx_questions(fx):
    ev = X.find_text(fx, "resume", "new product line?")
    ev["text"] += "\n2. Did the subscription price change? A. no B. yes"


def cx_repeat(fx):
    fx["sessions"]["again"] = [X.turn(X.TX("1. Is the profile still accurate? A. yes B. no")), X.turn(X.TX("OK."))]


def cx_profile_date(fx):
    fx["sessions"]["resume"][1] = X.turn(X.TX("Thanks, carrying on with week 5."))


def cx_stage_plan(fx):
    t = fx["sessions"]["resume"][1]
    t["events"] = [e for e in t["events"] if X.PLAN not in json.dumps(e)]


def cx_stage_prompt(fx):
    ev = X.find_text(fx, "resume", "stay on the launch plan")
    ev["text"] = ev["text"].replace("so we stay on the launch plan", "so you've entered the growth stage")


def cx_rule_recorded(fx):
    fx.update(X.gold_ex6(rules=X.rules_md(dated=(True, False)), t1_rules=X.rules_md()))


def cx_deny(fx):
    fx.update(X.gold_ex6(deny_key="channels"))


def cx_violation(fx):
    fx.update(X.gold_ex6(t2_text=X.LINK_IDEAS.replace("5. 向 GitHub 上的 awesome-monitoring 列表提交条目",
                                                       "5. 在 Reddit r/devops 发帖带上链接")))


def cx_created(fx):
    fx.update(X.gold_ex6(script=X.CHECK_PY.replace("import urllib.request", "import requests\nimport urllib.request")))


def cx_trial(fx):
    fx.update(X.gold_ex6(trial_out=X.TRIAL_OK.replace("/platforms/teams/ fail", "/platforms/teams/ pass")))


def cx_hash(fx):
    fx.update(X.gold_ex6(hash_in_registry=False))


def cx_weekly(fx):
    fx.update(X.gold_ex6(weekly_runs=False))


def cx_disabled(fx):
    fx.update(X.gold_ex6(t3b_runs=True))


def cx_survive(fx):
    fx.update(X.gold_ex6(t1_rules=X.rules_md().split("\n- ")[0] + "\n- " + X.rules_md().split("\n- ")[1].split("\n")[0] + "\n"))


def cx_pr(fx):
    fx.update(X.gold_ex6(pr_extra=[X.BS("git push origin pr-draft", "To github.com:x/y.git")]))


def cx_direct(fx):
    fx.update(X.gold_ex7_cold(ask_first=True))


def cx_title(fx):
    fx.update(X.gold_ex7_cold(touch_desc=True))


def cx_read_first(fx):
    fx.update(X.gold_ex7_warm(reads_after=True))


def cx_hreflang(fx):
    fx.update(X.gold_hreflang_clean(skip_de=True))


def cx_pmm_read(fx):
    fx.update(X.gold_ex11(read_late=True))


def cx_ring1(fx):
    fx.update(X.gold_ex11(extra_q=("When did you launch? A. October B. September",
                                   "Which markets do you ship to? A. US B. more")))


def cx_reask(fx):
    fx.update(X.gold_ex11(extra_q=("Who are your main customers? A. home brewers B. gift buyers",)))


def cx_written_back(fx):
    fx.update(X.gold_ex11(keep_v1=False))


COUNTER_EXT = [
    ("no_onboarding_rerun:续接时调了 onboard start", "ex5-control-nochange", cx_rerun, "no_onboarding_rerun"),
    ("resume_first_screen:第一屏没写档案确认日期", "ex5-control-nochange", cx_resume_date, "resume_first_screen"),
    ("questions_only_on:顺带问了订阅价", "ex5-new-line", cx_questions, "questions_only_on"),
    ("no_repeat_question:下一段又问档案", "ex5-30days", cx_repeat, "no_repeat_question"),
    ("profile_contains:核对后没更新确认日期", "ex5-30days", cx_profile_date, "profile_contains"),
    ("stage_prompted:确认后没重写方案", "ex5-threshold", cx_stage_plan, "stage_prompted_then_confirmed"),
    ("no_stage_prompt:单日冲高就说进了增长期", "ex5-spike-decoy", cx_stage_prompt, "no_stage_prompt"),
    ("rule_recorded:teach 段第二条规则没带日期(t1 段才补)", "ex6-user-rules", cx_rule_recorded, "rule_recorded"),
    ("deny_structured:禁用清单的键名不是 deny 类", "ex6-user-rules", cx_deny, "deny_structured"),
    ("rule_violations:t2 建议去 Reddit 发帖", "ex6-user-rules", cx_violation, "rule_violations_max"),
    ("custom_check_created:脚本 import requests", "ex6-user-rules", cx_created, "custom_check_created"),
    ("custom_check_trial:试跑把 teams 判成 pass", "ex6-user-rules", cx_trial, "custom_check_trial_matches"),
    ("custom_check_confirm:登记里没有 sha256", "ex6-user-rules", cx_hash, "custom_check_confirm_and_hash"),
    ("custom_check_weekly:运营单没跑检查", "ex6-user-rules", cx_weekly, "custom_check_runs_weekly"),
    ("custom_check_disabled:被改过还照跑", "ex6-user-rules", cx_disabled, "custom_check_disabled_on_change"),
    ("playbook_survives:升级后第一段把 Reddit 规则弄丢了", "ex6-user-rules", cx_survive, "playbook_survives_upgrade"),
    ("pr_draft:git push 了", "ex6-user-rules", cx_pr, "pr_draft_not_submitted"),
    ("direct_edit:动手前先问了", "ex7-title-cold", cx_direct, "direct_edit_no_questions"),
    ("title_changed_only:顺手改了 description", "ex7-title-cold", cx_title, "title_changed_only"),
    ("read_context_first:改完才读规则", "ex7-title-warm", cx_read_first, "read_context_first"),
    ("hreflang_verdict:没请求 de 页", "ex7-hreflang-clean", cx_hreflang, "hreflang_verdict"),
    ("pmm_read_first:第一次停下后才读文件", "ex11-shared-context", cx_pmm_read, "pmm_read_first"),
    ("ring1_reduced:第 1 环问了 3 个(基线 4 个)", "ex11-shared-context", cx_ring1, "ring1_questions_reduced"),
    ("pmm_no_reask:又问了主要客户", "ex11-shared-context", cx_reask, "pmm_no_reask_covered"),
    ("pmm_written_back:Changelog 的 v1 被删了", "ex11-shared-context", cx_written_back, "pmm_written_back"),
]


class ExtScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="onb_ext_")
        cls.w0s = {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def sub(self, name):
        d = tempfile.mkdtemp(prefix=name.split(":")[0] + "_", dir=self.tmp)
        return d

    def test_gold_all_pass(self):
        for sid, fn in X.GOLD_EXT.items():
            with self.subTest(gold=sid):
                r, _ = ext_grade(fn(), self.sub(sid), self.w0s)
                bad = [a for a in r["assertions"] if not a["pass"]]
                self.assertEqual(bad, [], json.dumps(bad, ensure_ascii=False)[:1500])
                self.assertIsNone(r["void"])
                self.assertEqual({n: s["driver_problems"] for n, s in r["sessions"].items() if s["driver_problems"]}, {})
                self.assertTrue(all(s["ended"] for s in r["sessions"].values()))

    def test_bare_all_new_fail(self):
        for sid, fn in X.BARE_EXT.items():
            with self.subTest(bare=sid):
                r, _ = ext_grade(fn(), self.sub("bare-" + sid), self.w0s)
                v = ext_verdict(r)
                self.assertTrue(v)
                self.assertEqual([k for k, x in v.items() if x], [])

    def test_each_counterexample_flips_only_its_assertion(self):
        for name, sid, fn, target in COUNTER_EXT:
            with self.subTest(counter=name):
                fx = X.GOLD_EXT[sid]()
                fn(fx)
                r, _ = ext_grade(fx, self.sub(name), self.w0s)
                v = verdict(r)
                self.assertIn(target, v)
                self.assertFalse(v[target], "%s 应该不过" % target)
                self.assertEqual([k for k, x in v.items() if k != target and not x], [])

    def test_every_ext_criterion_has_counterexample(self):
        defs = X.spec_ext()["criteria_defs_ext"]
        self.assertEqual(set(defs) - {t for _, _, _, t in COUNTER_EXT}, set())
        self.assertEqual(set(defs) - set(E.EXT_CRITERIA), set())
        used = {c["id"] for s in X.spec_ext()["scenarios"] for c in s["criteria"]}
        self.assertEqual(used - set(E.EXT_CRITERIA) - set(G.CRITERIA), set())

    def test_ring1_reduced_needs_ref(self):
        run = X.materialize(X.gold_ex11(), self.sub("noref"), self.w0s)
        r = E.grade_ext(E.load_run(run), answers_dir=ANSWERS, lifecycle=LC, refs=[])
        a = next(x for x in r["assertions"] if x["id"] == "ring1_questions_reduced")
        self.assertFalse(a["pass"])
        broken = dict(X.REF_LAUNCHED, stops=[{"ring": 2, "questions": 3}])
        r = E.grade_ext(E.load_run(run), answers_dir=ANSWERS, lifecycle=LC, refs=[broken])
        a = next(x for x in r["assertions"] if x["id"] == "ring1_questions_reduced")
        self.assertEqual((a["pass"], a["evidence"].get("baseline_broken")), (False, True))


class ExtDriver(unittest.TestCase):
    """setup / W0 / mutate / next 的机制(期望值取自 scenarios_ext.json 的 driver_ext 原文)。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_extdrv_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_base_variant_needs_w0(self):
        with self.assertRaises(SystemExit):
            E.setup_run("ex5-30days", "skill", os.path.join(self.tmp, "r"), 8899, X.EXT, T=X.T)

    def test_w0_rebase_port_and_mutate_actions(self):
        w0 = X.make_w0("onboard-launched", self.tmp, 8899, X.w0_launched()["seo_ops"])
        run = os.path.join(self.tmp, "nl")
        E.setup_run("ex5-new-line", "skill", run, 8901, X.EXT, w0=w0, T=X.T, rebase_port=True)
        R = E.load_run(run)
        self.assertEqual(R["base"], "http://127.0.0.1:8901")
        b = E.begin_session(run, "resume")
        acts = [m["action"] for m in b["mutate"]]
        self.assertEqual(acts, ["write", "write", "replace_in_files", "append_sitemap"])
        sm = E.read_text(os.path.join(R["site_dir"], "sitemap.xml"))
        self.assertIn("<loc>http://127.0.0.1:8901/wholesale/</loc><lastmod>%s</lastmod>" % X.T, sm)
        self.assertNotIn(":8899", sm)
        page = E.read_text(os.path.join(R["site_dir"], "wholesale", "index.html"))
        self.assertIn('href="http://127.0.0.1:8901/wholesale/"', page)
        self.assertTrue(os.path.isfile(os.path.join(E.sess_dir(run, "resume"), "start", "manifest.json")))
        with self.assertRaises(SystemExit):
            E.begin_session(run, "resume")                                  # 同一段不开两次

    def test_shift_dates_recipe(self):
        w0 = X.make_w0("onboard-launched", self.tmp, 8899, X.w0_launched()["seo_ops"])
        run = os.path.join(self.tmp, "d30")
        E.setup_run("ex5-30days", "skill", run, 8899, X.EXT, w0=w0, T=X.T)
        E.begin_session(run, "resume")
        prof = G.read_json(os.path.join(E.load_run(run)["ws"], X.PROFILE))
        self.assertEqual(prof["confirmed_at"], "2026-10-20")                # 2026-11-20 往前 31 天

    def test_topic_reply_then_user_turns(self):
        """driver_ext:停下先按话题回(max_uses 用完就不再回),没停下发下一条 user_turn,都发完就结束。"""
        fx = X.gold_ex6()
        run = X.materialize(fx, self.tmp)
        rows = G.load_driver(E.load_run(run)["sessions"]["teach"]["driver_log"])
        self.assertEqual([r["source"] for r in rows], ["user_turn:1", "user_turn:2", "topic:0"])
        self.assertEqual(rows[2]["user_text"], "结果对,启用吧。")
        info = E.load_run(run)["sessions"]
        self.assertTrue(all(info[n].get("ended") for n in E.load_run(run)["session_order"]))
        re_ = next(m for m in info["t1_compare_brief"]["mutate"] if m["action"] == "reinstall_skill")
        self.assertEqual(E.read_text(os.path.join(E.load_run(run)["skill_dir"], "VERSION")).strip(), "new")
        self.assertEqual(re_["playbook_before"], re_["playbook_after"])
        tam = next(m for m in info["t3b_weekly_tampered"]["mutate"] if m["action"] == "tamper")
        self.assertEqual(len(tam["files"]), 2)                               # checks/ 下的脚本和说明都被追加了一行

    def test_baseline_skips_reinstall(self):
        fx = X.gold_ex6()
        fx["arm"] = "baseline"
        fx["skill"] = False
        run = X.materialize(fx, self.tmp)
        re_ = next(m for m in E.load_run(run)["sessions"]["t1_compare_brief"]["mutate"] if m["action"] == "reinstall_skill")
        self.assertIn("skipped", re_)

    def test_verdict_words(self):
        self.assertIs(E.verdict_of("/platforms/slack/ ✓"), True)
        self.assertIs(E.verdict_of("/platforms/teams/ 缺 MCP 示例"), False)
        self.assertEqual(E.verdict_of("/platforms/teams/ pass but missing code"), "ambiguous")
        self.assertIsNone(E.verdict_of("/platforms/teams/"))

    def test_zero_dep(self):
        d = self.tmp
        for name, body, ok in (("a.py", "import json, os\nfrom urllib import request\n", True),
                               ("b.py", "import requests\n", False),
                               ("c.sh", "#!/bin/sh\nset -e\nfor u in a b; do curl -s \"$u\" | grep -q x; done\n", True),
                               ("d.sh", "jq . x.json\n", False),
                               ("e.mjs", "import fs from 'node:fs';\n", True),
                               ("f.mjs", "import x from 'cheerio';\n", False)):
            p = os.path.join(d, name)
            E.write_text(p, body)
            self.assertEqual(E.zero_dep(p)[0], ok, name)

    def test_exec_vs_read(self):
        tr_path = os.path.join(self.tmp, "t.jsonl")
        tx = X.Tx(tr_path)
        tx.first("go")
        tx.events([X.BS("cat seo-ops/playbook/checks/x.py"), X.BS("shasum -a 256 seo-ops/playbook/checks/x.py"),
                   X.BS("cd ws && python3 seo-ops/playbook/checks/x.py http://h"), X.BS("./seo-ops/playbook/checks/x.py")])
        ex = E.exec_calls(G.Transcript(tr_path), "x.py")
        self.assertEqual(len(ex), 2)


# ---------------------------------------------------------------------------
# 第 5 批:例 3 盲比(期望值取自 rubric_example3.json 的规则原文和 answers/launched.json)
# ---------------------------------------------------------------------------

BL = G._sub("grade_blind")
NEW_ITEMS = [
    "Submit the sitemap in Search Console and Bing for /subscription/ and the bean pages; watch indexed pages in GSC, week 1",
    "Add Product and Offer schema to /subscription/; track subscription conversion in GA4, week 2",
    "Write a V60 ratio brew guide on the blog for home brewers, linking to /subscription/; track clicks in Search Console, week 3",
    "List the roastery in pour-over community directories for backlinks to the home page; check referral traffic in GA4, week 4",
    "Publish /llms.txt with the bean and subscription facts; check server logs for AI citation crawls, week 5"]
OLD_TEXT = ("Here is what I recommend:\n\n1. Do a technical SEO audit\n2. Build backlinks\n3. Start a blog\n"
            "4. Add hreflang for international markets\n5. Run SEO A/B tests")
CF_NEW_ITEMS = ["Film a beginner chord video series for adults learning at home, week 1",
                "Launch a sheet music pack landing page with membership upsell, week 2"]


def mk_blind_run(d, arm, plan_items=None, last_text="Done."):
    ws = os.path.join(d, "ws")
    if plan_items is not None:
        E.write_json(os.path.join(ws, "seo-ops", "plan", "plan.json"), {"items": [{"title": t} for t in plan_items]})
        E.write_json(os.path.join(ws, "seo-ops", "context", "profile.json"),
                     {"facts": {"product.name": {"value": "Northfold Coffee"}}})
    os.makedirs(ws, exist_ok=True)
    os.makedirs(os.path.join(d, "sessions", "main"), exist_ok=True)
    tx = X.Tx(os.path.join(d, "sessions", "main", "transcript.jsonl"))
    tx.first("go")
    tx.events([{"text": last_text}])
    E.save_run(d, {"ws": ws, "arm": arm, "scenario": "onboard-launched", "scenarios_file": G.DEFAULT_SCENARIOS,
                   "run": d, "sessions": {"main": {"transcript": tx.path}}})
    return d


def blind_args(**kw):
    base = dict(product=None, round="r5", new_run=None, old_run=None, out=None, scenarios=None, answers_dir=None,
                new_skill_dir=None, old_skill_dir=None, rubric=None, judge=None, cf_new_ws=None, cf_old_ws=None,
                cf_old_transcript=None, blind_broken=False, result=None)
    base.update(kw)
    return argparse.Namespace(**base)


class Blind(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_blind_")
        self.rubric = BL.load_rubric()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def prep(self, old_text=OLD_TEXT, round_id="r5"):
        new = mk_blind_run(os.path.join(self.tmp, "new"), "skill", NEW_ITEMS)
        old = mk_blind_run(os.path.join(self.tmp, "old"), "v043", None, old_text)
        out = os.path.join(self.tmp, "out")
        BL.prepare(blind_args(new_run=new, old_run=old, out=out, round=round_id))
        return out, G.read_json(os.path.join(out, "record.json"))

    def judge(self, out, new_side, c4=(0, 2), c5=(0, 1), extra=None):
        old_side = "B" if new_side == "A" else "A"
        j = {"C4": {new_side: {"violations": c4[0]}, old_side: {"violations": c4[1]}},
             "C5": {new_side: {"fabrications": c5[0]}, old_side: {"fabrications": c5[1]}}}
        j.update(extra or {})
        p = os.path.join(self.tmp, "judge.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write("评审输出如下:\n" + json.dumps(j, ensure_ascii=False) + "\n(完)")
        return p

    def cf(self):
        cfn = os.path.join(self.tmp, "cfnew")
        E.write_json(os.path.join(cfn, "seo-ops", "plan", "plan.json"), {"items": [{"title": t} for t in CF_NEW_ITEMS]})
        cfo = mk_blind_run(os.path.join(self.tmp, "cfold"), "v043", None, OLD_TEXT)
        return cfn, E.load_run(cfo)["sessions"]["main"]["transcript"], E.load_run(cfo)["ws"]

    def test_seed_mapping(self):
        out, rec = self.prep(round_id="r5")
        h = hashlib.sha256(("launched" + "r5").encode("utf-8")).hexdigest()[:8]
        self.assertEqual(rec["seed_hex"], h)
        self.assertEqual(rec["new_is"], "A" if int(h, 16) % 2 == 1 else "B")
        prompt = open(os.path.join(out, "judge_prompt.md"), encoding="utf-8").read()
        for w in ("新版", "旧版", "0.43", "seo-suite"):
            self.assertNotIn(w, prompt)

    def test_pass_when_new_wins_5_with_counterfactual(self):
        out, rec = self.prep()
        n = rec["new_is"]
        self.assertEqual([len(rec["mech"][n]["C2_covered"]), sum(r["ok"] for r in rec["mech"][n]["C3"])], [5, 5])
        cfn, cft, cfw = self.cf()
        v = BL.tally(blind_args(out=out, judge=self.judge(out, n), cf_new_ws=cfn, cf_old_transcript=cft, cf_old_ws=cfw))
        self.assertEqual((v["type"], v["new_wins"], v["pass"]), ("blind_verdict", 5, True))
        self.assertEqual(v["counterfactual_unchanged"]["new"], 0)
        self.assertEqual(v["counterfactual_unchanged"]["old"], 5)           # 旧版的通用建议换了产品也不变

    def test_fail_without_counterfactual(self):
        out, rec = self.prep()
        v = BL.tally(blind_args(out=out, judge=self.judge(out, rec["new_is"])))
        self.assertFalse(v["pass"])
        self.assertEqual(v["missing"]["counterfactual"], ["new", "old"])

    def test_three_wins_two_ties_fail(self):
        out, rec = self.prep()
        cfn, cft, cfw = self.cf()
        v = BL.tally(blind_args(out=out, judge=self.judge(out, rec["new_is"], c4=(1, 1), c5=(0, 0)), cf_new_ws=cfn,
                                cf_old_transcript=cft, cf_old_ws=cfw))
        self.assertEqual((v["new_wins"], v["pass"]), (3, False))

    def test_blind_broken_auto(self):
        zh = "建议:\n\n1. 做技术审计\n2. 做外链\n3. 写博客\n4. 加多语言\n5. 做实验"
        out, rec = self.prep(old_text=zh)
        self.assertTrue(rec["blind_broken_auto"])
        cfn, cft, cfw = self.cf()
        v = BL.tally(blind_args(out=out, judge=self.judge(out, rec["new_is"]), cf_new_ws=cfn, cf_old_transcript=cft,
                                cf_old_ws=cfw))
        self.assertFalse(v["pass"])

    def test_normalize_strips_version_traces(self):
        items = [{"text": "**提交 sitemap**(seo-suite v0.44.0,第 2 环)← seo-ops/plan/plan.json 来源:GSC。", "section": ""},
                 {"text": "x" * 500, "section": ""}]
        out = BL.normalize(items, self.rubric)
        self.assertEqual(out[0]["text"], "提交 sitemap( ,)")             # 删完把连续空白压成一个空格(normalize 第 2 步)
        self.assertEqual(len(out[1]["text"]), 400)

    def test_c3_unclear_and_c2_negation(self):
        lst = [{"text": "改 /pricing 的 title,看 GSC 点击,第 2 周", "section": ""},
               {"text": "改 /pricing 的 title,看点击,第 2 周", "section": ""},
               {"text": "改 /pricing 的 title,第 2 周", "section": ""}]
        rows = BL.c3_items(lst)
        self.assertEqual([(r["ok"], r["unclear"]) for r in rows], [(True, False), (False, True), (False, False)])
        ans = G.read_json(os.path.join(ANSWERS, "launched.json"))
        rows, _ = BL.c2_items([{"text": "先不做多语言 hreflang", "section": ""},
                               {"text": "做多语言 hreflang", "section": ""}], ans)
        self.assertEqual([r["violates"] for r in rows], [[], [3]])

    def test_cf_unchanged_masks_names(self):
        a = [{"text": "Write a Northfold brew guide for home brewers"}]
        b = [{"text": "Write a Ferncraft brew guide for home brewers"}]
        same, _ = BL.cf_unchanged(a, b, ["Northfold", "Ferncraft"], 0.6)
        self.assertEqual(same, [1])
        same, _ = BL.cf_unchanged(a, [{"text": "Film a chord video series"}], ["Northfold", "Ferncraft"], 0.6)
        self.assertEqual(same, [])


# ---------------------------------------------------------------------------
# 第 5 批:宿主静态检查(期望值取自 hosts_static.json 每条的 pass 原文)
# ---------------------------------------------------------------------------

HS = G._sub("grade_hosts")
DESC = ("SEO and GEO workbench: keyword research, title and meta rewrites, robots.txt, sitemap, canonical, hreflang "
        "audits, 收录 checks and reporting for any website.")
ROUTES = "\n".join("- 说「%s」就进 %s 入口。" % (e, e) for e in HS.ENTRIES)
SKILL_BODY = ("# SEO suite\n\n## Hosts without a question tool\n\n"
              "宿主没有提问工具(没有 AskUserQuestion)时:把问题按编号列出,每个带选项或猜测,然后结束这一回合,等用户回话。"
              "Claude Code 才用 AskUserQuestion。\n\n## Entries\n\n" + ROUTES + "\n\nSee [references](references/intro.md).\n")
README = """# seo-suite

## Codex

复制到 `.agents/skills/seo-suite`(或 `$HOME/.agents/skills/seo-suite`)。也可以按插件装:根目录 plugin.json。
自定义提示文件已弃用(deprecated),不是唯一入口。随包的 AGENTS.md 启动协议:

```
Read skills/seo-suite/SKILL.md first.
```

## Cursor

复制到 `.cursor/skills/seo-suite` 或 `~/.cursor/skills/seo-suite`。不要同时放 ~/.claude/skills/seo-suite,会出现同名重复。
Cloud agents 只读 `~/.cursor/skills`,需要 sync 一份过去。

## Gemini CLI

`gemini skills install https://example.com/seo-suite.git --path skills/seo-suite`,或放到 `~/.gemini/skills/seo-suite`。
首次运行要授权(consent)读写工作区。

## VS Code Copilot

复制到 `.github/skills/seo-suite` 或 `~/.copilot/skills/seo-suite`。
"""
OPS_PY = ("#!/usr/bin/env python3\n# ops\nimport os\n\nWS = os.getcwd()\n\n\ndef save(text):\n"
          "    os.makedirs(os.path.join(WS, 'seo-ops'), exist_ok=True)\n"
          "    open(os.path.join(WS, 'seo-ops', 'weekly.md'), 'w').write(text)\n")


def mk_pkg(root, desc=DESC, body=SKILL_BODY, fm_extra="", files=None, readme=README):
    E.write_text(os.path.join(root, "skills", "seo-suite", "SKILL.md"),
                 "---\nname: seo-suite\ndescription: %s\n%s---\n%s" % (desc, fm_extra, body))
    E.write_text(os.path.join(root, "skills", "seo-suite", "references", "intro.md"), "intro\n")
    E.write_text(os.path.join(root, "skills", "seo-suite", "scripts", "ops.py"), OPS_PY)
    E.write_text(os.path.join(root, "README.md"), readme)
    E.write_json(os.path.join(root, "plugin.json"), {"name": "seo-suite", "skills": "./skills/"})
    E.write_json(os.path.join(root, "gemini-extension.json"),
                 {"name": os.path.basename(root), "version": "1.0.0", "description": "SEO suite"})
    for e in HS.ENTRIES:
        E.write_text(os.path.join(root, "commands", "seo-suite", e + ".toml"),
                     'description = "seo-suite %s"\nprompt = "Use seo-suite %s. {{args}}"\n' % (e, e))
    for rel, body_ in (files or {}).items():
        E.write_text(os.path.join(root, rel), body_)
    return root


def host_results(root):
    r = HS.run_checks(os.path.join(root, "skills", "seo-suite"), root)
    return {(h, cid): c["result"] for h, v in r["hosts"].items() for cid, c in v["checks"].items()}, r


COMMON = ("S1_frontmatter_name", "S2_description_length", "S3_description_front_loaded", "S4_skill_body_size",
          "S5_no_hardcoded_home", "S6_state_outside_skill_dir", "S7_stop_without_question_tool")
ALL_HOSTS = ("codex", "cursor", "gemini_cli", "vscode_copilot")


def hx(kw=None, files=None, readme_fn=None):
    def f(root):
        mk_pkg(root, files=files, readme=readme_fn(README) if readme_fn else README, **(kw or {}))
    return f


COUNTER_HOSTS = [
    ("S1", lambda r: (mk_pkg(r), E.write_text(os.path.join(r, "skills", "seo-suite", "SKILL.md"), E.read_text(
        os.path.join(r, "skills", "seo-suite", "SKILL.md")).replace("name: seo-suite", "name: seo_suite"))),
     [(h, "S1_frontmatter_name") for h in ALL_HOSTS] + [("vscode_copilot", "VS2_name_no_colon")]),
    ("S2", hx({"desc": DESC + " " + "x" * 1100}), [(h, "S2_description_length") for h in ALL_HOSTS]),
    ("S3", hx({"desc": "SEO helper for title, meta and robots."}), [(h, "S3_description_front_loaded") for h in ALL_HOSTS]),
    ("S4", hx({"body": SKILL_BODY + "\n" * 520}), [(h, "S4_skill_body_size") for h in ALL_HOSTS]),
    ("S5", hx(files={"skills/seo-suite/scripts/home.py": "import os\nP = os.path.expanduser('~/.claude/skills')\n"}),
     [(h, "S5_no_hardcoded_home") for h in ALL_HOSTS]),
    ("S6", hx(files={"skills/seo-suite/scripts/state.py":
                     "import os\nHERE = os.path.dirname(__file__)\nopen(os.path.join(HERE, 'state.json'), 'w').write('{}')\n"}),
     [(h, "S6_state_outside_skill_dir") for h in ALL_HOSTS] + [("gemini_cli", "GM5_consent_scope")]),
    ("S7", hx({"body": SKILL_BODY.replace("宿主没有提问工具(没有 AskUserQuestion)时", "提问时")}),
     [(h, "S7_stop_without_question_tool") for h in ALL_HOSTS]),
    ("S8", hx({"body": SKILL_BODY.replace("- 说「report」就进 report 入口。", "")},
              readme_fn=lambda t: t.replace("## Cursor", "说「report」就进 report 入口。\n\n## Cursor").replace(
                  "## Gemini CLI", "说「report」就进 report 入口。\n\n## Gemini CLI")),
     [("vscode_copilot", "S8_command_entries_reachable")]),
    ("CX1", hx(readme_fn=lambda t: t.replace("复制到 `.agents/skills/seo-suite`", "复制到 `~/.codex/skills/seo-suite`")),
     [("codex", "CX1_install_path")]),
    ("CX2", hx(files={"skills/seo-suite/agents/openai.yaml": "policy:\n  allow_implicit_invocation: false\n"}),
     [("codex", "CX2_openai_yaml")]),
    ("CX3", hx(files={"prompts/start.md": "Start seo-suite.\n"}), [("codex", "CX3_commands")]),
    ("CX4", hx(files={"plugin.json": json.dumps({"name": "seo-suite", "skills": "./other/"})}),
     [("codex", "CX4_plugin_manifest")]),
    ("CX5", hx(readme_fn=lambda t: t.replace("Read skills/seo-suite/SKILL.md first.", "x" * 9000)),
     [("codex", "CX5_agents_md_budget")]),
    ("CU1", hx(readme_fn=lambda t: t.replace("不要同时放 ~/.claude/skills/seo-suite,会出现同名重复。", "")),
     [("cursor", "CU1_install_path")]),
    ("CU2", hx({"fm_extra": "paths: src/**\n"}), [("cursor", "CU2_frontmatter_flags")]),
    ("CU3", hx(files={".cursor/commands/start.md": "Start seo-suite.\n"}), [("cursor", "CU3_commands")]),
    ("CU4", hx(readme_fn=lambda t: t.replace("Cloud agents 只读 `~/.cursor/skills`,需要 sync 一份过去。", "")),
     [("cursor", "CU4_cloud_agents")]),
    ("GM1", hx(readme_fn=lambda t: t.replace("--path skills/seo-suite", "--path skills/nope")), [("gemini_cli", "GM1_install_path")]),
    ("GM2", hx(files={"commands/seo-suite/report.toml": 'prompt = "Report on $ARGUMENTS"\n'}), [("gemini_cli", "GM2_command_toml")]),
    ("GM3", hx(files={"commands/other/x.toml": 'prompt = "x {{args}}"\n'}), [("gemini_cli", "GM3_command_namespace")]),
    ("GM4", hx(files={"gemini-extension.json": json.dumps({"name": "Wrong Name", "version": "1", "description": "d"})}),
     [("gemini_cli", "GM4_extension_manifest")]),
    ("GM5", hx(readme_fn=lambda t: t.replace("首次运行要授权(consent)读写工作区。", "")), [("gemini_cli", "GM5_consent_scope")]),
    ("VS1", hx(readme_fn=lambda t: t.replace("复制到 `.github/skills/seo-suite` 或 `~/.copilot/skills/seo-suite`。", "复制过去。")),
     [("vscode_copilot", "VS1_install_path")]),
    ("VS2", hx(files={"skills/extra/SKILL.md": "---\nname: seo:start\ndescription: x\n---\n"}),
     [("vscode_copilot", "VS2_name_no_colon")]),
    ("VS3", hx({"fm_extra": "user-invocable: false\n"}), [("vscode_copilot", "VS3_invocation_flags")]),
    ("VS4", hx(files={".github/prompts/start.prompt.md": "---\ndescription: start\n---\nStart.\n"}),
     [("vscode_copilot", "VS4_prompt_files")]),
]


def all_bad_pkg(root):
    """反面整包:每条检查都有一处不合格(验证每条都能判不过)。"""
    E.write_text(os.path.join(root, "skills", "seo-suite", "SKILL.md"),
                 "---\nname: SEO_Suite\ndescription: %s\npaths: x\nuser-invocable: false\n---\n%s" % (
                     "helper " * 200, "body\n" * 520 + "[a](references/deep/x.md)\n"))
    E.write_text(os.path.join(root, "skills", "seo-suite", "scripts", "x.py"),
                 "import os\nHERE = os.path.dirname(__file__)\nP = os.path.expanduser('~/.claude/x')\n"
                 "open(os.path.join(HERE, 's.json'), 'w')\n")
    E.write_text(os.path.join(root, "skills", "seo-suite", "agents", "openai.yaml"), "policy:\n\tallow_implicit_invocation: false\n")
    E.write_text(os.path.join(root, "README.md"), "# x\n\n## Codex\n\n装到 ~/.codex/skills。AGENTS.md\n\n```\n%s\n```\n\n"
                                                  "## Cursor\n\n复制。\n\n## Gemini CLI\n\n`gemini skills install x --path nope`\n\n"
                                                  "## VS Code\n\n复制。\n" % ("y" * 9000))
    E.write_json(os.path.join(root, "plugin.json"), {"skills": "./x"})
    E.write_json(os.path.join(root, "gemini-extension.json"), {"name": "Bad Name"})
    E.write_text(os.path.join(root, "commands", "other", "a.toml"), 'prompt = "do $ARGUMENTS"\n')
    E.write_text(os.path.join(root, "prompts", "sub", "a.md"), "x\n")
    E.write_text(os.path.join(root, ".cursor", "commands", "a.md"), "x\n")
    E.write_text(os.path.join(root, "x", "a.prompt.md"), "x\n")
    return root


class Hosts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_hosts_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pkg_dir(self, name):
        d = os.path.join(self.tmp, name.lower().replace(" ", "-"))
        os.makedirs(d, exist_ok=True)
        return d

    def test_gold_package_all_pass(self):
        res, r = host_results(mk_pkg(self.pkg_dir("gold")))
        self.assertEqual(r["type"], "hosts_static")
        self.assertEqual({k: v for k, v in res.items() if v != "pass"}, {})
        self.assertTrue(all(v["verdict"] == "pass" for v in r["hosts"].values()))
        ids = {c["id"] for h in G.read_json(HS.HOSTS_FILE)["hosts"].values() for c in h["checks"]}
        ids |= {c["id"] for c in G.read_json(HS.HOSTS_FILE)["common"]}
        self.assertEqual(ids - {cid for _, cid in res}, set())

    def test_all_bad_package_nothing_passes(self):
        res, r = host_results(all_bad_pkg(self.pkg_dir("bad")))
        self.assertEqual({k: v for k, v in res.items() if v == "pass"}, {})
        self.assertTrue(all(v["verdict"] == "fail" for v in r["hosts"].values()))

    def test_each_counterexample_flips_only_its_check(self):
        for name, build, targets in COUNTER_HOSTS:
            with self.subTest(counter=name):
                root = self.pkg_dir("seo-suite-" + name)
                build(root)
                res, _ = host_results(root)
                bad = sorted(k for k, v in res.items() if v != "pass")
                self.assertEqual(bad, sorted(targets))

    def test_every_check_has_counterexample(self):
        spec = G.read_json(HS.HOSTS_FILE)
        ids = {c["id"] for h in spec["hosts"].values() for c in h["checks"]} | {c["id"] for c in spec["common"]}
        covered = {cid for _, _, ts in COUNTER_HOSTS for _, cid in ts}
        self.assertEqual(ids - covered, set())

    def test_should_level_is_warn_not_fail(self):
        root = self.pkg_dir("seo-suite-warn")
        hx({"body": SKILL_BODY + "\n" * 520})(root)
        _, r = host_results(root)
        self.assertEqual(r["hosts"]["codex"]["checks"]["S4_skill_body_size"]["result"], "warn")
        self.assertEqual(r["hosts"]["codex"]["verdict"], "pass")


class Report5(unittest.TestCase):
    """report 按 family 分开:onboarding → products、real → real、ext → ext(按场景);盲比和宿主检查各一节。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_rep5_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def put(self, sub, name, d):
        p = os.path.join(self.tmp, sub, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)

    def test_families_blind_hosts(self):
        a = lambda i, k, ok: {"id": i, "kind": k, "pass": ok}  # noqa: E731
        self.put("real", "s.json", {"scenario": "onboard-real-x", "family": "real", "product": "x", "arm": "skill",
                                    "void": None, "assertions": [a("stage_correct_real", "outcome", True)]})
        self.put("real", "b.json", {"scenario": "onboard-real-x", "family": "real", "product": "x", "arm": "baseline",
                                    "void": None, "assertions": [a("stage_correct_real", "outcome", False)]})
        for arm, ok in (("skill", True), ("baseline", False)):
            self.put("ext/%s" % arm, "e.json", {
                "scenario": "ex5-threshold", "family": "ext", "product": "launched", "arm": arm, "void": None,
                "assertions": [a("stage_prompted_then_confirmed", "outcome+process", ok),
                               a("no_onboarding_rerun", "process", True)]})
        self.put("ext", "void.json", {"scenario": "ex5-threshold", "family": "ext", "product": "launched",
                                      "arm": "baseline", "void": "基线组用了 skill", "assertions": [a("x", "outcome", True)]})
        self.put("blind", "p1.json", {"type": "blind_verdict", "product": "idea", "pass": True, "new_wins": 4,
                                      "blind_broken": False})
        self.put("blind", "p2.json", {"type": "blind_verdict", "product": "mature", "pass": True, "new_wins": 5,
                                      "blind_broken": True})
        self.put("hosts", "h.json", {"type": "hosts_static", "label": "new", "hosts": {"codex": {"verdict": "pass"}}})
        rep = G.report(self.tmp)
        self.assertEqual(rep["real"]["x"]["outcome_gap_pp"]["skill_vs_baseline"], 100.0)
        ex = rep["ext"]["ex5-threshold"]
        self.assertEqual(ex["outcome_gap_pp"]["skill_vs_baseline"], 100.0)          # outcome+process 进差距
        self.assertIn("stage_prompted_then_confirmed", ex["process"]["skill"])     # 也在 process 里单列
        self.assertNotIn("no_onboarding_rerun", {k for k, v in ex["arms"]["skill"]["by_assertion"].items()
                                                 if v["kind"] in G.GAP_KINDS})
        self.assertEqual(len(rep["void"]), 1)
        self.assertEqual(rep["products"], {})
        self.assertEqual((rep["blind_example3"]["passed"], rep["blind_example3"]["of"]), (1, 1))
        self.assertEqual(rep["blind_example3"]["reference_only"], ["mature"])
        self.assertEqual(rep["hosts_static"], {"new": {"codex": "pass"}})


if __name__ == "__main__":
    unittest.main()
