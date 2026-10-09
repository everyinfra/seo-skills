#!/usr/bin/env python3
"""skill 自检:frontmatter 规范 + 模板七段式 + 死链。任何一项失败即退出码 1。"""
import os, re, sys, subprocess
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(BASE, 'SKILL.md')).read()
fail = []
m = re.match(r'^---\n(.*?)\n---\n', s, re.S)
if not m:
    fail.append('no frontmatter')
else:
    fm = m.group(1)
    name = re.search(r'name:\s*(\S+)', fm)
    desc = re.search(r'description:\s*(.*)', fm)
    if not name or not re.match(r'^[a-z0-9-]{1,64}$', name.group(1)):
        fail.append(f'name violates convention: {name and name.group(1)}')
    if not desc or len(desc.group(1)) > 1024:
        fail.append(f'description exceeds 1024 chars: {len(desc.group(1)) if desc else 0}')
    if len(s.splitlines()) > 500:
        fail.append(f'SKILL.md too long: {len(s.splitlines())} lines')
templates = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(BASE, 'templates')) for f in fs if f.endswith('.md')]
for t in templates:
    body = open(t).read()
    for sec in ['The answer', 'What could change this conclusion', 'Method Notes']:
        if sec not in body:
            fail.append(f'{os.path.relpath(t, BASE)} missing section: {sec}')
r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'link_check.py')], capture_output=True, text=True)
if r.returncode != 0:
    fail.append('link check failed:\n' + r.stdout)
if fail:
    print('SELF-CHECK FAILED:')
    for f in fail:
        print(' -', f)
    sys.exit(1)
print(f'OK: frontmatter compliant, {len(templates)} templates carry the 7-section structure, links clean')
