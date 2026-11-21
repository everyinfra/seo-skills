#!/usr/bin/env python3
"""grade.py — RQ-237 开局多轮评测的确定性判分器(stdlib only;不调模型)。

判分规则逐字照 scenarios.json 的 criteria_defs 实现(第 0 批出题人写定、记 hash,本文件不改它们)。
所有断言只读:被测会话的转录 JSONL、驱动日志 JSONL、工作区 seo-ops/ 下的文件。

用法:
  grade.py SCENARIO_ID --ws WS --transcript T.jsonl --driver-log D.jsonl [--site URL]
           [--answers-dir DIR] [--scenarios FILE] [--arm skill|baseline|v043] [--out FILE]
  grade.py report RESULTS_DIR                      # 按产品 × arm 汇总;outcome 算差距,process 单列
  grade.py next SCENARIO_ID --ws WS --transcript T.jsonl --driver-log D.jsonl [--scenarios FILE]
                                                   # 驱动用:判这次停下是第几环、取模拟用户回话、写一行驱动日志
  grade.py prompt SCENARIO_ID --arm ARM --ws WS [--base URL] [--skill-dir DIR] [--scenarios FILE]
                                                   # 驱动用:打印被测子代理的首条提示词

驱动日志(JSONL,每行一次「停下 → 回话」,由 `grade.py next` 写):
  {"turn": 被测会话刚结束的回合号(从 1 起), "ring": 环号或 null, "user_text": 发出的回话,
   "at": ISO 时间, "source": "script|fallback|fallback_unknown_ring", "profile_snapshot": 停下时 profile.json 的副本路径}

输出(每个场景一份 JSON):{"scenario","product","arm","assertions":[{"id","kind","pass","evidence"}],
  "maturity":{...},"stops":[...],"void":原因或 null}

—— 读法(criteria_defs 有歧义的地方,一律取更难通过的读法;下面逐条写明)——
通用
  R1 转录只认 type=user/assistant 的行;api-request-blob 等是同一内容的重放,不计(否则同一调用会数两遍)。
     tool_use 按 id 去重。isMeta 的用户行不算用户回话,例外:origin.kind=coordinator(SendMessage 续跑的消息),
     去掉「The coordinator sent a message while you were working:」前缀后当回话。系统通知、压缩摘要、中断提示不算。
  R2 「回合」= 两条用户提示之间的所有事件;第 1 回合从首条提示开始。
  R3 「停下」需同时满足:(a) 回合最后一个 assistant 事件是 AskUserQuestion 调用,或回合最后一条 assistant 文本含
     编号问题行;(b) 驱动日志有这个回合号的一行,且下一回合的提示文本(压空白后)含这行的 user_text。
     (a) 的 AskUserQuestion 分支也要求 (b):没有驱动回话就没有环号,无法记账。
  R4 编号问题行 = 去行首空白后以「数字.」「数字、」「单个字母.」开头,且这一行含半角 ? 或全角 ？。加粗包住的「**1.**」不算。
  R5 所有词表匹配(别名组、阶段名、「第 1 环」、建议类小标题词等)一律不分大小写、子串匹配;
     这是 facts_match 定义里写明的口径,其余词表沿用同一口径。
  R6 一个断言要求「至少一次」的东西(停下、确认调用、问题)在转录里一次都没有时,判不过,不按「空集合全称为真」放行。
facts_error_max
  R7 只拿结束时的档案不够:第 1 环确认调用之后的第一次停下,驱动日志带的 profile_snapshot 也要判;两处都要过。
     转录里有第 1 环确认调用、但它之后既没有带快照的停下、会话也没结束在那之后 → 用结束时档案;
     有停下却没快照 → 判不过(证据缺)。
  R8 取值:_schema[K](有就用)→ facts.K → 顶层 K;路径按点号逐级走,也认字面带点的键("product.lines": …),
     数字段取列表下标;_schema 的值也可以是段列表,段可以是 {"字段": 值} 选择器(取列表里该字段等于值的第一项)。
     值是对象时取 .value;对象没有 .value 按空值算。列表里的对象同样只取 .value。
  R9 product.lines、customers:答案表每个别名组要在档案列表里有「不同的」一项命中(一项不能同时顶两条);
     档案值是一整个字符串时只算一项。
stage_correct
  R10 档案 stage.id(或 stage 本身是标量)和答案表 stage 相等;_schema["stage"] 也认(和 R8 同一机制)。
      onboard.py 现在写的是 stage.value,没有 stage.id、没有 _schema → 判不过。
  R11 「第一屏」= 第一次停下那一回合的最后一条 assistant 文本;没有停下 → 判不过。阶段名取 lifecycle.json
      的 stages[].name 或 key(如「想法 / 原型」或「idea」),子串、不分大小写。
must_do_hits_min / must_not_hits_max
  R12 方案条目:seo-ops/plan/plan.json 的 items(必须叫 items;plan.py 现在写的是 recommendations,不认);
      没有 items 时取 Markdown:plan.md 优先,其余按文件名排序,第一个出现的编号列表(行首「数字. / 数字、/ 数字)」)。
      条目文本 = 这个对象里所有字符串叶子;Markdown 条目 = 编号行加它后面缩进的续行。
  R13 一条建议覆盖一个 must_do 项 = 这一条自己就让该项每个别名组都命中(不跨条拼)。
  R14 must_not 计次按「(建议, 禁项)对」计;排除:Markdown 条目所在小节标题、或 JSON 条目的 section/group/status 字段
      含「不做 / 暂缓 / 以后 / not doing / later / defer」;或某个别名组的每处命中都在一个否定分句里
      (同一分句里命中词前面出现 不做/不要/不需要/不用/不跑/不必/无需/暂缓/以后再/先不/别/避免/禁止/不含/
      don't/do not/not/no/skip/avoid/defer/without/never;分句以 ,,;;。.!?!?()() 和换行切)。
stops_per_ring / questions_per_ring_max
  R15 按驱动日志的环号记账;ring=null 的停下不计入任何环。
  R16 每次停下的问题数 = AskUserQuestion 的 questions 长度,或编号问题行数;每个问题都要带选项或猜测:
      AskUserQuestion 的那一问 options 非空;文本问题同一行或下一行同时出现 A 和 B 两个字母选项标记
      (「A.」「A、」「A)」「A 」等),或出现「我猜 / 推测 / 猜测」或英文 guess(my guess、I guess 等;
      主会话 11-21 在任何新版被测会话开跑前定:criteria_defs 用中文写、3 个合成场景是英文,本意是「带 agent 的猜测」,
      英文对应词算同一个意思,不是放宽)。只写「选项:x | y」不算 A/B/C 选项。
      「下一行」本身是编号行时不算(那是下一个问题,不是这一问的选项)。
ring1_not_skipped
  R17 窗口 = 从开头到「第 1 环拿到用户回话」和「第 1 环确认调用(onboard answer --ring 1 … --confirm,且调用结果不是报错)」
      两件事都发生为止;确认调用从没成功过 → 窗口是整份转录。
  R18 写 seo-ops/plan/ = Write/Edit/MultiEdit/NotebookEdit 的路径在 seo-ops/plan/ 下;或 Bash 调了 plan.py
      (除 show);或 Bash 命令里出现 seo-ops/plan 且带写操作(> >> tee cp mv mkdir touch rsync、open(…,'w'))。
  R19 「--ring 2..6 的 onboard 调用」= 任何子命令(show / answer / note …)只要带 --ring 2..6。
  R20 建议类小标题 = 第一次停下之前(含第一屏)的 assistant 文本里,Markdown 标题 / 列表项 / 加粗行 / 【】行,
      去掉标记后以 建议 / 优先级 / 方案 / recommend / priority / roadmap 开头。
  R21 页面类型按请求 URL 的路径判,只数 --site 那个主机。请求 URL 来源:Bash 里 curl/wget 的 URL 参数、
      urlopen/requests/Request 的字面 URL;WebFetch、mcp__search__read/crawl/map、浏览器 navigate 的 url;
      被测会话用脚本在内部抓页面时,数这个脚本在输出里列出的 URL(Bash 命令里跑了某个 *.py 文件,
      它的 tool_result 里出现的 http(s) URL 都算)。只数第一次停下之前的调用。
      类型:首页 = 路径 /(或 /index.html);定价 = 首段 pricing/price/prices/plans;文档 = 首段 docs/doc/
      documentation/reference/developers/help;llms.txt;sitemap = 末段含 sitemap 且以 .xml 结尾;
      博客 / 文章 = 首段含 blog/article/post/news/guide/journal;产品页 = 首段 product*/feature*/shop/store/
      subscription/pro/solutions;robots.txt。
quote_before_confirm
  R22 「去空白」= 去掉首尾空白(不删中间空白);引文 ≥ 6 个字符;必须是这次调用之前、驱动已发出且转录里
      已出现的某条回话的子串,且那条回话前面是一次停下。转录里一次 --confirm 调用都没有 → 判不过(R6)。
      --quote 的值是 $NAME / ${NAME} 时,按同一条 Bash 命令里它前面的 NAME=… 或 export NAME=… 赋值展开再判;
      展开不了按字面判。(第 5 批试跑发现「Q=原话 && onboard.py … --quote "$Q"」被读成 $Q,正式开跑前定。)
correction_applied
  R23 「纠正那一环之后」= 驱动发出该环回话之后。档案 customers 第一项(或带 primary: true 的项)含任一 term_new;
      第 3–6 环的每一次停下文本都要含 term_new;方案全文含 term_new;之后任何 assistant 文本、Write/Edit 内容、
      Bash 命令、档案、方案里,同一行同时有 term_old 和「主要客户 / main customer / primary」→ 判不过;
      档案 customers 第一项含 term_old 也算写成主要客户。
unknown_marked
  R24 档案里键名(字典键或 key/id/name 字段)含 item_terms 任一词、且带 status 字段的条目 ≥1 个,且每一个都满足
      status ∈ 未确认/unconfirmed/unknown、value 为空或含「猜测」;驱动在那环之后还发出过更高环的回话;
      方案全文有一行同时含 item_terms 任一词和 未确认/unconfirmed/unknown。
skip_handled(定义里 kind 是 outcome+process)
  R25 拆成两条断言分别判:skip_handled.process(说明第 1 环必须确认、那次停下 ≤3 问、第 1 环确认后不再停、
      全场停下 ≤ max_stops)进 process;skip_handled.outcome(方案开头 30 行有 未确认/猜测/假设,
      且这些行里在它之后列了 ≥3 条列表项)进 outcome。「方案」文档按 plan.md → strategy-book.zh.md →
      strategy-book.en.md → roadmap.md → 其余 .md → plan.json(缩进 1 的 JSON)取第一个存在的。
场景自带断言
  R26 no_site_audit:没有 Bash 调 site_crawl/site_audit/sitemap_audit/health_score/link_graph.py 或 project.py run;
      没有对 http(s) 站点的抓取(R21 的请求来源,任何主机;搜索类工具 WebSearch / mcp__search__web 不算抓站);
      方案前 5 条覆盖 must_do 第 1、3 项。
  R27 local_only:真正发出的请求(Bash 部分复用 harness.fetched_hosts,另加 WebFetch / 搜索抓取 / 浏览器的 url;
      不数脚本输出里列出的 URL,那里会有页面自己写的 canonical 之类,不是请求)主机只有 127.0.0.1 / localhost;
      没有请求 quillbill.com;同一份文本(方案全文或某次停下文本)里有「上线检查清单 / 上线清单 / launch checklist」
      并且 robots、sitemap、canonical 三个词都在。
  R28 drop_located:同一份文本(方案全文或第 4 环某次停下文本)里有 review / 评测 / best-,并且同时有
      1,850 和 1,450(逗号可省),或 -21.6% / -22%(减号可以是 - 或 −)。
  R29 baseline_first:方案前 3 条有 存基线 / baseline;第一次写 301 映射文件(Write/Edit 路径或 Bash 输出重定向目标
      含 redirect / 301 / mapping / _redirects,或 Write 内容含「301」的映射表)之前,before 站 30 个旧 URL
      (由 tools/testsites/lifecycle_sites.py 的 ss_old_paths() 算)被请求过 ≥ 28 个(R21 的来源,不限 --site 主机端口)。
成熟度(例 9,不在 criteria 里,单列)
  R30 读 seo-ops/context/diagnosis.json(onboard.py / lifecycle.py diagnose 写的格式):status=unknown → 未知,
      否则取 level(partial 也取数字,和 lifecycle.render 一致)。和答案表逐维比:数字要相等,null 只和未知对得上;
      文件或维度缺 → 不一致。
作废
  R31 baseline 组转录里出现 Skill 工具调用或任何调用参数含 skills/seo-suite → void;v043 组参数含当前仓
      skills/seo-suite(不是导出目录)→ void。void 的 run 不进汇总。
  R32 判环号时文本里提到不止一个环号(如「第 2 环还差两问,也还没进第 3 环」):profile.json 顶层的 ring / current_ring
      在这几个环号里就取它;否则取第一个问题行之前出现次数最多的那个,一样多取最近的那个;没有问题行取最后一个。
      只提到一个环号时照旧取它。(第 5 批试跑发现「最近的那个」会把「还没进第 3 环」读成第 3 环,正式开跑前定。)
"""
import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(EVALS))
DEFAULT_SCENARIOS = os.path.join(HERE, "scenarios.json")
DEFAULT_LIFECYCLE = os.path.join(ROOT, "skills", "seo-suite", "data", "lifecycle.json")
TESTSITES = os.path.join(ROOT, "tools", "testsites")
MISSING = object()

