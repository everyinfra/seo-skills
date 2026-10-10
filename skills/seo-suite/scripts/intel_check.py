#!/usr/bin/env python3
"""信源检查器:拉取 intel-sources.md 的源→与上次状态对比→输出变更报告。
用法:
  intel_check.py init              # 首次建基线(.intel-state.json)
  intel_check.py check             # 拉全部源→diff→报告(变更源列表+受影响模块映射)
  intel_check.py check --source google-blog  # 只查指定源
输出: 变更源+变更摘要+应更新的套件文件列表(基于 source→module 映射)
退出码: 0=无变更 / 1=有变更(触发更新流程) / 2=错误"""
import sys, os, json, re, hashlib, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = "Mozilla/5.0 (compatible; seo-suite-intel/1.0)"
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", ".intel-state.json")

# 源注册表:与 references/overview/intel-sources.md 同步维护
SOURCES = {
    "google-blog": {"url": "https://developers.google.com/search/blog/feed.xml", "type": "rss",
        "modules": ["content/geo-evidence.md", "technical/validation-guide.md", "content/llms-txt-guide.md"]},
    "google-updates": {"url": "https://developers.google.com/search/updates", "type": "hash",
        "modules": ["technical/validation-guide.md", "technical/audit-rule-catalog.md"]},
    "gsc-announce": {"url": "https://support.google.com/webmasters/announcements", "type": "hash",
        "modules": ["overview/intake-checklists.md", "monitoring/kpi-definitions.md"]},
    "status-dashboard": {"url": "https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history", "type": "hash",
        "modules": ["monitoring/seo-drift-monitoring.md"]},
    "lighthouse": {"url": "https://github.com/googlechrome/lighthouse/releases.atom", "type": "rss",
        "modules": ["technical/agent-readiness.md", "technical/agent-protocols.md"]},
    "bing-wm": {"url": "https://blogs.bing.com/webmaster/feed", "type": "rss",
        "modules": ["content/geo-platform-differences.md"]},
    "openai-bots": {"url": "https://developers.openai.com/api/docs/bots", "type": "hash",
        "modules": ["technical/ai-crawler-policy.md"]},
    "ard-spec": {"url": "https://github.com/ards-project/ard-spec/commits/main.atom", "type": "rss",
        "modules": ["technical/agent-protocols.md", "technical/agent-readiness.md"]},
    "anthropic-crawl": {"url": "https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler", "type": "hash",
        "modules": ["technical/ai-crawler-policy.md"]},
    "schema-org": {"url": "https://schema.org/docs/releases.html", "type": "hash",
        "modules": ["technical/schema-templates.md", "technical/schema-examples.md"]},
    "crux": {"url": "https://developer.chrome.com/docs/crux/release-notes/", "type": "hash",
        "modules": ["technical/cwv-playbook.md"]},
    "yandex-wm": {"url": "https://yandex.com/support/webmaster/en/new-features", "type": "hash",
        "modules": ["markets/ru.md", "references/markets/ru.md"]},
    "naver-wm": {"url": "https://searchadvisor.naver.com/", "type": "hash",
        "modules": ["markets/ko.md", "technical/naver-searchadvisor.md"]},
    "baidu-ziyuan": {"url": "https://ziyuan.baidu.com/", "type": "hash",
        "modules": ["markets/zh.md", "content/chinese-ai-search-guide.md"]},
    "statcounter-search": {"url": "https://gs.statcounter.com/search-engine-market-share", "type": "hash",
        "modules": ["overview/multilingual-workflow.md"]},
    "statcounter-ai": {"url": "https://gs.statcounter.com/ai-chatbot-market-share", "type": "hash",
        "modules": ["content/geo-platform-differences.md"]},
    "semrush-sensor": {"url": "https://www.semrush.com/sensor/", "type": "hash",
        "modules": ["monitoring/seo-drift-monitoring.md"]},
    "seroundtable": {"url": "https://www.seroundtable.com/index.xml", "type": "rss",
        "modules": ["monitoring/penalty-recovery.md", "technical/rendering-seo.md"]},
}

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(2_000_000).decode("utf-8", "replace")

