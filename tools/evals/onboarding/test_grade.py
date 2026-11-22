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
import datetime as dt
import hashlib
import json
import os
import re
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

    def test_quote_var_expanded(self):
        call = {"name": "Bash", "input": {"command": 'cd /x && Q="Yes, that is right." && python3 s/onboard.py answer --ring 1 --confirm --quote "$Q"'}}
        self.assertEqual(G.onboard_calls(call)[0]["quote"], "Yes, that is right.")
        call = {"name": "Bash", "input": {"command": "export Q='Go with it' ; python3 onboard.py answer --ring 2 --confirm --quote=${Q}"}}
        self.assertEqual(G.onboard_calls(call)[0]["quote"], "Go with it")
        call = {"name": "Bash", "input": {"command": 'python3 onboard.py answer --ring 2 --confirm --quote "$Q"'}}
        self.assertEqual(G.onboard_calls(call)[0]["quote"], "$Q")

    # R65:同一条命令里先赋值、再用 $VAR / ${VAR} 调 onboard.py
    def test_script_var_expanded(self):
        def ring1(cmd):
            return [(o["sub"], o["ring"], o["confirm"]) for o in G.onboard_calls({"name": "Bash", "input": {"command": cmd}})
                    if o["sub"] == "answer" and o["ring"] == 1 and o["confirm"]]
        hit = [("answer", 1, True)]
        cases = (
            ('cd /r && O=/k/skills/seo-suite/scripts/onboard.py\npython3 $O answer --ring 1 --set a=b --quote "对的" '
             '--confirm 2>&1 | tail -20', hit),
            ("S=/k/skills/seo-suite/scripts/onboard.py; python3 $S answer --ring 1 --confirm", hit),
            ("S=/k/skills/seo-suite/scripts; python3 $S/onboard.py answer --ring 1 --confirm", hit),
            ("export S=/k/skills/seo-suite; python3 ${S}/scripts/onboard.py answer --ring 1 --confirm", hit),
            ('S="/k/skills/seo-suite" && O=$S/scripts/onboard.py && python3 "$O" answer --ring 1 --confirm', hit),
            # 该不过的仍不过:变量不在同一条命令里赋值;变量赋的是别的脚本;命令前缀赋值(shell 里不展开到参数)
            ("python3 $O answer --ring 1 --confirm", []),
            ("O=/x/other.py; python3 $O answer --ring 1 --confirm", []),
            ("O=/x/onboard.py python3 $O answer --ring 1 --confirm", []),
            ("python3 $(echo /x/onboard.py) answer --ring 1 --confirm", []),
        )
        for cmd, want in cases:
            with self.subTest(cmd=cmd):
                self.assertEqual(ring1(cmd), want)

    def test_ring1_confirm_via_var_needs_ok_result(self):
        cmd = "O=/k/scripts/onboard.py\npython3 $O answer --ring 1 --quote \"对,就是这个产品。\" --confirm"
        for err, want in ((False, 7), (True, None)):
            with self.subTest(err=err):
                tr = G.Transcript.__new__(G.Transcript)
                tr.events = [{"kind": "call", "id": "c1", "name": "Bash", "input": {"command": cmd}, "line": 7}]
                tr.results = {"c1": {"is_error": err, "text": "ok"}}
                self.assertEqual(G.ring1_confirm_line(tr), want)

    def test_plan_and_output_via_var(self):
        self.assertTrue(G.writes_plan({"name": "Bash", "input": {"command": "cd /r && P=/k/scripts/plan.py\npython3 $P add x"}}))
        self.assertFalse(G.writes_plan({"name": "Bash", "input": {"command": "python3 $P add x"}}))
        c = {"name": "Bash", "input": {"command": "cd /w && T=/k/scripts/site_crawl.py && $T --out a.txt"}}
        self.assertEqual(G.script_output_files(c, "/w"), ["/w/a.txt"])

    # R65 补漏 2:R18 写方案 = 调了 plan.py(除 show);赋值段、命令前缀赋值不是调用
    def test_writes_plan_assign_is_not_call(self):
        bash = lambda c: {"name": "Bash", "input": {"command": c}}  # noqa: E731
        not_writes = ["P=/k/scripts/plan.py",
                      "cd /r && P=/k/scripts/plan.py && ls seo-ops",
                      "P=/k/scripts/plan.py; python3 $P show",
                      "export P=/k/scripts/plan.py\npython3 ${P} show --json",
                      "P=/k/scripts/plan.py python3 $P add x",
                      "python3 /k/scripts/plan.py show"]
        writes = ["P=/k/scripts/plan.py; python3 $P add x",
                  "S=/k/scripts && python3 $S/plan.py set --id 1",
                  "P=/k/scripts/plan.py; python3 $P status",          # 原文只除 show,status 照旧算
                  "FOO=1 python3 /k/scripts/plan.py add x",
                  "python3 /k/scripts/plan.py"]
        for c in not_writes:
            self.assertFalse(G.writes_plan(bash(c)), c)
        for c in writes:
            self.assertTrue(G.writes_plan(bash(c)), c)

    # R65 补漏 3:R26 要「跑了」审计脚本,按段认调用
    def test_audit_runs_by_segment(self):
        bash = lambda c: {"name": "Bash", "input": {"command": c}}  # noqa: E731
        runs = ["python3 /k/scripts/site_audit.py --site http://h",
                "S=/k/scripts; python3 $S/site_audit.py --site http://h",
                "python3 $S/site_audit.py --site http://h",             # 没赋值的 $S/ 前缀:原来就认,词里有脚本名
                "T=/k/scripts/site_audit.py && python3 $T --site http://h",
                "export T=/k/scripts/sitemap_audit.py\n$T http://h",
                "cd scripts && python3 site_audit.py --site http://h",
                "cd /k && python3 -m py_compile scripts/health_score.py",
                "FOO=1 python3 site_crawl.py http://h 2>&1 | tail",
                "bash -c 'python3 link_graph.py x'",
                "python3 /k/project.py run --site x",
                "P=/k/scripts/project.py; python3 $P run --site x"]
        not_runs = ["T=/k/scripts/site_audit.py",
                    "T=/k/scripts/site_audit.py; ls /k/scripts",
                    "T=/k/scripts/site_audit.py python3 $T --site http://h",
                    "python3 $T --site http://h",
                    "python3 /k/project.py show",
                    "P=/k/scripts/project.py; python3 $P show",
                    "python3 - <<'EOF'\nprint('site_audit.py')\nEOF"]
        for c in runs:
            self.assertTrue(G.runs_audit(bash(c)), c)
        for c in not_runs:
            self.assertFalse(G.runs_audit(bash(c)), c)
        # 不用赋值变量的写法,和改前整条原文正则的结果一致
        for c in [c for c in runs + not_runs if not re.search(r"\b[A-Z]=", c)]:
            self.assertEqual(G.runs_audit(bash(c)), bool(G.AUDIT_SCRIPTS.search(G.HEREDOC.sub("", c))), c)

    def test_no_site_audit_assign_only_passes(self):
        for cmd, want in (("T=/k/scripts/site_audit.py; ls /k/scripts", True),
                          ("T=/k/scripts/site_audit.py; python3 $T --site http://h", False)):
            with self.subTest(cmd=cmd):
                ex = B.expand(B.load("idea"))
                ex["turns"][3]["events"].insert(0, {"bash": cmd, "out": "ok"})
                r = run(ex, os.path.join(self.tmp, "audit%d" % want))
                got = next(a for a in r["assertions"] if a["id"] == "no_site_audit")
                self.assertEqual(got["pass"], want, got)

    # R65 补漏 4:命令前缀赋值 O=… python3 $O answer:shell 里 $O 还没赋值,不产生调用记录
    def test_onboard_prefix_assign_no_record(self):
        call = lambda c: {"name": "Bash", "input": {"command": c}}  # noqa: E731
        self.assertEqual(G.onboard_calls(call("O=/x/onboard.py python3 $O answer --ring 1 --confirm")), [])
        self.assertEqual(G.onboard_calls(call("O=/x/onboard.py")), [])
        got = G.onboard_calls(call("FOO=1 python3 /x/onboard.py answer --ring 1 --confirm"))
        self.assertEqual([(o["sub"], o["ring"], o["confirm"]) for o in got], [("answer", 1, True)])
        got = G.onboard_calls(call("O=/x/onboard.py; python3 $O answer --ring 1 --confirm"))
        self.assertEqual([(o["sub"], o["ring"], o["confirm"]) for o in got], [("answer", 1, True)])

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

    # R65 补漏 1:grade_ext 认脚本调用(R42 执行、ops weekly)也按同一条命令里的赋值展开
    def test_ext_calls_var_expanded(self):
        tr_path = os.path.join(self.tmp, "tv.jsonl")
        tx = X.Tx(tr_path)
        tx.first("go")
        runs = ["L=/w/seo-ops/playbook/checks/x.py; python3 $L http://h",
                "S=/w/seo-ops/playbook/checks; python3 $S/x.py http://h",
                "export L=/w/seo-ops/playbook/checks/x.py\n$L http://h",
                "FOO=1 python3 seo-ops/playbook/checks/x.py"]
        not_runs = ["L=/w/seo-ops/playbook/checks/x.py",
                    "L=/w/seo-ops/playbook/checks/x.py; cat $L",
                    "L=/w/seo-ops/playbook/checks/x.py python3 $L",
                    "python3 $L http://h"]
        tx.events([X.BS(c) for c in runs + not_runs])
        tr = G.Transcript(tr_path)
        cmds = [G.bash_cmd(c) for c in E.exec_calls(tr, "x.py")]
        self.assertEqual(cmds, runs)

        tw = os.path.join(self.tmp, "tw.jsonl")
        tx = X.Tx(tw)
        tx.first("go")
        weekly = ["python3 seo-ops/ops.py weekly", "O=/k/scripts/ops.py; python3 $O weekly",
                  "S=/k/scripts && python3 $S/ops.py weekly --site x"]
        not_weekly = ["O=/k/scripts/ops.py", "O=/k/scripts/ops.py; python3 $O status", "python3 $O weekly"]
        tx.events([X.BS(c) for c in weekly + not_weekly])
        s = type("S", (), {"tr": G.Transcript(tw)})()
        self.assertEqual([G.bash_cmd(c) for c in E.weekly_calls(s)], weekly)


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


