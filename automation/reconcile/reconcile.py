#!/usr/bin/env python3
"""The reconciler: checks every mechanical harness invariant.

Modes:
  --check         report findings, exit 1 if any (default)
  --file-retries  also write one repair item per check+subject into
                  message-queue/needs-agent/retries/ (idempotent, keyed by
                  full identity) and delete reconciler-filed items whose
                  findings cleared
  --fix-index     regenerate memory/index.md from the memory files

Design notes: invariants only (end states, never procedures); stdlib only;
every check no-ops if its folder is absent so adopters can pick pieces.
Registry: CHECKS at the bottom. Adding a check = one function + one entry.
"""
import argparse
import contextlib
import datetime
import hashlib
import re
import subprocess
import sys
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from check_action_projection import (
    LIST_ITEM_RE,
    action_like_rendered_prose,
    parse_task_queue_action_value,
    prose_without_links,
    section_entries,
    task_action_unit_counts,
    task_queue_action_paths_from_text,
    visible_outside_action_sections,
)
from markdown_semantics import (
    MARKDOWN_LINK_RE,
    contains_raw_html,
    markdown_link_destinations,
    markdown_links,
    normalized_action_tokens,
    rendered_human_text,
    semantic_text,
)

REPO = Path(__file__).resolve().parents[2]
TODAY = datetime.datetime.now(datetime.timezone.utc).date()

QUEUE = REPO / "message-queue"
RETRIES = QUEUE / "needs-agent" / "retries"
TASKS = REPO / "tasks"
TASK_STATUSES = ["0_backlog", "1_in-progress", "2_blocked", "3_in-review", "4_done"]
TASK_LIFECYCLE_TRANSITIONS = {"start", "review", "complete"}
TASK_ARTIFACT_NAMES = {
    "task.md", "design.md", "plan.md", "worklog.md", "verification.md",
}
TASK_MARKDOWN_SUFFIXES = {".md", ".markdown"}
TASK_ALLOWED_STATUS_TRANSITIONS = {
    "0_backlog": {"1_in-progress"},
    "1_in-progress": {"2_blocked", "3_in-review"},
    "2_blocked": {"1_in-progress"},
    "3_in-review": {"1_in-progress", "4_done"},
    "4_done": set(),
}
TASK_DELETABLE_STATUSES = {"0_backlog", "4_done"}
CONVERSATIONS = REPO / "history" / "conversations"
MEMORY = REPO / "memory"
MEMORY_ZONES = ["facts", "decisions", "lessons", "known-issues"]
ACTIVE_TRANSITIONS = set()
ACTIVE_TASK_ID = None
CHANGE_RANGE = None
DISPLACED_TIP = None
_GIT_SNAPSHOT_CACHE_ACTIVE = False
_GIT_INDEX_CACHE = None
_GIT_INDEX_OID_CACHE = None
_GIT_INDEX_ALL_PATHS_CACHE = None
_GIT_HEAD_PATHS_CACHE = None
_GIT_HEAD_OID = None
_GIT_ARTIFACT_CACHE = {}
_GIT_BLOB_CACHE = {}
_GIT_CAT_FILE_PROCESS = None

# Required bold-key fields per queue folder (relative to message-queue/). Delivery
# timing is encoded by the filename and validated separately below.
QUEUE_SCHEMAS = {
    "needs-human/decisions": ["Status", "Filed", "Action", "Full context"],
    "needs-human/clarifications": ["Status", "Filed", "Action", "Full context"],
    "needs-human/reviews": [
        "Status", "Filed", "Action", "Full context", "Review target",
        "Review revision", "Reviewed revision",
    ],
    "needs-agent/requests": ["Status", "Filed", "Action", "Full context"],
    "needs-agent/retries": ["Status", "Filed", "Check", "Subject", "Action"],
}

# Line budgets for contract files (progressive-disclosure enforcement).
ROOT_AGENTS_BUDGET = 140
LEAF_AGENTS_BUDGET = 60
SKILL_BUDGET = 70
# The root README is the human landing page — pitch + map, depth linked in handbook/
# (memory/decisions/2026-07-22-root-readme-line-budget.md).
ROOT_README_BUDGET = 140

STALE_QUEUE_DAYS = 30
STALE_TASK_DAYS = 14

TASK_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
REPOSITORY_SCOPE_RE = re.compile(r"^(core|records-only|service:[a-z0-9][a-z0-9-]*)$")
CONVERSATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}[A-Z]{2,5}-[a-z0-9][a-z0-9-]*$")
FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z -]*):\*\*[ \t]*(.*)$", re.M)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
LEADING_DATE_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})(?:,|\s|$)")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TASK_BOUNDARY_RE = re.compile(
    r"^task:(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)$"
)
TRANSITION_BOUNDARY_RE = re.compile(r"^transition:([a-z0-9][a-z0-9-]*)$")
EVENT_BOUNDARY_RE = re.compile(r"^event:([a-z0-9][a-z0-9-]*)$")
OPERATION_BOUNDARY_RE = re.compile(r"^operation:([a-z0-9][a-z0-9-]*)$")
REVIEW_REVISION_RE = re.compile(
    r"^(?:sha256:[0-9a-f]{64}|git:(?:[0-9a-f]{40}|[0-9a-f]{64})"
    r"(?:\.\.\.(?:[0-9a-f]{40}|[0-9a-f]{64}))?)$"
)
REVIEW_OUTCOMES = {
    "approved",
    "changes-requested",
    "rejected",
    "abandoned",
    "not-approved",  # legacy alias for changes-requested
}
REVIEW_SUCCESSOR_OUTCOMES = {"changes-requested", "not-approved"}
REVIEW_TERMINAL_OUTCOMES = {"approved", "rejected", "abandoned"}
GIT_RANGE_RE = re.compile(
    r"^(?:root:(?:[0-9a-f]{40}|[0-9a-f]{64})|"
    r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
    r"\.\.\.(?:[0-9a-f]{40}|[0-9a-f]{64}))$"
)
FULL_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
QUEUE_ITEM_RE = re.compile(
    r"^(blocking|future-blocking|non-blocking)-[a-z0-9][a-z0-9-]*\.md$"
)
QUEUE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"message-queue/(?:needs-human|needs-agent)/[a-z0-9][a-z0-9-]*/"
    r"(?:blocking|future-blocking|non-blocking)-[a-z0-9][a-z0-9-]*\.md"
    r"(?![A-Za-z0-9_.-])"
)
QUEUE_TIMING_FIELDS = {
    "blocking": ("Blocks now",),
    "future-blocking": ("Blocks at", "Until then"),
    "non-blocking": ("If unanswered",),
}
QUEUE_TIMING_ORDER = {
    "non-blocking": 0,
    "future-blocking": 1,
    "blocking": 2,
}
HUMAN_PROJECTION_FIELDS = (
    "Why-you-might-care",
    "If-you-do-nothing",
)
QUEUE_ROOT_DOCUMENT_PATHS = {
    "message-queue/AGENTS.md",
    "message-queue/README.md",
    "message-queue/CLAUDE.md",
}
PLACEHOLDER_RE = re.compile(
    r"^(?:_+|<[^>]*>|tbd|todo|none|n/?a|unknown)$", re.I
)
OPTION_RE = re.compile(r"^### Option(?:\s|$)", re.M)
EXAMPLE_CONSEQUENCE_RE = re.compile(
    r"^\*Example consequence:\*\s*(.+)$", re.M
)
CONTEXT_BACKTICK_RE = re.compile(r"`([^`\s]+)`")
HANDOVER_HUMAN_LINK_RE = re.compile(
    r"message-queue/needs-human/[a-z0-9][a-z0-9-]*/"
    r"(blocking|future-blocking|non-blocking)-[a-z0-9][a-z0-9-]*\.md"
    r"(?![A-Za-z0-9_.-])"
)
HANDOVER_AGENT_LINK_RE = re.compile(
    r"message-queue/needs-agent/[a-z0-9][a-z0-9-]*/"
    r"(blocking|future-blocking|non-blocking)-[a-z0-9][a-z0-9-]*\.md"
    r"(?![A-Za-z0-9_.-])"
)
RETRY_GENERATOR = "reconcile.py/v1"
RETRY_PROJECTION_START = "<!-- reconcile:projection:start -->"
RETRY_PROJECTION_END = "<!-- reconcile:projection:end -->"

# Link check: backticked or markdown-linked repo paths with >= 2 segments.
BACKTICK_RE = re.compile(r"`([^`\s]+/[^`\s]+)`")
LINK_SKIP_PREFIXES = ("http", "tmp/", "private/", ".")
LINK_SKIP_DIRS = {"templates", "history", "tmp"}  # + memory/decisions (records)


class Finding:
    def __init__(self, check, subject, message, fix):
        self.check, self.subject, self.message, self.fix = check, subject, message, fix

    def __str__(self):
        return f"[{self.check}] {self.subject}: {self.message}"


class GitSnapshotError(RuntimeError):
    """The exact Git candidate could not be read safely."""


def fields(path):
    return text_fields(repo_text(path))


def text_fields(text):
    return dict(FIELD_RE.findall(semantic_text(text)))


def field_counts(text):
    counts = {}
    for key, _ in FIELD_RE.findall(semantic_text(text)):
        counts[key] = counts.get(key, 0) + 1
    return counts


def parse_date(value):
    m = DATE_RE.search(value or "")
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group())
    except ValueError:
        return None


def parse_leading_date(value):
    matched = LEADING_DATE_RE.match(value or "")
    if not matched:
        return None
    try:
        return datetime.date.fromisoformat(matched.group(1))
    except ValueError:
        return None


def days_old(path):
    mtime = max((p.stat().st_mtime for p in path.rglob("*") if p.is_file()),
                default=path.stat().st_mtime)
    return (TODAY - datetime.date.fromtimestamp(mtime)).days


def has_concrete_value(value):
    value = (value or "").strip()
    return bool(value) and not PLACEHOLDER_RE.fullmatch(value)


def delivery_class(name):
    matched = QUEUE_ITEM_RE.fullmatch(name)
    return matched.group(1) if matched else None


def start_git_snapshot_cache():
    """Reuse one immutable index/HEAD view during a reconciler invocation."""
    global _GIT_SNAPSHOT_CACHE_ACTIVE
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE, _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    global _GIT_ARTIFACT_CACHE, _GIT_BLOB_CACHE
    close_git_cat_file()
    _GIT_SNAPSHOT_CACHE_ACTIVE = True
    _GIT_INDEX_CACHE = None
    _GIT_INDEX_OID_CACHE = None
    _GIT_INDEX_ALL_PATHS_CACHE = None
    _GIT_HEAD_PATHS_CACHE = None
    _GIT_HEAD_OID = None
    _GIT_ARTIFACT_CACHE = {}
    _GIT_BLOB_CACHE = {}
    load_git_index_snapshot()
    load_git_head_snapshot()


def stop_git_snapshot_cache():
    """Drop invocation-local Git data so callers can safely mutate the index."""
    global _GIT_SNAPSHOT_CACHE_ACTIVE
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE, _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    global _GIT_ARTIFACT_CACHE, _GIT_BLOB_CACHE
    close_git_cat_file()
    _GIT_SNAPSHOT_CACHE_ACTIVE = False
    _GIT_INDEX_CACHE = None
    _GIT_INDEX_OID_CACHE = None
    _GIT_INDEX_ALL_PATHS_CACHE = None
    _GIT_HEAD_PATHS_CACHE = None
    _GIT_HEAD_OID = None
    _GIT_ARTIFACT_CACHE = {}
    _GIT_BLOB_CACHE = {}


def close_git_cat_file():
    global _GIT_CAT_FILE_PROCESS
    process = _GIT_CAT_FILE_PROCESS
    _GIT_CAT_FILE_PROCESS = None
    if process is None:
        return
    try:
        process.stdin.close()
        process.wait(timeout=5)
    except (BrokenPipeError, OSError, ValueError, subprocess.TimeoutExpired):
        process.kill()
        process.wait()
    finally:
        for stream in (process.stdin, process.stdout):
            try:
                stream.close()
            except (AttributeError, OSError, ValueError):
                pass


def parse_git_index_records(data):
    """Return stage-0 modes/OIDs plus every path represented in index data."""
    modes = {}
    oids = {}
    all_paths = set()
    unmerged = set()
    for record in data.split(b"\0"):
        metadata, separator, encoded_name = record.partition(b"\t")
        if not separator:
            continue
        parts = metadata.decode("ascii", errors="replace").split()
        if len(parts) != 3:
            continue
        mode, oid, stage = parts
        name = encoded_name.decode("utf-8", errors="surrogateescape")
        all_paths.add(name)
        if stage != "0":
            unmerged.add(name)
            modes.pop(name, None)
            oids.pop(name, None)
            continue
        if name not in unmerged:
            modes[name] = mode
            oids[name] = oid
    return modes, oids, all_paths


def parse_git_tree_records(data):
    """Return path-to-mode entries from NUL-delimited ls-tree output."""
    entries = {}
    for record in data.split(b"\0"):
        metadata, separator, encoded_name = record.partition(b"\t")
        if not separator:
            continue
        parts = metadata.decode("ascii", errors="replace").split()
        if len(parts) != 3:
            continue
        mode, kind, _oid = parts
        if kind != "blob":
            continue
        name = encoded_name.decode("utf-8", errors="surrogateescape")
        entries[name] = mode
    return entries


def git_failure(result, fallback):
    detail = result.stderr.decode(
        "utf-8", errors="replace"
    ).strip() if result.stderr else ""
    return detail or fallback


def load_git_index_snapshot():
    """Capture stage-0 modes and object IDs in one NUL-safe Git query."""
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE
    if _GIT_INDEX_CACHE is not None:
        return
    _GIT_INDEX_CACHE = {}
    _GIT_INDEX_OID_CACHE = {}
    _GIT_INDEX_ALL_PATHS_CACHE = set()
    if not (REPO / ".git").exists():
        return
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, "could not capture the Git index"
        ))
    (
        _GIT_INDEX_CACHE,
        _GIT_INDEX_OID_CACHE,
        _GIT_INDEX_ALL_PATHS_CACHE,
    ) = parse_git_index_records(result.stdout)


def load_git_head_snapshot():
    """Capture the HEAD path set once for candidate-vs-committed comparisons."""
    global _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    if _GIT_HEAD_PATHS_CACHE is not None:
        return
    _GIT_HEAD_PATHS_CACHE = set()
    _GIT_HEAD_OID = None
    if not (REPO / ".git").exists():
        return
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if head.returncode == 1:
        return  # An unborn repository has no committed paths.
    if head.returncode:
        raise GitSnapshotError(
            head.stderr.strip() or "could not resolve Git HEAD"
        )
    _GIT_HEAD_OID = head.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", _GIT_HEAD_OID):
        raise GitSnapshotError("Git HEAD did not resolve to a full object ID")
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "-z", _GIT_HEAD_OID],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, "could not capture the Git HEAD tree"
        ))
    _GIT_HEAD_PATHS_CACHE = {
        name.decode("utf-8", errors="surrogateescape")
        for name in result.stdout.split(b"\0")
        if name
    }


def paths_under_prefix(paths, prefix):
    prefix = prefix.rstrip("/")
    if prefix in ("", "."):
        return paths
    return {
        name: value
        for name, value in paths.items()
        if name == prefix or name.startswith(prefix + "/")
    }


def git_index_entries(prefix):
    if not (REPO / ".git").exists():
        return {}
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        return paths_under_prefix(_GIT_INDEX_CACHE, prefix)
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", prefix],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, f"could not inspect Git index path `{prefix}`"
        ))
    entries, _, _ = parse_git_index_records(result.stdout)
    return entries


def git_index_has_path(path):
    """Return whether any index stage or mode represents this exact path."""
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        return path in _GIT_INDEX_ALL_PATHS_CACHE
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", path],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, f"could not inspect Git index path `{path}`"
        ))
    _, _, all_paths = parse_git_index_records(result.stdout)
    return path in all_paths


def git_head_paths(prefix):
    if not (REPO / ".git").exists():
        return set()
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        return set(paths_under_prefix(
            {name: None for name in _GIT_HEAD_PATHS_CACHE},
            prefix,
        ))
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", prefix],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return set(result.stdout.splitlines()) if result.returncode == 0 else set()


