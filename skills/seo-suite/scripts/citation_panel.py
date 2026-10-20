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
                     Wilson 95% score interval(z=1.96,
                     (p̂+z²/2n ± z√(p̂(1-p̂)/n + z²/4n²))/(1+z²/n);
                     区间跨 0.5 → unstable;k=0/n 时区间宽度非零——旧 Wald 近似
                     CI=p±z·√(p(1-p)/n) 在 0/全命中时宽 0,会把掷硬币样本误判 stable)
  prompts < 10     = 样本太小,结论只能当方向

子命令:
  init    --brand X (--prompts p.csv | --prompts-file prompt-bank.md)
          [--aliases a,b] [--domain example.com] [--engines e1,e2]
          [--competitors a.com,b.com]      # SoV 分母的追踪竞品域
          [--stage-mix]                    # 打印 5 awareness+3 consideration+2 decision 建议配方
          [--persona-fanout "core query" --personas CMO,Founder]
          [--panel PATH] [--force]
  record  --engine chatgpt --file run.csv [--run-id ID] [--date ISO] [--panel PATH]
  record  --from-referral referral.json [--panel PATH]
          # R6 竞品 Ryze 一方数据线对齐: 吃 ai_referral_log --as-panel-import 导出
          #   (纯 JSON / 整 stdout 重定向均可,按 marker 行切取)→ 建 source=referral
          #   run(engine 对齐面板六引擎,未知引擎/域→other+警告);referral 轨与采样轨
          #   在 report 分开列,不加权混合(证据分级: referral=下界 real,采样=est)
  report  [--engine E] [--panel PATH]      # 含指标族节: SoV/win_rate/citation_rate/
                                           #   brand_visibility vs source_visibility(Peec 官方公式)
                                           #   + referral 流量轨(有 source=referral run 时)
  diff    RUN1 RUN2 [--panel PATH]         # RUN 为 run 文件路径或面板内 run_id
                                           # 新增 signals 节(Scrunch 口径): |Δ|≥5pp 且配对 n≥10
                                           #   才报;fingerprint=sha1(metric+engine+topic)[:10];
                                           #   disappeared 按对 delta 的贡献排序
  decay   [--metric cited|mentioned] [--engine E] [--json] [--panel PATH]
          # citation decay 判定(Profound 官方方法论,2026-09 88.3 万页研究;阈值抄自官方):
          # 7 点滚动均值(官方 14 天,采样密度低取 7)/ 资格闸门 4 道 /
          # 半衰=peak 后平滑≤50%peak 且连续 14 天无反弹 / 状态机 5 态 / 重写队列
  decay-summary [--metric cited|mentioned] [--json] [--panel PATH]
          # R0-4 轻摘要(monitor.py 周检同源): 复用 decay 计算,--json 出单行
          #   {rewriting, decayed_count, per_engine}——rewriting=重写队列长度
          #   (decaying+decayed),decayed_count=已过半衰 cell 数,per_engine=分引擎计数
  score   (--run RUNID | --last) --scores scores.json [--panel PATH]
          # geo 打分写回(geo-scoring-rubric 五维打分卡,references/content/):
          #   agent 按卡语义打分 → 机检硬规则(硬 cap/枚举/top_pick 佐证/字段白名单/
          #   越界 clamp)→ 写回该 run 每条 result 的 geo 扩展键(panel.json 与
          #   runs/<id>.json 双写);硬违例整批原子拒绝;score --rubric 打印
          #   压缩判定要点(代码内常量,不读 md,standalone)
  triangulate --referral REF [--survey survey.csv] [--since D] [--until D] [--json]
          # 三源分歧度报告(R6 归因;同一品牌同期): referrer 日志(ai_referral_log
          #   输出/CSV/JSON)× 面板采样(窗口内 mention coverage)× 可选 survey
          #   (品牌提示回想%)→ 两两差(pp)+ 最大分歧源标注 + "referral 是下限"
          #   口径(kpi-definitions 对账纪律: 永不跨源求和,只读方向与分歧)

v4(借鉴 niubigeo,出处逐条标注 references/research/niubigeo-deep-read.md §3):
  N1 提及检测   record --answer-file ANSWER: URL 掩码+实体词表自动判定 mentioned/
                rank(引用链接里的域名不算正文提及;sentiment 恒 neutral);report 增
                提及检测标注节。旧 run.csv 口径不动,检测只填空缺/加扩展键。
  N2 指标切片   report 按 prompt.branded 分 branded_or_direct / organic_unbranded
                两栏(每指标 {numerator,denominator,value},分母=0 → null 永不报 0%)
                + 交叉错配计数;无 branded 标注按"prompt 含品牌名"自动判定,
                report --brand 可覆盖自动判定的品牌名(显式标注不受影响)。
  N5 意图冻结   init 冻结分母档案 panel['denominator_freeze'] 并校验 intents 非空;
                分母成员由档案(candidate_applicable≠False)决定,不由答案结果决定
                → coverage_frozen/sov_frozen 新口径;record 存每 run 冻结 hash,
                面板/run 与档案不一致时 report 警示分母漂移。
  N6 配对差分   record 存探针指纹 run['fingerprint'](engine+brand+prompt 集+规则
                版本);diff 增配对门: 只对同 prompt×engine 且同指纹的配对算 Δ,
                未配对单列不入 Δ;跨引擎/跨指纹强制标注"不可比"。

R6 referral 桥(竞品 Ryze 一方数据线对齐: GA4/GSC 式真实 AI-referral 流量
  即可见性证据,比 prompt 采样便宜且真实;规格 pipeline-completeness.md R6 竞品节):
  导出侧  ai_referral_log.py --as-panel-import(referrer 域→引擎映射 chatgpt.com→
          chatgpt 等、sessions=请求命中数、cited_urls=目标路径聚合,scope 标注
          下界 real 与采样 est 分轨)
  导入侧  record --from-referral FILE → 每引擎一条 source="referral" run
          (results 恒空——referral 轨不伪造 prompt cell);engine 对齐面板六引擎,
          未知引擎/域映射 other 并警告;采样 run 显式标 source="sampling"
  兼容    旧面板 run 无 source 字段 → 视为采样 run,一切旧口径不变;
          compute_stats 排除 referral run(coverage/share/stability/decay 只算采样);
          report 的 referral 轨与采样轨分开列,不加权混合(证据分级纪律)

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
  python3 ai_referral_log.py access.log --as-panel-import > referral.json
  python3 citation_panel.py record --from-referral referral.json   # 一方 referral 轨(R6)
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

# ---------- R6 referral 桥(竞品 Ryze 一方数据线对齐: AI-referral 流量即可见性证据) ----------
# 面板 run 增加 source 字段: "referral"=一方 referral 日志导入(下界 real 证据),
# "sampling"=prompt 采样(est);旧 run 无 source → 视为 sampling(向后兼容)。
# 证据分级纪律: referral 轨与采样轨分开列、不加权混合(与 triangulate
# "永不跨源求和"同路数);referral run 不伪造 prompt cell(results 恒空)。
REFERRAL_SOURCE = "referral"
SAMPLING_SOURCE = "sampling"
REFERRAL_MARKER_HINT = "referral panel import"   # ai_referral_log --as-panel-import 标记行关键词
REFERRAL_SCOPE_NOTE = ("下界(real): App 内打开常不带 referrer,真实引流 ≥ 此数;"
                       "sessions=请求命中数(未做会话化)")

# ---------- v2 扩展常数(出处见各节注释) ----------
# prompts 对象化(references/research/borrow-specs.md B3;+ v4 N5 意图档案字段)
PROMPT_FIELDS = ("text", "topic", "tags", "stage", "branded", "region", "lang",
                 "intents", "candidate_applicable", "recommendation_applicable")
PROMPT_COL_KEYS = ("prompt", "prompts", "query", "text", "提示词", "模板", "整句",
                   "prompt 句", "模板(整句)")          # 命中任一列名 → 该列为 prompt 文本
STAGE_COLS = ("stage", "阶段", "漏斗")                  # prompt-bank.md 主矩阵的漏斗列
STAGE_ALIASES = {"认知": "awareness", "比较": "consideration", "决策": "decision",
                 "转化": "conversion", "忠诚": "loyalty",
                 "awareness": "awareness", "consideration": "consideration",
                 "decision": "decision", "conversion": "conversion", "loyalty": "loyalty"}
# persona 前缀表(本套件口径,参考 Scrunch 公开文章)+ 固定后缀
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

# ---------- v4 扩展常数(出处: references/research/niubigeo-deep-read.md §3) ----------
MENTION_RULES_VERSION = "mask-url-v1"      # N1 提及检测规则版本(进 N6 指纹)
TARGETING_RULES_VERSION = "targeting-v1"   # N2 branded 自动判定规则版本
DENOM_FREEZE_VERSION = "denom-freeze-v1"   # N5 分母冻结协议版本
DIFF_PAIRING_VERSION = "pairing-v1"        # N6 配对差分协议版本
# N1 句子边界集(深读原文口径 ".。!?!?\n",ASCII+CJK 标点+换行)
SENTENCE_BOUNDARIES = set(".。!?!?\n")
# N1 URL 掩码正则(stdlib 近似 linkify-it;三选一):
#   1) scheme://…   2) www.…   3) 裸域+路径(裸域无路径视为行文提及不掩[推断])
URL_TOKEN_RE = re.compile(
    r"(?:(?:https?|ftp)://|www\.)[^\s<>\"'\)\]]+"
    r"|[A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9][A-Za-z0-9-]+)+/\S*")
# N5 prompt 意图档案字段(prompts 对象化新增,全部可选,旧数据不受影响)
INTENT_FIELDS = ("intents", "candidate_applicable", "recommendation_applicable")
# N2 targeting 切片标签(品牌词与中性词永不混进同一个分)
TARGETING_LABELS = ("branded_or_direct", "organic_unbranded")

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


def atomic_write_json(path, obj):
    """原子写 JSON(R5 GEO 修复): 同目录 tempfile 落盘 + fsync + os.replace——
    半写不留盘,进程中断/磁盘满时不会留下截断的 panel.json 或 runs/<id>.json。
    tempfile 早已 import 而未用,此处启用;失败时清理临时文件后原样抛出。"""
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def save_panel(path, panel):
    atomic_write_json(path, panel)


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
        # v4(niubigeo-deep-read.md N5)意图档案字段: 全部可选,仅在输入给出时携带
        raw_intents = p.get("intents")
        if raw_intents is not None:
            lst = raw_intents if isinstance(raw_intents, list) else re.split(r"[;,，、]", str(raw_intents))
            ints = [str(x).strip() for x in lst if str(x).strip()]
            if ints:                     # 空档案不落键(init 校验按"带 profile 无 intents"拒绝)
                obj["intents"] = ints
        for f in ("candidate_applicable", "recommendation_applicable"):
            if p.get(f) is not None:
                obj[f] = (p[f] if isinstance(p[f], bool)
                          else str(p[f]).strip().lower() in ("1", "true", "yes", "y", "是"))
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
    if not text:                               # prompt 列为空 → 不拿编号等别的列顶替(B58)
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
    # v4(niubigeo-deep-read.md N5)意图档案列(intents/candidate/recommendation_applicable)
    if m.get("intents", "").strip():
        obj["intents"] = [t.strip() for t in re.split(r"[;,，、]", m["intents"]) if t.strip()]
    for f in ("candidate_applicable", "recommendation_applicable"):
        if m.get(f, "").strip():
            obj[f] = m[f].strip().lower() in ("1", "true", "yes", "y", "是")
    return obj


