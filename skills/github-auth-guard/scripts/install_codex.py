#!/usr/bin/env python3
"""Install the GitHub auth guard into a user's Codex home, idempotently."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Optional, Sequence


GLOBAL_START = "<!-- github-auth-guard:start -->"
GLOBAL_END = "<!-- github-auth-guard:end -->"
SKILL_START = "<!-- github-auth-evidence:start -->"
SKILL_END = "<!-- github-auth-evidence:end -->"

GLOBAL_BLOCK = f"""{GLOBAL_START}
## GitHub authentication evidence

- A failing GitHub CLI check inside an agent sandbox is inconclusive; it does not
  prove that a credential is invalid or expired.
- Before claiming expiry or recommending reauthentication, run
  `/usr/bin/python3 ~/.codex/github-auth-guard/check.py --pretty`. In Codex, retry
  that check with scoped sandbox escalation so it can reach GitHub and the OS
  credential store.
- Recommend `gh auth login` only when the diagnostic returns
  `safe_to_recommend_login: true`. An invalid GitHub CLI environment-token override
  must be removed or replaced instead because it supersedes stored credentials.
- Never print, copy, or request the token while diagnosing authentication.
{GLOBAL_END}
"""

SKILL_BLOCK = f"""{SKILL_START}
## Authentication evidence gate (mandatory)

A sandboxed `gh auth status` failure is never sufficient evidence that login is
missing or expired. Before suggesting or running `gh auth login`, run:

```bash
/usr/bin/python3 ~/.codex/github-auth-guard/check.py --pretty
```

In Codex, repeat that diagnostic with scoped sandbox escalation. Login is permitted
only when it returns `safe_to_recommend_login: true`. If it reports an invalid
environment-token override, fix the override instead; login cannot supersede it.
Never display or capture a token.
{SKILL_END}
"""

IDENTITY_BLOCK = f"""{SKILL_START}
A target that appears missing inside Cursor or Codex is not proof that the human has
never authenticated: the agent process may be unable to read the OS keychain or reach
GitHub. Run `/usr/bin/python3 ~/.codex/github-auth-guard/check.py --pretty` with host
access first. Only a result with `safe_to_recommend_login: true` justifies asking the
human to authenticate; every inconclusive result stays with the agent for diagnosis.
{SKILL_END}
"""

IDENTITY_SECTION = f"""## One-Time Bootstrap

{IDENTITY_BLOCK.rstrip()}

`gh auth switch` can only select accounts already logged in for a host. If the
diagnostic authoritatively returns `safe_to_recommend_login: true`, the human may use
GitHub CLI's normal interactive setup once in a trusted terminal. The agent must not
initiate or prescribe that setup before the evidence gate.

Suggested checks:

```bash
/usr/bin/python3 ~/.codex/github-auth-guard/check.py --pretty
gh auth switch --hostname github.com --user QuentinMeow
```

"""

CURSOR_SECTION = """#### Cursor and Codex agent setup

Agent shells may run behind a network or credential-store sandbox even when the
integrated terminal and the saved GitHub credential are healthy. Therefore, a failed
`gh auth status` from an agent is an environment result, not a login diagnosis.

```bash
# Agent-safe check; contains no token material.
/usr/bin/python3 ~/.codex/github-auth-guard/check.py --pretty
```

Run that diagnostic with scoped host access when the first result is inconclusive.
Only when it returns `safe_to_recommend_login: true` should the human use the normal
interactive setup in a trusted terminal. If `GH_TOKEN` or `GITHUB_TOKEN` is rejected,
remove or replace that override instead of logging in again.

