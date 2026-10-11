#!/usr/bin/env python3
"""market_batch.py — 多市场批量编排与跨市场周报(R3-9,国际化管线"无批量编排"缺口的工具化;stdlib only)。
规格:references/overview/pipeline-completeness.md R3-9(一份声明→批量跑 market_lint/
serp_occupancy→跨市场周报)。

声明文件(--decl,受限 YAML 子集,自实现不依赖 PyYAML——project.py parse_project_yaml 风格):
  site: https://example.com          # 顶层标量,必填
  market: ja                         # 市场块开始(markets.json 市场码,重复=笔误拒收)
  key_pages:                         # 该市场关键页(≥1;首个=lint 代表页)
    - https://example.com/ja/
    - https://example.com/ja/pricing
  domains:                           # 可选:该市场品牌词 top10 域(serp_occupancy 输入)
    - note.com
  domains_file: serp-ja.txt          # 可选:域清单文件(空白/逗号分隔;周报轮换域用文件免改声明)

批量子进程(本脚本零网络——只编排不抓取;URL 由 market_lint 自抓,域表由声明/文件喂入):
  ① market_lint --market <码> --json <代表页>(key_pages[0];https?:// 走 --url,否则按本地
     文件路径);--json 摘要(critical/warn/output 行)直接聚合;lint FAIL(critical>0,退出码 1)
     是有效结果不是执行失败。
  ② serp_occupancy --market <区域码> <逗号域名>——仅当该市场在 markets.json serp_occupancy
     占位表内有区域(tr/th/in/kr/jp/vn/ru);语言码→区域码映射(ko→kr/ja→jp/hi→in/vi→vn);
     表外市场/无 domains 输入 → skipped 并记原因。stdout 解析:占位命中数 + UGC/比价/投诉分席
     (投诉/评测占位=信任面警告)。

输出:跨市场对比周报 markdown(每市场 lint 通过/CRITICAL/WARN/占位命中/投诉警告并排 +
逐市场明细)+ 单市场失败不拖垮(失败步骤记原因续跑;退出码 1 汇总,2 用法错)。
--json: 结构化(agent 消费);--out FILE: 周报另存文件。

环境变量: SEO_MARKET_BATCH_SCRIPTS_DIR 覆盖被编排脚本目录(默认本脚本所在目录;测试打桩用。
markets.json 校验与占位表恒读本脚本同目录,不受打桩影响)。
SEO_MARKET_BATCH_LINT_TIMEOUT / _OCC_TIMEOUT 覆盖子进程超时秒(默认 120/60)。

用法: python3 market_batch.py --decl markets.yaml [--out weekly.md] [--json]
退出码: 0 全部步骤执行成功(skipped 合法) / 1 存在执行失败的市场步骤 / 2 输入或用法错。"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

SCHEMA_VERSION = 1
PY = sys.executable or "python3"
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.environ.get("SEO_MARKET_BATCH_SCRIPTS_DIR") or HERE)
LINT_TIMEOUT_S = int(os.environ.get("SEO_MARKET_BATCH_LINT_TIMEOUT", "120"))
OCC_TIMEOUT_S = int(os.environ.get("SEO_MARKET_BATCH_OCC_TIMEOUT", "60"))

# 语言市场码 → serp_occupancy 占位表区域码(markets.json serp_occupancy 键为区域码)
REGION_OF = {"tr": "tr", "th": "th", "hi": "in", "ko": "kr", "ja": "jp", "vi": "vn", "ru": "ru"}

USAGE = __doc__


class UsageError(Exception):
    """输入/用法错(退出码 2)。"""


def die(msg):
    raise UsageError(msg)


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def script_path(name):
    return os.path.join(SCRIPTS_DIR, name)


def load_markets_json():
    """markets.json(恒读本脚本同目录,不受打桩影响)→ (markets, serp_occupancy 表)。"""
    with open(os.path.join(HERE, "markets.json"), encoding="utf-8") as f:
        data = json.load(f)
    return data.get("markets", {}), data.get("serp_occupancy", {})


# ---------------------------------------------------------------------------
# 声明文件(受限 YAML 子集:顶层 site 标量 + 重复 market 块 + key_pages/domains 列表
# + domains_file 标量;键必须顶格,列表项必须缩进,未知行拒收——照 project.py 风格)
# ---------------------------------------------------------------------------

def _unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_decl(path):
    """解析声明 → {"site": str, "markets": [{market, key_pages, domains, domains_file}]}。"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        die("声明文件不可读: %s" % e)
    site, blocks, cur, cur_list = None, [], None, None
    seen = set()
    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m_site = re.match(r"^site\s*:\s*(.+?)\s*$", line)
        m_mkt = re.match(r"^market\s*:\s*([A-Za-z]{2})\s*$", line)
        m_list = re.match(r"^(key_pages|domains)\s*:\s*$", line)
        m_file = re.match(r"^(domains_file)\s*:\s*(.+?)\s*$", line)
        m_item = re.match(r"^\s+-\s+(.+?)\s*$", line)
        if m_site:
            site = _unquote(m_site.group(1))
            cur = cur_list = None
        elif m_mkt:
            cur = {"market": m_mkt.group(1).lower(), "key_pages": [], "domains": [],
                   "domains_file": None}
            blocks.append(cur)
            cur_list = None
            if cur["market"] in seen:
                die("第 %d 行:市场 %s 重复声明(笔误?请合并为一个块)" % (ln, cur["market"]))
            seen.add(cur["market"])
        elif m_list:
            if cur is None:
                die("第 %d 行: %s 须在 market: 块内" % (ln, m_list.group(1)))
            cur_list = cur[m_list.group(1)]
        elif m_file:
            if cur is None:
                die("第 %d 行: domains_file 须在 market: 块内" % ln)
            cur["domains_file"] = _unquote(m_file.group(2))
            cur_list = None
        elif m_item:
            if cur_list is None:
                die("第 %d 行: 列表项缩进错位(须紧跟 key_pages:/domains: 之下): %s" % (ln, line.strip()))
            cur_list.append(_unquote(m_item.group(1)))
        else:
            die("第 %d 行无法解析(受限子集:site/market/key_pages/domains/domains_file): %s"
                % (ln, line.strip()))
    if not site:
        die("声明缺 site: 顶层标量")
    if not blocks:
        die("声明缺 market: 块(至少一个市场)")
    for b in blocks:
        if not b["key_pages"]:
            die("市场 %s 缺 key_pages(≥1;首个=lint 代表页)" % b["market"])
    return {"site": site, "markets": blocks}