def _plain_prompt_text(s):
    """纯文本行 → prompt 文本(剥 -/*/+/1. 列表标记)。"""
    t = re.sub(r"^[-*+]\s+", "", s)
    t = re.sub(r"^\d+[.、)]\s+", "", t)
    return t.strip()


def read_prompts_file(path):
    """templates/research/prompt-bank.md 形态 → prompt 对象列表。
    契约(B58 修,2026-10-21):
    - Markdown 表格:每张表按自己的表头解析(表与表之间以非表格行分隔),只收表头含
      prompt 列(prompt/text/query/提示词/模板/模板(整句)…)的表的该列单元格,其余列
      (漏斗→stage、topic/tags/branded/region/lang…)作元数据;表头行、分隔行 |---|、
      没有 prompt 列的表(persona 前缀表、定义表)不收。文件里只要有一张带 prompt 列
      的表,标题、正文句子、列表条目一律不算 prompt。
      (修前:只看第一张表的表头,其余表的表头/persona 行和全部正文句子都被当 prompt,
      整份 prompt-bank.md 解析出 72 条;修后 22 条 = 主矩阵 20 + 风险组 2。)
    - 无带 prompt 列的表:带表头 CSV(首列为 prompt/text 等),或纯文本一行一条
      (# 标题、<!-- 注释、> 引用行跳过;- / * / 1. 列表标记剥除)。
    按 text 去重。"""
    with open(path, encoding="utf-8") as f:
        raw_lines = f.read().splitlines()
    tables, plain_lines, cur = [], [], None
    for line in raw_lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 2:
            cells = [c.strip() for c in s[1:-1].split("|")]
            if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue                       # markdown 分隔行
            if cur is None:
                cur = []
                tables.append(cur)
            cur.append(cells)
            continue
        cur = None                             # 非表格行 → 当前表结束
        if s and not s.startswith(("#", "<", ">")):
            plain_lines.append(s)
    out = []
    prompt_tables = []
    for rows in tables:
        header = [c.lower() for c in rows[0]]
        if any(h in PROMPT_COL_KEYS for h in header if h):
            prompt_tables.append((header, rows[1:]))
    if prompt_tables:
        for header, body in prompt_tables:
            for cells in body:
                obj = _row_to_prompt(cells, header)
                if obj:
                    out.append(obj)
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
    """前缀注入变体清单(本套件口径,参考 Scrunch 的 persona 变换思路): 前缀+core query+固定后缀。
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
            # v4: 连 N5 意图档案字段一起继承(同 core query 的变体分母资格一致)
            for f in ("topic", "stage", "branded", "region", "lang",
                      "intents", "candidate_applicable", "recommendation_applicable"):
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
    # v4(niubigeo-deep-read.md N5)意图档案校验非空: 带 intents/candidate_applicable/
    # recommendation_applicable 任一字段的 prompt,intents 必须非空——冻结档案不许
    # 空标签进基线(防分母成员资格无据可查)
    bad_intents = []
    for e in prompts:
        if not isinstance(e, dict):
            continue
        if any(e.get(f) is not None for f in INTENT_FIELDS) and not prompt_obj(e).get("intents"):
            bad_intents.append(prompt_text(e))
    if bad_intents:
        print("错误: %d 条 prompt 带意图档案字段但 intents 为空(niubigeo-deep-read.md "
              "N5: 基线冻结不许空标签): %s" % (len(bad_intents), "; ".join(bad_intents[:3])),
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
    # v4(niubigeo-deep-read.md N5)意图冻结分母: init 时点冻结 eligible 集(此后只读
    # 不静默重写;prompt 增删/改措辞造成的漂移由 report 警示,不自动吸收)
    frz = denominator_freeze(panel)
    panel["denominator_freeze"] = {
        "version": frz["version"], "freeze_hash": frz["freeze_hash"],
        "eligible_prompts": frz["eligible_prompts"],
        "ineligible_prompts": frz["ineligible_prompts"],
        "frozen_at": datetime.now().isoformat(timespec="seconds")}
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


def read_run_csv(path, panel, explicit=None):
    """run.csv → ({prompt: result}, warnings)。
    explicit(v4 N1,可选 dict)回填 {prompt: 是否人工显式填了 mentioned/state}
    —— --answer-file 自动判定只覆盖非显式 cell,人工列永远优先。"""
    warnings, results = [], {}
    known = {prompt_text(p) for p in panel.get("prompts", [])}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            prompt = (row.get("prompt") or row.get("query") or "").strip()
            if not prompt:
                continue
            results[prompt] = normalize_result(row, warnings, prompt)
            if explicit is not None:
                explicit[prompt] = bool((row.get("mentioned") or "").strip()
                                        or (row.get("state") or "").strip())
            if prompt not in known:
                warnings.append("prompt 不在面板 prompts 列表中: %s" % prompt)
    return results, warnings


# ---------- R6 referral 桥导入: record --from-referral(一方 AI-referral 日志) ----------

def _slice_marker_json(raw):
    """混合输出(文本报告 + marker 行 + JSON)→ marker 行之后的 JSON 文本。
    ai_referral_log --as-panel-import 的整 stdout 重定向文件按 marker 定位切取;
    无 marker → None(调用方回退整文件直解)。"""
    lines = raw.splitlines()
    for i, ln in enumerate(lines):
        if REFERRAL_MARKER_HINT in ln:
            for j in range(i + 1, len(lines)):
                s = lines[j].lstrip()
                if s.startswith("{") or s.startswith("["):
                    return "\n".join(lines[j:])
            return ""                      # 有 marker 无 JSON 体(调用方报解析错)
    return None


def load_referral_import(path):
    """--from-referral FILE → (records, warnings)。
    吃 ai_referral_log --as-panel-import 的三种形态: ① 整 stdout 重定向(文本
    报告 + marker 行 + JSON,按 marker 切取);② 纯 wrapper
    {"source":"referral","records":[…]} 或裸 records 列表;③ 单条记录对象。
    每条 {date, engine, sessions, cited_urls};无效条目跳过并计 warning,
    一条有效条目都没有 → ValueError(整文件拒绝,不落盘)。"""
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read()
    except OSError as e:
        raise ValueError("无法读取 --from-referral %s: %s" % (path, e))
    if not raw.strip():
        raise ValueError("--from-referral %s 为空文件" % path)
    body = _slice_marker_json(raw)
    if body is None:
        body = raw
    data = None
    try:
        data = json.loads(body)
    except ValueError:
        try:
            data = json.loads(raw)         # 无 marker 纯文件兜底再试一次
        except ValueError as e:
            raise ValueError("--from-referral JSON 解析失败(需 ai_referral_log "
                             "--as-panel-import 输出,或 {date,engine,sessions,"
                             "cited_urls} 记录列表): %s" % e)
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        items = data["records"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "engine" in data:
        items = [data]
    else:
        raise ValueError("--from-referral 需 records 列表(wrapper/裸列表)或单条 "
                         "{date,engine,sessions,cited_urls} 对象")
    records, warnings = [], []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            warnings.append("referral 记录 %d 非对象,已跳过: %r" % (i + 1, it))
            continue
        eng = str(it.get("engine") or "").strip().lower()
        sess = it.get("sessions")
        if not eng or isinstance(sess, bool) or not isinstance(sess, (int, float)) \
                or sess < 0:
            warnings.append("referral 记录 %d 缺 engine/sessions 或 sessions 非负数,"
                            "已跳过: %r" % (i + 1, it))
            continue
        urls = it.get("cited_urls") or []
        if not isinstance(urls, list):
            warnings.append("referral 记录 %d cited_urls 非列表,按空处理: %r"
                            % (i + 1, it))
            urls = []
        records.append({
            "date": str(it.get("date") or datetime.now().isoformat(timespec="seconds")),
            "engine": eng,
            "sessions": (int(sess) if float(sess).is_integer() else float(sess)),
            "cited_urls": [str(u) for u in urls]})
    if not records:
        raise ValueError("--from-referral 无有效记录(警告 %d 条): %s"
                         % (len(warnings), "; ".join(warnings[:3]) or "(空 records)"))
    return records, warnings


def cmd_record_referral(args):
    """record --from-referral(R6 Ryze 一方数据线对齐): 一方 AI-referral 日志 →
    source=referral run。每引擎记录一条 run,results 恒空(referral 轨不伪造
    prompt cell);engine 对齐面板六引擎,未知引擎/域映射 other 并警告;
    panel.json 与 runs/<id>.json 双写(与采样 record 同纪律,原子写)。"""
    try:
        records, warnings = load_referral_import(args.from_referral)
    except ValueError as e:
        print("错误: %s" % e, file=sys.stderr)
        return 1
    panel = load_panel(args.panel)
    existing = {r.get("run_id") for r in panel.get("runs", [])}
    known_engines = set(DEFAULT_ENGINES) | set(panel.get("engines") or [])
    created = []
    for rec in records:
        eng = rec["engine"]
        if eng not in known_engines:       # 未知引擎/域 → other + 警告(六引擎对齐)
            warnings.append("未知引擎/域 %r → 映射 other(referral 轨;面板六引擎: %s)"
                            % (rec["engine"], ",".join(DEFAULT_ENGINES)))
            eng = "other"
        if eng not in panel["engines"]:
            panel["engines"].append(eng)
        run_id = "referral-%s-%s" % (eng, re.sub(r"[^\w.-]+", "-", rec["date"]))
        base, n = run_id, 2
        while run_id in existing:
            run_id = "%s-%d" % (base, n)
            n += 1
        existing.add(run_id)
        run = {"run_id": run_id, "engine": eng, "date": rec["date"],
               "brand": panel["brand"], "source": REFERRAL_SOURCE, "results": {},
               "referral": {"sessions": rec["sessions"],
                            "cited_urls": rec["cited_urls"],
                            "scope": REFERRAL_SCOPE_NOTE}}
        panel["runs"].append(run)
        created.append(run)
    save_panel(args.panel, panel)
    rdir = runs_dir_for(args.panel)
    os.makedirs(rdir, exist_ok=True)
    for run in created:
        atomic_write_json(os.path.join(rdir, run["run_id"] + ".json"), run)
    print("已导入 referral runs: %d 条(engine 记录 %d,Σsessions=%d;"
          "source=referral,下界 real 证据)→ %s"
          % (len(created), len(records),
             sum(r["referral"]["sessions"] for r in created), args.panel))
    for run in created:
        print("  run %s engine=%s date=%s sessions=%s cited_urls=%d"
              % (run["run_id"], run["engine"], run["date"],
                 run["referral"]["sessions"], len(run["referral"]["cited_urls"])))
    for w in warnings:
        print("  [!] %s" % w)
    print("  [i] report 中 referral 轨与采样轨分开列,不加权混合(证据分级纪律;"
          "referral=下界 real,采样=est)")
    return 0


def cmd_record(args):
    if getattr(args, "from_referral", None):
        return cmd_record_referral(args)     # R6: 一方 referral 轨导入
    if not (args.engine and args.file):
        print("错误: record 需要 --engine+--file(采样 run)或 "
              "--from-referral referral.json(一方 referral 轨)", file=sys.stderr)
        return 1
    panel = load_panel(args.panel)
    if args.engine not in panel["engines"]:
        panel["engines"].append(args.engine)
        print("[i] 引擎 %s 不在面板引擎列表,已追加" % args.engine)
    explicit = {} if args.answer_file else None
    results, warnings = read_run_csv(args.file, panel, explicit=explicit)
    if not results:
        print("错误: %s 中没有有效行(需 prompt,mentioned,cited,cited_urls 列)" % args.file,
              file=sys.stderr)
        return 1
    # v4(niubigeo-deep-read.md N1)URL 掩码提及检测: --answer-file 给出纯文本回答时
    # 自动判定 mentioned/rank(只填空缺,人工显式列永远优先并告警差异)
    if args.answer_file:
        try:
            answers = load_answers(args.answer_file)
        except (OSError, ValueError) as e:
            print("错误: 读取 --answer-file 失败: %s" % e, file=sys.stderr)
            return 1
        if not answers:
            print("错误: %s 中没有回答(需 prompt,answer 列 CSV 或 {prompt: 回答} JSON)"
                  % args.answer_file, file=sys.stderr)
            return 1
        for prompt, ans in answers.items():
            cell = results.get(prompt)
            if cell is None:
                warnings.append("answer-file 的 prompt 不在 run.csv,已忽略: %s" % prompt)
                continue
            if cell["state"] in ("failed", "no_answer"):
                warnings.append("state=%s 但 answer-file 有该 prompt 的回答文本,复核: %s"
                                % (cell["state"], prompt))
                continue
            det = detect_mentions(ans, panel)
            cell["mention_detection"] = det
            if det["mentioned"] != cell["mentioned"]:
                if explicit.get(prompt):
                    warnings.append("URL 掩码检测 mentioned=%d 与人工列 %d 不一致,"
                                    "以人工列为准(复核 answer-file): %s"
                                    % (det["mentioned"], cell["mentioned"], prompt))
                elif cell["cited"]:
                    # cited=1 蕴含 mentioned=1(面板口径: 引用即出现);掩码只测正文,
                    # 差异留在 detection 里作 cited_without_prose_mention 原料,面板值不动
                    pass
                else:
                    cell["mentioned"] = det["mentioned"]
                    cell["state"] = "name_only_mention" if det["mentioned"] else "brand_absent"
                    warnings.append("掩码检测自动填 mentioned=%d(answer-file): %s"
                                    % (det["mentioned"], prompt))
            if "rank" not in cell and det["rank_position"] is not None:
                cell["rank"] = det["rank_position"]    # 首现排位(品牌 vs 竞品域实体)
    date = args.date or datetime.now().isoformat(timespec="seconds")
    run_id = args.run_id or re.sub(r"[^\w.-]+", "-", "%s-%s" % (args.engine, date))
    existing = {r["run_id"] for r in panel["runs"]}
    base, n = run_id, 2
    while run_id in existing:
        run_id = "%s-%d" % (base, n)
        n += 1
    run = {"run_id": run_id, "engine": args.engine, "date": date,
           "brand": panel["brand"], "results": results,
           "source": SAMPLING_SOURCE}   # R6: 采样轨显式标注(旧 run 无 source 视为采样)
    # v4(niubigeo-deep-read.md N6/N5)run 时点快照: 探针指纹 + 分母冻结 hash
    run["fingerprint"] = run_fingerprint(run)
    run["denominator_freeze_hash"] = denominator_freeze(panel)["freeze_hash"]
    panel["runs"].append(run)
    save_panel(args.panel, panel)
    rdir = runs_dir_for(args.panel)
    os.makedirs(rdir, exist_ok=True)
    rpath = os.path.join(rdir, run_id + ".json")
    atomic_write_json(rpath, run)               # 原子写(与 panel.json 同纪律)
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
    """Wilson score interval 真公式(z=1.96):
    (p̂+z²/2n ± z√(p̂(1-p̂)/n + z²/4n²)) / (1+z²/n);区间跨 0.5 → unstable。
    R5 GEO 修复: 旧实现是 Wald 正态近似 CI=p±z·√(p(1-p)/n),k=0/n 时宽 0,
    零命中/全命中样本被误判 stable;真 Wilson 在 k=0 时上界>0(k=0,n=3 →
    上界≈0.5615)、k=n 时下界<1(k=3,n=3 → 下界≈0.4385),区间恒非零宽。
    判定逻辑不变(lo<0.5<hi 即区间与 0.5 线重叠 → unstable),只是换真 CI。"""
    if not n:
        return None
    p = k / n
    z2 = Z * Z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return p, lo, hi, (lo < 0.5 < hi)


def compute_stats(panel, engine=None, _per_engine=True, brand_override=None):
    # R6 referral 桥: referral run 不入采样指标(coverage/share/stability 只算采样轨,
    # 两轨分开列不加权混合);旧 run 无 source 字段 → 视为采样,行为不变
    runs = [r for r in panel.get("runs", [])
            if r.get("source") != REFERRAL_SOURCE
            and (not engine or r["engine"] == engine)]
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
    # ---- v4(N2)targeting 切片累积器: 品牌词与中性词永不混进同一个分 ----
    tgt = {lb: _new_targeting_slice() for lb in TARGETING_LABELS}
    tgt_basis = Counter()
    tgt_cache = {}
    _seen_prompts = []
    _pmap = {}                                   # text → 原始 prompt 对象(保 branded 等标注)
    for p in panel.get("prompts", []):
        t = prompt_text(p)
        if t not in _pmap:
            _pmap[t] = p
            _seen_prompts.append(t)
    # ---- v4(N5)意图冻结分母累积器: 成员=冻结档案 eligible 集,与答案结果无关 ----
    frz = denominator_freeze(panel)
    _elig = set(frz["eligible_prompts"])
    f_num = f_den = f_brand = f_comp = 0
    for run in runs:
        for prompt in run["results"]:
            if prompt not in _seen_prompts:
                _seen_prompts.append(prompt)   # 面板外 prompt 也按其文本归切片
    for t in _seen_prompts:
        lb, basis = _targeting_of(panel, _pmap.get(t, t), tgt_cache, brand_override)
        tgt[lb]["prompts"] += 1
        tgt_basis[basis] += 1
    for run in runs:
        for prompt, res in run["results"].items():
            cells += 1
            state_counts[res["state"]] += 1
            mentioned_sum += res["mentioned"]
            doms = {registrable_domain(u) for u in res.get("cited_urls", [])}
            doms.discard("")
            cited_urls_sum += len(res.get("cited_urls") or [])
            domain_total += len(doms)
            brand_hit = bool(brand_dom and brand_dom in doms)
            if brand_hit:
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
            # ---- v4(N2)切片累积(旧指标键不动) ----
            lb, _ = _targeting_of(panel, _pmap.get(prompt, prompt), tgt_cache,
                                  brand_override)
            sl = tgt[lb]
            sl["cells"] += 1
            if res["state"] != "failed":
                sl["denominator"] += 1
                sl["mentioned_sum"] += res["mentioned"]
                sl["cited_cells"] += res["cited"]
                if res["state"] != "no_answer":
                    sl["answers"] += 1
                if res["mentioned"] and not res["cited"]:
                    sl["mentioned_without_official_citation"] += 1
                det = res.get("mention_detection")
                if (isinstance(det, dict) and det.get("mentioned") == 0
                        and brand_hit):
                    sl["cited_without_prose_mention"] += 1
                if isinstance(rk, int) and rk > 0:
                    sl["rank_cells"] += 1
                    sl["wins"] += (rk == 1)
                if brand_hit:
                    sl["brand_hits"] += 1
                sl["comp_hits"] += sum(1 for d in doms if d in competitors)
            # ---- v4(N5)冻结分母累积(仅 eligible prompt 的 cell) ----
            if prompt in _elig and res["state"] != "failed":
                f_den += 1
                f_num += res["mentioned"]
                if brand_hit:
                    f_brand += 1
                f_comp += sum(1 for d in doms if d in competitors)
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
    # ---- v4(N2/N5)新口径键(旧键全部保留;分母=0 → value=None 永不报 0%) ----
    for sl in tgt.values():
        sl["mention_rate"] = metric_triple(sl["mentioned_sum"], sl["denominator"])
        sl["citation_rate"] = metric_triple(sl["cited_cells"], sl["answers"])
        sl["first_position_rate"] = metric_triple(sl["wins"], sl["rank_cells"])
        sl["share_of_voice"] = metric_triple(sl["brand_hits"],
                                             sl["brand_hits"] + sl["comp_hits"])
    stored_hash = (panel.get("denominator_freeze") or {}).get("freeze_hash")
    run_hash_drift = [r.get("run_id") for r in runs
                      if stored_hash and r.get("denominator_freeze_hash")
                      and r["denominator_freeze_hash"] != stored_hash]
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
            "visibility_gap_pp": gap_pp,
            # v4(N2)targeting 切片: branded_or_direct / organic_unbranded 两栏分报
            "targeting": {"labels": list(TARGETING_LABELS),
                          "rule": TARGETING_RULES_VERSION,
                          "brand_used": str(brand_override or panel.get("brand") or ""),
                          "basis_counts": dict(tgt_basis), "slices": tgt},
            # v4(N5)意图冻结分母: coverage_frozen/sov_frozen 只数 eligible prompt
            "frozen": {"version": DENOM_FREEZE_VERSION, "freeze_hash": frz["freeze_hash"],
                       "eligible_count": len(_elig),
                       "ineligible_prompts": frz["ineligible_prompts"],
                       "mention_rate": metric_triple(f_num, f_den),
                       "share_of_voice": metric_triple(f_brand, f_brand + f_comp),
                       "panel_freeze_stored": stored_hash,
                       "drift": bool(stored_hash is not None and stored_hash != frz["freeze_hash"]),
                       "run_hash_drift": run_hash_drift}}


def _pct(x):
    return "N/A" if x is None else "%.1f%%" % (100 * x)


def referral_summary(panel, engine=None):
    """source=referral runs → {engine: {runs, sessions, urls: Counter, dates: set}}。
    report referral 轨数据源——与采样轨分开聚合,不加权混合(证据分级纪律)。"""
    agg = {}
    for run in panel.get("runs", []):
        if run.get("source") != REFERRAL_SOURCE:
            continue
        if engine and run.get("engine") != engine:
            continue
        ref = run.get("referral") or {}
        a = agg.setdefault(run.get("engine") or "other",
                           {"runs": 0, "sessions": 0, "urls": Counter(),
                            "dates": set()})
        a["runs"] += 1
        sess = ref.get("sessions") or 0
        a["sessions"] += (sess if isinstance(sess, (int, float)) else 0)
        for u in ref.get("cited_urls") or []:
            a["urls"][str(u)] += 1
        d = str(run.get("date") or "")[:10]
        if d:
            a["dates"].add(d)
    return agg


def render_referral_section(panel, engine=None):
    """report 的 referral 轨节;无 source=referral run 时返回 [](旧面板整节不出现,
    向后兼容)。下界 real 证据,与采样轨分开列——不加权混合。"""
    agg = referral_summary(panel, engine)
    if not agg:
        return []
    L = ["-- referral 流量轨(source=referral;一方日志下界 real 证据,"
         "与采样轨分开列,不加权混合)--"]
    for eng in sorted(agg):
        a = agg[eng]
        top = " ".join("%s(%d)" % (u, c) for u, c in a["urls"].most_common(3))
        L.append("  %-12s runs=%-3d sessions=%-6d cited_urls=%-3d  top: %s"
                 % (eng, a["runs"], a["sessions"], len(a["urls"]), top or "-"))
    L.append("  [i] referral=下界(real): App 内打开常不带 referrer,真实引流 ≥ 此数;"
             "sessions 为请求命中数(未做会话化)")
    L.append("  [i] 采样轨 = prompt 采样(est);两轨证据分级,分开读取,永不合并或求和")
    return L


def render_report(panel, stats, engine=None):
    L = []
    L.append("== AI 可见性面板报告: %s ==" % panel["brand"])
    L.append("prompts=%d runs=%d cells=%d engines=%s"
             % (len(panel["prompts"]), stats["runs"], stats["cells"],
                ",".join(panel["engines"])))
    ref_sec = render_referral_section(panel, engine)   # R6: referral 轨(有才出现)
    if stats["runs"] == 0 and not ref_sec:
        L.append("尚无运行记录。先用 record 录入采样。")
        return "\n".join(L)
    if ref_sec:
        L.extend(ref_sec)
    if stats["runs"] == 0:                 # 只有 referral run: 采样轨缺,不崩不混
        L.append("-- 采样轨(prompt 采样,est): 无 runs --")
        L.append("  [i] 尚无采样 run;先用 record --engine --file 录入采样"
                 "(referral run 不充当采样证据)")
        return "\n".join(L)
    if ref_sec:                            # 双轨并存时给采样轨显式标签
        L.append("-- 采样轨(prompt 采样,est;以下指标只算采样 cell,"
                 "不含 referral runs)--")
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
    # v4(N1)提及检测标注节: 有 mention_detection 扩展键才出现(旧面板整节不出现)
    det_rows = mention_detection_rows(panel, engine)
    if det_rows:
        L.append("-- 提及检测(URL 掩码自动判定;niubigeo-deep-read.md N1;规则 %s) --"
                 % MENTION_RULES_VERSION)
        L.append("  [i] 引用链接里的域名不算正文提及(先掩码后匹配);"
                 "sentiment 恒 neutral(宁缺勿猜,情感留给语义层)")
        for eng, prompt, det in det_rows[:10]:
            terms = ", ".join("%s×%d@%d" % (h["term"], h["count"], h["first_index"])
                              for h in det.get("terms_hit", [])) or "(掩码后无实体命中)"
            L.append("  %-10s %-28.28s mentioned=%d rank=%s count=%d urls_masked=%d | %s"
                     % (eng, prompt, det.get("mentioned", 0),
                        det.get("rank_position") if det.get("rank_position") is not None else "-",
                        det.get("count", 0), det.get("urls_masked", 0), terms))
        if len(det_rows) > 10:
            L.append("  …另有 %d 个检测 cell(略)" % (len(det_rows) - 10))
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
    # v4(N2)指标切片: prompt_targeting 两栏分报(品牌词与中性词永不混进同一个分)
    tgt = stats.get("targeting") or {}
    if tgt:
        L.append("-- 指标切片: prompt_targeting(niubigeo-deep-read.md N2;"
                 "品牌词与中性词永不混进同一个分) --")
        basis = tgt.get("basis_counts", {})
        L.append("  判定: 显式 prompt.branded=%d 条,自动判定=%d 条(规则 %s;品牌名=%s,"
                 "report --brand 可覆盖自动判定)"
                 % (basis.get("explicit", 0), basis.get("auto", 0), tgt.get("rule"),
                    tgt.get("brand_used") or "(未设)"))
        for lb in TARGETING_LABELS:
            sl = tgt["slices"][lb]
            L.append("  [%s] prompts=%d cells=%d(成功分母 %d)"
                     % (lb, sl["prompts"], sl["cells"], sl["denominator"]))
            L.append("    mention_rate   = %s" % _fmt_triple(sl["mention_rate"]))
            L.append("    citation_rate  = %s" % _fmt_triple(sl["citation_rate"]))
            L.append("    first_position = %s" % _fmt_triple(sl["first_position_rate"]))
            L.append("    share_of_voice = %s" % _fmt_triple(sl["share_of_voice"]))
            L.append("    交叉错配: mentioned_without_official_citation=%d | "
                     "cited_without_prose_mention=%d"
                     % (sl["mentioned_without_official_citation"],
                        sl["cited_without_prose_mention"]))
        L.append("  [i] cited_without_prose_mention 需 record --answer-file 的 URL 掩码检测;"
                 "旧口径 cited=1 蕴含 mentioned=1 → 无检测数据时恒 0")
    # v4(N5)意图冻结分母: 分母成员由冻结档案决定,答案结果无权改变
    frz = stats.get("frozen") or {}
    if frz:
        L.append("-- 意图冻结分母(niubigeo-deep-read.md N5;分母成员由冻结 prompt 档案决定,"
                 "答案结果无权改变) --")
        stored = frz.get("panel_freeze_stored")
        src = ("面板 denominator_freeze 已冻结(init 时点)" if stored
               else "legacy 面板未冻结,按当前 prompts 现算(不回写)")
        L.append("  档案: eligible=%d ineligible=%d hash=%s(%s)"
                 % (frz["eligible_count"], len(frz["ineligible_prompts"]),
                    frz["freeze_hash"], src))
        L.append("    coverage_frozen = %s(仅 eligible prompt 的成功 cell;全 eligible 时=coverage)"
                 % _fmt_triple(frz["mention_rate"]))
        L.append("    sov_frozen      = %s(冻结分母下的 SoV,口径同 SoV 引用域代理)"
                 % _fmt_triple(frz["share_of_voice"]))
        if frz.get("ineligible_prompts"):
            L.append("    不入分母(candidate_applicable=False): %s"
                     % "; ".join(frz["ineligible_prompts"][:5]))
        if frz.get("drift"):
            L.append("    [!] 分母漂移: 面板 prompts 与冻结档案不一致(改措辞/增删 prompt "
                     "会改变跨期分母口径,对比前先确认口径)")
        if frz.get("run_hash_drift"):
            L.append("    [!] run 漂移: %s(采样时点分母档案≠面板冻结档案)"
                     % ", ".join(str(x) for x in frz["run_hash_drift"]))
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
    # v4(N2): --brand 覆盖 branded 缺省时自动判定所用品牌名(显式 prompt.branded 不受影响)
    stats = compute_stats(panel, engine=args.engine, brand_override=(args.brand or None))
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
    # v4(N6)未配对明细: 单列展示原因,不入 Δ(旧 excluded 计数键保留)
    unpaired = {"only_in_run1": [], "only_in_run2": [],
                "failed_in_run1": [], "failed_in_run2": []}
    for p in prompts:
        a, b = res_a.get(p), res_b.get(p)
        if a is None:
            miss_a += 1
            unpaired["only_in_run2"].append(p)
        elif b is None:
            miss_b += 1
            unpaired["only_in_run1"].append(p)
        elif a["state"] == "failed" or b["state"] == "failed":
            miss_a += (a["state"] == "failed")
            miss_b += (b["state"] == "failed")
            if a["state"] == "failed":
                unpaired["failed_in_run1"].append(p)
            if b["state"] == "failed":
                unpaired["failed_in_run2"].append(p)
        else:
            paired.append(p)
    new_mentions = [p for p in paired if res_b[p]["mentioned"] and not res_a[p]["mentioned"]]
    gone = [p for p in paired if res_a[p]["mentioned"] and not res_b[p]["mentioned"]]
    k1 = sum(res_a[p]["mentioned"] for p in paired)
    k2 = sum(res_b[p]["mentioned"] for p in paired)
    # v4(N6)配对门: 只对同 prompt×engine 且同探针指纹的配对算 Δ,否则标注不可比
    fp_a, fp_b = run_fingerprint(run_a), run_fingerprint(run_b)
    engine_matched = (run_a.get("engine") or "") == (run_b.get("engine") or "")
    return {"paired": paired, "excluded": {"missing_in_a": miss_a, "missing_in_b": miss_b},
            "k1": k1, "k2": k2, "new_mentions": new_mentions, "disappeared": gone,
            "engine_matched": engine_matched,
            "fingerprint_a": fp_a, "fingerprint_b": fp_b,
            "comparable": engine_matched and fp_a == fp_b,
            "unpaired": unpaired}


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
    # v4(N6)配对差分纪律节: 同 prompt×engine 且同指纹才可比;未配对单列不入 Δ
    same_fp = d.get("fingerprint_a") == d.get("fingerprint_b")
    print("-- 配对差分纪律(niubigeo-deep-read.md N6: 只对同 prompt×engine 且同指纹的配对算 Δ) --")
    print("  engine: %s %s %s" % (ra.get("engine"), "==" if d.get("engine_matched") else "!=",
                                  rb.get("engine")))
    print("  探针指纹: %s / %s(%s;同指纹≠范围一致——不含别名/上游模型版本)"
          % (d.get("fingerprint_a"), d.get("fingerprint_b"), "一致" if same_fp else "不同"))
    if d.get("comparable"):
        print("  可比: 是(同引擎+同指纹)")
    else:
        why = []
        if not d.get("engine_matched"):
            why.append("跨引擎")
        if not same_fp:
            why.append("指纹不同(prompt 集/brand/规则版本变更)")
        print("  [!] 不可比(%s): 上述 Δ 与下述 signals 仅作跨口径对照,不下结论"
              % "+".join(why))
    up = d.get("unpaired") or {}
    up_total = sum(len(v) for v in up.values())
    if up_total:
        parts = [("%s=%s" % (lbl, ",".join(sorted(v)))) for lbl, v in
                 (("仅run1", up.get("only_in_run1")), ("仅run2", up.get("only_in_run2")),
                  ("run1失败", up.get("failed_in_run1")), ("run2失败", up.get("failed_in_run2")))
                 if v]
        print("  未配对单列(%d,不入 Δ): %s" % (up_total, "; ".join(parts)))
    else:
        print("  未配对单列(0,不入 Δ): 无")
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
    not_cmp = "" if d.get("comparable", True) else " [不可比]"   # v4(N6)跨口径强制标注
    print("-- signals(Scrunch Signals 口径:|Δ|≥5pp 且配对 n≥10 才报) --")
    for s in sig["signals"]:
        print("  [signal] %-9s engine=%s topic=%s Δ=%+.1fpp n=%d fp=%s%s"
              % (s["metric"], s["engine"], s["topic"], s["delta_pp"], s["n"],
                 s["fingerprint"], not_cmp))
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


def collect_cell_series(panel, metric="cited", engine=None, skipped=None):
    """runs → {(prompt, engine): [(datetime, y)]}(failed 不入序列;y=metric 值 0/1)。
    R5 GEO 修复: 日期解析失败的 run 不再静默 continue——调用方传 skipped 列表时,
    {"run_id":…, "date":…} 会被追加进去(analyze_decay 汇总打警告并列出 run_id)。"""
    series = {}
    for run in panel.get("runs", []):
        if engine and run["engine"] != engine:
            continue
        d = parse_date(run.get("date"))
        if d is None:
            if skipped is not None:
                skipped.append({"run_id": run.get("run_id"), "date": run.get("date")})
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
    skipped = []
    series = collect_cell_series(panel, metric, engine, skipped=skipped)
    if skipped:      # 日期解析失败的 run: 警告 + 列出 run_id,不再静默丢
        print("[!] decay: %d 个 run 的 date 解析失败,已跳过(不产序列点,不入面板窗): %s"
              % (len(skipped), ", ".join(str(s.get("run_id")) for s in skipped)),
              file=sys.stderr)
    all_dates = [d for d in (parse_date(r.get("date")) for r in panel.get("runs", [])) if d]
    panel_start = min(all_dates) if all_dates else None
    panel_end = max(all_dates) if all_dates else None
    cells = []
    for (prompt, eng) in sorted(series):
        cell = {"prompt": prompt, "engine": eng}
        cell.update(eval_decay_cell(series[(prompt, eng)], panel_start))
        cells.append(cell)
    queue = [c for c in cells if c["status"] in ("decaying", "decayed")]
    queue.sort(key=lambda c: (c.get("days_to_half") is None, c.get("days_to_half") or 0.0))
    return {"metric": metric, "engine": engine or "(all)",
            "panel_window": {"start": panel_start.isoformat() if panel_start else None,
                             "end": panel_end.isoformat() if panel_end else None},
            "cells": cells, "rewrite_queue": queue, "skipped_runs": skipped}


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
    if result.get("skipped_runs"):    # R5: 日期解析失败的 run 单列,不静默丢
        L.append("[!] %d 个 run 的 date 解析失败,已跳过(不产序列点,不入面板窗): %s"
                 % (len(result["skipped_runs"]),
                    ", ".join(str(s.get("run_id")) for s in result["skipped_runs"])))
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


# ---------- decay 轻摘要(R0-4: decay-summary 子命令 + monitor.py 周检共用) ----------

def decay_summary(panel, metric="cited"):
    """R0-4 轻摘要: 复用 analyze_decay 的 decay 计算,产出
    {rewriting, decayed_count, per_engine}——rewriting=重写队列长度(decaying+decayed,
    官方口径"过峰且 share 正跌向峰值一半"才是该更新的页),decayed_count=状态机已判
    decayed(过峰且平滑≤50%peak 持续 14 天无反弹)的 cell 数,per_engine=分引擎计数
    (跨引擎相关仅 0.03-0.09,分引擎独立判定是硬规则)。monitor.py 周检经
    check_citation_decay 调本函数(decayed_count>0 → citation_decay warn)。"""
    result = analyze_decay(panel, metric=metric)
    per_engine = {}
    for c in result["cells"]:
        if c["status"] == "decayed":
            per_engine.setdefault(c["engine"], {"decayed_count": 0, "rewriting": 0}) \
                      ["decayed_count"] += 1
    for c in result["rewrite_queue"]:
        per_engine.setdefault(c["engine"], {"decayed_count": 0, "rewriting": 0})["rewriting"] += 1
    return {"rewriting": len(result["rewrite_queue"]),
            "decayed_count": sum(v["decayed_count"] for v in per_engine.values()),
            "per_engine": per_engine, "metric": metric}


def cmd_decay_summary(args):
    panel = load_panel(args.panel)
    if not panel.get("runs"):
        print("错误: 面板尚无 runs,先用 record 录入采样: %s" % args.panel, file=sys.stderr)
        return 1
    s = decay_summary(panel, metric=args.metric)
    if args.json:
        print(json.dumps(s, ensure_ascii=False))
    else:
        L = ["== citation decay 摘要: %s(Profound 官方方法论;阈值抄自官方)=="
             % panel.get("brand", "?"),
             "metric=%s | decayed(已过半衰)=%d | 重写队列(decaying+decayed)=%d"
             % (s["metric"], s["decayed_count"], s["rewriting"])]
        if s["per_engine"]:
            for eng in sorted(s["per_engine"]):
                pe = s["per_engine"][eng]
                L.append("  %-12s decayed=%d rewriting=%d"
                         % (eng, pe["decayed_count"], pe["rewriting"]))
        else:
            L.append("  (无已达 decay 判定门槛的 cell)")
        print("\n".join(L))
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
    atomic_write_json(rpath, run)      # 与 record 同步双写 run 文件(原子写,防半写)
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


# ---------- v4 扩展: 借鉴 niubigeo(出处逐条标注 references/research/niubigeo-deep-read.md §3) ----------
# 纪律: 全部为增量口径,五状态/Wilson CI/decay/signals 旧键与旧行为不动;新口径只新增键。

# ---- N1 提及检测: URL 掩码 + 实体词表(niubigeo-deep-read.md 第 1 条) ----

def entity_terms(panel):
    """实体词表 = {品牌名, 完整域名, 域名根(拆 "." 取首段且长度≥3), 全部别名},
    trim 后去重(忽略大小写)。降级注明: github repo 名无独立面板字段,经 --aliases
    承载(深读原文实体词表含 repo 名,本面板 schema 无此键)。"""
    terms = []
    brand = str(panel.get("brand") or "").strip()
    if brand:
        terms.append(brand)
    domain = str(panel.get("domain") or "").strip().lower()
    if domain:
        terms.append(domain)
        root = domain.split(".")[0]
        if len(root) >= 3:                      # 域名根过短(<3)不入词表(假阳性)
            terms.append(root)
    for a in panel.get("aliases") or []:
        a = str(a).strip()
        if a:
            terms.append(a)
    out, seen = [], set()
    for t in terms:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def mask_urls(text):
    """URL 掩码: 正文中所有 URL 的字符等长替换成空格(保索引),再子串匹配——
    引用链接里的域名不算正文提及(防假阳性核心)。stdlib 正则近似 linkify-it:
    scheme://… / www.… / 裸域+路径;裸域无路径(行文 "acme.ai 是…")不掩,
    完整域名实体可作正文提及[推断: 对 linkify-it 的保守近似]。返回(掩码文, URL 数)。"""
    n = [0]

    def _blank(m):
        n[0] += 1
        return " " * len(m.group(0))

    return URL_TOKEN_RE.sub(_blank, text), n[0]


def detect_mentions(answer, panel):
    """掩码后子串提及判定(忽略大小写)。返回 {mentioned, terms_hit[{term,
    first_index, count}], rank_position, count, context, urls_masked,
    sentiment, rules}:
    - rank_position = 品牌首个命中在全部实体(品牌词表 + 竞品域)按 first index
      排序中的名次(1 起);竞品只匹配完整域字符串(面板竞品是域,非品牌名)
    - count = Σ各实体词非重叠出现次数(不同实体词重叠区间会重复计,逐词统计)
    - context = 首命中点前 240/后 520 字符,句边界(SENTENCE_BOUNDARIES)内收
    - sentiment 恒 neutral——宁缺勿猜,情感判定留给上层语义评审"""
    raw = str(answer or "")
    masked, n_urls = mask_urls(raw)
    low = masked.lower()
    hits = []
    for t in entity_terms(panel):
        tl = t.lower()
        first = low.find(tl)
        if first >= 0:
            hits.append({"term": t, "first_index": first, "count": low.count(tl)})
    comp_first = []
    for c in panel.get("competitors") or []:
        cl = str(c).strip().lower()
        if cl:
            i = low.find(cl)
            if i >= 0:
                comp_first.append(i)
    rank_position = None
    first_hit = None
    if hits:
        first_hit = min(h["first_index"] for h in hits)
        rank_position = 1 + sum(1 for i in comp_first if i < first_hit)
        start, end = max(0, first_hit - 240), min(len(raw), first_hit + 520)
        seg = raw[start:end]
        if start > 0:                            # 前窗截断 → 内收到首个句边界之后
            for j, ch in enumerate(seg):
                if ch in SENTENCE_BOUNDARIES:
                    seg = seg[j + 1:]
                    break
        if end < len(raw):                       # 后窗截断 → 内收到末个句边界
            for j in range(len(seg) - 1, -1, -1):
                if seg[j] in SENTENCE_BOUNDARIES:
                    seg = seg[:j + 1]
                    break
        context = seg.strip()
    else:
        context = ""
    return {"mentioned": 1 if hits else 0, "terms_hit": hits,
            "rank_position": rank_position,
            "count": sum(h["count"] for h in hits), "context": context,
            "urls_masked": n_urls, "sentiment": "neutral",
            "rules": MENTION_RULES_VERSION}


def load_answers(path):
    """--answer-file 回答文件 → {prompt: 回答文本}。支持 JSON {prompt: 回答} 对象
    与 CSV(表头含 prompt/query 与 answer/回答/正文 列;引号字段可含换行)。"""
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("JSON answer-file 需为 {prompt: 回答} 对象")
        return {str(k).strip(): str(v) for k, v in data.items() if str(k).strip()}
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            prompt = (row.get("prompt") or row.get("query") or "").strip()
            ans = (row.get("answer") or row.get("回答") or row.get("正文") or "")
            if prompt:
                out[prompt] = ans.strip()
    return out


def mention_detection_rows(panel, engine=None):
    """runs → [(engine, prompt, detection)];report 的 N1 标注节数据源。"""
    rows = []
    for run in panel.get("runs", []):
        if engine and run.get("engine") != engine:
            continue
        for prompt, res in run.get("results", {}).items():
            det = res.get("mention_detection")
            if isinstance(det, dict):
                rows.append((run.get("engine", "?"), prompt, det))
    return rows


# ---- N2 指标切片: 显式分子分母 + branded/unbranded 分报(niubigeo-deep-read.md 第 2 条) ----

def metric_triple(num, den):
    """指标三元组 {numerator, denominator, value};denominator=0 → value=None
    永不报 0%(niubigeo metrics-engine 同路数: null=不能计算)。"""
    return {"numerator": num, "denominator": den, "value": (num / den) if den else None}


def _new_targeting_slice():
    return {"prompts": 0, "cells": 0, "denominator": 0, "mentioned_sum": 0,
            "cited_cells": 0, "answers": 0, "rank_cells": 0, "wins": 0,
            "brand_hits": 0, "comp_hits": 0,
            "mentioned_without_official_citation": 0, "cited_without_prose_mention": 0}


def prompt_targeting(panel, p, brand_override=None):
    """branded 判定 → (label, basis)。显式 prompt.branded 优先;缺省按"prompt 文本
    含品牌名/别名/主域(忽略大小写子串)"自动判定;report --brand 覆盖自动判定所用
    品牌名(不覆盖显式标注)。降级注明: 深读原文切片键为 prompt_targeting
    (organic_unbranded vs branded_or_direct),标签沿用;winner 逐 run 累计未实现
    (现有 win_rate 按排位口径,不重复建指标)。"""
    o = prompt_obj(p)
    if o.get("branded") is not None:
        return ("branded_or_direct" if o["branded"] else "organic_unbranded"), "explicit"
    text = o["text"].lower()
    names = {str(brand_override or panel.get("brand") or "").strip().lower()}
    names |= {str(a).strip().lower() for a in panel.get("aliases") or [] if str(a).strip()}
    dom = str(panel.get("domain") or "").strip().lower()
    if dom:
        names.add(dom)
    hit = any(n and n in text for n in names)
    return ("branded_or_direct" if hit else "organic_unbranded"), "auto"


def _targeting_of(panel, p, cache, brand_override):
    """按 prompt 文本缓存 targeting 判定(p 可为对象或字符串,缓存键统一取 text)。"""
    key = p if isinstance(p, str) else prompt_text(p)
    if key not in cache:
        cache[key] = prompt_targeting(panel, p, brand_override=brand_override)
    return cache[key]


def _fmt_triple(t):
    if t["value"] is None:
        return "null(分母=0 → null,永不报 0%)"
    return "%d/%d = %s" % (t["numerator"], t["denominator"], _pct(t["value"]))


# ---- N5 意图冻结分母(niubigeo-deep-read.md 第 5 条) ----

def denominator_freeze(panel):
    """冻结分母档案: eligible = prompts 中 candidate_applicable≠False 者(ineligible
    单列),hash=sha256(版本|brand|sorted(eligible))[:16]。init 时点写入
    panel['denominator_freeze'] 后只读不静默重写;分母成员由档案决定,不由每次
    会变的答案决定——coverage/SoV 的冻结口径(compute_stats['frozen'])只数
    eligible prompt 的成功 cell。降级注明: 深读原文的 12 意图多标签分类器不引入
    (prompt-bank 模板不在本脚本管辖),档案字段由 prompts 对象可选携带。"""
    eligible, ineligible = [], []
    for p in panel.get("prompts", []):
        o = prompt_obj(p)
        (ineligible if o.get("candidate_applicable") is False else eligible).append(o["text"])
    h = hashlib.sha256(("%s|%s|%s" % (DENOM_FREEZE_VERSION, panel.get("brand") or "",
                                      "\n".join(sorted(eligible)))).encode("utf-8")
                       ).hexdigest()[:16]
    return {"version": DENOM_FREEZE_VERSION, "eligible_prompts": eligible,
            "ineligible_prompts": ineligible, "freeze_hash": h}


# ---- N6 配对差分门 + 探针指纹(niubigeo-deep-read.md 第 6 条) ----

def run_fingerprint(run):
    """探针指纹 = sha256(配对协议版本|提及规则版本|engine(=provider/model)|
    subject(=brand)|keywordSetHash(sorted prompts))[:16]。record 时写入
    run['fingerprint'](已存则直读);diff 用它配对门: 跨指纹强制标注不可比。
    诚实声明(抄自原文): 同指纹≠范围一致——不含别名/实际上游模型版本;
    预算账本纪律(--budget-usd)属 monitor.py,本脚本不打 API 不涉及。"""
    if run.get("fingerprint"):
        return run["fingerprint"]
    kw = hashlib.sha256("\n".join(sorted(run.get("results", {}))).encode("utf-8")
                        ).hexdigest()[:16]
    return hashlib.sha256("|".join([DIFF_PAIRING_VERSION, MENTION_RULES_VERSION,
                                    str(run.get("engine") or ""),
                                    str(run.get("brand") or ""), kw]).encode("utf-8")
                          ).hexdigest()[:16]


# ---------- triangulate(R6 归因: 三源分歧度报告) ----------
# 同一品牌同期三个来源各自估计"AI 渠道品牌触达",口径互不相同:
#   referral = AI referrer 请求占可解析请求比(ai_referral_log 输出;下限口径)
#   panel    = 窗口内 mention coverage(本面板;prompt 抽样口径)
#   survey   = 品牌提示回想 %(CSV;用户记忆口径)
# 纪律(references/monitoring/kpi-definitions.md 对账五步的同路数): 永不跨源求和、
# 永不跨源平均、只读方向一致性与分歧度;referral 是下限(App 内打开常不带
# referrer),survey 回想含非 AI 渠道记忆(偏高),panel 只覆盖采样 prompt 集。
TRIANGULATE_VERSION = "triangulate-v1"
REFERRAL_TEXT_TOTAL_RE = re.compile(r"合计 AI referrer 请求:?\s*(\d+)")
REFERRAL_TEXT_PARSED_RE = re.compile(r"日志行 (\d+) \| 可解析 (\d+)")
SURVEY_COL_KEYS = ("recall", "回想", "提示回想", "aided_recall", "aided recall",
                   "recall_pct", "pct", "%")
SOURCE_HINTS = {
    "referral": "下限口径: App 内打开常不带 referrer,真实 AI 引流 ≥ 此数",
    "panel": "抽样口径: 只覆盖面板 prompt 集,n<10 时结论只能当方向",
    "survey": "记忆口径: 提示回想含非 AI 渠道记忆,系统性偏高",
}


def _win_date(s):
    """'YYYY-MM-DD…' → datetime;空/无法解析 → None(非法显式输入由调用方报错)。"""
    if not s:
        return None
    return parse_date(str(s)[:10] + "T00:00:00")


def _in_window(d, since, until):
    if d is None:
        return True                      # 无日期的源不参与窗口过滤(整文件口径)
    if since and d < since:
        return False
    if until and d > until:
        return False
    return True


def parse_referral_source(path, since=None, until=None):
    """--referral → {form, hits, parsed, value_pct, note}。
    吃三种形态:
      1) ai_referral_log.py 文本输出: 抓 "合计 AI referrer 请求: N" 与
         "日志行 X | 可解析 Y" → value_pct = N/Y×100(下限);
      2) CSV 列 date,hits[,total]: 窗口内 Σhits(与 Σtotal 有 total 列时算占比);
      3) JSON: {ai_total|ai_referral_hits|hits, parsed|total|requests} 或
         {"YYYY-MM-DD": hits 或 {hits,total}}(逐日,走窗口过滤)。"""
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read()
    except OSError as e:
        raise ValueError("无法读取 --referral %s: %s" % (path, e))
    if not raw.strip():
        raise ValueError("--referral %s 为空文件" % path)
    txt = raw.strip()
    if txt.startswith("{"):
        try:
            data = json.loads(txt)
        except ValueError as e:
            raise ValueError("--referral JSON 解析失败: %s" % e)
        if not isinstance(data, dict):
            raise ValueError("--referral JSON 需为对象")
        hits = parsed = total = None
        for k in ("ai_total", "ai_referral_hits", "hits", "ai_hits"):
            if isinstance(data.get(k), (int, float)):
                hits = float(data[k])
                break
        for k in ("parsed", "total", "total_requests", "requests"):
            if isinstance(data.get(k), (int, float)):
                parsed = float(data[k])
                break
        if hits is None:                       # 逐日形态 {"2026-10-01": 3 或 {hits,total}}
            hits = total = 0.0
            for k, v in data.items():
                d = _win_date(k)
                if not _in_window(d, since, until):
                    continue
                if isinstance(v, dict):
                    h, t = v.get("hits"), v.get("total")
                else:
                    h, t = v, None
                if isinstance(h, (int, float)):
                    hits += float(h)
                if isinstance(t, (int, float)):
                    total = (total or 0.0) + float(t)
            parsed = total
        value = (100.0 * hits / parsed) if (hits is not None and parsed) else None
        note = "" if value is not None else "JSON 无分母(parsed/total),只有计数,占比不可算"
        return {"form": "json", "hits": hits, "parsed": parsed, "value_pct": value,
                "note": note}
    m_total = REFERRAL_TEXT_TOTAL_RE.search(txt)
    if m_total:                                # ai_referral_log 文本输出
        hits = float(m_total.group(1))
        parsed = None
        m_log = REFERRAL_TEXT_PARSED_RE.search(txt)
        if m_log:
            parsed = float(m_log.group(2))     # 可解析行数 = 占比分母
        value = (100.0 * hits / parsed) if parsed else None
        return {"form": "ai_referral_log-text", "hits": hits, "parsed": parsed,
                "value_pct": value,
                "note": ("" if value is not None
                         else "文本中未找到 '日志行 X | 可解析 Y' 行,占比不可算")}
    # CSV: date,hits[,total]
    rows = list(csv.reader(txt.splitlines()))
    if not rows:
        raise ValueError("--referral %s 无可解析内容" % path)
    header = [(c or "").strip().lower() for c in rows[0]]
    hit_k = next((i for i, h in enumerate(header) if h in ("hits", "ai_hits", "点击", "访问")), None)
    if hit_k is None:
        raise ValueError("--referral 不认识的形态(需 ai_referral_log 输出文本 / "
                         "date,hits[,total] CSV / JSON 对象),首行: %r" % rows[0][:4])
    date_k = next((i for i, h in enumerate(header) if h in ("date", "day", "日期")), None)
    total_k = next((i for i, h in enumerate(header)
                    if h in ("total", "totals", "sessions", "requests", "总", "总量")), None)
    body = rows[1:] if any(h in ("date", "hits", "ai_hits", "day", "日期", "点击", "访问",
                                 "total", "sessions", "requests") for h in header) else rows
    hits = total = 0.0
    used = 0
    for r in body:
        if not r or not (r[hit_k] or "").strip():
            continue
        d = _win_date(r[date_k]) if (date_k is not None and date_k < len(r)) else None
        if date_k is not None and not _in_window(d, since, until):
            continue
        try:
            hits += float(r[hit_k])
        except ValueError:
            continue
        if total_k is not None and total_k < len(r) and r[total_k].strip():
            try:
                total += float(r[total_k])
            except ValueError:
                pass
        used += 1
    if not used:
        return {"form": "csv", "hits": 0.0, "parsed": None, "value_pct": None,
                "note": "窗口内没有 CSV 数据行"}
    value = (100.0 * hits / total) if total else None
    return {"form": "csv", "hits": hits, "parsed": total or None, "value_pct": value,
            "note": ("" if value is not None
                     else "CSV 无 total 列,只有计数,占比不可算(加 total 列或用 "
                          "ai_referral_log 输出)")}


def panel_window_coverage(panel, since=None, until=None):
    """窗口内面板 mention coverage(failed 不入分母;no_answer 留分母计 0)。"""
    cells = denom = mentioned = 0
    per_engine = {}
    runs_used = 0
    for run in panel.get("runs", []):
        d = parse_date(run.get("date"))
        if not _in_window(d, since, until):
            continue
        runs_used += 1
        for res in run.get("results", {}).values():
            cells += 1
            if res.get("state") == "failed":
                continue
            denom += 1
            mentioned += res.get("mentioned", 0)
            agg = per_engine.setdefault(run["engine"], {"denominator": 0, "mentioned": 0})
            agg["denominator"] += 1
            agg["mentioned"] += res.get("mentioned", 0)
    for eng, agg in per_engine.items():
        agg["coverage"] = (agg["mentioned"] / agg["denominator"]) \
            if agg["denominator"] else None
    return {"runs": runs_used, "cells": cells, "denominator": denom,
            "mentioned_sum": mentioned,
            "value_pct": (100.0 * mentioned / denom) if denom else None,
            "per_engine": per_engine}


def load_survey_csv(path, since=None, until=None):
    """survey CSV(date,recall%) → {rows, value_pct, note}。
    recall 列名认 recall/回想/提示回想/aided_recall/recall_pct/pct/%;
    值 0-100(>1 的整数百分比或 0-1 小数均接受: >1 按 %,<1 按比例×100);
    多行取窗口内均值。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        raise ValueError("无法读取 --survey %s: %s" % (path, e))
    if not rows:
        raise ValueError("--survey %s 无数据行" % path)
    keys = {(k or "").strip().lower(): k for k in (rows[0] or {}) if k}
    r_k = next((keys[k] for k in SURVEY_COL_KEYS if k in keys), None)
    d_k = next((keys[k] for k in ("date", "day", "日期") if k in keys), None)
    if r_k is None:
        raise ValueError("--survey 需要 recall/回想/提示回想 列,实际列=%s"
                         % list((rows[0] or {}).keys()))
    vals = []
    for row in rows:
        raw = (row.get(r_k) or "").strip().rstrip("%").strip()
        if not raw:
            continue
        if d_k:
            d = _win_date(row.get(d_k))
            if not _in_window(d, since, until):
                continue
        try:
            v = float(raw)
        except ValueError:
            continue
        if 0.0 <= v <= 1.0:
            v *= 100.0                        # 0-1 比例 → %
        if not (0.0 <= v <= 100.0):
            raise ValueError("--survey 回想值越界(0-100): %r" % raw)
        vals.append(v)
    if not vals:
        return {"rows": 0, "value_pct": None, "note": "窗口内无有效 recall 行"}
    return {"rows": len(vals), "value_pct": sum(vals) / len(vals),
            "note": ""}