def validate_range_candidate(change_range):
    """Bind --range checks to the captured head or its exact synthetic merge."""
    if not change_range:
        return
    if not (REPO / ".git").exists() or not _GIT_HEAD_OID:
        raise GitSnapshotError("--range requires a committed Git candidate")
    if change_range.startswith("root:"):
        base = None
        range_head = change_range[len("root:"):]
    else:
        base, range_head = change_range.split("...", 1)
    for label, revision in (("base", base), ("head", range_head)):
        if revision is None:
            continue
        commit = subprocess.run(
            [
                "git", "--no-replace-objects", "cat-file", "-e",
                f"{revision}^{{commit}}",
            ],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if commit.returncode:
            detail = commit.stderr.decode(
                "utf-8", errors="replace"
            ).strip() if commit.stderr else ""
            raise GitSnapshotError(
                detail or f"--range {label} is not an available commit"
            )
    if base is not None:
        common = subprocess.run(
            ["git", "--no-replace-objects", "merge-base", base, range_head],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if common.returncode or not common.stdout.strip():
            raise GitSnapshotError(git_failure(
                common, "--range base and head have no merge base"
            ))
    if _GIT_HEAD_OID != range_head:
        ancestry = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", _GIT_HEAD_OID],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if ancestry.returncode:
            raise GitSnapshotError(
                ancestry.stderr.strip()
                or "could not inspect the candidate commit parents"
            )
        parents = ancestry.stdout.split()[1:]
        if base is None or len(parents) != 2 \
                or set(parents) != {base, range_head}:
            raise GitSnapshotError(
                "captured candidate is neither the --range head nor an exact "
                "base+head synthetic merge"
            )
    staged = subprocess.run(
        ["git", "diff-index", "--cached", "--quiet", _GIT_HEAD_OID, "--"],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if staged.returncode == 1:
        raise GitSnapshotError(
            "--range candidate has staged changes beyond its captured commit"
        )
    if staged.returncode:
        detail = staged.stderr.decode(
            "utf-8", errors="replace"
        ).strip() if staged.stderr else ""
        raise GitSnapshotError(detail or "could not compare the candidate index")
    unstaged = subprocess.run(
        ["git", "diff-files", "--quiet", "--ignore-submodules=all", "--"],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if unstaged.returncode == 1:
        raise GitSnapshotError(
            "--range candidate has unstaged changes beyond its captured commit"
        )
    if unstaged.returncode:
        detail = unstaged.stderr.decode(
            "utf-8", errors="replace"
        ).strip() if unstaged.stderr else ""
        raise GitSnapshotError(detail or "could not compare the candidate worktree")
    untracked = subprocess.run(
        [
            "git", "ls-files", "--others",
            "--exclude-per-directory=.gitignore", "-z",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if untracked.returncode:
        raise GitSnapshotError(git_failure(
            untracked, "could not inspect untracked candidate paths"
        ))
    if untracked.stdout:
        raise GitSnapshotError(
            "--range candidate contains untracked files outside the commit"
        )


def validate_displaced_tip(displaced_tip, change_range):
    """Validate an explicit old ref tip without changing candidate selection."""
    if not displaced_tip:
        return
    if not change_range or change_range.startswith("root:"):
        raise GitSnapshotError(
            "--displaced-tip requires a full BASE...HEAD --range"
        )
    range_head = change_range.split("...", 1)[1]
    available = subprocess.run(
        [
            "git", "--no-replace-objects", "cat-file", "-e",
            f"{displaced_tip}^{{commit}}",
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if available.returncode:
        raise GitSnapshotError(git_failure(
            available, "--displaced-tip is not an available commit"
        ))
    common = subprocess.run(
        [
            "git", "--no-replace-objects", "merge-base",
            displaced_tip, range_head,
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if common.returncode:
        raise GitSnapshotError(git_failure(
            common, "--displaced-tip and --range head have no merge base"
        ))


def live_queue_items():
    indexed = git_index_entries("message-queue")
    committed = git_head_paths("message-queue")
    seen = set()
    for name in sorted(indexed):
        item = REPO / name
        if queue_document_path(name):
            continue
        seen.add(name)
        yield item
    if CHANGE_RANGE is not None:
        return
    if QUEUE.is_dir():
        for item in sorted(QUEUE.rglob("*")):
            if not (item.is_file() or item.is_symlink()):
                continue
            name = item.relative_to(REPO).as_posix()
            if queue_document_path(name):
                continue
            if name not in seen and name not in committed:
                yield item


def live_markdown_files():
    """Return Markdown files from the commit candidate plus untracked work."""
    indexed = git_index_entries(".")
    committed = git_head_paths(".")
    seen = set()
    for name, mode in sorted(indexed.items()):
        path = Path(name)
        if mode not in ("100644", "100755") or path.suffix != ".md":
            continue
        seen.add(name)
        yield REPO / path
    if CHANGE_RANGE is not None:
        return
    for path in sorted(REPO.rglob("*.md")):
        rel = path.relative_to(REPO)
        if rel.parts[0].startswith(".") or not path.is_file() or path.is_symlink():
            continue
        name = rel.as_posix()
        if name not in seen and name not in committed:
            yield path


def readable_queue_item(item):
    """Queue state must be stored in a repository-local regular file."""
    mode = git_index_entries(item.relative_to(REPO).as_posix()).get(
        item.relative_to(REPO).as_posix()
    )
    if mode is not None:
        return mode in ("100644", "100755")
    return item.is_file() and not item.is_symlink()


def section_body(text, heading):
    text = semantic_text(text)
    matched = re.search(
        r"^" + re.escape(heading)
        + r"\s*\n(.*?)(?=^#{1,3}(?:\s|$)"
        + r"|^\*\*(?:Your answer|Your review):\*\*|\Z)",
        text,
        flags=re.M | re.S,
    )
    return matched.group(1).strip() if matched else None


def level_two_section_body(text, heading):
    text = semantic_text(text)
    matched = re.search(
        r"^" + re.escape(heading) + r"\s*\n(.*?)(?=^##(?:\s|$)|\Z)",
        text,
        flags=re.M | re.S,
    )
    return matched.group(1).strip() if matched else None


def raw_level_two_section_body(text, heading):
    """Return raw section source for fail-closed syntax validation only."""
    matched = re.search(
        r"^" + re.escape(heading) + r"\s*\n(.*?)(?=^##(?:\s|$)|\Z)",
        text,
        flags=re.M | re.S,
    )
    return matched.group(1).strip() if matched else None


def context_files(value):
    candidates = context_path_candidates(value)
    found = []
    for candidate in candidates:
        target = REPO / Path(candidate)
        if repo_artifact_bytes(target) is not None:
            found.append(target)
    return found


def review_target(value):
    """Parse one exact local, Git, or HTTPS review target."""
    value = (value or "").strip()
    if REVIEW_REVISION_RE.fullmatch(value) and value.startswith("git:"):
        return "git", value
    local = re.fullmatch(r"`([^`\s]+)`", value)
    if local:
        candidates = context_path_candidates(value)
        return ("local", candidates[0]) if len(candidates) == 1 else None
    if re.fullmatch(r"https://[^\s,]+", value) \
            and value.count("https://") == 1:
        return "https", value
    angle_link = re.fullmatch(
        r"\[[^\]\n]+\]\(<([^<>\n]+)>\)", value
    )
    plain_link = re.fullmatch(
        r"\[[^\]\n]+\]\(([^()\s,]+)\)", value
    )
    linked = angle_link or plain_link
    if linked:
        destination = linked.group(1)
        if destination.startswith("https://") \
                and destination.count("https://") == 1:
            return "https", destination
        candidates = context_path_candidates(value)
        if len(candidates) == 1:
            return "local", candidates[0]
    return None


def repo_artifact_bytes(path):
    """Return committed-candidate bytes, using the Git index when available."""
    try:
        relative = path.relative_to(REPO).as_posix()
    except ValueError:
        return None
    if (REPO / ".git").exists():
        if _GIT_SNAPSHOT_CACHE_ACTIVE and relative in _GIT_ARTIFACT_CACHE:
            return _GIT_ARTIFACT_CACHE[relative]
        mode = git_index_entries(relative).get(relative)
        if mode not in ("100644", "100755"):
            if _GIT_SNAPSHOT_CACHE_ACTIVE:
                _GIT_ARTIFACT_CACHE[relative] = None
            return None
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            value = git_blob_bytes(_GIT_INDEX_OID_CACHE.get(relative))
        else:
            artifact = subprocess.run(
                ["git", "show", f":{relative}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if artifact.returncode:
                raise GitSnapshotError(
                    f"could not read staged Git object for `{relative}`"
                )
            value = artifact.stdout
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _GIT_ARTIFACT_CACHE[relative] = value
        return value
    try:
        if path.is_file() and not path.is_symlink():
            return path.read_bytes()
    except (OSError, ValueError):
        pass
    return None


def git_blob_bytes(oid):
    """Read a captured index object through one reusable cat-file process."""
    global _GIT_CAT_FILE_PROCESS
    if not oid:
        return None
    if oid in _GIT_BLOB_CACHE:
        return _GIT_BLOB_CACHE[oid]
    if _GIT_CAT_FILE_PROCESS is None:
        try:
            _GIT_CAT_FILE_PROCESS = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=REPO,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            raise GitSnapshotError(
                f"could not start Git blob reader: {error}"
            )
    process = _GIT_CAT_FILE_PROCESS
    try:
        process.stdin.write(oid.encode("ascii") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().rstrip(b"\n").split()
        if len(header) != 3:
            raise GitSnapshotError(f"Git could not read captured object {oid}")
        else:
            size = int(header[2])
            payload = process.stdout.read(size)
            delimiter = process.stdout.read(1)
            if header[1] != b"blob":
                raise GitSnapshotError(
                    f"captured object {oid} is not a Git blob"
                )
            value = payload
            if delimiter != b"\n":
                raise GitSnapshotError(
                    f"Git returned a malformed blob frame for {oid}"
                )
    except GitSnapshotError:
        close_git_cat_file()
        raise
    except (BrokenPipeError, OSError, ValueError) as error:
        close_git_cat_file()
        raise GitSnapshotError(
            f"could not read captured Git object {oid}: {error}"
        )
    _GIT_BLOB_CACHE[oid] = value
    return value


def repo_text(path):
    artifact = repo_artifact_bytes(path)
    if artifact is not None:
        return artifact.decode("utf-8")
    if (REPO / ".git").exists():
        relative = path.relative_to(REPO).as_posix()
        if git_index_has_path(relative) \
                or relative in git_head_paths(relative):
            raise GitSnapshotError(
                f"`{relative}` is tracked but not a readable regular candidate file"
            )
    return path.read_text(encoding="utf-8")


def context_path_candidates(value):
    candidates = set(CONTEXT_BACKTICK_RE.findall(value or ""))
    candidates.update(markdown_link_destinations(value or ""))
    paths = []
    for candidate in candidates:
        candidate = candidate.split("#", 1)[0]
        path = Path(candidate)
        if not candidate or path.is_absolute() or ".." in path.parts \
                or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
            continue
        paths.append(candidate)
    return sorted(set(paths))


def blocking_boundary_tokens(value):
    tokens = (value or "").strip().split()
    allowed = (
        TASK_BOUNDARY_RE,
        TRANSITION_BOUNDARY_RE,
        OPERATION_BOUNDARY_RE,
    )
    if len(tokens) != 1 or not any(
        pattern.fullmatch(tokens[0]) for pattern in allowed
    ):
        return []
    return tokens


def future_boundary_tokens(value):
    tokens = (value or "").strip().split()
    if not tokens:
        return []
    first = tokens[0]
    first_is_date = bool(LEADING_DATE_RE.fullmatch(first)) and parse_date(first) is not None
    first_is_named = bool(
        EVENT_BOUNDARY_RE.fullmatch(first) or TRANSITION_BOUNDARY_RE.fullmatch(first)
    )
    if not (first_is_date or first_is_named):
        return []
    if not all(TASK_BOUNDARY_RE.fullmatch(token) for token in tokens[1:]):
        return []
    return tokens


def valid_future_boundary(value):
    return bool(future_boundary_tokens(value))


def boundary_task_ids(tokens):
    return {
        matched.group(1)
        for token in tokens
        for matched in [TASK_BOUNDARY_RE.fullmatch(token)]
        if matched
    }


def boundary_transitions(tokens):
    return {
        matched.group(1)
        for token in tokens
        for matched in [TRANSITION_BOUNDARY_RE.fullmatch(token)]
        if matched
    }


def blocking_task_ids(value):
    return boundary_task_ids(blocking_boundary_tokens(value))


def valid_queue_item_path(path):
    parts = Path(path).parts
    return bool(
        len(parts) == 4
        and parts[0] == "message-queue"
        and parts[1] in ("needs-human", "needs-agent")
        and SLUG_RE.fullmatch(parts[2])
        and QUEUE_ITEM_RE.fullmatch(parts[3])
    )


def queue_document_path(path):
    """Recognize only root contracts and typed-leaf README documentation."""
    normalized = Path(path).as_posix()
    if normalized in QUEUE_ROOT_DOCUMENT_PATHS:
        return True
    parts = Path(normalized).parts
    return bool(
        len(parts) == 4
        and parts[0] == "message-queue"
        and parts[1] in ("needs-human", "needs-agent")
        and SLUG_RE.fullmatch(parts[2])
        and parts[3] == "README.md"
    )


def governed_queue_path(path):
    """Return whether a path can carry action state, even when malformed."""
    parts = Path(path).parts
    return bool(
        len(parts) >= 2
        and parts[0] == "message-queue"
        and not queue_document_path(path)
    )


def queue_action_slug(path):
    name = Path(path).name
    return re.sub(
        r"^(?:blocking|future-blocking|non-blocking)-", "", name
    )


def name_status_records(data):
    """Parse NUL-delimited Git --name-status output."""
    tokens = data.split(b"\0")
    records = []
    offset = 0
    while offset < len(tokens) and tokens[offset]:
        status = tokens[offset].decode("ascii", errors="replace")
        offset += 1
        if status.startswith(("R", "C")):
            if offset + 1 >= len(tokens):
                raise GitSnapshotError("Git returned a truncated rename record")
            source = tokens[offset].decode(
                "utf-8", errors="surrogateescape"
            )
            destination = tokens[offset + 1].decode(
                "utf-8", errors="surrogateescape"
            )
            offset += 2
            records.append((status, source, destination))
            continue
        if offset >= len(tokens):
            raise GitSnapshotError("Git returned a truncated name-status record")
        name = tokens[offset].decode("utf-8", errors="surrogateescape")
        offset += 1
        records.append((status, name, name))
    return records


def identity_preserving_queue_move(source, destination, status=""):
    """Keep queue-to-queue renames in the mutation stream for identity checks."""
    if not valid_queue_item_path(destination):
        return False
    if not valid_queue_item_path(source):
        return governed_queue_path(source)
    source_parts = Path(source).parts
    destination_parts = Path(destination).parts
    if source_parts[1:3] != destination_parts[1:3]:
        return True
    if queue_action_slug(source) == queue_action_slug(destination):
        return True
    # A path-only slug clarification is safe to send through content identity.
    # A content-changing new slug may be a resolution successor, so leave it in
    # the deletion stream where successor evidence is evaluated.
    return status == "R100"


def deleted_queue_paths_from_name_status(data):
    """Treat only identity-preserving queue-to-queue renames as moves."""
    paths = []
    for status, source, destination in name_status_records(data):
        if status.startswith("R"):
            if governed_queue_path(source) \
                    and not identity_preserving_queue_move(
                        source, destination, status
                    ):
                paths.append(source)
        elif status == "D" and governed_queue_path(source):
            paths.append(source)
    return paths


def mutated_queue_paths_from_name_status(data):
    """Return governed in-place changes and identity-preserving moves."""
    paths = []
    for status, source, destination in name_status_records(data):
        if status.startswith("R"):
            if governed_queue_path(source) \
                    and identity_preserving_queue_move(
                        source, destination, status
                    ):
                paths.append((source, destination))
        elif status in {"M", "T"} and governed_queue_path(source):
            paths.append((source, destination))
    return paths


def git_artifact_bytes_at(revision, path):
    """Read one regular repository file at an exact commit, or return absent."""
    tree = subprocess.run(
        ["git", "--no-replace-objects", "ls-tree", "-z", revision, "--", path],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(git_failure(
            tree, f"could not inspect `{path}` at {revision}"
        ))
    entries = parse_git_tree_records(tree.stdout)
    if entries.get(path) not in ("100644", "100755"):
        return None
    artifact = subprocess.run(
        ["git", "--no-replace-objects", "show", f"{revision}:{path}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if artifact.returncode:
        raise GitSnapshotError(git_failure(
            artifact, f"could not read `{path}` at {revision}"
        ))
    return artifact.stdout


def decode_utf8_artifact(artifact, label):
    try:
        return artifact.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GitSnapshotError(
            f"{label} is not valid UTF-8: {error}"
        ) from error


def git_text_at(revision, path):
    artifact = git_artifact_bytes_at(revision, path)
    if artifact is None:
        raise GitSnapshotError(
            f"could not read `{path}` from {revision}"
        )
    return decode_utf8_artifact(artifact, f"`{path}` at {revision}")


def queue_resolution_enabled():
    contract = repo_artifact_bytes(QUEUE / "AGENTS.md")
    return bool(
        contract is not None
        and text_fields(decode_utf8_artifact(
            contract, "candidate `message-queue/AGENTS.md`"
        )).get(
            "Queue resolution schema", ""
        ).strip() == "v1"
    )


def queue_resolution_v1_at(revision):
    """Return whether one exact candidate or commit enables queue v1."""
    artifact = (
        repo_artifact_bytes(QUEUE / "AGENTS.md")
        if revision is None
        else git_artifact_bytes_at(revision, "message-queue/AGENTS.md")
    )
    return bool(
        artifact is not None
        and text_fields(decode_utf8_artifact(
            artifact,
            (
                "candidate `message-queue/AGENTS.md`"
                if revision is None
                else f"`message-queue/AGENTS.md` at {revision}"
            ),
        )).get("Queue resolution schema", "").strip() == "v1"
    )


def schema_activation_commits(head, path, field, version="v1"):
    """Return every reachable marker-bearing commit, including merged branches."""
    if not head:
        return (), None
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "log",
            "--full-history", "--reverse", "--format=%H", head, "--", path,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if history.returncode:
        return (), history.stderr.strip() or (
            f"could not inspect {field} activation history"
        )
    activations = []
    for commit in history.stdout.splitlines():
        artifact = git_artifact_bytes_at(commit, path)
        if artifact is None:
            continue
        text = decode_utf8_artifact(artifact, f"`{path}` at {commit}")
        if text_fields(text).get(field, "").strip() == version:
            activations.append(commit)
    return tuple(activations), None


def queue_resolution_activation_commits(head):
    activations, error = schema_activation_commits(
        head,
        "message-queue/AGENTS.md",
        "Queue resolution schema",
    )
    if error:
        raise GitSnapshotError(error)
    return activations


def descended_from_any(revision, ancestors):
    """Return whether revision descends from any ancestor, failing Git errors closed."""
    for ancestor in ancestors:
        relationship = subprocess.run(
            [
                "git", "--no-replace-objects", "merge-base",
                "--is-ancestor", ancestor, revision,
            ],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if relationship.returncode == 0:
            return True, None
        if relationship.returncode != 1:
            detail = relationship.stderr.decode(
                "utf-8", errors="replace"
            ).strip() if relationship.stderr else ""
            return False, detail or (
                f"could not compare activation {ancestor} to {revision}"
            )
    return False, None


def governed_by_activation_join(revision, activations):
    """Govern descendants and histories joined in parallel with an activation."""
    governed, error = descended_from_any(revision, activations)
    if governed or error:
        return governed, error
    for activation in activations:
        relationship = subprocess.run(
            [
                "git", "--no-replace-objects", "merge-base",
                "--is-ancestor", revision, activation,
            ],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if relationship.returncode == 1:
            # Neither commit descends from the other. The candidate that joins
            # them activates the schema for this newly admitted history.
            return True, None
        if relationship.returncode != 0:
            detail = relationship.stderr.decode(
                "utf-8", errors="replace"
            ).strip() if relationship.stderr else ""
            return False, detail or (
                f"could not compare {revision} to activation {activation}"
            )
    # The revision predates every activation and remains a legacy record.
    return False, None


def deleted_paths_between(parent, child):
    deleted = subprocess.run(
        [
            "git", "--no-replace-objects", "diff-tree",
            "-r", "--no-commit-id", "--name-status",
            "-z", "-M", "--diff-filter=DR", parent, child, "--",
            "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if deleted.returncode:
        raise GitSnapshotError(git_failure(
            deleted, f"could not inspect queue deletions in {child}"
        ))
    return deleted_queue_paths_from_name_status(deleted.stdout)


def mutated_paths_between(parent, child):
    changed = subprocess.run(
        [
            "git", "--no-replace-objects", "diff-tree",
            "-r", "--no-commit-id", "--name-status",
            "-z", "-M", "--diff-filter=MRT", parent, child, "--",
            "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, f"could not inspect queue mutations in {child}"
        ))
    return mutated_queue_paths_from_name_status(changed.stdout)


def staged_deleted_queue_paths():
    if not _GIT_HEAD_OID:
        return []
    deleted = subprocess.run(
        [
            "git", "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=DR", _GIT_HEAD_OID, "--", "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if deleted.returncode:
        raise GitSnapshotError(git_failure(
            deleted, "could not inspect staged queue deletions"
        ))
    return deleted_queue_paths_from_name_status(deleted.stdout)


def staged_mutated_queue_paths():
    if not _GIT_HEAD_OID:
        return []
    changed = subprocess.run(
        [
            "git", "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=MRT", _GIT_HEAD_OID, "--", "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, "could not inspect staged queue mutations"
        ))
    return mutated_queue_paths_from_name_status(changed.stdout)


def queue_revision_edges(activations):
    """Yield every governed parent/candidate edge in the staged or range view."""
    if CHANGE_RANGE is None:
        if _GIT_HEAD_OID:
            yield _GIT_HEAD_OID, None
        return
    if CHANGE_RANGE.startswith("root:"):
        range_head = CHANGE_RANGE[len("root:"):]
        revision_range = range_head
    else:
        base, range_head = CHANGE_RANGE.split("...", 1)
        merge_base = subprocess.run(
            ["git", "--no-replace-objects", "merge-base", base, range_head],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if merge_base.returncode or not merge_base.stdout.strip():
            raise GitSnapshotError(
                merge_base.stderr.strip()
                or "could not find the queue-deletion range merge base"
            )
        revision_range = f"{merge_base.stdout.strip()}..{range_head}"

    revisions = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--reverse", "--topo-order", revision_range,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if revisions.returncode:
        raise GitSnapshotError(
            revisions.stderr.strip()
            or "could not enumerate queue-deletion commits"
        )
    commits = revisions.stdout.splitlines()
    if _GIT_HEAD_OID and _GIT_HEAD_OID != range_head:
        commits.append(_GIT_HEAD_OID)
    for commit in commits:
        governed, governance_error = governed_by_activation_join(
            commit, activations
        )
        if governance_error:
            raise GitSnapshotError(governance_error)
        if not governed:
            continue
        ancestry = subprocess.run(
            [
                "git", "--no-replace-objects", "rev-list",
                "--parents", "-n", "1", commit,
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if ancestry.returncode:
            raise GitSnapshotError(
                ancestry.stderr.strip()
                or f"could not inspect parents of {commit}"
            )
        for parent in ancestry.stdout.split()[1:]:
            yield parent, commit


def queue_deletion_events(activations):
    """Yield prior/candidate revisions for every governed queue deletion."""
    for parent, revision in queue_revision_edges(activations):
        deleted = (
            staged_deleted_queue_paths()
            if revision is None
            else deleted_paths_between(parent, revision)
        )
        for path in deleted:
            yield path, git_text_at(parent, path), parent, revision


def queue_mutation_events(activations):
    """Yield both sides of every governed action modification or move."""
    for parent, revision in queue_revision_edges(activations):
        mutated = (
            staged_mutated_queue_paths()
            if revision is None
            else mutated_paths_between(parent, revision)
        )
        for source, destination in mutated:
            before = git_text_at(parent, source)
            after_bytes = (
                repo_artifact_bytes(REPO / destination)
                if revision is None
                else git_artifact_bytes_at(revision, destination)
            )
            if after_bytes is None:
                raise GitSnapshotError(
                    f"could not read queue mutation destination `{destination}`"
                )
            after = decode_utf8_artifact(
                after_bytes,
                f"`{destination}` in the queue mutation candidate",
            )
            yield source, destination, before, after, parent, revision


def governed_handover_path(path):
    """Recognize a handover path even when its conversation name is malformed."""
    parts = Path(path).parts
    return bool(
        len(parts) == 4
        and parts[:2] == ("history", "conversations")
        and parts[3] == "handover.md"
    )


def mutated_handover_paths_from_name_status(data):
    """Return pre-existing handovers changed in place or renamed."""
    paths = []
    for status, source, _destination in name_status_records(data):
        if status.startswith("R") and governed_handover_path(source):
            paths.append(source)
        elif status in {"M", "T"} and governed_handover_path(source):
            paths.append(source)
    return paths


def mutated_handover_paths_between(parent, child):
    changed = subprocess.run(
        [
            "git", "--no-replace-objects", "diff-tree",
            "-r", "--no-commit-id", "--name-status",
            "-z", "-M", "--diff-filter=MRT", parent, child, "--",
            "history/conversations",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, f"could not inspect handover mutations in {child}"
        ))
    return mutated_handover_paths_from_name_status(changed.stdout)


def staged_mutated_handover_paths():
    if not _GIT_HEAD_OID:
        return []
    changed = subprocess.run(
        [
            "git", "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=MRT", _GIT_HEAD_OID, "--",
            "history/conversations",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, "could not inspect staged handover mutations"
        ))
    return mutated_handover_paths_from_name_status(changed.stdout)


def handover_mutation_events(activations):
    """Yield every post-adoption mutation edge, including intermediate commits."""
    for parent, revision in queue_revision_edges(activations):
        paths = (
            staged_mutated_handover_paths()
            if revision is None
            else mutated_handover_paths_between(parent, revision)
        )
        for path in paths:
            yield path, parent, revision


def committed_queue_deletion_events(parent, revision):
    """Yield queue deletions on one explicit committed snapshot edge."""
    for path in deleted_paths_between(parent, revision):
        yield path, git_text_at(parent, path), parent, revision


def committed_queue_mutation_events(parent, revision):
    """Yield queue mutations on one explicit committed snapshot edge."""
    for source, destination in mutated_paths_between(parent, revision):
        before = git_text_at(parent, source)
        after_bytes = git_artifact_bytes_at(revision, destination)
        if after_bytes is None:
            raise GitSnapshotError(
                f"could not read queue mutation destination `{destination}`"
            )
        after = decode_utf8_artifact(
            after_bytes,
            f"`{destination}` in the queue mutation candidate",
        )
        yield source, destination, before, after, parent, revision


def displaced_tip_edge():
    """Return an explicit divergent old-ref-tip -> new-head continuity edge."""
    if DISPLACED_TIP is None:
        return None
    if CHANGE_RANGE is None or CHANGE_RANGE.startswith("root:"):
        raise GitSnapshotError(
            "--displaced-tip requires a full BASE...HEAD --range"
        )
    range_head = CHANGE_RANGE.split("...", 1)[1]
    ancestor = subprocess.run(
        [
            "git", "--no-replace-objects", "merge-base",
            "--is-ancestor", DISPLACED_TIP, range_head,
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if ancestor.returncode == 0:
        return None
    if ancestor.returncode != 1:
        detail = ancestor.stderr.decode(
            "utf-8", errors="replace"
        ).strip() if ancestor.stderr else ""
        raise GitSnapshotError(
            detail or "could not compare the pushed old tip to the new head"
        )
    return DISPLACED_TIP, range_head


def pickup_task_path(text):
    candidates = [
        path for path in context_path_candidates(
            text_fields(text).get("Full context", "")
        )
        if re.fullmatch(
            r"tasks/0_backlog/"
            r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)/task\.md",
            path,
        )
    ]
    return candidates[0] if len(candidates) == 1 else None


def task_incarnations_at(revision, task_id):
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "--name-only", revision, "--", "tasks",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(
            tree.stderr.strip()
            or f"could not inspect task state in {revision}"
        )
    paths = tree.stdout.splitlines()
    return [
        name for name in paths
        if re.fullmatch(
            rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
            + re.escape(task_id)
            + r"/task\.md",
            name,
        )
    ]


def task_incarnations_in_tree(revision):
    """Return every canonical task record path at one exact revision."""
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "--name-only", revision, "--", "tasks",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(
            tree.stderr.strip()
            or f"could not inspect tasks at {revision}"
        )
    return [
        name for name in tree.stdout.splitlines()
        if re.fullmatch(
            rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
            r"\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*/task\.md",
            name,
        )
    ]


def task_service_present_at(revision):
    """Return whether an exact revision retains any tracked task-service file."""
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "--name-only", revision, "--", "tasks",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(
            tree.stderr.strip()
            or f"could not inspect the task service at {revision}"
        )
    return any(tree.stdout.splitlines())


def pickup_completed(path, text, prior_revision, revision):
    got = text_fields(text)
    if got.get("Request kind", "").strip() != "task-pickup" \
            or got.get("Status", "").strip() != "open":
        return False
    backlog = pickup_task_path(text)
    if backlog is None:
        return False
    task_id = Path(backlog).parts[2]
    current = f"tasks/1_in-progress/{task_id}/task.md"
    prior_incarnations = task_incarnations_at(prior_revision, task_id)
    prior_artifact = git_artifact_bytes_at(prior_revision, backlog)
    if prior_incarnations != [backlog] or prior_artifact is None:
        return False
    prior_task = text_fields(decode_utf8_artifact(
        prior_artifact, f"`{backlog}` at {prior_revision}"
    ))
    if prior_task.get("Claimed-by", "").strip() != "unclaimed" \
            or path not in task_queue_paths(
                prior_task.get("Queue actions", "")
            ):
        return False
    if revision is None:
        entries = git_index_entries("tasks")
        incarnations = [
            name for name in entries
            if re.fullmatch(
                rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
                + re.escape(task_id)
                + r"/task\.md",
                name,
            )
        ]
        artifact = repo_artifact_bytes(REPO / current)
        backlog_absent = backlog not in entries
    else:
        incarnations = task_incarnations_at(revision, task_id)
        artifact = git_artifact_bytes_at(revision, current)
        backlog_absent = backlog not in incarnations
    if len(incarnations) != 1 or incarnations[0] != current \
            or artifact is None or not backlog_absent:
        return False
    task = text_fields(decode_utf8_artifact(
        artifact, f"`{current}` in the pickup candidate"
    ))
    claimant = task.get("Claimed-by", "").strip()
    return bool(
        has_concrete_value(claimant)
        and claimant != "unclaimed"
        and path not in task_queue_paths(task.get("Queue actions", ""))
    )


def normalize_claim_status(text):
    return re.sub(
        r"^(\*\*Status:\*\*)[ \t]*.*$",
        r"\1 <claimed-status>",
        text,
        count=1,
        flags=re.M,
    )


def claim_identity(text, actor, leaf):
    got = text_fields(text)
    keys = {
        "Filed", "Action", "Full context", "Resolution evidence",
    }
    if actor == "needs-human":
        keys.update({
            "Your answer", "Your review", "Review target",
            "Review revision", "Reviewed revision", "Review outcome",
            "Successor action",
        })
    else:
        keys.update({
            "Request kind", "Check", "Subject",
            "Generated by", "Finding identity",
        })
    return tuple((key, got.get(key, "").strip()) for key in sorted(keys))


LIFECYCLE_MUTABLE_FIELDS = {
    "Status",
    "Blocks now",
    "Blocks at",
    "Until then",
    "If unanswered",
}
AGENT_NOTES_SECTION_RE = re.compile(
    r"^## Agent notes\s*\n.*?(?=^##(?:\s|$)|\Z)",
    flags=re.M | re.S,
)


def immutable_action_text(text, actor, leaf, extra_mutable_fields=()):
    """Return action-defining visible text with lifecycle state removed."""
    mutable_fields = set(LIFECYCLE_MUTABLE_FIELDS)
    mutable_fields.update(extra_mutable_fields)
    if actor == "needs-human" and leaf == "reviews":
        mutable_fields.update({
            "Your review", "Review target", "Review revision",
            "Reviewed revision", "Review outcome", "Successor action",
            "Resolution evidence",
        })
    elif actor == "needs-human":
        mutable_fields.update({"Your answer", "Your review"})
    clean = semantic_text(text)
    if actor == "needs-agent" and leaf == "retries":
        clean = AGENT_NOTES_SECTION_RE.sub("", clean)
    lines = []
    for line in clean.splitlines():
        matched = FIELD_RE.fullmatch(line)
        if matched and matched.group(1) in mutable_fields:
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def retry_action_identity(path, text):
    item = REPO / path
    if not (
        reconciler_owned_retry(item, text)
        or legacy_reconciler_retry(item, text)
    ):
        return None
    got = text_fields(text)
    parts = Path(path).parts
    actor = parts[1] if len(parts) > 1 else ""
    leaf = parts[2] if len(parts) > 2 else ""
    return (
        "generated-retry",
        actor,
        leaf,
        got.get("Check", "").strip(),
        got.get("Subject", "").strip().strip("`"),
    )


def queue_action_identity(path, text, extra_mutable_fields=()):
    retry = retry_action_identity(path, text)
    parts = Path(path).parts
    actor = parts[1] if len(parts) > 1 else ""
    leaf = parts[2] if len(parts) > 2 else ""
    return retry if retry is not None else (
        "ordinary-action",
        actor,
        leaf,
        immutable_action_text(
            text, actor, leaf, extra_mutable_fields=extra_mutable_fields
        ),
    )


def human_response_fields(text):
    got = text_fields(text)
    return {
        key: got.get(key, "").strip()
        for key in (
            "Your answer",
            "Your review",
            "Review target",
            "Review revision",
            "Reviewed revision",
            "Review outcome",
            "Resolution evidence",
        )
    }


def first_concrete_response(fields):
    for key in ("Your answer", "Your review"):
        if has_concrete_value(fields.get(key, "")):
            return key
    return None


def unanswered_review(fields):
    return bool(
        first_concrete_response(fields) is None
        and not has_concrete_value(fields.get("Reviewed revision", ""))
        and fields.get("Review outcome", "pending") in {"", "pending"}
    )


def human_projection_context_migration(
    source, destination, before, after, prior_revision, revision
):
    """Allow one legacy-human enrichment on the exact queue-v1 activation edge."""
    source_parts = Path(source).parts
    destination_parts = Path(destination).parts
    if len(source_parts) < 3 or len(destination_parts) < 3 \
            or source_parts[1] != "needs-human" \
            or destination_parts[1] != "needs-human" \
            or source_parts[2] != destination_parts[2] \
            or queue_resolution_v1_at(prior_revision) \
            or not queue_resolution_v1_at(revision):
        return False
    prior = text_fields(before)
    current = text_fields(after)
    for field in HUMAN_PROJECTION_FIELDS:
        if not has_concrete_value(current.get(field, "")):
            return False
        if has_concrete_value(prior.get(field, "")) \
                and prior[field].strip() != current[field].strip():
            return False
    return queue_action_identity(
        source,
        before,
        extra_mutable_fields=HUMAN_PROJECTION_FIELDS,
    ) == queue_action_identity(
        destination,
        after,
        extra_mutable_fields=HUMAN_PROJECTION_FIELDS,
    )


def queue_mutation_problem(
    source, destination, before, after, prior_revision=None, revision=None
):
    """Reject action replacement while permitting lifecycle-only updates."""
    if queue_action_identity(source, before) != queue_action_identity(
        destination, after
    ) and not human_projection_context_migration(
        source,
        destination,
        before,
        after,
        prior_revision,
        revision,
    ):
        return "action identity changed while the queue item remained live"

    source_parts = Path(source).parts
    destination_parts = Path(destination).parts
    actor = (
        destination_parts[1]
        if len(destination_parts) > 1
        and destination_parts[1] in {"needs-human", "needs-agent"}
        else source_parts[1]
        if len(source_parts) > 1
        and source_parts[1] in {"needs-human", "needs-agent"}
        else ""
    )
    prior_response = {}
    current_response = {}
    if actor == "needs-human":
        prior_response = human_response_fields(before)
        current_response = human_response_fields(after)
        prior_status = text_fields(before).get("Status", "").strip()
        current_status = text_fields(after).get("Status", "").strip()
        source_leaf = source_parts[2] if len(source_parts) > 2 else ""
        destination_leaf = (
            destination_parts[2] if len(destination_parts) > 2 else ""
        )
        is_review = "reviews" in {source_leaf, destination_leaf}
        if is_review:
            binding_keys = ("Review target", "Review revision")
            prior_binding = tuple(
                prior_response[key] for key in binding_keys
            )
            current_binding = tuple(
                current_response[key] for key in binding_keys
            )
            publication_transition = (
                prior_status == "awaiting-artifact"
                and current_status == "waiting"
                and prior_binding == ("pending", "pending")
                and unanswered_review(prior_response)
                and unanswered_review(current_response)
            )
            retraction_transition = (
                prior_status == "waiting"
                and current_status == "awaiting-artifact"
                and current_binding == ("pending", "pending")
                and unanswered_review(prior_response)
                and unanswered_review(current_response)
            )
            if prior_binding != current_binding \
                    and not (
                        publication_transition or retraction_transition
                    ):
                return (
                    "immutable review binding changed outside the "
                    "unanswered waiting -> awaiting-artifact retraction or "
                    "awaiting-artifact -> waiting publication transition"
                )
        response_changed = current_response != prior_response
        if first_concrete_response(prior_response) is not None \
                and response_changed:
            return (
                "human response or its immutable review binding changed "
                "after the first concrete response"
            )
        if current_status == "folding" and response_changed:
            return "the waiting -> folding claim changed more than status"

    source_timing = delivery_class(Path(source).name)
    destination_timing = delivery_class(Path(destination).name)
    prior_timing = tuple(
        (key, text_fields(before).get(key, "").strip())
        for keys in QUEUE_TIMING_FIELDS.values()
        for key in keys
    )
    current_timing = tuple(
        (key, text_fields(after).get(key, "").strip())
        for keys in QUEUE_TIMING_FIELDS.values()
        for key in keys
    )
    timing_changed = (
        source_timing != destination_timing
        or prior_timing != current_timing
    )
    if actor == "needs-human" and timing_changed and (
        first_concrete_response(prior_response) is not None
        or first_concrete_response(current_response) is not None
    ):
        return "dependency timing changed with or after the human response"
    if source_timing in QUEUE_TIMING_ORDER \
            and destination_timing in QUEUE_TIMING_ORDER \
            and QUEUE_TIMING_ORDER[destination_timing] \
            < QUEUE_TIMING_ORDER[source_timing]:
        return "dependency timing was weakened while the queue item remained live"
    if source_timing == destination_timing and prior_timing != current_timing:
        return "dependency timing changed without a matching timing-prefix rename"
    return None


def revision_parents(revision, label):
    ancestry = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--parents", "-n", "1", revision,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if ancestry.returncode:
        raise GitSnapshotError(
            ancestry.stderr.strip() or f"could not inspect {label}"
        )
    return ancestry.stdout.split()[1:]


def matching_lineage_paths(parent, revision, path, identity):
    """Find this action in one parent, following one unambiguous rename."""
    same_path = git_artifact_bytes_at(parent, path)
    if same_path is not None:
        text = decode_utf8_artifact(
            same_path, f"`{path}` at {parent}"
        )
        # Preserve the current incarnation even when its action bytes changed; the
        # claim check then reports that rewrite instead of losing the receipt.
        return [(path, text)]

    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "-z", parent, "--", "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(git_failure(
            tree, f"could not follow queue action lineage at {parent}"
        ))
    matches = []
    for candidate, mode in parse_git_tree_records(tree.stdout).items():
        if mode not in ("100644", "100755") \
                or not governed_queue_path(candidate):
            continue
        artifact = git_artifact_bytes_at(parent, candidate)
        if artifact is None:
            continue
        candidate_text = decode_utf8_artifact(
            artifact, f"`{candidate}` at {parent}"
        )
        if queue_action_identity(candidate, candidate_text) == identity:
            matches.append((candidate, candidate_text))
    if len(matches) > 1:
        raise GitSnapshotError(
            f"queue action lineage is ambiguous at {parent}: "
            + ", ".join(path for path, _text in matches)
        )
    # The prior path must disappear on this exact edge. Otherwise a newly
    # added identical action could borrow the older action's claim receipt.
    return [
        (candidate, candidate_text)
        for candidate, candidate_text in matches
        if git_artifact_bytes_at(revision, candidate) is None
    ]


def queue_lineage_revision_snapshots(path, text, prior_revision):
    """Yield revision, path, and text across one unambiguous action lineage."""
    identity = queue_action_identity(path, text)
    stack = [(prior_revision, path, text)]
    seen = set()
    while stack:
        revision, current_path, current = stack.pop()
        state = (revision, current_path)
        if state in seen:
            continue
        seen.add(state)
        if queue_action_identity(current_path, current) != identity:
            continue
        yield revision, current_path, current
        parents = revision_parents(
            revision, f"queue history for `{current_path}`"
        )
        predecessors = []
        for parent in parents:
            artifact = git_artifact_bytes_at(parent, current_path)
            if artifact is not None:
                predecessors.append((
                    parent,
                    current_path,
                    decode_utf8_artifact(
                        artifact, f"`{current_path}` at {parent}"
                    ),
                ))
        if not predecessors and len(parents) == 1:
            parent = parents[0]
            predecessors.extend(
                (parent, previous_path, previous)
                for previous_path, previous in matching_lineage_paths(
                    parent, revision, current_path, identity
                )
            )
        stack.extend(predecessors)


def queue_lineage_snapshots(path, text, prior_revision):
    """Yield one action's historical snapshots across unambiguous renames."""
    for _revision, current_path, current in queue_lineage_revision_snapshots(
        path, text, prior_revision
    ):
        yield current_path, current


def historical_queue_timing(path, text, prior_revision, timing):
    """Return the nearest snapshot where this action used one timing class."""
    return next(
        (
            (candidate_path, candidate_text)
            for candidate_path, candidate_text in queue_lineage_snapshots(
                path, text, prior_revision
            )
            if delivery_class(Path(candidate_path).name) == timing
        ),
        None,
    )


def claimed_lifecycle_problem(path, text, prior_revision, actor, leaf):
    """Require a committed status-only claim, even across a later timing rename."""
    claimed = "folding" if actor == "needs-human" else "in-repair"
    initial = "waiting" if actor == "needs-human" else "open"
    identity = queue_action_identity(path, text)
    final_identity = claim_identity(text, actor, leaf)
    stack = [(prior_revision, path, text)]
    seen = set()
    while stack:
        revision, current_path, current = stack.pop()
        state = (revision, current_path)
        if state in seen:
            continue
        seen.add(state)
        parents = revision_parents(
            revision, f"claim history for `{current_path}`"
        )
        predecessors = []
        for parent in parents:
            artifact = git_artifact_bytes_at(parent, current_path)
            if artifact is not None:
                predecessors.append((
                    parent,
                    current_path,
                    decode_utf8_artifact(
                        artifact, f"`{current_path}` at {parent}"
                    ),
                ))
        # A merge may present a same-path action on one parent and an identical
        # claimed action under another path on a second parent. Prefer exact-path
        # lineage across every merge; infer a rename only on a one-parent edge.
        if not predecessors and len(parents) == 1:
            parent = parents[0]
            predecessors.extend(
                (parent, previous_path, previous)
                for previous_path, previous in matching_lineage_paths(
                    parent, revision, current_path, identity
                )
            )
        if text_fields(current).get("Status", "").strip() == claimed:
            for _parent, previous_path, previous in predecessors:
                if previous_path != current_path:
                    continue  # a claim commit changes only the status line
                if text_fields(previous).get("Status", "").strip() != initial:
                    continue
                if normalize_claim_status(previous) != normalize_claim_status(current):
                    continue
                if claim_identity(current, actor, leaf) != final_identity:
                    return "action identity or response changed after it was claimed"
                return None
        stack.extend(predecessors)
    return (
        f"no committed one-line {initial} -> {claimed} claim transition exists"
    )


def resolution_evidence_paths(text):
    value = text_fields(text).get("Resolution evidence", "")
    paths = context_path_candidates(value)
    if not paths or any(
        path == "message-queue" or path.startswith("message-queue/")
        for path in paths
    ):
        return []
    return paths


def resolution_evidence_problem(text, prior_revision, revision):
    paths = resolution_evidence_paths(text)
    if not paths:
        return "missing non-queue **Resolution evidence:** file path"
    unchanged = []
    for path in paths:
        before = git_artifact_bytes_at(prior_revision, path)
        after = (
            repo_artifact_bytes(REPO / path)
            if revision is None
            else git_artifact_bytes_at(revision, path)
        )
        if after is None or after == before:
            unchanged.append(path)
    if unchanged:
        return (
            "resolution evidence was not created or changed in the deletion commit: "
            + ", ".join(f"`{path}`" for path in unchanged)
        )
    return None


@contextlib.contextmanager
def git_revision_candidate(revision, preserve_change_range=False):
    """Temporarily expose one committed tree through the candidate-read helpers."""
    global CHANGE_RANGE, _GIT_SNAPSHOT_CACHE_ACTIVE
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE, _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    global _GIT_ARTIFACT_CACHE, _GIT_BLOB_CACHE

    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "-z", revision,
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(git_failure(
            tree, f"could not capture historical candidate {revision}"
        ))
    modes = {}
    oids = {}
    all_paths = set()
    for record in tree.stdout.split(b"\0"):
        metadata, separator, encoded_name = record.partition(b"\t")
        if not separator:
            continue
        parts = metadata.decode("ascii", errors="replace").split()
        if len(parts) != 3:
            raise GitSnapshotError(
                f"Git returned malformed tree data for {revision}"
            )
        mode, kind, oid = parts
        name = encoded_name.decode("utf-8", errors="surrogateescape")
        all_paths.add(name)
        if kind == "blob":
            modes[name] = mode
            oids[name] = oid

    saved = (
        CHANGE_RANGE,
        _GIT_SNAPSHOT_CACHE_ACTIVE,
        _GIT_INDEX_CACHE,
        _GIT_INDEX_OID_CACHE,
        _GIT_INDEX_ALL_PATHS_CACHE,
        _GIT_HEAD_PATHS_CACHE,
        _GIT_HEAD_OID,
        _GIT_ARTIFACT_CACHE,
        _GIT_BLOB_CACHE,
    )
    close_git_cat_file()
    if not preserve_change_range:
        CHANGE_RANGE = f"root:{revision}"
    _GIT_SNAPSHOT_CACHE_ACTIVE = True
    _GIT_INDEX_CACHE = modes
    _GIT_INDEX_OID_CACHE = oids
    _GIT_INDEX_ALL_PATHS_CACHE = all_paths
    _GIT_HEAD_PATHS_CACHE = all_paths
    _GIT_HEAD_OID = revision
    _GIT_ARTIFACT_CACHE = {}
    _GIT_BLOB_CACHE = {}
    try:
        yield
    finally:
        close_git_cat_file()
        (
            CHANGE_RANGE,
            _GIT_SNAPSHOT_CACHE_ACTIVE,
            _GIT_INDEX_CACHE,
            _GIT_INDEX_OID_CACHE,
            _GIT_INDEX_ALL_PATHS_CACHE,
            _GIT_HEAD_PATHS_CACHE,
            _GIT_HEAD_OID,
            _GIT_ARTIFACT_CACHE,
            _GIT_BLOB_CACHE,
        ) = saved


def generated_retry_clear(text, revision=None):
    got = text_fields(text)
    check = got.get("Check", "").strip()
    subject = got.get("Subject", "").strip().strip("`")
    if not check or not subject or check == "queue-resolution":
        return False
    checker = CHECKS.get(check)
    if checker is None:
        return False
    context = (
        contextlib.nullcontext()
        if revision is None
        else git_revision_candidate(revision)
    )
    with context:
        return not any(
            finding.check == check and str(finding.subject) == subject
            for finding in checker()
        )


def candidate_artifact_bytes(path, revision):
    return (
        repo_artifact_bytes(REPO / path)
        if revision is None
        else git_artifact_bytes_at(revision, path)
    )


def review_binding_problem(text):
    """Validate one human response's immutable artifact binding."""
    got = text_fields(text)
    target = review_target(got.get("Review target", ""))
    review_revision = got.get("Review revision", "").strip()
    if target is None or not REVIEW_REVISION_RE.fullmatch(review_revision):
        return "review target or immutable revision is malformed"
    if got.get("Reviewed revision", "").strip() != review_revision:
        return "review response was not bound to its immutable revision"
    kind, value = target
    if kind == "git" and review_revision != value:
        return "Git review target and immutable revision do not match"
    if kind in {"local", "https"} \
            and not review_revision.startswith("sha256:"):
        return f"{kind} review target needs an immutable sha256 revision"
    return None


def review_candidate_problem(text, revision):
    """Require the bound artifact to remain exact in one candidate."""
    binding_problem = review_binding_problem(text)
    if binding_problem:
        return binding_problem
    got = text_fields(text)
    target = review_target(got.get("Review target", ""))
    review_revision = got.get("Review revision", "").strip()
    kind, value = target
    if kind == "local":
        artifact = candidate_artifact_bytes(value, revision)
        if artifact is None:
            return "reviewed local target is absent from the deletion candidate"
        expected = "sha256:" + hashlib.sha256(artifact).hexdigest()
        if review_revision != expected:
            return "reviewed local target changed after the bound review"
    elif kind == "git":
        if value != review_revision or git_review_revision_problems(
            review_revision
        ):
            return "reviewed Git target is no longer the bound artifact"
    return None


def git_is_ancestor(ancestor, descendant):
    result = subprocess.run(
        [
            "git", "--no-replace-objects", "merge-base", "--is-ancestor",
            ancestor, descendant,
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise GitSnapshotError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or f"could not compare Git ancestry for {ancestor} and {descendant}"
        )
    return result.returncode == 0


def deletion_and_later_candidates(revision):
    """Return the exact deletion candidate and every later admitted snapshot."""
    if revision is None:
        return (None,)
    head = committed_candidate_revision()
    if head is None or head == revision or not git_is_ancestor(revision, head):
        return (revision,)
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--reverse", "--topo-order", "--ancestry-path",
            f"{revision}..{head}",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if history.returncode:
        raise GitSnapshotError(
            history.stderr.strip()
            or "could not inspect post-deletion candidate history"
        )
    return (revision, *history.stdout.splitlines())


def changed_paths_between_revisions(base, head):
    result = subprocess.run(
        [
            "git", "--no-replace-objects", "diff", "--name-only", "-z",
            base, head, "--",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, f"could not compare reviewed Git candidate {base}..{head}"
        ))
    return {
        name.decode("utf-8", errors="surrogateescape")
        for name in result.stdout.split(b"\0")
        if name
    }


def reviewed_range_withdrawal_problem(text, candidate):
    """Require every reviewed proposal path to return to its base bytes."""
    got = text_fields(text)
    review_revision = got.get("Review revision", "").strip()
    if not review_revision.startswith("git:") or "..." not in review_revision:
        return "cancellation needs a candidate-range Git review"
    reviewed_base, reviewed_head = review_revision[len("git:"):].split("...")
    evidence = set(resolution_evidence_paths(text))
    proposal_paths = changed_paths_between_revisions(
        reviewed_base, reviewed_head
    )
    overlapping = sorted(proposal_paths.intersection(evidence))
    if overlapping:
        return (
            "cancellation evidence was part of the reviewed proposal: "
            + ", ".join(f"`{path}`" for path in overlapping)
        )
    still_active = []
    for path in sorted(proposal_paths):
        if valid_queue_item_path(path):
            continue
        if candidate_artifact_bytes(path, candidate) \
                != git_artifact_bytes_at(reviewed_base, path):
            still_active.append(path)
    if still_active:
        return (
            "reviewed proposal remains active at: "
            + ", ".join(f"`{path}`" for path in still_active)
        )
    return None


def git_range_review_tail_problem(review_revision, candidate):
    """Require one candidate to extend a reviewed range by queue state only."""
    object_ids = review_revision[len("git:"):].split("...")
    if len(object_ids) != 2:
        return None
    _reviewed_base, reviewed_head = object_ids
    if not git_is_ancestor(reviewed_head, candidate):
        return "reviewed Git head is not an ancestor of the boundary receipt"
    changed = changed_paths_between_revisions(reviewed_head, candidate)
    unreviewed = sorted(
        path for path in changed if not valid_queue_item_path(path)
    )
    if unreviewed:
        return (
            "boundary receipt contains unreviewed non-queue changes: "
            + ", ".join(f"`{path}`" for path in unreviewed)
        )
    return None


def git_range_review_freshness_problem(path, review_revision):
    """Require a Git-range approval to cover the active candidate modulo queue state."""
    object_ids = review_revision[len("git:"):].split("...")
    if len(object_ids) != 2:
        return None  # A single commit is a narrow artifact, not a candidate range.
    reviewed_base, reviewed_head = object_ids
    if CHANGE_RANGE is None or CHANGE_RANGE.startswith("root:"):
        return "Git-range approval needs an explicit active base...head range"
    active_base, _active_head = CHANGE_RANGE.split("...", 1)
    if reviewed_base != active_base:
        return (
            "reviewed Git base is stale; active base is "
            f"{active_base}"
        )
    candidate = committed_candidate_revision()
    if candidate is None:
        return "review freshness needs a committed candidate"
    problem = git_range_review_tail_problem(review_revision, candidate)
    if problem is None:
        return None
    return problem.replace(
        "boundary receipt", "active candidate"
    ).replace(
        "contains unreviewed non-queue changes",
        "changed outside queue lifecycle after review",
    )


def review_boundary_problem(item, reached):
    """Return why one live review does not satisfy its reached boundary."""
    rel = item.relative_to(REPO).as_posix()
    parts = Path(rel).parts
    if parts[1:3] != ("needs-human", "reviews"):
        return "the action still needs its recorded actor"
    text = repo_text(item)
    got = text_fields(text)
    if got.get("Status", "").strip() != "folding":
        return "the review has no committed folding claim"
    if got.get("Review outcome", "").strip() != "approved":
        return "only an approved review can authorize the boundary"
    if not has_concrete_value(got.get("Your review", "")):
        return "the review has no concrete human disposition"
    active_problem = active_blocking_repair_problem(item)
    if active_problem:
        return active_problem
    target_problem = review_candidate_problem(text, None)
    if target_problem:
        return target_problem
    review_revision = got.get("Review revision", "").strip()
    if review_revision.startswith("git:") and "..." in review_revision:
        return git_range_review_freshness_problem(rel, review_revision)
    return None


def task_status_at(revision, task_id):
    """Return one task's unique status and task record at a Git revision."""
    incarnations = task_incarnations_at(revision, task_id)
    if len(incarnations) != 1:
        return None, None
    path = incarnations[0]
    artifact = git_artifact_bytes_at(revision, path)
    if artifact is None:
        return None, None
    return (
        Path(path).parts[1],
        text_fields(decode_utf8_artifact(
            artifact, f"`{path}` at {revision}"
        )),
    )


def task_status_in_candidate(revision, task_id):
    """Return one task's unique status in an index or committed candidate."""
    if revision is not None:
        status, _task = task_status_at(revision, task_id)
        return status
    incarnations = sorted(
        path for path, mode in git_index_entries("tasks").items()
        if mode in ("100644", "100755")
        and re.fullmatch(
            rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
            + re.escape(task_id)
            + r"/task\.md",
            path,
        )
    )
    return (
        Path(incarnations[0]).parts[1]
        if len(incarnations) == 1 else None
    )


def task_ids_linking_queue_at(revision, queue_path):
    """Return task ids whose exact revision links one canonical queue item."""
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "--name-only", revision, "--", "tasks",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(
            tree.stderr.strip()
            or f"could not inspect task links in {revision}"
        )
    task_ids = set()
    for candidate in tree.stdout.splitlines():
        matched = re.fullmatch(
            rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
            r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)/task\.md",
            candidate,
        )
        if not matched:
            continue
        artifact = git_artifact_bytes_at(revision, candidate)
        if artifact is None:
            continue
        task = text_fields(decode_utf8_artifact(
            artifact, f"`{candidate}` at {revision}"
        ))
        if queue_path in task_queue_paths(task.get("Queue actions", "")):
            task_ids.add(matched.group(1))
    return task_ids


def task_transition_receipt_problem(
    path, text, prior_revision, revision, boundary_tokens
):
    """Require a committed task transition carrying an exact approved review."""
    transitions = boundary_transitions(boundary_tokens).intersection(
        TASK_LIFECYCLE_TRANSITIONS
    )
    if len(transitions) != 1:
        return "task-boundary cleanup needs one task lifecycle transition"
    transition = next(iter(transitions))
    task_ids = boundary_task_ids(boundary_tokens)
    if not task_ids:
        task_ids = task_ids_linking_queue_at(prior_revision, path)
    if not task_ids:
        return (
            "task-boundary cleanup needs a task:<id> boundary or a task "
            "record that still links the review"
        )

    history = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--topo-order", prior_revision,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if history.returncode:
        raise GitSnapshotError(
            history.stderr.strip()
            or "could not inspect task-boundary receipt history"
        )
    receipt_paths_at = {}
    for commit, receipt_path, receipt_text in queue_lineage_revision_snapshots(
        path, text, prior_revision
    ):
        if receipt_text == text:
            receipt_paths_at.setdefault(commit, set()).add(receipt_path)
    missing = []
    stale = {}
    for task_id in sorted(task_ids):
        prior_status, _prior_task = task_status_at(
            prior_revision, task_id
        )
        invalid_snapshots = [
            candidate for candidate in deletion_and_later_candidates(revision)
            if transition not in inferred_task_transitions(
                task_status_in_candidate(candidate, task_id)
            )
        ]
        if transition not in inferred_task_transitions(prior_status) \
                or invalid_snapshots:
            missing.append(task_id)
            stale[task_id] = (
                "task does not remain past transition:"
                + transition + (
                    " at " + ", ".join(
                        "index" if candidate is None else candidate
                        for candidate in invalid_snapshots
                    )
                    if invalid_snapshots else ""
                )
            )
            continue
        found = False
        for commit in history.stdout.splitlines():
            receipt_paths = receipt_paths_at.get(commit, set())
            if not receipt_paths:
                continue
            after_status, after_task = task_status_at(commit, task_id)
            if after_status is None \
                    or transition not in inferred_task_transitions(after_status) \
                    or not receipt_paths.intersection(task_queue_paths(
                        after_task.get("Queue actions", "")
                    )):
                continue
            for parent in revision_parents(
                commit, f"task-boundary receipt for {task_id}"
            ):
                before_status, _before_task = task_status_at(parent, task_id)
                if before_status is None:
                    continue
                if transition not in inferred_task_transitions(before_status):
                    found = True
                    break
            if found:
                break
        if not found:
            missing.append(task_id)
    if missing:
        detail = "; ".join(
            f"{task_id}: {stale[task_id]}"
            for task_id in missing if task_id in stale
        )
        return (
            "review must remain live until committed task transition "
            "history carries its exact approved receipt for: "
            + ", ".join(missing)
            + (f" ({detail})" if detail else "")
        )
    return None


def approved_review_merge_receipt_problem(
    path, text, prior_revision, boundary_tokens
):
    """Require the admitted target history to carry the live merge receipt."""
    got = text_fields(text)
    if "transition:merge" not in boundary_tokens:
        return (
            "review must remain live until its boundary adapter records "
            "durable crossing evidence"
        )
    review_revision = got.get("Review revision", "").strip()
    if not review_revision.startswith("git:") or "..." not in review_revision:
        return "merge cleanup needs a candidate-range Git review receipt"
    reviewed_base, reviewed_head = review_revision[len("git:"):].split("...")
    if CHANGE_RANGE is not None and CHANGE_RANGE.startswith("root:"):
        return (
            "merge cleanup needs a previously admitted target base; "
            "a root range has no prior admission boundary"
        )
    # In exact-range admission, only history already reachable from the
    # adapter-supplied target BASE can prove that the receipt survived a prior
    # boundary. A merge manufactured inside the candidate must not authorize
    # deleting the receipt before that candidate's own merge. No-range local
    # hooks use the deletion parent as a best-effort usability check; the
    # controlled range adapter rechecks the stronger target-history claim.
    receipt_history = (
        CHANGE_RANGE.split("...", 1)[0]
        if CHANGE_RANGE is not None
        else prior_revision
    )
    merges = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list", "--topo-order",
            "--merges", receipt_history,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if merges.returncode:
        raise GitSnapshotError(
            merges.stderr.strip() or "could not inspect merge-boundary receipts"
        )
    receipt_paths_at = {}
    for commit, receipt_path, receipt_text in queue_lineage_revision_snapshots(
        path, text, prior_revision
    ):
        if receipt_text == text:
            receipt_paths_at.setdefault(commit, set()).add(receipt_path)
    for merge in merges.stdout.splitlines():
        parents = revision_parents(merge, "merge-boundary receipt")
        if len(parents) != 2 or parents[0] != reviewed_base:
            continue
        feature_parent = parents[1]
        if not git_is_ancestor(reviewed_head, feature_parent):
            continue
        if not receipt_paths_at.get(merge):
            continue
        same_tree = subprocess.run(
            [
                "git", "--no-replace-objects", "diff", "--quiet",
                merge, feature_parent, "--",
            ],
            cwd=REPO,
            stderr=subprocess.PIPE,
            check=False,
        )
        if same_tree.returncode not in (0, 1):
            raise GitSnapshotError(
                same_tree.stderr.decode("utf-8", errors="replace").strip()
                or "could not verify merge-boundary receipt tree"
            )
        if same_tree.returncode:
            continue
        tail = changed_paths_between_revisions(reviewed_head, feature_parent)
        if any(not valid_queue_item_path(candidate) for candidate in tail):
            continue
        return None
    return (
        "review must remain live until the previously admitted target "
        "history contains an exact two-parent merge carrying its approved receipt"
    )


def negative_review_cancellation_problem(
    path, text, prior_revision, revision, boundary_tokens=()
):
    """Require a rejected artifact or task pursuit to be mechanically withdrawn."""
    evidence_problem = resolution_evidence_problem(
        text, prior_revision, revision
    )
    if evidence_problem:
        return evidence_problem
    got = text_fields(text)
    target = review_target(got.get("Review target", ""))
    evidence = set(resolution_evidence_paths(text))
    if target is not None and target[0] == "local" \
            and target[1] in evidence:
        return "review target and cancellation evidence must be distinct files"

    transitions = boundary_transitions(boundary_tokens)
    task_transitions = transitions.intersection(TASK_LIFECYCLE_TRANSITIONS)
    task_ids = boundary_task_ids(boundary_tokens)
    if task_transitions and not task_ids:
        task_ids = task_ids_linking_queue_at(prior_revision, path)
    candidates = deletion_and_later_candidates(revision)
    if task_ids:
        remaining = sorted(
            (task_id, candidate)
            for task_id in task_ids
            for candidate in candidates
            if task_status_in_candidate(candidate, task_id) is not None
        )
        if remaining:
            return (
                "rejected task pursuit remains live for: "
                + ", ".join(
                    task_id + "@"
                    + ("index" if candidate is None else candidate)
                    for task_id, candidate in remaining
                )
            )
        return None
    if task_transitions:
        return "task cancellation needs an associated task:<id>"

    if target is not None and target[0] == "git":
        for candidate in candidates:
            problem = reviewed_range_withdrawal_problem(text, candidate)
            if problem:
                return problem
        return None
    if target is None or target[0] != "local":
        return (
            "negative review cleanup needs a local target that can be "
            "withdrawn, or a candidate-range Git review"
        )
    expected = got.get("Review revision", "").strip()
    for candidate in candidates:
        artifact = candidate_artifact_bytes(target[1], candidate)
        if artifact is not None \
                and expected == "sha256:" + hashlib.sha256(artifact).hexdigest():
            return "rejected local review target remains unchanged and active"
    return None


def review_cleanup_boundary_problem(
    path, text, prior_revision, revision, boundary_text, timing
):
    """Require cancellation or a durable receipt before a review disappears."""
    got = text_fields(text)
    outcome = got.get("Review outcome", "").strip()
    if outcome in {"rejected", "abandoned"}:
        problem = negative_review_cancellation_problem(
            path, text, prior_revision, revision, (
                future_boundary_tokens(
                    text_fields(boundary_text).get("Blocks at", "")
                )
                if timing == "future-blocking"
                else blocking_boundary_tokens(
                    text_fields(boundary_text).get("Blocks now", "")
                )
            )
        )
        return (
            "negative review needs durable cancellation evidence: " + problem
            if problem else None
        )
    if outcome != "approved":
        return "review has no terminal outcome that can close its boundary"

    boundary = text_fields(boundary_text)
    tokens = (
        future_boundary_tokens(boundary.get("Blocks at", ""))
        if timing == "future-blocking"
        else blocking_boundary_tokens(boundary.get("Blocks now", ""))
    )
    transitions = boundary_transitions(tokens)
    if "merge" in transitions:
        target = review_target(got.get("Review target", ""))
        if target is None or target[0] != "git":
            return "merge cleanup needs a candidate-range Git review receipt"
        return approved_review_merge_receipt_problem(
            path, text, prior_revision, tokens
        )
    if transitions.intersection(TASK_LIFECYCLE_TRANSITIONS):
        target = review_target(got.get("Review target", ""))
        if target is None or target[0] != "local":
            return "task-boundary cleanup needs a stable local review target"
        return task_transition_receipt_problem(
            path, text, prior_revision, revision, tokens
        )
    if boundary_task_ids(tokens):
        return resolution_evidence_problem(
            text, prior_revision, revision
        )
    if timing == "future-blocking":
        first = tokens[0] if tokens else ""
        date_boundary = parse_date(first)
        if date_boundary is not None and date_boundary > TODAY:
            return "future review cannot close before its recorded date boundary"
        return resolution_evidence_problem(
            text, prior_revision, revision
        )
    if transitions or any(
        OPERATION_BOUNDARY_RE.fullmatch(token) for token in tokens
    ):
        problem = resolution_evidence_problem(
            text, prior_revision, revision
        )
        return (
            "blocking review needs durable boundary evidence: " + problem
            if problem else None
        )
    return None


def review_successor_problem(path, text, prior_revision, revision):
    got = text_fields(text)
    candidates = context_path_candidates(got.get("Successor action", ""))
    if len(candidates) != 1:
        return "changes-requested review needs exactly one **Successor action:**"
    successor_path = candidates[0]
    successor_parts = Path(successor_path).parts
    if successor_path == path or not valid_queue_item_path(successor_path) \
            or successor_parts[1] != "needs-agent":
        return "review successor is not a distinct canonical needs-agent action"
    successor_bytes = candidate_artifact_bytes(successor_path, revision)
    if successor_bytes is None:
        return "review successor is not live in the deletion candidate"
    if git_artifact_bytes_at(prior_revision, successor_path) is not None:
        return "review successor was not introduced by the resolution edge"
    successor_text = decode_utf8_artifact(
        successor_bytes, f"`{successor_path}` in the deletion candidate"
    )
    successor = text_fields(successor_text)
    if path not in context_path_candidates(successor.get("Supersedes", "")):
        return "review successor does not point back with **Supersedes:**"
    if successor.get("Status", "").strip() != "open":
        return "review successor is not an open needs-agent action"
    if not has_concrete_value(successor.get("Action", "")):
        return "review successor has no concrete **Action:**"
    if not resolution_evidence_paths(successor_text):
        return "review successor has no non-queue **Resolution evidence:**"
    if delivery_class(Path(successor_path).name) != delivery_class(Path(path).name):
        return "review successor changes the dependency timing"
    timing = delivery_class(Path(path).name)
    for key in QUEUE_TIMING_FIELDS.get(timing, ()):
        if successor.get(key, "").strip() != got.get(key, "").strip():
            return f"review successor changes **{key}:**"
    if successor.get("Full context", "").strip() != got.get(
        "Full context", ""
    ).strip():
        return "review successor changes the stable **Full context:** lineage"
    followup_value = successor.get("Follow-up review", "")
    if not has_concrete_value(followup_value):
        return (
            "review successor must preserve the review boundary with one "
            "**Follow-up review:**"
        )
    followups = context_path_candidates(followup_value)
    if len(followups) != 1:
        return "review successor needs exactly one canonical **Follow-up review:**"
    followup_path = followups[0]
    followup_parts = Path(followup_path).parts
    if followup_path in {path, successor_path} \
            or not valid_queue_item_path(followup_path) \
            or followup_parts[1:3] != ("needs-human", "reviews"):
        return "follow-up review is not a distinct canonical human review action"
    followup_bytes = candidate_artifact_bytes(followup_path, revision)
    if followup_bytes is None:
        return "follow-up review is not live in the deletion candidate"
    if git_artifact_bytes_at(prior_revision, followup_path) is not None:
        return "follow-up review was not introduced by the resolution edge"
    followup = text_fields(decode_utf8_artifact(
        followup_bytes, f"`{followup_path}` in the deletion candidate"
    ))
    if followup.get("Status", "").strip() != "awaiting-artifact":
        return "follow-up review is not awaiting its repaired artifact"
    if not has_concrete_value(followup.get("Action", "")):
        return "follow-up review has no concrete **Action:**"
    if followup.get("Action", "").strip() == successor.get(
        "Action", ""
    ).strip():
        return "follow-up review duplicates the needs-agent repair action"
    if path not in context_path_candidates(followup.get("Supersedes", "")):
        return "follow-up review does not point back with **Supersedes:**"
    dependencies = context_path_candidates(followup.get("Depends on", ""))
    if dependencies != [successor_path]:
        return "follow-up review does not name the repair with **Depends on:**"
    if delivery_class(Path(followup_path).name) != timing:
        return "follow-up review changes the dependency timing"
    for key in QUEUE_TIMING_FIELDS.get(timing, ()):
        if followup.get(key, "").strip() != got.get(key, "").strip():
            return f"follow-up review changes **{key}:**"
    if followup.get("Full context", "").strip() != got.get(
        "Full context", ""
    ).strip():
        return "follow-up review changes the stable **Full context:** lineage"
    if followup.get("Review target", "").strip() != "pending" \
            or followup.get("Review revision", "").strip() != "pending" \
            or not unanswered_review(followup):
        return "follow-up review must await an unbound repaired artifact"
    return None


def queue_deletion_problem(path, text, prior_revision, revision):
    got = text_fields(text)
    parts = Path(path).parts
    actor = parts[1] if len(parts) > 1 else ""
    leaf = parts[2] if len(parts) > 2 else ""
    status = got.get("Status", "").strip()
    if actor not in {"needs-human", "needs-agent"}:
        return (
            "malformed queue actor cannot establish resolution authority; "
            "normalize the live item to a canonical actor path first"
        )
    if actor == "needs-human":
        response_keys = (
            ("Your review",)
            if leaf == "reviews"
            else ("Your answer", "Your review")
        )
        response = next(
            (got.get(key, "") for key in response_keys if key in got),
            "",
        )
        if status != "folding" or not has_concrete_value(response):
            return (
                "human action was not committed as folding with a concrete response"
            )
        if leaf == "reviews":
            # The response disposition is write-once evidence, not pending delivery
            # state. Older live reviews may omit it until a response is recorded.
            outcome = got.get("Review outcome", "pending").strip()
            if outcome not in REVIEW_OUTCOMES:
                return "review has no terminal **Review outcome:**"
        lifecycle = claimed_lifecycle_problem(
            path, text, prior_revision, actor, leaf
        )
        if lifecycle:
            return lifecycle
        if leaf == "reviews":
            outcome = got.get("Review outcome", "").strip()
            target_problem = (
                review_binding_problem(text)
                if outcome in {"rejected", "abandoned"}
                else review_candidate_problem(text, revision)
            )
            if target_problem:
                return target_problem
            if outcome in REVIEW_SUCCESSOR_OUTCOMES:
                return review_successor_problem(
                    path, text, prior_revision, revision
                )
            if outcome in REVIEW_TERMINAL_OUTCOMES \
                    and context_path_candidates(
                        got.get("Successor action", "")
                    ):
                return (
                    f"{outcome} review is terminal and must not declare "
                    "**Successor action:**"
                )
            historical_future = historical_queue_timing(
                path, text, prior_revision, "future-blocking"
            )
            if historical_future is not None \
                    and outcome in REVIEW_TERMINAL_OUTCOMES:
                boundary_problem = review_cleanup_boundary_problem(
                    path,
                    text,
                    prior_revision,
                    revision,
                    historical_future[1],
                    "future-blocking",
                )
                if boundary_problem:
                    return boundary_problem
            elif delivery_class(Path(path).name) == "blocking" \
                    and outcome in REVIEW_TERMINAL_OUTCOMES:
                boundary_problem = review_cleanup_boundary_problem(
                    path,
                    text,
                    prior_revision,
                    revision,
                    text,
                    "blocking",
                )
                if boundary_problem:
                    return boundary_problem
            elif outcome in {"rejected", "abandoned"}:
                cancellation_problem = negative_review_cancellation_problem(
                    path, text, prior_revision, revision
                )
                if cancellation_problem:
                    return (
                        "negative review needs durable cancellation evidence: "
                        + cancellation_problem
                    )
            return None
        return resolution_evidence_problem(text, prior_revision, revision)
    item = REPO / path
    if actor == "needs-agent" and leaf == "retries" \
            and reconciler_owned_retry(item, text):
        check = got.get("Check", "").strip()
        if generated_retry_clear(text, revision):
            return None
        if check in CHECKS and check != "queue-resolution":
            return "generated retry identity is not cleared in the deletion candidate"
    if actor == "needs-agent" and leaf == "requests" \
            and got.get("Request kind", "").strip() == "task-pickup":
        return (
            None
            if pickup_completed(path, text, prior_revision, revision)
            else "task pickup was not atomically claimed and moved"
        )
    if status != "in-repair":
        return "agent action was not committed as in-repair before deletion"
    lifecycle = claimed_lifecycle_problem(
        path, text, prior_revision, actor, leaf
    )
    return lifecycle or resolution_evidence_problem(
        text, prior_revision, revision
    )


def check_queue_resolution():
    if not (REPO / ".git").exists():
        return
    queue_present = bool(git_index_entries("message-queue"))
    activations = queue_resolution_activation_commits(_GIT_HEAD_OID)
    enabled = queue_resolution_enabled()
    continuity_edge = displaced_tip_edge()
    displaced_activations = (
        queue_resolution_activation_commits(continuity_edge[0])
        if continuity_edge is not None
        else ()
    )
    if not activations and not enabled and not displaced_activations:
        return
    if (activations or displaced_activations) \
            and queue_present and not enabled:
        yield Finding(
            "queue-resolution",
            Path("message-queue/AGENTS.md"),
            "queue-resolution v1 was removed after activation",
            "restore **Queue resolution schema:** v1 before changing queue state",
        )
    if not activations and enabled and _GIT_HEAD_OID:
        activations = (_GIT_HEAD_OID,)
    reported = set()
    mutation_event_groups = []
    deletion_event_groups = []
    if activations:
        mutation_event_groups.append(queue_mutation_events(activations))
        deletion_event_groups.append((
            queue_deletion_events(activations),
            False,
        ))
    if continuity_edge is not None and (
        activations or displaced_activations
    ):
        parent, revision = continuity_edge
        mutation_event_groups.append(
            committed_queue_mutation_events(parent, revision)
        )
        deletion_event_groups.append((
            committed_queue_deletion_events(parent, revision),
            True,
        ))
    for events in mutation_event_groups:
        for (
            source,
            destination,
            before,
            after,
            prior_revision,
            revision,
        ) in events:
            problem = queue_mutation_problem(
                source,
                destination,
                before,
                after,
                prior_revision,
                revision,
            )
            if not problem:
                continue
            identity = (source, destination, problem)
            if identity in reported:
                continue
            reported.add(identity)
            yield Finding(
                "queue-resolution",
                Path(destination),
                f"live queue action was rewritten: {problem}",
                "preserve the action and response identity; file a distinct "
                "successor action when the requested work changes",
            )
    for events, is_continuity_edge in deletion_event_groups:
        for path, text, prior_revision, revision in events:
            problem = (
                "divergent update discarded a live old-tip action"
                if is_continuity_edge
                else queue_deletion_problem(
                    path, text, prior_revision, revision
                )
            )
            if problem:
                identity = (path, problem)
                if identity in reported:
                    continue
                reported.add(identity)
                yield Finding(
                    "queue-resolution",
                    Path(path),
                    f"deleted unresolved queue item: {problem}",
                    "commit the required claim/response evidence before deleting it",
                )


# ---------------------------------------------------------------- checks

def check_queue_name():
    for item in live_queue_items() or ():
        if not QUEUE_ITEM_RE.fullmatch(item.name):
            yield Finding(
                "queue-name",
                item.relative_to(REPO),
                "live queue filename does not declare dependency timing",
                "rename it to blocking-*, future-blocking-*, or non-blocking-*",
            )


def check_queue_location():
    for item in live_queue_items() or ():
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] not in ("needs-human", "needs-agent") \
                or not SLUG_RE.fullmatch(parts[1]):
            yield Finding(
                "queue-location",
                item.relative_to(REPO),
                "live queue item must be under one actor folder and one typed leaf",
                "move it to message-queue/{needs-human|needs-agent}/<kind>/",
            )
        if not readable_queue_item(item):
            yield Finding(
                "queue-location",
                item.relative_to(REPO),
                "live queue state must be a regular file, not a symlink",
                "replace the symlink with a repository-local regular Markdown file",
            )


def check_queue_schema():
    queue_v1 = queue_resolution_enabled()
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        timing = delivery_class(item.name)
        if timing is None:
            continue  # queue-name owns the malformed-name finding
        text = repo_text(item)
        got = text_fields(text)
        if "Blocking" in got:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "obsolete **Blocking:** field conflicts with filename timing",
                "remove it and use only the field required by the filename prefix",
            )
        expected = set(QUEUE_TIMING_FIELDS[timing])
        present = expected.intersection(got)
        for key in sorted(expected - present):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                f"missing required field **{key}:** for {timing}-*",
                "copy the matching delivery-class header from templates/queue/",
            )
        for key in sorted(expected):
            if key in got and not has_concrete_value(got[key]):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    f"field **{key}:** is empty or a placeholder",
                    "state the concrete blocked boundary or unattended outcome",
                )
        if timing == "blocking" and "Blocks now" in got \
                and has_concrete_value(got["Blocks now"]) \
                and not blocking_boundary_tokens(got["Blocks now"]):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Blocks now:** must be exactly one task:, transition:, or operation: token",
                "remove prose and name the single blocked boundary",
            )
        if timing == "future-blocking" and "Blocks at" in got \
                and has_concrete_value(got["Blocks at"]) \
                and not valid_future_boundary(got["Blocks at"]):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Blocks at:** must be an exact date, event:, or transition: token"
                " with optional task: tokens",
                "remove prose and name a machine-readable future boundary",
            )
        if timing == "future-blocking" and "Blocks at" in got:
            tokens = future_boundary_tokens(got["Blocks at"])
            internal = boundary_transitions(tokens).intersection(
                TASK_LIFECYCLE_TRANSITIONS
            )
            if internal and not boundary_task_ids(tokens):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "task lifecycle transition requires at least one task:<id> token: "
                    + ",".join(sorted(internal)),
                    "append every affected task:<id> after the transition token",
                )
        unexpected = set(QUEUE_TIMING_FIELDS["blocking"])
        unexpected.update(QUEUE_TIMING_FIELDS["future-blocking"])
        unexpected.update(QUEUE_TIMING_FIELDS["non-blocking"])
        unexpected -= expected
        for key in sorted(unexpected.intersection(got)):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                f"field **{key}:** contradicts the {timing}-* filename",
                "rename the item or keep only the timing fields for its prefix",
            )

    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] not in ("needs-human", "needs-agent"):
            continue
        actor, leaf = parts
        rel = "/".join(parts)
        required = QUEUE_SCHEMAS.get(rel)
        if required is None:
            required = ["Status", "Filed", "Action", "Full context"]
        else:
            required = list(required)
        if actor == "needs-human" and queue_v1:
            required.extend(HUMAN_PROJECTION_FIELDS)
        text = repo_text(item)
        clean = semantic_text(text)
        got = text_fields(text)
        status = got.get("Status", "").strip()
        allowed_statuses = (
            {"awaiting-artifact", "waiting", "folding"}
            if actor == "needs-human" and leaf == "reviews"
            else {"waiting", "folding"}
            if actor == "needs-human"
            else {"open", "in-repair"}
        )
        if "Status" in got and status not in allowed_statuses:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                f"**Status:** must be one of: {', '.join(sorted(allowed_statuses))}",
                "use the actor lifecycle defined by the matching queue template",
            )
        for key, count in sorted(field_counts(text).items()):
            if count > 1:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    f"field **{key}:** appears more than once",
                    "keep one unambiguous structured field",
                )
        for key in required:
            if key not in got:
                yield Finding("queue-schema", item.relative_to(REPO),
                              f"missing required field **{key}:**",
                              f"copy the base schema from templates/queue/ ({rel})")
        if actor == "needs-human" and queue_v1:
            for key in HUMAN_PROJECTION_FIELDS:
                if key in got and not has_concrete_value(got[key]):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        f"field **{key}:** is empty or a placeholder",
                        "state the concrete consequence copied into handover "
                        "action projections",
                    )
        if "Filed" in got and parse_leading_date(got["Filed"]) is None:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Filed:** does not contain a valid YYYY-MM-DD date",
                "record a real calendar date",
            )
        if "Action" in got and not has_concrete_value(got["Action"]):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Action:** is empty or a placeholder",
                "state the next actor's concrete action",
            )
        context_targets = context_files(got.get("Full context", ""))
        is_pickup = (
            actor == "needs-agent"
            and leaf == "requests"
            and got.get("Request kind", "").strip() == "task-pickup"
        )
        moving_task_paths = task_status_references(text)
        is_repair_record = actor == "needs-agent" and leaf == "retries"
        is_generated_retry = is_repair_record and (
            reconciler_owned_retry(item, text)
            or legacy_reconciler_retry(item, text)
        )
        if is_repair_record and not is_generated_retry:
            structured_notes = sorted({
                key
                for notes in AGENT_NOTES_SECTION_RE.findall(clean)
                for key, _value in FIELD_RE.findall(notes)
            })
            if structured_notes:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "manual retry Agent notes contain structured queue fields: "
                    + ", ".join(structured_notes),
                    "keep bold-key queue fields in the item header; Agent notes "
                    "may contain only unstructured diagnostic prose",
                )
        needs_resolution_evidence = (
            actor == "needs-human"
        ) or (
            actor == "needs-agent" and not (is_pickup or is_generated_retry)
        )
        if needs_resolution_evidence and not resolution_evidence_paths(text):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "ordinary action needs non-queue **Resolution evidence:** file path(s)",
                "name the durable file(s) that completion will create or change",
            )
        if actor == "needs-human" and leaf == "reviews":
            target = review_target(got.get("Review target", ""))
            evidence_paths = set(resolution_evidence_paths(text))
            if target is not None and target[0] == "local" \
                    and target[1] in evidence_paths:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "review target and Resolution evidence are the same file",
                    "predeclare a distinct cancellation record so a negative "
                    "outcome can withdraw the target without rewriting its evidence",
                )
            boundary_tokens = (
                future_boundary_tokens(got.get("Blocks at", ""))
                if timing == "future-blocking"
                else blocking_boundary_tokens(got.get("Blocks now", ""))
                if timing == "blocking"
                else []
            )
            transitions = boundary_transitions(boundary_tokens)
            review_revision = got.get("Review revision", "").strip()
            is_git_range = bool(
                review_revision.startswith("git:")
                and "..." in review_revision
            )
            if "merge" in transitions \
                    and review_revision != "pending" \
                    and has_concrete_value(review_revision) \
                    and (
                        target is None
                        or target[0] != "git"
                        or not is_git_range
                    ):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "merge-bound review must bind the candidate Git range",
                    "publish Review target/revision as git:<base>...<head>",
                )
            if transitions.intersection(TASK_LIFECYCLE_TRANSITIONS) \
                    and review_revision != "pending" \
                    and has_concrete_value(review_revision) \
                    and (target is None or target[0] != "local"):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "task-lifecycle review must bind a stable local artifact",
                    "review the task's design or verification file; reserve "
                    "candidate-range reviews for merge admission",
                )
        if moving_task_paths and not (is_pickup or is_repair_record):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "queue item uses status-dependent task path(s) outside task-pickup: "
                + ", ".join(moving_task_paths),
                "link stable evidence and refer to concrete tasks by id only",
            )
        if actor == "needs-agent" and leaf != "retries" \
                and "Full context" in got \
                and not context_targets:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Full context:** does not point to an existing repo-relative file",
                "link at least one durable source with a backticked path or markdown link",
            )
        if actor != "needs-human":
            continue
        if leaf == "reviews":
            response_options = ("Your review",)
        elif leaf in ("decisions", "clarifications"):
            response_options = ("Your answer",)
        else:
            response_options = ("Your answer", "Your review")
        if not any(response in got for response in response_options):
            label = " or ".join(f"**{response}:**" for response in response_options)
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                f"missing the literal {label} line",
                f"append `{response_options[0]}: ______` in bold-key form",
            )
        if "Full context" in got and not context_targets:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "**Full context:** does not point to an existing repo-relative file",
                "link at least one durable source with a backticked path or markdown link",
            )
        if leaf == "reviews" and "Review target" in got:
            status = got.get("Status", "").strip()
            target = got["Review target"].strip()
            revision = got.get("Review revision", "").strip()
            reviewed_revision = got.get("Reviewed revision", "").strip()
            # Pending delivery predates this response-classification field. Treat
            # omission as pending; a concrete response still requires a terminal value.
            outcome = got.get("Review outcome", "pending").strip()
            parsed_target = review_target(target)
            local_candidates = (
                [parsed_target[1]]
                if parsed_target and parsed_target[0] == "local"
                else []
            )
            local_targets = context_files(target) if local_candidates else []
            https_target = (
                parsed_target[1]
                if parsed_target and parsed_target[0] == "https"
                else None
            )
            git_target = (
                parsed_target[1]
                if parsed_target and parsed_target[0] == "git"
                else None
            )
            target_available = bool(
                https_target or git_target or len(local_targets) == 1
            )
            response = got.get("Your review", "").strip()
            if status == "awaiting-artifact":
                if target.lower() != "pending":
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "awaiting-artifact review must use **Review target:** pending",
                        "set status to waiting when a concrete target is linked",
                    )
                if revision.lower() != "pending":
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "awaiting-artifact review must use **Review revision:** pending",
                        "bind the review only after the exact artifact exists",
                    )
                if has_concrete_value(response) \
                        or has_concrete_value(reviewed_revision):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "review response and binding cannot exist before the artifact",
                        "leave Your review and Reviewed revision blank until status is waiting",
                    )
                if outcome != "pending":
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "awaiting-artifact review must have **Review outcome:** pending",
                        "leave the outcome pending until the bound response exists",
                    )
            else:
                if not target_available:
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "**Review target:** must identify exactly one file, Git range, or HTTPS artifact",
                        "name one repo file, Git commit/range, or HTTPS artifact",
                    )
                if not REVIEW_REVISION_RE.fullmatch(revision):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "**Review revision:** is not an immutable sha256 or Git revision",
                        "use sha256:<64 hex>, git:<full id>, or git:<base>...<head>",
                    )
                elif revision.startswith("git:"):
                    problems = git_review_revision_problems(revision)
                    if problems:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "**Review revision:** is not a reviewable Git artifact: "
                            + "; ".join(problems),
                            "use available literal commit ids with a shared history",
                        )
                if git_target and revision != git_target:
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "Git **Review target:** and **Review revision:** do not match",
                        "use the same literal git:<commit> or git:<base>...<head>",
                    )
                if https_target and REVIEW_REVISION_RE.fullmatch(revision) \
                        and not revision.startswith("sha256:"):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "HTTPS **Review target:** needs a sha256 revision",
                        "bind the external artifact to sha256:<64 hex>",
                    )
                if len(local_candidates) == 1 \
                        and len(local_targets) == 1 \
                        and not https_target:
                    if local_targets[0] == item:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "a review cannot target its own mutable queue item",
                            "target the underlying artifact and keep delivery state here",
                        )
                    expected = "sha256:" + hashlib.sha256(
                        repo_artifact_bytes(local_targets[0])
                    ).hexdigest()
                    if revision != expected:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "local **Review revision:** does not match target bytes",
                            f"bind the review to `{expected}`",
                        )
                if has_concrete_value(response):
                    if reviewed_revision != revision:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "review response is not bound to the requested revision",
                            "copy Review revision into Reviewed revision with the response",
                        )
                    if outcome not in REVIEW_OUTCOMES:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "review response needs an explicit terminal "
                            "**Review outcome:**",
                            "use approved, changes-requested, rejected, or "
                            "abandoned (legacy not-approved means changes-requested)",
                        )
                    elif outcome in REVIEW_TERMINAL_OUTCOMES \
                            and context_path_candidates(
                                got.get("Successor action", "")
                            ):
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            f"**Review outcome:** {outcome} is terminal but "
                            "**Successor action:** is present",
                            "remove the successor or classify the response as "
                            "changes-requested",
                        )
                elif has_concrete_value(reviewed_revision):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "Reviewed revision exists without a concrete review response",
                        "clear the stale binding or record the corresponding response",
                    )
                elif outcome != "pending":
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "review without a response must keep **Review outcome:** pending",
                        "record a response and binding before setting a terminal outcome",
                    )
        summary = section_body(clean, "## What you need to know")
        if not has_concrete_value(summary):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "missing a concrete ## What you need to know section",
                "summarize the action from zero context before linking to depth",
            )
        differences = section_body(clean, "## Differences")
        if not has_concrete_value(differences):
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "missing a concrete ## Differences section",
                "briefly contrast the choices or interpretations being reviewed",
            )
        if leaf == "decisions":
            examples = [
                value for value in EXAMPLE_CONSEQUENCE_RE.findall(clean)
                if has_concrete_value(value)
            ]
            if len(OPTION_RE.findall(clean)) < 2:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "decision needs at least two `### Option ...` choices",
                    "show at least two materially different choices",
                )
            if len(examples) < 2:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "decision needs a concrete *Example consequence:* for each choice",
                    "include at least two non-placeholder example consequences",
                )
        else:
            example = section_body(clean, "## Example")
            if not has_concrete_value(example):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "missing a concrete ## Example section",
                    "show one small scenario that makes the requested judgment tangible",
                )