def read_domains_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("domains_file 不可读: %s" % e)
    return [d for d in re.split(r"[\s,;]+", text) if d]


# ---------------------------------------------------------------------------
# 子步骤(单市场失败不拖垮:异常/超时/坏输出都收敛为 rec,批量继续)
# ---------------------------------------------------------------------------

def _run(cmd, timeout):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"rc": None, "stdout": "", "stderr": "", "error": "超时(>%ss)被终止" % timeout,
                "duration_s": round(time.monotonic() - t0, 2)}
    except OSError as e:
        return {"rc": None, "stdout": "", "stderr": "", "error": str(e),
                "duration_s": round(time.monotonic() - t0, 2)}
    return {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "error": None,
            "duration_s": round(time.monotonic() - t0, 2)}


def run_lint(code, page):
    """market_lint --json 子进程 → 摘要 rec;rc∈(0,1)=执行成功(critical 是有效结果)。"""
    cmd = [PY, script_path("market_lint.py"), "--market", code, "--json"]
    cmd += (["--url", page] if re.match(r"^https?://", page) else [page])
    r = _run(cmd, LINT_TIMEOUT_S)
    rec = {"cmd": cmd, "ran": True, "ok": False, "rc": r["rc"], "pass": False,
           "critical": None, "warn": None, "top_lines": [], "error": r["error"],
           "duration_s": r["duration_s"]}
    if r["error"]:
        return rec
    try:
        data = json.loads(r["stdout"])
        rec.update({"critical": int(data.get("critical", 0)), "warn": int(data.get("warn", 0)),
                    "pass": int(data.get("critical", 0)) == 0})
        rec["top_lines"] = [l for l in (data.get("output") or [])
                            if l.startswith(("[CRITICAL]", "[WARN]", "[v3-FAIL]"))][:3]
        rec["ok"] = r["rc"] in (0, 1)
        if not rec["ok"]:
            rec["error"] = "market_lint 退出码 %s(2=用法/输入错)" % r["rc"]
    except ValueError:
        rec["error"] = "market_lint --json 输出不可解析(rc=%s)" % r["rc"]
    return rec


