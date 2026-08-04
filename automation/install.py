#!/usr/bin/env python3
"""Idempotent setup for one checkout. Safe to re-run any time.

1. Converges the common repository's core.hooksPath on automation/hooks.
2. Creates this worktree's git-ignored agent-adapter symlinks:
   - CLAUDE.md -> AGENTS.md beside every non-root AGENTS.md (lazy folder loading)
   - .claude/skills/, .cursor/skills/, .agents/skills/ -> ../../skills/<name>
Symlink rationale: memory/decisions/2026-07-22-visible-skills-dir-with-symlinks.md
"""
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADAPTER_DIRS = [".claude", ".cursor", ".agents"]
HOOKS_PATH = "automation/hooks"
CONFIG_ATTEMPTS = 100
CONFIG_RETRY_SECONDS = 0.02


class InstallError(Exception):
    """A setup failure the caller can repair and retry."""


def git_config_value(scope, key, value_type=None):
    """Read one Git config scope without taking its write lock."""
    type_option = [] if value_type is None else ["--type={0}".format(value_type)]
    result = subprocess.run(
        ["git", "config"] + type_option + list(scope) + ["--get", key],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode == 0:
        return result.stdout.rstrip("\r\n")
    if result.returncode == 1:
        return None
    detail = result.stderr.strip() or "git config returned {0}".format(
        result.returncode
    )
    raise InstallError("could not read {0}: {1}".format(key, detail))


def git_config_hooks_path(scope=()):
    """Read core.hooksPath from one scope, or its effective value by default."""
    return git_config_value(scope, "core.hooksPath")


def configure_common_hooks():
    """Converge shared Git config; concurrent installers become reads or retries."""
    last_error = ""
    for attempt in range(CONFIG_ATTEMPTS):
        if git_config_hooks_path(("--local",)) == HOOKS_PATH:
            return attempt != 0

        result = subprocess.run(
            ["git", "config", "--local", "core.hooksPath", HOOKS_PATH],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if (result.returncode == 0 and
                git_config_hooks_path(("--local",)) == HOOKS_PATH):
            return True

        last_error = result.stderr.strip() or "git config returned {0}".format(
            result.returncode
        )
        if attempt + 1 < CONFIG_ATTEMPTS:
            time.sleep(CONFIG_RETRY_SECONDS)

    raise InstallError(
        "could not set shared core.hooksPath to {0} after {1} attempts; "
        "finish or stop the Git process holding config.lock, then rerun "
        "({2})".format(HOOKS_PATH, CONFIG_ATTEMPTS, last_error)
    )


def configure_worktree_hooks():
    """Converge an enabled worktree override that masks the common value."""
    if git_config_hooks_path() == HOOKS_PATH:
        return False
    if git_config_value(
            ("--local",), "extensions.worktreeConfig", value_type="bool") != "true":
        raise InstallError(
            "effective core.hooksPath is not {0} after common setup; remove the "
            "higher-precedence override, then rerun".format(HOOKS_PATH)
        )

    last_error = ""
    for attempt in range(CONFIG_ATTEMPTS):
        if git_config_hooks_path() == HOOKS_PATH:
            return attempt != 0
        result = subprocess.run(
            ["git", "config", "--worktree", "core.hooksPath", HOOKS_PATH],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode == 0 and git_config_hooks_path() == HOOKS_PATH:
            return True
        last_error = result.stderr.strip() or "git config returned {0}".format(
            result.returncode
        )
        if attempt + 1 < CONFIG_ATTEMPTS:
            time.sleep(CONFIG_RETRY_SECONDS)

    raise InstallError(
        "could not set this worktree's effective core.hooksPath to {0} after "
        "{1} attempts; finish or stop the Git process holding "
        "config.worktree.lock, then rerun ({2})".format(
            HOOKS_PATH, CONFIG_ATTEMPTS, last_error
        )
    )


def symlink_target(link):
    """Return a symlink's target, or None when the path is absent or not a link."""
    try:
        if link.is_symlink():
            return os.readlink(str(link))
    except OSError:
        # Another installer may be replacing the same generated link.
        return None
    return None


def ensure_symlink(link: Path, target: str, target_is_directory=False):
    """Create/verify a relative symlink; never touch another existing path."""
    current = symlink_target(link)
    if current is not None:
        if current == target:
            return "ok"
        # Never unlink after observing a stale target: another actor could replace
        # the symlink with a real file between observation and unlink. Preservation
        # makes both the ordinary mismatch and that race fail safe.
        return "symlink points to an unexpected target and was preserved"
    elif link.exists():
        return "real path exists and was preserved"
    try:
        link.parent.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        return "could not create adapter directory ({0})".format(err)
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as err:
        # Two same-worktree installers may both observe an absent path. The one that
        # loses creation still succeeds when the winner installed the same target.
        if symlink_target(link) == target:
            return "ok"
        if link.exists() and not link.is_symlink():
            return "real path appeared concurrently and was preserved"
        return (
            "could not create symlink ({0}); see "
            "memory/known-issues/install-symlinks-windows.md"
        ).format(err)
    return "ok"


def display_path(path):
    """Show adapter failures relative to the checkout when possible."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def main():
    problems = []

    if (REPO / ".git").exists():
        try:
            common_changed = configure_common_hooks()
            worktree_changed = configure_worktree_hooks()
        except InstallError as err:
            print("ERROR: {0}".format(err), file=sys.stderr)
            return 1
        for hook in (REPO / "automation" / "hooks").iterdir():
            mode = hook.stat().st_mode
            if mode & 0o111 != 0o111:
                hook.chmod(mode | 0o111)
        state = "configured" if common_changed else "already configured; no write"
        print(
            "git hooks (common repository): core.hooksPath -> {0} ({1})".format(
                HOOKS_PATH, state
            )
        )
        worktree_state = (
            "configured override" if worktree_changed else "already effective; no write"
        )
        print(
            "git hooks (this worktree): effective core.hooksPath -> {0} "
            "({1})".format(HOOKS_PATH, worktree_state)
        )
    else:
        problems.append((REPO / ".git", "not a Git checkout; run `git init` first"))

    count = 0
    for agents_md in REPO.rglob("AGENTS.md"):
        rel = agents_md.relative_to(REPO)
        if rel.parts[0].startswith(".") or rel.parts[0] == "templates" or agents_md.parent == REPO:
            continue
        note = ensure_symlink(
            agents_md.parent / "CLAUDE.md",
            "AGENTS.md",
            target_is_directory=False,
        )
        count += note == "ok"
        if note != "ok":
            problems.append((agents_md.parent / "CLAUDE.md", note))
    print("CLAUDE.md shims (this worktree): {0} in place".format(count))

    for adapter in ADAPTER_DIRS:
        for skill in sorted((REPO / "skills").iterdir()):
            if skill.is_dir():
                note = ensure_symlink(
                    REPO / adapter / "skills" / skill.name,
                    f"../../skills/{skill.name}",
                    target_is_directory=True,
                )
                if note != "ok":
                    problems.append((REPO / adapter / "skills" / skill.name, note))
    print(
        "skill adapters (this worktree): {0} -> skills/".format(
            ", ".join(ADAPTER_DIRS)
        )
    )

    if problems:
        print(
            "ERROR: worktree adapter setup is incomplete; move or remove the "
            "preserved path(s), fix the stated condition, then rerun:",
            file=sys.stderr,
        )
        for path, reason in problems:
            print("  - {0}: {1}".format(display_path(path), reason), file=sys.stderr)
        return 1

    print(
        "install: done (run once in every linked worktree; safe to rerun when "
        "skills or AGENTS.md files change)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