def check_stale_queue():
    if not QUEUE.is_dir():
        return
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        timing = delivery_class(item.name)
        if timing is None or timing == "non-blocking":
            continue
        got = fields(item)
        if timing == "future-blocking":
            boundary = parse_leading_date(got.get("Blocks at", ""))
            if boundary and boundary <= TODAY:
                yield Finding(
                    "stale-queue",
                    item.relative_to(REPO),
                    f"future blocking boundary {boundary} has passed",
                    "resolve it or rename it after recording the new dependency timing",
                )
            continue  # named event boundaries are not machine-inferable
        filed = parse_date(got.get("Filed", ""))
        if filed and (TODAY - filed).days > STALE_QUEUE_DAYS:
            yield Finding("stale-queue", item.relative_to(REPO),
                          f"filed {filed}, older than {STALE_QUEUE_DAYS} days",
                          "resolve or re-surface it; record a duplicate/moot disposition"
                          " before deletion")


def task_queue_paths(value):
    try:
        paths = parse_task_queue_action_value(value)
    except ValueError:
        return []
    return sorted(paths)


def queue_item_owned_by_task(path, task_id, revision=None):
    """Return whether one human queue item declares this task as its owner."""
    normalized = Path(path).as_posix()
    parts = Path(normalized).parts
    if len(parts) != 4 or parts[:2] != (
        "message-queue", "needs-human"
    ):
        return False
    artifact = (
        repo_artifact_bytes(REPO / normalized)
        if revision is None
        else git_artifact_bytes_at(revision, normalized)
    )
    if artifact is None:
        return False
    text = decode_utf8_artifact(
        artifact,
        (
            f"candidate `{normalized}`"
            if revision is None else f"`{normalized}` at {revision}"
        ),
    )
    got = text_fields(text)
    owned_boundaries = boundary_task_ids(
        blocking_boundary_tokens(got.get("Blocks now", ""))
    )
    owned_boundaries.update(boundary_task_ids(
        future_boundary_tokens(got.get("Blocks at", ""))
    ))
    if task_id in owned_boundaries:
        return True
    return bool(re.search(
        r"(?<![A-Za-z0-9_-])from[ \t]+task[ \t]+`"
        + re.escape(task_id)
        + r"`(?![A-Za-z0-9-])",
        got.get("Filed", ""),
        flags=re.I,
    ))