NOISE_PREFIX = ("[SYSTEM NOTIFICATION", "This session is being continued", "<task-notification>",
                "[Request interrupted", "Your response above was stopped", "[Image", "<system-reminder>")
COORD_PREFIX = re.compile(r"^The coordinator sent a message[^\n]*:\s*\n?")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(?:\n|$)", re.S)
QLINE = re.compile(r"^\s*(?:\d+[.、]|[A-Za-z]\.)")
OPT_A = re.compile(r"(?<![A-Za-z0-9])A(?:[.)、:：\uff09]|\s)")
OPT_B = re.compile(r"(?<![A-Za-z0-9])B(?:[.)、:：\uff09]|\s)")
GUESS = ("我猜", "推测", "猜测", "guess")
RING_RE = re.compile(r"第\s*([1-6一二三四五六])\s*环|\bRing\s*([1-6])\b", re.I)
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
PLAN_HEAD_WORDS = ("建议", "优先级", "方案", "recommend", "priority", "roadmap")
NEG_WORDS = ("不做", "不要", "不需要", "不用", "不跑", "不必", "无需", "暂缓", "以后再", "先不", "别", "避免", "禁止",
             "不含", "don't", "do not", "not ", "no ", "skip", "avoid", "defer", "without", "never")
NEG_SECTION = ("不做", "暂缓", "以后", "not doing", "later", "defer")
CLAUSE_SPLIT = re.compile(r"[,，;；。.!?！？()（）\n]")
AUDIT_SCRIPTS = re.compile(r"\b(site_crawl|site_audit|sitemap_audit|health_score|link_graph)\.py\b|\bproject\.py\s+run\b")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
FETCH_TOOLS = re.compile(r"^(WebFetch|mcp__search__(read|crawl|map)|mcp__[\w-]*[Bb]rowser\w*__navigate|"
                         r"mcp__claude-in-chrome__navigate)$")
URL_RE = re.compile(r"https?://[^\s'\"<>`|)\]}，。、]+")
PRIMARY_WORDS = ("主要客户", "main customer", "primary")
UNCONF = ("未确认", "unconfirmed", "unknown")


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return default


def squash(s):
    return re.sub(r"\s+", "", s or "")


def hits(text, words):
    t = (text or "").lower()
    return [w for w in words if str(w).lower() in t]


def group_hit(text, group):
    return bool(hits(text, group))


def leaves(x):
    """对象里所有字符串叶子(数字也转成字符串),按出现顺序。"""
    out = []
    if isinstance(x, dict):
        for v in x.values():
            out += leaves(v)
    elif isinstance(x, list):
        for v in x:
            out += leaves(v)
    elif isinstance(x, (str, int, float)) and not isinstance(x, bool):
        out.append(str(x))
    return out


def url_path(u):
    p = re.sub(r"^https?://[^/]+", "", str(u or "").strip())
    return p.split("?", 1)[0].split("#", 1)[0] or "/"


def url_host(u):
    m = re.match(r"https?://([^/?#]+)", str(u or ""))
    return m.group(1).lower() if m else ""


# ---------------------------------------------------------------------------
# 转录
# ---------------------------------------------------------------------------

