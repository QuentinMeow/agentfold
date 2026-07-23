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
import datetime
import hashlib
import re
import subprocess
import sys
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from markdown_semantics import markdown_link_destinations, semantic_text

REPO = Path(__file__).resolve().parents[2]
TODAY = datetime.date.today()

QUEUE = REPO / "message-queue"
RETRIES = QUEUE / "needs-agent" / "retries"
TASKS = REPO / "tasks"
TASK_STATUSES = ["0_backlog", "1_in-progress", "2_blocked", "3_in-review", "4_done"]
CONVERSATIONS = REPO / "history" / "conversations"
MEMORY = REPO / "memory"
MEMORY_ZONES = ["facts", "decisions", "lessons", "known-issues"]
ACTIVE_TRANSITIONS = set()
ACTIVE_TASK_ID = None
CHANGE_RANGE = None

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
GIT_RANGE_RE = re.compile(
    r"^(?:[0-9a-f]{40}|[0-9a-f]{64})"
    r"\.\.\.(?:[0-9a-f]{40}|[0-9a-f]{64})$"
)
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


def fields(path):
    return text_fields(path.read_text(encoding="utf-8"))


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


def live_queue_items():
    if not QUEUE.is_dir():
        return
    for item in sorted(QUEUE.rglob("*")):
        if (item.is_file() or item.is_symlink()) \
                and item.name not in ("README.md", "AGENTS.md", "CLAUDE.md"):
            yield item


def readable_queue_item(item):
    """Queue state must be stored in a repository-local regular file."""
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