def queue_endpoint(path):
    try:
        return path.parent.relative_to(QUEUE).as_posix()
    except ValueError:
        return ""


def inferred_task_transitions(status):
    reached = set()
    if status in ("1_in-progress", "2_blocked", "3_in-review", "4_done"):
        reached.add("start")
    if status in ("3_in-review", "4_done"):
        reached.add("review")
    if status == "4_done":
        reached.add("complete")
    return reached


def live_task_directories():
    """Return task directories represented by the Git index or a no-Git tree."""
    directories = set()
    if (REPO / ".git").exists():
        for name in git_index_entries("tasks"):
            parts = Path(name).parts
            if len(parts) >= 4 and parts[0] == "tasks":
                directories.add(REPO.joinpath(*parts[:3]))
        return directories
    if not TASKS.is_dir():
        return directories
    for status in TASK_STATUSES:
        folder = TASKS / status
        if folder.is_dir():
            directories.update(
                item for item in folder.iterdir() if item.is_dir()
            )
    return directories


def indexed_task_topology():
    """Return invalid status folders and loose status files in the Git index."""
    invalid_statuses = set()
    loose_files = set()
    if not (REPO / ".git").exists():
        return invalid_statuses, loose_files
    for name in git_index_entries("tasks"):
        path = Path(name)
        parts = path.parts
        if len(parts) < 2 or parts[0] != "tasks":
            continue
        if len(parts) == 2 and parts[1] in ("AGENTS.md", "README.md", "CLAUDE.md"):
            continue
        if parts[1] not in TASK_STATUSES:
            invalid_statuses.add(Path(*parts[:2]))
        elif len(parts) == 3 \
                and parts[2] != "README.md" \
                and not parts[2].startswith("."):
            loose_files.add(path)
    return invalid_statuses, loose_files


