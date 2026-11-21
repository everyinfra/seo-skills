#!/usr/bin/env python3
"""ops install 写进站点仓的钩子要找得到真实安装位置(RQ-237 第 4 批第 10 项;stdlib unittest,零网络)。

期望值来源:
- 红队意见 13(需求卡 RQ-237 第 7 节):「ops.py 写死 $HOME/.claude/skills,插件安装会失效,第 4 批修」。
  这里模拟的就是这种安装:skill 不在 ~/.claude/skills,而在 ~/.agents/skills(npx skills / 其他宿主的位置)。
- 钩子退出码的意思来自 Claude Code 官方 hooks 文档:PreToolUse 退出码 2 = 拦下(stderr 给模型看),0 = 放行;
  guard_hook.py 文件头同样写着「退出码 2 = 拦下;0 = 放行」。
- pre-push 钩子:SKILL.md 原则 3「不推主干」——编码 agent(带 CLAUDECODE)推 main 要被拒(退出码非 0)。
修前(origin/main 的 ops.py):钩子命令是 `python3 "$HOME/.claude/skills/.../guard_hook.py"`,文件不存在 →
python 报 can't open file、退出码 2,于是分支上的正常编辑也被拦;pre-push 钩子 `[ -f "$G" ] || exit 0` 直接放行推 main。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _copy_skill(dst):
    """只复制 scripts/、data/ 和 VERSION(钩子和 install 用得到的),够模拟一次安装。"""
    os.makedirs(dst)
    shutil.copytree(os.path.join(BASE, "scripts"), os.path.join(dst, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(BASE, "data"), os.path.join(dst, "data"))
    shutil.copy(os.path.join(BASE, "VERSION"), os.path.join(dst, "VERSION"))


class InstallPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="installpath_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.skill = os.path.join(self.home, ".agents", "skills", "seo-suite")
        _copy_skill(self.skill)
        self.repo = os.path.join(self.tmp, "site")
        os.makedirs(os.path.join(self.repo, "seo-ops"))
        with open(os.path.join(self.repo, "seo-ops", "project.yaml"), "w", encoding="utf-8") as f:
            f.write("site: https://example.com\nmarket: en\n")
        # 测试进程自己的环境里可能有 CLAUDE_PLUGIN_ROOT / SEO_SUITE_DIR(在插件会话里跑测试时),全部去掉
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_PLUGIN_ROOT", "SEO_SUITE_DIR", "CLAUDECODE", "AI_AGENT")}
        self.env.update(HOME=self.home, PYTHONIOENCODING="utf-8")
        subprocess.run(["git", "init", "-q", self.repo], check=True, env=self.env)
        r = subprocess.run([sys.executable, os.path.join(self.skill, "scripts", "project.py"), "ops", "install",
                            "--repo", self.repo], cwd=self.repo, capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def hook_command(self):
        with open(os.path.join(self.repo, ".claude", "settings.json"), encoding="utf-8") as f:
            s = json.load(f)
        cmds = [h["command"] for g in s["hooks"]["PreToolUse"] for h in g["hooks"] if "guard_hook.py" in h["command"]]
        self.assertEqual(len(cmds), 1, cmds)
        return cmds[0]

    def run_hook(self, event):
        return subprocess.run(["sh", "-c", self.hook_command()], input=json.dumps(event), capture_output=True,
                              text=True, cwd=self.repo, env=self.env)

    def test_pretooluse_hook_finds_skill_outside_claude_skills(self):
        blocked = self.run_hook({"tool_name": "Write", "_branch": "main",
                                 "tool_input": {"file_path": os.path.join(self.repo, "robots.txt"), "content": "x"}})
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertIn("seo-suite 拦下", blocked.stderr)
        ok = self.run_hook({"tool_name": "Write", "_branch": "seo/title-fix",
                            "tool_input": {"file_path": os.path.join(self.repo, "robots.txt"), "content": "x"}})
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_pre_push_hook_finds_skill_outside_claude_skills(self):
        hook = os.path.join(self.repo, ".git", "hooks", "pre-push")
        self.assertTrue(os.path.isfile(hook))
        env = dict(self.env, CLAUDECODE="1")
        r = subprocess.run(["sh", hook, "origin", "git@example.com:x/y.git"], input="refs/heads/main a refs/heads/main b\n",
                           capture_output=True, text=True, cwd=self.repo, env=env)
        self.assertNotEqual(r.returncode, 0, "编码 agent 推 main 没被拒:" + r.stderr)

    def test_written_files_carry_no_absolute_home(self):
        """装进站点仓(会提交)的文件不带本机用户目录:安装位置写成 $HOME 相对路径。"""
        for rel in (os.path.join(".claude", "settings.json"), os.path.join("seo-ops", "schedule", "cloud-agent-prompt.md"),
                    "AGENTS.md"):
            with open(os.path.join(self.repo, rel), encoding="utf-8") as f:
                self.assertNotIn(self.home, f.read(), rel)


if __name__ == "__main__":
    unittest.main()
