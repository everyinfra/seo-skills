#!/usr/bin/env python3
"""fix_plan.py --git-branch 发布通道测试(R1-10;standalone、合成 fixture、零网络,
tests/run_tests.py 自动发现本文件)。临时 git 仓库(init/config user)验证五件事:
分支创建并提交 seo-fixes/ 修复物 / 主干不受影响(原分支 ref 不动,切回后工作树无 seo-fixes)、
非 git 仓库退出码 2 且不写任何文件 / 失败(pre-commit 钩子拒绝提交)回退原分支并删除半成品分支 /
建议的 PR 只打印 gh pr create 命令行、绝不自动执行(外发动作人审边界)。
用法: python3 tests/test_fix_plan_branch.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
FIX_PLAN = os.path.join(SCRIPTS, "fix_plan.py")
sys.path.insert(0, SCRIPTS)

GIT_MISSING = shutil.which("git") is None

# 隔离宿主 git 全局/系统配置(core.hooksPath/commit.gpgsign 等不污染本测试的仓库语义)
HERMETIC_ENV = dict(os.environ, PYTHONIOENCODING="utf-8",
                    GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

ROOT = "https://unit.test"


def audit_payload():
    """合成 site_audit --json 输出:robots/llms.txt 不可达 + title 缺失 → robots/llms 两类修复物。"""
    findings = [
        {"severity": "CRITICAL", "area": "title", "message": "缺失"},
        {"severity": "INFO", "area": "robots", "message": "//robots.txt 不可达"},
        {"severity": "INFO", "area": "llms.txt", "message": "//llms.txt 不可达"},
    ]
    ai = {"score": 30,
          "bots": {"allowed": ["Googlebot"], "blocked": ["PerplexityBot"]},
          "checks": [{"id": "bots", "pass": False, "detail": "被禁: PerplexityBot"},
                     {"id": "llms_txt", "pass": False, "detail": "/llms.txt 缺失/404(notice)"},
                     {"id": "freshness", "pass": True, "detail": ""},
                     {"id": "semantic_html", "pass": False, "detail": ""},
                     {"id": "content_length", "pass": True, "detail": ""},
                     {"id": "bluf", "pass": False, "detail": ""}]}
    return {"audited": 1, "critical": 1,
            "results": {ROOT + "/": {"verdict": "fail", "findings": findings,
                                     "meta": {"title": "", "words": 12, "jsonld": 0},
                                     "ai_search_health": ai}}}


def make_git_repo(hook_fails=False):
    """临时 git 仓库(init + 本地 user 配置 + 一个 base 提交);hook_fails=True 装
    必败 pre-commit 钩子(验证失败回退)。返回仓库路径。"""
    d = tempfile.mkdtemp(prefix="fp-git-")

    def git(*args):
        p = subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, env=HERMETIC_ENV)
        assert p.returncode == 0, "git %s: %s" % (args, p.stderr)
        return p.stdout.strip()

    git("init", "-q")
    git("config", "user.email", "test@example.test")
    git("config", "user.name", "Test")
    git("config", "commit.gpgsign", "false")
    with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
        f.write("base\n")
    git("add", "README.md")
    git("commit", "-q", "-m", "base")
    if hook_fails:
        hook = os.path.join(d, ".git", "hooks", "pre-commit")
        with open(hook, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\nexit 1\n")
        os.chmod(hook, 0o755)
    return d


def repo_git(repo, *args):
    """在临时仓库里跑 git(不断言成功,供事后核验用)。"""
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=HERMETIC_ENV)


@unittest.skipIf(GIT_MISSING, "git 不可用,跳过 --git-branch 通道测试")
class GitBranchModeTests(unittest.TestCase):
    """--apply --git-branch:建分支+提交 / 主干不受影响 / 非 git 退出 2 / 失败回退 / gh 只打印"""

    def setUp(self):
        self.repo = make_git_repo()
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.audit_path = os.path.join(self.repo, "audit.json")
        with open(self.audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_payload(), f, ensure_ascii=False)
        out = repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD")
        self.orig_branch = out.stdout.strip()
        self.orig_sha = repo_git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def run_cli(self, *flags):
        return subprocess.run(
            [sys.executable, FIX_PLAN, "--audit", self.audit_path, *flags],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env=HERMETIC_ENV, timeout=120)

    def test_branch_created_files_committed_main_untouched(self):
        r = self.run_cli("--only", "robots,llms", "--apply",
                         "--git-branch", "feat/seo-fixes-test", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        # 分支创建:提交落在 feat 分支上,git_branch/pr 结构齐全
        self.assertEqual(data["git_branch"]["branch"], "feat/seo-fixes-test")
        self.assertEqual(data["git_branch"]["original"], self.orig_branch)
        self.assertTrue(data["git_branch"]["commit"])
        self.assertTrue(data["pr"]["command"].startswith("gh pr create"))
        self.assertEqual(repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
                         "feat/seo-fixes-test")
        # 文件提交:分支树里有 seo-fixes/ 修复物,与 applied_files 一致
        tree = repo_git(self.repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.split()
        written = {os.path.basename(p) for p in data["applied_files"]}
        self.assertEqual(written, {"robots.txt", "llms.txt"})
        self.assertEqual({"seo-fixes/" + w for w in written} & set(tree),
                         {"seo-fixes/robots.txt", "seo-fixes/llms.txt"})
        # 主干不受影响:原分支 ref 不动,README 未被改写
        self.assertEqual(repo_git(self.repo, "rev-parse", self.orig_branch).stdout.strip(),
                         self.orig_sha)
        with open(os.path.join(self.repo, "README.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "base\n")
        # 未污染主工作树:切回原分支后 seo-fixes/ 从工作树消失
        back = repo_git(self.repo, "checkout", "-q", self.orig_branch)
        self.assertEqual(back.returncode, 0, back.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "seo-fixes")))

    def test_default_branch_name_generated_when_flag_has_no_value(self):
        r = self.run_cli("--only", "llms", "--apply", "--git-branch")   # 值缺省 → 自动命名
        self.assertEqual(r.returncode, 0, r.stderr)
        current = repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertTrue(current.startswith("feat/seo-fixes-"), current)  # feat/seo-fixes-<date>

    def test_not_a_git_repo_exits_2_and_writes_nothing(self):
        plain = tempfile.mkdtemp(prefix="fp-nogit-")
        self.addCleanup(shutil.rmtree, plain, ignore_errors=True)
        audit_path = os.path.join(plain, "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_payload(), f, ensure_ascii=False)
        r = subprocess.run([sys.executable, FIX_PLAN, "--audit", audit_path,
                            "--apply", "--git-branch"],
                           cwd=plain, capture_output=True, text=True, encoding="utf-8",
                           env=HERMETIC_ENV, timeout=120)
        self.assertEqual(r.returncode, 2)
        self.assertIn("git 仓库", r.stderr)                             # 报错说明原因
        self.assertEqual(os.listdir(plain), ["audit.json"])             # 一个文件都没写

    def test_git_branch_requires_apply_exits_2(self):
        r = self.run_cli("--git-branch", "feat/x")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--apply", r.stderr)                              # 分支模式只在 --apply 下可用

    def test_existing_branch_name_exits_2_without_side_effects(self):
        taken = repo_git(self.repo, "branch", "feat/taken")
        self.assertEqual(taken.returncode, 0, taken.stderr)
        r = self.run_cli("--only", "llms", "--apply", "--git-branch", "feat/taken")
        self.assertEqual(r.returncode, 2)
        self.assertIn("建分支失败", r.stderr)
        self.assertEqual(repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
                         self.orig_branch)                              # 仍在原分支
        self.assertFalse(os.path.exists(os.path.join(self.repo, "seo-fixes")))
        self.assertEqual(repo_git(self.repo, "rev-parse", self.orig_branch).stdout.strip(),
                         self.orig_sha)                                 # 原分支 ref 不动

    def test_commit_failure_rolls_back_to_original_branch(self):
        self.repo = make_git_repo(hook_fails=True)                      # pre-commit 钩子必败
        self.audit_path = os.path.join(self.repo, "audit.json")
        with open(self.audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_payload(), f, ensure_ascii=False)
        orig = repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        sha = repo_git(self.repo, "rev-parse", "HEAD").stdout.strip()
        r = self.run_cli("--only", "llms", "--apply", "--git-branch", "feat/will-fail")
        self.assertEqual(r.returncode, 2)
        self.assertIn("已回退到原分支", r.stderr)                        # 回退告知
        self.assertEqual(repo_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
                         orig)                                          # 回到原分支
        self.assertEqual(repo_git(self.repo, "branch", "--list", "feat/will-fail").stdout.strip(),
                         "")                                            # 半成品分支已删
        self.assertEqual(repo_git(self.repo, "rev-parse", orig).stdout.strip(), sha)
        self.assertEqual(repo_git(self.repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip(),
                         sha)                                           # 无新提交

    def test_pr_suggestion_printed_never_executed(self):
        r = self.run_cli("--only", "llms", "--apply", "--git-branch", "feat/pr-suggest")
        self.assertEqual(r.returncode, 0, r.stderr)
        # gh 命令行只打印:带人审边界说明 + 建议命令(draft PR,含 --title/--body/--head)
        self.assertIn("gh pr create --draft --title", r.stdout)
        self.assertIn("不自动执行", r.stdout)
        self.assertIn("--head feat/pr-suggest", r.stdout)
        self.assertIn("人审后手动执行", r.stdout)
        back = repo_git(self.repo, "checkout", "-q", self.orig_branch)  # 回原分支再跑第二轮
        self.assertEqual(back.returncode, 0, back.stderr)
        rj = self.run_cli("--only", "llms", "--apply",
                          "--git-branch", "feat/pr-json", "--json")
        self.assertEqual(rj.returncode, 0, rj.stderr)
        pr = json.loads(rj.stdout)["pr"]
        self.assertTrue(pr["command"].startswith("gh pr create --draft"))
        self.assertIn("seo-fixes(", pr["title"])                        # 标题含站点与件数


if __name__ == "__main__":
    unittest.main(verbosity=1)