def context_files(value):
    candidates = set(CONTEXT_BACKTICK_RE.findall(value or ""))
    candidates.update(markdown_link_destinations(value or ""))
    found = []
    for candidate in candidates:
        candidate = candidate.split("#", 1)[0]
        path = Path(candidate)
        if not candidate or path.is_absolute() or ".." in path.parts:
            continue
        target = REPO / path
        try:
            if target.is_file() and not target.is_symlink():
                found.append(target)
        except (OSError, ValueError):
            continue
    return found


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
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        timing = delivery_class(item.name)
        if timing is None:
            continue  # queue-name owns the malformed-name finding
        text = item.read_text(encoding="utf-8")
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
        text = item.read_text(encoding="utf-8")
        clean = semantic_text(text)
        got = text_fields(text)
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
        if actor == "needs-agent" and leaf != "retries" \
                and "Full context" in got \
                and not context_files(got["Full context"]):
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
        if "Full context" in got and not context_files(got["Full context"]):
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
            local_targets = context_files(target)
            linked_targets = markdown_link_destinations(target)
            https_targets = [
                candidate for candidate in [target, *linked_targets]
                if re.fullmatch(r"https://[^\s]+", candidate)
            ]
            target_available = len(local_targets) == 1 or len(https_targets) == 1
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
            else:
                if not target_available:
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "**Review target:** must identify exactly one file or HTTPS artifact",
                        "link one exact file, diff, commit, or artifact being judged",
                    )
                if not REVIEW_REVISION_RE.fullmatch(revision):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "**Review revision:** is not an immutable sha256 or Git revision",
                        "use sha256:<64 hex>, git:<full id>, or git:<base>...<head>",
                    )
                if local_targets:
                    if local_targets[0] == item:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "a review cannot target its own mutable queue item",
                            "target the underlying artifact and keep delivery state here",
                        )
                    expected = "sha256:" + hashlib.sha256(
                        local_targets[0].read_bytes()
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
                elif has_concrete_value(reviewed_revision):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        "Reviewed revision exists without a concrete review response",
                        "clear the stale binding or record the corresponding response",
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
    if (value or "").strip().lower() == "none":
        return []
    return sorted(set(QUEUE_PATH_RE.findall(value or "")))


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


def task_records():
    if not TASKS.is_dir():
        return {}
    records = {}
    for status in TASK_STATUSES:
        folder = TASKS / status
        if not folder.is_dir():
            continue
        for task in folder.iterdir():
            if task.is_dir() and TASK_ID_RE.fullmatch(task.name) \
                    and (task / "task.md").is_file():
                records[task.name] = (status, task, fields(task / "task.md"))
    return records


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
        if ACTIVE_TASK_ID is not None and task_ids and ACTIVE_TASK_ID not in task_ids:
            continue
        reached = boundary_transitions(tokens).intersection(ACTIVE_TRANSITIONS)
        if reached:
            yield Finding(
                "queue-boundary",
                item.relative_to(REPO),
                f"unresolved {timing} action reached transition:"
                + ",".join(sorted(reached)),
                "resolve the action or reclassify its timing before crossing the boundary",
            )


def check_queue_task_reciprocity():
    if not QUEUE.is_dir() or not TASKS.is_dir():
        return
    records = task_records()
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
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

        context_task_ids = set()
        context_targets = []
        if queue_endpoint(item) == "needs-agent/requests":
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
        is_pickup = got.get("Request kind", "").strip() == "task-pickup"
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
                yield Finding(
                    "queue-task-reciprocity",
                    item.relative_to(REPO),
                    f"blocking task:{task_id} is not in 2_blocked",
                    "move the stopped task to 2_blocked or reclassify the queue timing",
                )


def check_task_structure():
    if not TASKS.is_dir():
        return
    queue_enabled = QUEUE.is_dir()
    for entry in TASKS.iterdir():
        if entry.name in ("AGENTS.md", "README.md", "CLAUDE.md") or entry.name.startswith("."):
            continue
        if entry.name not in TASK_STATUSES:
            yield Finding("task-structure", entry.relative_to(REPO),
                          "not a valid status folder", f"one of: {', '.join(TASK_STATUSES)}")
            continue
        for task in entry.iterdir():
            if task.name == "README.md" or task.name.startswith("."):
                continue
            rel = task.relative_to(REPO)
            if not task.is_dir():
                yield Finding("task-structure", rel, "loose file in a status folder",
                              "tasks are folders; move stray files into one")
                continue
            if not TASK_ID_RE.match(task.name):
                yield Finding("task-structure", rel, "task id must be YYYY-MM-DD-kebab-slug",
                              "rename per handbook/naming-conventions.md")
            if not (task / "task.md").is_file():
                yield Finding("task-structure", rel, "missing task.md",
                              "copy templates/task/task.md")
                continue
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
            if entry.name == "0_backlog" and claimant != "unclaimed":
                yield Finding(
                    "task-structure",
                    rel / "task.md",
                    "backlog task must remain unclaimed",
                    "move the claimed task to 1_in-progress in its claim commit",
                )
            if entry.name != "0_backlog" and claimant == "unclaimed":
                yield Finding(
                    "task-structure",
                    rel / "task.md",
                    "active or completed task cannot be unclaimed",
                    "record the claimant before leaving backlog",
                )
            if queue_enabled:
                queue_value = got.get("Queue actions", "")
                queue_paths = task_queue_paths(queue_value)
                queue_is_none = queue_value.strip().lower() == "none"
                if "Queue actions" in got and not queue_is_none and not queue_paths:
                    yield Finding(
                        "task-structure",
                        rel / "task.md",
                        "**Queue actions:** must be `none` or list live queue paths",
                        "list root-relative message-queue paths with valid delivery prefixes",
                    )
                remainder = QUEUE_PATH_RE.sub("", queue_value)
                if queue_paths and re.search(r"\bnone\b", remainder, flags=re.I):
                    yield Finding(
                        "task-structure",
                        rel / "task.md",
                        "**Queue actions:** cannot combine `none` with a queue path",
                        "use exactly `none`, or list the live queue paths",
                    )
                live_queue_paths = []
                for queue_path in queue_paths:
                    target = REPO / queue_path
                    if not target.is_file() or target.is_symlink():
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"Queue actions path `{queue_path}` is not a live file",
                            "create the queue item or remove the stale task reference",
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
                    live_queue_paths.append(target)
                if entry.name == "0_backlog":
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
                reached = inferred_task_transitions(entry.name)
                for target in live_queue_paths:
                    if delivery_class(target.name) != "future-blocking":
                        continue
                    tokens = future_boundary_tokens(
                        fields(target).get("Blocks at", "")
                    )
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
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "task crossed unresolved future boundary transition:"
                            + ",".join(sorted(crossed)),
                            "resolve or reclassify the queue action before moving task status",
                        )
                if entry.name == "4_done" and not queue_is_none:
                    yield Finding(
                        "task-structure",
                        rel / "task.md",
                        "done task must declare **Queue actions:** none",
                        "resolve or transfer every pending action before moving to 4_done",
                    )
                if entry.name == "2_blocked":
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
            if entry.name in ("1_in-progress", "2_blocked", "3_in-review", "4_done"):
                for needed in ("plan.md", "worklog.md"):
                    if not (task / needed).is_file():
                        yield Finding("task-structure", rel, f"missing {needed}",
                                      f"copy templates/task/{needed}")
            if entry.name in ("3_in-review", "4_done") and not (task / "verification.md").is_file():
                yield Finding("task-structure", rel, "missing verification.md",
                              "record real command output per templates/task/verification.md")
            if entry.name == "1_in-progress" and days_old(task) > STALE_TASK_DAYS:
                yield Finding("stale-task", rel,
                              f"untouched for over {STALE_TASK_DAYS} days",
                              "continue it, or move back to 0_backlog and unclaim")