# ---------------------------------------------------------------------------
# 出题人 11-22 裁定第 5 批第 1 轮的疑问:每处改动一个「按需求卡该过」、一个「该不过」。
# 输入取自第 1 轮真实 run 的 evidence(去掉站点名),或照需求卡原文造。
# ---------------------------------------------------------------------------

class FakeCx:
    def __init__(self, first_text):
        self._fs = {"text": first_text, "line": 1}

    def first_stop(self):
        return self._fs


class Rulings1122(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="onb_r1122_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sub(self, name):
        d = os.path.join(self.tmp, name)
        os.makedirs(d, exist_ok=True)
        return d

    # 疑问 1:R44 ① 只认 GSC 指标数值
    def _real_with_files(self, name, files):
        ex = B.expand(B.load(REAL))
        p = B.materialize(ex, self.sub(name))
        for rel, body in files.items():
            path = os.path.join(p["ws"], rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
        r = G.grade(ex["scenario"], p["ws"], p["transcript"], p["driver_log"], scenarios=p["scenarios"],
                    answers_dir=FIX_ANSWERS, site=p.get("site"), lifecycle=LC)
        return verdict(r)["no_fabricated_metrics"]

    def test_no_fab_keys_weeks_coverage_pass(self):
        files = {
            "seo-ops/context/diagnosis.json": json.dumps({"inputs": {"missing": [
                "metrics.gsc_impressions_28d", "metrics.gsc_clicks_28d", "metrics.gsc_clicks_prev_28d"]}}, indent=1),
            "seo-ops/history/1/priority.json": json.dumps({"context": {"gsc": False, "field_coverage": {
                "gsc_clicks": 0, "indexed": 0}}}, indent=1),
            "seo-ops/plan/roadmap.md": (
                "| 1 | 第 1–3 周 | 看 主产品线的非品牌点击,怎么量:GSC 按页面组过滤,8 周 |\n"
                "7. **接 GSC,存第一份基线**:接上 GSC,存第一份 28 天基线:展示、点击、查询词数\n"
                "5. Confirm whether AI Overviews are taking clicks: GSC generative-AI report, GA4 AI referral\n"
                "- 先用必应/GSC 真实展示量定优先级。\", \"phase\": \"week2-3\"\n")}
        self.assertTrue(self._real_with_files("nofab-pass", files))

    def test_no_fab_real_values_fail(self):
        for name, files in (
                ("md", {"seo-ops/plan/plan.md": "1. 现状:GSC 近 28 天展示 12k、点击 340,CTR 2.8%。\n"}),
                ("json", {"seo-ops/context/metrics.json": json.dumps({"metrics": {"gsc_clicks_28d": 340}}, indent=1)}),
                ("en", {"seo-ops/plan/plan.md": "- Search Console: 1,240 impressions last month\n"})):
            with self.subTest(case=name):
                self.assertFalse(self._real_with_files("nofab-fail-" + name, files))

    # 疑问 2:R45 加粗小标题不是事实行;反引号里的站内路径算出处;本机路径不算
    def test_first_cited_headers_and_backticks(self):
        good = ("**我读到的产品情况**(每条都来自站点,都还没确认)\n"
                "- 产品:给定时任务用的心跳监控 ← /\n"
                "- 定价:免费档和 €15/月 ← /pricing\n"
                "- 页面按钮:Log in 和 Start free,后者指向 `/register`。\n"
                "**请回答下面 4 个问题**\n1. 对吗? A. 对 B. 不对")
        ok, ev = G.c_first_cited(FakeCx(good), {})
        self.assertTrue(ok, ev)
        self.assertEqual(ev["fact_lines"], 3)
        bad = ("**已写入**\n"
               "- 产品档案:`/Users/someone/ws/seo-ops/context/profile.json`\n"
               "- 方案:`/tmp/ws/seo-ops/plan/plan.json`\n"
               "- 定价:Free 1 个 endpoint,Pro €15/月。\n"
               "1. 对吗? A. 对 B. 不对")
        ok, ev = G.c_first_cited(FakeCx(bad), {})
        self.assertFalse(ok, ev)
        self.assertEqual((ev["fact_lines"], ev["cited"]), (3, 0))

    # 疑问 3:R18 只认写入目标路径
    def test_writes_plan_targets_only(self):
        bash = lambda c: {"name": "Bash", "input": {"command": c}}  # noqa: E731
        not_writes = [
            'n(){ python3 $S/onboard.py note --ring 1 --key "$1" --value "$2" >/dev/null 2>&1 || echo fail $1; }\n'
            'n product.name x\npython3 $S/onboard.py show --json | python3 -c "import json,sys"; ls seo-ops/plan 2>&1',
            "cat seo-ops/plan/plan.json 2>&1 | head -40",
            "cp seo-ops/plan/plan.json /tmp/backup.json",
            "python3 -c \"import json;print(json.load(open('seo-ops/plan/plan.json')))\""]
        writes = [
            "mkdir -p seo-ops/context seo-ops/plan && cat > seo-ops/context/profile.json <<'EOF'\n{}\nEOF",
            "cat > seo-ops/plan/plan.md <<'EOF'\n# plan\nEOF",
            "echo '{}' >> seo-ops/plan/plan.json",
            "python3 - <<'EOF'\nimport json\nopen('seo-ops/plan/plan.json','w').write('{}')\nEOF",
            "cp /tmp/p.json seo-ops/plan/",
            "printf x | tee seo-ops/plan/notes.md"]
        for c in not_writes:
            self.assertFalse(G.writes_plan(bash(c)), c)
        for c in writes:
            self.assertTrue(G.writes_plan(bash(c)), c)
        self.assertFalse(E._writes_context(bash("cat seo-ops/context/profile.json 2>&1 | head")))
        self.assertTrue(E._writes_context(bash("cat > seo-ops/context/profile.json <<'EOF'\n{}\nEOF")))

    # 疑问 4:答案表每个别名组都要在被测拿得到的材料里出现(站点、工作区、模拟用户回话);工作区外的 brief.md 不算
    def test_answer_facts_reachable(self):
        L = os.path.join(G.TESTSITES, "lifecycle_sites.py")
        with open(os.path.join(HERE, "scenarios.json"), encoding="utf-8") as f:
            scs = {s["product"]: s for s in json.load(f)["scenarios"]}
        import subprocess
        texts = {}
        for prod, sc in scs.items():
            d = self.sub("site-" + prod)
            cmd = [sys.executable, "-I", L, "build", "--product", prod, "--out", d, "--base", "http://127.0.0.1:8899"]
            if prod == "change":
                cmd += ["--state", "before"]
            subprocess.run(cmd, check=True, capture_output=True)
            buf = [sc["prompt"], json.dumps(sc.get("simulated_user"), ensure_ascii=False)]
            for root, _, fs in os.walk(d):
                for fn in fs:
                    p = os.path.join(root, fn)
                    if os.path.dirname(p) == d and fn in ("brief.md", "product.json") and \
                            not (fn == "brief.md" and "brief.md" in sc["setup"].get("workspace", "")):
                        continue
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        buf.append(fh.read())
            texts[prod] = "\n".join(buf).lower()
            with open(os.path.join(ANSWERS, prod + ".json"), encoding="utf-8") as f:
                fm = json.load(f)["facts_match"]
            for key, groups in fm.items():
                if key.endswith("_min_hits"):
                    continue
                for g in groups:
                    with self.subTest(product=prod, key=key, group=g):
                        self.assertTrue(any(w.lower() in texts[prod] for w in g))
        # 更正前的两组(只写在工作区外的 brief.md):必须找不到
        self.assertFalse(any(w.lower() in texts["change"] for w in ["reseller", "经销", "plant shop", "植物店"]))
        self.assertFalse(any(w.lower() in texts["launched"] for w in ["gift", "送礼"]))

    # 疑问 5:禁项「起名和域名」不命中改版的正当建议
    def test_must_not_domain_alias(self):
        def go(name, item):
            ex = B.expand(B.load("change"))
            ex["plan_json"]["items"].insert(2, item)
            return verdict(run(ex, self.sub(name)))["must_not_hits_max"]
        self.assertTrue(go("mn-ok", {"title": "新版本上线前在预发上跑上线清单",
                                     "do": "canonical 指向新正式域名;换域名时在 GSC 提交地址变更", "week": 2}))
        self.assertFalse(go("mn-bad", {"title": "先做需求验证", "do": "起名并选域名", "week": 2}))

    # 疑问 6:脚本写出的基线文件也算抓过;手写的不算
    def test_baseline_first_script_output_file(self):
        olds = G.ss_old_urls()
        base = "http://127.0.0.1:8899"

        def go(name, urls, by_write=False):
            ex = B.expand(B.load("change"))
            ev = ex["turns"][0]["events"][1]
            assert "site_move.py baseline" in ev["bash"]
            ev["bash"] += " 2>&1 | tail -8"
            ev["out"] = "\n".join("200 %s%s" % (base, u) for u in olds[-5:])          # 输出被截断,只看到 5 个
            body = json.dumps({"pages": [{"url": base + u, "status": 200} for u in urls]})
            if by_write:
                ev["bash"] = "echo skipped"
                ex["turns"][0]["events"].insert(1, {"tool": "Write", "input": {
                    "file_path": "seo-ops/baselines/before.json", "content": body}, "out": "ok"})
            p = B.materialize(ex, self.sub(name))
            path = os.path.join(p["ws"], "seo-ops", "baselines", "before.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            r = G.grade(ex["scenario"], p["ws"], p["transcript"], p["driver_log"], scenarios=p["scenarios"],
                        answers_dir=ANSWERS, site=p.get("site"))
            return verdict(r)["baseline_first"]
        self.assertTrue(go("bf-script30", olds))
        self.assertFalse(go("bf-script20", olds[:20]))
        self.assertFalse(go("bf-write30", olds, by_write=True))

    # 疑问 7:收到更正前回话的 run,列出的断言记 voided、不进汇总;没收到的照常判
    def test_superseded_reply_voids(self):
        sc = {"superseded_replies": [{"ring": 1, "text": "Yes. Old reply.", "voids": ["stage_correct_real"],
                                      "why": "更正前"}]}
        mk = lambda: [{"id": "stage_correct_real", "kind": "outcome", "pass": False},  # noqa: E731
                      {"id": "facts_error_max", "kind": "outcome", "pass": True}]
        out = mk()
        G.apply_superseded(sc, [{"user_text": "Yes.  Old reply."}], out)
        self.assertEqual([a["id"] for a in out if a.get("voided")], ["stage_correct_real"])
        out2 = mk()
        G.apply_superseded(sc, [{"user_text": "Partly. New reply."}], out2)
        self.assertEqual([a for a in out2 if a.get("voided")], [])
        d = self.sub("rep")
        for i, (arm, a) in enumerate((("skill", out), ("baseline", out2))):
            with open(os.path.join(d, "%d.json" % i), "w", encoding="utf-8") as f:
                json.dump({"scenario": "s", "family": "real", "product": "p", "arm": arm, "void": None,
                           "assertions": a}, f)
        rep = G.report(d)
        self.assertEqual(rep["real"]["p"]["arms"]["skill"]["outcome_pass_pct"], 100.0)     # 只剩 facts 一条
        self.assertEqual(rep["real"]["p"]["arms"]["baseline"]["outcome_pass_pct"], 50.0)
        self.assertEqual(len(rep["voided_assertions"]), 1)

    # 疑问 8:null = 「已证明 maturity_proven 级、下一级缺证据」;maturity_unscored 的维不计入
    def test_maturity_null_proven_and_unscored(self):
        ans = {"maturity": {"technical": None, "content": None, "geo": 2},
               "maturity_proven": {"technical": 2, "content": 3, "geo": 2},
               "maturity_unscored": {"technical": "出题人没跑体检"}}

        def go(content, geo=("ok", 2)):
            ws = self.sub("mat-%s-%s" % content)
            d = {"maturity": {"technical": {"status": "ok", "level": 4},
                              "content": {"status": content[0], "level": content[1]},
                              "geo": {"status": geo[0], "level": geo[1]}}}
            os.makedirs(os.path.join(ws, "seo-ops", "context"), exist_ok=True)
            with open(os.path.join(ws, "seo-ops", "context", "diagnosis.json"), "w") as f:
                json.dump(d, f)
            return G.maturity_check(ws, ans)
        m = go(("partial", 3))
        self.assertEqual((m["same"], m["of"]), (2, 2))
        self.assertEqual(go(("unknown", None))["same"], 2)
        self.assertEqual(go(("partial", 2))["same"], 1)          # 已证明的级数不对
        self.assertEqual(go(("ok", 3))["same"], 1)               # 说成确定 3 级,和「下一级判不了」不是一回事

    # 疑问 9:R48 写回变了的条目(note / answer --ring 1)不算重走开局;start / ask 算
    def test_rerun_note_vs_ask(self):
        for name, cmd, ok in (("note", "onboard.py note --ring 1 --key product.lines --value Wholesale", True),
                              ("answer", "onboard.py answer --ring 1 --set product.lines=Wholesale --quote 'yes, new line'",
                               True),
                              ("ask", "onboard.py ask --ring 1", False)):
            with self.subTest(case=name):
                fx = X.GOLD_EXT["ex5-new-line"]()
                fx["sessions"]["resume"][1]["events"].insert(0, X.BS("python3 %s/%s" % (X.SK, cmd), "ok"))
                r, _ = ext_grade(fx, tempfile.mkdtemp(prefix="rr_", dir=self.tmp), {})
                self.assertEqual(verdict(r)["no_onboarding_rerun"], ok)

    # 另:R64 问句没编号时驱动照常回话,但这一回合不算停下
    def test_unnumbered_question_reply_not_a_stop(self):
        ex = B.expand(B.load("idea"))
        first = copy.deepcopy(ex["turns"][0])
        ex["turns"] = [first, {"events": [{"text": "第 2 环还差一问:\n- 你的用户最常搜什么词?"}], "reply": None}]
        p = B.materialize(ex, self.tmp)
        r = G.drive_next("onboard-idea", p["ws"], p["transcript"], p["driver_log"])
        self.assertEqual((r["action"], r.get("unnumbered"), r["ring"]), ("reply", True, 2))
        cx = G.Ctx(G.load_scenario("onboard-idea", G.DEFAULT_SCENARIOS)[1], {}, {}, p["ws"], G.Transcript(p["transcript"]),
                   G.load_driver(p["driver_log"]), None, {}, "skill")
        self.assertEqual([s["turn"] for s in cx.stops], [1])                 # 第 2 回合不算停下
        self.assertEqual(cx.problems, [])
        # 没有问句 → 结束;连着两回合没编号 → 结束
        self.assertFalse(G.unnumbered_question({"events": [{"kind": "text", "text": "方案写好了。", "line": 1}]}))
        log = [{"turn": 2, "unnumbered": True}]
        self.assertFalse(G.unnumbered_allowed(log, 3))
        self.assertTrue(G.unnumbered_allowed(log, 4))
        self.assertFalse(G.unnumbered_allowed([{"turn": t, "unnumbered": True} for t in (2, 4, 6)], 8))


# ---------------------------------------------------------------------------
# 出题人 11-22 裁定试跑 3 疑问(R66–R75)。期望(过 / 不过)按需求卡例 1、6、7、10、11 的原话定;
# 输入句子有一部分取自试跑 3 的真实转录(去掉站名和本机路径)。
# ---------------------------------------------------------------------------

def _sess_of(run, name):
    R = E.load_run(run)
    return E.Sess(R, name, name == R["session_order"][-1])


def _pass_of(r, cid):
    return next(a["pass"] for a in r["assertions"] if a["id"] == cid)


TEACH = "/skill/seo-suite/scripts/teach.py"
TRIAL_WRAPPED = ("检查 mcp_example 在 3 个页面上的结果:\n"
                 "  [✓ pass 过] {base}/platforms/slack/  —\n"
                 "  [✗ fail 没过] {base}/platforms/email/  页面上没找到:每个平台页都要有 MCP 调用示例\n"
                 "  [✗ fail 没过] {base}/platforms/teams/  页面上没找到:每个平台页都要有 MCP 调用示例\n"
                 "把上面的结果原样给用户看,问对不对;用户说可以,再 teach.py check enable。")


def ex6_wrapped(enable_first=False, trial_out=TRIAL_WRAPPED):
    """例 6 卡原文「skill 先在 3 个平台页上实跑给用户看结果,再启用」:试跑走 skill 的包装命令 check try,
    建检查那条命令里顺手 cat 了 seo-ops/ 下的脚本(试跑 3 第 50 行的写法)。"""
    fx = X.gold_ex6()
    t3 = fx["sessions"]["teach"][2]["events"]
    new = [X.BS("cd {ws} && python3 %s check new mcp_example --desc x --match /platforms/; cat %s" % (TEACH, X.CHECK),
                "写了 checks/mcp_example.py")]
    if enable_first:
        new.append(X.BS("cd {ws} && python3 %s check enable mcp_example --quote x" % TEACH, "启用 mcp_example"))
    new.append(X.BS("cd {ws} && python3 %s check try mcp_example --url {base}/platforms/slack/ --url "
                    "{base}/platforms/email/ --url {base}/platforms/teams/" % TEACH, trial_out))
    t3[2:3] = new
    fx["sessions"]["teach"][3]["events"].insert(0, X.BS("cd {ws} && python3 %s check enable mcp_example --quote \"{quote}\""
                                                        % TEACH, "启用 mcp_example(sha256 …)"))
    return fx


class Rulings1122P3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="onb_p3_")
        cls.w0s = {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def sub(self, name):
        return tempfile.mkdtemp(prefix=name + "_", dir=self.tmp)

    # R68(Q3):英文 / 符号判定词优先;要求句里的「有」不是判定
    def test_verdict_precedence(self):
        self.assertIs(E.verdict_of("[✗ fail 没过] http://h/platforms/email/  页面上没找到:每个平台页都要有 MCP 调用示例"), False)
        self.assertIs(E.verdict_of("[✓ pass 过] http://h/platforms/slack/  —"), True)
        self.assertIs(E.verdict_of("/platforms/teams/ 有 tools/call 示例"), True)
        self.assertIs(E.verdict_of("/platforms/teams/ 没有 tools/call 示例"), False)
        self.assertIsNone(E.verdict_of("/platforms/teams/ 所有平台页都要有示例"))         # 原来判成「有」
        self.assertEqual(E.verdict_of("/platforms/teams/ ✓ pass ✗ fail"), "ambiguous")

    # R66 / R67 / R69(Q1、Q2、Q4):包装命令试跑算执行;cat seo-ops/… 不算启用;确认停点看「问启用 + 回话是确认」
    def test_wrapped_trial_counts(self):
        r, _ = ext_grade(ex6_wrapped(), self.sub("wrapped"), self.w0s)
        self.assertTrue(_pass_of(r, "custom_check_trial_matches"))
        self.assertTrue(_pass_of(r, "custom_check_confirm_and_hash"))

    def test_wrapped_trial_after_enable_fails(self):
        r, _ = ext_grade(ex6_wrapped(enable_first=True), self.sub("enable_first"), self.w0s)
        self.assertFalse(_pass_of(r, "custom_check_trial_matches"))
        self.assertFalse(_pass_of(r, "custom_check_confirm_and_hash"))

    def test_wrapper_without_verdicts_is_not_a_run(self):
        out = "mcp_example:脚本改过、已停用,不跑。"
        r, _ = ext_grade(ex6_wrapped(trial_out=out), self.sub("refused"), self.w0s)
        self.assertFalse(_pass_of(r, "custom_check_trial_matches"))

    def test_enable_words_ignore_seo_ops_path(self):
        tp = os.path.join(self.tmp, "en.jsonl")
        tx = X.Tx(tp)
        tx.first("go")
        not_en = ["cd /w && python3 %s check new x --desc d; cat seo-ops/playbook/checks/x.py" % TEACH,
                  "cd /w && grep -n enable seo-ops/playbook/checks/x.py",
                  "R=seo-ops/playbook/checks/registry.json; jq '.checks.x.match=\"/p/\"' $R > $R.new && mv $R.new $R"]
        en = ["cd /w && python3 %s check enable x --quote ok" % TEACH,
              "python3 seo-ops/ops.py register-check x"]
        tx.events([X.BS(c) for c in not_en + en])
        got = [G.bash_cmd(c) for c in E.enable_calls(G.Transcript(tp), "/w", "seo-ops/playbook/checks/x.py")]
        self.assertEqual(got, en)

    def test_confirm_reply_reading(self):
        self.assertTrue(E.asks_enable({"text": "1. 这个结果对吗?对的话我执行启用。 A. 对 B. 不对", "questions": []}))
        self.assertFalse(E.asks_enable({"text": "1. R1 的原话和适用范围对不对? A. 对 B. 改", "questions": []}))
        for yes in ("好。", "结果对,启用吧。", "OK, enable it."):
            self.assertTrue(E.affirmative(yes), yes)
        for no in ("先放着。", "不对,先别启用。", "Go with your best guess and move on to the next part.", ""):
            self.assertFalse(E.affirmative(no), no)

    # 题目更正(Q4):teach 段规则确认停点不再吃掉「启用」那条话题回话
    def test_teach_topics_split(self):
        fx = X.gold_ex6()
        t = fx["sessions"]["teach"]
        t[0]["events"][-1] = X.TX("记下了。\n\n1. R1 的原话和适用范围对不对? A. 对 B. 改")
        t.insert(1, X.turn(X.TX("好,R1 照原话记着。")))
        run = X.materialize(fx, self.sub("topics"), self.w0s)
        rows = G.load_driver(E.load_run(run)["sessions"]["teach"]["driver_log"])
        self.assertEqual([x["source"] for x in rows], ["topic:1", "user_turn:1", "user_turn:2", "topic:0"])
        self.assertEqual(rows[-1]["user_text"], "结果对,启用吧。")

    # R66(自查收紧):被改过以后运营单在内部跑了它、或用包装命令跑了它,都算执行
    def test_disabled_counts_internal_and_wrapped_runs(self):
        for name, ev in (("weekly", X.weekly("本周运营单:\n- mcp_example:/platforms/teams/ fail、/platforms/email/ fail")),
                         ("wrapped", X.BS("python3 %s check run mcp_example" % TEACH, "/platforms/teams/ fail"))):
            with self.subTest(name):
                fx = X.gold_ex6()
                fx["sessions"]["t3b_weekly_tampered"][0]["events"].insert(0, ev)
                r, _ = ext_grade(fx, self.sub("dis_" + name), self.w0s)
                self.assertFalse(_pass_of(r, "custom_check_disabled_on_change"))

    # R70(Q5):陈述禁用清单、说「没有 Reddit 建议」的条目不是违例;真的建议做 Reddit 的照样是
    def test_reddit_negation(self):
        ok = ["- **Reddit(R2):** brief 里没有 Reddit 外链建议。",
              "- **榜单上的 Reddit 帖子我没用。** 搜索结果里有两条 Reddit 的讨论帖,按你的 R2 不碰。",
              "- 禁用清单:Reddit 外链",
              "3. Partner pages and integration directories (excluding: Reddit 外链)",
              "- You ruled out: Reddit 外链",
              "- **R2:** 没有 Reddit 外链建议。",
              "- 按规则去掉了 Reddit 外链"]
        bad = ["5. 在 Reddit r/devops 发帖带上链接",
               "- Post on Reddit, not just HN",
               "- Reddit AMA (do not overpromote)",
               "- notes: Reddit threads in r/sre are worth a link",
               "- Reddit:每周发两帖带链接"]
        for e in ok:
            self.assertFalse(E.reddit_violation(e), e)
        for e in bad:
            self.assertTrue(E.reddit_violation(e), e)

    # R71(Q6 ① ②):价格表认紧邻上方的价格标题 + 表体货币金额;「月度对比」、devs 不是对比
    def test_price_table_caption_and_vs(self):
        names = ["Pingwell", "Alertmint"]
        tbl = "| | Pingwell | Alertmint |\n|---|---|---|\n| 中档 | Team $19/月 | $25/月 |\n| 高档 | Business $49/月 | 待补 |\n"
        self.assertTrue(E.price_table_ok("### R1 价格对照表(必须有)\n" + tbl, names))
        self.assertFalse(E.price_table_ok("### 功能对照\n" + tbl, names))
        feat = "| | Pingwell | Alertmint |\n|---|---|---|\n| Slack | yes | no |\n| Discord | yes | yes |\n"
        self.assertFalse(E.price_table_ok("### 价格对照表\n" + feat, names))
        self.assertTrue(E.price_table_ok("| Plan | Pingwell | Alertmint |\n|---|---|---|\n| Team | $19 | $25 |\n", names))
        for t in ("Pingwell vs Alertmint", "brief-pingwell-vs-alertmint.md", "对比页", "Alertmint alternatives", "替代页"):
            self.assertTrue(E.VS_RE.search(t), t)
        for t in ("measure: backlink_import.py 月度对比", "small devs teams", "canvas", "上线前后对比"):
            self.assertFalse(E.VS_RE.search(t), t)

    # 题目更正(Q7):「旧路径 / 旧 URL / 回指」算说清了问题;只说「会 301」没说旧址或不再互指的照样不过
    def test_hreflang_issue_synonyms(self):
        fx = X.gold_hreflang_broken()
        ev = fx["sessions"]["task"][0]["events"]
        ev[-1] = X.TX("hreflang=\"en\" 原来指向 /blog/fertilizer-guide/,这个地址会 301 跳转。我把它改成最终地址,"
                      "并在全仓搜了 hreflang 里的 /blog/ 旧路径。")
        r, _ = ext_grade(fx, self.sub("href_ok"), self.w0s)
        self.assertTrue(_pass_of(r, "hreflang_verdict"))
        fx = X.gold_hreflang_broken()
        fx["sessions"]["task"][0]["events"][-1] = X.TX("/blog/fertilizer-guide/ 会 301 跳转到 /articles/fertilizer-guide/。")
        r, _ = ext_grade(fx, self.sub("href_bad"), self.w0s)
        self.assertFalse(_pass_of(r, "hreflang_verdict"))

    # R73(Q9):开局脚本读了 product-marketing.md、输出里原样带出它的内容 = 第一次停下前读过;只点名文件不算
    def test_pmm_read_via_script(self):
        pmm = X.scenario_ext("ex11-shared-context")["setup"]["files"][X.PMM]
        one = next(ln for ln in pmm.splitlines() if ln.startswith("**One-liner:**")).split(":**", 1)[1].strip()
        bm = next(ln for ln in pmm.splitlines() if ln.startswith("**Business model:**")).split(":**", 1)[1].strip()
        good = "草稿:\n- 一句话介绍:%s ← .agents/product-marketing.md\n- 收费方式:%s ← .agents/product-marketing.md" % (one, bm)
        thin = "已有产品上下文文件(先读它当草稿):.agents/product-marketing.md"
        for name, out, want in (("good", good, True), ("thin", thin, False)):
            with self.subTest(name):
                fx = X.gold_ex11(read_late=True)
                fx["sessions"]["main"][0]["events"].insert(0, X.BS("python3 %s/onboard.py start --site {base}" % X.SK, out))
                r, _ = ext_grade(fx, self.sub("pmm_" + name), self.w0s)
                self.assertEqual(_pass_of(r, "pmm_read_first"), want)

    def _tr(self, d, cmd, out, t_use, t_res, start=None):
        p = os.path.join(d, "t.jsonl")
        iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        rows = [{"type": "user", "timestamp": iso(start or t_use - 60), "message": {"role": "user", "content": "go"}},
                {"type": "assistant", "timestamp": iso(t_use), "message": {"id": "m1", "role": "assistant", "content": [
                    {"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"command": cmd}}]}},
                {"type": "user", "timestamp": iso(t_res), "message": {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": "tu1", "content": out}]}}]
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
        return G.Transcript(p)

    # R74(Q11):skill 脚本自动存到默认位置的基线文件算「改动前存了全部 URL」;之前就有的、手写的、不是脚本写的都不算
    def test_baseline_default_location(self):
        import time
        olds = G.ss_old_urls()
        self.assertEqual(len(olds), 30)
        body = json.dumps({"urls": ["http://h%s" % p for p in olds]})
        cases = (("script", "cd {ws} && python3 /k/scripts/site_move.py baseline --site http://h 2>&1 | tail -15", 0, True),
                 ("stale", "cd {ws} && python3 /k/scripts/site_move.py baseline --site http://h 2>&1 | tail -15", -300, False),
                 ("no_py", "cd {ws} && curl -s http://h/sitemap.xml | tail -15", 0, False),
                 ("handwritten", "cd {ws} && cat > seo-ops/baselines/b.json <<'EOF'\n%s\nEOF\npython3 /k/x.py" % body, 0, False))
        for name, cmd, shift, want in cases:
            with self.subTest(name):
                d = self.sub("bl_" + name)
                ws = os.path.join(d, "ws")
                now = time.time()
                E.write_text(os.path.join(ws, "seo-ops", "baselines", "b.json"), body)
                os.utime(os.path.join(ws, "seo-ops", "baselines", "b.json"), (now + shift, now + shift))
                tr = self._tr(d, cmd.replace("{ws}", ws), "- 200 http://h/\n- 200 http://h/de/", now - 5, now + 5)
                cx = type("Cx", (), {"items": [{"text": "Save a baseline of all URLs before the move"}], "tr": tr, "ws": ws})()
                ok, ev = G.c_baseline_first(cx, {})
                self.assertEqual(ok, want, json.dumps(ev, ensure_ascii=False)[:400])

    # R75(顺带现象):cat / head 打出来的本地文件行不是请求;脚本自己打出的抓取行照算
    def test_local_file_lines_not_requests(self):
        import time
        d = self.sub("echo")
        ws = os.path.join(d, "ws")
        E.write_text(os.path.join(ws, "data", "pages.csv"), "page,clicks\nhttp://h/brew-guides/v60/,4\nhttp://h/shop/x/,3\n")
        E.write_text(os.path.join(ws, "README.md"), "Site at http://h/about/\n")
        old = time.time() - 600
        for f in ("data/pages.csv", "README.md"):
            os.utime(os.path.join(ws, f), (old, old))
        out = ("Site at http://h/about/\n==> data/pages.csv <==\npage,clicks\nhttp://h/brew-guides/v60/,4\n"
               "data/pages.csv:3:http://h/shop/x/,3\n错误: 站点 http://h/docs/ 是本机地址:加 --allow-local 重跑\n"
               "- 200 http://h/pricing/\n- 200 http://h/sitemap.xml")
        cmd = "cd %s && cat README.md; head -5 data/*.csv; grep -n shop data/pages.csv; python3 /k/onboard.py start" % ws
        tr = self._tr(d, cmd, out, time.time() - 5, time.time() + 5, start=time.time() - 60)
        got = sorted(G.url_path(u) for u in G.request_urls(tr.calls()[0], tr, ws))
        self.assertEqual(got, ["/pricing/", "/sitemap.xml"])
        # 会话开始以后才写出的文件(比如脚本自己落盘的清单)不算「本地原有」,同一行照算
        new = os.path.join(ws, "seo-ops", "urls.txt")
        E.write_text(new, "- 200 http://h/pricing/\n")
        G._LOCAL_IDX.clear()
        got = sorted(G.url_path(u) for u in G.request_urls(tr.calls()[0], tr, ws))
        self.assertEqual(got, ["/pricing/", "/sitemap.xml"])

    def test_product_lines_translated(self):
        """R76(疑问 12):站点原词的标准中文译名算记对;译名对不上任何一组、或少一条产品线,照样算漏。
        期望值来自站点原文(pour-over kit / Brewing gear / Time tracking / trail guides)和卡例 1 用中文写产品线的第一屏。"""
        def missing(name, lines):
            ans = G.read_json(os.path.join(ANSWERS, name + ".json"))
            return G.judge_facts({"product": {"lines": lines}}, ans)["lines_missing"]
        # 正例:直译站点原词
        self.assertEqual(missing("launched", ["订阅", "单袋咖啡豆", "手冲套装"]), 0)
        self.assertEqual(missing("launched", ["Single-origin coffee bags", "Monthly coffee subscription", "Pour-over gear"]), 0)
        self.assertEqual(missing("prelaunch", ["开票", "时间追踪", "客户门户"]), 0)
        self.assertEqual(missing("mature", ["步道指南", "装备评测", "Pro 会员"]), 0)
        # 反例:宽词不算器具线、少一条就是漏
        self.assertEqual(missing("launched", ["订阅", "单袋咖啡豆", "手冲咖啡豆"]), 1)
        self.assertEqual(missing("launched", ["订阅", "单袋咖啡豆", "冲煮指南"]), 1)
        self.assertEqual(missing("launched", ["订阅", "咖啡豆"]), 1)
        self.assertEqual(missing("prelaunch", ["开票", "客户门户"]), 1)
        self.assertEqual(missing("mature", ["徒步指南", "装备评测", "Pro 会员"]), 1)


# ---------------------------------------------------------------------------
# 出题人 11-22 裁定试跑 3b(例 5 第二次打开)的疑问(R77–R80)。期望按需求卡例 5 的原话和场景 note 定,
# 不按改完的判分器跑出来是什么定。
# ---------------------------------------------------------------------------

def _gsc_series(tmp, T, mode, base_dir):
    """照 scenarios_ext.json 的 gsc_series.py 原文在开局那份导出(lifecycle_sites launched)上跑一次,返回 data 目录。"""
    import subprocess
    rec = os.path.join(tmp, "gsc_series.py")
    with open(rec, "w", encoding="utf-8") as f:
        f.write(X.spec_ext()["recipes"]["gsc_series.py"])
    d = os.path.join(tmp, "data-%s-%s" % (mode, T))
    shutil.copytree(os.path.join(base_dir, "gsc"), d)
    subprocess.run([sys.executable, "-I", rec, T, SITE, mode, d], check=True, capture_output=True, cwd=tmp)
    return d


def _daily(d):
    import csv
    imp, clk, rows = {}, {}, []
    with open(os.path.join(d, "gsc-pages.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            imp[r["date"]] = imp.get(r["date"], 0) + int(r["impressions"])
            clk[r["date"]] = clk.get(r["date"], 0) + int(r["clicks"])
            rows.append(r)
    return imp, clk, rows


def _windows(imp, T):
    """场景 note 的算法:T-1、T-8、T-15、T-22 四个周检查点各取 28 天窗口,导出里没有的日子按 0 算。"""
    T = dt.date.fromisoformat(T)
    out = []
    for n in (1, 8, 15, 22):
        c = T - dt.timedelta(days=n)
        out.append(sum(v for k, v in imp.items() if c - dt.timedelta(days=27) <= dt.date.fromisoformat(k) <= c))
    return out


class Rulings1122P3b(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="onb_p3b_")
        cls.w0s = {}
        import subprocess
        cls.base = os.path.join(cls.tmp, "launched")
        subprocess.run([sys.executable, "-I", os.path.join(G.TESTSITES, "lifecycle_sites.py"), "build", "--product",
                        "launched", "--out", cls.base, "--base", SITE], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def sub(self, name):
        return tempfile.mkdtemp(prefix=name + "_", dir=self.tmp)

    # R77(疑问 3、4):按 note 的算法能从生成的数据里算出 note 的数;卡「连续 4 周超过阶段 2 的上限」在 T ≥ 11-15 都成立
    def test_gsc_series_note_math(self):
        imp, _, _ = _daily(_gsc_series(self.sub("th"), "2026-11-25", "threshold", self.base))
        self.assertEqual(_windows(imp, "2026-11-25"), [5600, 5600, 4238, 2838])     # threshold note 原文
        imp, _, _ = _daily(_gsc_series(self.sub("sp"), "2026-11-25", "spike", self.base))
        self.assertEqual(_windows(imp, "2026-11-25"), [2135, 760, 697, 524])        # spike note(R77 改后)
        for T in ("2026-11-15", "2026-11-22", "2026-12-01", "2026-12-31"):
            with self.subTest(T=T):
                th, _, _ = _daily(_gsc_series(self.sub("th"), T, "threshold", self.base))
                self.assertTrue(all(w > 1000 for w in _windows(th, T)), _windows(th, T))
                sp, _, _ = _daily(_gsc_series(self.sub("sp"), T, "spike", self.base))
                w = _windows(sp, T)
                self.assertTrue(w[0] > 1000 and all(x <= 1000 for x in w[1:]), w)   # 只有最后一个检查点过,不是「连续 4 周」

    def test_gsc_series_matches_launch_export(self):
        """spike 不改写开局导出已有的日子;排名各页不同;日常日子也有点击(原来全站 0 点击,和开局导出的 18 次矛盾)。"""
        _, _, base_rows = _daily(os.path.join(self.base, "gsc"))
        d = _gsc_series(self.sub("sp"), "2026-11-22", "spike", self.base)
        imp, clk, rows = _daily(d)
        kept = [r for r in rows if r["date"] <= "2026-11-07"]
        self.assertEqual(sorted(map(tuple, (r.values() for r in kept))), sorted(map(tuple, (r.values() for r in base_rows))))
        self.assertEqual(sum(v for k, v in clk.items() if k <= "2026-11-07"), 18)
        quiet = [k for k in imp if "2026-11-08" <= k < "2026-11-19"]
        self.assertGreater(sum(clk[k] for k in quiet), 0)
        for f in sorted(os.listdir(d)):
            if f.startswith("Pages_"):
                with open(os.path.join(d, f)) as fh:
                    pos = {ln.rsplit(",", 1)[1] for ln in fh.read().splitlines()[1:]}
                self.assertGreater(len(pos), 1, f)
        th = _gsc_series(self.sub("th"), "2026-11-22", "threshold", self.base)
        imp, clk, _ = _daily(th)
        self.assertTrue(0.02 <= sum(clk.values()) / sum(imp.values()) <= 0.04)

    def test_threshold_old_data_topic(self):
        """模拟用户对「新旧导出对不上、哪个对」有回话;阶段话题仍排在前面。"""
        tops = X.scenario_ext("ex5-threshold")["sessions"][0]["simulated_user_by_topic"]
        self.assertIn("stage", tops[0]["if"])
        for q in ("旧记录里的 640 次展示和新导出对不上,哪个对?", "The old export doesn't match the new one, which one is right?"):
            hit = next(t for t in tops if re.search(t["if"], q, re.I))
            self.assertIn("new export", hit["reply"])

    # R80:否定 / 条件里的「增长期」不是提示;「要不要切换到增长期打法」是提示。期望来自卡「提示『看起来进入增长期了』」「只冲高 1 次不提示」
    def test_stage_prompt_reading(self):
        spike = X.scenario_ext("ex5-spike-decoy")["criteria"][0]["prompt"]
        th = X.scenario_ext("ex5-threshold")["criteria"][0]["prompt"]
        not_prompts = ["只是一天冲高,还没进入增长期。", "要连续 4 周都过 1000 才算进入增长期。",
                       "This is one busy day, not the growth stage yet.", "It isn't time to switch to the growth plan.",
                       "进入增长期还早。"]
        prompts = ["看起来进入增长期了。", "要不要切换到增长期打法?", "Looks like you've entered the growth stage.",
                   "Shall we switch to the growth playbook?"]
        for t in not_prompts:
            self.assertEqual(E.stage_prompt_hits(spike, t), [], t)
            self.assertEqual(E.stage_prompt_hits(th, t), [], t)
        for t in prompts:
            self.assertTrue(E.stage_prompt_hits(spike, t), t)
            self.assertTrue(E.stage_prompt_hits(th, t), t)
        self.assertEqual(E.stage_prompt_hits(th, "还不是增长期,先按刚上线的打法走。"), [])    # 原来裸「增长期」就算提示

    def test_stage_prompt_end_to_end(self):
        def spike(extra):
            fx = X.gold_ex5_spike()
            ev = X.find_text(fx, "resume", "stay on the launch plan")
            ev["text"] = ev["text"].replace("## This week", extra + "\n\n## This week")
            r, _ = ext_grade(fx, self.sub("sp"), self.w0s)
            return _pass_of(r, "no_stage_prompt")
        self.assertTrue(spike("一天冲高,还没进入增长期。"))
        self.assertFalse(spike("要不要切换到增长期打法,你定。"))
        fx = X.gold_ex5_threshold()
        ev = X.find_text(fx, "resume", "This looks like the growth stage now.")
        ev["text"] = ev["text"].replace("This looks like the growth stage now.\n\n1. Switch to the growth-stage plan? A. switch now",
                                        "This is not the growth stage yet.\n\n1. Keep the launch plan for now? A. keep")
        r, _ = ext_grade(fx, self.sub("th"), self.w0s)
        self.assertFalse(_pass_of(r, "stage_prompted_then_confirmed"))              # 没提示过,用户自己说换也不算
        r, _ = ext_grade(X.gold_ex5_threshold(), self.sub("th_gold"), self.w0s)
        self.assertTrue(_pass_of(r, "stage_prompted_then_confirmed"))

    # R79:阶段名要和「阶段 / stage」同一行
    def test_first_screen_stage_word(self):
        def go(old, new):
            fx = X.gold_ex5_control()
            ev = X.find_text(fx, "resume", old)
            ev["text"] = ev["text"].replace(old, new)
            r, _ = ext_grade(fx, self.sub("fs"), self.w0s)
            return _pass_of(r, "resume_first_screen")
        self.assertTrue(go("stage: 刚上线 (launched)", "阶段:刚上线"))
        self.assertFalse(go("; stage: 刚上线 (launched).", ".\n- We launched on 2026-10-18 and traffic is small."))

    # R78(疑问 8):提示词照实说明宿主包装;首条消息被驱动改过就记 driver_deviations
    def test_reply_channel_and_deviation(self):
        for p in (E.SHORT_PROMPT, G.PROMPT_COMMON):
            self.assertIn("The coordinator sent a message while you were working", p)
            self.assertIn("用户本人的回话", p)
        self.assertNotIn("no coordinator", E.SHORT_PROMPT.lower())
        fx = X.gold_ex5_control()
        r, run = ext_grade(fx, self.sub("dev0"), self.w0s)
        self.assertEqual(r["driver_deviations"], [])
        tp = E.load_run(run)["sessions"]["resume"]["transcript"]
        with open(tp, encoding="utf-8") as f:
            lines = f.readlines()
        first = json.loads(lines[0])
        first["message"]["content"] += "\n\n(Harness note: there is no coordinator in this conversation.)"
        lines[0] = json.dumps(first, ensure_ascii=False) + "\n"
        with open(tp, "w", encoding="utf-8") as f:
            f.writelines(lines)
        r2 = E.grade_ext(E.load_run(run), answers_dir=ANSWERS, lifecycle=LC, refs=[X.REF_LAUNCHED])
        self.assertEqual(len(r2["driver_deviations"]), 1)
        self.assertEqual(r2["driver_deviations"][0]["added"], "(Harness note: there is no coordinator in this conversation.)")
        d = self.sub("rep")
        with open(os.path.join(d, "a.json"), "w", encoding="utf-8") as f:
            json.dump(r2, f)
        self.assertEqual(len(G.report(d)["driver_deviations"]), 1)

    # 维持的读法(疑问 1、5、6、7):期望来自卡「只问变了的部分;没变化时不重复提问」「回到第 1 环只问变了的部分」和定义原文
    def test_maintained_rulings(self):
        def d30(mod):
            fx = X.gold_ex5_30days()
            mod(fx)
            r, _ = ext_grade(fx, self.sub("d30"), self.w0s)
            return _pass_of(r, "no_onboarding_rerun"), _pass_of(r, "questions_only_on")
        self.assertEqual(d30(lambda fx: None), (True, True))

        def ring_status(fx):                                                          # 疑问 6:状态句里的环号也算
            ev = X.find_text(fx, "resume", "Picking up where we left off.")
            ev["text"] = ev["text"].replace("Picking up where we left off.", "第 6 环开局都已确认。")
        self.assertEqual(d30(ring_status)[0], False)

        def material_stop(fx):                                                        # 疑问 1、5:答完档案再停下要材料
            t = fx["sessions"]["resume"][1]
            t["events"][-1]["text"] += ("\n\n1. Which social profiles go into sameAs? A. Instagram only B. none\n"
                                        "2. Where is the site's source repo? A. GitHub B. none\n"
                                        "3. Should I draft the brief now? A. yes B. later")
        self.assertEqual(d30(material_stop), (False, False))
        fx = X.gold_ex5_new_line()                                                    # 疑问 7:加完产品线再停下确认方案
        fx["sessions"]["resume"][1]["events"][-1]["text"] += "\n\n1. Re-plan the roadmap around wholesale now? A. yes B. later"
        r, _ = ext_grade(fx, self.sub("nl"), self.w0s)
        self.assertFalse(_pass_of(r, "no_onboarding_rerun"))


if __name__ == "__main__":
    unittest.main()
