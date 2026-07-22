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
FENCE_RE = re.compile(r"```.*?```", re.S)

CORE_PREFIXES = (
    "skills/",
    "automation/",
    "templates/",
    "handbook/",
)
CORE_EXACT = {
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "docs/AGENTS.md",
    "docs/designs/AGENTS.md",
    "history/AGENTS.md",
    "memory/AGENTS.md",
    "message-queue/AGENTS.md",
    "services/AGENTS.md",
    "tasks/AGENTS.md",
}
PROTECTED_PATHS_FILE = "automation/core-scope-paths.txt"
EXECUTABLE_SUFFIXES = {".py", ".sh", ".bash", ".js", ".ts", ".rb", ".ps1"}
GLOBAL_STATE_MARKERS = (
    (re.compile(r"\bPath\.home\s*\("), "home-path API"),
    (re.compile(r"\.expanduser\s*\("), "home expansion"),
    (re.compile(r"\bos\.path\.expanduser\s*\("), "home expansion"),
    (re.compile(r"\b(?:os\.)?(?:getenv|environ\.(?:get))\s*\(\s*['\"](?:HOME|USERPROFILE|[A-Z][A-Z0-9_]*_HOME)['\"]"), "home environment"),
    (re.compile(r"\benviron\s*\[\s*['\"](?:HOME|USERPROFILE|[A-Z][A-Z0-9_]*_HOME)['\"]\s*\]"), "home environment"),
    (re.compile(r"(?<![A-Za-z0-9_])~/\."), "dot-directory beneath home"),
    (re.compile(r"\$(?:\{)?(?:HOME|USERPROFILE|[A-Z][A-Z0-9_]*_HOME)(?:\})?|%(?:HOME|USERPROFILE|[A-Z][A-Z0-9_]*_HOME)%"), "shell home environment"),
    (re.compile(r"\$(?:\{)?env:(?:HOME|USERPROFILE|[A-Z][A-Z0-9_]*_HOME)(?:\})?", re.I), "PowerShell home environment"),
    (re.compile(r"['\"]/(?:Users|home)/[^/'\"]+/"), "absolute user-home path"),
)


def git(*args, repo=REPO):
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def parsed_fields(text):
    pairs = FIELD_RE.findall(FENCE_RE.sub("", text or ""))
    counts = {}
    for key, _ in pairs:
        counts[key] = counts.get(key, 0) + 1
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    return dict(pairs), duplicates


def named_sections(text, title):
    clean = FENCE_RE.sub("", text or "")
    pattern = re.compile(
        rf"^## {re.escape(title)}(?:[ \t].*)?\n(.*?)(?=^##[ \t]|\Z)", re.M | re.S
    )
    return pattern.findall(clean)


def is_placeholder(value):
    value = (value or "").strip()
    return not value or "<" in value or value in {"______", "none yet"}


def display(path):
    try:
        return path.relative_to(REPO)
    except ValueError:
        return path


