#!/usr/bin/env python3
"""R6 referral 桥测试(一方 AI-referral 流量即可见性证据;竞品 Ryze 路线对标,
规格 references/overview/pipeline-completeness.md R6 竞品节)。桥的两半:
  ① ai_referral_log.py --as-panel-import——分析输出之外追加 citation_panel 导入
     JSON(referrer 域→引擎映射 chatgpt.com→chatgpt 等、sessions=请求命中数、
     cited_urls=目标路径聚合),scope 标注"下界证据(real)与 prompt 采样(est)分轨";
  ② citation_panel.py record --from-referral FILE——吃上述导出建 source=referral
     run(engine 对齐面板六引擎,未知引擎/域→other+警告),referral 轨与采样轨在
     report 分开列不加权混合(证据分级纪律);旧面板 run 无 source → 视为采样轨。
standalone(自带 run_script 助手,合成 CLF/JSON 日志与面板,零网络):
python3 tests/test_referral_bridge.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import ai_referral_log as ar   # noqa: E402  (需先入 SCRIPTS 路径)
import citation_panel as cp    # noqa: E402


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形): 子进程跑脚本,捕获输出,零网络。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def clf(ip, path, referer, ts="09/Oct/2026:10:00:00 +0800"):
    """合成一行 combined(CLF)日志(浏览器 UA,无 bot)。"""
    return ('%s - - [%s] "GET %s HTTP/1.1" 200 128 "%s" "Mozilla/5.0"'
            % (ip, ts, path, referer))


def write_log(lines, prefix="refbridge_log_"):
    fd, path = tempfile.mkstemp(suffix=".log", prefix=prefix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def write_json(obj, prefix="refbridge_json_"):
    fd, path = tempfile.mkstemp(suffix=".json", prefix=prefix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    return path


def make_panel(prompts=("best crm", "crm 对比", "helpdesk tools"), prefix="refbridge_p_"):
    """init 一个合成面板 → panel.json 路径(cmd 级,不直接改 dict)。"""
    tmp = tempfile.mkdtemp(prefix=prefix)
    prompts_csv = os.path.join(tmp, "prompts.csv")
    with open(prompts_csv, "w", encoding="utf-8") as f:
        f.write("prompt\n" + "\n".join(prompts) + "\n")
    panel_path = os.path.join(tmp, "panel.json")
    r = run_script("citation_panel.py",
                   ["init", "--brand", "Acme", "--domain", "acme.ai",
                    "--prompts", prompts_csv, "--panel", panel_path])
    assert r.returncode == 0, r.stderr
    return panel_path


def record_sampling(panel_path, engine="chatgpt", date="2026-10-01"):
    """录一条合成采样 run(1 cited + 1 absent)→ run.csv 路径。"""
    run_csv = os.path.join(os.path.dirname(panel_path), "run_%s.csv" % engine)
    with open(run_csv, "w", encoding="utf-8") as f:
        f.write("prompt,mentioned,cited,cited_urls\nbest crm,1,1,https://acme.ai/guide\n"
                "crm 对比,0,0,\n")
    r = run_script("citation_panel.py",
                   ["record", "--engine", engine, "--file", run_csv,
                    "--panel", panel_path, "--date", date])
    assert r.returncode == 0, r.stderr
    return run_csv


class ExportSideTests(unittest.TestCase):
    """① ai_referral_log --as-panel-import 导出侧。"""

    def test_domain_to_engine_mapping_aligns_six_panel_engines(self):
        """六域→六引擎一一对应,键集=AI_REFERRER_DOMAINS,值集=citation_panel 六引擎;
        子域经 match_ai_domain 归并后再映射(www.grok.com → grok)。"""
        self.assertEqual(set(ar.DOMAIN_TO_ENGINE), set(ar.AI_REFERRER_DOMAINS))
        self.assertEqual(set(ar.DOMAIN_TO_ENGINE.values()),
                         {"chatgpt", "perplexity", "gemini", "copilot", "claude", "grok"})
        self.assertEqual(ar.DOMAIN_TO_ENGINE, {
            "chatgpt.com": "chatgpt", "perplexity.ai": "perplexity",
            "gemini.google.com": "gemini", "copilot.microsoft.com": "copilot",
            "claude.ai": "claude", "grok.com": "grok"})
        self.assertEqual(ar.DOMAIN_TO_ENGINE[ar.match_ai_domain("www.grok.com")], "grok")
        self.assertEqual(ar.DOMAIN_TO_ENGINE[ar.match_ai_domain("chatgpt.com")], "chatgpt")

    def test_log_date_of_clf_iso_and_garbage(self):
        """date 从日志 ts 推导: CLF(09/Oct/2026:…)与 ISO(2026-10-09T…)两种形态;
        垃圾/空 → None(调用方回退今天)。"""
        self.assertEqual(ar.log_date_of("09/Oct/2026:10:00:00 +0800"), "2026-10-09")
        self.assertEqual(ar.log_date_of("1/Jan/2027:00:00:00 +0000"), "2027-01-01")
        self.assertEqual(ar.log_date_of("2026-10-09T12:06:00Z"), "2026-10-09")
        self.assertIsNone(ar.log_date_of("-"))
        self.assertIsNone(ar.log_date_of("garbage"))
        self.assertIsNone(ar.log_date_of(""))
        self.assertIsNone(ar.log_date_of(None))

    def test_panel_import_payload_records_and_scope_note(self):
        """合成日志(子域 referrer + 同路径多命中 + JSON 行)→ 每命中域一条
        {date,engine,sessions,cited_urls};cited_urls 按命中数降序;scope 标注
        下界(real)/采样(est)分轨——诚实口径不丢。"""
        lines = [
            clf("1.1.1.1", "/pricing", "https://chatgpt.com/"),
            clf("2.2.2.2", "/pricing", "https://chatgpt.com/c/abc",
                ts="10/Oct/2026:11:00:00 +0800"),
            clf("3.3.3.3", "/blog", "https://chatgpt.com/"),
            clf("4.4.4.4", "/x", "https://www.perplexity.ai/search?q=crm"),
            '{"path": "/y", "status": 200, "user_agent": "Mozilla/5.0", '
            '"referer": "https://claude.ai/chat/abc", "ip": "5.5.5.5", '
            '"time": "2026-10-11T09:00:00Z"}',
            clf("6.6.6.6", "/nope", "https://google.com/"),   # 非 AI referrer 不入
        ]
        res = ar.analyze(lines)
        imp = ar.panel_import_payload(res)
        self.assertEqual(imp["source"], "referral")
        self.assertEqual(imp["date"], "2026-10-11")           # 取日志内最新可解析日期
        got = {r["engine"]: (r["sessions"], r["cited_urls"]) for r in imp["records"]}
        self.assertEqual(got, {
            "chatgpt": (3, ["/pricing", "/blog"]),            # /pricing×2 > /blog×1
            "perplexity": (1, ["/x"]),
            "claude": (1, ["/y"])})
        self.assertNotIn("gemini", got) and self.assertNotIn("google", str(got))
        for frag in ("下界", "(real)", "(est)", "分轨", "source:referral"):
            self.assertIn(frag, imp["scope"], frag)           # 诚实口径注释齐全

    def test_panel_import_payload_empty_when_no_ai_referrer(self):
        """零 AI referrer 命中 → records=[](诚实导出空,不造数);date 仍从日志
        ts 推导;log_dates 为空(无可解析行)→ fallback_date 回退。"""
        res = ar.analyze([clf("1.1.1.1", "/a", "-"),
                          clf("2.2.2.2", "/b", "https://google.com/")])
        imp = ar.panel_import_payload(res, fallback_date="2026-10-12")
        self.assertEqual(imp["records"], [])
        self.assertEqual(imp["source"], "referral")
        self.assertEqual(imp["date"], "2026-10-09")           # 日志 ts 可解析 → 推导优先
        empty = ar.panel_import_payload(
            {"stats": {d: {"hits": 0, "paths": {}} for d in ar.AI_REFERRER_DOMAINS},
             "log_dates": set()}, fallback_date="2026-10-12")
        self.assertEqual(empty["records"], [])
        self.assertEqual(empty["date"], "2026-10-12")         # 无可解析日期 → 回退

    def test_cli_as_panel_import_marker_and_json(self):
        """CLI: 文本报告 + marker 行 + 其后纯 JSON;按 marker 切取可解析;
        help 列出新旗标。"""
        log = write_log([clf("1.1.1.1", "/pricing", "https://chatgpt.com/"),
                         clf("2.2.2.2", "/blog", "https://grok.com/")])
        r = run_script("ai_referral_log.py", [log, "--as-panel-import"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("== AI 引用流量日志分析 ==", r.stdout)   # 原分析输出仍在
        self.assertIn("下界", r.stdout)
        self.assertIn(ar.PANEL_IMPORT_MARKER, r.stdout)
        body = r.stdout.split(ar.PANEL_IMPORT_MARKER, 1)[1]
        payload = json.loads(body)                            # marker 后是纯 JSON
        self.assertEqual(payload["source"], "referral")
        self.assertEqual({rec["engine"] for rec in payload["records"]},
                         {"chatgpt", "grok"})
        h = run_script("ai_referral_log.py", ["--help"])
        self.assertEqual(h.returncode, 0)
        self.assertIn("--as-panel-import", h.stdout)
        os.unlink(log)

    def test_referral_log_self_test_green(self):
        """--self-test 冒烟(含 R6 导出断言)整跑 rc=0。"""
        r = run_script("ai_referral_log.py", ["--self-test"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[self-test] PASS ai_referral_log", r.stdout)


class ImportSideTests(unittest.TestCase):
    """② citation_panel record --from-referral 导入侧 + 面板双轨。"""

    def _referral_file(self, records, wrapper=True):
        obj = {"tool": "ai_referral_log", "source": "referral",
               "scope": "下界证据(real)", "date": "2026-10-09",
               "records": records} if wrapper else records
        return write_json(obj)

    def test_record_from_referral_creates_source_runs(self):
        """导入 → source=referral run(results 恒空,referral.sessions/cited_urls
        落 run),panel.json 与 runs/<id>.json 双写。"""
        panel = make_panel()
        record_sampling(panel)
        ref = self._referral_file([{"date": "2026-10-09", "engine": "chatgpt",
                                    "sessions": 4,
                                    "cited_urls": ["/pricing", "/blog/geo"]}])
        r = run_script("citation_panel.py",
                       ["record", "--from-referral", ref, "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("source=referral", r.stdout)
        with open(panel, encoding="utf-8") as f:
            data = json.load(f)
        ref_runs = [run for run in data["runs"] if run.get("source") == "referral"]
        self.assertEqual(len(ref_runs), 1)
        self.assertEqual(ref_runs[0]["engine"], "chatgpt")
        self.assertEqual(ref_runs[0]["results"], {})          # 不伪造 prompt cell
        self.assertEqual(ref_runs[0]["referral"]["sessions"], 4)
        self.assertEqual(ref_runs[0]["referral"]["cited_urls"],
                         ["/pricing", "/blog/geo"])
        run_file = os.path.join(os.path.dirname(os.path.abspath(panel)), "runs",
                                ref_runs[0]["run_id"] + ".json")
        with open(run_file, encoding="utf-8") as f:           # runs/ 双写
            self.assertEqual(json.load(f)["run_id"], ref_runs[0]["run_id"])
        os.unlink(ref)

    def test_referral_runs_excluded_from_sampling_stats(self):
        """证据分级: referral run 不入采样指标——cells/runs/coverage/share 与
        无 referral run 的面板逐项相等(不加权混合的机检形态)。"""
        panel = make_panel()
        record_sampling(panel, engine="chatgpt", date="2026-10-01")
        record_sampling(panel, engine="perplexity", date="2026-10-02")
        with open(panel, encoding="utf-8") as f:
            before = json.load(f)
        stats_before = cp.compute_stats(before)
        ref = self._referral_file([{"date": "2026-10-09", "engine": "chatgpt",
                                    "sessions": 999, "cited_urls": ["/p"]}])
        r = run_script("citation_panel.py",
                       ["record", "--from-referral", ref, "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(panel, encoding="utf-8") as f:
            after = json.load(f)
        self.assertEqual(len(after["runs"]), len(before["runs"]) + 1)
        stats_after = cp.compute_stats(after)
        for key in ("runs", "cells", "denominator", "mentioned_sum",
                    "coverage", "share", "brand_hits", "domain_total"):
            self.assertEqual(stats_after[key], stats_before[key], key)  # 采样口径零漂移
        self.assertEqual(set(stats_after["per_engine"]),
                         set(stats_before["per_engine"]))     # referral 不产生采样引擎行
        os.unlink(ref)

    def test_report_lists_two_tracks_separately(self):
        """report 双轨分列: referral 轨节(sessions/cited_urls)+ 采样轨标签;
        referral 数字只出现在 referral 轨,采样指标行不含 sessions。"""
        panel = make_panel()
        record_sampling(panel)
        ref = self._referral_file([{"date": "2026-10-09", "engine": "chatgpt",
                                    "sessions": 7, "cited_urls": ["/pricing", "/pricing"]}])
        self.assertEqual(run_script("citation_panel.py",
                                    ["record", "--from-referral", ref,
                                     "--panel", panel]).returncode, 0)
        r = run_script("citation_panel.py", ["report", "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("referral 流量轨", r.stdout)
        self.assertIn("source=referral", r.stdout)
        self.assertIn("不加权混合", r.stdout)                  # 分轨纪律显式打印
        self.assertIn("下界(real)", r.stdout)
        self.assertIn("采样轨", r.stdout) and self.assertIn("(est)", r.stdout)
        ref_line = next(ln for ln in r.stdout.splitlines() if "sessions=" in ln)
        self.assertIn("chatgpt", ref_line) and self.assertIn("sessions=7", ref_line)
        self.assertIn("/pricing(2)", r.stdout)                # cited_urls 聚合计数
        cov_line = next(ln for ln in r.stdout.splitlines() if "mention coverage" in ln)
        self.assertNotIn("7", cov_line.split("=")[-1])        # 采样 coverage 不吃 sessions
        os.unlink(ref)

    def test_unknown_engine_maps_to_other_with_warning(self):
        """未知引擎/域(如 duck.ai)→ engine=other + [!] 警告;other 进面板引擎列表。"""
        panel = make_panel()
        ref = self._referral_file([{"date": "2026-10-09", "engine": "duck.ai",
                                    "sessions": 2, "cited_urls": []}])
        r = run_script("citation_panel.py",
                       ["record", "--from-referral", ref, "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("未知引擎/域 'duck.ai' → 映射 other", r.stdout)
        with open(panel, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["runs"][0]["engine"], "other")
        self.assertIn("other", data["engines"])
        os.unlink(ref)

    def test_import_accepts_full_marker_mixed_output_roundtrip(self):
        """E2E 零网络回路: ①整 stdout 重定向成文件 → ②按 marker 切取导入成功。"""
        log = write_log([clf("1.1.1.1", "/pricing", "https://chatgpt.com/"),
                         clf("2.2.2.2", "/blog", "https://www.claude.ai/chat/x")])
        out = run_script("ai_referral_log.py", [log, "--as-panel-import"])
        self.assertEqual(out.returncode, 0, out.stderr)
        panel = make_panel()
        raw = os.path.join(os.path.dirname(panel), "referral_raw.txt")
        with open(raw, "w", encoding="utf-8") as f:
            f.write(out.stdout)                               # 文本+marker+JSON 混合
        r = run_script("citation_panel.py",
                       ["record", "--from-referral", raw, "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(panel, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual({(run["engine"], run["referral"]["sessions"])
                          for run in data["runs"]},
                         {("chatgpt", 1), ("claude", 1)})
        os.unlink(log)

    def test_import_rejects_bad_input(self):
        """坏输入整文件拒绝 rc=1: 不存在的文件 / 非 JSON / 空 records /
        记录全缺 engine/sessions。"""
        panel = make_panel()
        for bad, desc in [
            (os.path.join(os.path.dirname(panel), "nope.json"), "文件不存在"),
        ]:
            r = run_script("citation_panel.py",
                           ["record", "--from-referral", bad, "--panel", panel])
            self.assertEqual(r.returncode, 1, desc)
        junk = os.path.join(os.path.dirname(panel), "junk.txt")
        with open(junk, "w", encoding="utf-8") as f:
            f.write("not json at all {{{")
        for path, desc in [(junk, "非 JSON"),
                           (self._referral_file([]), "空 records"),
                           (self._referral_file([{"date": "2026-10-09",
                                                  "sessions": 3}] * 0
                                                 + [{"date": "2026-10-09",
                                                     "no_engine": 1,
                                                     "sessions": 3}]), "缺 engine")]:
            r = run_script("citation_panel.py",
                           ["record", "--from-referral", path, "--panel", panel])
            self.assertEqual(r.returncode, 1, desc)
            self.assertIn("错误", r.stderr)
        with open(panel, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["runs"], [])        # 拒绝不落盘

    def test_record_sampling_still_requires_engine_and_file(self):
        """record 既无 --file 也无 --from-referral → rc=1 友好错误;
        采样路径 record --engine --file 照旧(向后兼容)。"""
        panel = make_panel()
        r = run_script("citation_panel.py", ["record", "--panel", panel])
        self.assertEqual(r.returncode, 1)
        self.assertIn("--from-referral", r.stderr)
        self.assertEqual(record_sampling(panel) is not None, True)  # 旧用法仍绿

    def test_legacy_panel_runs_without_source_are_sampling(self):
        """旧面板(run 无 source 字段)→ 全按采样轨统计,report 无 referral 轨节
        (整节不出现,向后兼容)。"""
        legacy = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
                  "prompts": ["p1"], "engines": ["chatgpt"],
                  "runs": [{"run_id": "old-1", "engine": "chatgpt",
                            "date": "2026-10-01", "brand": "Acme",
                            "results": {"p1": {"state": "cited_brand",
                                               "mentioned": 1, "cited": 1,
                                               "cited_urls": ["https://acme.ai/a"]}}}]}
        stats = cp.compute_stats(legacy)
        self.assertEqual((stats["runs"], stats["cells"]), (1, 1))
        self.assertEqual(stats["coverage"], 1.0)
        self.assertEqual(cp.render_referral_section(legacy), [])
        rep = cp.render_report(legacy, stats)
        self.assertNotIn("referral 流量轨", rep)              # 旧面板零新节

    def test_referral_only_panel_report_does_not_crash(self):
        """只有 referral run 的面板: report 出 referral 轨 + 采样轨缺提示,
        不崩不把 referral 当采样证据。"""
        panel = make_panel()
        ref = self._referral_file([{"date": "2026-10-09", "engine": "perplexity",
                                    "sessions": 5, "cited_urls": ["/x"]}])
        self.assertEqual(run_script("citation_panel.py",
                                    ["record", "--from-referral", ref,
                                     "--panel", panel]).returncode, 0)
        r = run_script("citation_panel.py", ["report", "--panel", panel])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("referral 流量轨", r.stdout)
        self.assertIn("采样轨(prompt 采样,est): 无 runs", r.stdout)
        self.assertNotIn("五状态分类", r.stdout)               # 无采样 cell 不渲染采样指标
        os.unlink(ref)

    def test_referral_summary_aggregates_and_filters(self):
        """referral_summary: 同引擎多 run 聚合(runs/sessions/urls 计数);
        engine 过滤只看单引擎。"""
        panel = {"brand": "Acme", "engines": list(cp.DEFAULT_ENGINES), "runs": [
            {"run_id": "a", "engine": "chatgpt", "date": "2026-10-09", "brand": "Acme",
             "source": "referral", "results": {},
             "referral": {"sessions": 3, "cited_urls": ["/p", "/q"]}},
            {"run_id": "b", "engine": "chatgpt", "date": "2026-10-10", "brand": "Acme",
             "source": "referral", "results": {},
             "referral": {"sessions": 4, "cited_urls": ["/p"]}},
            {"run_id": "c", "engine": "claude", "date": "2026-10-10", "brand": "Acme",
             "source": "referral", "results": {},
             "referral": {"sessions": 9, "cited_urls": ["/z"]}},
            {"run_id": "s", "engine": "chatgpt", "date": "2026-10-11", "brand": "Acme",
             "source": "sampling", "results": {}, "referral": None}]}
        agg = cp.referral_summary(panel)
        self.assertEqual(agg["chatgpt"]["runs"], 2)
        self.assertEqual(agg["chatgpt"]["sessions"], 7)
        self.assertEqual(agg["chatgpt"]["urls"], {"/p": 2, "/q": 1})
        self.assertEqual(agg["claude"]["sessions"], 9)
        only = cp.referral_summary(panel, engine="claude")    # 引擎过滤
        self.assertEqual(set(only), {"claude"})
        section = cp.render_referral_section(panel, engine="claude")
        self.assertTrue(any("sessions=9" in ln for ln in section))
        self.assertFalse(any("sessions=7" in ln for ln in section))

    def test_import_run_ids_dedup_on_reimport(self):
        """同面板重复导入同日期记录 → run_id 加 -2 后缀不覆盖(与采样 record 同纪律)。"""
        panel = make_panel()
        ref = self._referral_file([{"date": "2026-10-09", "engine": "chatgpt",
                                    "sessions": 1, "cited_urls": []}])
        for _ in range(2):
            self.assertEqual(run_script("citation_panel.py",
                                        ["record", "--from-referral", ref,
                                         "--panel", panel]).returncode, 0)
        with open(panel, encoding="utf-8") as f:
            ids = [run["run_id"] for run in json.load(f)["runs"]]
        self.assertEqual(len(ids), 2)
        self.assertEqual(ids[0], "referral-chatgpt-2026-10-09")
        self.assertEqual(ids[1], "referral-chatgpt-2026-10-09-2")

    def test_citation_panel_self_test_and_help_green(self):
        """--self-test(含 R6 桥断言)与 record --help(--from-referral 旗标)整跑绿。"""
        st = run_script("citation_panel.py", ["--self-test"])
        self.assertEqual(st.returncode, 0, st.stderr)
        self.assertIn("[self-test] PASS citation_panel", st.stdout)
        h = run_script("citation_panel.py", ["record", "--help"])
        self.assertEqual(h.returncode, 0)
        self.assertIn("--from-referral", h.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
