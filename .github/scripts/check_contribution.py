#!/usr/bin/env python3
"""Contribution check for this Skill library. Run it before you open a pull request; maintainers run it when reviewing.

    python3 .github/scripts/check_contribution.py          # checks 1-3 on the whole library, 4-7 on what you changed
    python3 .github/scripts/check_contribution.py --all    # checks 4-7 on every file too

"What you changed" = files that differ from origin/main (committed or not) plus new untracked files.
Standard library only. It never merges or pushes anything. Exit code 0 = all checks passed, 1 = something to fix.

What it checks:
  1. manifest.json parses; every entry's skill_path exists, and its example_path (if any) exists and parses.
  2. Every skills/<dir>/SKILL.md is listed in manifest.json with slug == <dir>, and every listed slug has a folder.
  3. SKILL.md front matter follows the Agent Skills format: `name` equals the folder name, uses only lowercase
     letters, digits and hyphens, at most 64 characters; `description` is present and at most 1024 characters.
  4. Relative links to files in Markdown under skills/ and examples/ point to files that exist.
  5. .json files under skills/ and examples/ parse.
  6. No API keys, tokens or private keys. A deliberate test fixture can carry `pragma: allowlist secret` on its line.
  7. Example data is synthetic: manifest example files are named *.synthetic.json (no real customer or personal data).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Only targets shaped like a relative file path are checked; prose such as [x](url) or (see 5.10) is skipped.
PATH_RE = re.compile(r"^[A-Za-z0-9_.~/-]+$")
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
}
TEXT_SUFFIXES = {".md", ".json", ".py", ".js", ".ts", ".yml", ".yaml", ".toml", ".txt", ".csv", ".sh", ".html", ".svg"}

problems: list[str] = []


def fail(path: Path | str, msg: str) -> None:
    rel = path.relative_to(ROOT) if isinstance(path, Path) and path.is_absolute() else path
    problems.append(f"{rel}: {msg}")


def front_matter(text: str) -> dict[str, str] | None:
    """Top-level `key: value` pairs of the leading --- block (enough for name/description; no YAML dependency)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    out: dict[str, str] = {}
    key = None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip().strip("\"'")
        elif key and line.startswith((" ", "\t")) and out.get(key) in ("", ">", "|", ">-", "|-"):
            out[key] = (out[key].lstrip(">|-") + " " + line.strip()).strip()
    return out


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    return [n for n in out.decode().split("\0") if n]


def files_to_scan(check_all: bool) -> list[Path]:
    try:
        if check_all:
            names = _git("ls-files", "-z")
        else:
            base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT,
                                  capture_output=True, check=True, text=True).stdout.strip()
            names = _git("diff", "-z", "--name-only", "--diff-filter=ACMR", base) + \
                _git("ls-files", "-z", "--others", "--exclude-standard")
    except (OSError, subprocess.CalledProcessError):
        print("(no origin/main to compare with: checking every file)")
        names = _git("ls-files", "-z") if (ROOT / ".git").exists() else \
            [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()]
    return [ROOT / n for n in dict.fromkeys(names) if (ROOT / n).is_file()]


def check_manifest() -> set[str]:
    path = ROOT / "manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(path, f"cannot read manifest.json ({exc})")
        return set()
    slugs: set[str] = set()
    for i, entry in enumerate(manifest.get("skills") or []):
        slug = entry.get("slug") or ""
        if not slug:
            fail(path, f"skills[{i}] has no slug")
            continue
        if slug in slugs:
            fail(path, f"slug {slug!r} is listed twice")
        slugs.add(slug)
        skill_path = ROOT / (entry.get("skill_path") or "")
        if entry.get("skill_path") != f"skills/{slug}/SKILL.md":
            fail(path, f"{slug}: skill_path should be skills/{slug}/SKILL.md")
        elif not skill_path.is_file():
            fail(path, f"{slug}: skill_path {entry['skill_path']} does not exist")
        example = entry.get("example_path")
        if example:
            ex = ROOT / example
            if not ex.is_file():
                fail(path, f"{slug}: example_path {example} does not exist")
            elif ex.suffix == ".json" and ".synthetic." not in ex.name:
                fail(path, f"{slug}: example files must be synthetic and named *.synthetic.json ({example})")
    return slugs


def check_skills(slugs: set[str]) -> None:
    skills_dir = ROOT / "skills"
    folders = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()
    for name in sorted(folders - slugs):
        fail(skills_dir / name, "folder is not listed in manifest.json (add an entry with this slug)")
    for name in sorted(slugs - folders):
        fail(ROOT / "manifest.json", f"slug {name!r} has no folder under skills/")
    for name in sorted(folders):
        skill = skills_dir / name / "SKILL.md"
        if not skill.is_file():
            fail(skills_dir / name, "missing SKILL.md")
            continue
        fm = front_matter(skill.read_text(encoding="utf-8"))
        if fm is None:
            fail(skill, "must start with a --- front matter block containing name and description")
            continue
        if fm.get("name") != name:
            fail(skill, f"front matter name {fm.get('name')!r} must equal the folder name {name!r}")
        if not NAME_RE.match(name) or len(name) > 64:
            fail(skill, "skill name: lowercase letters, digits and hyphens only, at most 64 characters")
        desc = fm.get("description", "")
        if not desc:
            fail(skill, "front matter needs a description (what it does and when to use it)")
        elif len(desc) > 1024:
            fail(skill, f"description is {len(desc)} characters; keep it at most 1024")


def check_links_and_json(files: list[Path]) -> None:
    for path in files:
        rel = path.relative_to(ROOT)
        if not rel.parts or rel.parts[0] not in ("skills", "examples"):
            continue
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                fail(path, f"invalid JSON ({exc})")
        elif path.suffix == ".md":
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in LINK_RE.findall(text):
                file_part = target.split("#", 1)[0].split("?", 1)[0]
                if not file_part or file_part.startswith("/") or not PATH_RE.match(file_part) \
                        or ("/" not in file_part and "." not in file_part):
                    continue
                if not (path.parent / file_part).exists():
                    fail(path, f"broken link -> {target}")


def check_secrets(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            for m in pattern.finditer(text):
                line_text = text[text.rfind("\n", 0, m.start()) + 1:text.find("\n", m.end()) % (len(text) + 1)]
                if "pragma: allowlist secret" in line_text:
                    continue
                line = text.count("\n", 0, m.start()) + 1
                fail(path, f"line {line}: looks like a secret ({label}); remove it (use a placeholder such as YOUR_API_KEY)")
                break


def main() -> int:
    files = files_to_scan("--all" in sys.argv[1:])
    check_skills(check_manifest())
    check_links_and_json(files)
    check_secrets(files)
    if problems:
        print(f"{len(problems)} problem(s) to fix:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("All contribution checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
