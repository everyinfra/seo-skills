#!/usr/bin/env python3
"""选题合并队列 + ContentOps 遥测(content_queue;stdlib only)。

规格:references/overview/pipeline-completeness.md R1-8(选题合并队列:trend
backlog + gsc striking-distance + serp_overlap 缺口 → 周排期,复用 remediation
状态机)+ 内容生产体系报告的 ContentOps 状态机+遥测(lead time / WIP / 按闸
拒收率)。三源只读上游产物,不改上游状态文件。

数据文件 contentops.json(默认当前目录,--file 可指定):{schema_version, items:[…]},
每项统一 idea:{id:"CQ-001", source, topic, evidence, score, status, created,
url, published_at, gate_rejections, entered_gated, history[], note}。

三源与读法(缺源=未提供或文件不存在 → 跳过并告警,不猜;文件在但解析不了
→ 退出码 2,不静默降级):
  trend_watch   --trend-state .trend-state.json(默认当前目录,同 R0-7 工作区口径;
                也可指 trend_watch 的 STATE_FILE)取 status=="watch" 的信号——
                WATCH 态=热点未过闸但仍在看,正是选题队列的候补;go/pivot 由
                trend-jack 管线自走,open 未机检完,都不收。
  gsc_mining    --gsc CUR.csv(现算 striking distance:pos 5-20 且曝光≥20,同
                gsc_mining.py 口径,曝光降序取前 30);再给一个 --gsc PREV.csv
                则加算衰退桶(28v28、prev≥10 且降幅≤-25%,只统计两期都出现的词,
                按流失点击降序取前 30)。或 --gsc-out 预跑输出(gsc_mining --json
                的 query/decay 形态,可多份)。列名前缀匹配(Query/Clicks/
                Impressions/CTR/Position,兼容 GSC 导出头两行题头)。
  serp_overlap  --serp-out 预跑输出(serp_overlap.py 存盘的表格文本):共享域
                ≥4(同一篇文章/同簇)=一页可服务两词 → 对比页缺口 idea;互链/分开
                不入队只计数(关键词按存盘文本截断口径,继承上游)。

评分口径(注释即契约,score = 流量潜力 × 意图系数 × 时效加成,保留 2 位):
  流量潜力 TP(0-10):gsc striking = 10×min(1, 曝光/2000)(2k 月曝光封顶——
    striking-distance 的增益随曝光线性,封顶防单词霸榜);gsc decay = 10×min(1,
    前期点击/500)(衰退修复的价值=找回的量,500 点击/28d 封顶);trend 与 serp
    源无量级数据 → 中性 5(brief 阶段补真实量级,不猜)。
  意图系数 IC(词面标志,gsc_mining 深读词表的压缩版):BOFU/对比标志(vs/
    alternative/best/价格/对比…)→1.2;MOFU(how to/guide/教程/怎么…)→1.0;
    其余(TOFU/未分类)→0.8。拉丁词整词边界匹配,CJK 子串匹配。
  时效加成 FB:仅 trend 源按 first_seen 距今——<24h→1.5 / <72h→1.3 / <7d→1.1 /
    ≥7d→1.0(窗口口径同 trend_watch Q3:news 24h/analysis 72h/late);gsc 与
    serp 为常青选题 → 1.0。理论上限 10×1.2×1.5=18。

状态机(复用 remediation.py 纪律):idea→briefed→drafting→gated→published→
measured 六态逐级前进;跳级/回退/同态一律拒绝(降级拒绝,退出码 2);published
必须带 --url(http/https);measured 为终态。唯一合法回退:gated --reject 打回
drafting(闸门审稿结论),每次计一次按闸拒收(gate_rejections)。

ContentOps 遥测三指标(track 每次推进后打印,report 汇总):
  lead time  idea→published 的天数分布(created→published_at,已发布条目;
             缺任一时间戳不计,不猜);
  WIP 当前   briefed+drafting+gated 条数(published 即出制);plan --wip 上限
             排程,超限只列不排;
  按闸拒收率 Σgate_rejections ÷ 进过闸的条数(entered_gated 或被打回过);
             无进闸条目 → N/A。

用法: python3 content_queue.py <collect|plan|track|report> [选项]
退出码: 0 正常 / 1 collect 三源全缺(没东西可收)/ 2 输入或参数错误。

并发(R5 同 remediation):save_data 原子写(tempfile+os.replace)+ 数据文件级
flock,collect/track 的 load→改→save 全程持锁。"""
import argparse
import contextlib
import csv
try:
    import fcntl
except ImportError:  # Windows 没有 fcntl,改用 msvcrt.locking 加同样的排他锁
    fcntl = None
    import msvcrt
import json
import os
import re
import statistics
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = 1
DEFAULT_FILE = "contentops.json"
DEFAULT_TREND_STATE = ".trend-state.json"
STATUSES = ("idea", "briefed", "drafting", "gated", "published", "measured")
WIP_STATUSES = ("briefed", "drafting", "gated")            # published 即出制
TRANSITIONS = {("idea", "briefed"), ("briefed", "drafting"), ("drafting", "gated"),
               ("gated", "published"), ("published", "measured")}
TRACK_TARGETS = ("briefed", "drafting", "gated", "published", "measured")
ID_RE = re.compile(r"^CQ-(\d+)$")
HISTORY_CAP = 30                                             # trend_watch 同款上限

