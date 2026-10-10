#!/usr/bin/env python3
"""AI 可见性采样面板管理器(人工采样协议的工程化)。stdlib-only。

五状态分类(unifapi 口径;采集失败 ≠ 内容缺口):
  no_answer          引擎没给答案 → 留在覆盖分母,计 zero-presence
  failed             采集失败       → 不入任何分母
  brand_absent       有答案但品牌未出现(文本别名与引用域名均无)
  name_only_mention  品牌名/别名出现在正文,但引用来源无品牌域名(mentioned≠cited)
  cited_brand        品牌域名出现在引用来源

指标口径:
  mention coverage = Σmentioned / 成功 cell 数(成功 = 非 failed;no_answer 计 0 留分母)
  citation share   = 品牌被引 answer 数 / Σ(每 answer 去重后的引用域名数)
                     每答案每品牌至多计 1 次 → 各品牌 share 恒和 100%;空分母 N/A
  跨期比较         = 配对分母:只比两期均成功(非 failed)的 cell
  稳定性           = 单次引用检查 = 掷硬币;同一 prompt ≥3 次采样才报
                     Wilson 95% CI(z=1.96,w=√(p(1-p)/n),CI=p±z·w;区间跨 0.5 → unstable)
  prompts < 10     = 样本太小,结论只能当方向

子命令:
  init    --brand X (--prompts p.csv | --prompts-file prompt-bank.md)
          [--aliases a,b] [--domain example.com] [--engines e1,e2]
          [--competitors a.com,b.com]      # SoV 分母的追踪竞品域
          [--stage-mix]                    # 打印 5 awareness+3 consideration+2 decision 建议配方
          [--persona-fanout "core query" --personas CMO,Founder]
          [--panel PATH] [--force]
  record  --engine chatgpt --file run.csv [--run-id ID] [--date ISO] [--panel PATH]
  report  [--engine E] [--panel PATH]      # 含指标族节: SoV/win_rate/citation_rate/
                                           #   brand_visibility vs source_visibility(Peec 官方公式)
  diff    RUN1 RUN2 [--panel PATH]         # RUN 为 run 文件路径或面板内 run_id
                                           # 新增 signals 节(Scrunch 口径): |Δ|≥5pp 且配对 n≥10
                                           #   才报;fingerprint=sha1(metric+engine+topic)[:10];
                                           #   disappeared 按对 delta 的贡献排序
  decay   [--metric cited|mentioned] [--engine E] [--json] [--panel PATH]
          # citation decay 判定(Profound 官方方法论,2026-09 88.3 万页研究;阈值抄自官方):
          # 7 点滚动均值(官方 14 天,采样密度低取 7)/ 资格闸门 4 道 /
          # 半衰=peak 后平滑≤50%peak 且连续 14 天无反弹 / 状态机 5 态 / 重写队列
  score   (--run RUNID | --last) --scores scores.json [--panel PATH]
          # geo 打分写回(geo-scoring-rubric 五维打分卡,references/content/):
          #   agent 按卡语义打分 → 机检硬规则(硬 cap/枚举/top_pick 佐证/字段白名单/
          #   越界 clamp)→ 写回该 run 每条 result 的 geo 扩展键(panel.json 与
          #   runs/<id>.json 双写);硬违例整批原子拒绝;score --rubric 打印
          #   压缩判定要点(代码内常量,不读 md,standalone)

run.csv 列: prompt, mentioned, cited, cited_urls[, state][, rank]
  mentioned/cited ∈ {0,1};cited_urls 分号分隔;state 可显式给 failed/no_answer
  或三态之一覆盖,否则由 mentioned/cited 推导;cited=1 蕴含 mentioned=1;
  rank 可选(引擎答案中品牌排位,1=第一;有 rank 数据才报 win_rate)。

prompts 对象化: panel.prompts 支持对象 {text, topic, tags[], stage, branded,
  region, lang}(Scrunch stage 框架: awareness/consideration/conversion/loyalty);
  旧字符串形式向后兼容,读取时自动升级为 {text: ...}。

面板文件 panel.json 与 runs/ 目录同层;record 同时写入面板与独立 run 文件。

用法:
  python3 citation_panel.py init --brand Acme --prompts prompts.csv --domain acme.ai
  python3 citation_panel.py init --brand Acme --prompts-file templates/research/prompt-bank.md \
      --stage-mix --persona-fanout "best CRM" --personas CMO,Founder --competitors hub.com
  python3 citation_panel.py record --engine chatgpt --file run1.csv
  python3 citation_panel.py report
  python3 citation_panel.py diff runs/r1.json runs/r2.json
  python3 citation_panel.py decay --engine chatgpt [--json]
  python3 citation_panel.py score --last --scores scores.json
  python3 citation_panel.py --self-test
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import traceback
from collections import Counter
from datetime import datetime, timedelta

DEFAULT_ENGINES = ["chatgpt", "perplexity", "gemini", "copilot", "claude", "grok"]
STATES = ("no_answer", "failed", "brand_absent", "name_only_mention", "cited_brand")
Z = 1.96

# ---------- v2 扩展常数(出处见各节注释) ----------
# prompts 对象化(references/research/borrow-specs.md B3)
PROMPT_FIELDS = ("text", "topic", "tags", "stage", "branded", "region", "lang")
PROMPT_COL_KEYS = ("prompt", "prompts", "query", "text", "提示词", "模板", "整句",
                   "prompt 句", "模板(整句)")          # 命中任一列名 → 该列为 prompt 文本
STAGE_COLS = ("stage", "阶段", "漏斗")                  # prompt-bank.md 主矩阵的漏斗列
STAGE_ALIASES = {"认知": "awareness", "比较": "consideration", "决策": "decision",
                 "转化": "conversion", "忠诚": "loyalty",
                 "awareness": "awareness", "consideration": "consideration",
                 "decision": "decision", "conversion": "conversion", "loyalty": "loyalty"}
# persona 前缀表(Scrunch 官方配方)+ 固定后缀
PERSONA_PREFIXES = {
    "CMO": "As a CMO evaluating this for a 50-person team, ",
    "Founder": "As a bootstrapped founder, ",
    "SEO Lead": "As an SEO lead judging tooling ROI, ",
    "PMM": "As a product marketing manager sizing a launch, ",
}
FANOUT_SUFFIX = " Respond with sources and direct claims first."
# 初始集配方(Scrunch 官方): 5 awareness + 3 consideration + 2 decision
STAGE_MIX_RECIPE = (("awareness", 5), ("consideration", 3), ("decision", 2))
# citation decay(Profound 官方方法论,2026-09 88.3 万页研究;阈值抄自官方)
DECAY_SMOOTH_WINDOW = 7       # 滚动均值点数(官方 14 天,我们采样密度低取 7)
DECAY_MIN_WINDOW_DAYS = 28    # 资格闸门 1: 观察窗≥28 天(官方)
DECAY_PEAK_WINDOW_DAYS = 7    # 峰值窗 = 峰值±7 天
DECAY_MIN_PEAK_SAMPLES = 5    # 资格闸门 2: 峰值窗内采样≥5(官方)
DECAY_NO_REBOUND_DAYS = 14    # 半衰确认: ≤50%peak 后连续 14 天无反弹(官方)
DECAY_LATE_START_DAYS = 30    # 资格闸门 4: 首采距窗起点>30 天剔除(官方)
OFFICIAL_MEDIAN_HALF_LIFE = 11   # 官方常数: 中位半衰期 11 天(参照行/先验)

SL_TLD = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "co.jp", "ne.jp",
          "or.jp", "com.cn", "net.cn", "org.cn", "com.br", "com.mx", "com.tr",
          "co.kr", "co.in", "co.za", "com.sg", "com.hk"}


# ---------- 基础工具 ----------

def registrable_domain(url):
    """从 URL 提取可注册域(近似:last-two-labels,常见二级 TLD 取三位)。"""
    host = (url or "").strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in host:
        host = host.split("@")[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if not parts:
        return ""
    if len(parts) >= 3 and ".".join(parts[-2:]) in SL_TLD:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return parts[0]


def load_panel(path):
    with open(path, encoding="utf-8") as f:
        panel = json.load(f)
    panel.setdefault("runs", [])
    panel.setdefault("aliases", [])
    panel.setdefault("engines", list(DEFAULT_ENGINES))
    return panel


def save_panel(path, panel):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel, f, ensure_ascii=False, indent=2)


def runs_dir_for(panel_path):
    return os.path.join(os.path.dirname(os.path.abspath(panel_path)), "runs")


def _to01(v):
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "是"):
        return 1
    if s in ("0", "false", "no", "n", "否", "", "na", "n/a", "-"):
        return 0
    raise ValueError("mentioned/cited 需要 0/1,得到 %r" % (v,))


# ---------- prompts 对象化(旧字符串向后兼容) ----------

def prompt_obj(p):
    """任意形态 prompt → 规范对象 {text, topic, tags[], stage, branded, region, lang}。
    旧字符串自动升级为 {text: ...}(不回写 panel.json,仅读取时升级)。"""
    if isinstance(p, dict):
        text = str(p.get("text", "")).strip()
        if not text:
            raise ValueError("prompt 对象缺少非空 text 字段: %r" % (p,))
        obj = {"text": text, "tags": []}
        for f in ("topic", "stage", "region", "lang"):
            if p.get(f) not in (None, ""):
                obj[f] = str(p[f]).strip()
        if "stage" in obj:
            obj["stage"] = obj["stage"].lower()
        tags = p.get("tags") or []
        if isinstance(tags, str):
            tags = re.split(r"[;,，、]", tags)
        obj["tags"] = [str(t).strip() for t in tags if str(t).strip()]
        if p.get("branded") is not None:
            obj["branded"] = (p["branded"] if isinstance(p["branded"], bool)
                              else str(p["branded"]).strip().lower() in ("1", "true", "yes", "y", "是"))
        return obj
    return {"text": str(p).strip(), "tags": []}


def prompt_text(p):
    return prompt_obj(p)["text"]


def prompt_texts(panel):
    return [prompt_text(p) for p in panel.get("prompts", [])]



# ---------- init ----------

def read_prompts_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if r and r[0].strip()]
    if not rows:
        return []
    head = rows[0][0].strip().lower()
    body = rows[1:] if head in ("prompt", "prompts", "query", "提示词") else rows
    seen, out = set(), []
    for r in body:
        p = r[0].strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _row_to_prompt(cells, header):
    """表格/CSV 一行 → prompt 对象;header=None 时第一列按 prompt 文本处理。
    列名支持英文与 prompt-bank.md 的中文列(漏斗列自动映射为 stage)。"""
    if header is None:
        text = (cells[0] or "").strip() if cells else ""
        return {"text": text} if text else None
    m = dict(zip(header, cells))
    text = ""
    for k, v in m.items():
        if k in PROMPT_COL_KEYS and v and v.strip():
            text = v.strip()
            break
    if not text and cells:
        text = (cells[0] or "").strip()
    if not text:
        return None
    obj = {"text": text}
    for f in ("topic", "region", "lang"):
        if m.get(f, "").strip():
            obj[f] = m[f].strip()
    stage_raw = ""
    for k, v in m.items():
        if k in STAGE_COLS and v and v.strip():
            stage_raw = v.strip()
            break
    if stage_raw:
        obj["stage"] = STAGE_ALIASES.get(stage_raw, stage_raw.lower())
    if m.get("tags", "").strip():
        obj["tags"] = [t.strip() for t in re.split(r"[;,，、]", m["tags"]) if t.strip()]
    if m.get("branded", "").strip():
        obj["branded"] = m["branded"].strip().lower() in ("1", "true", "yes", "y", "是")
    return obj


def _plain_prompt_text(s):
    """纯文本行 → prompt 文本(剥 -/*/+/1. 列表标记)。"""
    t = re.sub(r"^[-*+]\s+", "", s)
    t = re.sub(r"^\d+[.、)]\s+", "", t)
    return t.strip()


def read_prompts_file(path):
    """templates/research/prompt-bank.md 形态 → prompt 对象列表。
    支持: markdown 表格(列名 prompt/text/stage/topic/tags/branded/region/lang 任意子集,
    分隔行 |---| 跳过)、带表头 CSV(首列为 prompt/text 等)、纯文本一行一条
    (# 标题、<!-- 注释、> 引用行跳过;- / * / 1. 列表标记剥除)。表格与纯文本可混排;
    按 text 去重。"""
    with open(path, encoding="utf-8") as f:
        raw_lines = f.read().splitlines()
    table_rows, plain_lines = [], []
    for line in raw_lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 2:
            cells = [c.strip() for c in s[1:-1].split("|")]
            if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue                       # markdown 分隔行
            table_rows.append(cells)
        elif s and not s.startswith(("#", "<", ">")):
            plain_lines.append(s)
    out = []
    if table_rows:
        header = [c.lower() for c in table_rows[0]]
        mapped = any(h in PROMPT_COL_KEYS or h in PROMPT_FIELDS for h in header if h)
        for cells in table_rows[1:] if mapped else table_rows:
            obj = _row_to_prompt(cells, header if mapped else None)
            if obj:
                out.append(obj)
        out.extend({"text": t} for t in map(_plain_prompt_text, plain_lines) if t)
    elif plain_lines:
        header = [c.strip().lower() for c in next(csv.reader([plain_lines[0]]))]
        if any(h in PROMPT_COL_KEYS for h in header):
            for ln in plain_lines[1:]:
                obj = _row_to_prompt(next(csv.reader([ln])), header)
                if obj:
                    out.append(obj)
        else:
            out.extend({"text": t} for t in map(_plain_prompt_text, plain_lines) if t)
    seen, uniq = set(), []
    for o in out:
        if o["text"] and o["text"] not in seen:
            seen.add(o["text"])
            uniq.append(o)
    return uniq


def persona_fanout(core_query, personas, existing=None):
    """前缀注入变体清单(Scrunch 官方 persona 变换): 前缀+core query+固定后缀。
    core query 命中 existing 中同名 prompt 时继承其 topic/stage 等元数据。"""
    core = core_query.strip()
    base = None
    for e in existing or []:
        if isinstance(e, dict) and prompt_text(e) == core:
            base = e
            break
    out = []
    for persona in personas:
        persona = persona.strip()
        if not persona:
            continue
        prefix = PERSONA_PREFIXES.get(persona)
        if prefix is None:                     # 大小写/写法归一后再试一次
            for k, v in PERSONA_PREFIXES.items():
                if k.lower() == persona.lower():
                    prefix = v
                    break
        if prefix is None:
            prefix = "As a %s, " % persona
        obj = {"text": "%s%s%s" % (prefix, core, FANOUT_SUFFIX),
               "tags": ["persona-fanout", persona]}
        if base:
            for f in ("topic", "stage", "branded", "region", "lang"):
                if base.get(f) is not None:
                    obj[f] = base[f]
        out.append(obj)
    return out


def stage_mix_advice(prompts):
    """--stage-mix: 对照 Scrunch 官方初始集配方打印建议(只打印,不强制)。"""
    counts = Counter()
    untagged = 0
    for p in prompts:
        st = (prompt_obj(p).get("stage") or "").strip()
        if st:
            counts[st] += 1
        else:
            untagged += 1
    L = ["[stage-mix] Scrunch 官方初始集配方: 5 awareness + 3 consideration + 2 decision"
         "(起步 10-20 awareness + 20-30 consideration 跑 30 天)"]
    cur = ", ".join("%s=%d" % (k, counts.get(k, 0))
                    for k in ("awareness", "consideration", "decision", "conversion", "loyalty")
                    if counts.get(k)) or "无 stage 标注"
    L.append("[stage-mix] 当前: %s, 未标注=%d" % (cur, untagged))
    gaps = []
    for k, want in STAGE_MIX_RECIPE:
        if counts.get(k, 0) < want:
            gaps.append("补 %d 条 %s" % (want - counts.get(k, 0), k))
    if untagged:
        gaps.append("为 %d 条未标注 prompt 补 stage(templates/research/prompt-bank.md)" % untagged)
    L.append("[stage-mix] 建议: " + (";".join(gaps) if gaps else "已符合配方"))
    return "\n".join(L)


def cmd_init(args):
    entries = []   # --prompts 产字符串(旧形态);--prompts-file/--persona-fanout 产对象
    if args.prompts:
        csv_prompts = read_prompts_csv(args.prompts)
        if not csv_prompts:
            print("错误: %s 中没有读到 prompt" % args.prompts, file=sys.stderr)
            return 1
        entries.extend(csv_prompts)
    if args.prompts_file:
        file_prompts = read_prompts_file(args.prompts_file)
        if not file_prompts:
            print("错误: %s 中没有读到 prompt(支持 markdown 表格/带表头 CSV/纯文本一行一条)"
                  % args.prompts_file, file=sys.stderr)
            return 1
        entries.extend(file_prompts)
    if args.persona_fanout:
        personas = [p.strip() for p in (args.personas or "").split(",") if p.strip()]
        if not personas:
            print("错误: --persona-fanout 需要配 --personas(如 CMO,Founder)", file=sys.stderr)
            return 1
        fanout = persona_fanout(args.persona_fanout, personas, entries)
        entries.extend(fanout)
        print("[persona-fanout] 生成 %d 条前缀注入变体(固定后缀 %r):"
              % (len(fanout), FANOUT_SUFFIX))
        for i, o in enumerate(fanout, 1):
            print("  %d. %s" % (i, o["text"]))
    seen, prompts = set(), []
    for e in entries:
        t = prompt_text(e)
        if t and t not in seen:
            seen.add(t)
            prompts.append(e)
    if not prompts:
        print("错误: 需要 --prompts 或 --prompts-file(或 --persona-fanout)提供 prompt",
              file=sys.stderr)
        return 1
    if os.path.exists(args.panel) and not args.force:
        print("面板已存在: %s(用 --force 覆盖)" % args.panel, file=sys.stderr)
        return 1
    panel = {
        "brand": args.brand,
        "aliases": [a.strip() for a in (args.aliases or "").split(",") if a.strip()],
        "domain": (args.domain or "").strip().lower(),
        "prompts": prompts,
        "engines": [e.strip() for e in (args.engines or "").split(",") if e.strip()]
        or list(DEFAULT_ENGINES),
        "created": datetime.now().isoformat(timespec="seconds"),
        "runs": [],
    }
    if args.competitors:
        panel["competitors"] = [c.strip().lower() for c in args.competitors.split(",")
                                if c.strip()]
    os.makedirs(runs_dir_for(args.panel), exist_ok=True)
    save_panel(args.panel, panel)
    print("面板已建立: %s(brand=%s, domain=%s, prompts=%d, engines=%s)"
          % (args.panel, args.brand, panel["domain"] or "(未设)", len(prompts),
             ",".join(panel["engines"])))
    if args.stage_mix:
        print(stage_mix_advice(prompts))
    if len(prompts) < 10:
        print("[!] prompts=%d <10:样本太小,结论只能当方向" % len(prompts))
    return 0


# ---------- record ----------

def normalize_result(row, warnings, prompt):
    state = (row.get("state") or "").strip().lower()
    if state in ("failed", "no_answer"):
        return {"state": state, "mentioned": 0, "cited": 0, "cited_urls": []}
    if state in ("brand_absent", "name_only_mention", "cited_brand"):
        m, c = {"brand_absent": (0, 0),
                "name_only_mention": (1, 0),
                "cited_brand": (1, 1)}[state]
    else:
        m = _to01(row.get("mentioned", 0))
        c = _to01(row.get("cited", 0))
        if c and not m:
            warnings.append("cited=1 但 mentioned=0,已按 mentioned=1 处理: %s" % prompt)
            m = 1
        state = "cited_brand" if c else ("name_only_mention" if m else "brand_absent")
    urls = [u.strip() for u in re.split(r"[;,\s]+", row.get("cited_urls") or "") if u.strip()]
    out = {"state": state, "mentioned": m, "cited": c, "cited_urls": urls}
    rank = str(row.get("rank") or "").strip()
    if rank:
        try:
            out["rank"] = int(float(rank))
        except ValueError:
            warnings.append("rank 无法解析为正整数,已忽略: %r(%s)" % (rank, prompt))
    return out


def read_run_csv(path, panel):
    warnings, results = [], {}
    known = {prompt_text(p) for p in panel.get("prompts", [])}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            prompt = (row.get("prompt") or row.get("query") or "").strip()
            if not prompt:
                continue
            results[prompt] = normalize_result(row, warnings, prompt)
            if prompt not in known:
                warnings.append("prompt 不在面板 prompts 列表中: %s" % prompt)
    return results, warnings


def cmd_record(args):
    panel = load_panel(args.panel)
    if args.engine not in panel["engines"]:
        panel["engines"].append(args.engine)
        print("[i] 引擎 %s 不在面板引擎列表,已追加" % args.engine)
    results, warnings = read_run_csv(args.file, panel)
    if not results:
        print("错误: %s 中没有有效行(需 prompt,mentioned,cited,cited_urls 列)" % args.file,
              file=sys.stderr)
        return 1
    date = args.date or datetime.now().isoformat(timespec="seconds")
    run_id = args.run_id or re.sub(r"[^\w.-]+", "-", "%s-%s" % (args.engine, date))
    existing = {r["run_id"] for r in panel["runs"]}
    base, n = run_id, 2
    while run_id in existing:
        run_id = "%s-%d" % (base, n)
        n += 1
    run = {"run_id": run_id, "engine": args.engine, "date": date,
           "brand": panel["brand"], "results": results}
    panel["runs"].append(run)
    save_panel(args.panel, panel)
    rdir = runs_dir_for(args.panel)
    os.makedirs(rdir, exist_ok=True)
    rpath = os.path.join(rdir, run_id + ".json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=2)
    sc = Counter(r["state"] for r in results.values())
    print("已记录 run: %s(engine=%s, cells=%d)→ %s" % (run_id, args.engine, len(results), rpath))
    print("  五状态: " + ", ".join("%s=%d" % (s, sc.get(s, 0)) for s in STATES))
    for w in warnings:
        print("  [!] %s" % w)
    if len(panel["prompts"]) < 10:
        print("  [!] prompts=%d <10:样本太小,结论只能当方向" % len(panel["prompts"]))
    return 0


# ---------- 统计 ----------

def wilson_ci(k, n):
    """按面板口径(正态近似):w=√(p(1-p)/n),CI=p±z·w,z=1.96。"""
    if not n:
        return None
    p = k / n
    w = math.sqrt(p * (1 - p) / n)
    lo = max(0.0, p - Z * w)
    hi = min(1.0, p + Z * w)
    return p, lo, hi, (lo < 0.5 < hi)


def compute_stats(panel, engine=None, _per_engine=True):
    runs = [r for r in panel.get("runs", []) if not engine or r["engine"] == engine]
    state_counts = Counter()
    cells = mentioned_sum = brand_hits = domain_total = 0
    co_cited = Counter()
    per_prompt = {}
    brand_dom = (panel.get("domain") or "").lower()
    competitors = {str(c).strip().lower() for c in panel.get("competitors") or []
                   if str(c).strip()}
    comp_hits = Counter()          # 每 cell 每竞品域至多计 1 次(SoV 分母用)
    cited_urls_sum = 0             # citation_rate 分子(显式引用次数)
    rank_cells = wins = 0          # win_rate(Peec: 排第一次数/响应数)
    for run in runs:
        for prompt, res in run["results"].items():
            cells += 1
            state_counts[res["state"]] += 1
            mentioned_sum += res["mentioned"]
            doms = {registrable_domain(u) for u in res.get("cited_urls", [])}
            doms.discard("")
            cited_urls_sum += len(res.get("cited_urls") or [])
            domain_total += len(doms)
            if brand_dom and brand_dom in doms:
                brand_hits += 1
            for d in doms:
                if d != brand_dom:
                    co_cited[d] += 1
                if d in competitors:
                    comp_hits[d] += 1
            rk = res.get("rank")
            if isinstance(rk, int) and rk > 0:
                rank_cells += 1
                wins += (rk == 1)
            agg = per_prompt.setdefault(prompt, {"n": 0, "k": 0})
            if res["state"] != "failed":
                agg["n"] += 1
                agg["k"] += res["mentioned"]
    denom = cells - state_counts["failed"]
    answers = denom - state_counts["no_answer"]
    coverage = (mentioned_sum / denom) if denom else None
    share = (brand_hits / domain_total) if (domain_total and brand_dom) else None
    # 指标族(Peec 官方公式;SoV 的"提及"以引用域命中为代理——record 未存竞品文本提及)
    tracked_total = (brand_hits + sum(comp_hits.values())) if (brand_dom and competitors) else 0
    sov = (brand_hits / tracked_total) if tracked_total else None
    win_rate = (wins / rank_cells) if rank_cells else None
    citation_rate = (cited_urls_sum / answers) if answers else None
    source_visibility = (brand_hits / answers) if (answers and brand_dom) else None
    gap_pp = (abs(coverage - source_visibility) * 100
              if (coverage is not None and source_visibility is not None) else None)
    stability = {}
    for prompt, agg in per_prompt.items():
        if agg["n"] >= 3:
            stability[prompt] = (agg["k"], agg["n"]) + wilson_ci(agg["k"], agg["n"])
    per_engine = {}
    if _per_engine:
        for eng in sorted({r["engine"] for r in runs}):
            sub = compute_stats({**panel, "runs": [r for r in runs if r["engine"] == eng]},
                                _per_engine=False)
            per_engine[eng] = sub
    return {"runs": len(runs), "cells": cells, "state_counts": state_counts,
            "denominator": denom, "mentioned_sum": mentioned_sum, "coverage": coverage,
            "brand_hits": brand_hits, "domain_total": domain_total, "share": share,
            "co_cited": co_cited, "stability": stability, "per_engine": per_engine,
            # v2 指标族新增键(旧键全部保留)
            "answers": answers, "cited_urls_sum": cited_urls_sum,
            "citation_rate": citation_rate,
            "competitors": sorted(competitors), "comp_hits": comp_hits, "sov": sov,
            "rank_cells": rank_cells, "wins": wins, "win_rate": win_rate,
            "brand_visibility": coverage, "source_visibility": source_visibility,
            "visibility_gap_pp": gap_pp}


def _pct(x):
    return "N/A" if x is None else "%.1f%%" % (100 * x)


def render_report(panel, stats, engine=None):
    L = []
    L.append("== AI 可见性面板报告: %s ==" % panel["brand"])
    L.append("prompts=%d runs=%d cells=%d engines=%s"
             % (len(panel["prompts"]), stats["runs"], stats["cells"],
                ",".join(panel["engines"])))
    if stats["runs"] == 0:
        L.append("尚无运行记录。先用 record 录入采样。")
        return "\n".join(L)
    sc = stats["state_counts"]
    L.append("-- 五状态分类 --")
    notes = {"failed": "  ← 采集失败≠内容缺口,不入分母",
             "no_answer": "  ← 留在覆盖分母,计 zero-presence"}
    for s in STATES:
        pct = (100 * sc.get(s, 0) / stats["cells"]) if stats["cells"] else 0
        L.append("  %-18s %4d  (%5.1f%%)%s" % (s, sc.get(s, 0), pct, notes.get(s, "")))
    L.append("-- mention coverage --")
    L.append("  Σmentioned=%d / 成功 cell=%d(=cells−failed;no_answer 计 0 留分母)= %s"
             % (stats["mentioned_sum"], stats["denominator"], _pct(stats["coverage"])))
    L.append("-- citation share(每答案每品牌至多计 1 次,各品牌恒和 100%)--")
    if panel.get("domain"):
        if stats["share"] is None:
            L.append("  N/A(尚无任何引用 URL,空分母)")
        else:
            L.append("  %s: %d / %d = %s"
                     % (panel["domain"], stats["brand_hits"], stats["domain_total"],
                        _pct(stats["share"])))
        top = stats["co_cited"].most_common(5)
        if top:
            L.append("  同场竞品域(top5): " + ", ".join(
                "%s %.1f%%" % (d, 100 * c / stats["domain_total"]) for d, c in top))
    else:
        L.append("  N/A(面板未设 --domain,无法把引用 URL 归到品牌)")
    L.append("-- 每 prompt 稳定性(≥3 次有效采样才报;z=1.96) --")
    if stats["stability"]:
        for prompt, (k, n, p, lo, hi, unstable) in sorted(stats["stability"].items()):
            L.append("  %-40.40s n=%d k=%d p=%.2f CI95[%.2f,%.2f] %s"
                     % (prompt, n, k, p, lo, hi,
                        "UNSTABLE(区间跨 0.5)" if unstable else "stable"))
    else:
        L.append("  无 ≥3 次采样的 prompt")
    L.append("  [i] 单次引用检查 = 掷硬币:不足 3 次采样的 prompt 不下结论")
    L.append("-- 指标族(Peec 官方公式) --")
    if stats.get("competitors"):
        tracked = stats["brand_hits"] + sum(stats["comp_hits"].values())
        if stats["sov"] is None:
            L.append("  SoV = N/A(自身与追踪竞品均无引用域命中,空分母)")
        else:
            L.append("  SoV = 自身提及/(全部追踪品牌提及) = %d/%d = %s"
                     % (stats["brand_hits"], tracked, _pct(stats["sov"])))
            L.append("    (提及以引用域命中为代理——record 未存竞品文本提及;竞品=%s)"
                     % ",".join(stats["competitors"]))
    else:
        L.append("  SoV = N/A(面板无竞品名单:init --competitors a.com,b.com 或 "
                 "panel['competitors']=[域])")
    if stats["win_rate"] is None:
        L.append("  win_rate = N/A(run.csv 无 rank 列;有排位数据才算)")
    else:
        L.append("  win_rate = 排第一次数/响应数 = %d/%d = %s"
                 % (stats["wins"], stats["rank_cells"], _pct(stats["win_rate"])))
    if stats["citation_rate"] is None:
        L.append("  citation_rate = N/A(无有答案 cell)")
    else:
        L.append("  citation_rate = 被检索时显式引用均次 = %d/%d = %.2f 次/响应"
                 % (stats["cited_urls_sum"], stats["answers"], stats["citation_rate"]))
    bv, sv = stats["brand_visibility"], stats["source_visibility"]
    if bv is not None and sv is not None:
        L.append("  brand_visibility(被提)= %s vs source_visibility(被引)= %s(差距 %.1fpp)"
                 % (_pct(bv), _pct(sv), stats["visibility_gap_pp"]))
        if stats["visibility_gap_pp"] > 20:
            L.append("  [!] 两者差距>20pp:被提≠被引——品牌关联弱/内容信任不足二选一"
                     "(被提不被引=内容不被信任,改可引用格式;被引不被提=品牌关联弱)")
    else:
        L.append("  brand_visibility(被提)= %s,source_visibility(被引)= %s(缺 --domain 时被引为 N/A)"
                 % (_pct(bv), _pct(sv)))
    L.extend(render_geo_section(panel, engine))
    L.append("-- 分引擎(报告按 AI 引擎分列,不合并统计) --")
    for eng, sub in stats["per_engine"].items():
        L.append("  %-12s cells=%-3d coverage=%-7s share=%s"
                 % (eng, sub["cells"], _pct(sub["coverage"]), _pct(sub["share"])))
    if len(panel["prompts"]) < 10:
        L.append("[!] prompts=%d <10:样本太小,结论只能当方向" % len(panel["prompts"]))
    return "\n".join(L)


def cmd_report(args):
    panel = load_panel(args.panel)
    stats = compute_stats(panel, engine=args.engine)
    print(render_report(panel, stats, engine=args.engine))
    return 0


# ---------- diff(配对分母跨期)+ signals(Scrunch 口径) ----------

def resolve_run(arg, panel):
    if os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return json.load(f)
    for r in panel.get("runs", []):
        if r.get("run_id") == arg:
            return r
    return None


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s))
    except ValueError:
        return None


def signal_fingerprint(metric, engine, topic):
    """信号指纹 = sha1(metric+engine+topic) 前 10 位(Scrunch Signals 口径,跨夜去重用)。"""
    return hashlib.sha1(("%s+%s+%s" % (metric, engine, topic)).encode("utf-8")).hexdigest()[:10]


def prior_mention_mean(panel, prompt, engine, not_after):
    """前期均值: 同引擎、日期≤not_after 的全部有效采样中该 prompt 的 mentioned 均值。"""
    vals = []
    for r in panel.get("runs", []):
        if r.get("engine") != engine:
            continue
        d = parse_date(r.get("date"))
        if not_after and d and d > not_after:
            continue
        res = r.get("results", {}).get(prompt)
        if res and res.get("state") != "failed":
            vals.append(res.get("mentioned", 0))
    return (sum(vals) / len(vals)) if vals else None


def diff_signals(run_a, run_b, d, panel):
    """Scrunch Signals 口径: |Δ|≥5pp 且配对 n≥10 才报;不足 10 列'样本不足';
    |Δ|<5pp 计 stable 不报(不制造紧迫感)。信号粒度 = metric × engine × topic,
    topic 来自 prompts 对象化元数据(无标注归"(未标注 topic)"),另有"(整体)"聚合行。
    disappeared 按贡献排序: 该 prompt 前期均值×消失 → 对 delta 的拖累(pp)。"""
    engine = run_b.get("engine") or ""
    res_a, res_b = run_a["results"], run_b["results"]
    paired = d["paired"]
    topics = {}
    for p in panel.get("prompts", []):
        o = prompt_obj(p)
        if o.get("topic"):
            topics[o["text"]] = o["topic"]
    groups = {"(整体)": list(paired)}
    for p in paired:
        if p in topics:
            groups.setdefault(topics[p], []).append(p)
    signals, insufficient, stable = [], [], 0
    for topic in sorted(groups):
        plist = groups[topic]
        n = len(plist)
        for metric, key in (("mention", "mentioned"), ("citation", "cited")):
            k1 = sum(res_a[p][key] for p in plist)
            k2 = sum(res_b[p][key] for p in plist)
            delta = ((k2 - k1) / n * 100) if n else 0.0
            entry = {"metric": metric, "engine": engine, "topic": topic, "n": n,
                     "delta_pp": delta, "fingerprint": signal_fingerprint(metric, engine, topic)}
            if n < 10:
                entry["status"] = "insufficient_n"
                insufficient.append(entry)
            elif abs(delta) >= 5:
                entry["status"] = "reported"
                signals.append(entry)
            else:
                stable += 1
    not_after = parse_date(run_a.get("date"))
    ranked = []
    for p in d["disappeared"]:
        pm = prior_mention_mean(panel, p, run_a.get("engine") or engine, not_after)
        if pm is None:
            pm = float(res_a[p]["mentioned"])   # 无历史时退回 run1 值(消失者为 1)
        contrib = (-pm / len(paired) * 100) if paired else 0.0
        ranked.append((p, pm, contrib))
    ranked.sort(key=lambda x: -abs(x[2]))
    return {"signals": signals, "insufficient": insufficient, "stable_count": stable,
            "disappeared_ranked": ranked}


def diff_runs(run_a, run_b):
    res_a, res_b = run_a["results"], run_b["results"]
    prompts = set(res_a) | set(res_b)
    paired, miss_a, miss_b = [], 0, 0
    for p in prompts:
        a, b = res_a.get(p), res_b.get(p)
        if a is None:
            miss_a += 1
        elif b is None:
            miss_b += 1
        elif a["state"] == "failed" or b["state"] == "failed":
            miss_a += (a["state"] == "failed")
            miss_b += (b["state"] == "failed")
        else:
            paired.append(p)
    new_mentions = [p for p in paired if res_b[p]["mentioned"] and not res_a[p]["mentioned"]]
    gone = [p for p in paired if res_a[p]["mentioned"] and not res_b[p]["mentioned"]]
    k1 = sum(res_a[p]["mentioned"] for p in paired)
    k2 = sum(res_b[p]["mentioned"] for p in paired)
    return {"paired": paired, "excluded": {"missing_in_a": miss_a, "missing_in_b": miss_b},
            "k1": k1, "k2": k2, "new_mentions": new_mentions, "disappeared": gone}


def cmd_diff(args):
    panel = load_panel(args.panel)
    ra, rb = resolve_run(args.run1, panel), resolve_run(args.run2, panel)
    if ra is None or rb is None:
        print("错误: 找不到 run(应为 run 文件路径或面板内 run_id): %s / %s"
              % (args.run1, args.run2), file=sys.stderr)
        return 1
    d = diff_runs(ra, rb)
    n = len(d["paired"])
    print("== diff(配对分母:只比两期均成功(非 failed)的 cell) ==")
    print("run1: %s (%s, %s)" % (ra.get("run_id"), ra.get("engine"), ra.get("date")))
    print("run2: %s (%s, %s)" % (rb.get("run_id"), rb.get("engine"), rb.get("date")))
    print("配对 cell: %d | 排除: run1 侧 %d,run2 侧 %d(失败或缺测)"
          % (n, d["excluded"]["missing_in_a"], d["excluded"]["missing_in_b"]))
    if n:
        print("mention: run1 %d/%d=%.1f%% → run2 %d/%d=%.1f%%"
              % (d["k1"], n, 100 * d["k1"] / n, d["k2"], n, 100 * d["k2"] / n))
    print("新提及(%d): %s" % (len(d["new_mentions"]),
          "; ".join(d["new_mentions"]) if d["new_mentions"] else "(无)"))
    print("消失提及(%d): %s" % (len(d["disappeared"]),
          "; ".join(d["disappeared"]) if d["disappeared"] else "(无)"))
    if n < 10:
        print("[!] 配对 cell=%d <10:样本太小,结论只能当方向" % n)
    sig = diff_signals(ra, rb, d, panel)
    print("-- signals(Scrunch Signals 口径:|Δ|≥5pp 且配对 n≥10 才报) --")
    for s in sig["signals"]:
        print("  [signal] %-9s engine=%s topic=%s Δ=%+.1fpp n=%d fp=%s"
              % (s["metric"], s["engine"], s["topic"], s["delta_pp"], s["n"], s["fingerprint"]))
    for s in sig["insufficient"]:
        print("  [样本不足] %-9s engine=%s topic=%s Δ=%+.1fpp n=%d(<10,不下结论)"
              % (s["metric"], s["engine"], s["topic"], s["delta_pp"], s["n"]))
    if sig["stable_count"]:
        print("  (另有 %d 条 |Δ|<5pp 且 n≥10:stable 不报——指标全平不制造紧迫感)"
              % sig["stable_count"])
    if sig["disappeared_ranked"]:
        print("  消失提及按贡献排序(该 prompt 前期均值×消失 → 对 Δ 的拖累,pp):")
        for i, (prompt, mean, contrib) in enumerate(sig["disappeared_ranked"], 1):
            print("    %d. %-40.40s 前期均值 %.2f → 贡献 %+.1fpp" % (i, prompt, mean, contrib))
    return 0


# ---------- decay(Profound 官方方法论;阈值抄自官方) ----------
# 出处: references/research/borrow-specs.md B1(Profound 2026-09 88.3 万页研究)。
# 序列 y_t = 该 cell 每次(非 failed)采样的 metric 值(0/1;no_answer 计 0 留序列),
# 按日期升序后取 7 点滚动均值(官方 14 天滚动,我们采样密度低取 7)。
# 资格闸门 4 道(官方): 观察窗≥28 天 / 峰值窗(峰值±7 天)采样≥5 / 峰值>0 /
# 首采距面板窗起点>30 天剔除。半衰 = peak 后平滑≤50%peak 且连续 14 天无反弹的
# 天数(未达成 = holding 右删失,不丢弃)。状态机: rising / peaked(近 14 天=peak)/
# decaying(过峰未满半)/ decayed / holding。重写队列(官方口径:"过峰且 share 正
# 跌向峰值一半"才是该更新的页)按距半衰剩余天数升序。

def rolling_mean(vals, window=DECAY_SMOOTH_WINDOW):
    """7 点滚动均值(官方 14 天;采样密度低取 7)。前 window−1 点为暖机期,
    不产平滑值(否则首点=原值,会伪造早期峰值)。"""
    out = [None] * len(vals)
    for i in range(window - 1, len(vals)):
        out[i] = sum(vals[i - window + 1: i + 1]) / window
    return out


def eval_decay_cell(samples, panel_start):
    """单个 (prompt,engine) cell 的 decay 判定。samples=[(datetime, y)] 升序。"""
    dates = [d for d, _ in samples]
    ys = [y for _, y in samples]
    n = len(ys)
    base = {"n_samples": n, "window_days": (dates[-1] - dates[0]).days if n > 1 else 0,
            "peak": None, "peak_date": None, "half_life_days": None,
            "days_to_half": None, "smooth_last": None, "note": ""}
    if (dates[-1] - dates[0]).days < DECAY_MIN_WINDOW_DAYS:
        return dict(base, status="excluded",
                    exclude_reason="观察窗 %d 天<%d(官方)"
                                   % ((dates[-1] - dates[0]).days, DECAY_MIN_WINDOW_DAYS))
    if panel_start and (dates[0].date() - panel_start.date()).days > DECAY_LATE_START_DAYS:
        return dict(base, status="excluded",
                    exclude_reason="首采距面板窗起点 %d 天>%d(官方)"
                                   % ((dates[0].date() - panel_start.date()).days,
                                      DECAY_LATE_START_DAYS))
    smooth = rolling_mean(ys)
    defined = [(i, v) for i, v in enumerate(smooth) if v is not None]
    if len(defined) < 2:
        return dict(base, status="excluded",
                    exclude_reason="采样点 <%d,无法平滑" % (DECAY_SMOOTH_WINDOW + 1))
    base["smooth_last"] = defined[-1][1]
    peak = max(v for _, v in defined)
    base["peak"] = peak
    peak_i = min(i for i, v in defined if abs(v - peak) < 1e-12)   # 首次达峰
    peak_date = dates[peak_i]
    base["peak_date"] = peak_date.isoformat()
    if peak <= 0:
        return dict(base, status="excluded", exclude_reason="峰值≤0(全程无命中)")
    n_peak = sum(1 for d in dates if abs((d - peak_date).days) <= DECAY_PEAK_WINDOW_DAYS)
    if n_peak < DECAY_MIN_PEAK_SAMPLES:
        return dict(base, status="excluded",
                    exclude_reason="峰值窗(±%d 天)采样 %d<%d(官方)"
                                   % (DECAY_PEAK_WINDOW_DAYS, n_peak, DECAY_MIN_PEAK_SAMPLES))
    half = 0.5 * peak
    last_date = dates[-1]
    if peak_i >= n - 2 and smooth[-1] >= peak - 1e-9:
        return dict(base, status="rising", note="平滑最高在尾部,仍在爬升/顶部")
    if (last_date - peak_date).days <= DECAY_NO_REBOUND_DAYS:
        return dict(base, status="peaked", note="峰值在近 %d 天内" % DECAY_NO_REBOUND_DAYS)
    # 半衰搜索: 最早满足"平滑≤half 且此后 14 天无反弹"且确认窗被完整观察到的 t
    half_life = censored = rebounded = None
    no_rebound_end = timedelta(days=DECAY_NO_REBOUND_DAYS)
    for ti in range(peak_i + 1, n):
        if smooth[ti] > half + 1e-9:
            continue                       # 候选起点必须已 ≤半
        ok = all(smooth[tj] <= half + 1e-9
                 for tj in range(ti, n) if dates[tj] <= dates[ti] + no_rebound_end)
        if not ok:
            rebounded = True
            continue
        if dates[ti] + no_rebound_end <= last_date:
            half_life = (dates[ti] - peak_date).days
        else:
            censored = True               # ≤半维持到观察末尾但确认窗未满 → 右删失
        break
    if half_life is not None:
        return dict(base, status="decayed", half_life_days=half_life, days_to_half=0,
                    note="过峰且平滑≤50%%peak 持续 %d 天无反弹" % DECAY_NO_REBOUND_DAYS)
    if censored:
        return dict(base, status="holding",
                    note="右删失:已≤半但观察不足以确认 %d 天无反弹(不丢弃)" % DECAY_NO_REBOUND_DAYS)
    if rebounded:
        return dict(base, status="holding", note="≤半后反弹,半衰未成立(不丢弃)")
    if smooth[-1] >= peak - 1e-9:
        return dict(base, status="holding", note="峰后持平于峰值附近,未见衰退(右删失)")
    # decaying: 过峰未满半,线性外推距半衰剩余天数
    slope = (smooth[-1] - peak) / max(1, (last_date - peak_date).days)
    if slope < -1e-9:
        remain = max(0.0, (smooth[-1] - half) / (-slope))
        return dict(base, status="decaying", days_to_half=remain,
                    note="过峰未满半,线性外推距半衰≈%.0f 天 [est]" % remain)
    return dict(base, status="decaying", days_to_half=None,
                note="过峰未满半且斜率平缓;官方中位半衰期 %d 天参照 [est]"
                     % OFFICIAL_MEDIAN_HALF_LIFE)


def collect_cell_series(panel, metric="cited", engine=None):
    """runs → {(prompt, engine): [(datetime, y)]}(failed 不入序列;y=metric 值 0/1)。"""
    series = {}
    for run in panel.get("runs", []):
        if engine and run["engine"] != engine:
            continue
        d = parse_date(run.get("date"))
        if d is None:
            continue
        for prompt, res in run["results"].items():
            if res["state"] == "failed":
                continue
            series.setdefault((prompt, run["engine"]), []).append((d, float(res.get(metric, 0))))
    for key in series:
        series[key].sort(key=lambda x: x[0])
    return series


def analyze_decay(panel, metric="cited", engine=None):
    """全面板 decay 判定 + 重写队列(状态∈decaying/decayed × 距半衰剩余天数升序)。"""
    all_dates = [d for d in (parse_date(r.get("date")) for r in panel.get("runs", [])) if d]
    panel_start = min(all_dates) if all_dates else None
    panel_end = max(all_dates) if all_dates else None
    cells = []
    series = collect_cell_series(panel, metric, engine)
    for (prompt, eng) in sorted(series):
        cell = {"prompt": prompt, "engine": eng}
        cell.update(eval_decay_cell(series[(prompt, eng)], panel_start))
        cells.append(cell)
    queue = [c for c in cells if c["status"] in ("decaying", "decayed")]
    queue.sort(key=lambda c: (c.get("days_to_half") is None, c.get("days_to_half") or 0.0))
    return {"metric": metric, "engine": engine or "(all)",
            "panel_window": {"start": panel_start.isoformat() if panel_start else None,
                             "end": panel_end.isoformat() if panel_end else None},
            "cells": cells, "rewrite_queue": queue}


def _decay_fmt(x, est=False):
    if x is None:
        return "-"
    if isinstance(x, float):
        return ("≈%.1f" % x) + (" [est]" if est else "")
    return str(x)


def render_decay(panel, result):
    cells, queue = result["cells"], result["rewrite_queue"]
    judged = [c for c in cells if c["status"] != "excluded"]
    L = []
    L.append("== citation decay: %s(Profound 官方方法论;阈值抄自官方)=="
             % panel.get("brand", "?"))
    L.append("metric=%s(0/1 序列;failed 不入序列,no_answer 计 0);平滑=%d 点滚动均值"
             "(官方 14 天,采样密度低取 7)" % (result["metric"], DECAY_SMOOTH_WINDOW))
    L.append("资格闸门 4 道: 观察窗≥%d 天;峰值窗(峰值±%d 天)采样≥%d;峰值>0;"
             "首采距面板窗起点≤%d 天" % (DECAY_MIN_WINDOW_DAYS, DECAY_PEAK_WINDOW_DAYS,
                                      DECAY_MIN_PEAK_SAMPLES, DECAY_LATE_START_DAYS))
    L.append("面板窗: %s → %s | cells: %d 判定 / %d 剔除"
             % (result["panel_window"]["start"], result["panel_window"]["end"],
                len(judged), len(cells) - len(judged)))
    L.append("| prompt | engine | 状态 | n | 窗(天) | peak | 半衰(天) | 距半衰剩余(天) | 备注/剔除原因 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for c in cells:
        remain = "0" if c["status"] == "decayed" else _decay_fmt(c["days_to_half"], est=True)
        L.append("| %s | %s | %s | %d | %d | %s | %s | %s | %s |" % (
            c["prompt"].replace("|", "\\|"), c["engine"], c["status"], c["n_samples"],
            c["window_days"], _decay_fmt(c["peak"]), _decay_fmt(c["half_life_days"]),
            remain, (c.get("exclude_reason") or c.get("note") or "").replace("|", "\\|")))
    L.append("-- 重写队列(官方口径:过峰且 share 正跌向峰值一半才是该更新的页;"
             "按距半衰剩余天数升序)--")
    if queue:
        for i, c in enumerate(queue, 1):
            if c["status"] == "decayed":
                remain = "0(已过半衰)"
            elif isinstance(c.get("days_to_half"), float):
                remain = "≈%d 天" % round(c["days_to_half"])
            else:
                remain = "未知(官方中位半衰期 %d 天参照) [est]" % OFFICIAL_MEDIAN_HALF_LIFE
            L.append("%d. [%s](%s) %s,距半衰剩余 %s → 建议更新(owned 页以面板 prompt 为代理 [est])"
                     % (i, c["prompt"], c["engine"], c["status"], remain))
    else:
        L.append("(无——没有过峰且正跌向一半的 cell;decay 是触发器,不是季度末才发现)")
    L.append("脚注: 跨引擎相关仅 0.03-0.09,分引擎独立判定(Profound 官方)")
    L.append("官方常数参照: 中位半衰期 %d 天;78%% 页两周内掉半"
             "(Profound 2026-09 88.3 万页研究)" % OFFICIAL_MEDIAN_HALF_LIFE)
    return "\n".join(L)


def cmd_decay(args):
    panel = load_panel(args.panel)
    if not panel.get("runs"):
        print("错误: 面板尚无 runs,先用 record 录入采样: %s" % args.panel, file=sys.stderr)
        return 1
    result = analyze_decay(panel, metric=args.metric, engine=args.engine)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_decay(panel, result))
    return 0


# ---------- geo 打分写回(geo-scoring-rubric 五维打分卡) ----------
# 出处: references/content/geo-scoring-rubric.md(2026-10-10;oneglanse 441 行骨架 +
# 本套件证据约束)。geo 是**分析层扩展键**,写进 results.<prompt>.geo;采集层口径
# 不动——compute_stats/diff/decay 只读 state/mentioned/cited/cited_urls/rank,geo 键
# 被忽略,打分写回不改变 coverage/share,也不触发 diff signals(geo 变化是分析层
# 判定变化,不是采集层指标变化)。schema(rubric 十一节,键序一致):
#   {geo_score, presence, position{absolute_rank,mentions,first_occurrence_pct},
#    sentiment, recommendation, competitors[{brand,absolute_rank,mentions,sentiment}],
#    risks[]}
# 机检分层: 硬违例(枚举外值/白名单外字段/类型错/prompt 对不上/failed cell)→ 整批
# 原子拒绝不落盘;可机修的(硬 cap 封顶/越界 clamp/top_pick 缺佐证降级/缺席置 null)
# → 警告后落盘。presence→面板 state 映射(rubric 十一节): refused→no_answer、
# echo_only→brand_absent,其余同名(细粒度值只活在 geo 块里)。

GEO_PRESENCE = ("refused", "no_answer", "echo_only", "brand_absent",
                "name_only_mention", "cited_brand")
GEO_RECOMMENDATIONS = ("top_pick", "recommended", "honorable_mention",
                       "neutral", "discouraged", "absent")
GEO_RISKS = ("outdated_info", "factual_error", "brand_confusion",
             "negative_association", "missing_from_response")
GEO_KEYS = ("geo_score", "presence", "position", "sentiment",
            "recommendation", "competitors", "risks")
GEO_POSITION_KEYS = ("absolute_rank", "mentions", "first_occurrence_pct")
GEO_COMPETITOR_KEYS = ("brand", "absolute_rank", "mentions", "sentiment")
GEO_ABSENT_PRESENCE = ("refused", "no_answer", "brand_absent")  # 缺席不打分 → geo_score=null
GEO_SCORED_PRESENCE = ("name_only_mention", "cited_brand")      # 应产出数值 geo_score
GEO_PRESENCE_TO_STATE = {"refused": "no_answer", "echo_only": "brand_absent"}  # 其余同名
# rubric 第四节硬 cap(封顶不是扣分,多条命中取最严)
GEO_CAP_SINGLE_MENTION = 50          # 仅 1 次提及
GEO_CAP_ECHO_ONLY = 10               # 只出现在问题/回声里
GEO_CAP_COMPARATIVE_NEGATIVE = 35    # 对比性负面(机检代理: discouraged 或 sentiment≤20)
GEO_ANTI_INFLATION_MEAN = 75         # 反通胀提示线(rubric 九节: LLM 系统性打高分)
GEO_SCORE_BANDS = ((0, 35), (36, 55), (56, 75), (76, 100))
# 分布档含义(rubric 锚点带): 0-35=硬 cap 区(单提及/负面/回声)/36-55=平均列名带/
# 56-75=正向无最高级/76-100=最高级与强推荐带

GEO_RUBRIC_DIGEST = """== geo-scoring-rubric 压缩判定要点(代码内常量,standalone;全文见 references/content/geo-scoring-rubric.md) ==
质量闸(先过闸再打分): refusal/no_answer → 不打分(presence=refused/no_answer;面板 state=no_answer);
  echo_only(品牌只出现在复述问题的回声句,论证部分零出现)→ 不算提及(presence=echo_only;面板 mentioned=0/state=brand_absent)。
五维加权(各维 0-100): A 覆盖 25%(纯列名 20/单属性 40/2-3 属性 60/多属性+事实 80/专属小节 100)
  B 首现位置 25%(全文绝对排名映射 #1→100/#2→85/#3→70/#4→55/#5→40/#6+→30;子类目第 1 ≠ 全文第 1)
  C 结构显著性 20%(标题级 100/列表表格条目 80/段首或表列名 60/行文中段 40/长段深处 20)
  D 频次 15%(1 次=30/2-3 次=55/4-5 次=75/≥6 次=90;回声不计入)
  E 语境角色 15%(明确推荐 100/对比胜出 80/中立并列 60/仅反例 40/被警告 20/被劝退 0)
硬 cap 表(加权分先过这张表;封顶不是扣分,多条命中取最严): 仅 1 次提及 ≤50;只出现在回声里 ≤10;对比性负面 ≤35。
情感校准(决策树自上而下): 显式最高级词 → 81-100(没有 → 封顶 79);同屏 pro+con → ≤79;
  纯列表无评价词 → 50-55;负向主导 → 21-45(明确劝退 0-20);"贵"单独出现按混合 21-45。
recommendation 六级: top_pick=全文绝对 #1+显式最高级措辞(缺一降级)/recommended(入围推荐非首选)/
  honorable_mention(列名无评语)/neutral(并列中性)/discouraged(上榜但负面或被劝退)/absent(未被提及,含 echo_only)。
竞品去重: 子产品先并入父品牌再排名(位次取各子产品最早,情感按提及次数加权平均);去重先于排名编号。
反通胀纪律: LLM 打分系统性偏高——"pretty good/decent"落 61-75 不是 80+;平均列名 45-55 不是 70+;
  情感 81+ 必须有原文显式最高级词;一批大多 70+ → 回锚点重校,不顺手下调。
risks 五型枚举: outdated_info/factual_error/brand_confusion/negative_association/missing_from_response。
缺席不打分: refused/no_answer/echo_only/brand_absent → geo_score=null 不入任何均值;failed cell 不打分不入分母;
  单次打分=掷硬币,prompt 级结论取 3 次采样多数档,分歧大标 unstable。"""


def _geo_num(v, field, prompt, errors):
    """数值字段提取(bool/str 拒绝——schema 要数值)。失败记 error 并返回 None。"""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errors.append("%s: %s 需要数值,得到 %r" % (prompt, field, v))
        return None
    return float(v)


def _geo_clamp(val, lo, hi, field, prompt, warnings):
    """越界值拉回 [lo,hi](hi=None 只限下界)+ 警告(越界 clamp,不整条拒绝)。"""
    if val < lo:
        warnings.append("%s: %s=%s 越界,已 clamp 到 %s" % (prompt, field, val, lo))
        return float(lo)
    if hi is not None and val > hi:
        warnings.append("%s: %s=%s 越界,已 clamp 到 %s" % (prompt, field, val, hi))
        return float(hi)
    return val


def validate_geo(geo, prompt, cell, errors, warnings):
    """geo-scoring-rubric 硬规则机检(防 agent 打分违例)。硬违例记 errors(调用方
    整批原子拒绝不落盘);可机修项(硬 cap 封顶/越界 clamp/top_pick 缺佐证降级/
    缺席置 null)记 warnings 后照常落盘。返回规范化 geo 块(errors 非空时返回 None)。"""
    if not isinstance(geo, dict):
        errors.append("%s: geo 块需要 {geo_score,presence,...} 对象,得到 %r" % (prompt, geo))
        return None
    unknown = sorted(set(geo) - set(GEO_KEYS))
    if unknown:
        errors.append("%s: 未知字段 %s(schema 白名单: %s)"
                      % (prompt, ",".join(unknown), ",".join(GEO_KEYS)))
    if cell.get("state") == "failed":
        errors.append("%s: 该 cell state=failed,不打分不入分母(rubric 十二节)" % prompt)
        return None
    presence = geo.get("presence")
    if presence not in GEO_PRESENCE:
        errors.append("%s: presence=%r 不在枚举 %s" % (prompt, presence, list(GEO_PRESENCE)))
    rec = geo.get("recommendation")
    if rec not in GEO_RECOMMENDATIONS:
        errors.append("%s: recommendation=%r 不在六枚举 %s"
                      % (prompt, rec, list(GEO_RECOMMENDATIONS)))
    risks_in = geo.get("risks")
    risks = []
    if risks_in is not None:
        if not isinstance(risks_in, list):
            errors.append("%s: risks 需要 list,得到 %r" % (prompt, risks_in))
        else:
            for rk in risks_in:
                if rk not in GEO_RISKS:
                    errors.append("%s: risks=%r 不在五型枚举 %s"
                                  % (prompt, rk, list(GEO_RISKS)))
                elif rk in risks:
                    warnings.append("%s: risks 重复项 %s 已去重" % (prompt, rk))
                else:
                    risks.append(rk)
    # position(可缺;字段白名单 + 越界 clamp)
    pos_out, pos_mentions = None, None
    pos = geo.get("position")
    if pos is not None:
        if not isinstance(pos, dict):
            errors.append("%s: position 需要对象,得到 %r" % (prompt, pos))
        else:
            p_unknown = sorted(set(pos) - set(GEO_POSITION_KEYS))
            if p_unknown:
                errors.append("%s: position 未知字段 %s(白名单: %s)"
                              % (prompt, ",".join(p_unknown), ",".join(GEO_POSITION_KEYS)))
            else:
                pos_out = {}
                if pos.get("absolute_rank") is not None:
                    v = _geo_num(pos["absolute_rank"], "position.absolute_rank", prompt, errors)
                    if v is not None:
                        pos_out["absolute_rank"] = int(round(_geo_clamp(
                            v, 1, None, "position.absolute_rank", prompt, warnings)))
                if pos.get("mentions") is not None:
                    v = _geo_num(pos["mentions"], "position.mentions", prompt, errors)
                    if v is not None:
                        pos_mentions = int(round(_geo_clamp(
                            v, 0, None, "position.mentions", prompt, warnings)))
                        pos_out["mentions"] = pos_mentions
                if pos.get("first_occurrence_pct") is not None:
                    v = _geo_num(pos["first_occurrence_pct"], "position.first_occurrence_pct",
                                 prompt, errors)
                    if v is not None:
                        pos_out["first_occurrence_pct"] = int(round(_geo_clamp(
                            v, 0, 100, "position.first_occurrence_pct", prompt, warnings)))
    # sentiment(可缺;0-100 clamp)
    sent = None
    if geo.get("sentiment") is not None:
        v = _geo_num(geo["sentiment"], "sentiment", prompt, errors)
        if v is not None:
            sent = int(round(_geo_clamp(v, 0, 100, "sentiment", prompt, warnings)))
    # competitors(可缺;brand 必填,字段白名单 + clamp)
    comps_out = None
    comps = geo.get("competitors")
    if comps is not None:
        if not isinstance(comps, list):
            errors.append("%s: competitors 需要 list,得到 %r" % (prompt, comps))
        else:
            comps_out = []
            for c in comps:
                if not isinstance(c, dict) or not str(c.get("brand") or "").strip():
                    errors.append("%s: competitor 条目需要非空 brand,得到 %r" % (prompt, c))
                    continue
                c_unknown = sorted(set(c) - set(GEO_COMPETITOR_KEYS))
                if c_unknown:
                    errors.append("%s: competitor(%s)未知字段 %s(白名单: %s)"
                                  % (prompt, c["brand"], ",".join(c_unknown),
                                     ",".join(GEO_COMPETITOR_KEYS)))
                    continue
                cc = {"brand": str(c["brand"]).strip()}
                if c.get("absolute_rank") is not None:
                    v = _geo_num(c["absolute_rank"], "competitor.absolute_rank", prompt, errors)
                    if v is not None:
                        cc["absolute_rank"] = int(round(_geo_clamp(
                            v, 1, None, "competitor.absolute_rank", prompt, warnings)))
                if c.get("mentions") is not None:
                    v = _geo_num(c["mentions"], "competitor.mentions", prompt, errors)
                    if v is not None:
                        cc["mentions"] = int(round(_geo_clamp(
                            v, 0, None, "competitor.mentions", prompt, warnings)))
                if c.get("sentiment") is not None:
                    v = _geo_num(c["sentiment"], "competitor.sentiment", prompt, errors)
                    if v is not None:
                        cc["sentiment"] = int(round(_geo_clamp(
                            v, 0, 100, "competitor.sentiment", prompt, warnings)))
                comps_out.append(cc)
    # geo_score: null=缺席不打分;数值 0-100 clamp 后过 rubric 第四节硬 cap 表
    gs = geo.get("geo_score")
    if isinstance(gs, bool) or not (gs is None or isinstance(gs, (int, float))):
        errors.append("%s: geo_score 需要数值或 null,得到 %r" % (prompt, gs))
        gs = None
    elif gs is not None:
        gs = _geo_clamp(float(gs), 0, 100, "geo_score", prompt, warnings)
    if presence in GEO_ABSENT_PRESENCE and gs is not None:
        warnings.append("%s: presence=%s 缺席不打分,geo_score=%s 已置 null(rubric 十一节)"
                        % (prompt, presence, gs))
        gs = None
    if gs is None and presence in GEO_SCORED_PRESENCE:
        warnings.append("%s: presence=%s 应产出数值 geo_score,得到 null(rubric 十一节)"
                        % (prompt, presence))
    if gs is not None:
        caps = []
        if pos_mentions == 1:
            caps.append((GEO_CAP_SINGLE_MENTION, "仅 1 次提及"))
        if presence == "echo_only":
            caps.append((GEO_CAP_ECHO_ONLY, "只出现在问题/回声里"))
        if rec == "discouraged" or (sent is not None and sent <= 20):
            caps.append((GEO_CAP_COMPARATIVE_NEGATIVE,
                         "对比性负面提及(discouraged 或 sentiment≤20)"))
        for cap, why in sorted(caps, key=lambda x: x[0]):    # 多条命中取最严
            if gs > cap:
                warnings.append("%s: geo_score=%d 违反硬 cap(%s → ≤%d),已封顶到 %d"
                                "(cap 是封顶不是扣分)" % (prompt, gs, why, cap, cap))
                gs = cap
    # top_pick 佐证机检: 必须有 position 绝对排名 #1,否则降 honorable_mention
    if rec == "top_pick" and (pos_out is None or pos_out.get("absolute_rank") != 1):
        warnings.append("%s: top_pick 无 position 绝对排名 #1 佐证,已降级 honorable_mention"
                        "(rubric 七节: 全文绝对 #1+显式最高级,缺佐证不认)" % prompt)
        rec = "honorable_mention"
    if rec == "absent" and presence in GEO_SCORED_PRESENCE:
        warnings.append("%s: presence=%s 已被提及但 recommendation=absent(复核;"
                        "未提及/echo_only 才记 absent)" % (prompt, presence))
    # presence ↔ 面板 state 映射软校验(refused→no_answer,echo_only→brand_absent)
    if presence in GEO_PRESENCE:
        expected = GEO_PRESENCE_TO_STATE.get(presence, presence)
        if cell.get("state") and cell["state"] != expected:
            warnings.append("%s: presence=%s 按映射应对应 state=%s,该 cell 实为 state=%s"
                            "(复核采集列与打分是否同一 cell)"
                            % (prompt, presence, expected, cell["state"]))
    if errors:
        return None
    out = {"geo_score": (int(gs) if gs is not None else None), "presence": presence}
    if pos_out is not None:
        out["position"] = pos_out
    if sent is not None:
        out["sentiment"] = sent
    out["recommendation"] = rec
    if comps_out is not None:
        out["competitors"] = comps_out
    if risks:
        out["risks"] = risks
    return out


def load_scores(path):
    """scores.json → {prompt: geo 块}。支持 {prompt: {...geo...}} 对象形态与
    [{"prompt": ..., **geo}] 列表形态(prompt 是包装字段,不进 geo 块)。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()}
    if isinstance(data, list):
        out = {}
        for e in data:
            if not isinstance(e, dict) or "prompt" not in e:
                raise ValueError("scores 列表项需要 prompt 字段: %r" % (e,))
            out[str(e["prompt"])] = {k: v for k, v in e.items() if k != "prompt"}
        return out
    raise ValueError("scores.json 需为 {prompt: geo} 对象或带 prompt 字段的对象列表")


def cmd_score(args):
    if args.rubric:
        print(GEO_RUBRIC_DIGEST)
        return 0
    if args.last and args.run:
        print("错误: --run 与 --last 二选一", file=sys.stderr)
        return 1
    if not args.scores:
        print("错误: score 需要 --scores scores.json(或单独 --rubric 打印判定要点)",
              file=sys.stderr)
        return 1
    if not args.run and not args.last:
        print("错误: score 需要 --run RUNID 或 --last 指定目标 run", file=sys.stderr)
        return 1
    panel = load_panel(args.panel)
    if not panel.get("runs"):
        print("错误: 面板尚无 runs,先 record 录入采样: %s" % args.panel, file=sys.stderr)
        return 1
    if args.last:
        run = panel["runs"][-1]              # 最近一条(append 序=时间序)
    else:
        run = next((r for r in panel["runs"] if r.get("run_id") == args.run), None)
        if run is None:
            print("错误: 面板内找不到 run_id=%s" % args.run, file=sys.stderr)
            return 1
    run_id = run.get("run_id")
    try:
        scores = load_scores(args.scores)
    except (OSError, ValueError) as e:
        print("错误: 读取 scores 失败: %s" % e, file=sys.stderr)
        return 1
    if not scores:
        print("错误: %s 中没有打分条目" % args.scores, file=sys.stderr)
        return 1
    errors, warnings, cleaned = [], [], {}
    for prompt, geo in scores.items():
        cell = run.get("results", {}).get(prompt)
        if cell is None:
            errors.append("%s: 不在 run %s 的 results 中(prompt 需与采样 prompt 一致)"
                          % (prompt, run_id))
            continue
        c = validate_geo(geo, prompt, cell, errors, warnings)
        if c is not None:
            cleaned[prompt] = c
    if errors:                               # 原子拒绝: 有硬违例整批不落盘(防半写)
        print("错误: %d 条硬违例,整批拒绝未写回(修正 scores.json 后重跑):"
              % len(errors), file=sys.stderr)
        for e in errors:
            print("  [reject] %s" % e, file=sys.stderr)
        return 1
    rescored = sum(1 for p in cleaned if "geo" in run["results"][p])
    for prompt, c in cleaned.items():
        run["results"][prompt]["geo"] = c
    save_panel(args.panel, panel)
    rpath = os.path.join(runs_dir_for(args.panel), run_id + ".json")
    with open(rpath, "w", encoding="utf-8") as f:      # 与 record 同步双写 run 文件
        json.dump(run, f, ensure_ascii=False, indent=2)
    null_n = sum(1 for c in cleaned.values() if c["geo_score"] is None)
    print("geo 打分已写回 run %s: %d/%d 条(缺席 null=%d,重打 %d)→ %s"
          % (run_id, len(cleaned), len(run["results"]), null_n, rescored, rpath))
    for w in warnings:
        print("  [!] %s" % w)
    vals = [c["geo_score"] for c in cleaned.values() if c["geo_score"] is not None]
    if vals:
        mean = sum(vals) / len(vals)
        print("  本 run geo_score 均值=%.1f(scored=%d;null 缺席不入均值)" % (mean, len(vals)))
        if mean > GEO_ANTI_INFLATION_MEAN:
            print("  [!] 均值>75: LLM 系统性打高分,复核是否虚高(rubric 反通胀纪律)")
    return 0


def aggregate_geo(panel, engine=None):
    """geo 扩展键聚合(rubric 输出层)。按引擎分列——跨引擎不合并是既定纪律
    (与 decay 脚注同源: 跨引擎相关仅 0.03-0.09)。geo_score=null(缺席)与无 geo
    键的旧 result 不入任何均值(缺席不是 0 分回答,是没有可打分的呈现)。"""
    per_engine = {}
    for run in panel.get("runs", []):
        if engine and run["engine"] != engine:
            continue
        agg = per_engine.setdefault(run["engine"], {"cells": 0, "scores": [],
                                                    "presence": Counter(),
                                                    "recommendation": Counter()})
        for r in run.get("results", {}).values():
            geo = r.get("geo")
            if not isinstance(geo, dict):
                continue
            agg["cells"] += 1
            agg["presence"][geo.get("presence", "(缺 presence)")] += 1
            if geo.get("recommendation"):
                agg["recommendation"][geo["recommendation"]] += 1
            gs = geo.get("geo_score")
            if isinstance(gs, (int, float)) and not isinstance(gs, bool):
                agg["scores"].append(float(gs))
    return {e: a for e, a in per_engine.items() if a["cells"]}


def render_geo_section(panel, engine=None):
    """report 的 geo 聚合节;无任何 geo 键时返回 [](旧面板整节不出现,向后兼容)。
    均值>75 → 反通胀提示行(rubric 九节: LLM 系统性打高分)。"""
    geo = aggregate_geo(panel, engine)
    if not geo:
        return []
    L = ["-- GEO 打分聚合(geo-scoring-rubric 写回;按引擎分列不合并;null 缺席不入均值)--"]
    for eng in sorted(geo):
        agg = geo[eng]
        pres = ", ".join("%s=%d" % (p, agg["presence"][p])
                         for p in GEO_PRESENCE if agg["presence"].get(p))
        L.append("  %-12s geo cells=%d scored=%d presence: %s"
                 % (eng, agg["cells"], len(agg["scores"]), pres or "(无)"))
        if agg["scores"]:
            mean = sum(agg["scores"]) / len(agg["scores"])
            bands = [0] * len(GEO_SCORE_BANDS)
            for s in agg["scores"]:
                for i, (lo, hi) in enumerate(GEO_SCORE_BANDS):
                    if s <= hi or i == len(GEO_SCORE_BANDS) - 1:
                        bands[i] += 1
                        break
            L.append("    geo_score 均值=%.1f 分布: %s" % (
                mean, " ".join("%d-%d:%d" % (lo, hi, bands[i])
                               for i, (lo, hi) in enumerate(GEO_SCORE_BANDS))))
            if mean > GEO_ANTI_INFLATION_MEAN:
                L.append("    [!] 均值>75: LLM 系统性打高分,复核是否虚高(rubric 反通胀纪律)")
        recs = ", ".join("%s=%d" % (r, agg["recommendation"][r])
                         for r in GEO_RECOMMENDATIONS if agg["recommendation"].get(r))
        if recs:
            L.append("    recommendation: %s" % recs)
    L.append("  [i] geo 是分析层扩展键: 不进 coverage/share/diff/signals 口径"
             "(采集层只读 state/mentioned/cited;diff 不因 geo 键变化触发信号)")
    return L


# ---------- CLI / 自测 ----------

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("init", help="建立 panel.json")
    p.add_argument("--brand", required=True)
    p.add_argument("--prompts", default="",
                   help="prompt 列表 CSV(单列,可带表头;产出旧字符串形态)")
    p.add_argument("--prompts-file", default="",
                   help="prompt 库文件(markdown 表格/带表头 CSV/纯文本一行一条,"
                        "templates/research/prompt-bank.md 形态;产出对象形态)")
    p.add_argument("--stage-mix", action="store_true",
                   help="打印 stage 配方建议(Scrunch 官方: 5 awareness+3 consideration+2 decision)")
    p.add_argument("--persona-fanout", default="",
                   help='core query,如 "best CRM for small business";配 --personas 生成前缀注入变体')
    p.add_argument("--personas", default="", help="persona 列表,逗号分隔(如 CMO,Founder,SEO Lead,PMM)")
    p.add_argument("--aliases", default="", help="品牌别名,逗号分隔")
    p.add_argument("--domain", default="", help="品牌主域(用于 citation share)")
    p.add_argument("--competitors", default="",
                   help="追踪竞品域,逗号分隔(用于 SoV 分母;不设则 SoV=N/A)")
    p.add_argument("--engines", default="", help="逗号分隔,默认 chatgpt,perplexity,gemini,copilot,claude,grok")
    p.add_argument("--panel", default="panel.json")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("record", help="记录一次采样运行")
    p.add_argument("--engine", required=True)
    p.add_argument("--file", required=True, help="run.csv(prompt,mentioned,cited,cited_urls[,state][,rank])")
    p.add_argument("--run-id", default="")
    p.add_argument("--date", default="")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_record)
    p = sub.add_parser("report", help="输出面板报告")
    p.add_argument("--engine", default=None)
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_report)
    p = sub.add_parser("diff", help="两组 run 配对对比(文件路径或 run_id;含 signals 节)")
    p.add_argument("run1")
    p.add_argument("run2")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_diff)
    p = sub.add_parser("decay", help="citation decay 判定(Profound 官方方法论)")
    p.add_argument("--metric", default="cited", choices=("cited", "mentioned"),
                   help="序列取值(默认 cited=被引)")
    p.add_argument("--engine", default=None, help="只判定单引擎(分引擎独立判定是硬规则)")
    p.add_argument("--json", action="store_true", help="输出 JSON(默认 markdown)")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_decay)
    p = sub.add_parser(
        "score", help="geo 打分写回(geo-scoring-rubric;校验后写 results.<prompt>.geo)")
    p.add_argument("--run", default="", help="目标 run_id(与 --last 二选一)")
    p.add_argument("--last", action="store_true", help="写回最近一条 run")
    p.add_argument("--scores", default="",
                   help="scores.json: {prompt: {geo_score,presence,position,sentiment,"
                        "recommendation,competitors,risks}}(agent 按 rubric 打好的分)")
    p.add_argument("--rubric", action="store_true",
                   help="打印 rubric 压缩判定要点后退出(代码内常量,不读 md,standalone)")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_score)
    return ap


def _self_test():
    tmp = tempfile.mkdtemp(prefix="citation_panel_")
    panel_path = os.path.join(tmp, "panel.json")
    prompts_csv = os.path.join(tmp, "prompts.csv")
    with open(prompts_csv, "w", encoding="utf-8") as f:
        f.write("prompt\nbest crm for small business\ncrm 软件对比\nhelpdesk software\n")
    args = build_parser().parse_args(
        ["init", "--brand", "Acme", "--domain", "acme.ai", "--prompts", prompts_csv,
         "--panel", panel_path])
    assert cmd_init(args) == 0
    panel = load_panel(panel_path)
    assert panel["prompts"] == ["best crm for small business", "crm 软件对比", "helpdesk software"]
    assert os.path.isdir(os.path.join(tmp, "runs"))

    P1, P2, P3 = panel["prompts"]
    runs = [
        {"engine": "chatgpt", "rows": [
            (P1, "1", "1", "https://acme.ai/guide;https://www.comp.com/x", ""),
            (P2, "1", "0", "", ""),
            (P3, "0", "0", "", "failed")]},
        {"engine": "chatgpt", "rows": [
            (P1, "0", "0", "", ""),
            (P2, "1", "1", "https://acme.ai/pricing;https://docs.other.org/a", ""),
            (P3, "0", "0", "", "no_answer")]},
        {"engine": "perplexity", "rows": [
            (P1, "1", "1", "https://acme.ai/g2", ""),
            (P2, "0", "0", "", ""),
            (P3, "0", "0", "", "")]},
    ]
    for i, spec in enumerate(runs, 1):
        path = os.path.join(tmp, "run%d.csv" % i)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["prompt", "mentioned", "cited", "cited_urls", "state"])
            for row in spec["rows"]:
                w.writerow(row)
        rc = cmd_record(build_parser().parse_args(
            ["record", "--engine", spec["engine"], "--file", path,
             "--panel", panel_path, "--date", "2026-10-0%dT00:00:00" % i]))
        assert rc == 0

    panel = load_panel(panel_path)
    assert len(panel["runs"]) == 3
    stats = compute_stats(panel)
    # 五状态: cited_brand=3, name_only=1, failed=1, no_answer=1, brand_absent=3
    assert stats["cells"] == 9
    assert stats["state_counts"]["cited_brand"] == 3
    assert stats["state_counts"]["name_only_mention"] == 1
    assert stats["state_counts"]["failed"] == 1
    assert stats["state_counts"]["no_answer"] == 1
    assert stats["state_counts"]["brand_absent"] == 3
    # coverage: Σmentioned=4 / 成功=9-1=8 = 50.0%
    assert stats["denominator"] == 8 and stats["mentioned_sum"] == 4
    assert abs(stats["coverage"] - 0.5) < 1e-9
    # citation share: 品牌被引 3 / 去重域名总数 5 = 60%
    assert stats["brand_hits"] == 3 and stats["domain_total"] == 5
    assert abs(stats["share"] - 0.6) < 1e-9
    # Wilson: P1 n=3 k=2 → p=2/3, w=√(p(1-p)/3)≈0.272,CI 跨 0.5 → unstable
    k, n, p, lo, hi, unstable = stats["stability"][P1]
    assert (k, n) == (2, 3) and unstable and lo < 0.5 < hi
    # P2 n=3 k=2 同样 unstable;P3 n=2 不足 3 次,不报
    assert stats["stability"][P2][0] == 2 and P3 not in stats["stability"]
    # wilson 公式自检
    p, lo, hi, uns = wilson_ci(2, 3)
    w = math.sqrt((2 / 3) * (1 / 3) / 3)
    assert abs(hi - min(1.0, 2 / 3 + Z * w)) < 1e-12

    report = render_report(panel, stats)
    assert "五状态分类" in report and "50.0%" in report and "60.0%" in report
    assert "样本太小" in report and "掷硬币" in report

    d = diff_runs(panel["runs"][0], panel["runs"][1])
    assert sorted(d["paired"]) == [P1, P2]          # P3 在 run1 为 failed → 排除
    assert d["new_mentions"] == [] and d["disappeared"] == [P1]
    assert d["excluded"]["missing_in_a"] == 1
    d2 = diff_runs(panel["runs"][1], panel["runs"][2])
    assert d2["new_mentions"] == [P1] and d2["disappeared"] == [P2]

    # cited=1 但 mentioned=0 → 纠正为 mentioned=1
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("prompt,mentioned,cited,cited_urls\n%s,0,1,https://acme.ai/x\n" % P1)
    res, warns = read_run_csv(bad, panel)
    assert res[P1]["mentioned"] == 1 and res[P1]["state"] == "cited_brand" and warns
    # registrable_domain
    assert registrable_domain("https://www.acme.co.uk/a?b=1") == "acme.co.uk"
    assert registrable_domain("https://docs.other.org/x") == "other.org"

    # ---- v2 扩展(详细用例见 tests/test_citation_decay.py) ----
    # prompts 对象化: 旧字符串自动升级;对象字段规范化
    assert prompt_obj("旧字符串") == {"text": "旧字符串", "tags": []}
    o = prompt_obj({"text": "x", "stage": "Awareness ", "tags": "a;b", "branded": "yes",
                    "topic": "crm"})
    assert o["stage"] == "awareness" and o["tags"] == ["a", "b"] and o["branded"] is True
    # signals: fingerprint 稳定;|Δ|≥5pp 且 n≥10 门限
    fp = signal_fingerprint("mention", "chatgpt", "(整体)")
    assert fp == signal_fingerprint("mention", "chatgpt", "(整体)") and len(fp) == 10
    sig_panel = {"brand": "Acme", "domain": "acme.ai",
                 "prompts": ["p%d" % i for i in range(12)], "engines": ["chatgpt"],
                 "aliases": [], "runs": []}
    ra = {"engine": "chatgpt", "date": "2026-10-01T00:00:00",
          "results": {"p%d" % i: {"state": "name_only_mention", "mentioned": 1, "cited": 0,
                                  "cited_urls": []} for i in range(12)}}
    rb = {"engine": "chatgpt", "date": "2026-10-08T00:00:00",
          "results": {"p%d" % i: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                                  "cited_urls": []} for i in range(12)}}
    sig = diff_signals(ra, rb, diff_runs(ra, rb), sig_panel)
    assert len(sig["signals"]) == 1 and sig["signals"][0]["delta_pp"] == -100.0
    assert sig["signals"][0]["n"] == 12 and sig["disappeared_ranked"]
    # decay: 明确掉半序列 → decayed,半衰=peak 后首触 ≤50%peak 且 14 天无反弹
    d0 = datetime(2026, 1, 1)
    samples = [(d0 + timedelta(days=2 * i), 1.0 if i < 10 else 0.0) for i in range(23)]
    cell = eval_decay_cell(samples, panel_start=d0)
    assert cell["status"] == "decayed" and cell["half_life_days"] == 14, cell
    assert cell["peak"] == 1.0 and cell["days_to_half"] == 0
    # 指标族: 无竞品名单 → SoV=N/A;source_visibility 有分母
    st2 = compute_stats({**panel, "competitors": []})
    assert st2["sov"] is None and st2["win_rate"] is None
    assert st2["source_visibility"] is not None and st2["answers"] == 7
    st3 = compute_stats({**panel, "competitors": ["other.org"]})
    assert abs(st3["sov"] - 3 / (3 + 1)) < 1e-9   # other.org 在 1 个 cell 被引 → 3/4

    # ---- geo 打分写回(详细用例见 tests/test_geo_writeback.py) ----
    errs, warns = [], []
    g = validate_geo({"geo_score": 72, "presence": "name_only_mention",
                      "position": {"absolute_rank": 2, "mentions": 1,
                                   "first_occurrence_pct": 40},
                      "sentiment": 60, "recommendation": "recommended"},
                     "P1", {"state": "name_only_mention"}, errs, warns)
    assert g["geo_score"] == 50 and not errs       # 仅 1 次提及 → 硬 cap≤50 封顶
    g = validate_geo({"geo_score": 45, "presence": "echo_only",
                      "recommendation": "absent"}, "P2", {"state": "brand_absent"},
                     errs, warns)
    assert g["geo_score"] == 10                    # echo_only → 硬 cap≤10
    g = validate_geo({"geo_score": 90, "presence": "cited_brand", "sentiment": 85,
                      "position": {"absolute_rank": 3, "mentions": 4},
                      "recommendation": "top_pick"}, "P3", {"state": "cited_brand"},
                     errs, warns)
    assert g["recommendation"] == "honorable_mention"   # top_pick 无 #1 佐证 → 降级
    g = validate_geo({"geo_score": 88, "presence": "cited_brand", "sentiment": 90,
                      "position": {"absolute_rank": 1, "mentions": 3},
                      "recommendation": "top_pick"}, "P4", {"state": "cited_brand"},
                     errs, warns)
    assert g["recommendation"] == "top_pick" and g["geo_score"] == 88   # 有佐证不降级
    assert validate_geo({"geo_score": 50, "presence": "cited_brand",
                         "recommendation": "neutral", "extra": 1},
                        "PX", {"state": "cited_brand"}, errs, []) is None
    assert errs and "未知字段" in errs[-1]         # 白名单外字段 → 硬拒绝
    geo_run = {"engine": "chatgpt", "results": {
        "a": {"state": "cited_brand", "mentioned": 1, "cited": 1, "cited_urls": [],
              "geo": {"geo_score": 80, "presence": "cited_brand",
                      "recommendation": "top_pick"}},
        "b": {"state": "brand_absent", "mentioned": 0, "cited": 0, "cited_urls": [],
              "geo": {"geo_score": None, "presence": "brand_absent",
                      "recommendation": "absent"}}}}
    sec = render_geo_section({"runs": [geo_run]})
    assert any("geo cells=2 scored=1" in x for x in sec) and any("均值=80.0" in x for x in sec)
    assert any("反通胀" in x for x in sec)         # 均值>75 → 反通胀提示行
    print("[self-test] PASS citation_panel(9 cells, coverage=62.5%, share=60.0%, "
          "wilson unstable 案例, 配对 diff, cited/mentioned 纠正; "
          "v2: prompts 对象化/signals/decay 半衰/指标族; "
          "v3: geo 写回/硬 cap 机检/top_pick 佐证降级/反通胀聚合)")


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "self_test", False):
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL citation_panel")
            return 1
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