def protected_paths(text):
    return {
        line.strip() for line in (text or "").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def is_core_path(path, extra_exact=()):
    path = Path(path).as_posix()
    while path.startswith("./"):
        path = path[2:]
    return path in CORE_EXACT or path in set(extra_exact) or path.startswith(CORE_PREFIXES)


def is_core_executable(path, content="", mode=""):
    rel = Path(path)
    parts = rel.parts
    if not parts or parts[0] not in {"automation", "skills"} or "tests" in parts:
        return False
    return (
        mode == "100755"
        or content.startswith("#!")
        or rel.suffix in EXECUTABLE_SUFFIXES
        or "scripts" in parts
        or parts[:2] == ("automation", "hooks")
        or (parts[0] == "automation" and not rel.suffix)
    )


def task_id_from_branch(branch):
    branch = branch or ""
    if branch.startswith("refs/heads/"):
        branch = branch[len("refs/heads/"):]
    return branch[len("task/"):] if branch.startswith("task/") else None


def find_task(branch, repo=REPO, load_text=None):
    task_id = task_id_from_branch(branch)
    if not task_id:
        return None
    if load_text:
        matches = []
        for status in ("0_backlog", "1_in-progress", "2_blocked", "3_in-review", "4_done"):
            task = repo / "tasks" / status / task_id
            try:
                load_text((Path("tasks") / status / task_id / "task.md").as_posix())
                matches.append(task)
            except RuntimeError:
                pass
    else:
        matches = sorted((repo / "tasks").glob(f"*/{task_id}"))
    return matches[0] if len(matches) == 1 else None


def disposition_with_reason(value, allowed):
    value = (value or "").strip()
    match = re.match(r"(.+?)\s+(?:—|-)\s+(.+)$", value)
    return bool(match and match.group(1).strip().lower() in allowed
                and len(match.group(2).strip()) >= 12 and not is_placeholder(value))


def evidence_text(path, load_text=None):
    try:
        if load_text:
            return load_text(Path(display(path)).as_posix())
        return path.read_text(encoding="utf-8")
    except (OSError, RuntimeError):
        return None


def valid_adapter(value):
    value = (value or "").strip()
    if value.lower() == "none":
        return True
    pieces = [piece.strip() for piece in value.split(";")]
    if len(pieces) != 4 or any(piece.count("=") != 1 for piece in pieces):
        return False
    pairs = dict(piece.split("=", 1) for piece in pieces)
    if set(pairs) != {"canonical", "optional", "policy", "writes"}:
        return False
    canonical = pairs["canonical"].strip()
    canonical_path = Path(canonical)
    return bool(
        canonical
        and re.fullmatch(r"[A-Za-z0-9._/-]+", canonical)
        and not canonical_path.is_absolute()
        and ".." not in canonical_path.parts
        and pairs["optional"].strip().lower() == "yes"
        and pairs["policy"].strip().lower() == "none"
        and pairs["writes"].strip().lower() == "repo-only"
    )


def same_reviewer_as_claimant(reviewer, claimant):
    claimant_words = re.findall(r"[a-z0-9]+", (claimant or "").lower())
    reviewer_words = set(re.findall(r"[a-z0-9]+", (reviewer or "").lower()))
    return bool(claimant_words and claimant_words[0] in reviewer_words)


def validate_task(task, touched_core, require_review=False, load_text=None):
    errors = []
    task_file = task / "task.md"
    task_text = evidence_text(task_file, load_text)
    task_fields, task_duplicates = parsed_fields(task_text)
    if task_duplicates:
        errors.append(f"{display(task_file)} has duplicate field(s): {', '.join(task_duplicates)}")
    scope = task_fields.get("Repository scope", "")
    if touched_core and scope != "core":
        errors.append(
            f"{display(task_file)} must declare `**Repository scope:** core` "
            "before changing AgentFold core"
        )

    design = task / "design.md"
    design_text = evidence_text(design, load_text)
    design_sections = named_sections(design_text, "Core fit")
    design_fields, design_duplicates = parsed_fields(
        design_sections[0] if len(design_sections) == 1 else ""
    )
    if touched_core or (task.parent.name in {"3_in-review", "4_done"} and scope == "core"):
        if design_text is None:
            errors.append(f"{display(task)} needs design.md with a completed Core fit section")
        else:
            if len(design_sections) != 1:
                errors.append("design.md needs exactly one real `## Core fit` section")
            core_keys = {
                "Agent substitution", "Provider substitution", "Repository substitution",
                "User-global writes", "Why AgentFold core", "Thin adapter",
            }
            duplicate_core = sorted(core_keys.intersection(design_duplicates))
            if duplicate_core:
                errors.append(f"Core fit has duplicate field(s): {', '.join(duplicate_core)}")
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
            if not valid_adapter(design_fields.get("Thin adapter")):
                errors.append(
                    "`**Thin adapter:**` must be `none` or exact nonempty canonical=, "
                    "optional=yes, policy=none, writes=repo-only pairs"
                )

    review_needed = require_review or (
        task.parent.name in {"3_in-review", "4_done"} and scope == "core"
    )
    if review_needed:
        verification = task / "verification.md"
        verification_text = evidence_text(verification, load_text) or ""
        review_sections = named_sections(verification_text, "Review verdicts")
        if len(review_sections) != 1:
            errors.append("verification.md needs exactly one real `## Review verdicts` section")
        verdicts = REVIEW_RE.findall(review_sections[0] if len(review_sections) == 1 else "")
        claimant = task_fields.get("Claimed-by", "")
        latest = {}
        for reviewer, verdict, _ in verdicts:
            if not same_reviewer_as_claimant(reviewer, claimant):
                latest[reviewer.strip().lower()] = verdict.lower()
        approvals = sum(verdict == "approve" for verdict in latest.values())
        blocks = sum(verdict == "block" for verdict in latest.values())
        if not latest:
            errors.append(
                "verification.md needs `- core-fit / <independent reviewer>: approve — <finding>`"
            )
        elif approvals <= blocks:
            errors.append(
                f"core-fit review lacks an approve majority ({approvals} approve, {blocks} block)"
            )
    return errors


def global_state_findings(paths, load_content, load_mode=lambda _: ""):
    findings = []
    for path in paths:
        parts = Path(path).parts
        if not parts or parts[0] not in {"automation", "skills"} or "tests" in parts:
            continue
        try:
            content = load_content(path)
            mode = load_mode(path)
        except (OSError, RuntimeError):
            continue  # deleted or unavailable in the selected tree
        instruction_file = parts[0] == "skills" and Path(path).suffix.lower() == ".md"
        if not instruction_file and not is_core_executable(path, content, mode):
            continue
        for pattern, label in GLOBAL_STATE_MARKERS:
            if pattern.search(content):
                findings.append(
                    f"{path} references {label}; tracked core files may use repo-local state only"
                )
    return findings


def staged_paths(repo=REPO):
    return [line for line in git(
        "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=ACMRD", repo=repo
    ).splitlines() if line]


def range_paths(spec, repo=REPO):
    return [line for line in git(
        "diff", "--no-renames", "--name-only", "--diff-filter=ACMRD", spec, repo=repo
    ).splitlines() if line]


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
        load_mode = lambda path: (git("ls-tree", head, "--", path).split() or [""])[0]
    else:
        paths = staged_paths()
        load_content = lambda path: git("show", f":{path}")
        load_mode = lambda path: (git("ls-files", "-s", "--", path).split() or [""])[0]

    try:
        registered_paths = protected_paths(load_content(PROTECTED_PATHS_FILE))
    except RuntimeError:
        registered_paths = set()
    core_paths = [path for path in paths if is_core_path(path, registered_paths)]
    task = find_task(branch, load_text=load_content)
    errors = []
    if core_paths and task is None:
        errors.append(
            "core changes require a `task/<task-id>` branch and matching task folder; "
            "personal/provider setup belongs outside AgentFold"
        )
    elif task is not None:
        errors.extend(validate_task(
            task, bool(core_paths), args.require_review and bool(core_paths), load_content
        ))
    errors.extend(global_state_findings(core_paths, load_content, load_mode))

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