# striking/decay 单桶上限(同 gsc_mining.py 顶 30 口径)
GSC_CAP = 30
# serp_overlap 存盘表格行:关键词对 × 共享数 判据(判据词为上游固定词表,
# ASCII 括号按字面匹配——re.escape,防被当捕获组)
SERP_VERDICTS = ("同一篇文章", "同簇(一页可服务)", "互链", "分开")
SERP_ROW_RE = re.compile(r"^(.+?)\s*×\s*(.+?)\s+(\d+)\s+("
                         + "|".join(re.escape(v) for v in SERP_VERDICTS) + r")\s*$")
SERP_GAP_MIN_SHARED = 4            # ≥4(同文/同簇)=一页可服务两词 → 对比页缺口

# 意图系数词表(gsc_mining.py 头部"可代码化规则参考"词表的压缩版)
BOFU_MARKERS = ("vs", "versus", "alternative", "compare", "comparison", "best", "top",
                "review", "price", "pricing", "cost", "cheap", "buy",
                "对比", "比较", "价格", "多少钱", "怎么选", "排行", "推荐", "评测")
MOFU_MARKERS = ("how", "guide", "tutorial", "template", "checklist", "example",
                "what is", "案例", "怎么", "如何", "教程", "指南", "模板", "清单",
                "是什么", "步骤")

_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")

USAGE_EPILOG = """\
评分口径: score = 流量潜力(0-10) × 意图系数(BOFU/对比 1.2, MOFU 1.0, 其余 0.8)
          × 时效加成(trend 源按 first_seen <24h 1.5 / <72h 1.3 / <7d 1.1 / 其余 1.0;
          gsc/serp 常青 1.0)。流量潜力: striking=10×min(1,曝光/2000);
          decay=10×min(1,前期点击/500); trend/serp 无量级数据取中性 5(不猜)。
退出码: 0 正常 / 1 collect 三源全缺 / 2 输入或参数错误。\
"""


def die(msg, with_usage=False):
    """输入/参数错误 → stderr + 退出码 2。"""
    sys.stderr.write(msg + ("\n" + USAGE_EPILOG if with_usage else "") + "\n")
    sys.exit(2)


def now_utc():
    """当前 UTC 时间(秒级;套件统一 timezone.utc 口径)。"""
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_dt(s):
    """ISO 时间戳 → aware datetime;无法解析 → None;naive 视作 UTC。"""
    if not isinstance(s, str) or not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def esc(t):
    """markdown 表格安全(去竖线/反引号;trend_watch 同款)。"""
    return str(t).replace("|", "\\|").replace("`", "'")


# ---------------------------------------------------------------------------
# 数据文件:读 / 原子写 / 锁(纪律同 remediation.py)
# ---------------------------------------------------------------------------
def check_item(it, where):
    """单条 idea 的最小结构校验;返回错误文案或 None。"""
    if not isinstance(it, dict):
        return "%s 不是对象" % where
    if not isinstance(it.get("id"), str) or not it["id"]:
        return "%s 缺 id 字符串" % where
    if it.get("status") not in STATUSES:
        return "%s 的 status 非法(%r;合法值: %s)" % (where, it.get("status"),
                                                     "|".join(STATUSES))
    return None


def normalize(it):
    """补齐可选字段的缺省(手写/旧版数据不炸读写端)。"""
    it.setdefault("source", "unknown")
    it.setdefault("topic", "")
    it.setdefault("evidence", "")
    it.setdefault("score", None)
    it.setdefault("created", None)
    it.setdefault("url", None)
    it.setdefault("published_at", None)
    it.setdefault("gate_rejections", 0)
    it.setdefault("entered_gated", False)
    it.setdefault("history", [])
    it.setdefault("note", "")
    return it


def load_data(path, create=False):
    """读队列数据文件;create=True 且文件不存在 → 空库(供 collect 首建);
    文件存在但结构不符 → 退出码 2(不静默降级)。"""
    if not os.path.exists(path):
        if create:
            return {"schema_version": SCHEMA_VERSION, "items": []}
        die("队列数据文件不存在: %s(先运行 collect 生成)" % path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError) as e:
        die("队列数据文件读不了: %s: %s" % (path, e))
    items = data.get("items")
    if not isinstance(items, list):
        die("队列数据格式不符: 缺 items 列表(%s)" % path)
    for n, it in enumerate(items, 1):
        err = check_item(it, "items[%d]" % n)
        if err:
            die("队列数据格式不符: %s(%s)" % (err, path))
    data.setdefault("schema_version", SCHEMA_VERSION)
    for it in items:
        normalize(it)
    return data


def save_data(path, data):
    """原子写(R5):tempfile + os.replace——中断/并发不落半截文件。"""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextlib.contextmanager
def data_lock(path, timeout=120.0):
    """数据文件级 flock(照 remediation.data_lock 惯例):lockfile 落在数据文件
    所在目录,LOCK_EX|LOCK_NB 轮询;超时 → 警告并跳过本次写(防并发覆盖丢单)。"""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    lock_path = os.path.join(d, "." + os.path.basename(path) + ".lock")
    fh = open(lock_path, "w")
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise SystemExit(
                        "警告: 另一 content_queue 进程持有 %s 超过 %.0fs,"
                        "跳过本次写(防并发覆盖丢失)" % (lock_path, timeout))
                time.sleep(0.5)
        yield
    finally:
        try:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_UN)
            else:
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:  # 等锁超时、没拿到锁时解锁会报错;close 也会释放锁
                    pass
        finally:
            fh.close()


