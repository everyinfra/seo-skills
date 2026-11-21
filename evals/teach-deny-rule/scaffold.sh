#!/bin/bash
# 预置一个已有 seo-ops/ 的站点仓(还没有 playbook)
set -e
mkdir -p seo-ops
printf 'site: https://example.com\nmarket: en\n' > seo-ops/project.yaml
git init -q . && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm init