def triangulate_sources(sources):
    """可用源(% 值非 None)两两差 + 最大分歧源(对其他源的平均绝对差最大)。"""
    names = [n for n in ("referral", "panel", "survey")
             if sources.get(n) and sources[n].get("value_pct") is not None]
    pairwise = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            diff = sources[a]["value_pct"] - sources[b]["value_pct"]
            higher, lower = (a, b) if diff >= 0 else (b, a)
            pairwise.append({"a": a, "b": b, "diff_pp": round(diff, 2),
                             "abs_pp": round(abs(diff), 2),
                             "direction": "%s 高于 %s %.1fpp" % (higher, lower,
                                                                abs(diff))})
    max_div = None
    if len(names) >= 2:
        score = {}
        for n in names:
            rel = [p for p in pairwise if n in (p["a"], p["b"])]
            score[n] = sum(p["abs_pp"] for p in rel) / len(rel)
        worst = max(sorted(names), key=lambda n: score[n])
        max_div = {"source": worst, "mean_abs_pp": round(score[worst], 2),
                   "hint": SOURCE_HINTS.get(worst, "")}
    return {"pairwise": pairwise, "n_comparable": len(names),
            "comparable_sources": names, "max_divergence": max_div}


def render_triangulate(panel, ref, pan, svy, tri, since, until):
    L = ["== 三源分歧度报告(triangulate): %s ==" % panel.get("brand", "?"),
         "窗口: %s → %s" % (since or "(面板全部 runs)", until or "(至今)"),
         "[口径] referral=下限(App 内打开常不带 referrer);panel=prompt 抽样;"
         "survey=提示回想(记忆口径,偏高)。永不跨源求和/平均,只读方向与分歧。"]
    L.append("-- 三源 --")
    L.append("  referral(%s): value=%s hits=%s 分母=%s%s"
             % (ref["form"], _pct((ref["value_pct"] / 100) if ref["value_pct"] is not None else None),
                _fmt_num(ref["hits"]), _fmt_num(ref["parsed"]),
                (" | " + ref["note"]) if ref.get("note") else ""))
    L.append("  panel: value=%s(runs=%d, 成功 cell=%d, Σmentioned=%d)"
             % (_pct((pan["value_pct"] / 100) if pan["value_pct"] is not None else None),
                pan["runs"], pan["denominator"], pan["mentioned_sum"]))
    for eng in sorted(pan["per_engine"]):
        agg = pan["per_engine"][eng]
        L.append("    %-12s %s" % (eng, _pct(agg["coverage"])))
    if svy is None:
        L.append("  survey: 未提供(--survey survey.csv,品牌提示回想%)")
    else:
        L.append("  survey: value=%s(rows=%d)%s"
                 % (_pct((svy["value_pct"] / 100) if svy["value_pct"] is not None else None),
                    svy["rows"], (" | " + svy["note"]) if svy.get("note") else ""))
    L.append("-- 两两差(pp) --")
    if tri["pairwise"]:
        for p in tri["pairwise"]:
            L.append("  %s vs %s: %+.2fpp(|Δ|=%.2f)" % (p["a"], p["b"], p["diff_pp"], p["abs_pp"]))
    else:
        L.append("  可比较源不足 2 个(带 % 的源),分歧度无法计算")
    if tri["max_divergence"]:
        md = tri["max_divergence"]
        L.append("-- 最大分歧源: %s(对其他源平均 |Δ|=%.2fpp) --" % (md["source"], md["mean_abs_pp"]))
        if md["hint"]:
            L.append("  [i] %s: %s" % (md["source"], md["hint"]))
    L.append("-- 口径注记 --")
    L.append("  [!] referral 是下限: 真实 AI 引流 ≥ referrer 测得值(ai_referral_log 口径)")
    L.append("  [i] 三源方向一致才可下'触达在升/降'的结论;分歧大时先查口径再查数据")
    if len(panel.get("prompts", [])) < 10:
        L.append("  [!] prompts=%d <10:panel 源结论只能当方向" % len(panel.get("prompts", [])))
    return "\n".join(L)