def next_id(items):
    """顺延编号:现有最大 CQ-<N> 的 N+1,零填充三位。"""
    mx = 0
    for it in items:
        m = ID_RE.match(str(it.get("id", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    return "CQ-%03d" % (mx + 1)


def sort_key(it):
    """按编号自然排序(CQ-2 < CQ-10);非标准 id 排最后按字典序。"""
    m = ID_RE.match(str(it.get("id", "")))
    return (0, int(m.group(1)), "") if m else (1, 0, str(it.get("id", "")))


def _history(it, event, detail, now):
    it.setdefault("history", []).append(
        {"ts": now.isoformat(), "event": event, "detail": str(detail)[:120]})
    it["history"] = it["history"][-HISTORY_CAP:]


# ---------------------------------------------------------------------------
# 评分口径:score = 流量潜力 × 意图系数 × 时效加成(模块 docstring 注释即契约)
# ---------------------------------------------------------------------------
def _has_cjk(s):
    return bool(_CJK_RE.search(s))


def intent_coef(text):
    """意图系数:BOFU/对比 1.2 / MOFU 1.0 / 其余 0.8(拉丁整词边界,CJK 子串)。"""
    t = str(text or "").lower()
    for markers, coef in ((BOFU_MARKERS, 1.2), (MOFU_MARKERS, 1.0)):
        for m in markers:
            if _has_cjk(m):
                if m in t:
                    return coef
            elif re.search(r"\b%s\b" % re.escape(m), t):
                return coef
    return 0.8


def freshness_bonus(first_seen, now):
    """时效加成(仅 trend 源):<24h 1.5 / <72h 1.3 / <7d 1.1 / ≥7d 1.0;
    无/未来时间戳按 1.0(不猜)。窗口口径同 trend_watch Q3。"""
    dt = parse_dt(first_seen)
    if dt is None or dt > now:
        return 1.0
    h = (now - dt).total_seconds() / 3600.0
    if h < 24:
        return 1.5
    if h < 72:
        return 1.3
    if h < 168:
        return 1.1
    return 1.0


def traffic_potential(source, metrics):
    """流量潜力(0-10):striking 按曝光/2000、decay 按前期点击/500 封顶;
    trend/serp 无量级数据 → 中性 5(brief 阶段补,不猜)。"""
    if source == "gsc_mining:striking":
        return 10.0 * min(1.0, float(metrics.get("impressions") or 0) / 2000.0)
    if source == "gsc_mining:decay":
        return 10.0 * min(1.0, float(metrics.get("prev") or 0) / 500.0)
    return 5.0


def idea_score(source, topic, metrics, now):
    """统一 idea 分:TP × IC × FB,保留 2 位。"""
    tp = traffic_potential(source, metrics)
    ic = intent_coef(topic)
    fb = freshness_bonus(metrics.get("first_seen"), now) if source == "trend_watch" else 1.0
    return round(tp * ic * fb, 2)


# ---------------------------------------------------------------------------
# 三源读取
# ---------------------------------------------------------------------------
def read_gsc_csv(path, what):
    """GSC 导出 CSV → 行 dict 列表(列名小写+前缀匹配,兼容导出头两行题头;
    读不了 → 退出码 2)。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    except OSError as e:
        die("读不了 %s: %s: %s" % (what, path, e))
    header_idx = None
    for i, r in enumerate(rows):
        cells = [c.strip().lower() for c in r]
        if any(c.startswith("query") or c.startswith("top queries") for c in cells):
            header_idx = i
            break
    if header_idx is None:
        return []                                        # 无表头 → 0 行(明说,不猜)
    header = [c.strip().lower() for c in rows[header_idx]]
    out = []
    for r in rows[header_idx + 1:]:
        if not any(c.strip() for c in r):
            continue                                     # 空行
        r = list(r) + [""] * (len(header) - len(r))
        out.append(dict(zip(header, [c.strip() for c in r])))
    return out


def gsc_get(r, *names):
    """列前缀匹配取值(gsc_mining.get 同法)。"""
    for n in names:
        for k in r:
            if k.startswith(n):
                return r[k]
    return ""


def mine_striking(rows):
    """striking distance:gsc_mining 同口径(pos 5-20 且曝光≥20),曝光降序前 30。"""
    out = []
    for r in rows:
        q = gsc_get(r, "query", "top queries")
        if not q:
            continue
        try:
            pos = float(gsc_get(r, "position"))
            impr = float(gsc_get(r, "impressions"))
            clk = float(gsc_get(r, "clicks") or 0)
        except ValueError:
            continue
        if 5 <= pos <= 20 and impr >= 20:
            out.append({"query": q, "pos": pos, "impressions": int(impr),
                        "clicks": int(clk)})
    out.sort(key=lambda x: -x["impressions"])
    return out[:GSC_CAP]


def mine_decay(cur_rows, prev_rows):
    """衰退桶:28v28、prev≥10 且降幅≤-25%,只统计两期都出现的词(口径=gsc_mining
    --decay;缺失 prev 不默认 10——那是上游的坑,不抄),按流失点击降序前 30。"""
    pc = {}
    for r in prev_rows:
        q = gsc_get(r, "query", "top queries")
        if not q:
            continue
        try:
            pc[q] = pc.get(q, 0) + float(gsc_get(r, "clicks") or 0)
        except ValueError:
            continue
    out = []
    for r in cur_rows:
        q = gsc_get(r, "query", "top queries")
        if q not in pc or pc[q] <= 0:
            continue
        try:
            cur = float(gsc_get(r, "clicks") or 0)
        except ValueError:
            continue
        prev = pc[q]
        if prev >= 10 and (cur - prev) / prev <= -0.25:
            out.append({"query": q, "prev": int(prev), "cur": int(cur),
                        "delta": "%.0f%%" % (((cur - prev) / prev) * 100)})
    out.sort(key=lambda x: -(x["prev"] - x["cur"]))
    return out[:GSC_CAP]


def collect_trend(path, now):
    """trend 源:--trend-state 的 WATCH 态信号 → 候选列表;文件缺失 → None
    (调用方告警跳过);损坏 → 退出码 2。返回 (candidates, note)。"""
    if not os.path.exists(path):
        return None, "状态文件不存在: %s" % path
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError) as e:
        die("--trend-state 解析失败: %s: %s" % (path, e))
    signals = data.get("signals")
    if not isinstance(signals, dict):
        die("--trend-state 格式不符: 缺 signals 字典(trend_watch.py 的状态库): %s" % path)
    cands = []
    for sig in signals.values():
        if not isinstance(sig, dict) or sig.get("status") != "watch":
            continue                                     # 只收 WATCH 态(见模块 docstring)
        topic = str(sig.get("title") or "").strip()
        if not topic:
            continue
        rel = sig.get("rel_score")
        m = {"first_seen": sig.get("first_seen")}
        ev = "WATCH;Q1=%s;源=%s;first_seen=%s;deadline=%s" % (
            rel if rel is not None else "-", "+".join(sig.get("sources") or []) or "-",
            str(sig.get("first_seen") or "-")[:16], str(sig.get("deadline") or "-")[:16])
        cands.append({"source": "trend_watch", "topic": topic, "evidence": ev,
                      "score": idea_score("trend_watch", topic, m, now)})
    return cands, "WATCH 态 %d 条(信号库共 %d 条;go/pivot/open/drop 不收)" % (
        len(cands), len(signals))


def collect_gsc_csv(paths, now):
    """gsc 源(现算):--gsc CUR [PREV] → (candidates, note);文件缺失 → None。"""
    existing = [p for p in paths if os.path.exists(p)]
    if not existing:
        return None, "导出 CSV 不存在: %s" % ",".join(paths)
    cur_rows = read_gsc_csv(existing[0], "--gsc(cur)")
    cands = []
    striking = mine_striking(cur_rows)
    for m in striking:
        ev = ("GSC striking-distance(pos5-20,曝光≥20):pos=%.1f,impr=%d/mo,clicks=%d"
              % (m["pos"], m["impressions"], m["clicks"]))
        cands.append({"source": "gsc_mining:striking", "topic": m["query"],
                      "evidence": ev,
                      "score": idea_score("gsc_mining:striking", m["query"], m, now)})
    parts = ["striking %d 条(%s)" % (len(striking), existing[0])]
    if len(existing) >= 2:
        prev_rows = read_gsc_csv(existing[1], "--gsc(prev)")
        decay = mine_decay(cur_rows, prev_rows)
        for m in decay:
            ev = ("GSC 28v28 衰退≥25%%:%d→%d clicks(%s)"
                  % (m["prev"], m["cur"], m["delta"]))
            cands.append({"source": "gsc_mining:decay", "topic": m["query"],
                          "evidence": ev,
                          "score": idea_score("gsc_mining:decay", m["query"], m, now)})
        parts.append("衰退 %d 条(cur=%s vs prev=%s)"
                     % (len(decay), existing[0], existing[1]))
    return cands, ";".join(parts)


def collect_gsc_out(path, now):
    """gsc 源(预跑):gsc_mining --json 输出(query/decay 形态,或手工合并的两键
    文档)→ (candidates, note);文件缺失 → None;结构不符 → 退出码 2。"""
    if not os.path.exists(path):
        return None, "预跑输出不存在: %s" % path
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (ValueError, OSError) as e:
        die("--gsc-out 解析失败: %s: %s" % (path, e))
    if not isinstance(d, dict):
        die("--gsc-out 格式不符: 顶层须为 JSON 对象(gsc_mining --json 输出): %s" % path)
    striking = d.get("striking_distance")
    declined = d.get("declined")
    for name, val in (("striking_distance", striking), ("declined", declined)):
        if val is not None and not isinstance(val, list):
            die("--gsc-out 格式不符: %s 须为列表: %s" % (name, path))
    if striking is None and declined is None:
        die("--gsc-out 格式不符: 缺 striking_distance/declined 列表"
            "(gsc_mining --json 的 query/decay 形态): %s" % path)
    cands = []
    for m in striking or []:
        if not isinstance(m, dict) or not m.get("query"):
            continue
        mm = {"impressions": m.get("impressions")}
        ev = ("GSC striking-distance(预跑):pos=%s,impr=%s/mo,clicks=%s"
              % (m.get("pos"), m.get("impressions"), m.get("clicks")))
        cands.append({"source": "gsc_mining:striking", "topic": str(m["query"]),
                      "evidence": ev,
                      "score": idea_score("gsc_mining:striking", m["query"], mm, now)})
    for m in declined or []:
        if not isinstance(m, dict) or not m.get("query"):
            continue
        mm = {"prev": m.get("prev")}
        ev = "GSC 衰退(预跑):%s→%s clicks(%s)" % (m.get("prev"), m.get("cur"),
                                                   m.get("delta"))
        cands.append({"source": "gsc_mining:decay", "topic": str(m["query"]),
                      "evidence": ev,
                      "score": idea_score("gsc_mining:decay", m["query"], mm, now)})
    return cands, "预跑输出:striking %d + 衰退 %d" % (
        len(striking or []), len(declined or []))


def collect_serp(path, now):
    """serp 源(预跑存盘文本):共享域≥4 的对 → 对比页缺口;互链/分开只计数。"""
    if not os.path.exists(path):
        return None, "预跑输出不存在: %s" % path
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("--serp-out 读取失败: %s: %s" % (path, e))
    cands, skipped = [], 0
    for line in text.splitlines():
        m = SERP_ROW_RE.match(line.strip())
        if not m:
            continue                                     # 表头/表线/非数据行
        a, b, shared, verdict = m.group(1).strip(), m.group(2).strip(), \
            int(m.group(3)), m.group(4)
        if shared < SERP_GAP_MIN_SHARED:
            skipped += 1
            continue
        topic = "%s × %s" % (a, b)
        ev = "SERP 重叠 %d/10 共享域(%s)→ 一页可服务两词" % (shared, verdict)
        cands.append({"source": "serp_overlap", "topic": topic, "evidence": ev,
                      "score": idea_score("serp_overlap", "%s %s" % (a, b), {}, now)})
    return cands, "缺口 %d 条(共享≥4);跳过 %d 条(互链/分开,不单开页)" % (
        len(cands), skipped)


# ---------------------------------------------------------------------------
# collect:三源合并 → 统一 idea 入库
# ---------------------------------------------------------------------------
def cmd_collect(rest):
    ap = argparse.ArgumentParser(prog="content_queue.py collect")
    ap.add_argument("--trend-state", default=DEFAULT_TREND_STATE,
                    help="trend_watch 状态库(默认当前目录 .trend-state.json;取 WATCH 态信号)")
    ap.add_argument("--gsc", action="append", default=[], metavar="CSV",
                    help="GSC 导出 CSV(现算):一次给 cur,两次给 cur prev(加算衰退桶);可与其他源并用")
    ap.add_argument("--gsc-out", action="append", default=[], metavar="JSON",
                    help="gsc_mining --json 预跑输出(query/decay 形态;可多份)")
    ap.add_argument("--serp-out", action="append", default=[], metavar="TXT",
                    help="serp_overlap.py 预跑存盘输出(表格文本;可多份)")
    ap.add_argument("--file", default=DEFAULT_FILE, help="队列数据文件(默认 contentops.json)")
    ap.add_argument("--json", action="store_true", help="机读输出")
    a = ap.parse_args(rest)          # 参数错/--help 由 argparse 处理(exit 2/0,同口径)
    if len(a.gsc) > 2:
        die("--gsc 至多两个文件(cur [prev]);更多期对比请用 --gsc-out 预跑")

    now = now_utc()
    src_status = {}          # 源名 → {"state": ok|missing|empty, "candidates": n, "note": …}
    candidates = []

    cands, note = collect_trend(a.trend_state, now)
    src_status["trend_watch"] = {"state": "ok" if cands is not None else "missing",
                                 "candidates": len(cands or []), "note": note}
    if cands is None:
        sys.stderr.write("[warn] 跳过 trend 源: %s\n" % note)
    else:
        candidates.extend(cands)

    gsc_parts, gsc_missing = [], True
    if a.gsc:
        cands, note = collect_gsc_csv(a.gsc, now)
        gsc_missing = False
        gsc_parts.append((cands, note))
    for p in a.gsc_out:
        cands, note = collect_gsc_out(p, now)
        gsc_missing = False
        gsc_parts.append((cands, note))
    if gsc_missing:
        src_status["gsc_mining"] = {"state": "missing", "candidates": 0,
                                    "note": "未提供 --gsc/--gsc-out"}
        sys.stderr.write("[warn] 跳过 gsc 源: 未提供 --gsc/--gsc-out\n")
    else:
        for cands, note in gsc_parts:
            if cands is None:
                sys.stderr.write("[warn] 跳过 gsc 输入: %s\n" % note)
        ok_cands = [c for c, _ in gsc_parts if c is not None]
        got_any = bool(ok_cands)
        merged = [c for cands in ok_cands for c in cands]
        candidates.extend(merged)
        src_status["gsc_mining"] = {
            "state": "ok" if got_any else "missing", "candidates": len(merged),
            "note": "; ".join(n for c, n in gsc_parts if c is not None) or
                    "; ".join(n for _, n in gsc_parts)}

    if a.serp_out:
        serp_c, serp_notes, serp_ok = [], [], False
        for p in a.serp_out:
            cands, note = collect_serp(p, now)
            if cands is None:
                sys.stderr.write("[warn] 跳过 serp 输入: %s\n" % note)
            else:
                serp_ok = True
                serp_c.extend(cands)
                serp_notes.append(note)
        candidates.extend(serp_c)
        src_status["serp_overlap"] = {"state": "ok" if serp_ok else "missing",
                                      "candidates": len(serp_c),
                                      "note": "; ".join(serp_notes)}
    else:
        src_status["serp_overlap"] = {"state": "missing", "candidates": 0,
                                      "note": "未提供 --serp-out"}
        sys.stderr.write("[warn] 跳过 serp 源: 未提供 --serp-out\n")

    any_source = any(v["state"] == "ok" for v in src_status.values())
    new_items, skipped = [], 0
    with data_lock(a.file):
        data = load_data(a.file, create=True)
        existing = {(it.get("source"), it.get("topic")) for it in data["items"]}
        for c in candidates:
            if (c["source"], c["topic"]) in existing:    # 幂等:同源同题不重复入库
                skipped += 1
                continue
            item = {"id": next_id(data["items"]), "source": c["source"],
                    "topic": c["topic"], "evidence": c["evidence"], "score": c["score"],
                    "status": "idea", "created": now.isoformat(), "url": None,
                    "published_at": None, "gate_rejections": 0,
                    "entered_gated": False,
                    "history": [{"ts": now.isoformat(), "event": "collect",
                                 "detail": "入队(source=%s)" % c["source"]}],
                    "note": ""}
            data["items"].append(item)
            existing.add((c["source"], c["topic"]))
            new_items.append(item)
        if any_source:
            save_data(a.file, data)   # 有可用源即落库(0 新增也建文件,供 plan/report)

    if a.json:
        print(json.dumps({"schema_version": SCHEMA_VERSION,
                          "file": os.path.abspath(a.file), "new": len(new_items),
                          "skipped_dup": skipped, "total": len(data["items"]),
                          "sources": src_status,
                          "ideas": new_items}, ensure_ascii=False, indent=1))
    else:
        for name in ("trend_watch", "gsc_mining", "serp_overlap"):
            s = src_status[name]
            print("[%s] %s" % (name, s["note"] if s["state"] != "missing"
                               else "缺源跳过 —— %s" % s["note"]))
        print("collect: 新增 %d 条 idea(去重跳过 %d)→ %s(总 %d)"
              % (len(new_items), skipped, os.path.abspath(a.file), len(data["items"])))
    if not any_source:
        sys.stderr.write("[error] 三源全缺(未提供或文件不存在),没东西可收;"
                         "至少提供一个源\n")
        return 1
    return 0


# ---------------------------------------------------------------------------
# plan:周排期 markdown(Top N + WIP 上限 + 建议管线)
# ---------------------------------------------------------------------------
def pipeline_for(source):
    """源 → 建议管线(spec 口径:trend→trend-jack / 关键词→content-brief / 缺口→对比页)。"""
    if source == "trend_watch":
        return ("trend-jack 管线",
                "trend_watch gate 过闸 → 决策件(templates/content/trend-jack-playbook.md)"
                "→ 写作 → templates/content/pre-publish-checklist.md")
    if source == "gsc_mining:decay":
        return ("content-brief 管线",
                "templates/content/content-brief.md;衰退桶优先按"
                " references/content/content-refresh-playbook.md 刷新既有页")
    if source.startswith("gsc_mining"):
        return ("content-brief 管线", "templates/content/content-brief.md")
    return ("对比页模板",
            "references/content/content-structure-templates.md §对比(A vs B):"
            "结论先行→对比表→分维度→各自适合谁")


def cmd_plan(rest):
    ap = argparse.ArgumentParser(prog="content_queue.py plan")
    ap.add_argument("--week", default=None,
                    help="周标签(默认当前 ISO 周,如 2026-W42;仅作排期标题)")
    ap.add_argument("--top", type=int, default=10, help="参与排期的 Top N(按分数,默认 10)")
    ap.add_argument("--wip", type=int, default=3,
                    help="WIP 上限(briefed+drafting+gated;默认 3;超限只列不排)")
    ap.add_argument("--file", default=DEFAULT_FILE)
    a = ap.parse_args(rest)
    if a.top < 0 or a.wip < 0:
        die("--top/--wip 须为非负整数")
    data = load_data(a.file)
    items = data["items"]
    now = now_utc()
    week = a.week or "%d-W%02d" % (now.isocalendar()[0], now.isocalendar()[1])

    wip_items = sorted((it for it in items if it["status"] in WIP_STATUSES), key=sort_key)
    ideas = sorted((it for it in items if it["status"] == "idea"),
                   key=lambda it: (-(it.get("score") or 0), sort_key(it)))
    wip_now = len(wip_items)
    slots = max(0, a.wip - wip_now)
    top = ideas[:a.top]
    scheduled, deferred = top[:slots], top[slots:]

    def table(rows):
        cols = ("ID", "分数", "源", "选题", "建议管线")
        body = [[it["id"], ("%.2f" % it["score"]) if it.get("score") is not None else "-",
                 it.get("source", ""), esc(str(it.get("topic", ""))[:56]),
                 pipeline_for(it.get("source", ""))[0]] for it in rows]
        widths = [len(c) for c in cols]
        for r in body:
            for n, v in enumerate(r):
                widths[n] = max(widths[n], len(v))
        out = [" ".join(c.ljust(widths[n]) for n, c in enumerate(cols)).rstrip(),
               " ".join("-" * w for w in widths)]
        for r in body:
            out.append(" ".join(v.ljust(widths[n]) for n, v in enumerate(r)).rstrip())
        return "\n".join(out)

    L = ["# 内容周排期:%s" % week, "",
         "- 数据文件: %s(共 %d 条;生成于 %s)"
         % (os.path.abspath(a.file), len(items), now.date().isoformat()),
         "- WIP: 当前 %d / 上限 %d → 本周可排 %d 条;idea 积压 %d"
         % (wip_now, a.wip, slots, len(ideas)),
         "- 口径: plan 只排期不改状态;开工用 track --status briefed 逐级推进", ""]
    L.append("## 在制(WIP %d/%d)" % (wip_now, a.wip))
    L.append(table([dict(it, source=it.get("source", "") + " (" + it["status"] + ")")
                    for it in wip_items]) if wip_items else "(无在制)")
    L.append("")
    L.append("## 本周排期(%d 条;Top %d 按分数)" % (len(scheduled), a.top))
    L.append(table(scheduled) if scheduled
             else "(0 条 —— WIP 已满或无 idea;候补见下)")
    if deferred:
        L.append("")
        L.append("## 候补(超 WIP 上限,只列不排;%d 条)" % len(deferred))
        L.append(table(deferred))
    L.append("")
    L.append("## 建议管线对照")
    L.append("- trend 源 → trend-jack 管线: %s" % pipeline_for("trend_watch")[1])
    L.append("- 关键词源(gsc_mining) → content-brief 管线: %s"
             % pipeline_for("gsc_mining:striking")[1])
    L.append("- 衰退桶(gsc_mining:decay) → %s" % pipeline_for("gsc_mining:decay")[1])
    L.append("- 缺口源(serp_overlap) → 对比页模板: %s" % pipeline_for("serp_overlap")[1])
    print("\n".join(L))
    return 0


# ---------------------------------------------------------------------------
# track:六态状态机(remediation 纪律)+ 推进后遥测
# ---------------------------------------------------------------------------
def telemetry(items):
    """ContentOps 遥测三指标(lead time / WIP / 按闸拒收率);口径见模块 docstring。"""
    lead = []
    for it in items:
        c, p = parse_dt(it.get("created")), parse_dt(it.get("published_at"))
        if c is not None and p is not None and p >= c:
            lead.append((it.get("id", "?"), round((p - c).total_seconds() / 86400.0, 1)))
    days = sorted(d for _, d in lead)
    wip = sum(1 for it in items if it.get("status") in WIP_STATUSES)
    rej = sum(int(it.get("gate_rejections") or 0) for it in items)
    entered = sum(1 for it in items
                  if it.get("entered_gated") or int(it.get("gate_rejections") or 0) > 0)
    lt = None
    if days:
        lt = {"n": len(days), "median": round(statistics.median(days), 2),
              "mean": round(statistics.mean(days), 2),
              "min": round(min(days), 2), "max": round(max(days), 2),
              "items": [{"id": i, "days": d} for i, d in sorted(lead, key=lambda x: x[0])]}
    return {"lead_time_days": lt, "wip": wip,
            "gate_rejections": {"count": rej, "entered_gated": entered,
                                "rate": (round(rej / entered, 3) if entered else None)}}


def telemetry_line(t):
    """track 推进后的一行遥测速览。"""
    lt = t["lead_time_days"]
    g = t["gate_rejections"]
    lt_s = ("n=%d(中位 %.1fd)" % (lt["n"], lt["median"])) if lt else "N/A(尚无 published)"
    rate = ("%d%%(%d/%d)" % (round(g["rate"] * 100), g["count"], g["entered_gated"])
            if g["rate"] is not None else "N/A(尚无进闸)")
    return "遥测: lead time %s / WIP 当前 %d / 闸拒收率 %s" % (lt_s, t["wip"], rate)


def cmd_track(rest):
    ap = argparse.ArgumentParser(prog="content_queue.py track")
    ap.add_argument("id", help="idea 编号(CQ-001)")
    ap.add_argument("--status", default=None,
                    help="目标态:%s(逐级前进;published 需 --url)" % "|".join(TRACK_TARGETS))
    ap.add_argument("--reject", action="store_true",
                    help="按闸打回:gated → drafting(唯一合法回退,计一次拒收)")
    ap.add_argument("--url", default=None, help="发布 URL(--status published 时必填,http/https)")
    ap.add_argument("--note", default=None, help="备注(存 note 字段)")
    ap.add_argument("--file", default=DEFAULT_FILE)
    a = ap.parse_args(rest)
    if a.reject and a.status:
        die("--reject 与 --status 互斥(打回走 --reject,推进走 --status)")
    if not a.reject and a.status is None:
        die("缺少 --status 或 --reject\n", with_usage=True)
    if a.status is not None and a.status not in TRACK_TARGETS:
        die("--status 非法 %r;track 只接受 %s(idea 是初始态不可作为目标——降级拒绝)"
            % (a.status, "|".join(TRACK_TARGETS)))
    if a.url is not None and a.status != "published":
        die("--url 仅在 --status published 时接受")

    with data_lock(a.file):
        data = load_data(a.file)
        item = next((it for it in data["items"] if it.get("id") == a.id), None)
        if item is None:
            die("找不到 idea %r(%s 中共 %d 条)" % (a.id, a.file, len(data["items"])))
        cur = item["status"]
        now = now_utc()
        if a.reject:
            if cur != "gated":
                die("按闸打回只对 gated 态合法(当前 %s;降级拒绝口径同 remediation)"
                    % cur)
            item["status"] = "drafting"
            item["gate_rejections"] = int(item.get("gate_rejections") or 0) + 1
            _history(item, "gate-reject", "gated → drafting(第 %d 次打回)"
                     % item["gate_rejections"], now)
            save_data(a.file, data)
            print("track: %s gated → drafting(按闸打回,累计 %d 次)"
                  % (a.id, item["gate_rejections"]))
        else:
            new = a.status
            if (cur, new) not in TRANSITIONS:
                die("非法状态转换 %s → %s;合法链 idea→briefed→drafting→gated→"
                    "published→measured 逐级前进(跳级/回退/同态拒绝——降级拒绝);"
                    "gated 打回走 --reject" % (cur, new))
            if new == "published":
                p = urllib.parse.urlparse(a.url or "")
                if p.scheme not in ("http", "https") or not p.netloc:
                    die("--status published 必须带合法 --url(http/https;如 "
                        "https://example.com/post)")
                item["url"] = a.url
                item["published_at"] = now.isoformat()
            if new == "gated":
                item["entered_gated"] = True
            item["status"] = new
            _history(item, "track", "%s → %s" % (cur, new), now)
            save_data(a.file, data)
            print("track: %s %s → %s%s" % (a.id, cur, new,
                                           "(url=%s)" % item["url"]
                                           if new == "published" else ""))
        if a.note is not None:
            item["note"] = a.note
            save_data(a.file, data)
    print(telemetry_line(telemetry(data["items"])))
    return 0


# ---------------------------------------------------------------------------
# report:遥测 + 状态分布
# ---------------------------------------------------------------------------
def cmd_report(rest):
    ap = argparse.ArgumentParser(prog="content_queue.py report")
    ap.add_argument("--file", default=DEFAULT_FILE)
    ap.add_argument("--json", action="store_true", help="机读输出")
    a = ap.parse_args(rest)
    data = load_data(a.file)
    items = sorted(data["items"], key=sort_key)
    counts = {s: 0 for s in STATUSES}
    for it in items:
        counts[it["status"]] += 1
    t = telemetry(items)
    if a.json:
        print(json.dumps({"schema_version": SCHEMA_VERSION,
                          "file": os.path.abspath(a.file), "total": len(items),
                          "counts": counts, "wip": t["wip"],
                          "telemetry": t}, ensure_ascii=False, indent=1))
        return 0
    g = t["gate_rejections"]
    lt = t["lead_time_days"]
    L = ["# 内容队列 ContentOps 报告", "",
         "- 数据文件: %s(共 %d 条 idea)" % (os.path.abspath(a.file), len(items)),
         "- 状态分布: %s" % " / ".join("%s %d" % (s, counts[s]) for s in STATUSES),
         "- WIP 当前: %d(briefed+drafting+gated;上限由 plan --wip 控制,默认 3)"
         % t["wip"],
         "- 按闸拒收: %d 次打回 / %d 条进闸 = %s"
         % (g["count"], g["entered_gated"],
            ("%d%%" % round(g["rate"] * 100)) if g["rate"] is not None else "N/A"),
         "", "## 遥测"]
    if lt:
        L.append("- Lead time(idea→published): n=%d,中位 %.1fd,均值 %.1fd,"
                 "区间 %.1f-%.1fd" % (lt["n"], lt["median"], lt["mean"], lt["min"],
                                      lt["max"]))
        L.append("  - 明细: %s" % "; ".join("%s %.1fd" % (i["id"], i["days"])
                                           for i in lt["items"]))
    else:
        L.append("- Lead time(idea→published): N/A(尚无带 published_at 的条目)")
    wip_items = [it for it in items if it["status"] in WIP_STATUSES]
    if wip_items:
        L += ["", "## 在制清单(%d)" % len(wip_items)]
        L += ["- %s [%s] %s(打回 %d 次)" % (it["id"], it["status"],
                                             esc(str(it.get("topic", ""))[:56]),
                                             int(it.get("gate_rejections") or 0))
              for it in wip_items]
    print("\n".join(L))
    return 0


COMMANDS = {"collect": cmd_collect, "plan": cmd_plan, "track": cmd_track,
            "report": cmd_report}


class _ArgParser(argparse.ArgumentParser):
    """argparse 参数错误 → exit 2(remediation 同口径),不走默认 exit 2 之外的码。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print("[error] 参数错误: %s(exit 2)" % message, file=sys.stderr)
        sys.exit(2)


def build_parser():
    p = _ArgParser(
        prog="content_queue.py",
        description=("选题合并队列 + ContentOps 遥测:trend_watch WATCH 态 + gsc_mining "
                     "striking/衰退 + serp_overlap 缺口 → 统一 idea(contentops.json)→ "
                     "周排期(WIP 上限)→ 六态状态机 → 遥测(lead time/WIP/闸拒收率)。"
                     "规格: pipeline-completeness.md R1-8 + 内容生产体系报告。"),
        epilog=USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", metavar="{collect,plan,track,report}")
    sub.add_parser("collect", help="合并三源 → 统一 idea 入库(缺源跳过告警不猜)")
    sub.add_parser("plan", help="周排期 markdown(Top N 按分数 + WIP 上限 + 建议管线)")
    sub.add_parser("track", help="状态机推进(降级拒绝;published 需 --url;gated --reject 打回)")
    sub.add_parser("report", help="ContentOps 遥测三指标 + 状态分布")
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # 子命令后的 --help 交给子命令自己的 argparse(列出该子命令的参数);只有总帮助在这里打印
    if argv and argv[0] in COMMANDS:
        return COMMANDS[argv[0]](argv[1:])
    if any(x in ("-h", "--help") for x in argv):
        build_parser().print_help()
        return 0
    if not argv:
        build_parser().print_usage(sys.stderr)
        sys.stderr.write("缺少子命令(collect|plan|track|report)\n")
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        die("未知子命令 %r;合法值: %s" % (cmd, "|".join(COMMANDS)), with_usage=True)
    return COMMANDS[cmd](rest)


if __name__ == "__main__":
    sys.exit(main())
