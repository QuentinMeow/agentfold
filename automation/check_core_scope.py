#!/usr/bin/env python3
"""Gate AgentFold core changes on explicit core-fit evidence.

Local hooks inspect staged bytes. Pull-request CI supplies a base...head range.
The deterministic checks force architectural deliberation without pretending syntax
proves the rationale. ``--require-review`` validates a revision-bound receipt after a
human explicitly invokes that token-expensive independent review.
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from markdown_semantics import (
    claimed_by_identity_source,
    core_fit_review_evidence,
    independent_review_verdicts,
    semantic_text,
)

REPO = Path(__file__).resolve().parents[1]
FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z -]*):\*\*\s*(.*)$", re.M)
CORE_PREFIXES = (
    "skills/",
    "automation/",
    "templates/",
    "handbook/",
)
CORE_EXACT = {
    "AGENTS.md",
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
ORDINARY_ROOT_MARKDOWN = {
    "CHANGELOG.md", "CODE_OF_CONDUCT.md", "LICENSE.md", "README.md", "SECURITY.md",
    "SUPPORT.md",
}
ROOT_INSTRUCTION_TOKENS = {
    "agent", "agents", "assistant", "assistants", "instruction", "instructions",
    "prompt", "prompts",
}
HIDDEN_INSTRUCTION_TOKENS = {"instruction", "instructions", "prompt", "prompts", "rule", "rules"}
ADAPTER_IGNORE_START = "# agentfold-adapters:start"
ADAPTER_IGNORE_END = "# agentfold-adapters:end"
ADAPTER_IGNORE_LINES = (
    ".claude/",
    ".cursor/",
    ".agents/",
    "**/CLAUDE.md",
    "!/CLAUDE.md",
)
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


# Every Git read in this gate goes through this prefix, so a `refs/replace/*` entry
# cannot substitute a forged commit, tree, or blob for the real one the gate was asked
# about. Without it a blob passes the "is this a commit" test and a stale core-fit
# review passes as fresh. The source-level guard in
# `automation/tests/test_reconcile_queue.py` holds that line.
RAW_GIT = ("git", "--no-replace-objects")


def git(*args, repo=REPO):
    result = subprocess.run(
        [*RAW_GIT, *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def parsed_fields(text):
    pairs = FIELD_RE.findall(semantic_text(text))
    counts = {}
    for key, _ in pairs:
        counts[key] = counts.get(key, 0) + 1
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    return dict(pairs), duplicates


def named_sections(text, title):
    clean = semantic_text(text)
    pattern = re.compile(
        rf"^## {re.escape(title)}(?:[ \t][^\r\n]*)?\r?\n"
        rf"(.*?)(?=^##(?:[ \t]|\r?$)|\Z)",
        re.M | re.S,
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
    rel = Path(path)
    component_tokens = [
        re.findall(r"[a-z0-9]+", Path(part).stem.lower()) for part in rel.parts
    ]
    root_tokens = component_tokens[0] if component_tokens else []
    root_instruction_doc = (
        len(rel.parts) == 1 and rel.suffix.lower() == ".md"
        and rel.name not in ORDINARY_ROOT_MARKDOWN
        and bool(root_tokens) and root_tokens[0] in ROOT_INSTRUCTION_TOKENS
    )
    hidden_directory_instruction = any(
        HIDDEN_INSTRUCTION_TOKENS.intersection(tokens)
        for tokens in component_tokens[1:-1]
    )
    hidden_filename_instruction = bool(
        component_tokens and HIDDEN_INSTRUCTION_TOKENS.intersection(component_tokens[-1])
    )
    hidden_instruction_file = (
        len(rel.parts) > 1 and rel.parts[0].startswith(".")
        and rel.suffix.lower() == ".md"
        and (hidden_directory_instruction or hidden_filename_instruction)
    )
    return bool(
        path in CORE_EXACT or path in set(extra_exact) or path.startswith(CORE_PREFIXES)
        or root_instruction_doc or hidden_instruction_file
    )


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


def validate_task(
    task, touched_core, require_review=False, load_text=None,
    review_revision_check=None,
):
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

    if require_review and scope != "core":
        errors.append("--require-review applies only to a task with `Repository scope: core`")
    elif require_review:
        verification = task / "verification.md"
        verification_text = evidence_text(verification, load_text) or ""
        review_evidence = core_fit_review_evidence(verification_text)
        if review_evidence["section_count"] != 1:
            errors.append("verification.md needs exactly one real `## Review verdicts` section")
        if review_evidence["revision_count"] != 1:
            errors.append(
                "Review verdicts needs exactly one real "
                "`**Reviewed revision:** <commit>` field"
            )
        else:
            reviewed_revision = review_evidence["reviewed_revision"]
            if review_revision_check:
                errors.extend(review_revision_check(reviewed_revision))
        claimant = claimed_by_identity_source(task_text)
        latest = {}
        for matched, reviewer_key in independent_review_verdicts(
            review_evidence, claimant
        ):
            verdict = matched.group("verdict")
            latest[reviewer_key] = verdict.lower()
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
        if not is_core_executable(path, content, mode):
            continue
        for pattern, label in GLOBAL_STATE_MARKERS:
            if pattern.search(content):
                findings.append(
                    f"{path} references {label}; tracked core files may use repo-local state only"
                )
    return findings


def generated_adapter_findings(paths, load_content):
    findings = []
    for path in paths:
        generated = path.startswith((".claude/", ".cursor/", ".agents/"))
        generated = generated or (Path(path).name == "CLAUDE.md" and path != "CLAUDE.md")
        if not generated:
            continue
        try:
            load_content(path)
        except RuntimeError:
            continue  # deleting an accidentally tracked adapter is the repair
        findings.append(
            f"{path} is generated agent-adapter state; keep canonical content in AGENTS.md or skills/"
        )
    return findings


def adapter_ignore_findings(paths, load_content):
    if ".gitignore" not in paths:
        return []
    try:
        lines = load_content(".gitignore").splitlines()
    except RuntimeError:
        return [".gitignore cannot be deleted; it protects generated agent-adapter state"]
    if lines.count(ADAPTER_IGNORE_START) != 1 or lines.count(ADAPTER_IGNORE_END) != 1:
        return [".gitignore must keep the single AgentFold adapter block and its markers"]
    start = lines.index(ADAPTER_IGNORE_START)
    end = lines.index(ADAPTER_IGNORE_END)
    if start >= end or tuple(lines[start + 1:end]) != ADAPTER_IGNORE_LINES:
        return [".gitignore AgentFold adapter block changed; edit product ignores outside its markers"]

    protected_examples = (
        ".claude", ".claude/", ".claude/skills/example",
        ".cursor", ".cursor/", ".cursor/skills/example",
        ".agents", ".agents/", ".agents/skills/example", "service/CLAUDE.md",
    )
    for line in lines[:start] + lines[end + 1:]:
        rule = line.strip()
        if not rule.startswith("!") or rule == "!/CLAUDE.md":
            continue
        pattern = rule[1:].lstrip("/")
        if any(fnmatch.fnmatch(example, pattern) for example in protected_examples):
            return [f".gitignore rule {rule!r} re-includes generated agent-adapter state"]
    return []


def staged_paths(repo=REPO):
    return [line for line in git(
        "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=ACMRD", repo=repo
    ).splitlines() if line]


def range_paths(spec, repo=REPO):
    return [line for line in git(
        "diff", "--no-renames", "--name-only", "--diff-filter=ACMRD", spec, repo=repo
    ).splitlines() if line]


def is_review_bound_task_path(path, task_id):
    parts = Path(path).parts
    return bool(
        len(parts) == 4
        and parts[0] == "tasks"
        and parts[2] == task_id
        and parts[3] in {"task.md", "design.md", "plan.md"}
    )


def task_input_blob_map(lines, task_id):
    blobs = {}
    for line in lines:
        metadata, separator, path = line.partition("\t")
        fields = metadata.split()
        if not separator or len(fields) < 2 or not is_review_bound_task_path(path, task_id):
            continue
        oid = fields[2] if len(fields) >= 3 and fields[1] == "blob" else fields[1]
        blobs.setdefault(Path(path).name, []).append(oid)
    return {name: tuple(sorted(oids)) for name, oids in blobs.items()}


def committed_task_input_blobs(revision, task_id, repo=REPO):
    lines = git("ls-tree", "-r", revision, "--", "tasks", repo=repo).splitlines()
    return task_input_blob_map(lines, task_id)


def staged_task_input_blobs(task_id, repo=REPO):
    lines = git("ls-files", "-s", "--", "tasks", repo=repo).splitlines()
    return task_input_blob_map(lines, task_id)


def review_revision_findings(
    reviewed_revision, current_revision, registered_paths=(),
    pending_paths=(), task_id="", selected_task_blobs=None, repo=REPO,
):
    resolved = subprocess.run(
        [*RAW_GIT, "rev-parse", "--verify", f"{reviewed_revision}^{{commit}}"],
        cwd=repo, text=True, capture_output=True, check=False,
    )
    if resolved.returncode:
        return [f"reviewed revision {reviewed_revision!r} is not a commit in this repository"]
    reviewed_commit = resolved.stdout.strip()
    if reviewed_revision.lower() != reviewed_commit.lower():
        return [
            f"reviewed revision {reviewed_revision!r} must be the repository's full "
            "commit ID, not an abbreviation"
        ]
    current = git("rev-parse", "--verify", f"{current_revision}^{{commit}}", repo=repo).strip()
    ancestry = subprocess.run(
        [*RAW_GIT, "merge-base", "--is-ancestor", reviewed_commit, current],
        cwd=repo, text=True, capture_output=True, check=False,
    )
    if ancestry.returncode:
        return [
            f"reviewed revision {reviewed_revision} is not an ancestor of {current[:12]}"
        ]
    later_paths = range_paths(f"{reviewed_commit}...{current}", repo=repo)
    later_bound = [
        path for path in later_paths
        if is_core_path(path, registered_paths)
    ]
    later_bound.extend(
        path for path in pending_paths
        if is_core_path(path, registered_paths)
        and path not in later_bound
    )
    reviewed_task_blobs = committed_task_input_blobs(reviewed_commit, task_id, repo=repo)
    if selected_task_blobs is None:
        selected_task_blobs = committed_task_input_blobs(current, task_id, repo=repo)
    changed_inputs = sorted(
        name for name in set(reviewed_task_blobs).union(selected_task_blobs)
        if reviewed_task_blobs.get(name) != selected_task_blobs.get(name)
    )
    later_bound.extend(
        f"task input {name}" for name in changed_inputs
    )
    if later_bound:
        preview = ", ".join(later_bound[:3])
        suffix = " ..." if len(later_bound) > 3 else ""
        return [
            f"core-fit review for {reviewed_commit[:12]} is stale; later bound changes: "
            f"{preview}{suffix}"
        ]
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="inspect the staged Git diff (default)")
    mode.add_argument("--range", dest="diff_range", help="inspect a Git base...head range")
    parser.add_argument("--branch", help="task branch name; defaults to the current branch")
    parser.add_argument(
        "--require-review", action="store_true",
        help="validate a revision-bound receipt from an explicitly invoked review",
    )
    args = parser.parse_args(argv)

    branch = args.branch or git("branch", "--show-current").strip()
    if args.diff_range:
        paths = range_paths(args.diff_range)
        head = args.diff_range.rsplit("...", 1)[-1]
        current_revision = git("rev-parse", "--verify", f"{head}^{{commit}}").strip()
        load_content = lambda path: git("show", f"{head}:{path}")
        load_mode = lambda path: (git("ls-tree", head, "--", path).split() or [""])[0]
    else:
        paths = staged_paths()
        current_revision = git("rev-parse", "--verify", "HEAD^{commit}").strip()
        load_content = lambda path: git("show", f":{path}")
        load_mode = lambda path: (git("ls-files", "-s", "--", path).split() or [""])[0]

    try:
        registered_paths = protected_paths(load_content(PROTECTED_PATHS_FILE))
    except RuntimeError:
        registered_paths = set()
    core_paths = [path for path in paths if is_core_path(path, registered_paths)]
    task = find_task(branch, load_text=load_content)
    errors = []
    errors.extend(adapter_ignore_findings(paths, load_content))
    errors.extend(generated_adapter_findings(paths, load_content))
    if (core_paths or args.require_review) and task is None:
        errors.append(
            "core changes require a `task/<task-id>` branch and matching task folder; "
            "personal/provider setup belongs outside AgentFold"
        )
    elif task is not None:
        pending_paths = paths if not args.diff_range else ()
        selected_task_blobs = (
            None if args.diff_range else staged_task_input_blobs(task.name)
        )
        review_revision_check = lambda revision: review_revision_findings(
            revision,
            current_revision,
            registered_paths,
            pending_paths,
            task.name,
            selected_task_blobs,
        )
        errors.extend(validate_task(
            task,
            bool(core_paths),
            args.require_review,
            load_content,
            review_revision_check,
        ))
    errors.extend(global_state_findings(core_paths, load_content, load_mode))

    if errors:
        for error in errors:
            print(f"[core-scope] {error}")
        print(
            "    fix: complete templates/task/design.md, route external setup outside "
            "core, or record review when --require-review is selected"
        )
        return 1
    if core_paths:
        review_state = (
            "independent review verified" if args.require_review
            else "independent review manual; not invoked"
        )
        print(
            f"core-scope: pass ({len(core_paths)} core path(s), task {task.name}; "
            f"{review_state})"
        )
    elif args.require_review:
        print(
            f"core-scope: pass (no later core changes, task {task.name}; "
            "independent review verified)"
        )
    else:
        print("core-scope: no core changes (independent review manual; not invoked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