def task_record_occurrences():
    records = {}
    for task in sorted(live_task_directories()):
        rel = task.relative_to(TASKS)
        if len(rel.parts) != 2:
            continue
        status = rel.parts[0]
        task_record = task / "task.md"
        if status in TASK_STATUSES and TASK_ID_RE.fullmatch(task.name) \
                and repo_artifact_bytes(task_record) is not None:
            records.setdefault(task.name, []).append(
                (status, task, fields(task_record))
            )
    return records


def task_records():
    return {
        task_id: occurrences[0]
        for task_id, occurrences in task_record_occurrences().items()
    }


def git_review_revision_problems(revision):
    object_ids = revision[len("git:"):].split("...")
    problems = []
    for object_id in object_ids:
        result = subprocess.run(
            ["git", "cat-file", "-t", object_id],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode:
            problems.append(f"{object_id} is unavailable")
        elif result.stdout.strip() != "commit":
            problems.append(
                f"{object_id} is {result.stdout.strip()}, not a commit"
            )
    if len(object_ids) == 2 and not problems:
        merge_base = subprocess.run(
            ["git", "merge-base", object_ids[0], object_ids[1]],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if merge_base.returncode:
            problems.append("base and head have no merge base")
    return problems


def task_status_references(text):
    return sorted(set(re.findall(
        r"tasks/(?:0_backlog|1_in-progress|2_blocked|3_in-review|4_done)/"
        r"\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*(?:/[A-Za-z0-9._/-]+)?",
        semantic_text(text),
    )))


def task_tokens(text):
    return set(re.findall(
        r"(?<![A-Za-z0-9_-])task:"
        r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)"
        r"(?![A-Za-z0-9-])",
        semantic_text(text),
    ))


def task_ids_from_change_range(change_range):
    """Infer task association from changed task records and commit messages."""
    if not change_range or not (REPO / ".git").exists():
        return set()
    if change_range.startswith("root:"):
        head = change_range[len("root:"):]
        changed_command = [
            "git", "ls-tree", "-r", "--name-only", head, "--", "tasks",
        ]
        log_range = head
    else:
        base, head = change_range.split("...", 1)
        changed_command = [
            "git", "diff", "--no-renames", "--name-only",
            change_range, "--", "tasks",
        ]
        log_range = f"{base}..{head}"
    changed = subprocess.run(
        changed_command,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    task_ids = set()
    if changed.returncode == 0:
        for name in changed.stdout.splitlines():
            parts = Path(name).parts
            if len(parts) >= 3 and parts[0] == "tasks" \
                    and parts[1] in TASK_STATUSES \
                    and TASK_ID_RE.fullmatch(parts[2]):
                task_ids.add(parts[2])
    messages = subprocess.run(
        ["git", "log", "--format=%B", log_range],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if messages.returncode == 0:
        task_ids.update(re.findall(
            r"(?<![A-Za-z0-9_-])task:\s*"
            r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)"
            r"(?![A-Za-z0-9-])",
            messages.stdout,
        ))
    return task_ids


def active_task_scope_matches(task_ids):
    if not task_ids or ACTIVE_TASK_ID is None:
        return True
    if isinstance(ACTIVE_TASK_ID, (set, frozenset)):
        return bool(task_ids.intersection(ACTIVE_TASK_ID))
    return bool(ACTIVE_TASK_ID) and ACTIVE_TASK_ID in task_ids


def committed_candidate_revision():
    """Return the commit whose bytes must already contain an active claim."""
    if _GIT_HEAD_OID:
        return _GIT_HEAD_OID
    if not (REPO / ".git").exists():
        return None
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if head.returncode:
        return None
    revision = head.stdout.strip()
    return revision if FULL_GIT_OID_RE.fullmatch(revision) else None


def active_blocking_repair_problem(item):
    """Explain why a blocker lacks a committed agent-owned repair claim."""
    rel = item.relative_to(REPO).as_posix()
    parts = Path(rel).parts
    if len(parts) != 4:
        return "queue path has no canonical actor and typed leaf"
    actor, leaf = parts[1:3]
    text = repo_text(item)
    got = text_fields(text)
    active_status = "folding" if actor == "needs-human" else "in-repair"
    if actor not in {"needs-human", "needs-agent"}:
        return "queue actor is malformed"
    if got.get("Status", "").strip() != active_status:
        return f"status is not {active_status}"
    if actor == "needs-human" \
            and first_concrete_response(human_response_fields(text)) is None:
        return "folding has no concrete committed human response"
    revision = committed_candidate_revision()
    if revision is None:
        return "active status is not present in a committed candidate"
    committed = git_artifact_bytes_at(revision, rel)
    candidate = repo_artifact_bytes(item)
    if committed is None or committed != candidate:
        return "active status is not yet committed"
    return claimed_lifecycle_problem(
        rel, text, revision, actor, leaf
    )


def check_active_queue_boundaries():
    if not ACTIVE_TRANSITIONS:
        return
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        timing = delivery_class(item.name)
        got = fields(item)
        if timing == "future-blocking":
            tokens = future_boundary_tokens(got.get("Blocks at", ""))
        elif timing == "blocking":
            tokens = blocking_boundary_tokens(got.get("Blocks now", ""))
        else:
            continue
        task_ids = boundary_task_ids(tokens)
        if not active_task_scope_matches(task_ids):
            continue
        reached = boundary_transitions(tokens).intersection(ACTIVE_TRANSITIONS)
        if timing == "blocking" and task_ids:
            # `blocking-*` means the named task cannot advance at all. Unlike a
            # future blocker, it does not need to restate each external transition.
            reached.update(ACTIVE_TRANSITIONS)
        if reached:
            if timing == "future-blocking":
                boundary_problem = review_boundary_problem(item, reached)
                if boundary_problem is None:
                    continue
            else:
                boundary_problem = None
            yield Finding(
                "queue-boundary",
                item.relative_to(REPO),
                f"unresolved {timing} action reached transition:"
                + ",".join(sorted(reached))
                + (
                    f": {boundary_problem}"
                    if boundary_problem is not None else ""
                ),
                "resolve the action with fresh boundary evidence or reclassify "
                "its timing before crossing the boundary",
            )


def check_queue_task_reciprocity():
    records = task_records()
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        text = repo_text(item)
        got = fields(item)
        timing = delivery_class(item.name)
        if timing == "blocking":
            task_ids = blocking_task_ids(got.get("Blocks now", ""))
        elif timing == "future-blocking":
            task_ids = boundary_task_ids(
                future_boundary_tokens(got.get("Blocks at", ""))
            )
        else:
            task_ids = set()
        if queue_endpoint(item) != "needs-agent/retries":
            task_ids.update(task_tokens(text))

        context_task_ids = set()
        context_targets = []
        is_pickup = got.get("Request kind", "").strip() == "task-pickup"
        if queue_endpoint(item) == "needs-agent/requests" and is_pickup:
            context_targets = context_files(got.get("Full context", ""))
            for target in context_targets:
                try:
                    rel = target.relative_to(TASKS)
                except ValueError:
                    continue
                if len(rel.parts) == 3 and rel.parts[2] == "task.md" \
                        and rel.parts[0] in TASK_STATUSES \
                        and TASK_ID_RE.fullmatch(rel.parts[1]):
                    context_task_ids.add(rel.parts[1])
        task_ids.update(context_task_ids)
        if is_pickup:
            if timing != "non-blocking":
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    "task-pickup request must use non-blocking timing",
                    "rename it non-blocking-* and state the safe backlog outcome",
                )
            if len(context_targets) != 1 or len(context_task_ids) != 1:
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    "task-pickup Full context must be exactly one task.md",
                    "link only the current backlog task.md",
                )

        queue_path = item.relative_to(REPO).as_posix()
        for task_id in sorted(task_ids):
            record = records.get(task_id)
            if record is None:
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    f"queue item names missing task:{task_id}",
                    "fix the task token/context or restore the task record",
                )
                continue
            status, task, task_fields = record
            if queue_path not in task_queue_paths(
                task_fields.get("Queue actions", "")
            ):
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    f"task:{task_id} does not link this live queue action",
                    f"add `{queue_path}` to that task's Queue actions",
                )
            if is_pickup and status != "0_backlog":
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    f"task:{task_id} left backlog but its pickup request remains live",
                    "delete the completed pickup request and remove its task backlink",
                )
            if timing == "blocking" and task_id in blocking_task_ids(
                got.get("Blocks now", "")
            ) and status != "2_blocked":
                active_problem = (
                    active_blocking_repair_problem(item)
                    if status == "1_in-progress"
                    else None
                )
                if status == "1_in-progress" and active_problem is None:
                    continue
                if status == "1_in-progress":
                    yield Finding(
                        "queue-task-reciprocity",
                        item.relative_to(REPO),
                        f"blocking task:{task_id} may remain in 1_in-progress "
                        "only during a committed active repair/folding claim: "
                        + active_problem,
                        "move the stopped task to 2_blocked, or commit the "
                        "queue claim before returning it to 1_in-progress",
                    )
                    continue
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    f"blocking task:{task_id} is not in 2_blocked",
                    "move the stopped task to 2_blocked or reclassify the queue timing",
                )


