#!/bin/bash
# 预置:开局 6 环做完、方案已定稿,方案里有一条用户自定义的 Reddit 外链打法;之后用户说「不做 Reddit 外链」。
set -e
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$here"
while [ "$root" != "/" ] && [ ! -f "$root/.claude-plugin/plugin.json" ]; do root="$(dirname "$root")"; done
S="$root/skills/seo-suite/scripts"
[ -f "$S/onboard.py" ] || { echo "scaffold: 找不到插件的 scripts/(从 $here 往上找 .claude-plugin/plugin.json)" >&2; exit 1; }
cat > scan.json <<'JSON'
{"schema": 1, "site": "https://acme.example",
 "signals": {"site_live": true, "robots_block_all": false, "homepage_noindex": false, "url_count": 400,
             "first_seen": "2025-06-01", "has_llms_txt": true, "analytics": ["gtag"]},
 "site_scan": {"page_types": {"pricing": 1, "docs": 30, "blog": 40}},
 "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
           {"key": "product.lines", "value": ["Invoicing"], "source": "llms.txt", "kind": "inferred"}],
 "errors": []}
JSON
mkdir -p seo-ops/playbook
cat > seo-ops/playbook/plays.json <<'JSON'
{"plays": [{"id": "reddit-threads", "stages": [3], "theme": "links", "dims": ["authority"], "base": 50,
  "title": "在 Reddit 相关版块发帖拿外链", "title_en": "Earn links from Reddit threads",
  "do": "每周在 Reddit 回 5 个和 {main_line} 有关的帖子并带链接", "do_en": "Answer 5 Reddit threads a week",
  "page_types": ["博客"], "metric": "引荐域", "measure": "backlink_import.py", "week": 1, "weeks": 13,
  "tags": ["外链", "reddit"], "ref": "", "cmd": ""}]}
JSON
O() { python3 "$S/onboard.py" "$@" >/dev/null; }
O start --site https://acme.example --scan scan.json --market en
O answer --ring 1 --set profile_ok=ok --set conversion=signup --set customers=SMB --set main_line=Invoicing --quote ok --confirm
O show --ring 2; O answer --ring 2 --set jargon=invoice --quote ok --confirm
O show --ring 3; O answer --ring 3 --set real_competitors=Rival --quote ok --confirm
O show --ring 4; O answer --ring 4 --set capacity=4 --quote ok --confirm
O show --ring 5; O answer --ring 5 --set market_first=en --set deny_topics=none --quote ok --confirm
O show --ring 6
python3 "$S/plan.py" build --ws seo-ops >/dev/null
O answer --ring 6 --set approve_plan=可以 --quote 可以 --confirm
# 定稿日固定成 2030-01-01,提问里的 --date 2030-01-07 就落在方案第 2 周(不随跑评测那天变)
python3 - <<'PY'
import json, os
p = "seo-ops/plan/plan.json"
d = json.load(open(p, encoding="utf-8"))
d["approved_at"] = "2030-01-01T00:00:00Z"
with open(p + ".tmp", "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
os.replace(p + ".tmp", p)
PY
python3 "$S/teach.py" rule add --quote "别再建议我们去做 Reddit 外链了,我们不做" --deny reddit >/dev/null
git init -q . && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm init
