#!/usr/bin/env python3
"""notify.py P0-3 回归:按告警类型路由(Conductor per-definition)/ redact 强化 /
incident_key 生命周期 + resolve 子命令。standalone:合成 config/alerts,零网络
(发送层全部 monkeypatch,不触真实 webhook/SMTP)。可直接
`python3 tests/test_notify_routing.py`,亦被 tests/run_tests.py 自动装载。"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import notify as N  # noqa: E402


def _mkdir(channels):
    tmp = tempfile.mkdtemp(prefix="nfy_route_")
    mdir = os.path.join(tmp, ".seo-monitor")
    os.makedirs(mdir)
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com", "run_cadence_hours": 24,
                   "channels": channels}, f)
    return mdir


def _alerts_file(mdir, alerts):
    path = os.path.join(mdir, "alerts-%d.json" % int(datetime.now().timestamp() * 1000))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com",
                   "generated": datetime.now().isoformat(timespec="seconds"),
                   "alerts": alerts}, f)
    return path


class _FakeTargets:
    """替换 N.channel_targets:记录 (渠道名, 消息),全部返回成功(零网络)。"""

    def __init__(self, names):
        self.names = names
        self.sent = []

    def __call__(self, cfg):
        def mk(nm):
            def fn(msg):
                self.sent.append((nm, msg))
                return 200, "ok"
            return fn
        return [(nm, mk(nm)) for nm in self.names]


class RouteMatchingTests(unittest.TestCase):
    """route.codes 的 fnmatch 前缀通配 / 无 route 渠道照收 / 分组保序。"""

    def test_fnmatch_prefix_and_exact_match(self):
        """robots_* 前缀命中、site_down 精确命中、title_* 不命中;无 route 的渠道不出现在 routes 表。"""
        routes = N.channel_routes({"channels": {
            "slack-tech": {"type": "slack",
                           "route": {"codes": ["robots_*", "noindex_*", "site_down"]}}}})
        self.assertEqual(routes, {"slack-tech": ["robots_*", "noindex_*", "site_down"]})
        tg = [("slack-tech", None)]
        self.assertEqual(len(N.targets_for_code(tg, routes, "robots_changed")), 1)  # 前缀
        self.assertEqual(len(N.targets_for_code(tg, routes, "site_down")), 1)       # 精确
        self.assertEqual(N.targets_for_code(tg, routes, "site_down_extra"), [])     # fnmatch 非子串
        self.assertEqual(N.targets_for_code(tg, routes, "title_missing"), [])       # 不命中
        self.assertEqual(N.channel_routes({"channels": {"slack": {}}}), {})         # 未配 route

    def test_unrouted_channel_receives_everything(self):
        """未配 route 的渠道照收全部 code(向后兼容),配了 route 的只收命中项。"""
        tg = [("slack-tech", None), ("slack-all", None)]
        rts = {"slack-tech": ["noindex_*"]}
        self.assertEqual([n for n, _ in N.targets_for_code(tg, rts, "noindex_added")],
                         ["slack-tech", "slack-all"])
        self.assertEqual([n for n, _ in N.targets_for_code(tg, rts, "title_missing")],
                         ["slack-all"])

    def test_group_by_recipients_splits_and_keeps_order(self):
        """同一批告警按可达渠道集合分组,组内保序;route 未命中任何渠道 → 空组。"""
        tg = [("slack-tech", None), ("slack-all", None)]
        rts = {"slack-tech": ["robots_*"]}
        alerts = [{"code": "robots_changed", "level": "warn"},
                  {"code": "title_missing", "level": "warn"},
                  {"code": "robots_removed", "level": "warn"}]
        groups = N.group_by_recipients(alerts, tg, rts)
        self.assertEqual([[n for n, _ in sub] for sub, _ in groups],
                         [["slack-tech", "slack-all"], ["slack-all"]])
        self.assertEqual([a["code"] for a in groups[0][1]],
                         ["robots_changed", "robots_removed"])
        # 全部渠道都被 route 筛掉 → 空子 targets(由调用方记日志)
        only_tech = [("slack-tech", None)]
        self.assertEqual(N.group_by_recipients(alerts, only_tech, rts)[1][0], [])

    def test_route_table_template_covers_default_groups(self):
        """默认建议路由表(注释模板,不强制):技术/内容/性能三类 code 模式齐全。"""
        for pat in ("robots_*", "noindex_*", "canonical_*", "site_down", "ssl_*",
                    "title_*", "meta_*", "content_*", "cwv_*", "latency"):
            self.assertIn(pat, N.ROUTE_TEMPLATE)
        self.assertIn("fnmatch", N.ROUTE_TEMPLATE)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(N.cmd_routes(None), 0)
        self.assertIn("robots_*", buf.getvalue())


class RoutingFlowTests(unittest.TestCase):
    """cmd_notify 全链路(渠道层 monkeypatch):路由只决定去哪,级别节奏不变。"""

    def test_critical_immediate_cadence_unaffected_by_routing(self):
        """配了 route 的渠道下 critical 仍同 run 即时发送,不进 pending 批。"""
        mdir = _mkdir({"slack-tech": {"type": "slack", "route": {"codes": ["noindex_*"]}}})
        fake = _FakeTargets(["slack-tech"])
        alerts = [{"level": "critical", "code": "noindex_added", "key": "/pricing",
                   "message": "页面出现 noindex", "action": "摘除", "boundary": "auto"}]
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, alerts)]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake.sent), 1)                        # 即时发,不落 pending
        self.assertIn("noindex_added", fake.sent[0][1])
        self.assertIn("[CRITICAL]", fake.sent[0][1])
        st = N.load_state(os.path.join(mdir, N.STATE_FILE))
        self.assertEqual(st["pending_warn"], [])                   # 路由不改变级别节奏
        # 发出的告警附 incident_key(id: 段透出)且已记录
        self.assertIn("id:", fake.sent[0][1])
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertEqual(list(inc), [N.incident_key(alerts[0])])

    def test_routed_away_alert_only_logged(self):
        """code 未命中任何 route 且无兜底渠道 → 只进日志不发送,rc=0,不记 incident。"""
        mdir = _mkdir({"slack-tech": {"type": "slack", "route": {"codes": ["noindex_*"]}}})
        fake = _FakeTargets(["slack-tech"])
        alerts = [{"level": "critical", "code": "title_missing", "key": "/about",
                   "message": "缺 title", "action": "补", "boundary": "auto"}]
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, alerts)]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertEqual(fake.sent, [])
        self.assertFalse(os.path.exists(os.path.join(mdir, N.INCIDENTS_FILE)))

    def test_flush_digest_split_by_route_and_incident_recorded(self):
        """warn 日批 flush 时按 route 拆分投递;送达后 pending 清空、incident 落盘。"""
        mdir = _mkdir({"slack-tech": {"type": "slack", "route": {"codes": ["robots_*"]}},
                       "slack-all": {"type": "slack"}})
        alerts = [{"level": "warn", "code": "robots_changed", "key": "/robots.txt",
                   "message": "新增 Disallow"},
                  {"level": "warn", "code": "title_missing", "key": "/about",
                   "message": "缺 title"}]
        fake = _FakeTargets(["slack-tech", "slack-all"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            af = _alerts_file(mdir, alerts)
            rc1 = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af]))
            self.assertEqual(rc1, 0)
            self.assertEqual(fake.sent, [])                        # warn 只暂存,未 flush 不发
            rc2 = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af, "--flush", "warn"]))
            self.assertEqual(rc2, 0)
        finally:
            N.channel_targets = orig
        tech_msgs = [m for n, m in fake.sent if n == "slack-tech"]
        all_msgs = [m for n, m in fake.sent if n == "slack-all"]
        self.assertTrue(tech_msgs and all("[WARN] robots_changed" in m for m in tech_msgs))
        self.assertFalse(any("title_missing" in m for m in tech_msgs))   # 内容类不进技术渠道
        self.assertTrue(any("title_missing" in m for m in all_msgs))     # 无 route 渠道照收
        st = N.load_state(os.path.join(mdir, N.STATE_FILE))
        self.assertEqual(st["pending_warn"], [])                   # 全渠道成功 → 清批
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertEqual(set(inc), {N.incident_key(a) for a in alerts})

    def test_per_definition_same_type_channels_via_env(self):
        """同型多渠道 per-definition(自定义键名 + type + 各自 env):都被装配,路由各归各。"""
        mdir = _mkdir({"slack-tech": {"type": "slack", "env": "SEO_TEST_SLACK_TECH"},
                       "slack-content": {"type": "slack", "env": "SEO_TEST_SLACK_CONTENT",
                                         "route": {"codes": ["title_*"]}}})
        env = {"SEO_TEST_SLACK_TECH": "https://hooks.example.test/tech/x",
               "SEO_TEST_SLACK_CONTENT": "https://hooks.example.test/content/x"}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            with open(os.path.join(mdir, "config.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            self.assertEqual([n for n, _ in N.channel_targets(cfg)],
                             ["slack-tech", "slack-content"])
            self.assertEqual(N.channel_routes(cfg), {"slack-content": ["title_*"]})
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class RedactHardeningTests(unittest.TestCase):
    """P0-3 redact 强化(claude-seo 口径):email / token·password·secret·api_key 值。"""

    def test_email_redacted(self):
        out = N.redact("SMTP auth failed for ops@example.com (535)")
        self.assertNotIn("ops@example.com", out)
        self.assertIn("<redacted-email>", out)

    def test_secret_kv_values_redacted(self):
        out = N.redact("env SEO_MONITOR_TG_TOKEN=123456789:AAFF-x_yz chat=42")
        self.assertNotIn("123456789:AAFF-x_yz", out)
        self.assertIn("SEO_MONITOR_TG_TOKEN=<redacted>", out)
        out2 = N.redact('{"api_key": "sk-abcdefghijklmnopqrst", "password": "hunter2"}')
        self.assertNotIn("sk-abcdefghijklmnopqrst", out2)
        self.assertNotIn("hunter2", out2)
        self.assertIn("api_key", out2)                             # 键名保留便于排查

    def test_url_pass_unchanged_and_idempotent(self):
        once = N.redact("GET https://api.telegram.org/bot123:ABC-DEF/sendMessage failed")
        self.assertIn("api.telegram.org", once)
        self.assertNotIn("123:ABC-DEF", once)
        self.assertEqual(N.redact(once), once)                     # 渠道 URL 已处理过不再变形


class IncidentLifecycleTests(unittest.TestCase):
    """incident_key 稳定性 / 记录与 24h 过期 / resolve 子命令。"""

    def test_incident_key_stable_and_distinct(self):
        a = {"code": "noindex_added", "key": "/pricing", "level": "critical"}
        self.assertEqual(N.incident_key(a), N.incident_key(dict(a)))   # 跨调用稳定
        self.assertTrue(N.incident_key(a).startswith("noindex_added@"))
        self.assertNotEqual(N.incident_key(a),
                            N.incident_key(dict(a, key="/blog")))      # 主对象不同则不同
        self.assertNotEqual(N.incident_key(a),
                            N.incident_key(dict(a, code="noindex_removed")))

    def test_record_skips_dry_run_and_expires_after_24h(self):
        mdir = _mkdir({"slack": {}})
        alert = {"code": "robots_changed", "key": "/robots.txt",
                 "level": "warn", "message": "m"}
        N.record_incidents(mdir, [alert], dry_run=True)
        self.assertFalse(os.path.exists(os.path.join(mdir, N.INCIDENTS_FILE)))
        N.record_incidents(mdir, [alert])
        k = N.incident_key(alert)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn(k, inc)
        inc[k]["sent_at"] = (datetime.now() - timedelta(hours=25)).isoformat(timespec="seconds")
        N.save_incidents(os.path.join(mdir, N.INCIDENTS_FILE), {"incidents": inc})
        self.assertEqual(N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"], {})

    def test_resolve_sends_to_routed_channel_and_closes(self):
        """resolve 按记录的 code 走同一路由,发 RESOLVED 消息并关闭 incident。"""
        mdir = _mkdir({"slack-tech": {"type": "slack", "route": {"codes": ["robots_*"]}}})
        N.record_incidents(mdir, [{"code": "robots_changed", "key": "/robots.txt",
                                   "level": "critical", "message": "全站封禁"}])
        k = N.incident_key({"code": "robots_changed", "key": "/robots.txt"})
        fake = _FakeTargets(["slack-tech"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_resolve(N.build_parser().parse_args(["resolve", "--dir", mdir, k]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake.sent), 1)
        self.assertIn("已恢复", fake.sent[0][1])
        self.assertIn("robots_changed", fake.sent[0][1])
        self.assertIn(k, fake.sent[0][1])
        self.assertNotIn(k, N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"])

    def test_resolve_unknown_key_skipped_not_failed(self):
        """未知/过期 key 只提示跳过不判错(rc=0),不产生发送。"""
        mdir = _mkdir({"slack": {}})
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_resolve(N.build_parser().parse_args(
                ["resolve", "--dir", mdir, "ghost@000000000000"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertEqual(fake.sent, [])

    def test_resolve_empty_keys_is_input_error(self):
        mdir = _mkdir({"slack": {}})
        rc = N.cmd_resolve(N.build_parser().parse_args(["resolve", "--dir", mdir]))
        self.assertEqual(rc, 4)


if __name__ == "__main__":
    unittest.main(verbosity=1)
