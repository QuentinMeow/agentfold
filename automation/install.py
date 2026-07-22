#!/usr/bin/env python3
"""Idempotent setup for a fresh clone. Safe to re-run any time.

1. Points git at the tracked hooks (core.hooksPath automation/hooks).
2. Creates git-ignored agent-adapter symlinks:
   - CLAUDE.md -> AGENTS.md beside every non-root AGENTS.md (lazy folder loading)
   - .claude/skills/, .cursor/skills/, .agents/skills/ -> ../../skills/<name>
Symlink rationale: memory/decisions/2026-07-22-visible-skills-dir-with-symlinks.md
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADAPTER_DIRS = [".claude", ".cursor", ".agents"]


def ensure_symlink(link: Path, target: str):
    """Create/refresh a relative symlink; never touch a real (non-link) file."""
    if link.is_symlink():
        if os.readlink(link) == target:
            return "ok"
        link.unlink()
    elif link.exists():
        return f"SKIP (real file exists): {link}"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except OSError as err:  # e.g. Windows without developer mode
        return f"SKIP ({err}): {link} — see memory/known-issues/install-symlinks-windows.md"
    return "ok"


def main():
    notes = []

    if (REPO / ".git").exists():
        subprocess.run(["git", "config", "core.hooksPath", "automation/hooks"],
                       cwd=REPO, check=True)
        for hook in (REPO / "automation" / "hooks").iterdir():
            hook.chmod(hook.stat().st_mode | 0o111)
        print("git hooks: core.hooksPath -> automation/hooks")
    else:
        notes.append("no .git here — run `git init` then re-run to install hooks")

    count = 0
    for agents_md in REPO.rglob("AGENTS.md"):
        rel = agents_md.relative_to(REPO)
        if rel.parts[0].startswith(".") or rel.parts[0] == "templates" or agents_md.parent == REPO:
            continue
        note = ensure_symlink(agents_md.parent / "CLAUDE.md", "AGENTS.md")
        count += note == "ok"
        if note != "ok":
            notes.append(note)
    print(f"CLAUDE.md shims: {count} in place")

    for adapter in ADAPTER_DIRS:
        for skill in sorted((REPO / "skills").iterdir()):
            if skill.is_dir():
                note = ensure_symlink(REPO / adapter / "skills" / skill.name,
                                      f"../../skills/{skill.name}")
                if note != "ok":
                    notes.append(note)
    print(f"skill adapters: {', '.join(ADAPTER_DIRS)} -> skills/")

    for note in notes:
        print(note)
    print("install: done (idempotent — re-run whenever skills or AGENTS.md files change)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