def check_task_structure():
    task_directories = live_task_directories()
    if not task_directories and not TASKS.is_dir():
        return
    queue_enabled = bool(git_index_entries("message-queue")) \
        if (REPO / ".git").exists() else QUEUE.is_dir()
    for task_id, occurrences in task_record_occurrences().items():
        if len(occurrences) <= 1:
            continue
        locations = ", ".join(
            str(task.relative_to(REPO)) for _, task, _ in occurrences
        )
        yield Finding(
            "task-structure",
            TASKS.relative_to(REPO),
            f"task id {task_id} exists in multiple status folders: {locations}",
            "keep exactly one task folder; status is represented only by its parent",
        )
    reported_invalid = set()
    reported_loose = set()
    if TASKS.is_dir() and CHANGE_RANGE is None:
        for entry in sorted(TASKS.iterdir()):
            if entry.name in ("AGENTS.md", "README.md", "CLAUDE.md") \
                    or entry.name.startswith("."):
                continue
            if entry.name not in TASK_STATUSES:
                yield Finding(
                    "task-structure",
                    entry.relative_to(REPO),
                    "not a valid status folder",
                    f"one of: {', '.join(TASK_STATUSES)}",
                )
                reported_invalid.add(entry.relative_to(REPO))
                continue
            for item in sorted(entry.iterdir()):
                if item.name == "README.md" or item.name.startswith("."):
                    continue
                if not item.is_dir():
                    yield Finding(
                        "task-structure",
                        item.relative_to(REPO),
                        "loose file in a status folder",
                        "tasks are folders; move stray files into one",
                    )
                    reported_loose.add(item.relative_to(REPO))
    indexed_invalid, indexed_loose = indexed_task_topology()
    for rel in sorted(indexed_invalid - reported_invalid):
        yield Finding(
            "task-structure",
            rel,
            "not a valid status folder",
            f"one of: {', '.join(TASK_STATUSES)}",
        )
    for rel in sorted(indexed_loose - reported_loose):
        yield Finding(
            "task-structure",
            rel,
            "loose file in a status folder",
            "tasks are folders; move stray files into one",
        )
    for task in sorted(task_directories):
            rel = task.relative_to(REPO)
            entry_name = rel.parts[1]
            if entry_name not in TASK_STATUSES:
                continue  # the status-folder finding above owns this path
            if not TASK_ID_RE.fullmatch(task.name):
                yield Finding("task-structure", rel, "task id must be YYYY-MM-DD-kebab-slug",
                              "rename per handbook/naming-conventions.md")
            if repo_artifact_bytes(task / "task.md") is None:
                yield Finding("task-structure", rel, "missing task.md",
                              "copy templates/task/task.md")
                continue
            task_text = repo_text(task / "task.md")
            moving_references = task_status_references(task_text)
            if moving_references:
                yield Finding(
                    "task-structure",
                    rel / "task.md",
                    "task record uses moving status path(s): "
                    + ", ".join(moving_references),
                    "refer to concrete tasks by immutable task id only",
                )
            got = fields(task / "task.md")
            required = ["Claimed-by", "Filed", "Repository scope"]
            if queue_enabled:
                required.append("Queue actions")
            for key in required:
                if key not in got:
                    yield Finding("task-structure", rel / "task.md",
                                  f"missing required field **{key}:**",
                                  "copy the header from templates/task/task.md")
            scope = got.get("Repository scope", "")
            if scope and not REPOSITORY_SCOPE_RE.fullmatch(scope):
                yield Finding("task-structure", rel / "task.md",
                              f"invalid Repository scope {scope!r}",
                              "use core, records-only, or service:<name>")
            claimant = got.get("Claimed-by", "").strip()
            if entry_name == "0_backlog" and claimant != "unclaimed":
                yield Finding(
                    "task-structure",
                    rel / "task.md",
                    "backlog task must remain unclaimed",
                    "move the claimed task to 1_in-progress in its claim commit",
                )
            if entry_name != "0_backlog" and claimant == "unclaimed":
                yield Finding(
                    "task-structure",
                    rel / "task.md",
                    "active or completed task cannot be unclaimed",
                    "record the claimant before leaving backlog",
                )
            if queue_enabled or "Queue actions" in got:
                queue_value = got.get("Queue actions", "")
                queue_paths = []
                queue_is_none = False
                queue_field_count = field_counts(task_text).get(
                    "Queue actions", 0
                )
                if queue_field_count > 1:
                    yield Finding(
                        "task-structure",
                        rel / "task.md",
                        "task must contain exactly one **Queue actions:** field",
                        "keep one field containing exactly `none` or canonical "
                        "backticked queue paths",
                    )
                elif queue_field_count == 1:
                    try:
                        queue_paths = list(
                            task_queue_action_paths_from_text(task_text)
                        )
                        queue_is_none = not queue_paths
                    except ValueError as error:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "invalid **Queue actions:** projection: "
                            + str(error),
                            "use exactly `none` or canonical backticked queue "
                            "paths separated by `;` or `,`",
                        )
                live_queue_paths = []
                for queue_path in queue_paths:
                    target = REPO / queue_path
                    if repo_artifact_bytes(target) is None:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"Queue actions path `{queue_path}` is not in the Git index",
                            "stage the queue item or remove the stale task reference",
                        )
                        continue
                    if delivery_class(target.name) is None:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"Queue actions path `{queue_path}` lacks a valid delivery prefix",
                            "rename it to blocking-*, future-blocking-*, or non-blocking-*",
                        )
                        continue
                    if queue_endpoint(target).startswith("needs-human/") \
                            and not queue_item_owned_by_task(
                                queue_path, task.name
                            ):
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"human Queue actions path `{queue_path}` is not "
                            f"owned by task:{task.name}",
                            "name the task in a valid Blocks now/Blocks at "
                            "boundary or add exact Filed provenance `from task "
                            f"{task.name}`",
                        )
                    live_queue_paths.append(target)
                if entry_name == "0_backlog":
                    requests = [
                        target for target in live_queue_paths
                        if queue_endpoint(target) == "needs-agent/requests"
                        and delivery_class(target.name) == "non-blocking"
                        and fields(target).get("Request kind", "").strip()
                        == "task-pickup"
                        and len(context_files(
                            fields(target).get("Full context", "")
                        )) == 1
                        and (task / "task.md") in context_files(
                            fields(target).get("Full context", "")
                        )
                    ]
                    if not requests:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "unclaimed backlog work has no canonical needs-agent request",
                            "file a non-blocking pickup request and link it in Queue actions",
                        )
                reached = inferred_task_transitions(entry_name)
                for target in live_queue_paths:
                    timing = delivery_class(target.name)
                    if timing == "future-blocking":
                        tokens = future_boundary_tokens(
                            fields(target).get("Blocks at", "")
                        )
                    elif timing == "blocking":
                        tokens = blocking_boundary_tokens(
                            fields(target).get("Blocks now", "")
                        )
                    else:
                        continue
                    associated_tasks = boundary_task_ids(tokens)
                    if associated_tasks and task.name not in associated_tasks:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"future queue action `{target.relative_to(REPO)}`"
                            " names a different task boundary",
                            "fix the task: token or remove the unrelated Queue actions link",
                        )
                        continue
                    crossed = boundary_transitions(tokens).intersection(reached)
                    if crossed:
                        if timing in {"future-blocking", "blocking"}:
                            boundary_problem = review_boundary_problem(
                                target, crossed
                            )
                            if boundary_problem is None:
                                continue
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"task crossed unresolved {timing} boundary transition:"
                            + ",".join(sorted(crossed)),
                            "resolve or reclassify the queue action before moving task status",
                        )
                if entry_name == "4_done" and not queue_is_none:
                    receipt_actions = bool(live_queue_paths)
                    for target in live_queue_paths:
                        timing = delivery_class(target.name)
                        got = fields(target)
                        tokens = (
                            future_boundary_tokens(got.get("Blocks at", ""))
                            if timing == "future-blocking"
                            else blocking_boundary_tokens(
                                got.get("Blocks now", "")
                            )
                            if timing == "blocking"
                            else []
                        )
                        if "complete" not in boundary_transitions(tokens) \
                                or review_boundary_problem(
                                    target, {"complete"}
                                ) is not None:
                            receipt_actions = False
                            break
                    if len(live_queue_paths) != len(queue_paths):
                        receipt_actions = False
                    if not receipt_actions:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "done task must declare **Queue actions:** none",
                            "resolve or transfer pending actions; only an exact "
                            "approved completion receipt may survive its crossing commit",
                        )
                if entry_name == "2_blocked":
                    reciprocal = "task:" + task.name
                    blockers = [
                        target for target in live_queue_paths
                        if delivery_class(target.name) == "blocking"
                        and task.name in blocking_task_ids(
                            fields(target).get("Blocks now", "")
                        )
                    ]
                    if not blockers:
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "blocked task lacks a reciprocal live blocking-* queue action",
                            f"list a queue item whose **Blocks now:** contains `{reciprocal}`",
                        )
            if entry_name in ("1_in-progress", "2_blocked", "3_in-review", "4_done"):
                for needed in ("plan.md", "worklog.md"):
                    if repo_artifact_bytes(task / needed) is None:
                        yield Finding("task-structure", rel, f"missing {needed}",
                                      f"copy templates/task/{needed}")
            if entry_name in ("3_in-review", "4_done") \
                    and repo_artifact_bytes(task / "verification.md") is None:
                yield Finding("task-structure", rel, "missing verification.md",
                              "record real command output per templates/task/verification.md")
            if entry_name == "1_in-progress" and task.is_dir() \
                    and days_old(task) > STALE_TASK_DAYS:
                yield Finding("stale-task", rel,
                              f"untouched for over {STALE_TASK_DAYS} days",
                              "continue it, or move back to 0_backlog and unclaim")


def task_admission_enabled(revision=None):
    """Return whether one exact task tree enables edge-by-edge admission."""
    artifact = (
        repo_artifact_bytes(REPO / "tasks/AGENTS.md")
        if revision is None
        else git_artifact_bytes_at(revision, "tasks/AGENTS.md")
    )
    return bool(
        artifact is not None
        and text_fields(decode_utf8_artifact(
            artifact,
            (
                "candidate `tasks/AGENTS.md`"
                if revision is None else f"`tasks/AGENTS.md` at {revision}"
            ),
        )).get("Task admission schema", "").strip() == "v1"
    )


def task_admission_activation_commits(head):
    activations, error = schema_activation_commits(
        head,
        "tasks/AGENTS.md",
        "Task admission schema",
    )
    if error:
        raise GitSnapshotError(error)
    return activations


def git_empty_tree():
    result = subprocess.run(
        ["git", "hash-object", "-t", "tree", "--stdin"],
        cwd=REPO,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, "could not identify Git's empty tree"
        ))
    return result.stdout.decode("ascii").strip()


def task_admission_edges(activations):
    """Yield governed task edges, including a repository's root edge."""
    yielded = set()
    for edge in queue_revision_edges(activations):
        yielded.add(edge)
        yield edge
    if CHANGE_RANGE is None:
        if not _GIT_HEAD_OID and task_admission_enabled():
            yield git_empty_tree(), None
        return
    range_head = (
        CHANGE_RANGE[len("root:"):]
        if CHANGE_RANGE.startswith("root:")
        else CHANGE_RANGE.split("...", 1)[1]
    )
    roots = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--max-parents=0", range_head,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if roots.returncode:
        raise GitSnapshotError(
            roots.stderr.strip() or "could not inspect root task edges"
        )
    empty = git_empty_tree()
    for root in roots.stdout.splitlines():
        governed, error = governed_by_activation_join(root, activations)
        if error:
            raise GitSnapshotError(error)
        edge = (empty, root)
        if governed and edge not in yielded:
            yield edge


def governed_task_artifact_path(path):
    parts = Path(path).parts
    return bool(
        len(parts) >= 4
        and parts[0] == "tasks"
        and parts[1] in TASK_STATUSES
        and TASK_ID_RE.fullmatch(parts[2])
        and Path(path).suffix.casefold() in TASK_MARKDOWN_SUFFIXES
    )


def task_ids_changed_on_edge(parent, revision):
    """Return logical task ids touched on one exact Git/index edge."""
    command = (
        [
            "git", "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=ADMRT", parent, "--",
        ]
        if revision is None else
        [
            "git", "--no-replace-objects", "diff-tree",
            "-r", "--no-commit-id", "--name-status", "-z", "-M",
            "--diff-filter=ADMRT", parent, revision, "--",
        ]
    )
    changed = subprocess.run(
        command,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, "could not inspect task action-origin changes"
        ))
    task_ids = set()
    for _status, source, destination in name_status_records(changed.stdout):
        for candidate in (source, destination):
            if governed_task_artifact_path(candidate):
                task_ids.add(Path(candidate).parts[2])
    return task_ids


def task_snapshot(revision, task_id):
    """Return one task's queue ownership and all exact Markdown artifacts."""
    if revision is None:
        entries = git_index_entries("tasks")
        incarnations = sorted(
            path for path, mode in entries.items()
            if mode in ("100644", "100755")
            and re.fullmatch(
                rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
                + re.escape(task_id)
                + r"/task\.md",
                path,
            )
        )
    else:
        incarnations = task_incarnations_at(revision, task_id)
    if len(incarnations) != 1:
        return None
    task_path = Path(incarnations[0])
    task_bytes = (
        repo_artifact_bytes(REPO / task_path)
        if revision is None
        else git_artifact_bytes_at(revision, task_path.as_posix())
    )
    if task_bytes is None:
        return None
    task_text = decode_utf8_artifact(
        task_bytes,
        (
            f"candidate `{task_path}`"
            if revision is None else f"`{task_path}` at {revision}"
        ),
    )
    allowed = {
        path for path in task_queue_paths(
            text_fields(task_text).get("Queue actions", "")
        )
        if queue_item_owned_by_task(path, task_id, revision)
    }
    task_directory = task_path.parent
    prefix = task_directory.as_posix() + "/"
    if revision is None:
        artifact_paths = sorted(
            Path(path)
            for path, mode in git_index_entries(prefix).items()
            if mode in ("100644", "100755")
            and path.startswith(prefix)
            and Path(path).suffix.casefold() in TASK_MARKDOWN_SUFFIXES
        )
    else:
        tree = subprocess.run(
            [
                "git", "--no-replace-objects", "ls-tree", "-r",
                "--name-only", "-z", revision, "--", task_directory.as_posix(),
            ],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if tree.returncode:
            raise GitSnapshotError(git_failure(
                tree, f"could not inspect task artifacts for {task_id}"
            ))
        artifact_paths = sorted(
            Path(raw.decode("utf-8", errors="surrogateescape"))
            for raw in tree.stdout.split(b"\0")
            if raw and Path(
                raw.decode("utf-8", errors="surrogateescape")
            ).suffix.casefold() in TASK_MARKDOWN_SUFFIXES
        )
    artifacts = {}
    for path in artifact_paths:
        artifact = (
            repo_artifact_bytes(REPO / path)
            if revision is None
            else git_artifact_bytes_at(revision, path.as_posix())
        )
        if artifact is None:
            continue
        key = path.relative_to(task_directory).as_posix()
        artifacts[key] = (
            path.as_posix(),
            decode_utf8_artifact(
                artifact,
                (
                    f"candidate `{path}`"
                    if revision is None else f"`{path}` at {revision}"
                ),
            ),
        )
    return allowed, artifacts


def task_action_origin_problems(parent, revision):
    """Yield newly introduced unprojected human actions on one task edge."""
    for task_id in sorted(task_ids_changed_on_edge(parent, revision)):
        before = task_snapshot(parent, task_id)
        after = task_snapshot(revision, task_id)
        before_allowed, before_artifacts = before or (set(), {})
        after_allowed, after_artifacts = after or (set(), {})
        before_counts = {}
        after_counts = {}
        after_paths = {}
        for _filename, (before_path, before_text) in sorted(
            before_artifacts.items()
        ):
            for excerpt, count in task_action_unit_counts(
                before_text,
                before_path,
                before_allowed,
                repo=REPO,
                candidate_revision=parent,
            ).items():
                before_counts[excerpt] = (
                    before_counts.get(excerpt, 0) + count
                )
        for _filename, (after_path, after_text) in sorted(
            after_artifacts.items()
        ):
            for excerpt, count in task_action_unit_counts(
                after_text,
                after_path,
                after_allowed,
                repo=REPO,
                candidate_revision=revision,
            ).items():
                after_counts[excerpt] = after_counts.get(excerpt, 0) + count
                after_paths.setdefault(excerpt, after_path)
        for excerpt in sorted(after_counts):
            count = after_counts[excerpt] - before_counts.get(excerpt, 0)
            if count <= 0:
                continue
            yield (
                Path(after_paths[excerpt]),
                count,
                excerpt,
            )


def task_record_paths_at(revision):
    """Return canonical task records grouped by immutable task id."""
    paths = (
        [
            path for path, mode in git_index_entries("tasks").items()
            if mode in ("100644", "100755")
        ]
        if revision is None else task_incarnations_in_tree(revision)
    )
    records = {}
    for path in paths:
        matched = re.fullmatch(
            rf"tasks/({'|'.join(TASK_STATUSES)})/"
            r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)/task\.md",
            path,
        )
        if matched:
            records.setdefault(matched.group(2), []).append(
                (matched.group(1), path)
            )
    return records