def run_occupancy(code, domains):
    """serp_occupancy 子进程 → 摘要 rec;表外/无输入=skipped(合法),rc≠0=执行失败。"""
    _markets, table = load_markets_json()
    region = REGION_OF.get(code)
    rec = {"cmd": None, "ran": False, "status": None, "region": region,
           "ok": True, "rc": None, "hits": None, "serp_total": None,
           "ugc": None, "price": None, "complaint": None, "error": None, "reason": None}
    if region is None or region not in table:
        rec["status"] = "skipped"
        rec["reason"] = ("占位表无该市场区域(现有表: %s)——语言码 %s 无对应区域码"
                         % (", ".join(sorted(table)), code))
        return rec
    if not domains:
        rec["status"] = "skipped"
        rec["reason"] = ("无 domains 输入(声明 domains: 列表或 domains_file: 文件,"
                         "喂该市场品牌词 top10 域)")
        return rec
    cmd = [PY, script_path("serp_occupancy.py"), "--market", region, ",".join(domains)]
    rec["cmd"] = cmd
    r = _run(cmd, OCC_TIMEOUT_S)
    rec["ran"] = True
    if r["error"]:
        rec.update({"ok": False, "status": "failed", "error": r["error"],
                    "duration_s": r["duration_s"]})
        return rec
    if r["rc"] != 0:
        tail = " | ".join((r["stderr"] or r["stdout"] or "").strip().splitlines()[-2:])
        rec.update({"ok": False, "status": "failed", "rc": r["rc"],
                    "error": ("serp_occupancy 退出码 %s: %s" % (r["rc"], tail[:200]))
                             or "退出码 %s(无输出)" % r["rc"]})
        return rec
    out = r["stdout"]
    m_hits = re.search(r"占位表命中\s+(\d+)", out)
    m_serp = re.search(r"SERP\s+(\d+)\s*席", out)
    m_cats = re.search(r"UGC 平台\s+(\d+)\s*席 \| 比价\s+(\d+)\s*席 \| 投诉/评测\s+(\d+)\s*席", out)
    rec.update({"status": "ok", "ok": True,
                "hits": int(m_hits.group(1)) if m_hits else None,
                "serp_total": int(m_serp.group(1)) if m_serp else None,
                "ugc": int(m_cats.group(1)) if m_cats else None,
                "price": int(m_cats.group(2)) if m_cats else None,
                "complaint": int(m_cats.group(3)) if m_cats else None})
    return rec


def run_batch(decl, decl_path):
    results = []
    for b in decl["markets"]:
        code = b["market"]
        domains = list(b["domains"])
        if b["domains_file"]:
            domains += read_domains_file(b["domains_file"])
        lint = run_lint(code, b["key_pages"][0])
        occ = run_occupancy(code, domains)
        results.append({"market": code, "key_pages": b["key_pages"],
                        "rep_page": b["key_pages"][0], "lint": lint, "occupancy": occ})
    return {"schema_version": SCHEMA_VERSION, "tool": "market_batch.py",
            "generated_at": now_utc_iso(), "site": decl["site"], "decl": decl_path,
            "markets": results}


# ---------------------------------------------------------------------------
# 周报 markdown
# ---------------------------------------------------------------------------