def _fmt_num(v):
    return "-" if v is None else ("%d" % round(v) if float(v).is_integer() else "%.2f" % v)


def cmd_triangulate(args):
    try:
        panel = load_panel(args.panel)
    except (OSError, ValueError) as e:
        print("错误: 读取面板失败: %s" % e, file=sys.stderr)
        return 1
    if not panel.get("runs"):
        print("错误: 面板尚无 runs,先用 record 录入采样: %s" % args.panel, file=sys.stderr)
        return 1
    since, until = None, None
    for label, raw in (("--since", args.since), ("--until", args.until)):
        if raw:
            d = _win_date(raw)
            if d is None:
                print("错误: %s 需要 YYYY-MM-DD,得到 %r" % (label, raw), file=sys.stderr)
                return 1
            if label == "--since":
                since = d
            else:
                until = d
    try:
        ref = parse_referral_source(args.referral, since, until)
    except ValueError as e:
        print("错误: %s" % e, file=sys.stderr)
        return 1
    svy = None
    if args.survey:
        try:
            svy = load_survey_csv(args.survey, since, until)
        except ValueError as e:
            print("错误: %s" % e, file=sys.stderr)
            return 1
    pan = panel_window_coverage(panel, since, until)
    if pan["runs"] == 0:
        print("错误: 窗口 %s→%s 内没有面板 runs(检查 --since/--until)"
              % (args.since or "(开)", args.until or "(开)"), file=sys.stderr)
        return 1
    sources = {"referral": ref, "panel": pan, "survey": svy}
    tri = triangulate_sources(sources)
    if args.json:
        payload = {"tool": "citation_panel.triangulate",
                   "version": TRIANGULATE_VERSION,
                   "brand": panel.get("brand"),
                   "window": {"since": args.since or None, "until": args.until or None},
                   "sources": {k: dict(v) for k, v in sources.items() if v is not None},
                   "pairwise": tri["pairwise"],
                   "n_comparable": tri["n_comparable"],
                   "max_divergence": tri["max_divergence"],
                   "caveats": ["referral 是下限: App 内打开常不带 referrer,真实 AI 引流 ≥ 此数",
                               "永不跨源求和/平均;只读方向一致性与分歧度",
                               SOURCE_HINTS["survey"], SOURCE_HINTS["panel"]]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_triangulate(panel, ref, pan, svy, tri, args.since, args.until))
    return 0


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
                   help="prompt 库文件,产出对象形态。Markdown:只取各表「模板(整句)/prompt/"
                        "text/query」列单元格(漏斗/stage 等列作元数据;无 prompt 列的表、"
                        "标题、正文不收);否则带表头 CSV 或纯文本一行一条")
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
    p = sub.add_parser("record",
                       help="记录一次采样运行(或 --from-referral 导入一方 referral 轨)")
    p.add_argument("--engine", default="",
                   help="AI 引擎(如 chatgpt;采样 run 必填,--from-referral 时不需要)")
    p.add_argument("--file", default="", help="run.csv(prompt,mentioned,cited,cited_urls[,state][,rank])")
    p.add_argument("--from-referral", dest="from_referral", default="",
                   help="R6 Ryze 对齐: ai_referral_log --as-panel-import 导出 JSON → "
                        "source=referral run(engine 对齐六引擎,未知域→other+警告;"
                        "与采样轨分开列不加权混合;整 stdout 重定向文件按 marker 切取)")
    p.add_argument("--answer-file", default="",
                   help="纯文本回答文件(CSV: prompt,answer 列;或 JSON {prompt: 回答});"
                        "URL 掩码提及检测自动填 mentioned/rank,人工显式列优先"
                        "(niubigeo-deep-read.md N1)")
    p.add_argument("--run-id", default="")
    p.add_argument("--date", default="")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_record)
    p = sub.add_parser("report", help="输出面板报告")
    p.add_argument("--engine", default=None)
    p.add_argument("--brand", default="",
                   help="覆盖 branded 缺省时自动判定所用品牌名(niubigeo-deep-read.md N2;"
                        "显式 prompt.branded 标注不受影响)")
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
        "decay-summary",
        help="decay 轻摘要 {rewriting,decayed_count,per_engine}(R0-4;monitor 周检同源)")
    p.add_argument("--metric", default="cited", choices=("cited", "mentioned"),
                   help="序列取值(默认 cited=被引)")
    p.add_argument("--json", action="store_true",
                   help="单行 JSON {rewriting,decayed_count,per_engine}(默认人类可读摘要)")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_decay_summary)
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
    p = sub.add_parser(
        "triangulate",
        help="三源分歧度报告(R6 归因: referral 日志 × 面板采样 × survey 回想)")
    p.add_argument("--referral", required=True,
                   help="referrer 日志源: ai_referral_log 输出文本 / CSV(date,hits[,total]) /"
                        " JSON({ai_total,parsed} 或 逐日 {date: hits})")
    p.add_argument("--survey", default="",
                   help="可选 survey CSV(date,recall%% 列;品牌提示回想)")
    p.add_argument("--since", default="", help="窗口起 YYYY-MM-DD(过滤 panel runs/survey/referral 逐日行)")
    p.add_argument("--until", default="", help="窗口止 YYYY-MM-DD")
    p.add_argument("--json", action="store_true", help="输出 JSON(默认 markdown)")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_triangulate)
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
    # Wilson: P1 n=3 k=2 → p=2/3,真 Wilson CI≈[0.208,0.939] 跨 0.5 → unstable
    k, n, p, lo, hi, unstable = stats["stability"][P1]
    assert (k, n) == (2, 3) and unstable and lo < 0.5 < hi
    # P2 n=3 k=2 同样 unstable;P3 n=2 不足 3 次,不报
    assert stats["stability"][P2][0] == 2 and P3 not in stats["stability"]
    # wilson 真公式自检(R5: 旧 Wald 近似 k=0/n 时宽 0 → 误判 stable)
    p, lo, hi, uns = wilson_ci(2, 3)
    ctr = (2 / 3 + Z * Z / 6) / (1 + Z * Z / 3)
    half = Z * math.sqrt((2 / 3) * (1 / 3) / 3 + Z * Z / 36) / (1 + Z * Z / 3)
    assert abs(lo - (ctr - half)) < 1e-12 and abs(hi - (ctr + half)) < 1e-12
    assert abs(hi - 0.9385) < 1e-3 and abs(lo - 0.2077) < 1e-3
    _, lo0, hi0, uns0 = wilson_ci(0, 3)     # k=0,n=3 → 上界≈0.56,区间非零宽
    assert hi0 > 0.5 and uns0 and hi0 - lo0 > 0.5
    _, lon, hin, unsn = wilson_ci(3, 3)     # k=n=3 → 下界≈0.44,跨 0.5 → unstable
    assert lon < 0.5 < hin and unsn and hin - lon > 0.5

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

    # ---- v4(niubigeo-deep-read.md;详细用例见 tests/test_niubigeo_panel.py) ----
    npanel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
              "competitors": ["comp.com"]}
    det = detect_mentions("comp.com leads. Acme is solid. Source: https://acme.ai/g", npanel)
    assert det["mentioned"] == 1 and det["rank_position"] == 2 and det["sentiment"] == "neutral"
    det2 = detect_mentions("See https://acme.ai/guide and www.acme.ai/x for details.",
                           {"brand": "Acme", "domain": "acme.ai", "aliases": []})
    assert det2["mentioned"] == 0 and det2["urls_masked"] == 2   # 链接域名不算正文提及
    tpanel = {"brand": "Acme", "domain": "acme.ai", "aliases": [],
              "prompts": [{"text": "is acme worth it"}, {"text": "top crm"}]}
    assert prompt_targeting(tpanel, tpanel["prompts"][0])[0] == "branded_or_direct"
    assert prompt_targeting(tpanel, tpanel["prompts"][1])[0] == "organic_unbranded"
    assert prompt_targeting(tpanel, {"text": "zoho vs hubspot"},
                            brand_override="Zoho")[0] == "branded_or_direct"  # --brand 覆盖
    fr = denominator_freeze(dict(sig_panel, prompts=[{"text": "k%d" % i,
                                                      "candidate_applicable": i != 0}
                                                     for i in range(3)]))
    assert len(fr["freeze_hash"]) == 16 and fr["ineligible_prompts"] == ["k0"]
    fp_a = run_fingerprint(ra)
    assert fp_a == run_fingerprint(ra) and len(fp_a) == 16
    assert run_fingerprint(rb) == fp_a                    # 同 engine/brand/prompt 集
    rb2 = dict(rb, results=dict(rb["results"], pz={"state": "brand_absent", "mentioned": 0,
                                                   "cited": 0, "cited_urls": []}))
    assert run_fingerprint(rb2) != fp_a                   # prompt 集变 → 指纹变
    d6 = diff_runs(ra, rb)
    assert d6["comparable"] and d6["engine_matched"]      # 同引擎+同指纹 → 可比
    d7 = diff_runs(ra, dict(rb, engine="perplexity"))
    assert not d7["comparable"] and not d7["engine_matched"]   # 跨引擎不配对
    d8 = diff_runs(ra, rb2)
    assert not d8["comparable"]                         # 跨指纹 → 不可比
    st4 = compute_stats({"brand": "Acme", "domain": "acme.ai", "aliases": [],
                         "prompts": [{"text": "acme q", "branded": True},
                                     {"text": "plain q"}],
                         "runs": [{"engine": "chatgpt", "date": "2026-10-01",
                                   "results": {"acme q": {"state": "name_only_mention",
                                                          "mentioned": 1, "cited": 0,
                                                          "cited_urls": []},
                                               "plain q": {"state": "brand_absent",
                                                           "mentioned": 0, "cited": 0,
                                                           "cited_urls": []}}}]})
    tslices = st4["targeting"]["slices"]
    assert tslices["branded_or_direct"]["mention_rate"]["value"] == 1.0
    assert tslices["organic_unbranded"]["mention_rate"]["value"] == 0.0
    assert st4["frozen"]["mention_rate"]["value"] == 0.5   # 全 eligible → =coverage

    # ---- R6 referral 桥(详细用例见 tests/test_referral_bridge.py) ----
    ref_json = os.path.join(tmp, "referral.json")
    with open(ref_json, "w", encoding="utf-8") as f:
        json.dump({"tool": "ai_referral_log", "source": "referral",
                   "scope": "下界证据(real)", "date": "2026-10-09",
                   "records": [
                       {"date": "2026-10-09", "engine": "chatgpt", "sessions": 4,
                        "cited_urls": ["/pricing", "/blog/geo"]},
                       {"date": "2026-10-09", "engine": "duck.ai", "sessions": 2,
                        "cited_urls": []}]}, f, ensure_ascii=False)
    assert cmd_record(build_parser().parse_args(
        ["record", "--from-referral", ref_json, "--panel", panel_path])) == 0
    panel = load_panel(panel_path)
    assert len(panel["runs"]) == 5                        # 3 采样 + 2 referral
    ref_runs = [r for r in panel["runs"] if r.get("source") == REFERRAL_SOURCE]
    samp_runs = [r for r in panel["runs"] if r.get("source") != REFERRAL_SOURCE]
    assert len(ref_runs) == 2 and all(r["results"] == {} for r in ref_runs)
    assert all(r.get("source") == SAMPLING_SOURCE for r in samp_runs)  # 新采样 run 显式标注
    assert {r["engine"] for r in ref_runs} == {"chatgpt", "other"}     # duck.ai → other
    stats_r = compute_stats(panel)                        # referral run 不入采样指标
    assert stats_r["runs"] == 3 and stats_r["cells"] == 9
    assert stats_r["coverage"] == stats["coverage"] and stats_r["share"] == stats["share"]
    rep = render_report(panel, stats_r)
    assert "referral 流量轨" in rep and "source=referral" in rep and "不加权混合" in rep
    assert "采样轨" in rep and "下界(real)" in rep and "sessions=4" in rep
    # 混合输出(marker 行 + JSON)同样可导入;旧面板(无 source)视为采样轨
    mixed = os.path.join(tmp, "mixed.txt")
    with open(mixed, "w", encoding="utf-8") as f:
        f.write("== AI 引用流量日志分析 ==\n文本行\n-- referral panel import "
                "(source=referral; citation_panel record --from-referral) --\n"
                '{"source": "referral", "records": [{"date": "2026-10-10", '
                '"engine": "perplexity", "sessions": 3, "cited_urls": ["/x"]}]}')
    recs, _w = load_referral_import(mixed)
    assert recs == [{"date": "2026-10-10", "engine": "perplexity",
                     "sessions": 3, "cited_urls": ["/x"]}]
    legacy = {"brand": "Acme", "domain": "acme.ai", "aliases": [], "prompts": ["p1"],
              "engines": ["chatgpt"],
              "runs": [{"run_id": "old-1", "engine": "chatgpt", "date": "2026-10-01",
                        "brand": "Acme",
                        "results": {"p1": {"state": "cited_brand", "mentioned": 1,
                                           "cited": 1,
                                           "cited_urls": ["https://acme.ai/a"]}}}]}
    lst = compute_stats(legacy)
    assert lst["runs"] == 1 and lst["cells"] == 1 and lst["coverage"] == 1.0
    assert render_referral_section(legacy) == []          # 旧面板无 referral 轨节
    print("[self-test] PASS citation_panel(9 cells, coverage=62.5%, share=60.0%, "
          "wilson unstable 案例, 配对 diff, cited/mentioned 纠正; "
          "v2: prompts 对象化/signals/decay 半衰/指标族; "
          "v3: geo 写回/硬 cap 机检/top_pick 佐证降级/反通胀聚合; "
          "v4: niubigeo N1 掩码提及检测/N2 targeting 切片/N5 冻结分母/N6 配对差分门; "
          "R6: referral 桥(--from-referral 导入/双轨分开列/旧面板兼容))")


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