def task_artifact_renames_on_edge(parent, revision):
    """Return detected task-local renames on one exact Git/index edge."""
    command = (
        [
            "git", "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=R", parent, "--", "tasks",
        ]
        if revision is None else
        [
            "git", "--no-replace-objects", "diff-tree",
            "-r", "--no-commit-id", "--name-status", "-z", "-M",
            "--diff-filter=R", parent, revision, "--", "tasks",
        ]
    )
    changed = subprocess.run(
        command,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if changed.returncode:
        raise GitSnapshotError(git_failure(
            changed, "could not inspect task artifact renames"
        ))
    return [
        (source, destination)
        for status, source, destination in name_status_records(changed.stdout)
        if status.startswith("R")
        and governed_task_artifact_path(source)
        and governed_task_artifact_path(destination)
    ]


def task_topology_problems(parent, revision, adopting=False):
    """Yield immutable-id and lifecycle violations on one task edge."""
    before = task_record_paths_at(parent)
    after = task_record_paths_at(revision)
    renamed_ids = set()
    for source, destination in task_artifact_renames_on_edge(
        parent, revision
    ):
        source_id = Path(source).parts[2]
        destination_id = Path(destination).parts[2]
        if source_id == destination_id:
            continue
        identity = (source_id, destination_id)
        if identity in renamed_ids:
            continue
        renamed_ids.add(identity)
        yield (
            Path(destination),
            f"task id changed from {source_id} to {destination_id}",
            "keep the original task id; create a separate backlog task if "
            "the work has a new identity",
        )

    for task_id in sorted(set(before) | set(after)):
        prior = before.get(task_id, [])
        current = after.get(task_id, [])
        if len(prior) > 1 or len(current) > 1:
            continue  # task-structure owns duplicate incarnations
        if not prior:
            if adopting or not current:
                continue
            status, path = current[0]
            if status != "0_backlog":
                yield (
                    Path(path),
                    f"new task:{task_id} was created directly in {status}",
                    "create new tasks in 0_backlog, then claim and move them "
                    "through the lifecycle",
                )
            continue
        prior_status, prior_path = prior[0]
        if not current:
            if prior_status not in TASK_DELETABLE_STATUSES:
                yield (
                    Path(prior_path),
                    f"active task:{task_id} was deleted from {prior_status}",
                    "restore the task; only backlog cancellation or done-task "
                    "pruning may delete a task record",
                )
            continue
        status, path = current[0]
        if status == prior_status:
            continue
        if status not in TASK_ALLOWED_STATUS_TRANSITIONS[prior_status]:
            allowed = ", ".join(sorted(
                TASK_ALLOWED_STATUS_TRANSITIONS[prior_status]
            )) or "no further status"
            yield (
                Path(path),
                f"task:{task_id} jumped from {prior_status} to {status}",
                f"use one declared lifecycle edge at a time; from "
                f"{prior_status} the allowed destination is {allowed}",
            )


def check_task_action_origin():
    """Require every newly introduced human task ask to be a queue projection."""
    if not (REPO / ".git").exists():
        return
    activations = task_admission_activation_commits(_GIT_HEAD_OID)
    enabled = task_admission_enabled()
    if not activations and not enabled:
        return
    edges = (
        ((_GIT_HEAD_OID, None),)
        if enabled and not activations and _GIT_HEAD_OID
        else task_admission_edges(activations)
    )
    reported = set()
    for parent, revision in edges:
        for path, count, excerpt in task_action_origin_problems(
            parent, revision
        ):
            identity = (
                revision or "index",
                path.as_posix(),
                excerpt,
            )
            if identity in reported:
                continue
            reported.add(identity)
            suffix = f" ({count} copies)" if count > 1 else ""
            yield Finding(
                "task-action-origin",
                path,
                "task artifact introduced an unqueued human action"
                f"{suffix}: {excerpt}",
                "create one needs-human queue item, list it in task.md "
                "Queue actions, and replace the ask with its exact action link",
            )


def check_task_admission_history():
    """Recheck every governed committed task snapshot in an admitted range."""
    if not (REPO / ".git").exists():
        return
    activations = task_admission_activation_commits(_GIT_HEAD_OID)
    enabled = task_admission_enabled()
    if not activations and not enabled:
        return
    candidate_has_tasks = bool(git_index_entries("tasks"))
    if activations and not enabled and candidate_has_tasks:
        yield Finding(
            "task-admission",
            Path("tasks/AGENTS.md"),
            "Task admission schema v1 was removed after activation",
            "restore **Task admission schema:** v1 while tasks remain",
        )
    if not activations:
        return  # a staged first activation has no earlier governed Git edge

    reported = set()
    for parent, revision in task_admission_edges(activations):
        adopting = bool(
            revision is not None
            and not task_admission_enabled(parent)
            and task_admission_enabled(revision)
        )
        for subject, message, fix in task_topology_problems(
            parent, revision, adopting=adopting
        ):
            identity = (
                revision or "index",
                "task-topology",
                str(subject),
                message,
            )
            if identity in reported:
                continue
            reported.add(identity)
            yield Finding(
                "task-admission",
                subject,
                (
                    f"task snapshot {revision} violated lifecycle topology: "
                    if revision is not None
                    else "staged task candidate violated lifecycle topology: "
                ) + message,
                fix,
            )
        if revision is None:
            continue  # task-structure checks the staged candidate directly
        if not task_admission_enabled(revision) \
                and task_service_present_at(revision):
            identity = (revision, "task-admission-marker")
            if identity not in reported:
                reported.add(identity)
                yield Finding(
                    "task-admission",
                    Path("tasks/AGENTS.md"),
                    f"task snapshot {revision} removed Task admission schema v1",
                    "restore **Task admission schema:** v1; a later commit "
                    "cannot erase an admitted downgrade",
                )
        with git_revision_candidate(
            revision, preserve_change_range=True
        ):
            findings = list(check_task_structure())
        for finding in findings:
            identity = (
                revision,
                finding.check,
                str(finding.subject),
                finding.message,
            )
            if identity in reported:
                continue
            reported.add(identity)
            yield Finding(
                "task-admission",
                finding.subject,
                f"task snapshot {revision} violated "
                f"{finding.check}: {finding.message}",
                "repair the introducing commit; a later revert cannot erase "
                "an admitted task-boundary violation",
            )


def live_conversation_directories():
    directories = set()
    if (REPO / ".git").exists():
        for name in git_index_entries("history/conversations"):
            parts = Path(name).parts
            if len(parts) >= 4 \
                    and parts[:2] == ("history", "conversations"):
                directories.add(REPO.joinpath(*parts[:3]))
        return directories
    if CONVERSATIONS.is_dir():
        directories.update(
            conv for conv in CONVERSATIONS.iterdir() if conv.is_dir()
        )
    return directories


def check_handover_present():
    for conv in sorted(live_conversation_directories()):
        rel = conv.relative_to(REPO)
        if not CONVERSATION_RE.match(conv.name):
            yield Finding("handover-present", rel,
                          "folder name must be YYYY-MM-DD-HHMM<TZ>-kebab-slug (local time + zone)",
                          "rename per history/AGENTS.md")
        if repo_artifact_bytes(conv / "handover.md") is None:
            yield Finding("handover-present", rel, "conversation without handover.md",
                          "write one from templates/handover.md — the session ritual skipped")


def handover_projection_enabled():
    contract = REPO / "history" / "AGENTS.md"
    artifact = repo_artifact_bytes(contract)
    if artifact is None:
        return False
    return text_fields(
        artifact.decode("utf-8")
    ).get("Queue projection schema", "").strip() == "v1"


def live_handover_paths():
    """Return exact handover paths from the commit candidate plus untracked files."""
    indexed = git_index_entries("history/conversations")
    committed = git_head_paths("history/conversations")
    paths = set()
    for name, mode in indexed.items():
        path = Path(name)
        if mode in ("100644", "100755") \
                and len(path.parts) == 4 \
                and path.parts[:2] == ("history", "conversations") \
                and CONVERSATION_RE.fullmatch(path.parts[2]) \
                and path.parts[3] == "handover.md":
            paths.add(path)
    if CHANGE_RANGE is not None:
        return paths
    if CONVERSATIONS.is_dir():
        for handover in CONVERSATIONS.glob("*/handover.md"):
            if not handover.is_file() or handover.is_symlink():
                continue
            path = handover.relative_to(REPO)
            if path.as_posix() not in committed:
                paths.add(path)
    return paths


def projection_schema_activation_commits(
    head, field="Queue projection schema", version="v1"
):
    activations, error = schema_activation_commits(
        head,
        "history/AGENTS.md",
        field,
        version=version,
    )
    if error:
        return (), error
    if activations:
        return activations, None
    return (), f"could not find a v1 {field} activation commit"


def handover_action_entry_version():
    contract = repo_artifact_bytes(REPO / "history" / "AGENTS.md")
    if contract is None:
        return None
    version = text_fields(
        contract.decode("utf-8")
    ).get("Queue action-entry schema", "").strip()
    return version if version in {"v1", "v2"} else None


def handover_action_entry_enabled():
    return handover_action_entry_version() is not None


def history_service_present():
    if (REPO / ".git").exists():
        return bool(git_index_entries("history"))
    return (REPO / "history").is_dir()


def handover_action_entry_activations(version="v1"):
    """Return committed entry-version activations, including merged branches."""
    revision = committed_candidate_revision()
    if revision is None:
        return ()
    activations, _error = projection_schema_activation_commits(
        revision,
        field="Queue action-entry schema",
        version=version,
    )
    return activations


def handover_projection_activations():
    """Return committed queue-projection activations, including merged branches."""
    revision = committed_candidate_revision()
    if revision is None:
        return ()
    activations, _error = projection_schema_activation_commits(
        revision,
        field="Queue projection schema",
    )
    return activations


def handover_action_entry_version_for(rel):
    """Return the highest entry schema governing this handover's creation."""
    current_version = handover_action_entry_version()
    activation_map = {
        version: handover_action_entry_activations(version)
        for version in ("v1", "v2")
    }
    if current_version is None and not any(activation_map.values()):
        return None, None
    if CHANGE_RANGE is None:
        return current_version, None
    created_at, creation_error = handover_creation_commit(rel)
    if creation_error:
        return None, creation_error
    range_head = (
        CHANGE_RANGE[len("root:"):]
        if CHANGE_RANGE.startswith("root:")
        else CHANGE_RANGE.rsplit("...", 1)[-1]
    )
    candidate = _GIT_HEAD_OID or range_head
    governed_versions = []
    for version in ("v1", "v2"):
        activations = activation_map[version]
        if not activations:
            activations, activation_error = projection_schema_activation_commits(
                candidate,
                field="Queue action-entry schema",
                version=version,
            )
            if activation_error and current_version == version:
                return None, activation_error
        if not activations:
            continue
        governed, governance_error = governed_by_activation_join(
            created_at, activations
        )
        if governance_error:
            return None, governance_error
        if governed:
            governed_versions.append(version)
    return (
        max(governed_versions, key=lambda value: int(value[1:]))
        if governed_versions else None,
        None,
    )


def newly_added_handovers():
    """Return handovers added in the staged diff or an explicit CI range."""
    if CHANGE_RANGE is None and not (REPO / ".git").exists():
        return set(), None
    if CHANGE_RANGE is None and _GIT_SNAPSHOT_CACHE_ACTIVE:
        lines = sorted(
            name
            for name, mode in git_index_entries(
                "history/conversations"
            ).items()
            if mode in ("100644", "100755")
            and name not in _GIT_HEAD_PATHS_CACHE
        )
    elif CHANGE_RANGE and CHANGE_RANGE.startswith("root:"):
        command = [
            "git", "ls-tree", "-r", "--name-only",
            CHANGE_RANGE[len("root:"):], "--", "history/conversations",
        ]
    else:
        command = ["git", "diff", "--no-renames", "--name-only", "--diff-filter=A"]
        command.append(CHANGE_RANGE if CHANGE_RANGE else "--cached")
        command.extend(["--", "history/conversations"])
    if not (CHANGE_RANGE is None and _GIT_SNAPSHOT_CACHE_ACTIVE):
        result = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            return set(), result.stderr.strip() or "git diff failed"
        lines = result.stdout.splitlines()
    paths = set()
    for line in lines:
        candidate = Path(line)
        parts = candidate.parts
        if len(parts) == 4 \
                and parts[:2] == ("history", "conversations") \
                and CONVERSATION_RE.fullmatch(parts[2]) \
                and parts[3] == "handover.md":
            paths.add(candidate)
    if CHANGE_RANGE and not CHANGE_RANGE.startswith("root:"):
        base, head = CHANGE_RANGE.split("...", 1)
        merge_base = subprocess.run(
            ["git", "merge-base", base, head],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        tree = subprocess.run(
            [
                "git", "ls-tree", "-r", "--name-only", head, "--",
                "history/conversations",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if merge_base.returncode or tree.returncode:
            return set(), merge_base.stderr.strip() or tree.stderr.strip() \
                or "could not inspect range handover incarnations"
        boundary = merge_base.stdout.strip()
        for line in tree.stdout.splitlines():
            candidate = Path(line)
            parts = candidate.parts
            if len(parts) != 4 \
                    or parts[:2] != ("history", "conversations") \
                    or not CONVERSATION_RE.fullmatch(parts[2]) \
                    or parts[3] != "handover.md":
                continue
            latest = subprocess.run(
                [
                    "git", "--no-replace-objects", "log",
                    "--no-renames", "-1", "--format=%H",
                    "--diff-filter=A", head, "--", candidate.as_posix(),
                ],
                cwd=REPO,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            creation = latest.stdout.strip() if latest.returncode == 0 else ""
            if not creation:
                return set(), latest.stderr.strip() \
                    or f"could not find current creation commit for {candidate}"
            before_boundary = subprocess.run(
                ["git", "merge-base", "--is-ancestor", creation, boundary],
                cwd=REPO,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if before_boundary.returncode != 0:
                paths.add(candidate)
    if CHANGE_RANGE:
        range_head = (
            CHANGE_RANGE[len("root:"):]
            if CHANGE_RANGE.startswith("root:")
            else CHANGE_RANGE.rsplit("...", 1)[-1]
        )
        candidate_head = _GIT_HEAD_OID or range_head
        activations, activation_error = projection_schema_activation_commits(
            candidate_head
        )
        if activation_error:
            return set(), activation_error
        governed = set()
        for path in paths:
            creation = subprocess.run(
                [
                    "git", "--no-replace-objects", "log",
                    "--no-renames", "--reverse", "--format=%H",
                    "--diff-filter=A",
                    (
                        range_head
                        if CHANGE_RANGE.startswith("root:")
                        else CHANGE_RANGE
                    ),
                    "--", path.as_posix(),
                ],
                cwd=REPO,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            commits = creation.stdout.splitlines() if creation.returncode == 0 else []
            if creation.returncode or not commits:
                detail = creation.stderr.strip() or (
                    f"could not find a creation commit for {path}"
                )
                return set(), detail
            is_governed, governance_error = governed_by_activation_join(
                commits[-1], activations
            )
            if governance_error:
                return set(), governance_error
            if is_governed:
                governed.add(path)
        paths = governed
    return paths, None


def live_human_queue_paths():
    return {
        item.relative_to(REPO).as_posix()
        for item in live_queue_items() or ()
        if readable_queue_item(item)
        and item.relative_to(QUEUE).parts[0] == "needs-human"
    }


def live_agent_queue_paths():
    return {
        item.relative_to(REPO).as_posix()
        for item in live_queue_items() or ()
        if readable_queue_item(item)
        and item.relative_to(QUEUE).parts[0] == "needs-agent"
    }


def split_live_queue_entries(entries):
    """Partition valid regular queue-item paths by the next actor."""
    live_human = set()
    live_agent = set()
    for name, mode in entries.items():
        path = Path(name)
        if mode not in ("100644", "100755") \
                or len(path.parts) != 4 \
                or path.parts[0] != "message-queue" \
                or path.parts[1] not in ("needs-human", "needs-agent") \
                or not SLUG_RE.fullmatch(path.parts[2]) \
                or not QUEUE_ITEM_RE.fullmatch(path.parts[3]):
            continue
        if path.parts[1] == "needs-human":
            live_human.add(path.as_posix())
        else:
            live_agent.add(path.as_posix())
    return live_human, live_agent


def handover_creation_commit(rel):
    """Return the commit that created the current handover incarnation."""
    if CHANGE_RANGE is None:
        return None, None
    history_range = (
        CHANGE_RANGE[len("root:"):]
        if CHANGE_RANGE.startswith("root:")
        else CHANGE_RANGE
    )
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "log",
            "--no-renames", "--format=%H", "--reverse",
            "--diff-filter=A", history_range, "--", rel.as_posix(),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commits = history.stdout.splitlines() if history.returncode == 0 else []
    if history.returncode or not commits:
        detail = history.stderr.strip() or (
            "could not find the current handover's creation commit"
        )
        return None, detail
    return commits[-1], None


def handover_creation_state(handover, rel):
    """Read a new handover and queue from the snapshot that created the record."""
    if CHANGE_RANGE is None:
        if not (REPO / ".git").exists():
            return (
                handover.read_text(encoding="utf-8"),
                live_human_queue_paths(),
                live_agent_queue_paths(),
                None,
            )
        artifact = repo_artifact_bytes(handover)
        if artifact is None:
            return None, None, None, \
                "could not read the staged handover snapshot"
        live_human, live_agent = split_live_queue_entries(
            git_index_entries("message-queue")
        )
        return artifact.decode("utf-8"), live_human, live_agent, None

    created_at, creation_error = handover_creation_commit(rel)
    if creation_error:
        return None, None, None, creation_error

    artifact = subprocess.run(
        ["git", "show", f"{created_at}:{rel.as_posix()}"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    tree = subprocess.run(
        [
            "git", "ls-tree", "-r", "-z", created_at, "--",
            "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if artifact.returncode or tree.returncode:
        detail = artifact.stderr.strip() or git_failure(
            tree, "could not read the creation snapshot"
        )
        return None, None, None, detail

    live_human, live_agent = split_live_queue_entries(
        parse_git_tree_records(tree.stdout)
    )
    return artifact.stdout, live_human, live_agent, None


def handover_queue_fields_at_creation(rel, queue_path, required):
    """Read projection fields from the handover's immutable creation snapshot."""
    if CHANGE_RANGE is None:
        artifact = repo_artifact_bytes(REPO / queue_path)
    else:
        created_at, creation_error = handover_creation_commit(rel)
        if creation_error:
            return None, creation_error
        artifact = git_artifact_bytes_at(created_at, queue_path)
    if artifact is None:
        return None, f"`{queue_path}` is absent from the creation snapshot"
    text = decode_utf8_artifact(
        artifact, f"`{queue_path}` in the handover creation snapshot"
    )
    counts = field_counts(text)
    got = text_fields(text)
    projected = {}
    for field in required:
        if counts.get(field, 0) != 1:
            return None, (
                f"`{queue_path}` must contain exactly one **{field}:**"
            )
        value = got.get(field, "").strip()
        if not has_concrete_value(value):
            return None, (
                f"`{queue_path}` has no concrete **{field}:**"
            )
        projected[field] = value
    return projected, None


def handover_candidate_text(rel):
    """Read a handover from the exact staged or CI candidate snapshot."""
    artifact = repo_artifact_bytes(REPO / rel)
    if artifact is None:
        return None, "could not read the candidate handover"
    return artifact.decode("utf-8"), None


def handover_current_incarnation_text(rel):
    """Read bytes from the most recent commit that added this path."""
    revision = _GIT_HEAD_OID or "HEAD"
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "log",
            "--no-renames", "-1", "--format=%H",
            "--diff-filter=A", revision, "--", rel.as_posix(),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    created_at = history.stdout.strip() if history.returncode == 0 else ""
    if not created_at:
        return None, history.stderr.strip() or "could not find creation commit"
    artifact = subprocess.run(
        ["git", "show", f"{created_at}:{rel.as_posix()}"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if artifact.returncode:
        return None, artifact.stderr.strip() or "could not read creation bytes"
    return artifact.stdout, None


def prior_governed_v1_handover_incarnation(rel):
    """Find an earlier immutable v1 incarnation of a newly added handover."""
    revision = committed_candidate_revision()
    if revision is None:
        return None, None

    current_creation = None
    if CHANGE_RANGE is not None:
        current_creation, creation_error = handover_creation_commit(rel)
        if creation_error:
            return None, creation_error

    history = subprocess.run(
        [
            "git", "--no-replace-objects", "log",
            "--full-history", "--reverse", "--format=%H",
            "--diff-filter=A", revision, "--", rel.as_posix(),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if history.returncode:
        return None, history.stderr.strip() \
            or "could not inspect prior handover incarnations"
    commits = history.stdout.splitlines()
    if not commits:
        return None, None

    activations, activation_error = schema_activation_commits(
        revision,
        "history/AGENTS.md",
        "Queue projection schema",
    )
    if activation_error:
        return None, activation_error
    if not activations:
        return None, None

    for commit in commits:
        if commit == current_creation:
            continue
        try:
            artifact = git_artifact_bytes_at(commit, rel.as_posix())
            if artifact is None:
                return None, (
                    f"could not read prior handover incarnation at {commit}"
                )
            prior_text = decode_utf8_artifact(
                artifact,
                f"`{rel.as_posix()}` at {commit}",
            )
        except GitSnapshotError as error:
            return None, str(error)
        if text_fields(prior_text).get(
            "Queue projection", ""
        ).strip() != "v1":
            continue
        governed, governance_error = governed_by_activation_join(
            commit, activations
        )
        if governance_error:
            return None, governance_error
        if governed:
            return commit, None
    return None, None


def new_handover_queue_target(handover, target, actor="needs-human"):
    """Resolve a new handover link to one exact portable queue path."""
    candidate = target.split("#", 1)[0]
    path = Path(candidate)
    if not candidate or path.is_absolute() \
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
        return None
    try:
        resolved = (handover.parent / path).resolve()
        relative = resolved.relative_to(REPO.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return None
    pattern = (
        HANDOVER_HUMAN_LINK_RE
        if actor == "needs-human"
        else HANDOVER_AGENT_LINK_RE
    )
    return relative if pattern.fullmatch(relative) else None


def handover_projection_entries(
    rel,
    handover,
    body,
    actor,
    live_paths,
    entry_version,
    raw_body=None,
):
    """Validate strict action-owned list entries in a new v1 handover."""
    actor_label = "human" if actor == "needs-human" else "agent"
    entries, outside = section_entries(body)
    problems = []
    projected = []
    if outside:
        problems.append(
            "contains content outside the top-level action list; make every "
            "projection a list item and indent wrapped context under its item"
        )
    if not entries:
        problems.append("has no top-level queue-linked action entries")
        return projected, problems

    raw_entries, raw_outside = section_entries(
        body if raw_body is None else raw_body
    )
    if entry_version == "v2" and action_like_rendered_prose(raw_outside):
        problems.append(
            "contains an action-like rendered question or directive outside "
            "the top-level action list"
        )
    for index, entry in enumerate(entries, start=1):
        raw_entry = raw_entries[index - 1] if index <= len(raw_entries) else ""
        if entry_version == "v2" and contains_raw_html(raw_entry):
            problems.append(
                f"entry {index} contains raw HTML; strict handover action "
                "entries permit only the sole Markdown queue link and fixed "
                "plain-text context"
            )
        links = markdown_links(entry)
        queue_looking = [
            (label, destination)
            for label, destination in links
            if "message-queue/" in destination
        ]
        if len(queue_looking) != 1:
            problems.append(
                f"entry {index} must contain exactly one canonical "
                f"needs-{actor_label} queue link"
            )
            continue
        if len(links) != 1:
            problems.append(
                f"entry {index} must contain only its exact Action-labeled "
                f"needs-{actor_label} queue link"
            )
        label, destination = queue_looking[0]
        canonical = new_handover_queue_target(
            handover, destination, actor=actor
        )
        if canonical is None:
            problems.append(
                f"entry {index} has an invalid or wrong-actor "
                f"needs-{actor_label} queue link"
            )
            continue

        first_line = semantic_text(entry).splitlines()[0]
        list_item = LIST_ITEM_RE.match(first_line)
        first_link = (
            MARKDOWN_LINK_RE.match(first_line, list_item.end())
            if list_item else None
        )
        first_destination = (
            first_link.group("angle")
            if first_link and first_link.group("angle") is not None
            else first_link.group("bare")
            if first_link
            else None
        )
        if first_destination != destination:
            problems.append(
                f"entry {index} must put its owning queue link first; "
                "action prose cannot borrow a later link"
            )

        if canonical not in live_paths:
            problems.append(
                f"entry {index} links `{canonical}`, which was not live "
                "at handover creation"
            )
            continue
        projected.append(canonical)

        required_fields = (
            ("Action", "Why-you-might-care", "If-you-do-nothing")
            if actor == "needs-human"
            else ("Action",)
        )
        queue_fields, fields_error = handover_queue_fields_at_creation(
            rel, canonical, required_fields
        )
        if fields_error:
            problems.append(f"entry {index} {fields_error}")
            continue
        action = queue_fields["Action"]
        if normalized_action_tokens(label) != normalized_action_tokens(action):
            problems.append(
                f"entry {index} link label must exactly project the linked "
                f"queue item's **Action:** `{action}`"
            )

        expected_context = (
            "— Why-you-might-care: "
            + queue_fields["Why-you-might-care"]
            + " || If-you-do-nothing: "
            + queue_fields["If-you-do-nothing"]
            if actor == "needs-human"
            else ""
        )
        for context in (
            prose_without_links(entry),
            prose_without_links(rendered_human_text(entry)),
        ):
            marker = LIST_ITEM_RE.match(context)
            if marker:
                context = context[marker.end():]
            if " ".join(context.split()) != " ".join(
                expected_context.split()
            ):
                if actor == "needs-human":
                    problems.append(
                        f"entry {index} must copy the creation-snapshot "
                        "Why-you-might-care and If-you-do-nothing fields "
                        "using the fixed handover suffix"
                    )
                else:
                    problems.append(
                        f"entry {index} must contain only its exact "
                        "Action-labeled needs-agent queue link"
                    )
                break

    if len(projected) != len(set(projected)):
        problems.append(
            f"projects a needs-{actor_label} queue action more than once"
        )
    return projected, problems


def check_handover_queue_projection():
    if not history_service_present():
        return
    projection_activations = handover_projection_activations()
    entry_v1_activations = handover_action_entry_activations("v1")
    entry_v2_activations = handover_action_entry_activations("v2")
    entry_version_now = handover_action_entry_version()
    if projection_activations \
            and not handover_projection_enabled():
        yield Finding(
            "handover-queue-projection",
            Path("history/AGENTS.md"),
            "Queue projection schema v1 was removed after activation",
            "restore **Queue projection schema:** v1 while history remains",
        )
    if entry_v2_activations and entry_version_now != "v2":
        yield Finding(
            "handover-queue-projection",
            Path("history/AGENTS.md"),
            "Queue action-entry schema v2 was removed or downgraded after activation",
            "restore **Queue action-entry schema:** v2 while history remains",
        )
    elif entry_v1_activations and entry_version_now not in {"v1", "v2"}:
        yield Finding(
            "handover-queue-projection",
            Path("history/AGENTS.md"),
            "Queue action-entry schema v1 was removed after activation",
            "restore **Queue action-entry schema:** v1 or upgrade to v2",
        )
    if not handover_projection_enabled() and not projection_activations:
        return
    reported_mutations = set()
    mutation_activations = projection_activations
    if not mutation_activations and handover_projection_enabled() \
            and _GIT_HEAD_OID:
        mutation_activations = (_GIT_HEAD_OID,)
    for path, _parent, _revision in handover_mutation_events(
        mutation_activations
    ):
        if path in reported_mutations:
            continue
        reported_mutations.add(path)
        yield Finding(
            "handover-queue-projection",
            Path(path),
            "handover record was modified after queue-projection adoption",
            "restore the original bytes; record a correction in a new "
            "conversation handover (deletion remains allowed)",
        )
    added, diff_error = newly_added_handovers()
    if diff_error:
        yield Finding(
            "handover-queue-projection",
            (REPO / "history" / "AGENTS.md").relative_to(REPO),
            f"could not identify newly added handovers: {diff_error}",
            "pass a valid --range in CI or repair the staged Git diff",
        )
    order = {"blocking": 0, "future-blocking": 1, "non-blocking": 2}
    handovers = live_handover_paths().union(added)
    for rel in sorted(handovers):
        handover = REPO / rel
        is_new = rel in added
        text = None
        candidate_text, candidate_error = handover_candidate_text(rel)
        if candidate_error:
            yield Finding(
                "handover-queue-projection",
                rel,
                "could not verify candidate handover bytes: " + candidate_error,
                "preserve a readable regular file in the candidate snapshot",
            )
            continue
        live_human = live_human_queue_paths()
        live_agent = live_agent_queue_paths()
        entry_version = None
        if is_new:
            text, live_human, live_agent, creation_error = handover_creation_state(
                handover, rel
            )
            if creation_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify the handover's creation snapshot: "
                    + creation_error,
                    "preserve the add commit and pass a range containing it",
                )
                continue
            entry_version, strict_error = handover_action_entry_version_for(
                rel
            )
            if strict_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify strict action-entry activation: "
                    + strict_error,
                    "preserve the schema activation and handover creation commits",
                )
            prior_incarnation, incarnation_error = (
                prior_governed_v1_handover_incarnation(rel)
            )
            if incarnation_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify prior handover incarnations: "
                    + incarnation_error,
                    "preserve the path history or use a new conversation folder",
                )
                continue
            if prior_incarnation:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "reuses a path that already has a committed governed v1 "
                    f"handover incarnation at {prior_incarnation}",
                    "keep committed handover paths single-incarnation; record "
                    "the correction in a new conversation handover",
                )
        else:
            text = candidate_text
        strict_entries = entry_version is not None
        if entry_version == "v2" and contains_raw_html(text):
            yield Finding(
                "handover-queue-projection",
                rel,
                "strict handover contains raw HTML outside code",
                "replace raw HTML with structural Markdown; arbitrary HTML "
                "cannot define or preserve queue-projection boundaries",
            )
            continue
        if entry_version == "v2" and action_like_rendered_prose(
            visible_outside_action_sections(
                text,
                ("Needs your attention", "Next steps"),
            )
        ):
            yield Finding(
                "handover-queue-projection",
                rel,
                "action-like question or directive exists outside the "
                "queue-owned projection sections",
                "move the pending action into a canonical queue item and "
                "project it only from Needs your attention or Next steps",
            )
        has_v1 = text_fields(text).get("Queue projection", "").strip() == "v1"
        if not has_v1 and not is_new:
            continue  # old records stay immutable; creation-time checks govern new ones
        if has_v1 and (REPO / ".git").exists():
            if is_new:
                creation_text, creation_error = text, None
            else:
                creation_text, creation_error = handover_current_incarnation_text(rel)
            if creation_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify immutable handover bytes: " + creation_error,
                    "preserve the path's add commit or restore the original record",
                )
                continue
            if candidate_text != creation_text:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "committed v1 handover changed after its creation snapshot",
                    "restore immutable bytes; record a correction in a new handover",
                )
                continue
        if not has_v1:
            yield Finding(
                "handover-queue-projection",
                rel,
                "missing exact **Queue projection:** v1 schema marker",
                "add the v1 marker and format Needs your attention from the template",
            )
        attention_count = len(re.findall(
            r"^## Needs your attention\s*$",
            semantic_text(text),
            flags=re.M,
        ))
        if attention_count != 1:
            yield Finding(
                "handover-queue-projection",
                rel,
                "handover must contain exactly one ## Needs your attention section",
                "keep one section that exactly projects the creation-time queue",
            )
            continue
        next_count = len(re.findall(
            r"^## Next steps\s*$",
            semantic_text(text),
            flags=re.M,
        ))
        if next_count != 1:
            yield Finding(
                "handover-queue-projection",
                rel,
                "handover must contain exactly one ## Next steps section",
                "use `None.` or link every assigned cross-session action to needs-agent",
            )
        else:
            next_body = level_two_section_body(text, "## Next steps")
            if next_body != "None.":
                if re.search(r"^None\.\s*$", next_body or "", flags=re.M):
                    yield Finding(
                        "handover-queue-projection",
                        rel,
                        "`None.` must be the entire Next steps section",
                        "remove it when cross-session queue links are present",
                    )
                if strict_entries:
                    _agent_entries, entry_problems = (
                        handover_projection_entries(
                            rel,
                            handover,
                            next_body or "",
                            "needs-agent",
                            live_agent,
                            entry_version,
                            raw_body=raw_level_two_section_body(
                                text, "## Next steps"
                            ),
                        )
                    )
                    for problem in entry_problems:
                        yield Finding(
                            "handover-queue-projection",
                            rel,
                            "Next steps " + problem,
                            "use one top-level list entry per live agent action; "
                            "make its exact Action-labeled queue link the "
                            "entry's only content",
                        )
                agent_targets = []
                invalid_agent_links = []
                for target in markdown_link_destinations(next_body or ""):
                    if "message-queue/needs-agent/" not in target:
                        continue
                    canonical = (
                        new_handover_queue_target(
                            handover, target, actor="needs-agent"
                        )
                        if is_new else None
                    )
                    matched = (
                        HANDOVER_AGENT_LINK_RE.fullmatch(canonical)
                        if canonical is not None
                        else HANDOVER_AGENT_LINK_RE.search(target)
                        if not is_new
                        else None
                    )
                    if matched:
                        agent_targets.append(canonical or matched.group(0))
                    else:
                        invalid_agent_links.append(target)
                if invalid_agent_links:
                    yield Finding(
                        "handover-queue-projection",
                        rel,
                        "Next steps contains an unprefixed or invalid needs-agent link",
                        "link timing-prefixed actions under message-queue/needs-agent/",
                    )
                if not agent_targets:
                    yield Finding(
                        "handover-queue-projection",
                        rel,
                        "Next steps assigns work without a canonical needs-agent link",
                        "use `None.` or replace prose with links to live agent actions",
                    )
                elif is_new:
                    nonexistent = sorted(set(agent_targets) - live_agent)
                    if nonexistent:
                        yield Finding(
                            "handover-queue-projection",
                            rel,
                            "Next steps links agent actions absent at creation: "
                            + ", ".join(nonexistent),
                            "create the queue items in the handover commit or remove the links",
                        )
        body = level_two_section_body(text, "## Needs your attention")
        if body is None:
            yield Finding(
                "handover-queue-projection",
                rel,
                "missing ## Needs your attention section",
                "add exactly `None.` or links to the canonical needs-human queue items",
            )
            continue
        if body == "None.":
            if is_new and live_human:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "new handover says None. while human queue actions are live",
                    "project every live needs-human item in canonical urgency order",
                )
            continue
        if re.search(r"^None\.\s*$", body, flags=re.M):
            yield Finding(
                "handover-queue-projection",
                rel,
                "`None.` must be the entire Needs your attention section",
                "remove it when the section contains queue links",
            )
        strict_human_entries = None
        if strict_entries:
            strict_human_entries, entry_problems = handover_projection_entries(
                rel,
                handover,
                body,
                "needs-human",
                live_human,
                entry_version,
                raw_body=raw_level_two_section_body(
                    text, "## Needs your attention"
                ),
            )
            for problem in entry_problems:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "Needs your attention " + problem,
                    "use one top-level list entry per live human action; "
                    "put an exact Action-labeled queue link first and "
                    "keep context declarative",
                )
        targets = markdown_link_destinations(body)
        classes = []
        invalid_human_links = []
        projected_human = []
        for target in targets:
            if "message-queue/needs-human/" not in target:
                continue
            canonical = (
                new_handover_queue_target(handover, target)
                if is_new else None
            )
            matched = (
                HANDOVER_HUMAN_LINK_RE.fullmatch(canonical)
                if canonical is not None
                else HANDOVER_HUMAN_LINK_RE.search(target)
                if not is_new
                else None
            )
            if matched:
                classes.append(matched.group(1))
                projected_human.append(canonical or matched.group(0))
            else:
                invalid_human_links.append(target)
        if invalid_human_links:
            yield Finding(
                "handover-queue-projection",
                rel,
                "Needs your attention contains an unprefixed or invalid needs-human link",
                "link only timing-prefixed items under decisions, clarifications, or reviews",
            )
        if not classes:
            yield Finding(
                "handover-queue-projection",
                rel,
                "Needs your attention has prose but no canonical needs-human queue link",
                "replace orphan prose with one or more markdown links to live queue projections",
            )
            continue
        ranks = [order[delivery] for delivery in classes]
        if ranks != sorted(ranks):
            yield Finding(
                "handover-queue-projection",
                rel,
                "needs-human links are not ordered blocking, future-blocking, non-blocking",
                "group links by delivery class in canonical urgency order",
            )
        if is_new and len(projected_human) != len(set(projected_human)):
            yield Finding(
                "handover-queue-projection",
                rel,
                "new handover projects a human queue action more than once",
                "keep one actionable entry per live needs-human item",
            )
        if is_new and set(projected_human) != live_human:
            missing = sorted(live_human - set(projected_human))
            stale = sorted(set(projected_human) - live_human)
            detail = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if stale:
                detail.append("not live " + ", ".join(stale))
            yield Finding(
                "handover-queue-projection",
                rel,
                "new handover is not an exact projection of the live human queue: "
                + "; ".join(detail),
                "list every live needs-human item once; omit resolved or invented asks",
            )
        if strict_entries and strict_human_entries is not None:
            expected = sorted(
                live_human,
                key=lambda path: (
                    order[delivery_class(Path(path).name)],
                    path,
                ),
            )
            if strict_human_entries != expected:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "new handover human entries are not in canonical "
                    "timing-and-filename order",
                    "order all live human actions by blocking, "
                    "future-blocking, non-blocking, then queue path",
                )


def memory_entries():
    if (REPO / ".git").exists():
        for name, mode in sorted(git_index_entries("memory").items()):
            path = Path(name)
            if mode in ("100644", "100755") \
                    and len(path.parts) >= 3 \
                    and path.parts[0] == "memory" \
                    and path.parts[1] in MEMORY_ZONES \
                    and path.suffix == ".md" \
                    and path.name != "README.md":
                yield path.parts[1], REPO / path
        return
    for zone in MEMORY_ZONES:
        folder = MEMORY / zone
        if folder.is_dir():
            for f in sorted(folder.rglob("*.md")):
                if f.name != "README.md":
                    yield zone, f


def check_memory_schema():
    for zone, entry in memory_entries():
        got = fields(entry)
        required = ["Description", "Review-by"]
        if zone == "decisions":
            required += ["Status", "Date", "Decided-by"]
        if zone == "lessons":
            required += ["Area", "Last-confirmed"]
        if zone == "known-issues":
            required += ["Status", "Severity"]
        for key in required:
            if key not in got:
                yield Finding("memory-schema", entry.relative_to(REPO),
                              f"missing required field **{key}:**",
                              f"copy the header from templates/memory/ ({zone})")


def check_memory_expiry():
    for _, entry in memory_entries():
        due = parse_date(fields(entry).get("Review-by", ""))
        if due and due < TODAY:
            yield Finding("memory-expiry", entry.relative_to(REPO),
                          f"Review-by {due} is past",
                          "run the memory-gardener skill: re-verify, compact, or delete")


def generated_index():
    lines = ["<!-- GENERATED by reconcile.py --fix-index — edit the memory files, never this index -->",
             "# Memory index", ""]
    superseded = set()
    for zone, decision in memory_entries():
        if zone == "decisions":
            superseded.update(context_files(fields(decision).get("Supersedes", "")))
    for zone in MEMORY_ZONES:
        entries = [(z, e) for z, e in memory_entries() if z == zone]
        if not entries:
            continue
        lines.append(f"## {zone}")
        for _, entry in entries:
            text = repo_text(entry)
            title = next((l[2:] for l in text.splitlines() if l.startswith("# ")), entry.stem)
            metadata = fields(entry)
            status = ""
            if zone == "decisions" and (
                metadata.get("Status", "").strip() == "superseded"
                or entry in superseded
            ):
                status = " **[superseded]**"
            desc = metadata.get("Description", "").strip()
            lines.append(f"- [{title}]({entry.relative_to(MEMORY)}){status} — {desc}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def check_memory_index():
    index = MEMORY / "index.md"
    if not MEMORY.is_dir():
        return
    artifact = repo_artifact_bytes(index)
    if artifact is None \
            or artifact.decode("utf-8") != generated_index():
        yield Finding("memory-index", index.relative_to(REPO),
                      "index does not match the memory files",
                      "run: python3 automation/reconcile/reconcile.py --fix-index")


def check_links():
    for md in live_markdown_files():
        rel = md.relative_to(REPO)
        parts = rel.parts
        if parts[0] in LINK_SKIP_DIRS or parts[0].startswith("."):
            continue
        if parts[:2] == ("memory", "decisions"):  # immutable records may cite dead paths
            continue
        if parts[:3] == ("message-queue", "needs-agent", "retries"):
            continue  # repair items cite broken/deleted subjects by design
        text = semantic_text(repo_text(md))
        if parts[0] == "message-queue":
            # Resolution evidence is deliberately predeclared before it exists.
            # Its lifecycle check requires creation/change when the action closes.
            text = re.sub(
                r"^\*\*Resolution evidence:\*\*[^\n]*$",
                "",
                text,
                flags=re.M,
            )
        candidates = set(BACKTICK_RE.findall(text))
        candidates.update(markdown_link_destinations(text))
        for cand in sorted(candidates):
            if cand.startswith(LINK_SKIP_PREFIXES) or any(c in cand for c in "*<>{}$"):
                continue
            if cand.count("/") < 1 or (cand.count("/") == 1 and cand.endswith("/")):
                continue
            if not re.fullmatch(r"[\w./-]+", cand):
                continue
            try:
                root_target = REPO / cand
                local_target = (md.parent / cand).resolve()
                root_exists = repo_artifact_bytes(root_target) is not None \
                    or bool(git_index_entries(cand))
                local_exists = False
                try:
                    local_rel = local_target.relative_to(REPO.resolve()).as_posix()
                    local_exists = repo_artifact_bytes(REPO / local_rel) is not None \
                        or bool(git_index_entries(local_rel))
                except ValueError:
                    local_exists = local_target.exists()
                if root_exists or local_exists:
                    continue
            except (OSError, ValueError):
                pass
            yield Finding("link-check", rel, f"`{cand}` does not exist",
                          "fix the path, create the target, or unquote if not a path")


def check_agents_budget():
    for md in live_markdown_files():
        parts = md.relative_to(REPO).parts
        if parts[0].startswith(".") or parts[0] == "templates":  # schemas, not live contracts
            continue
        lines = len(repo_text(md).splitlines())
        budget = None
        if md.name == "AGENTS.md":
            budget = ROOT_AGENTS_BUDGET if md.parent == REPO else LEAF_AGENTS_BUDGET
        elif md.name == "SKILL.md":
            budget = SKILL_BUDGET
        elif md.name == "README.md" and md.parent == REPO:
            budget = ROOT_README_BUDGET
        if budget and lines > budget:
            yield Finding("agents-budget", md.relative_to(REPO),
                          f"{lines} lines exceeds the {budget}-line budget",
                          "move depth into a linked doc (handbook/principles/progressive-disclosure.md)")


def check_mode_valid():
    root = REPO / "AGENTS.md"
    if not root.is_file():
        return
    mode = fields(root).get("Collaboration mode", "").strip("`* ").split("`")[0].strip("` ")
    if mode not in ("autonomous", "async", "pair"):
        yield Finding("mode-valid", "AGENTS.md",
                      f"collaboration mode {mode!r} is not autonomous|async|pair",
                      "fix the **Collaboration mode:** line")


def check_roadmap_fresh():
    current = REPO / "roadmap" / "current-state.md"
    done = TASKS / "4_done"
    if not current.is_file() or not done.is_dir():
        return
    updated = parse_date(fields(current).get("Last-updated", ""))
    if (REPO / ".git").exists():
        done_ids = {
            Path(name).parts[2]
            for name in git_index_entries("tasks/4_done")
            if len(Path(name).parts) >= 4
            and TASK_ID_RE.fullmatch(Path(name).parts[2])
        }
        newest = max(
            (parse_date(task_id) for task_id in done_ids),
            default=None,
        )
    else:
        newest = max((parse_date(t.name) for t in done.iterdir()
                      if t.is_dir() and parse_date(t.name)), default=None)
    if updated and newest and updated < newest:
        yield Finding("roadmap-fresh", "roadmap/current-state.md",
                      f"Last-updated {updated} predates the newest done task ({newest})",
                      "re-read current-state.md against reality and bump Last-updated")


CHECKS = {
    "queue-name": check_queue_name,
    "queue-location": check_queue_location,
    "queue-schema": check_queue_schema,
    "queue-resolution": check_queue_resolution,
    "queue-boundary": check_active_queue_boundaries,
    "queue-task-reciprocity": check_queue_task_reciprocity,
    "stale-queue": check_stale_queue,
    "task-structure": check_task_structure,
    "task-admission": check_task_admission_history,
    "task-action-origin": check_task_action_origin,
    "handover-present": check_handover_present,
    "handover-queue-projection": check_handover_queue_projection,
    "memory-schema": check_memory_schema,
    "memory-expiry": check_memory_expiry,
    "memory-index": check_memory_index,
    "link-check": check_links,
    "agents-budget": check_agents_budget,
    "mode-valid": check_mode_valid,
    "roadmap-fresh": check_roadmap_fresh,
}


# ---------------------------------------------------------- retry filing

def finding_identity(check, subject):
    return hashlib.sha256(
        f"{check}\0{subject}".encode("utf-8")
    ).hexdigest()


def finding_key(f):
    slug = re.sub(r"[^a-z0-9]+", "-", str(f.subject).lower()).strip("-")
    digest = finding_identity(f.check, f.subject)[:10]
    base = f"reconcile-{f.check}-{slug}"
    room = 80 - len(digest) - 1
    return f"{base[:room].rstrip('-')}-{digest}"


def legacy_finding_key(f):
    """Return the pre-v1 retry filename key used before digest identities."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(f.subject).lower()).strip("-")
    return f"reconcile-{f.check}-{slug}"[:80]


def aggregate_findings(findings):
    grouped = {}
    for finding in findings:
        identity = (finding.check, str(finding.subject))
        grouped.setdefault(identity, []).append(finding)
    combined = []
    for group in grouped.values():
        if len(group) == 1:
            combined.append(group[0])
            continue
        messages = list(dict.fromkeys(str(finding.message) for finding in group))
        fixes = list(dict.fromkeys(str(finding.fix) for finding in group))
        combined.append(Finding(
            group[0].check,
            group[0].subject,
            f"{len(messages)} {group[0].check} violations remain:\n"
            + "\n".join(f"- {message}" for message in messages),
            "Resolve every violation:\n"
            + "\n".join(f"- {fix}" for fix in fixes),
        ))
    return combined


def retry_title(f):
    return str(f.message).splitlines()[0].rstrip(":")


def retry_action(f):
    if "\n" in str(f.fix):
        return f"resolve all listed {f.check} violations for `{f.subject}`"
    return re.sub(r"\s+", " ", str(f.fix)).strip()


def retry_projection(f):
    return (
        f"{RETRY_PROJECTION_START}\n"
        f"## Broken invariant\n\n{f.message}\n\nSubject: `{f.subject}`\n\n"
        f"## Fix\n\n{f.fix}\n"
        f"{RETRY_PROJECTION_END}"
    )


def retry_text(f):
    return (
        f"# {retry_title(f)}\n\n"
        f"**Status:** open\n"
        f"**Filed:** {TODAY}, by reconciler\n"
        f"**Generated by:** {RETRY_GENERATOR}\n"
        f"**Finding identity:** sha256:{finding_identity(f.check, f.subject)}\n"
        f"**Check:** {f.check}\n"
        f"**Subject:** `{f.subject}`\n"
        f"**Action:** {retry_action(f)}\n"
        f"**Blocks now:** transition:merge\n\n"
        f"{retry_projection(f)}\n\n"
        "## Agent notes\n\nNone yet.\n"
    )


def reconciler_owned_retry(path, text):
    got = text_fields(text)
    check = got.get("Check", "").strip()
    subject = got.get("Subject", "").strip().strip("`")
    identity = got.get("Finding identity", "").strip()
    filed = got.get("Filed", "")
    if not (
        got.get("Generated by", "").strip() == RETRY_GENERATOR
        and check
        and subject
        and identity == f"sha256:{finding_identity(check, subject)}"
        and re.search(r"(?:^|,\s*)by reconciler(?:\s*$|,)", filed)
        and text.count(RETRY_PROJECTION_START) == 1
        and text.count(RETRY_PROJECTION_END) == 1
        and "## Broken invariant" in text
        and "## Fix" in text
    ):
        return False
    unprefixed = re.sub(
        r"^(?:blocking|future-blocking|non-blocking)-", "", path.name
    )
    expected = finding_key(Finding(check, Path(subject), "", ""))
    return bool(re.fullmatch(
        re.escape(expected) + r"(?:-[0-9]+)?\.md",
        unprefixed,
    ))


def legacy_reconciler_retry(path, text):
    got = text_fields(text)
    unprefixed = re.sub(
        r"^(?:blocking|future-blocking|non-blocking)-", "", path.name
    )
    if not unprefixed.startswith("reconcile-"):
        return False
    filed = got.get("Filed", "")
    legacy_provenance = re.search(r"(?:^|,\s*)by reconciler(?:\s*$|,)", filed)
    return bool(
        legacy_provenance
        and got.get("Check")
        and got.get("Subject")
        and "## Broken invariant" in text
        and "## Fix" in text
    )


def refresh_retry_text(text, finding, timing="blocking"):
    got = text_fields(text)
    text = re.sub(
        r"\A# .*$",
        lambda _: f"# {retry_title(finding)}",
        text,
        count=1,
        flags=re.M,
    )
    additions = []
    if "Generated by" not in got:
        additions.append(f"**Generated by:** {RETRY_GENERATOR}")
    desired_identity = (
        f"sha256:{finding_identity(finding.check, finding.subject)}"
    )
    if got.get("Finding identity", "").strip() != desired_identity:
        additions.append(f"**Finding identity:** {desired_identity}")
    if timing == "blocking" and "Blocks now" not in got:
        additions.append("**Blocks now:** transition:merge")
    subject_line = re.search(r"^\*\*Subject:\*\*.*$", text, flags=re.M)
    if additions and not subject_line:
        return text  # provenance recognition requires Subject; avoid a destructive guess
    if additions:
        insertion = "\n" + "\n".join(additions)
        text = text[:subject_line.end()] + insertion + text[subject_line.end():]

    desired_action = f"**Action:** {retry_action(finding)}"
    if re.search(r"^\*\*Action:\*\*.*$", text, flags=re.M):
        text = re.sub(
            r"^\*\*Action:\*\*.*$",
            lambda _: desired_action,
            text,
            count=1,
            flags=re.M,
        )
    else:
        subject_line = re.search(r"^\*\*Subject:\*\*.*$", text, flags=re.M)
        if subject_line:
            text = (
                text[:subject_line.end()]
                + "\n"
                + desired_action
                + text[subject_line.end():]
            )

    projection = retry_projection(finding)
    marked = re.compile(
        re.escape(RETRY_PROJECTION_START)
        + r".*?"
        + re.escape(RETRY_PROJECTION_END),
        re.S,
    )
    if marked.search(text):
        return marked.sub(lambda _: projection, text, count=1)

    legacy_start = re.search(r"^## Broken invariant\s*$", text, flags=re.M)
    if legacy_start:
        actor_tail = re.search(
            r"^## (?!Broken invariant$|Fix$).+$",
            text[legacy_start.start():],
            flags=re.M,
        )
        end = (
            legacy_start.start() + actor_tail.start()
            if actor_tail
            else len(text)
        )
        return (
            text[:legacy_start.start()].rstrip()
            + "\n\n"
            + projection
            + "\n\n"
            + text[end:].lstrip()
        ).rstrip() + "\n"

    return text.rstrip() + "\n\n" + projection + "\n"


def retry_identity_matches(text, finding):
    got = text_fields(text)
    return (
        got.get("Check", "").strip() == finding.check
        and got.get("Subject", "").strip().strip("`") == str(finding.subject)
    )


def retry_destination(key, finding):
    if RETRIES.is_dir():
        for candidate in sorted(RETRIES.glob("*.md")):
            if delivery_class(candidate.name) is None \
                    or not candidate.is_file() or candidate.is_symlink():
                continue
            text = candidate.read_text(encoding="utf-8")
            if (
                reconciler_owned_retry(candidate, text)
                or legacy_reconciler_retry(candidate, text)
            ) \
                    and retry_identity_matches(text, finding):
                return candidate

    base = RETRIES / f"blocking-{key}.md"
    existing = [base]
    existing.extend(sorted(RETRIES.glob(f"blocking-{key}-[0-9]*.md")))
    for candidate in existing:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        text = candidate.read_text(encoding="utf-8")
        if (
            reconciler_owned_retry(candidate, text)
            or legacy_reconciler_retry(candidate, text)
        ) \
                and retry_identity_matches(text, finding):
            return candidate

    suffix = 0
    while True:
        disambiguator = "" if suffix == 0 else f"-{suffix}"
        candidate = RETRIES / f"blocking-{key}{disambiguator}.md"
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        suffix += 1


def file_retries(findings):
    RETRIES.mkdir(parents=True, exist_ok=True)
    wanted = aggregate_findings(findings)
    active_paths = set()
    removed = 0
    for f in wanted:
        key = finding_key(f)
        desired = retry_destination(key, f)
        active_paths.add(desired)
        if desired.is_file() and not desired.is_symlink():
            text = desired.read_text(encoding="utf-8")
            if reconciler_owned_retry(desired, text) \
                    or legacy_reconciler_retry(desired, text):
                refreshed = refresh_retry_text(
                    text, f, delivery_class(desired.name)
                )
                if refreshed != text:
                    desired.write_text(refreshed, encoding="utf-8")
            continue  # preserve actor-owned status/notes; refresh only machine projection
        legacy_candidates = {
            RETRIES / f"{key}.md",
            RETRIES / f"{legacy_finding_key(f)}.md",
        }
        migrated = False
        for legacy in sorted(legacy_candidates):
            if not legacy.is_file() or legacy.is_symlink():
                continue
            text = legacy.read_text(encoding="utf-8")
            if not (
                reconciler_owned_retry(legacy, text)
                or legacy_reconciler_retry(legacy, text)
            ) \
                    or not retry_identity_matches(text, f):
                continue
            desired.write_text(
                refresh_retry_text(
                    text, f, delivery_class(desired.name)
                ),
                encoding="utf-8",
            )
            legacy.unlink()
            removed += 1
            migrated = True
            break
        if migrated:
            continue
        desired.write_text(retry_text(f), encoding="utf-8")
    generated = set(RETRIES.glob("*.md"))
    for item in generated:
        if item.is_symlink() or not item.is_file():
            continue
        text = item.read_text(encoding="utf-8")
        if not reconciler_owned_retry(item, text):
            continue
        check = text_fields(text).get("Check", "").strip()
        if check not in CHECKS or check == "queue-resolution":
            continue
        if item not in active_paths:
            item.unlink()
            removed += 1
    return len(wanted), removed


def reconcile(argv=None):
    global ACTIVE_TASK_ID, ACTIVE_TRANSITIONS, CHANGE_RANGE, DISPLACED_TIP
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report findings (default)")
    parser.add_argument("--file-retries", action="store_true",
                        help="write repair items for findings; gc fixed ones")
    parser.add_argument("--fix-index", action="store_true",
                        help="regenerate memory/index.md")
    parser.add_argument(
        "--at-transition",
        action="append",
        default=[],
        metavar="NAME",
        help="reject unresolved blocking actions whose transition:<name> is reached",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--task-id",
        metavar="ID",
        help="scope reached boundaries to one task id (a task/<id> branch is accepted)",
    )
    scope.add_argument(
        "--branch",
        metavar="NAME",
        help="derive scope from task/<id>, changed task records, or commit task tags",
    )
    parser.add_argument(
        "--range",
        metavar="BASE...HEAD|root:HEAD",
        help="Git range used to identify new handovers; root:HEAD covers a first push",
    )
    parser.add_argument(
        "--displaced-tip",
        metavar="FULL_OID",
        help="old ref tip replaced by --range head; validates force-push continuity",
    )
    args = parser.parse_args(argv)
    invalid_transitions = [
        transition for transition in args.at_transition
        if not SLUG_RE.fullmatch(transition)
    ]
    if invalid_transitions:
        parser.error("--at-transition values must be lowercase kebab-case")
    if args.range and not GIT_RANGE_RE.fullmatch(args.range):
        parser.error(
            "--range must be full-base...full-head or root:full-head"
        )
    if args.displaced_tip and not FULL_GIT_OID_RE.fullmatch(args.displaced_tip):
        parser.error("--displaced-tip must be one full commit object id")
    if args.displaced_tip and (
        not args.range or args.range.startswith("root:")
    ):
        parser.error("--displaced-tip requires a full BASE...HEAD --range")
    ACTIVE_TRANSITIONS = set(args.at_transition)
    CHANGE_RANGE = args.range
    DISPLACED_TIP = args.displaced_tip
    validate_range_candidate(CHANGE_RANGE)
    validate_displaced_tip(DISPLACED_TIP, CHANGE_RANGE)
    if args.task_id:
        task_id = args.task_id
        if task_id.startswith("task/"):
            task_id = task_id[len("task/"):]
        if not TASK_ID_RE.fullmatch(task_id):
            parser.error("--task-id must be YYYY-MM-DD-kebab-slug or task/<that-id>")
        ACTIVE_TASK_ID = task_id
    elif args.branch:
        if args.branch.startswith("task/"):
            task_id = args.branch[len("task/"):]
            if not TASK_ID_RE.fullmatch(task_id):
                parser.error("task branch must be task/YYYY-MM-DD-kebab-slug")
            ACTIVE_TASK_ID = task_id
        else:
            inferred = task_ids_from_change_range(CHANGE_RANGE)
            ACTIVE_TASK_ID = frozenset(inferred) if inferred else ""
    else:
        ACTIVE_TASK_ID = None  # unscoped invocation checks every task boundary

    if args.fix_index:
        (MEMORY / "index.md").write_text(generated_index(), encoding="utf-8")
        print("memory/index.md regenerated")
        if not (args.check or args.file_retries):
            return 0

    findings = [f for check in CHECKS.values() for f in check()]
    for f in findings:
        print(f)
        print(f"    fix: {f.fix}")

    if args.file_retries:
        filed, removed = file_retries(findings)
        print(f"retries: {filed} filed/refreshed, {removed} cleared")

    print(f"reconcile: {len(findings)} finding(s)")
    return 1 if findings else 0


def main(argv=None):
    try:
        start_git_snapshot_cache()
        return reconcile(argv)
    except GitSnapshotError as error:
        print(f"reconcile: Git snapshot error: {error}", file=sys.stderr)
        return 2
    finally:
        stop_git_snapshot_cache()


if __name__ == "__main__":
    sys.exit(main())
