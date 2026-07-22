#!/usr/bin/env python3
"""Gate AgentFold core changes on explicit, independently reviewed core fit.

Local hooks inspect staged bytes. Pull-request CI supplies a base...head range.
The check is intentionally narrow: syntax forces architectural deliberation; an
independent reviewer, not a keyword list, judges whether the rationale is true.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z -]*):\*\*\s*(.*)$", re.M)
REVIEW_RE = re.compile(
    r"^- core-fit / ([^:]+):\s*(approve|block)\s+[—-]\s+(.+)$", re.I | re.M
)

CORE_PREFIXES = (
    "skills/",
    "automation/",
    "templates/",
    "handbook/principles/",
    ".github/workflows/",
)
EXECUTABLE_SUFFIXES = {".py", ".sh", ".bash", ".js", ".ts", ".rb", ".ps1"}
GLOBAL_STATE_MARKERS = (
    (re.compile(r"\bPath\.home\s*\("), "home-path API"),
    (re.compile(r"\.expanduser\s*\("), "home expansion"),
    (re.compile(r"\bos\.path\.expanduser\s*\("), "home expansion"),
    (re.compile(r"\b(?:os\.)?(?:getenv|environ\.(?:get))\s*\(\s*['\"](?:HOME|USERPROFILE|[A-Z]+_HOME)['\"]"), "home environment"),
    (re.compile(r"\benviron\s*\[\s*['\"](?:HOME|USERPROFILE|[A-Z]+_HOME)['\"]\s*\]"), "home environment"),
    (re.compile(r"['\"]~/\."), "dot-directory beneath home"),
    (re.compile(r"\$(?:HOME|USERPROFILE)\b|%(?:HOME|USERPROFILE)%"), "shell home environment"),
    (re.compile(r"['\"]/(?:Users|home)/[^/'\"]+/"), "absolute user-home path"),
)


def git(*args, repo=REPO):
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def fields(path):
    return dict(FIELD_RE.findall(path.read_text(encoding="utf-8")))


def is_placeholder(value):
    value = (value or "").strip()
    return not value or "<" in value or value in {"______", "none yet"}


def display(path):
    try:
        return path.relative_to(REPO)
    except ValueError:
        return path


def is_core_path(path):
    path = Path(path).as_posix()
    while path.startswith("./"):
        path = path[2:]
    return path == "AGENTS.md" or path.startswith(CORE_PREFIXES)


def is_core_executable(path):
    rel = Path(path)
    parts = rel.parts
    if not parts or parts[0] not in {"automation", "skills"} or "tests" in parts:
        return False
    return rel.suffix in EXECUTABLE_SUFFIXES or parts[:2] == ("automation", "hooks")


def task_id_from_branch(branch):
    branch = branch or ""
    if branch.startswith("refs/heads/"):
        branch = branch[len("refs/heads/"):]
    return branch[len("task/"):] if branch.startswith("task/") else None


def find_task(branch, repo=REPO):
    task_id = task_id_from_branch(branch)
    if not task_id:
        return None
    matches = sorted((repo / "tasks").glob(f"*/{task_id}"))
    return matches[0] if len(matches) == 1 else None


def disposition_with_reason(value, allowed):
    value = (value or "").strip()
    match = re.match(r"(.+?)\s+(?:—|-)\s+(.+)$", value)
    return bool(match and match.group(1).strip().lower() in allowed
                and len(match.group(2).strip()) >= 12 and not is_placeholder(value))


def validate_task(task, touched_core, require_review=False):
    errors = []
    task_file = task / "task.md"
    task_fields = fields(task_file) if task_file.is_file() else {}
    scope = task_fields.get("Repository scope", "")
    if touched_core and scope != "core":
        errors.append(
            f"{display(task_file)} must declare `**Repository scope:** core` "
            "before changing AgentFold core"
        )

    design = task / "design.md"
    design_fields = fields(design) if design.is_file() else {}
    if touched_core or (task.parent.name in {"3_in-review", "4_done"} and scope == "core"):
        if not design.is_file():
            errors.append(f"{display(task)} needs design.md with a completed Core fit section")
        else:
            if not disposition_with_reason(design_fields.get("Agent substitution"), {"pass"}):
                errors.append("Core fit needs `**Agent substitution:** pass — <reason>`")
            if not disposition_with_reason(
                design_fields.get("Provider substitution"), {"pass", "not applicable", "not-applicable"}
            ):
                errors.append("Core fit needs `**Provider substitution:** pass|not-applicable — <reason>`")
            if not disposition_with_reason(design_fields.get("Repository substitution"), {"pass"}):
                errors.append("Core fit needs `**Repository substitution:** pass — <reason>`")
            if design_fields.get("User-global writes", "").strip().lower() != "none":
                errors.append("Core fit requires `**User-global writes:** none`")
            why = design_fields.get("Why AgentFold core", "")
            if is_placeholder(why) or len(why.strip()) < 24:
                errors.append("Core fit needs a concrete `**Why AgentFold core:**` rationale")
            adapter = design_fields.get("Thin adapter", "").strip().lower()
            adapter_tokens = ("canonical=", "optional=yes", "policy=none", "writes=repo-only")
            if adapter != "none" and not all(token in adapter for token in adapter_tokens):
                errors.append(
                    "`**Thin adapter:**` must be `none` or declare canonical=, "
                    "optional=yes, policy=none, and writes=repo-only"
                )

    review_needed = require_review or (
        task.parent.name in {"3_in-review", "4_done"} and scope == "core"
    )
    if review_needed:
        verification = task / "verification.md"
        text = verification.read_text(encoding="utf-8") if verification.is_file() else ""
        verdicts = REVIEW_RE.findall(text)
        claimant = task_fields.get("Claimed-by", "").strip().lower().split(" ", 1)[0]
        if any(verdict.lower() == "block" for _, verdict, _ in verdicts):
            errors.append("core-fit review still contains a blocking verdict")
        independent = [
            reviewer for reviewer, verdict, _ in verdicts
            if verdict.lower() == "approve" and reviewer.strip().lower() != claimant
        ]
        if not independent:
            errors.append(
                "verification.md needs `- core-fit / <independent reviewer>: approve — <finding>`"
            )
    return errors


def global_state_findings(paths, load_content):
    findings = []
    for path in paths:
        if not is_core_executable(path):
            continue
        try:
            content = load_content(path)
        except (OSError, RuntimeError):
            continue  # deleted or unavailable in the selected tree
        for pattern, label in GLOBAL_STATE_MARKERS:
            if pattern.search(content):
                findings.append(
                    f"{path} references {label}; tracked core executables may use repo-local state only"
                )
    return findings


def staged_paths(repo=REPO):
    return [line for line in git("diff", "--cached", "--name-only", "--diff-filter=ACMR", repo=repo).splitlines() if line]


def range_paths(spec, repo=REPO):
    return [line for line in git("diff", "--name-only", "--diff-filter=ACMR", spec, repo=repo).splitlines() if line]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="inspect the staged Git diff (default)")
    mode.add_argument("--range", dest="diff_range", help="inspect a Git base...head range")
    parser.add_argument("--branch", help="task branch name; defaults to the current branch")
    parser.add_argument("--require-review", action="store_true", help="require an independent approval")
    args = parser.parse_args(argv)

    branch = args.branch or git("branch", "--show-current").strip()
    if args.diff_range:
        paths = range_paths(args.diff_range)
        head = args.diff_range.rsplit("...", 1)[-1]
        load_content = lambda path: git("show", f"{head}:{path}")
    else:
        paths = staged_paths()
        load_content = lambda path: git("show", f":{path}")

    core_paths = [path for path in paths if is_core_path(path)]
    task = find_task(branch)
    errors = []
    if core_paths and task is None:
        errors.append(
            "core changes require a `task/<task-id>` branch and matching task folder; "
            "personal/provider setup belongs outside AgentFold"
        )
    elif task is not None:
        errors.extend(validate_task(task, bool(core_paths), args.require_review and bool(core_paths)))
    errors.extend(global_state_findings(core_paths, load_content))

    if errors:
        for error in errors:
            print(f"[core-scope] {error}")
        print("    fix: complete templates/task/design.md, route external setup outside core, or obtain independent review")
        return 1
    if core_paths:
        print(f"core-scope: pass ({len(core_paths)} core path(s), task {task.name})")
    else:
        print("core-scope: no core changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