def render_report(batch):
    rows = batch["markets"]
    n_pass = sum(1 for r in rows if r["lint"]["ran"] and r["lint"]["pass"])
    n_lint = sum(1 for r in rows if r["lint"]["ran"])
    occ_warn = sum((r["occupancy"].get("complaint") or 0) for r in rows)
    L = ["# 多市场周报 — %s" % batch["site"],
         "",
         "生成: %s | 声明: `%s` | 市场 %d 个 | lint 通过 %d/%d(market_lint 代表页口径:key_pages[0])"
         % (batch["generated_at"], batch["decl"], len(rows), n_pass, n_lint),
         "",
         "## 跨市场并排",
         "",
         "| 市场 | lint | CRIT | WARN | 占位命中 | UGC/比价/投诉 | 投诉警告 | 备注 |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lint, occ = r["lint"], r["occupancy"]
        if not lint["ran"]:
            cell_l, cell_c, cell_w = "✗ 执行失败", "—", "—"
        else:
            cell_l = "✓" if lint["pass"] else "✗"
            cell_c, cell_w = str(lint["critical"]), str(lint["warn"])
        if occ.get("status") == "ok":
            cell_h = "%s/%s" % (occ["hits"] if occ["hits"] is not None else "?",
                                occ["serp_total"] if occ["serp_total"] is not None else "?")
            cell_u = "%s/%s/%s" % (occ["ugc"], occ["price"], occ["complaint"])
            cell_cw = ("⚠ %s" % occ["complaint"]) if occ["complaint"] else "0"
        else:
            cell_h = cell_u = cell_cw = "—"
        notes = []
        if lint.get("error"):
            notes.append("lint 失败: %s" % lint["error"])
        elif lint["ran"] and not lint["pass"] and lint["top_lines"]:
            notes.append(lint["top_lines"][0][:60])
        if occ.get("status") == "skipped":
            notes.append("占位跳过")
        elif occ.get("error"):
            notes.append("占位失败: %s" % occ["error"])
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["market"], cell_l, cell_c, cell_w, cell_h, cell_u, cell_cw,
            ";".join(notes) if notes else "—"))
    L += ["",
          "lint 通过率: %d/%d 市场;投诉/评测类占位警告合计: %d(占位=信任面失守信号,投诉类优先处理)"
          % (n_pass, n_lint, occ_warn),
          "", "## 逐市场明细", ""]
    for r in rows:
        lint, occ = r["lint"], r["occupancy"]
        L.append("### %s — 代表页 %s" % (r["market"], r["rep_page"]))
        if lint["ran"]:
            L.append("- market_lint: %s(CRITICAL %s/WARN %s;退出码 %s)"
                     % ("PASS" if lint["pass"] else "FAIL", lint["critical"],
                        lint["warn"], lint["rc"]))
            for ln in lint["top_lines"]:
                L.append("  - %s" % ln[:120])
        else:
            L.append("- market_lint: 执行失败 — %s" % lint["error"])
        if occ.get("status") == "ok":
            L.append("- serp_occupancy(%s): SERP %s 席命中 %s;UGC %s/比价 %s/投诉 %s"
                     % (occ["region"], occ["serp_total"], occ["hits"],
                        occ["ugc"], occ["price"], occ["complaint"]))
        elif occ.get("status") == "skipped":
            L.append("- serp_occupancy: 跳过(%s)" % occ["reason"])
        else:
            L.append("- serp_occupancy: 失败(%s)" % occ["error"])
        L.append("")
    L += ["失败市场不拖垮: 单市场步骤失败只记因续跑;退出码 1=存在执行失败(见上),0=全部执行成功。",
          "下一轮: 更新各市场 domains_file(品牌词 top10 域)后重跑;lint FAIL 页回修后单独复跑 market_lint。"]
    return "\n".join(L)


def summarize(batch):
    rows = batch["markets"]
    failed = ["%s:%s" % (r["market"], step)
              for r in rows for step, rec in (("lint", r["lint"]), ("occupancy", r["occupancy"]))
              if rec.get("error") and rec.get("status") != "skipped"]
    return {"markets": len(rows),
            "lint_pass": sum(1 for r in rows if r["lint"]["ran"] and r["lint"]["pass"]),
            "lint_ran": sum(1 for r in rows if r["lint"]["ran"]),
            "occ_complaint_total": sum((r["occupancy"].get("complaint") or 0) for r in rows),
            "failed_steps": failed}


def main(argv=None):
    ap = argparse.ArgumentParser(description=USAGE,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decl", required=True, help="多市场批量声明 YAML(受限子集,见 --help)")
    ap.add_argument("--out", help="周报 markdown 另存路径(缺省仅打印)")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    ns = ap.parse_args(argv)

    decl = parse_decl(ns.decl)
    markets, _table = load_markets_json()
    bad = [b["market"] for b in decl["markets"] if b["market"] not in markets]
    if bad:
        print("market_batch.py: 声明含未知市场 %s;可用: %s"
              % (",".join(bad), ", ".join(sorted(markets))), file=sys.stderr)
        return 2

    batch = run_batch(decl, os.path.abspath(ns.decl))
    batch["summary"] = summarize(batch)
    report = render_report(batch)
    if ns.out:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    if ns.json:
        print(json.dumps(batch, ensure_ascii=False, indent=1))
    else:
        print(report)
    return 1 if batch["summary"]["failed_steps"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except UsageError as e:
        print("market_batch.py: %s" % e, file=sys.stderr)
        sys.exit(2)