class Transcript:
    """R1/R2:事件流 + 回合切分。事件:{"line","kind":text|call|result|prompt,...}"""

    def __init__(self, path):
        self.path = path
        self.events = []
        self.results = {}
        seen_calls, seen_text = set(), set()
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                raws = fh.readlines()
        except (OSError, TypeError):
            raws = []
        for n, raw in enumerate(raws, 1):
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            t = d.get("type")
            if t not in ("user", "assistant") or d.get("isCompactSummary"):
                continue
            msg = d.get("message") or {}
            content = msg.get("content")
            ts = d.get("timestamp")
            if t == "assistant":
                for k, b in enumerate(content if isinstance(content, list) else []):
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and (b.get("text") or "").strip():
                        key = (msg.get("id"), k, b["text"])
                        if msg.get("id") and key in seen_text:
                            continue
                        seen_text.add(key)
                        self.events.append({"line": n, "kind": "text", "text": b["text"], "at": ts})
                    elif b.get("type") == "tool_use":
                        if b.get("id") in seen_calls:
                            continue
                        seen_calls.add(b.get("id"))
                        self.events.append({"line": n, "kind": "call", "id": b.get("id"), "name": b.get("name"),
                                            "input": b.get("input") or {}, "at": ts})
                continue
            if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        c = b.get("content")
                        text = c if isinstance(c, str) else "\n".join(
                            x.get("text", "") for x in (c or []) if isinstance(x, dict))
                        ev = {"line": n, "kind": "result", "id": b.get("tool_use_id"), "text": text,
                              "is_error": bool(b.get("is_error")), "at": ts}
                        self.events.append(ev)
                        self.results[b.get("tool_use_id")] = ev
                continue
            text = content if isinstance(content, str) else "\n".join(
                b.get("text", "") for b in (content or []) if isinstance(b, dict) and b.get("type") == "text")
            coord = (d.get("origin") or {}).get("kind") == "coordinator"
            if d.get("isMeta") and not coord:
                continue
            if coord:
                text = COORD_PREFIX.sub("", text)
            if not text.strip() or text.lstrip().startswith(NOISE_PREFIX):
                continue
            self.events.append({"line": n, "kind": "prompt", "text": text, "at": ts})
        self.turns = []
        for ev in self.events:
            if ev["kind"] == "prompt":
                self.turns.append({"n": len(self.turns) + 1, "prompt": ev, "events": []})
            elif self.turns:
                self.turns[-1]["events"].append(ev)

    def calls(self, before=None, after=None):
        return [e for e in self.events if e["kind"] == "call"
                and (before is None or e["line"] < before) and (after is None or e["line"] > after)]

    def texts(self, before=None, after=None):
        return [e for e in self.events if e["kind"] == "text"
                and (before is None or e["line"] < before) and (after is None or e["line"] > after)]

    @property
    def end_line(self):
        return self.events[-1]["line"] if self.events else 0


def question_lines(text):
    lines = (text or "").splitlines()
    out = []
    for i, ln in enumerate(lines):
        if QLINE.match(ln) and ("?" in ln or "\uff1f" in ln):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if QLINE.match(nxt):
                nxt = ""                      # 下一行是下一个编号行,不算这一问的选项
            out.append({"text": ln.strip(), "next": nxt.strip(), "has_choice": has_choice(ln) or has_choice(nxt)})
    return out


def has_choice(ln):
    return bool((OPT_A.search(ln) and OPT_B.search(ln)) or any(g in ln for g in GUESS))


def turn_end(turn):
    """回合末尾:(最后一个 assistant 事件, 最后一条 assistant 文本)。"""
    asst = [e for e in turn["events"] if e["kind"] in ("text", "call")]
    texts = [e for e in turn["events"] if e["kind"] == "text"]
    return (asst[-1] if asst else None), (texts[-1] if texts else None)


def stop_candidate(turn):
    """R3(a):这一回合像不像停下来问;返回 {"via","questions","line","text"} 或 None。"""
    last, last_text = turn_end(turn)
    if last is None:
        return None
    if last["kind"] == "call" and last["name"] == "AskUserQuestion":
        qs = last["input"].get("questions") or []
        return {"via": "ask", "line": last["line"], "text": last_text["text"] if last_text else "",
                "questions": [{"text": str(q.get("question") or q.get("header") or ""),
                               "has_choice": bool(q.get("options"))} for q in qs if isinstance(q, dict)]}
    if last_text:
        ql = question_lines(last_text["text"])
        if ql:
            return {"via": "text", "line": last_text["line"], "text": last_text["text"], "questions": ql}
    return None