"""

RULES_CONTENT = """# Installed by AgentFold's github-auth-guard.
prefix_rule(
    pattern = [["gh", "/usr/local/bin/gh", "/opt/homebrew/bin/gh", "/usr/bin/gh"], "auth", "login"],
    decision = "forbidden",
    justification = "Run ~/.codex/github-auth-guard/check.py with host access first. Only the human may perform an evidence-backed interactive login in a normal terminal.",
    match = [
        "gh auth login",
        "gh auth login --hostname github.com",
        "gh auth login --web",
        "/usr/local/bin/gh auth login",
    ],
    not_match = [
        "gh auth status",
        "gh api user",
        "gh auth switch --hostname github.com --user example",
    ],
)
"""

PLUGIN_REPLACEMENTS = (
    (
        "- Require authenticated `gh` session. Run `gh auth status`. If not authenticated, ask the user to run `gh auth login` (and re-run `gh auth status`) before continuing.",
        "- Require authenticated `gh` session. Run `~/.codex/github-auth-guard/check.py` with host access; ask for login only when `safe_to_recommend_login` is true.",
    ),
    (
        "Prereq: authenticate with GitHub CLI once, then confirm with `gh auth status`. Repo and workflow scopes are typically required for Actions inspection.",
        "Prereq: classify authentication with `~/.codex/github-auth-guard/check.py` under host access. Repo and workflow scopes are typically required for Actions inspection.",
    ),
    (
        "   - If unauthenticated, ask the user to run `gh auth login` (ensuring repo + workflow scopes) before proceeding.",
        "   - Treat a sandbox failure as inconclusive; ask for login only when the host-access guard returns `safe_to_recommend_login: true`.",
    ),
)


def upsert_block(
    content: str,
    block: str,
    start: str,
    end: str,
    anchor: Optional[str] = None,
) -> str:
    if start in content and end in content:
        before, rest = content.split(start, 1)
        _, after = rest.split(end, 1)
        return before + block.rstrip() + after
    if anchor and anchor in content:
        index = content.index(anchor) + len(anchor)
        return content[:index] + "\n\n" + block.rstrip() + "\n" + content[index:].lstrip("\n")
    separator = "" if not content or content.endswith("\n\n") else "\n"
    return content + separator + block


def write_text(path: Path, content: str, dry_run: bool, notes: list[str]) -> None:
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous == content:
        notes.append(f"ok: {path}")
        return
    notes.append(f"{'would update' if dry_run else 'updated'}: {path}")
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_scripts(codex_home: Path, dry_run: bool, notes: list[str]) -> Path:
    source_dir = Path(__file__).resolve().parent
    target_dir = codex_home / "github-auth-guard"
    for name in ("check.py", "codex_hook.py"):
        source = source_dir / name
        target = target_dir / name
        content = source.read_text(encoding="utf-8")
        write_text(target, content, dry_run, notes)
        if not dry_run and target.exists():
            target.chmod(target.stat().st_mode | 0o111)
    return target_dir / "codex_hook.py"


def install_global_instructions(codex_home: Path, dry_run: bool, notes: list[str]) -> None:
    path = codex_home / "AGENTS.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "# Global Codex instructions\n"
    updated = upsert_block(content, GLOBAL_BLOCK, GLOBAL_START, GLOBAL_END)
    write_text(path, updated, dry_run, notes)


def install_rules(codex_home: Path, dry_run: bool, notes: list[str]) -> None:
    path = codex_home / "rules" / "github-auth-guard.rules"
    write_text(path, RULES_CONTENT, dry_run, notes)


def install_hooks(
    codex_home: Path,
    hook_script: Path,
    dry_run: bool,
    notes: list[str],
) -> None:
    path = codex_home / "hooks.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "description": "User-level Codex guardrails.",
            "hooks": {},
        }
    hooks = data.setdefault("hooks", {})
    interpreter = Path("/usr/bin/python3")
    if not interpreter.exists():
        interpreter = Path(sys.executable)
    command = f"{shlex.quote(str(interpreter))} {shlex.quote(str(hook_script))}"

    for event, matcher in (
        ("PreToolUse", "^Bash$"),
        ("PostToolUse", "^Bash$"),
        ("Stop", None),
    ):
        groups = hooks.setdefault(event, [])
        already_present = any(
            handler.get("command") == command
            for group in groups
            if isinstance(group, dict)
            for handler in group.get("hooks", [])
            if isinstance(handler, dict)
        )
        if already_present:
            continue
        group: dict[str, object] = {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": 30,
                    "statusMessage": "Guarding GitHub authentication evidence",
                }
            ]
        }
        if matcher is not None:
            group["matcher"] = matcher
        groups.append(group)

    content = json.dumps(data, indent=2, sort_keys=True) + "\n"
    write_text(path, content, dry_run, notes)


def patch_github_manager(codex_home: Path, dry_run: bool, notes: list[str]) -> None:
    root = codex_home / "skills" / "global-github-manager"
    skill = root / "SKILL.md"
    if not skill.exists():
        notes.append(f"skip (not installed): {root}")
        return

    content = skill.read_text(encoding="utf-8")
    content = upsert_block(
        content,
        SKILL_BLOCK,
        SKILL_START,
        SKILL_END,
        anchor="# GitHub Manager",
    )
    content = re.sub(
        r"\| `gh` \| Always — install and `gh auth login` \*\*inside Cursor's terminal\*\* if agents lack auth \|",
        "| `gh` | Always — diagnose with the auth-evidence guard; login only after confirmed rejection or absence |",
        content,
    )
    write_text(skill, content, dry_run, notes)

    identity = root / "references" / "gh-identity.md"
    if identity.exists():
        content = identity.read_text(encoding="utf-8")
        start = content.find("## One-Time Bootstrap")
        end = content.find("## Repo-Local Workflow", start)
        if start != -1 and end != -1:
            content = content[:start] + IDENTITY_SECTION + content[end:]
        write_text(identity, content, dry_run, notes)

    comprehensive = root / "references" / "pr-workflows-comprehensive.md"
    if comprehensive.exists():
        content = comprehensive.read_text(encoding="utf-8")
        start = content.find("#### Cursor IDE setup")
        end = content.find("#### SSH certificate auth", start)
        if start != -1 and end != -1:
            content = content[:start] + CURSOR_SECTION + content[end:]
        content = content.replace(
            "| `Permission denied (publickey)` on git push | Run `gh auth login` in Cursor terminal with SSH protocol; or `gh auth setup-git` |",
            "| `Permission denied (publickey)` on git push | Diagnose the SSH key, agent, or certificate; GitHub API login does not repair SSH authentication |",
        )
        standard_heading = "#### Standard setup (human in a regular terminal)"
        standard_note = (
            "\n\n> This block is only for a first-time human setup or a diagnostic result with "
            "`safe_to_recommend_login: true`; agents must not route sandbox failures here."
        )
        if standard_heading in content and standard_note.strip() not in content:
            content = content.replace(standard_heading, standard_heading + standard_note)
        write_text(comprehensive, content, dry_run, notes)

    identity_script = root / "scripts" / "gh_identity.py"
    if identity_script.exists():
        content = identity_script.read_text(encoding="utf-8")
        content = content.replace(
            "from typing import Callable, Optional",
            "from typing import Callable, List, Optional",
        )
        content = content.replace(
            "Runner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]",
            "Runner = Callable[[List[str], Path], subprocess.CompletedProcess]",
        )
        if "def _remove_file(path: Path)" not in content:
            helper = (
                "\n\ndef _remove_file(path: Path) -> None:\n"
                "    try:\n"
                "        path.unlink()\n"
                "    except FileNotFoundError:\n"
                "        pass\n"
            )
            content = content.replace("\ndef get_active_login(", helper + "\n\ndef get_active_login(")
        content = content.replace("path.unlink(missing_ok=True)", "_remove_file(path)")
        content = content.replace(
            '"Could not determine the active gh login. Run `gh auth login` first if needed.",',
            '"Could not determine the active gh login. Treat this as inconclusive in a sandbox; run the GitHub auth guard with host access before considering reauthentication.",',
        )
        content = content.replace(
            '"If that account is not logged in yet, run `gh auth login` in Cursor first.",',
            '"Use the GitHub auth guard with host access to distinguish a missing account from sandboxed credential access before considering reauthentication.",',
        )
        write_text(identity_script, content, dry_run, notes)


def patch_plugin_skills(codex_home: Path, dry_run: bool, notes: list[str]) -> None:
    changed = 0
    plugins = codex_home / "plugins"
    if not plugins.exists():
        notes.append(f"skip (no plugins): {plugins}")
        return
    for path in sorted(plugins.rglob("SKILL.md")):
        content = path.read_text(encoding="utf-8")
        updated = content
        for old, new in PLUGIN_REPLACEMENTS:
            updated = updated.replace(old, new)
        if updated != content:
            write_text(path, updated, dry_run, notes)
            changed += 1
    if changed == 0:
        notes.append("ok: installed plugin skills contain no known login-first prerequisite")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the Codex GitHub auth evidence guard.")
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser(),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-github-manager-patch", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    codex_home = args.codex_home.expanduser().resolve()
    notes: list[str] = []
    hook = install_scripts(codex_home, args.dry_run, notes)
    install_global_instructions(codex_home, args.dry_run, notes)
    install_rules(codex_home, args.dry_run, notes)
    install_hooks(codex_home, hook, args.dry_run, notes)
    if not args.skip_github_manager_patch:
        patch_github_manager(codex_home, args.dry_run, notes)
    patch_plugin_skills(codex_home, args.dry_run, notes)
    print("\n".join(notes))
    print("Next: restart Codex, open /hooks, and trust the GitHub auth guard once.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