def check_handover_present():
    if not CONVERSATIONS.is_dir():
        return
    for conv in CONVERSATIONS.iterdir():
        if not conv.is_dir():
            continue
        rel = conv.relative_to(REPO)
        if not CONVERSATION_RE.match(conv.name):
            yield Finding("handover-present", rel,
                          "folder name must be YYYY-MM-DD-HHMM<TZ>-kebab-slug (local time + zone)",
                          "rename per history/AGENTS.md")
        if not (conv / "handover.md").is_file():
            yield Finding("handover-present", rel, "conversation without handover.md",
                          "write one from templates/handover.md — the session ritual skipped")


def handover_projection_enabled():
    contract = REPO / "history" / "AGENTS.md"
    if not contract.is_file():
        return False
    return fields(contract).get("Queue projection schema", "").strip() == "v1"


def newly_added_handovers():
    """Return handovers added in the staged diff or an explicit CI range."""
    if CHANGE_RANGE is None and not (REPO / ".git").exists():
        return set(), None
    command = ["git", "diff", "--name-only", "--diff-filter=A"]
    command.append(CHANGE_RANGE if CHANGE_RANGE else "--cached")
    command.extend(["--", "history/conversations"])
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
    paths = set()
    for line in result.stdout.splitlines():
        candidate = Path(line)
        parts = candidate.parts
        if len(parts) == 4 \
                and parts[:2] == ("history", "conversations") \
                and CONVERSATION_RE.fullmatch(parts[2]) \
                and parts[3] == "handover.md":
            paths.add(candidate)
    return paths, None


def check_handover_queue_projection():
    if not QUEUE.is_dir() or not CONVERSATIONS.is_dir():
        return
    if not handover_projection_enabled():
        return
    added, diff_error = newly_added_handovers()
    if diff_error:
        yield Finding(
            "handover-queue-projection",
            (REPO / "history" / "AGENTS.md").relative_to(REPO),
            f"could not identify newly added handovers: {diff_error}",
            "pass a valid --range in CI or repair the staged Git diff",
        )
    order = {"blocking": 0, "future-blocking": 1, "non-blocking": 2}
    live_human = {
        item.relative_to(REPO).as_posix()
        for item in live_queue_items() or ()
        if readable_queue_item(item)
        and item.relative_to(QUEUE).parts[0] == "needs-human"
    }
    for conv in sorted(CONVERSATIONS.iterdir()):
        if not conv.is_dir():
            continue
        if not CONVERSATION_RE.fullmatch(conv.name):
            continue  # handover-present owns invalid conversation names
        handover = conv / "handover.md"
        if not handover.is_file():
            continue  # handover-present owns the missing record
        rel = handover.relative_to(REPO)
        text = handover.read_text(encoding="utf-8")
        is_new = rel in added
        has_v1 = fields(handover).get("Queue projection", "").strip() == "v1"
        if not has_v1 and not is_new:
            continue  # old records stay immutable; creation-time checks govern new ones
        if not has_v1:
            yield Finding(
                "handover-queue-projection",
                rel,
                "missing exact **Queue projection:** v1 schema marker",
                "add the v1 marker and format Needs your attention from the template",
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
        targets = markdown_link_destinations(body)
        classes = []
        invalid_human_links = []
        projected_human = []
        for target in targets:
            if "message-queue/needs-human/" not in target:
                continue
            matched = HANDOVER_HUMAN_LINK_RE.search(target)
            if matched:
                classes.append(matched.group(1))
                projected_human.append(matched.group(0))
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


def memory_entries():
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
    decisions = MEMORY / "decisions"
    if decisions.is_dir():
        for decision in decisions.rglob("*.md"):
            superseded.update(context_files(fields(decision).get("Supersedes", "")))
    for zone in MEMORY_ZONES:
        entries = [(z, e) for z, e in memory_entries() if z == zone]
        if not entries:
            continue
        lines.append(f"## {zone}")
        for _, entry in entries:
            text = entry.read_text(encoding="utf-8")
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
    if not index.is_file() or index.read_text(encoding="utf-8") != generated_index():
        yield Finding("memory-index", index.relative_to(REPO),
                      "index does not match the memory files",
                      "run: python3 automation/reconcile/reconcile.py --fix-index")


def check_links():
    for md in REPO.rglob("*.md"):
        rel = md.relative_to(REPO)
        parts = rel.parts
        if parts[0] in LINK_SKIP_DIRS or parts[0].startswith("."):
            continue
        if parts[:2] == ("memory", "decisions"):  # immutable records may cite dead paths
            continue
        if parts[:3] == ("message-queue", "needs-agent", "retries"):
            continue  # repair items cite broken/deleted subjects by design
        text = semantic_text(md.read_text(encoding="utf-8"))
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
                if (REPO / cand).exists() or (md.parent / cand).resolve().exists():
                    continue
            except (OSError, ValueError):
                pass
            yield Finding("link-check", rel, f"`{cand}` does not exist",
                          "fix the path, create the target, or unquote if not a path")


def check_agents_budget():
    for md in REPO.rglob("*.md"):
        parts = md.relative_to(REPO).parts
        if parts[0].startswith(".") or parts[0] == "templates":  # schemas, not live contracts
            continue
        lines = len(md.read_text(encoding="utf-8").splitlines())
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
    "queue-boundary": check_active_queue_boundaries,
    "queue-task-reciprocity": check_queue_task_reciprocity,
    "stale-queue": check_stale_queue,
    "task-structure": check_task_structure,
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

def finding_key(f):
    slug = re.sub(r"[^a-z0-9]+", "-", str(f.subject).lower()).strip("-")
    identity = f"{f.check}\0{f.subject}".encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:10]
    base = f"reconcile-{f.check}-{slug}"
    room = 80 - len(digest) - 1
    return f"{base[:room].rstrip('-')}-{digest}"


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
        f"**Check:** {f.check}\n"
        f"**Subject:** `{f.subject}`\n"
        f"**Action:** {retry_action(f)}\n"
        f"**Blocks now:** transition:repository-admission\n\n"
        f"{retry_projection(f)}\n\n"
        "## Agent notes\n\nNone yet.\n"
    )