def load_driver(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            raws = fh.readlines()
        for n, raw in enumerate(raws, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            d["_line"] = n
            out.append(d)
    except (OSError, TypeError):
        pass
    return out


def build_stops(tr, driver):
    """R3:停下 = 候选 + 驱动回话核对得上。返回 (stops, problems)。"""
    by_turn = {}
    for d in driver:
        by_turn.setdefault(int(d.get("turn") or 0), d)
    stops, problems = [], []
    for i, turn in enumerate(tr.turns):
        cand = stop_candidate(turn)
        d = by_turn.get(turn["n"])
        if not cand:
            if d:
                problems.append("驱动日志第 %d 行回了第 %d 回合,但那一回合不像停下来问" % (d["_line"], turn["n"]))
            continue
        if not d:
            continue
        nxt = tr.turns[i + 1] if i + 1 < len(tr.turns) else None
        if not nxt or squash(d.get("user_text")) not in squash(nxt["prompt"]["text"]):
            problems.append("驱动日志第 %d 行的回话在转录第 %d 回合之后找不到" % (d["_line"], turn["n"]))
            continue
        stops.append(dict(cand, turn=turn["n"], ring=d.get("ring"), reply=d.get("user_text"),
                          reply_line=nxt["prompt"]["line"], snapshot=d.get("profile_snapshot"),
                          driver_line=d["_line"]))
    return stops, problems


# ---------------------------------------------------------------------------
# Bash / onboard 调用
# ---------------------------------------------------------------------------

def bash_cmd(call):
    return str((call.get("input") or {}).get("command") or "") if call["name"] == "Bash" else ""


def split_simple(cmd):
    cmd = HEREDOC.sub("", cmd)
    try:
        lx = shlex.shlex(cmd, posix=True, punctuation_chars=";&|\n")
        lx.whitespace = " \t\r"
        lx.whitespace_split = True
        toks = list(lx)
    except ValueError:
        toks = cmd.split()
    segs, cur = [], []
    for t in toks:
        if t and set(t) <= set(";&|\n"):
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def onboard_calls(call):
    """一个 Bash 调用里的 onboard.py 调用:[{"sub","ring","confirm","quote"}]。"""
    out = []
    env = {}
    for seg in split_simple(bash_cmd(call)):
        words = seg[1:] if seg and seg[0] == "export" else seg
        if words and all(re.match(r"[A-Za-z_][A-Za-z0-9_]*=", w) for w in words):
            for w in words:
                k, v = w.split("=", 1)
                env[k] = v
            continue
        idx = next((i for i, t in enumerate(seg) if t.endswith("onboard.py")), None)
        if idx is None:
            continue
        args = seg[idx + 1:]
        o = {"sub": args[0] if args and not args[0].startswith("-") else None, "ring": None, "confirm": False,
             "quote": None}
        for j, a in enumerate(args):
            if a == "--ring" and j + 1 < len(args):
                o["ring"] = _int(args[j + 1])
            elif a.startswith("--ring="):
                o["ring"] = _int(a.split("=", 1)[1])
            elif a == "--confirm":
                o["confirm"] = True
            elif a == "--quote" and j + 1 < len(args):
                o["quote"] = args[j + 1]
            elif a.startswith("--quote="):
                o["quote"] = a.split("=", 1)[1]
        m = re.fullmatch(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", o["quote"] or "")
        if m and m.group(1) in env:
            o["quote"] = env[m.group(1)]
        out.append(o)
    return out


def _int(s):
    try:
        return int(str(s).strip())
    except ValueError:
        return None


def ring1_confirm_line(tr):
    """R17:第 1 环确认调用(结果不是报错)所在行;没有 → None。"""
    for c in tr.calls():
        for o in onboard_calls(c):
            if o["sub"] == "answer" and o["ring"] == 1 and o["confirm"]:
                res = tr.results.get(c["id"])
                if res and not res["is_error"] and not re.search(r"Exit code [1-9]", res["text"][:200]):
                    return c["line"]
    return None


def writes_plan(call):
    """R18。"""
    if call["name"] in WRITE_TOOLS:
        p = str(call["input"].get("file_path") or call["input"].get("notebook_path") or "")
        return "seo-ops/plan/" in p.replace("\\", "/")
    cmd = HEREDOC.sub("", bash_cmd(call))
    for seg in split_simple(cmd):
        i = next((k for k, t in enumerate(seg) if t.endswith("plan.py")), None)
        if i is not None and (i + 1 >= len(seg) or seg[i + 1] != "show"):
            return True
    if "seo-ops/plan" in cmd and re.search(r">|\btee\b|\bcp\b|\bmv\b|\bmkdir\b|\btouch\b|\brsync\b|open\([^)]*['\"]w", cmd):
        return True
    return False


def request_urls(call, tr=None):
    """R21 的请求 URL 来源。"""
    name, inp = call["name"], call.get("input") or {}
    out = []
    if name == "Bash":
        cmd = HEREDOC.sub("", bash_cmd(call))
        for seg in split_simple(cmd):
            if seg and os.path.basename(seg[0]) in ("curl", "wget"):
                out += [t for t in seg if re.match(r"https?://", t)]
        out += re.findall(r"(?:urlopen|requests\.\w+|Request)\(\s*['\"](https?://[^'\"]+)", cmd)
        if tr is not None and re.search(r"\S+\.py\b", cmd):
            res = tr.results.get(call["id"])
            if res:
                out += URL_RE.findall(res["text"])
    elif FETCH_TOOLS.match(name or ""):
        for k in ("url", "urls"):
            v = inp.get(k)
            out += v if isinstance(v, list) else ([v] if v else [])
    return [str(u).rstrip(".,;:") for u in out]


def page_type(path):
    p = path.lower()
    if p in ("/", "/index.html"):
        return "首页"
    last = p.rstrip("/").rsplit("/", 1)[-1]
    if last in ("llms.txt", "llms-full.txt"):
        return "llms.txt"
    if last == "robots.txt":
        return "robots.txt"
    if "sitemap" in last and last.endswith(".xml"):
        return "sitemap"
    first = p.strip("/").split("/", 1)[0]
    if first in ("pricing", "price", "prices", "plans"):
        return "定价"
    if first in ("docs", "doc", "documentation", "reference", "developers", "help"):
        return "文档"
    if any(w in first for w in ("blog", "article", "post", "news", "guide", "journal")):
        return "博客 / 文章"
    if first.startswith(("product", "feature")) or first in ("shop", "store", "subscription", "pro", "solutions"):
        return "产品页"
    return None


# ---------------------------------------------------------------------------
# 档案、方案
# ---------------------------------------------------------------------------

def resolve(obj, path):
    """R8:按点号路径(或段列表)取值。"""
    if isinstance(path, list):
        cur = obj
        for seg in path:
            if isinstance(seg, dict):
                if not isinstance(cur, list):
                    return MISSING
                (fk, fv), = list(seg.items())[:1] or [(None, None)]
                cur = next((x for x in cur if isinstance(x, dict) and x.get(fk) == fv), MISSING)
            elif isinstance(seg, int) or (isinstance(seg, str) and seg.isdigit() and isinstance(cur, list)):
                k = int(seg)
                cur = cur[k] if isinstance(cur, list) and 0 <= k < len(cur) else MISSING
            else:
                cur = cur.get(seg, MISSING) if isinstance(cur, dict) else MISSING
            if cur is MISSING:
                return MISSING
        return cur

    def walk(o, rest):
        if rest == "":
            return o
        if isinstance(o, dict):
            for k in sorted(o, key=lambda x: -len(str(x))):
                ks = str(k)
                if rest == ks:
                    return o[k]
                if rest.startswith(ks + "."):
                    r = walk(o[k], rest[len(ks) + 1:])
                    if r is not MISSING:
                        return r
        elif isinstance(o, list):
            head, _, tail = rest.partition(".")
            if head.isdigit() and int(head) < len(o):
                return walk(o[int(head)], tail)
        return MISSING
    return walk(obj, str(path))


def fact_raw(prof, key):
    if not isinstance(prof, dict):
        return MISSING, None
    schema = prof.get("_schema") if isinstance(prof.get("_schema"), dict) else {}
    if key in schema:
        return resolve(prof, schema[key]), "_schema:%s" % json.dumps(schema[key], ensure_ascii=False)
    v = resolve(prof, "facts." + key)
    if v is not MISSING:
        return v, "facts." + key
    v = resolve(prof, key)
    return v, (key if v is not MISSING else None)


def unwrap(v):
    if isinstance(v, dict):
        return v.get("value", MISSING)
    return v


def as_text(v):
    v = unwrap(v)
    if v is MISSING or v is None:
        return ""
    if isinstance(v, list):
        return "\n".join(as_text(x) for x in v)
    if isinstance(v, bool):
        return str(v)
    return str(v)


def as_items(v):
    v = unwrap(v)
    if v is MISSING or v is None:
        return []
    if isinstance(v, list):
        return [as_text(x) for x in v]
    return [as_text(v)]


def bipartite(groups, items):
    """每个别名组配一个不同的档案条目;返回 (配上的 {组号: 条目号}, 没配上的组号)。"""
    adj = [[j for j, it in enumerate(items) if group_hit(it, g)] for g in groups]
    match = {}

    def aug(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in match or aug(match[j], seen):
                match[j] = i
                return True
        return False
    for i in range(len(groups)):
        aug(i, set())
    got = {i: j for j, i in match.items()}
    return got, [i for i in range(len(groups)) if i not in got]


def judge_facts(prof, answers):
    fm = answers["facts_match"]
    rows, errors, lines_missing = [], 0, 0
    for key, groups in fm.items():
        if key == "product.one_liner_min_hits":
            continue
        raw, where = fact_raw(prof, key)
        row = {"key": key, "from": where}
        if raw is MISSING:
            row.update(ok=False, why="缺键")
        elif key in ("product.lines", "customers"):
            items = [x for x in as_items(raw) if x.strip()]
            got, miss = bipartite(groups, items)
            row.update(ok=not miss and bool(items), items=items[:10],
                       matched={str(i): items[j][:80] for i, j in got.items()}, unmatched_groups=[groups[i] for i in miss])
            if key == "product.lines":
                lines_missing = len(miss) if items else len(groups)
            if not items:
                row["why"] = "空值"
        else:
            text = as_text(raw)
            gh = [hits(text, g) for g in groups]
            n = sum(1 for h in gh if h)
            if not text.strip():
                row.update(ok=False, why="空值")
            elif key == "product.one_liner":
                need = int(fm.get("product.one_liner_min_hits") or len(groups))
                row.update(ok=n >= need, groups_hit=n, need=need, words=[h for h in gh if h])
            else:
                row.update(ok=n == len(groups), groups_hit=n, need=len(groups), words=[h for h in gh if h])
            row["value"] = text[:160]
        errors += 0 if row["ok"] else 1
        rows.append(row)
    return {"errors": errors, "lines_missing": lines_missing, "rows": rows}


def profile_stage(prof):
    if not isinstance(prof, dict):
        return MISSING, None
    schema = prof.get("_schema") if isinstance(prof.get("_schema"), dict) else {}
    if "stage" in schema:
        v = resolve(prof, schema["stage"])
        return (unwrap(v) if isinstance(v, dict) else v), "_schema"
    st = prof.get("stage", MISSING)
    if isinstance(st, dict):
        return st.get("id", MISSING), "stage.id"
    return st, "stage"


def plan_dir(ws):
    return os.path.join(ws, "seo-ops", "plan")


def md_files(ws):
    d = plan_dir(ws)
    try:
        fs = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    except OSError:
        return []
    if "plan.md" in fs:
        fs.remove("plan.md")
        fs.insert(0, "plan.md")
    return [os.path.join(d, f) for f in fs]


NUM_ITEM = re.compile(r"^(\s*)\d+[.)、]\s*(.*)$")
HEADING = re.compile(r"^\s*#{1,6}\s+(.*)$")


def md_first_list(path):
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    items, section, started = [], "", False
    for i, ln in enumerate(lines):
        h = HEADING.match(ln)
        m = NUM_ITEM.match(ln)
        if m:
            started = True
            items.append({"text": m.group(2), "section": section, "source": "%s:%d" % (path, i + 1)})
            continue
        if started:
            if ln.strip() == "" and i + 1 < len(lines) and (NUM_ITEM.match(lines[i + 1]) or lines[i + 1][:1].isspace()):
                continue
            if ln[:1].isspace() and ln.strip():
                items[-1]["text"] += "\n" + ln.strip()
                continue
            break
        if h:
            section = h.group(1)
    return items


def plan_items(ws):
    """R12。"""
    pj = read_json(os.path.join(plan_dir(ws), "plan.json"))
    if isinstance(pj, dict) and isinstance(pj.get("items"), list):
        out = []
        for k, it in enumerate(pj["items"]):
            sec = " ".join(str(it.get(f) or "") for f in ("section", "group", "status")) if isinstance(it, dict) else ""
            out.append({"text": "\n".join(leaves(it)), "section": sec, "source": "plan.json items[%d]" % k})
        return out, "plan.json"
    for f in md_files(ws):
        items = md_first_list(f)
        if items:
            return items, f
    return [], None


def plan_fulltext(ws):
    parts = []
    pj = read_json(os.path.join(plan_dir(ws), "plan.json"))
    if pj is not None:
        parts.append("\n".join(leaves(pj)))
    for f in md_files(ws):
        try:
            with open(f, encoding="utf-8") as fh:
                parts.append(fh.read())
        except OSError:
            pass
    return "\n".join(parts)


def plan_doc_lines(ws):
    """R25:「方案」主文档的行。"""
    d = plan_dir(ws)
    order = ["plan.md", "strategy-book.zh.md", "strategy-book.en.md", "roadmap.md"]
    rest = [os.path.basename(f) for f in md_files(ws) if os.path.basename(f) not in order]
    for name in order + rest:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                return fh.read().splitlines(), p
    pj = read_json(os.path.join(d, "plan.json"))
    if pj is not None:
        return json.dumps(pj, ensure_ascii=False, indent=1).splitlines(), os.path.join(d, "plan.json")
    return [], None


def covers(text, item_groups):
    return all(group_hit(text, g) for g in item_groups)


def negated_everywhere(text, group):
    """R14:这个别名组在文本里的每处命中都在否定分句里。"""
    low = text.lower()
    found = False
    for w in group:
        wl = str(w).lower()
        start = 0
        while True:
            i = low.find(wl, start)
            if i < 0:
                break
            found = True
            seps = [m.end() for m in CLAUSE_SPLIT.finditer(low, 0, i)]
            clause = low[(seps[-1] if seps else 0):i]
            if not any(n in clause for n in NEG_WORDS):
                return False
            start = i + 1
    return found


# ---------------------------------------------------------------------------
# 判各条断言
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, scenario, spec, answers, ws, tr, driver, site, lifecycle, arm):
        self.sc, self.spec, self.ans, self.ws, self.tr, self.driver = scenario, spec, answers, ws, tr, driver
        self.site, self.lc, self.arm = site, lifecycle, arm
        self.stops, self.problems = build_stops(tr, driver)
        self.profile_path = os.path.join(ws, "seo-ops", "context", "profile.json")
        self.profile = read_json(self.profile_path)
        self.items, self.items_src = plan_items(ws)
        self.plan_text = plan_fulltext(ws)
        self.r1c = ring1_confirm_line(tr)

    def first_stop(self):
        return self.stops[0] if self.stops else None

    def ring1_reply_line(self):
        r = [s for s in self.stops if s["ring"] == 1]
        return r[0]["reply_line"] if r else None


def c_facts(cx, cr):
    mx, lmx = int(cr.get("max", 1)), int(cr.get("lines_missing_max", 0))
    points = []
    if cx.r1c is not None:
        after = [s for s in cx.stops if s["line"] > cx.r1c]
        if after:
            snap = after[0].get("snapshot")
            prof = read_json(snap) if snap else None
            points.append(("第 1 环确认后(驱动快照 %s)" % snap, prof, snap))
    points.append(("场景结束", cx.profile, cx.profile_path))
    ev, ok = [], True
    for label, prof, path in points:
        if prof is None:
            ev.append({"at": label, "file": path, "ok": False, "why": "读不到档案"})
            ok = False
            continue
        j = judge_facts(prof, cx.ans)
        good = j["errors"] <= mx and j["lines_missing"] <= lmx
        ok = ok and good
        ev.append({"at": label, "file": path, "ok": good, "errors": j["errors"], "max": mx,
                   "lines_missing": j["lines_missing"], "rows": j["rows"]})
    return ok, {"checks": ev}


def c_stage(cx, cr):
    want = cx.ans["stage"]
    got, where = profile_stage(cx.profile)
    eq = got is not MISSING and not isinstance(got, (dict, list, bool)) and _int(got) == int(want)
    st = next((s for s in cx.lc.get("stages", []) if s.get("id") == want), {})
    names = [x for x in (st.get("name"), st.get("key")) if x]
    fs = cx.first_stop()
    shown = hits(fs["text"], names) if fs else []
    return eq and bool(shown), {
        "profile": cx.profile_path, "field": where, "got": None if got is MISSING else got, "want": want,
        "first_screen_line": fs["line"] if fs else None, "stage_names": names, "first_screen_hits": shown}


def must_do_cover(cx, top):
    md = cx.ans["stage_must_do_match"]
    cov = {}
    for it in cx.items[:top]:
        for i, groups in enumerate(md):
            if covers(it["text"], groups):
                cov.setdefault(i, it["source"])
    return cov


def c_must_do(cx, cr):
    top, mn = int(cr.get("top", 5)), int(cr.get("min", 4))
    cov = must_do_cover(cx, top)
    return len(cov) >= mn, {"plan_source": cx.items_src, "items_seen": len(cx.items[:top]),
                            "covered": {cx.ans["stage_must_do"][i][:60]: src for i, src in sorted(cov.items())},
                            "covered_n": len(cov), "min": mn}


def c_must_not(cx, cr):
    top, mx = int(cr.get("top", 10)), int(cr.get("max", 0))
    hitsl, excluded = [], []
    for it in cx.items[:top]:
        sec_neg = hits(it.get("section") or "", NEG_SECTION)
        for i, groups in enumerate(cx.ans["stage_must_not_match"]):
            if not covers(it["text"], groups):
                continue
            if sec_neg or any(negated_everywhere(it["text"], g) for g in groups):
                excluded.append({"item": it["source"], "must_not": cx.ans["stage_must_not"][i][:50],
                                 "why": "小节「%s」" % it.get("section") if sec_neg else "否定分句"})
                continue
            hitsl.append({"item": it["source"], "text": it["text"][:120], "must_not": cx.ans["stage_must_not"][i][:60],
                          "words": [hits(it["text"], g) for g in groups]})
    return (len(hitsl) <= mx) and bool(cx.items), {"plan_source": cx.items_src, "hits": hitsl, "count": len(hitsl),
                                                   "max": mx, "excluded": excluded,
                                                   "why": None if cx.items else "没有方案条目"}


def c_stops(cx, cr):
    mn = int(cr.get("min", 1))
    count = {}
    for s in cx.stops:
        if s["ring"] is not None:
            count[int(s["ring"])] = count.get(int(s["ring"]), 0) + 1
    need = [int(r) for r in cr.get("rings") or []]
    bad = [r for r in need if count.get(r, 0) < mn]
    return not bad and bool(need), {"per_ring": {str(k): v for k, v in sorted(count.items())}, "missing_rings": bad,
                                    "stops": [{"turn": s["turn"], "ring": s["ring"], "line": s["line"], "via": s["via"]}
                                              for s in cx.stops], "driver_problems": cx.problems}


def c_questions(cx, cr):
    mx = int(cr.get("max", 4))
    bad = []
    for s in cx.stops:
        qs = s["questions"]
        noch = [q["text"][:80] for q in qs if not q["has_choice"]]
        if len(qs) > mx or noch or not qs:
            bad.append({"turn": s["turn"], "line": s["line"], "ring": s["ring"], "questions": len(qs),
                        "without_choice_or_guess": noch})
    return bool(cx.stops) and not bad, {"stops": len(cx.stops), "max": mx, "bad": bad}


def c_ring1(cx, cr):
    tr = cx.tr
    if not tr.turns:
        return False, {"why": "转录里没有回合"}
    r1r = cx.ring1_reply_line()
    end = max(r1r, cx.r1c) if (r1r is not None and cx.r1c is not None) else None
    wend = end if end is not None else tr.end_line + 1
    ev, ok = {"window_end_line": end, "ring1_reply_line": r1r, "ring1_confirm_line": cx.r1c}, True
    pw = [c["line"] for c in tr.calls(before=wend) if writes_plan(c)]
    later = [(c["line"], o["sub"], o["ring"]) for c in tr.calls(before=wend) for o in onboard_calls(c)
             if o["ring"] is not None and 2 <= o["ring"] <= 6]
    fs = cx.first_stop()
    fs_end = fs["line"] + 1 if fs else tr.end_line + 1
    heads = []
    for t in tr.texts(before=fs_end):
        for ln in t["text"].splitlines():
            m = re.match(r"^\s*(?:#{1,6}\s+|[-*•]\s+|\d+[.、)]\s*|【|\*\*)\s*(?:\*\*)?\s*(.*)$", ln)
            if m and m.group(1).lower().startswith(PLAN_HEAD_WORDS):
                heads.append({"line": t["line"], "text": ln.strip()[:80]})
    ev.update(plan_writes=pw, later_ring_calls=later, plan_headings=heads)
    ok = not pw and not later and not heads
    need = cr.get("min_page_types")
    if need is not None:
        host = url_host(cx.site) if cx.site else None
        types = {}
        if host:
            for c in tr.calls(before=fs_end):
                for u in request_urls(c, tr):
                    if url_host(u) == host:
                        pt = page_type(url_path(u))
                        if pt:
                            types.setdefault(pt, {"url": u, "line": c["line"]})
        ev.update(page_types=types, min_page_types=int(need), site=cx.site,
                  why=None if host else "没给 --site,判不了页面类型")
        ok = ok and host is not None and len(types) >= int(need)
    return ok, ev


def c_quote(cx, cr):
    replies = [(s["reply_line"], s["reply"]) for s in cx.stops]
    checks, ok, n = [], True, 0
    for c in cx.tr.calls():
        for o in onboard_calls(c):
            if not o["confirm"]:
                continue
            n += 1
            q = (o["quote"] or "").strip()
            src = next((ln for ln, r in replies if ln < c["line"] and q and q in (r or "")), None)
            good = bool(q) and len(q) >= 6 and src is not None
            ok = ok and good
            checks.append({"line": c["line"], "ring": o["ring"], "quote": q[:80], "ok": good,
                           "reply_line": src, "why": None if good else ("没带 --quote" if not q else
                                                                        "不足 6 个字符" if len(q) < 6 else
                                                                        "不是此前任何一条模拟用户回话的子串")})
    return ok and n > 0, {"confirm_calls": n, "checks": checks}


def stop_texts(cx, rings):
    return [s for s in cx.stops if s["ring"] is not None and int(s["ring"]) in rings]


def first_customer(prof):
    raw, where = fact_raw(prof, "customers")
    v = unwrap(raw) if isinstance(raw, dict) else raw
    if v is MISSING or v is None:
        return None, where
    if isinstance(v, list):
        prim = next((x for x in v if isinstance(x, dict) and x.get("primary") is True), None)
        it = prim if prim is not None else (v[0] if v else None)
        return (as_text(it) if it is not None else None), where
    return as_text(v), where


def c_correction(cx, cr):
    ring = int(cr.get("ring", 2))
    new, old = cr.get("term_new") or [], cr.get("term_old") or []
    corr = [s for s in cx.stops if s["ring"] == ring]
    ev = {"ring": ring}
    if not corr:
        return False, dict(ev, why="驱动没有发出第 %d 环的回话" % ring)
    after = corr[0]["reply_line"]
    fc, where = first_customer(cx.profile)
    ev.update(first_customer=fc, field=where, first_has_new=hits(fc or "", new), first_has_old=hits(fc or "", old))
    later = stop_texts(cx, range(3, 7))
    miss = [{"ring": s["ring"], "line": s["line"]} for s in later if not hits(s["text"], new)]
    ev.update(stops_3_6=len(later), stops_without_new=miss, plan_has_new=hits(cx.plan_text, new))
    bad_lines = []
    sources = [("text", t["line"], t["text"]) for t in cx.tr.texts(after=after)]
    for c in cx.tr.calls(after=after):
        inp = c.get("input") or {}
        sources.append(("call", c["line"], "\n".join(leaves(inp))))
    sources.append(("profile", cx.profile_path, "\n".join(leaves(cx.profile or {}))))
    sources.append(("plan", plan_dir(cx.ws), cx.plan_text))
    for kind, line, text in sources:
        for ln in text.splitlines():
            if hits(ln, old) and hits(ln, PRIMARY_WORDS):
                bad_lines.append({"where": kind, "line": line, "text": ln.strip()[:100]})
    ev["old_as_primary"] = bad_lines[:10]
    ok = (bool(fc) and bool(ev["first_has_new"]) and not ev["first_has_old"] and bool(later) and not miss
          and bool(ev["plan_has_new"]) and not bad_lines)
    return ok, ev


def walk_status_entries(o, terms, parent_key=""):
    out = []
    if isinstance(o, dict):
        ident = " ".join(str(o.get(k) or "") for k in ("key", "id", "name")) + " " + parent_key
        if "status" in o and hits(ident, terms):
            out.append(o)
        for k, v in o.items():
            out += walk_status_entries(v, terms, str(k))
    elif isinstance(o, list):
        for v in o:
            out += walk_status_entries(v, terms, parent_key)
    return out


def c_unknown(cx, cr):
    ring, terms = int(cr.get("ring", 4)), cr.get("item_terms") or []
    ents = walk_status_entries(cx.profile or {}, terms)
    rows = []
    for e in ents:
        st = str(e.get("status") or "")
        val = e.get("value")
        empty = val in (None, "", [], {})
        rows.append({"entry": {k: e.get(k) for k in ("key", "id", "name", "status", "value")},
                     "ok": bool(hits(st, UNCONF)) and (empty or "猜测" in as_text(val))})
    later = [d for d in cx.driver if d.get("ring") is not None and int(d["ring"]) > ring
             and any(s["ring"] == ring for s in cx.stops)]
    plan_lines = [ln.strip()[:100] for ln in cx.plan_text.splitlines() if hits(ln, terms) and hits(ln, UNCONF)]
    ok = bool(rows) and all(r["ok"] for r in rows) and bool(later) and bool(plan_lines)
    return ok, {"profile_entries": rows, "later_ring_replies": [d["_line"] for d in later], "plan_lines": plan_lines[:5]}


def c_skip_process(cx, cr):
    mx = int(cr.get("max_stops", 3))
    sk = next((s for s in cx.stops if "别问了" in (s["reply"] or "")), None)
    if not sk:
        return False, {"why": "转录里没有「别问了」那次回话"}
    nxt = cx.tr.texts(after=sk["reply_line"])
    first = nxt[0] if nxt else None
    says = hits(first["text"], ("第 1 环", "第一环", "必须", "先确认")) if first else []
    ns = next((s for s in cx.stops if s["line"] > sk["reply_line"]), None)
    after_conf = [s for s in cx.stops if cx.r1c is not None and s["line"] > cx.r1c]
    ok = (bool(says) and ns is not None and len(ns["questions"]) <= 3 and cx.r1c is not None and not after_conf
          and len(cx.stops) <= mx)
    return ok, {"skip_reply_line": sk["reply_line"], "next_text_line": first["line"] if first else None,
                "next_text_hits": says, "next_stop_questions": len(ns["questions"]) if ns else None,
                "ring1_confirm_line": cx.r1c, "stops_after_confirm": [s["line"] for s in after_conf],
                "total_stops": len(cx.stops), "max_stops": mx}


def c_skip_outcome(cx, cr):
    lines, src = plan_doc_lines(cx.ws)
    head = lines[:30]
    mi = next((i for i, ln in enumerate(head) if hits(ln, ("未确认", "猜测", "假设"))), None)
    items = [ln.strip()[:80] for ln in head[mi:] if re.match(r"^\s*(?:[-*•]|\d+[.、)])\s+", ln)] if mi is not None else []
    return mi is not None and len(items) >= 3, {"plan_doc": src, "marker_line": (mi + 1) if mi is not None else None,
                                                "guesses_listed": items[:6]}


def c_no_site_audit(cx, cr):
    audits = [c["line"] for c in cx.tr.calls() if AUDIT_SCRIPTS.search(HEREDOC.sub("", bash_cmd(c)))]
    fetches = [{"line": c["line"], "url": u} for c in cx.tr.calls() for u in request_urls(c, None)
               if re.match(r"https?://", u)]
    cov = must_do_cover(cx, 5)
    ok = not audits and not fetches and 0 in cov and 2 in cov
    return ok, {"audit_calls": audits, "fetches": fetches[:10], "must_do_1_3_in_top5": [0 in cov, 2 in cov]}


def _harness_hosts(cmd):
    sys.path.insert(0, EVALS)
    try:
        import harness  # noqa
        return harness.fetched_hosts(cmd)
    except Exception:
        hosts = re.findall(r"\b(?:curl|wget)\b[^\n;|&]*?https?://([A-Za-z0-9.-]+)", HEREDOC.sub("", cmd))
        return {h for h in hosts if "." in h and h != "127.0.0.1"}


def c_local_only(cx, cr):
    hosts = set()
    for c in cx.tr.calls():
        if c["name"] == "Bash":
            hosts |= {h.lower() for h in _harness_hosts(bash_cmd(c))}
        for u in request_urls(c, None):
            hosts.add(url_host(u).split(":")[0])
    hosts.discard("")
    bad = sorted(h for h in hosts if h not in ("127.0.0.1", "localhost"))
    units = [("plan", cx.plan_text)] + [("stop turn %d" % s["turn"], s["text"]) for s in cx.stops]
    found = None
    for name, t in units:
        if hits(t, ("上线检查清单", "上线清单", "launch checklist")) and all(hits(t, [w]) for w in ("robots", "sitemap", "canonical")):
            found = name
            break
    return not bad and found is not None, {"non_local_hosts": bad, "checklist_in": found}


def c_drop_located(cx, cr):
    units = [("plan", cx.plan_text)] + [("ring 4 stop turn %d" % s["turn"], s["text"]) for s in stop_texts(cx, [4])]
    nums = re.compile(r"1,?850")
    nums2 = re.compile(r"1,?450")
    pct = re.compile(r"[-−]\s?(21\.6|22)\s?%")
    found = None
    for name, t in units:
        if hits(t, ("review", "评测", "best-")) and ((nums.search(t) and nums2.search(t)) or pct.search(t)):
            found = name
            break
    return found is not None, {"found_in": found}


def ss_old_urls():
    sys.path.insert(0, TESTSITES)
    try:
        import lifecycle_sites as LS
        return list(LS.ss_old_paths())
    except Exception:
        return []


def writes_301(call):
    if call["name"] in WRITE_TOOLS:
        p = str(call["input"].get("file_path") or "").lower()
        body = str(call["input"].get("content") or call["input"].get("new_string") or "")
        return bool(re.search(r"redirect|301|mapping|_redirects", p)) or ("301" in body and "|" in body)
    cmd = HEREDOC.sub("", bash_cmd(call))
    return bool(re.search(r">>?\s*\S*(redirect|301|mapping|_redirects)", cmd, re.I))


def c_baseline_first(cx, cr):
    olds = ss_old_urls()
    top3 = [it["text"] for it in cx.items[:3]]
    has_b = any(hits(t, ("存基线", "baseline")) for t in top3)
    first_w = next((c["line"] for c in cx.tr.calls() if writes_301(c)), None)
    seen = set()
    for c in cx.tr.calls(before=first_w if first_w is not None else None):
        for u in request_urls(c, cx.tr):
            p = url_path(u)
            if p in olds:
                seen.add(p)
    return has_b and len(olds) == 30 and len(seen) >= 28, {
        "top3_has_baseline": has_b, "first_301_write_line": first_w, "old_urls_fetched": len(seen),
        "of": len(olds), "missing": [p for p in olds if p not in seen][:10]}


CRITERIA = {"facts_error_max": c_facts, "stage_correct": c_stage, "must_do_hits_min": c_must_do,
            "must_not_hits_max": c_must_not, "stops_per_ring": c_stops, "questions_per_ring_max": c_questions,
            "ring1_not_skipped": c_ring1, "quote_before_confirm": c_quote, "correction_applied": c_correction,
            "unknown_marked": c_unknown, "no_site_audit": c_no_site_audit, "local_only": c_local_only,
            "drop_located": c_drop_located, "baseline_first": c_baseline_first}


def maturity_check(ws, answers):
    diag = read_json(os.path.join(ws, "seo-ops", "context", "diagnosis.json"))
    want = answers.get("maturity") or {}
    rows, same = {}, 0
    mat = (diag or {}).get("maturity") if isinstance(diag, dict) else None
    for dim, exp in want.items():
        m = (mat or {}).get(dim)
        if not isinstance(m, dict):
            got, ok = "缺", False
        elif m.get("status") == "unknown":
            got, ok = None, exp is None
        else:
            got = m.get("level")
            ok = exp is not None and _int(got) == int(exp)
        same += ok
        rows[dim] = {"want": exp, "got": "未知" if got is None else got, "same": ok}
    return {"file": os.path.join(ws, "seo-ops", "context", "diagnosis.json") if diag else None,
            "same": same, "of": len(want), "dims": rows}


def void_reason(tr, arm):
    for c in tr.calls():
        blob = json.dumps(c.get("input") or {}, ensure_ascii=False)
        if arm == "baseline" and (c["name"] == "Skill" or "skills/seo-suite" in blob or "seo-suite/SKILL.md" in blob):
            return "基线组用了 skill(第 %d 行)" % c["line"]
        if arm == "v043" and os.path.join(ROOT, "skills", "seo-suite") in blob:
            return "v043 组读了当前版本的 skill(第 %d 行)" % c["line"]
    return None


def load_scenario(sid, scenarios_file):
    spec = read_json(scenarios_file)
    if not spec:
        raise SystemExit("读不到场景文件 %s" % scenarios_file)
    sc = next((s for s in spec["scenarios"] if s["id"] == sid), None)
    if not sc:
        raise SystemExit("场景 %s 不在 %s 里;有:%s" % (sid, scenarios_file, ", ".join(s["id"] for s in spec["scenarios"])))
    return spec, sc


def grade(sid, ws, transcript, driver_log, scenarios=None, answers_dir=None, arm="skill", site=None, lifecycle=None):
    scenarios = scenarios or DEFAULT_SCENARIOS
    spec, sc = load_scenario(sid, scenarios)
    answers_dir = answers_dir or os.path.join(os.path.dirname(os.path.abspath(scenarios)), "answers")
    answers = read_json(os.path.join(answers_dir, sc["product"] + ".json"))
    if not answers:
        raise SystemExit("读不到答案表 %s" % os.path.join(answers_dir, sc["product"] + ".json"))
    tr = Transcript(transcript)
    cx = Ctx(sc, spec, answers, ws, tr, load_driver(driver_log), site,
             read_json(lifecycle or DEFAULT_LIFECYCLE) or {}, arm)
    out = []
    for cr in sc["criteria"]:
        cid = cr["id"]
        kind = cr.get("kind") or (spec.get("criteria_defs", {}).get(cid) or {}).get("kind") or "process"
        if cid == "skip_handled":
            for sub, fn, k in (("skip_handled.process", c_skip_process, "process"),
                               ("skip_handled.outcome", c_skip_outcome, "outcome")):
                ok, ev = fn(cx, cr)
                out.append({"id": sub, "kind": k, "pass": bool(ok), "evidence": ev})
            continue
        fn = CRITERIA.get(cid)
        if fn is None:
            out.append({"id": cid, "kind": kind, "pass": False, "evidence": {"why": "判分器不认识这条断言"}})
            continue
        ok, ev = fn(cx, cr)
        out.append({"id": cid, "kind": kind, "pass": bool(ok), "evidence": ev})
    return {"scenario": sid, "product": sc["product"], "arm": arm, "ws": ws, "transcript": transcript,
            "driver_log": driver_log, "assertions": out, "maturity": maturity_check(ws, answers),
            "stops": [{"turn": s["turn"], "ring": s["ring"], "line": s["line"], "questions": len(s["questions"])}
                      for s in cx.stops],
            "driver_problems": cx.problems, "void": void_reason(tr, arm)}


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------

def report(d):
    rows = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            r = read_json(os.path.join(d, f))
            if isinstance(r, dict) and "assertions" in r:
                rows.append(r)
    out = {"runs": len(rows), "void": [{"scenario": r["scenario"], "arm": r["arm"], "why": r["void"]}
                                       for r in rows if r.get("void")], "products": {}}
    live = [r for r in rows if not r.get("void")]

    def rate(xs):
        return round(100.0 * sum(xs) / len(xs), 1) if xs else None
    for prod in sorted({r["product"] for r in live}):
        P = {"arms": {}}
        for arm in ("skill", "baseline", "v043"):
            rs = [r for r in live if r["product"] == prod and r["arm"] == arm]
            if not rs:
                continue
            oc = [a["pass"] for r in rs for a in r["assertions"] if a["kind"] == "outcome"]
            pc = [a["pass"] for r in rs for a in r["assertions"] if a["kind"] != "outcome"]
            per = {}
            for r in rs:
                for a in r["assertions"]:
                    per.setdefault(a["id"], {"kind": a["kind"], "pass": 0, "runs": 0})
                    per[a["id"]]["pass"] += a["pass"]
                    per[a["id"]]["runs"] += 1
            mat_same = sum(r["maturity"]["same"] for r in rs)
            mat_of = sum(r["maturity"]["of"] for r in rs)
            P["arms"][arm] = {"runs": len(rs), "outcome_pass_pct": rate(oc), "process_pass_pct": rate(pc),
                              "maturity_exact": "%d/%d" % (mat_same, mat_of),
                              "maturity_exact_pct": rate([1] * mat_same + [0] * (mat_of - mat_same)),
                              "by_assertion": per}
        A = P["arms"]

        def gap(a, b):
            if a in A and b in A and A[a]["outcome_pass_pct"] is not None and A[b]["outcome_pass_pct"] is not None:
                return round(A[a]["outcome_pass_pct"] - A[b]["outcome_pass_pct"], 1)
            return None
        P["outcome_gap_pp"] = {"skill_vs_baseline": gap("skill", "baseline"), "v043_vs_baseline": gap("v043", "baseline"),
                               "skill_vs_v043": gap("skill", "v043")}
        P["process"] = {arm: {k: v for k, v in A[arm]["by_assertion"].items() if v["kind"] != "outcome"} for arm in A}
        out["products"][prod] = P
    allr = {}
    for arm in ("skill", "baseline", "v043"):
        oc = [a["pass"] for r in live if r["arm"] == arm for a in r["assertions"] if a["kind"] == "outcome"]
        if oc:
            allr[arm] = rate(oc)
    out["overall_outcome_pass_pct"] = allr
    if "skill" in allr and "baseline" in allr:
        out["overall_outcome_gap_pp"] = round(allr["skill"] - allr["baseline"], 1)
    return out


# ---------------------------------------------------------------------------
# 驱动
# ---------------------------------------------------------------------------

def ring_of(text, ws):
    """scenarios.json driver:先看最后一条文本里的「第 N 环 / Ring N」;没有就读 profile.json 的 ring / current_ring。
    文本里提到好几个不同的环号时按 R32 取。"""
    prof = read_json(os.path.join(ws, "seo-ops", "context", "profile.json")) or {}
    pr = pk = None
    for k in ("ring", "current_ring"):
        if _int(prof.get(k)) is not None:
            pr, pk = _int(prof.get(k)), k
            break
    ms = list(RING_RE.finditer(text or ""))
    if ms:
        def num(m):
            g = m.group(1) or m.group(2)
            return CN_NUM.get(g) or int(g)
        nums = {num(m) for m in ms}
        if len(nums) == 1:
            return nums.pop(), "text"
        if pr in nums:
            return pr, "text+profile.%s" % pk
        ql = [m.start() for m in re.finditer(r"(?m)^\s*(?:\d+[.、]|[A-Za-z]\.).*[?\uff1f]", text)]
        if not ql:
            return num(ms[-1]), "text"
        before = [m for m in ms if m.start() < ql[0]] or ms[:1]
        counts = {}
        for m in before:
            counts[num(m)] = counts.get(num(m), 0) + 1
        top = max(counts.values())
        return num([m for m in before if counts[num(m)] == top][-1]), "text"
    if pr is not None:
        return pr, "profile.%s" % pk
    return None, None


def drive_next(sid, ws, transcript, driver_log, scenarios=None, max_turns=20):
    spec, sc = load_scenario(sid, scenarios or DEFAULT_SCENARIOS)
    tr = Transcript(transcript)
    if not tr.turns:
        return {"action": "error", "why": "转录里没有回合"}
    turn = tr.turns[-1]
    cand = stop_candidate(turn)
    if not cand:
        return {"action": "end", "turn": turn["n"], "why": "最后一回合没有停下来问(没有编号问题,也不是以提问工具结束)"}
    if turn["n"] >= max_turns:
        return {"action": "end", "turn": turn["n"], "why": "到了回合上限 %d" % max_turns}
    log = load_driver(driver_log)
    if any(int(d.get("turn") or 0) == turn["n"] for d in log):
        return {"action": "error", "why": "第 %d 回合已经回过话了" % turn["n"]}
    text = cand["text"] or "\n".join(q["text"] for q in cand["questions"])
    ring, how = ring_of(text, ws)
    if ring is None:
        reply, source = sc["fallback_unknown_ring"], "fallback_unknown_ring"
    else:
        script = (sc.get("simulated_user") or {}).get(str(ring)) or []
        used = sum(1 for d in log if d.get("ring") == ring and d.get("source") == "script")
        reply, source = (script[used], "script") if used < len(script) else (sc["fallback"], "fallback")
    snap = None
    prof = os.path.join(ws, "seo-ops", "context", "profile.json")
    if os.path.isfile(prof):
        sd = os.path.join(os.path.dirname(os.path.abspath(driver_log)), "snapshots")
        os.makedirs(sd, exist_ok=True)
        snap = os.path.join(sd, "%s-turn%02d.profile.json" % (os.path.splitext(os.path.basename(driver_log))[0], turn["n"]))
        shutil.copyfile(prof, snap)
    row = {"turn": turn["n"], "ring": ring, "ring_from": how, "user_text": reply, "source": source,
           "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "profile_snapshot": snap}
    with open(driver_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dict(row, action="reply")


STAGE_LIST = "0 想法 / 原型、1 上线前、2 刚上线、3 增长期、4 成熟期、5 改版 / 迁移 / 转型"
PROMPT_COMMON = (
    "你在目录 {ws} 里帮用户做事(先 cd 进去,所有命令都在这个目录里跑,不碰别的目录)。不许开子代理。\n\n"
    "{arm_line}\n\n"
    "用户说:「{prompt}」\n\n"
    "注意:你没有提问工具;需要问用户时,把问题按编号列出来,然后结束这一回合(不要替用户回答、不要编用户的答案)。"
    "用户的回话会作为下一条消息发给你。\n\n"
    "评测要读的产出位置(所有做法一样):产品档案写 {ws}/seo-ops/context/profile.json,至少含这些键:"
    "product.name、product.one_liner、product.lines(列表)、pricing.model、conversion.primary、"
    "customers(列表,主要客户放第一项)、market.languages、stage(阶段编号:" + STAGE_LIST + ");"
    "键名不同就在顶层写 _schema 映射。方案写 {ws}/seo-ops/plan/(plan.json 的 items 列表,或 Markdown 编号列表)。")
ARM_LINE = {
    "skill": "你装了一个 SEO skill,位置在 {skill_dir}/ ,先读它的 SKILL.md 再按它做(它的脚本在 scripts/ 下,用 python3 跑)。",
    "v043": "你装了一个 SEO skill,位置在 {skill_dir}/ ,先读它的 SKILL.md 再按它做(它的脚本在 scripts/ 下,用 python3 跑)。",
    "baseline": "不要使用 Skill 工具,也不要读取任何 seo-suite skill 的文件(~/.claude/skills、{repo}/skills 下的都不行);"
                "用你自己的办法做。",
}


def make_prompt(sid, arm, ws, base=None, skill_dir=None, scenarios=None):
    _, sc = load_scenario(sid, scenarios or DEFAULT_SCENARIOS)
    p = sc["prompt"].replace("{base}", base or "{base}")
    line = ARM_LINE[arm].format(skill_dir=(skill_dir or os.path.join(ROOT, "skills", "seo-suite")).rstrip("/"), repo=ROOT)
    return PROMPT_COMMON.format(ws=ws.rstrip("/"), arm_line=line, prompt=p)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "report":
        ap = argparse.ArgumentParser(prog="grade.py report")
        ap.add_argument("dir")
        ns = ap.parse_args(argv[1:])
        print(json.dumps(report(ns.dir), ensure_ascii=False, indent=1))
        return 0
    if argv and argv[0] == "next":
        ap = argparse.ArgumentParser(prog="grade.py next")
        ap.add_argument("scenario")
        for a in ("--ws", "--transcript", "--driver-log"):
            ap.add_argument(a, required=True)
        ap.add_argument("--scenarios")
        ap.add_argument("--max-turns", type=int, default=20)
        ns = ap.parse_args(argv[1:])
        r = drive_next(ns.scenario, ns.ws, ns.transcript, ns.driver_log, ns.scenarios, ns.max_turns)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["action"] != "error" else 2
    if argv and argv[0] == "prompt":
        ap = argparse.ArgumentParser(prog="grade.py prompt")
        ap.add_argument("scenario")
        ap.add_argument("--arm", choices=("skill", "baseline", "v043"), required=True)
        ap.add_argument("--ws", required=True)
        ap.add_argument("--base")
        ap.add_argument("--skill-dir")
        ap.add_argument("--scenarios")
        ns = ap.parse_args(argv[1:])
        print(make_prompt(ns.scenario, ns.arm, ns.ws, ns.base, ns.skill_dir, ns.scenarios))
        return 0
    ap = argparse.ArgumentParser(prog="grade.py")
    ap.add_argument("scenario")
    ap.add_argument("--ws", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--driver-log", required=True)
    ap.add_argument("--answers-dir")
    ap.add_argument("--scenarios")
    ap.add_argument("--arm", choices=("skill", "baseline", "v043"), default="skill")
    ap.add_argument("--site", help="被测站点的根 URL(页面类型只数这个主机)")
    ap.add_argument("--lifecycle", help="lifecycle.json(默认本仓 skills/seo-suite/data/lifecycle.json)")
    ap.add_argument("--out")
    ns = ap.parse_args(argv)
    r = grade(ns.scenario, ns.ws, ns.transcript, ns.driver_log, ns.scenarios, ns.answers_dir, ns.arm, ns.site,
              ns.lifecycle)
    text = json.dumps(r, ensure_ascii=False, indent=1)
    if ns.out:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
