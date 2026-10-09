#!/usr/bin/env python3
"""校验 skill 内部 markdown 链接全部可达(SKILL.md 的 references/ 风格 + 参考文件间的相对链接)。"""
import os, re, sys, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
broken = []
for f in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
    t = open(f).read()
    rel = os.path.relpath(f, BASE)
    for m in re.finditer(r'\]\(([^)http][^)]*?\.md)(#[^)]*)?\)', t):
        target = os.path.normpath(os.path.join(os.path.dirname(f), m.group(1)))
        if not os.path.exists(target):
            broken.append((rel, m.group(1)))
if broken:
    for b in broken:
        print('BROKEN:', b)
    sys.exit(1)
print('OK: all internal markdown links resolve')