def reconciler_owned_retry(text):
    got = text_fields(text)
    if got.get("Generated by", "").strip() == RETRY_GENERATOR:
        return True
    filed = got.get("Filed", "")
    legacy_provenance = re.search(r"(?:^|,\s*)by reconciler(?:\s*$|,)", filed)
    return bool(
        legacy_provenance
        and got.get("Check")
        and got.get("Subject")
        and "## Broken invariant" in text
        and "## Fix" in text
    )


def refresh_retry_text(text, finding):
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
    if "Blocks now" not in got:
        additions.append("**Blocks now:** transition:repository-admission")
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
    base = RETRIES / f"blocking-{key}.md"
    existing = [base]
    existing.extend(sorted(RETRIES.glob(f"blocking-{key}-[0-9]*.md")))
    for candidate in existing:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        text = candidate.read_text(encoding="utf-8")
        if reconciler_owned_retry(text) and retry_identity_matches(text, finding):
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
    for f in wanted:
        key = finding_key(f)
        desired = retry_destination(key, f)
        active_paths.add(desired)
        if desired.is_file() and not desired.is_symlink():
            text = desired.read_text(encoding="utf-8")
            if reconciler_owned_retry(text):
                refreshed = refresh_retry_text(text, f)
                if refreshed != text:
                    desired.write_text(refreshed, encoding="utf-8")
            continue  # preserve actor-owned status/notes; refresh only machine projection
        legacy = RETRIES / f"{key}.md"
        if legacy.is_file() and not legacy.is_symlink():
            text = legacy.read_text(encoding="utf-8")
            if reconciler_owned_retry(text):
                desired.write_text(refresh_retry_text(text, f), encoding="utf-8")
                continue
        desired.write_text(retry_text(f), encoding="utf-8")
    removed = 0
    generated = set(RETRIES.glob("blocking-reconcile-*.md"))
    generated.update(RETRIES.glob("reconcile-*.md"))
    for item in generated:
        if item.is_symlink() or not item.is_file():
            continue
        text = item.read_text(encoding="utf-8")
        if not reconciler_owned_retry(text):
            continue
        if item not in active_paths:
            item.unlink()
            removed += 1
    return len(wanted), removed


def main(argv=None):
    global ACTIVE_TASK_ID, ACTIVE_TRANSITIONS, CHANGE_RANGE
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
        help="derive task scope from task/<id>; other branches check only global boundaries",
    )
    parser.add_argument(
        "--range",
        metavar="BASE...HEAD",
        help="Git range used to identify newly added handovers in CI",
    )
    args = parser.parse_args(argv)
    invalid_transitions = [
        transition for transition in args.at_transition
        if not SLUG_RE.fullmatch(transition)
    ]
    if invalid_transitions:
        parser.error("--at-transition values must be lowercase kebab-case")
    if args.range and not GIT_RANGE_RE.fullmatch(args.range):
        parser.error("--range must be full-base-object...full-head-object")
    ACTIVE_TRANSITIONS = set(args.at_transition)
    CHANGE_RANGE = args.range
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
            ACTIVE_TASK_ID = ""  # untracked branch: global boundaries only
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


if __name__ == "__main__":
    sys.exit(main())