def get_rss_items(xml_text, limit=5):
    """提取 RSS/Atom 最近 N 条: (title, link, date)"""
    items = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "rss": "http://purl.org/rss/1.0/"}
        # RSS 2.0
        for item in root.iter("item"):
            t = (item.findtext("title") or "").strip()
            l = (item.findtext("link") or "").strip()
            d = (item.findtext("pubDate") or "").strip()
            items.append((t, l, d))
        # Atom
        if not items:
            for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
                t = (e.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                l = (e.findtext("{http://www.w3.org/2005/Atom}link") or "").strip()
                d = (e.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
                items.append((t, l, d))
    except ET.ParseError:
        pass
    return items[:limit]

def content_hash(text):
    # 去时间戳/随机段后哈希,减假阳性
    text = re.sub(r"\d{4}-\d{2}-\d{2}T[\d:.+Z-]+", "", text)
    text = re.sub(r"csrf|nonce|_token|cache[-_]?bust\w*", "", text, flags=re.I)
    return hashlib.sha256(text.encode()).hexdigest()[:32]

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"checked_at": None, "sources": {}}

def save_state(state):
    state["checked_at"] = datetime.now(timezone.utc).isoformat()
    json.dump(state, open(STATE_FILE, "w"), indent=1)

def check_source(name, cfg, prev):
    """返回 (changed:bool, detail:str)"""
    try:
        body = fetch(cfg["url"])
    except Exception as e:
        return False, f"fetch_error: {type(e).__name__}"
    h = content_hash(body)
    if cfg["type"] == "hash":
        if prev and prev.get("hash") == h:
            return False, ""
        return (prev is not None), f"hash:{h[:12]}"
    # rss
    items = get_rss_items(body)
    if not items:
        # fallback: hash comparison if rss parsing failed
        if prev and prev.get("hash") == h:
            return False, ""
        return (prev is not None and "top" not in (prev or {})), f"hash:{h[:12]}"
    top = items[0][0]
    if prev and prev.get("top") == top:
        return False, ""
    new_items = [t for t, _, _ in items if not (prev and t in prev.get("seen", []))]
    return True, " | ".join(t[:60] for t in new_items[:3]) or f"top: {top[:60]}"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    if "--source" in sys.argv:
        only = sys.argv[sys.argv.index("--source") + 1]
    state = load_state()
    if args and args[0] == "init":
        sources = state["sources"]
        for name, cfg in SOURCES.items():
            if only and name != only: continue
            try:
                body = fetch(cfg["url"])
                if cfg["type"] == "rss":
                    items = get_rss_items(body)
                    sources[name] = {"top": items[0][0] if items else content_hash(body),
                                     "seen": [t for t, _, _ in items], "ts": datetime.now(timezone.utc).isoformat()}
                else:
                    sources[name] = {"hash": content_hash(body), "ts": datetime.now(timezone.utc).isoformat()}
                print(f"  init {name}: ok")
            except Exception as e:
                print(f"  init {name}: {type(e).__name__} (skip)")
        save_state(state)
        print("基线已建;下次 check 检测变更")
        return
    # check mode
    changed_sources = []
    errors = []
    for name, cfg in SOURCES.items():
        if only and name != only: continue
        prev = state["sources"].get(name)
        try:
            ch, detail = check_source(name, cfg, prev)
            if ch:
                changed_sources.append((name, detail, cfg["modules"]))
                # update state
                body = fetch(cfg["url"])  # refetch for state
                if cfg["type"] == "rss":
                    items = get_rss_items(body)
                    old_seen = state["sources"].get(name, {}).get("seen", [])
                    seen = old_seen + [t for t, _, _ in items if t not in old_seen]
                    state["sources"][name] = {"top": items[0][0] if items else content_hash(body),
                                              "seen": seen[-50:], "ts": datetime.now(timezone.utc).isoformat()}
                else:
                    state["sources"][name] = {"hash": content_hash(body), "ts": datetime.now(timezone.utc).isoformat()}
            elif detail.startswith("fetch_error"):
                errors.append((name, detail))
        except Exception as e:
            errors.append((name, str(e)))
    save_state(state)
    if changed_sources:
        print(f"=== {len(changed_sources)} 个信源变更 ===")
        affected = set()
        for name, detail, mods in changed_sources:
            print(f"[CHANGED] {name}: {detail}")
            for m in mods:
                affected.add(m)
                print(f"  → 应更新: references/{m}")
        print(f"\n受影响文件共 {len(affected)} 个")
        print("\n下一步: 按 self-update-protocol.md 逐个更新 → self_check → commit")
        sys.exit(1)
    else:
        print(f"无变更(已查 {len([n for n in SOURCES if not only or n == only])} 源;{len(errors)} 错误)")
        for n, e in errors[:3]: print(f"  err {n}: {e}")
        sys.exit(0)

if __name__ == "__main__": main()
