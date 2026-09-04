#!/usr/bin/env python3
"""The reconciler: checks every mechanical harness invariant.

Modes:
  --check         report findings, exit 1 if any (default)
  --file-retries  also write one repair item per check+subject into
                  message-queue/needs-agent/retries/ (idempotent, keyed by
                  full identity) and delete reconciler-filed items whose
                  findings cleared
  --fix-index     regenerate memory/index.md from the memory files
  --fix-open-actions
                  regenerate message-queue/open-actions.md from the queue

Design notes: invariants only (end states, never procedures); stdlib only;
every check no-ops if its folder is absent so adopters can pick pieces.
Registry: CHECKS at the bottom. Adding a check = one function + one entry.
"""
import argparse
import contextlib
import datetime
import hashlib
import html
import re
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath

AUTOMATION = Path(__file__).resolve().parents[1]
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from check_action_projection import (
    LIST_ITEM_RE,
    action_like_rendered_prose,
    copied_prose_without_links,
    parse_task_queue_action_value,
    prose_without_links,
    section_entries,
    task_action_unit_counts,
    task_queue_action_paths_from_text,
    visible_outside_action_sections,
)
from markdown_semantics import (
    MARKDOWN_LINK_RE,
    RAW_HTML_TOKEN_RE,
    commonmark_lines,
    contains_raw_html,
    contains_default_ignorable_characters,
    inline_code_spans,
    markdown_link_destinations,
    markdown_links,
    normalized_action_tokens,
    render_inline_code,
    rendered_human_text,
    semantic_line_offsets,
    semantic_text,
    strip_default_ignorable_characters,
    strip_indented_code,
    strip_inline_code,
    visible_html_text,
)

REPO = Path(__file__).resolve().parents[2]
TODAY = datetime.datetime.now(datetime.timezone.utc).date()

# Every read of a Git object goes through this prefix, so a `refs/replace/*`
# entry cannot substitute a forged commit, tree, or blob for the real one this
# checker was asked about. Only commands that read the index or the worktree,
# or that resolve a location, may be spelled bare — a source-level guard in
# `automation/tests/test_reconcile_queue.py` holds that line.
RAW_GIT = ("git", "--no-replace-objects")

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
    # The unstart edge is load-bearing, not cosmetic. `transition:start` is the
    # only boundary a human item may still bind, and a start gate is only
    # deadlock-free while every review outcome is satisfiable by a commit an
    # agent can make at any time. Two of the four — reject and changes-requested
    # — need the task back in `0_backlog`, which is also what `check_stale_task`
    # has always told an agent to do ("move back to `0_backlog` and unclaim").
    "1_in-progress": {"0_backlog", "2_blocked", "3_in-review"},
    "2_blocked": {"1_in-progress"},
    "3_in-review": {"1_in-progress", "4_done"},
    "4_done": set(),
}
# Merging, moving a task through review, and recording it complete are all
# revertible Git edges, so nothing a human owes may withhold one. A
# `needs-human/` item may bind only `transition:start` on a task still in
# `0_backlog`, or one act with no undo (`operation:<name>`). `needs-agent/` is
# untouched: an agent obligation is discharged by an agent at any time, so an
# agent boundary cannot strand.
HUMAN_UNSPELLABLE_TRANSITIONS = frozenset({"merge", "review", "complete"})
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
_GIT_IGNORED_PREFIX_CACHE = None
_GIT_HEAD_PATHS_CACHE = None
_GIT_HEAD_OID = None
_GIT_ARTIFACT_CACHE = {}
_GIT_BLOB_CACHE = {}
_GIT_CAT_FILE_PROCESS = None
_GIT_RAW_CAT_FILE_PROCESS = None
_GIT_RAW_READER_AVAILABLE = True
_GIT_COMMIT_TREE_CACHE = {}
_GIT_TREE_ENTRIES_CACHE = {}
_GIT_STAGED_PARENTS_CACHE = None
_GIT_STAGED_SIDE_COMMITS_CACHE = None
_GIT_STAGED_SIDE_CREATION_CACHE = {}
_GIT_TREE_PATH_ENTRY_CACHE = {}
_GIT_TREE_BLOB_ENTRY_CACHE = {}
_GIT_REVISION_PARENTS_CACHE = {}
_GIT_ANCESTRY_CACHE = {}
_GIT_MERGE_BASE_CACHE = {}
_GIT_COMMIT_AVAILABLE_CACHE = {}
_GIT_OBJECT_KIND_CACHE = {}
_GIT_REPOSITORY_PATH_CACHE = {}
_GIT_SCHEMA_ACTIVATION_CACHE = {}
_GIT_IMMUTABLE_CACHE_REPO = None
_QUEUE_IDENTITY_CACHE = {}
_TASK_SNAPSHOT_CACHE = {}
_LIVE_QUEUE_PATHS_CACHE = None
_HANDOVER_HISTORY_RECHECK_ACTIVE = False

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
# A task whose folder id is dated on or after this day was filed under the provenance
# grammar — `templates/task/requirements.md`, labelled acceptance criteria, `## Fit` —
# so the blocking `task-provenance` rules apply to it. An older live record receives
# `task-provenance-advice` only: an obligation may not be placed on a committed record
# its author could not have met
# (`memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md`).
TASK_PROVENANCE_SINCE = datetime.date(2026, 9, 4)
# How long an agent-proposed goal may sit in `roadmap/desired-state.md` without the
# owner's confirmation before `roadmap-goals-advice` says so.
UNCONFIRMED_GOAL_DAYS = 30

TASK_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
REPOSITORY_SCOPE_RE = re.compile(r"^(core|records-only|service:[a-z0-9][a-z0-9-]*)$")
# Owner words, labels, and goal fit (`templates/task/requirements.md`,
# `templates/task/task.md`, `templates/roadmap/goal.md`).
ROADMAP_DESIRED_STATE = "roadmap/desired-state.md"
CLARIFICATIONS_PREFIX = "message-queue/needs-human/clarifications/"
DECISIONS_PREFIX = "message-queue/needs-human/decisions/"
# The text of an entry heading after `## `: a date, an em dash, the source.
REQUIREMENTS_ENTRY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) — (\S.*)$")
# Only a backtick fence whose info string is `text`, so a copied template and a
# hand-written entry agree on one shape; a longer fence may hold words with backticks.
REQUIREMENTS_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<fence>`{3,})text[ \t]*$")
NO_OWNER_WORDS_RE = re.compile(r"^No owner words — filed by \S.* from `[^`]+`\.[ \t]*$")
CRITERION_LINE_RE = re.compile(r"^[ \t]*[-*+][ \t]+\[(?: |x|X)\][ \t]+(\S.*?)[ \t]*$")
CRITERION_USER_RE = re.compile(r"^\[user (\d{4}-\d{2}-\d{2})\]")
CRITERION_DERIVED_RE = re.compile(r"^\[derived\]")
FIT_SERVES_GOAL_RE = re.compile(r"^(G\d+) — (\S.*?)[ \t]*$")
FIT_SERVES_NONE_RE = re.compile(r"^none — `([^`]+)`$")
FIT_VALUES = ("aligned", "extends", "conflicts", "unclear")
FIT_REQUIRED_STATUSES = ("1_in-progress", "2_blocked", "3_in-review", "4_done")
PRE_ACTIVATION_ADVICE_STATUSES = ("1_in-progress", "2_blocked")
GOAL_HEADING_RE = re.compile(r"^(G\d+) — (\S.*?)[ \t]*$")
GOAL_CONFIRMED_OWNER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) by owner$")
GOAL_CONFIRMED_NO_RE = re.compile(r"^no — agent-proposed, clarification `([^`]+)`$")
CONVERSATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}[A-Z]{2,5}-[a-z0-9][a-z0-9-]*$")
# Trailing whitespace is presentation, never value: two spaces at end of line are a
# Markdown hard break, which the sanctioned record fold puts on every field line but
# its last. Capturing them would push `"pending  "` and `"______  "` into the parsed
# value, where each reader would have to remember to strip them and `PLACEHOLDER_RE`
# stops matching an unfilled slot. Deciding it once here is inert on the corpus:
# `templates/queue/{decision,clarification,review}.md` are the only tracked files
# whose parsed values change, and they change to what they already meant.
FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z -]*):\*\*[ \t]*(.*?)[ \t]*$", re.M)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
LEADING_DATE_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})(?:,|\s|$)")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TASK_BOUNDARY_RE = re.compile(
    r"^task:(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)$"
)
# The `task:<id>` token a commit message carries. One pattern serves every
# reader, so a commit attributed to a task means the same thing everywhere.
TASK_COMMIT_TAG_RE = re.compile(
    r"(?<![A-Za-z0-9_-])task:\s*"
    r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)"
    r"(?![A-Za-z0-9-])"
)
# The statuses a task may hold at a commit whose work resolves a queue action:
# every status past pickup. `0_backlog` is excluded, so a later claim cannot
# retroactively validate work committed while nobody owned the task.
RESOLVING_TASK_STATUSES = frozenset(
    {"1_in-progress", "2_blocked", "3_in-review", "4_done"}
)
TRANSITION_BOUNDARY_RE = re.compile(r"^transition:([a-z0-9][a-z0-9-]*)$")
EVENT_BOUNDARY_RE = re.compile(r"^event:([a-z0-9][a-z0-9-]*)$")
# An operation is a real act with a real name, and release names carry version dots:
# `operation:release-ios-8.7.0-rc3` is the ordinary case, not an exotic one. Dots are
# admitted inside the name only, so a name still starts and ends on an alphanumeric.
OPERATION_BOUNDARY_RE = re.compile(
    r"^operation:([a-z0-9](?:[a-z0-9.-]*[a-z0-9])?)$"
)
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
    # The fifth cell, and the only one that is a verdict on the *item* rather
    # than on its subject: the reader could not tell from what they were given.
    # Without it "I can't answer this" has to be recorded as one of four things
    # it is not. It adds no new trust assumption — every outcome here is already
    # an attested classification
    # (`memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`)
    # — and it authorizes nothing, because it is not terminal.
    "unanswerable",
}
REVIEW_SUCCESSOR_OUTCOMES = {"changes-requested", "not-approved"}
REVIEW_TERMINAL_OUTCOMES = {"approved", "rejected", "abandoned"}
# Parallel to REVIEW_SUCCESSOR_OUTCOMES: an outcome that withdraws nothing and
# decides nothing, so the question is still owed an answer. `check_stale_queue`
# skips any answered item as "a record awaiting its fold", so without an
# obligation at the deletion edge an unanswerable review would look resolved with
# nobody holding the question — exactly the silent wait AGENTS.md forbids.
REVIEW_REASK_OUTCOMES = {"unanswerable"}
# The two review fields the folding agent supplies, never the human. Keeping them
# out of the human's own commit is what lets a review be answered in one edit
# (`handbook/human-action-guide.md`); `review_terminal_binding_write` bounds when
# and how an agent may fill them.
AGENT_REVIEW_BINDING_FIELDS = ("Reviewed revision", "Review outcome")
GIT_RANGE_RE = re.compile(
    r"^(?:root:(?:[0-9a-f]{40}|[0-9a-f]{64})|"
    r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
    r"\.\.\.(?:[0-9a-f]{40}|[0-9a-f]{64}))$"
)
FULL_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
GIT_TREE_MODE_RE = re.compile(r"[0-7]{5,6}")
# ls-tree prints a six-digit mode and the object kind a raw tree only implies.
LS_TREE_KINDS = {"40000": "tree", "040000": "tree", "160000": "commit"}
UNREAD_TREE_ENTRY = object()  # "ask Git directly", distinct from "absent"
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
# A boundary token is the whole of a dependency-timing claim another item can be
# compared against; the prose standing beside it is presentation, not dependency.
BOUNDARY_TIMING_FIELDS = {
    "blocking": ("Blocks now",),
    "future-blocking": ("Blocks at",),
    "non-blocking": (),
}
# Under the human-attention format a live human item keeps only that token:
# `If you do nothing` above the fold carries the whole unattended outcome, so
# `Until then` and `If unanswered` would be a second answer to one question.
HUMAN_QUEUE_TIMING_FIELDS = BOUNDARY_TIMING_FIELDS
HUMAN_PROJECTION_FIELDS = (
    "Why this matters",
    "If you do nothing",
)
# The pre-rename spelling stays valid forever: a record written under it is a
# record, and reformatting one to match a later presentation would rewrite it.
LEGACY_HUMAN_PROJECTION_FIELDS = (
    "Why-you-might-care",
    "If-you-do-nothing",
)
HUMAN_PROJECTION_FIELD_PAIRS = tuple(
    zip(HUMAN_PROJECTION_FIELDS, LEGACY_HUMAN_PROJECTION_FIELDS)
)
# Exactly these three, and nothing else, stand above the first heading, so the
# top of the file and the notification a human receives are the same artifact.
HUMAN_ABOVE_FOLD_FIELDS = ("Action",) + HUMAN_PROJECTION_FIELDS
HUMAN_CONTEXT_FIELDS = (
    "Today",
    "What this would change",
    "What this does not decide",
)
HUMAN_VERDICT_FIELDS = ("Recommendation", "My working assumption")
HUMAN_COUNTER_CASE_FIELD = "Strongest case against this"
HUMAN_CONFIDENCE_FIELD = "Confidence"
# Machine bookkeeping lives below the answer line. This deny-list is closed and
# is checked against the parsed field set, never against rendered prose.
HUMAN_MACHINE_FIELDS = frozenset({
    "Status", "Filed", "Full context", "Resolution evidence",
    "Review target", "Review revision", "Reviewed revision", "Review outcome",
    "Blocks now", "Blocks at", "Until then", "If unanswered",
    "Answer by", "Re-asked",
    "Supersedes", "Depends on", "Successor action", "Follow-up review",
    "External assignment", "External source", "Request kind",
})
# Dead fields that may not drift back. `Look-at` had six live uses, no template,
# no contract sentence, and no reader; the source is named once in the prose.
BANNED_QUEUE_FIELDS = ("Look-at",)
# 800, and neither the number nor the way it moved is free. Two measurements pointed
# opposite ways and both are kept, because acting on one alone is what produced the
# wrong value twice.
#
#   Raising the ceiling made freshly authored items measurably longer, in words and in
#   rendered lines, with no quality difference that could be told apart from noise.
#   Authors expand into a ceiling. That is real, and it is why the raise is not free.
#
#   But judged against items written without this gate in view, 700 refused work that
#   was not too long: most such items landed above 700 and none above 800, so a 700
#   ceiling mostly refuses complete, competent asks rather than padded ones.
#
# The first says how long authors write; the second says whether the threshold refuses
# good work, and only the second is what a budget is for — so 800 stands. The figures,
# the runs behind them, and the reverted 700 they corrected are recorded in the task
# that set this number, `2026-08-18-fold-the-queue-machine-record`; this comment carries
# the conclusion rather than the evidence, so it cannot drift away from it.
#
# The real repair is not the number: it is that an author could not see the count until
# the gate refused them. `--word-count` prints it on demand and the finding carries it,
# so the threshold is now something a person can check rather than guess at.
HUMAN_ATTENTION_WORD_BUDGET = 800
HUMAN_CHOICES_HEADINGS = ("## Your choices", "## Differences", "## Options")
CHOICE_HEADING_RE = re.compile(r"^###[ \t]+(\S.*?)[ \t]*$", re.M)
# A bare adjective is not a calibration signal: say what was checked and what
# was not, or the grade carries no information.
CONFIDENCE_RE = re.compile(r"^(?:high|medium|low)\s+—\s+\S", re.I)
HUMAN_RESPONSE_LINE_RE = re.compile(
    r"^\*\*(?:Your answer|Your review):\*\*", re.M
)
# The sanctioned fold. These three exact line shapes are the entire raw-HTML
# language a live human item may contain; `templates/README.md` states the nine
# rules once and the emitter below writes them, so nothing asks an author to
# reproduce them by hand.
FOLD_OPEN_RE = re.compile(r"^<details>$")
FOLD_SUMMARY_RE = re.compile(r"^<summary>[^<>]+</summary>$")
FOLD_CLOSE_RE = re.compile(r"^</details>$")
FOLD_SUMMARY_TEXT = (
    "For the record — bookkeeping the reconciler reads. Nothing here needs you."
)
RECORD_HEADING = "## For the record"
DETAILS_OPEN_TOKEN_RE = re.compile(r"<details(?=[\s/>])", re.I)
DETAILS_CLOSE_TOKEN_RE = re.compile(r"</details(?=[\s>])", re.I)
SUMMARY_TOKEN_RE = re.compile(r"</?summary(?=[\s/>])", re.I)
# The container markers a rendered bold label can sit behind, repeated: CommonMark
# nests them freely, so `>> `, `> > `, `- - ` and `2. 1. ` all render the label in
# bold just as one marker does. `1)` is an ordered-list marker too — CommonMark
# accepts both delimiters — and reading only `1.` missed half of them.
RECORD_MARKER_PREFIX = r"(?:[ \t]*(?:>|[-*+][ \t]|\d{1,9}[.)][ \t]))*[ \t]*"
# A line whose *rendered* shape is a bold key, however it is indented, quoted,
# listed or tabled. `FIELD_RE` is anchored at column zero, so every shape this
# accepts and `FIELD_RE` rejects is a field a reader sees and no check can read.
# The optional `|`-run admits a label in any cell of a leading-pipe table row, not
# only the first; a pipeless GFM row is not read, and the docstring on
# `record_swallow_losses` says so rather than implying total coverage.
RECORD_FIELD_SHAPE_RE = re.compile(
    RECORD_MARKER_PREFIX
    + r"(?:\|(?:[^|\n]*\|)*[ \t]*)?"
    r"(?P<field>\*\*(?P<key>[A-Za-z][A-Za-z -]*):\*\*)"
)
# What the emitter is allowed to *harvest* and re-emit at column 0. Deliberately
# narrower than the shape above: a bold label inside a table cell is a cell, and
# promoting it to a machine field would invent a record nobody wrote.
RECORD_FIELD_LINE_RE = re.compile(
    RECORD_MARKER_PREFIX
    + r"(?P<field>\*\*(?P<key>[A-Za-z][A-Za-z -]*):\*\*)"
)
# The fold's own tags, wherever they sit on a line. Removing them is what lets the
# emitter repair the one-line `<details><summary>…</summary>**Status:** …</details>`
# form, whose fields are otherwise unreachable behind a tag at column 0.
FOLD_TOKEN_SPAN_RE = re.compile(
    r"</?details(?:[ \t][^<>]*)?/?>|<summary>[^<>]*</summary>|</?summary[ \t]*/?>",
    re.I,
)
# The sentence the fold's summary replaces, so re-emitting a legacy block does
# not leave it stranded above a summary that now says the same thing.
RECORD_LEGACY_SUMMARY_PROSE = (
    "Bookkeeping the reconciler reads. Nothing here needs you."
)
HTML_COMMENT_SPAN_RE = re.compile(r"<!--.*?-->", re.S)
QUEUE_STATUS_TOKEN_RE = re.compile(
    r"`(awaiting-artifact|waiting|folding|open|in-repair)`"
)
QUEUE_ROOT_DOCUMENT_PATHS = {
    "message-queue/AGENTS.md",
    "message-queue/README.md",
    "message-queue/CLAUDE.md",
    # The generated digest of every live item. It carries no action state of its
    # own, so the location, naming, schema, and staleness checks must read past it
    # rather than report it as a malformed item; `open-actions` is its own check.
    "message-queue/open-actions.md",
}
PLACEHOLDER_RE = re.compile(
    r"^(?:_+|<[^>]*>|tbd|todo|none|n/?a|unknown)$", re.I
)
OPTION_RE = re.compile(r"^### Option(?:\s|$)", re.M)
EXAMPLE_CONSEQUENCE_RE = re.compile(
    r"^\*Example consequence:\*\s*(.+)$", re.M
)
# A decisive source citation carries the source's own words, then the heading
# or bounded source lines that contain them. The check compares those bytes;
# it does not establish whether the source supports the author's judgment.
QUOTE_ELISION_RE = re.compile(r"\s*(?:\[[ \t]*(?:\.\.\.|…)[ \t]*\]|…|\.\.\.)\s*")
# Keep complete quoted literals intact, including triple-delimited bodies with
# embedded short quotes. Escaped delimiters stay in the body; matching triples
# before short delimiters prevents the opener becoming an empty quote pair.
SOURCE_STRING_RE = re.compile(
    r"""(?P<delimiter>"{3}|'{3}|["'])(?:\\.|(?!(?P=delimiter))[^\\])*(?P=delimiter)""", re.S
)
# Continuation additions from Unicode 13.0.0 to 16.0.0 (10,132 code points).
# Generated by comparing alnum + Mn/Mc/Me/Pc/Cf in the Python 3.9 and 3.14
# stdlib databases. Consult only when the runtime calls a character unassigned;
# new symbols must not become identifier continuations merely because Python
# predates them. Update this bounded supplement when advancing Unicode support.
QUOTE_IDENTIFIER_UNICODE16_ADDITIONS = (
    (0x870, 0x887), (0x889, 0x88E), (0x890, 0x891),
    (0x897, 0x89F), (0x8B5, 0x8B5), (0x8C8, 0x8D2),
    (0xC3C, 0xC3C), (0xC5D, 0xC5D), (0xCDD, 0xCDD),
    (0xCF3, 0xCF3), (0xECE, 0xECE), (0x170D, 0x170D),
    (0x1715, 0x1715), (0x171F, 0x171F), (0x180F, 0x180F),
    (0x1AC1, 0x1ACE), (0x1B4C, 0x1B4C), (0x1C89, 0x1C8A),
    (0x1DFA, 0x1DFA), (0x2C2F, 0x2C2F), (0x2C5F, 0x2C5F),
    (0x9FFD, 0x9FFF), (0xA7C0, 0xA7C1), (0xA7CB, 0xA7CD),
    (0xA7D0, 0xA7D1), (0xA7D3, 0xA7D3), (0xA7D5, 0xA7DC),
    (0xA7F2, 0xA7F4), (0x10570, 0x1057A), (0x1057C, 0x1058A),
    (0x1058C, 0x10592), (0x10594, 0x10595), (0x10597, 0x105A1),
    (0x105A3, 0x105B1), (0x105B3, 0x105B9), (0x105BB, 0x105BC),
    (0x105C0, 0x105F3), (0x10780, 0x10785), (0x10787, 0x107B0),
    (0x107B2, 0x107BA), (0x10D40, 0x10D65), (0x10D69, 0x10D6D),
    (0x10D6F, 0x10D85), (0x10EC2, 0x10EC4), (0x10EFC, 0x10EFF),
    (0x10F70, 0x10F85), (0x11070, 0x11075), (0x110C2, 0x110C2),
    (0x1123F, 0x11241), (0x11380, 0x11389), (0x1138B, 0x1138B),
    (0x1138E, 0x1138E), (0x11390, 0x113B5), (0x113B7, 0x113C0),
    (0x113C2, 0x113C2), (0x113C5, 0x113C5), (0x113C7, 0x113CA),
    (0x113CC, 0x113D3), (0x113E1, 0x113E2), (0x116D0, 0x116E3),
    (0x11740, 0x11746), (0x11AB0, 0x11ABF), (0x11BC0, 0x11BE0),
    (0x11BF0, 0x11BF9), (0x11F00, 0x11F10), (0x11F12, 0x11F3A),
    (0x11F3E, 0x11F42), (0x11F50, 0x11F5A), (0x12F90, 0x12FF0),
    (0x1342F, 0x1342F), (0x13439, 0x13455), (0x13460, 0x143FA),
    (0x16100, 0x16139), (0x16A70, 0x16ABE), (0x16AC0, 0x16AC9),
    (0x16D40, 0x16D6C), (0x16D70, 0x16D79), (0x18CFF, 0x18CFF),
    (0x1AFF0, 0x1AFF3), (0x1AFF5, 0x1AFFB), (0x1AFFD, 0x1AFFE),
    (0x1B11F, 0x1B122), (0x1B132, 0x1B132), (0x1B155, 0x1B155),
    (0x1CCF0, 0x1CCF9), (0x1CF00, 0x1CF2D), (0x1CF30, 0x1CF46),
    (0x1D2C0, 0x1D2D3), (0x1DF00, 0x1DF1E), (0x1DF25, 0x1DF2A),
    (0x1E030, 0x1E06D), (0x1E08F, 0x1E08F), (0x1E290, 0x1E2AE),
    (0x1E4D0, 0x1E4F9), (0x1E5D0, 0x1E5FA), (0x1E7E0, 0x1E7E6),
    (0x1E7E8, 0x1E7EB), (0x1E7ED, 0x1E7EE), (0x1E7F0, 0x1E7FE),
    (0x2A6DE, 0x2A6DF), (0x2B735, 0x2B739), (0x2EBF0, 0x2EE5D),
    (0x31350, 0x323AF),
)
# Keep the existing Unicode decimal class, plus its 110 additions after 13.0.
# These are spelling boundaries only; no digit values are converted.
SOURCE_DECIMAL_DIGIT = (
    r"[\d\U00010D40-\U00010D49\U000116D0-\U000116E3\U00011BF0-\U00011BF9"
    r"\U00011F50-\U00011F59\U00016130-\U00016139\U00016AC0-\U00016AC9"
    r"\U00016D70-\U00016D79\U0001CCF0-\U0001CCF9\U0001E4F0-\U0001E4F9"
    r"\U0001E5F1-\U0001E5FA]"
)
# Bounded source-number spellings, not an expression or language parser. A dot
# belongs to a number when fractional digits or an exponent follow it; prose
# "10." can still supply the complete number "10".
SOURCE_NUMBER_RE = re.compile(
    (
        r"[+-]?(?:0[xX](?:_?[0-9a-fA-F](?:_?[0-9a-fA-F])*(?:\.[0-9a-fA-F](?:_?[0-9a-fA-F])*|\.(?=[pP][+-]?\d))?"
        r"|\.[0-9a-fA-F](?:_?[0-9a-fA-F])*)(?:[pP][+-]?\d(?:_?\d)*)?"
        r"|0[bB]_?[01](?:_?[01])*|0[oO]_?[0-7](?:_?[0-7])*"
        r"|(?:\d(?:_?\d)*(?:\.\d(?:_?\d)*|\.(?=[eE][+-]?\d))?|\.\d(?:_?\d)*)(?:[eE][+-]?\d(?:_?\d)*)?)"
    ).replace(r"\d", SOURCE_DECIMAL_DIGIT)
)
# A missing source must be stated explicitly, not inferred from an empty slot.
NO_SOURCE_LITERAL = "No source document — everything you need is above."
# A backticked token shaped like a repository *file*. Backticks render as code, so
# it is not clickable on any surface a human reads an item on. A directory is
# exempt: it has no passage to quote, so a link is the honest form for it.
QUEUE_FILE_TOKEN_RE = re.compile(
    r"^[A-Za-z0-9_.@-]+(?:/[A-Za-z0-9_.@-]+)*\.(?:md|py|txt|json|toml|ya?ml|sh)$"
)
# Everything that opens a new CommonMark block, so the line before it ended where a
# per-line pattern thinks it ended. Anything else following a non-blank line is a
# lazy paragraph continuation: rendered as part of the same value, read by nobody.
# The last alternative is an emphasis label such as `*Example consequence:*`, which
# is not a block start in CommonMark but is the shape this repository's own choices
# put under a paragraph, and treating it as one keeps that shape out of the finding.
BLOCK_START_RE = re.compile(
    r"^(?:"
    r"[ ]{0,3}#{1,6}(?:[ \t]|$)"
    r"|[ ]{0,3}(?:`{3,}|~{3,})"
    r"|[ ]{0,3}<"
    r"|[ ]{0,3}>"
    r"|[ ]{0,3}[-+*](?:[ \t]|$)"
    r"|[ ]{0,3}\d{1,9}[.)](?:[ \t]|$)"
    r"|[ ]{0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})[ \t]*$"
    r"|[ ]{0,3}(?:=+|-+)[ \t]*$"
    r"|[ ]{4,}"
    r"|\|"
    r"|\*[A-Za-z][A-Za-z -]*:\*"
    r")"
)
SECTION_HEADING_RE = re.compile(r"^##[ \t]+(\S.*?)[ \t]*$", re.M)
# Where each queue leaf's own shape is written down. The requirement is read from
# the template at run time rather than copied here, so the schema keeps living in
# exactly one file; a leaf an adopter adds without a template gets no rule, which
# is the same "new typed leaves inherit the actor's generic schema" already in
# `automation/AGENTS.md`.
QUEUE_TEMPLATES = "templates/queue"
# The day `explanation-shape` landed, which is the day an agent request gained a
# section rule at all. An item filed before it was written under a schema that had no
# such rule and keeps that schema; an item filed on or after it is checked, whatever
# field spelling it copied from an older neighbour. The date is what makes the
# agent-side carve-out shrink instead of grow: without it, one human-only field copied
# from the single live legacy request switches the rule off for every new agent item,
# and for an agent request nothing else has ever read its sections at all —
# `check_queue_schema` scopes every section rule behind `if actor != "needs-human"`.
EXPLANATION_SHAPE_ACTIVATION = datetime.date(2026, 8, 2)
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
# Handover action-entry schema versions, oldest first. This namespace versions
# projection *syntax* only; which actions a projection must contain is versioned
# separately below, so the two can move without colliding (history/AGENTS.md).
# A record keeps the grammar it was created under; a newly rejecting expansion
# adds a version instead of retroactively invalidating immutable history.
HANDOVER_ENTRY_VERSIONS = ("v1", "v2", "v3")
HANDOVER_ENTRY_FIELD = "Queue action-entry schema"
# Handover liveness schema versions, oldest first. v1 projects only the
# needs-human actions that still await the human.
HANDOVER_LIVENESS_VERSIONS = ("v1",)
HANDOVER_LIVENESS_FIELD = "Queue liveness schema"
UNRESOLVED_HUMAN_LIVENESS_VERSION = "v1"
# The needs-human status that binds nothing for the human to act on at all.
QUEUE_UNBOUND_HUMAN_STATUS = "awaiting-artifact"
# The needs-human statuses a committed human response resolves.
QUEUE_ANSWERABLE_HUMAN_STATUSES = frozenset({"waiting", "folding"})

RETRY_GENERATOR = "reconcile.py/v1"
RETRY_PROJECTION_START = "<!-- reconcile:projection:start -->"
RETRY_PROJECTION_END = "<!-- reconcile:projection:end -->"

# Link check: backticked or markdown-linked repo paths with >= 2 segments.
BACKTICK_RE = re.compile(r"`([^`\s]+/[^`\s]+)`")
# Anchored: an unanchored "http" or "." also matched `httpd/...` or any dotfile
# path, so a genuinely broken link starting either way silently passed. A leading
# "./" is not skipped: pathlib normalizes it away, so `./handbook/x.md` still
# resolves and checks exactly like `handbook/x.md`. A leading "../" stays skipped
# on purpose: read from the repository root (what the checks below actually do)
# it names a path outside the repository, and Git itself refuses that pathspec —
# `git ls-files -- ../x` fails with "is outside repository", which would abort
# the whole reconciler rather than report one broken link. Resolving it correctly
# needs the citing file's own directory, which no case here currently exercises.
# "tmp/" stays here even though `live_markdown_files` skips git-ignored scratch:
# the two act on different halves of the check. This tuple filters the *cited*
# path, so a doc may name a scratch path it does not expect to resolve; the
# enumeration filter decides which files are *read*.
LINK_SKIP_PREFIXES = ("http://", "https://", "tmp/", "private/", "../")
# "tmp" is not listed here: `live_markdown_files` already excludes git-ignored scratch
# paths, and a tracked file must still be checked even at a path that looks scratch.
LINK_SKIP_DIRS = {"templates", "history"}  # + memory/decisions (records)
# A bare slash also shows up in ordinary prose (`24/7`, `and/or`, `s/foo/bar/`),
# which otherwise matches the same shape as a repository path and reports every
# such sentence as broken. A candidate only counts as a path claim when it either
# names a known file type or starts under an entry that already exists in the
# repository — real paths overwhelmingly satisfy one of the two.
LINK_PATH_EXTENSIONS = {
    ".md", ".py", ".sh", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg",
    ".ini", ".js", ".ts", ".html", ".css",
}


# Advisory findings print with a marker and are counted separately, but never exit 1.
# Two kinds live here. Most report drift the calendar alone can create, so an unchanged
# clean tree must never start failing on a date
# (`handbook/principles/eventual-consistency.md`). `explanation-shape` is the other
# kind: a readability rule whose shape a program can see but whose intent it cannot, so
# it is put in front of the agent that broke it and is never allowed to refuse a commit
# (`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).
# Every other check is blocking.
ADVISORY_CHECKS = {
    "explanation-shape",
    "memory-expiry",
    # A Markdown hard break is unenforceable by any blocking check: an editor that
    # trims trailing whitespace on save strips it, and refusing that commit would
    # refuse the one edit in which a human answers, for which no repair exists.
    # `.gitattributes` removes Git itself as a stripper and `--fix-queue-fold`
    # repairs the rest, so the loss is transient rather than permanent.
    "queue-render",
    "roadmap-fresh",
    # A goal the owner has not confirmed, or a fit copied before a goal moved, is
    # something to put in front of the agent, never a broken invariant.
    "roadmap-goals-advice",
    "stale-queue",
    "stale-task",
    "task-provenance-advice",
}


class Finding:
    def __init__(self, check, subject, message, fix):
        self.check, self.subject, self.message, self.fix = check, subject, message, fix

    @property
    def advisory(self):
        """Whether this reports something to know instead of a broken invariant."""
        return self.check in ADVISORY_CHECKS

    @property
    def severity(self):
        return "advisory" if self.advisory else "blocking"

    def __str__(self):
        return f"[{self.check}] {self.subject}: {self.message}"


class GitSnapshotError(RuntimeError):
    """The exact Git candidate could not be read safely."""


class CheckFailure(RuntimeError):
    """One check could not run to completion, so its result is unknown."""


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


def immutable_revision(revision):
    """Return whether a revision names one exact, unchangeable Git object."""
    return bool(revision) and bool(FULL_GIT_OID_RE.fullmatch(revision))


def scope_immutable_git_caches():
    """Bind the object-ID caches to one repository, dropping a stale scope.

    What a full object ID contains — a tree entry, blob bytes, a parent list,
    an ancestry answer — cannot change while the repository stays the same, so
    those answers are cached for the whole process instead of once per
    reconciler invocation. Another repository need not hold the same objects,
    so switching ``REPO`` (only tests do) discards the cached answers and the
    reader process opened against the old repository.
    """
    global _GIT_IMMUTABLE_CACHE_REPO, _GIT_RAW_READER_AVAILABLE
    scope = str(REPO)
    if scope == _GIT_IMMUTABLE_CACHE_REPO:
        return
    _GIT_IMMUTABLE_CACHE_REPO = scope
    _GIT_RAW_READER_AVAILABLE = True
    _GIT_COMMIT_TREE_CACHE.clear()
    _GIT_TREE_ENTRIES_CACHE.clear()
    _GIT_TREE_BLOB_ENTRY_CACHE.clear()
    _GIT_ANCESTRY_CACHE.clear()
    _GIT_MERGE_BASE_CACHE.clear()
    _GIT_COMMIT_AVAILABLE_CACHE.clear()
    _GIT_OBJECT_KIND_CACHE.clear()
    _GIT_REPOSITORY_PATH_CACHE.clear()
    _GIT_TREE_PATH_ENTRY_CACHE.clear()
    _GIT_REVISION_PARENTS_CACHE.clear()
    _GIT_SCHEMA_ACTIVATION_CACHE.clear()
    _GIT_BLOB_CACHE.clear()
    _QUEUE_IDENTITY_CACHE.clear()
    close_git_cat_file()


def start_git_snapshot_cache():
    """Reuse one immutable index/HEAD view during a reconciler invocation."""
    global _GIT_SNAPSHOT_CACHE_ACTIVE
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE, _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    global _GIT_IGNORED_PREFIX_CACHE
    global _GIT_ARTIFACT_CACHE, _GIT_BLOB_CACHE
    global _GIT_STAGED_PARENTS_CACHE, _GIT_STAGED_SIDE_COMMITS_CACHE
    global _GIT_STAGED_SIDE_CREATION_CACHE, _GIT_TREE_PATH_ENTRY_CACHE
    global _GIT_REVISION_PARENTS_CACHE, _GIT_SCHEMA_ACTIVATION_CACHE
    global _TASK_SNAPSHOT_CACHE, _LIVE_QUEUE_PATHS_CACHE
    close_git_cat_file()
    _GIT_SNAPSHOT_CACHE_ACTIVE = True
    _GIT_INDEX_CACHE = None
    _GIT_INDEX_OID_CACHE = None
    _GIT_INDEX_ALL_PATHS_CACHE = None
    _GIT_IGNORED_PREFIX_CACHE = None
    _GIT_HEAD_PATHS_CACHE = None
    _GIT_HEAD_OID = None
    _GIT_ARTIFACT_CACHE = {}
    _GIT_BLOB_CACHE = {}
    _GIT_STAGED_PARENTS_CACHE = None
    _GIT_STAGED_SIDE_COMMITS_CACHE = None
    _GIT_STAGED_SIDE_CREATION_CACHE = {}
    _GIT_TREE_PATH_ENTRY_CACHE = {}
    _GIT_REVISION_PARENTS_CACHE = {}
    _GIT_SCHEMA_ACTIVATION_CACHE = {}
    _TASK_SNAPSHOT_CACHE = {}
    _LIVE_QUEUE_PATHS_CACHE = None
    load_git_index_snapshot()
    load_git_head_snapshot()
    load_git_ignored_snapshot()


def stop_git_snapshot_cache():
    """Drop invocation-local Git data so callers can safely mutate the index."""
    global _GIT_SNAPSHOT_CACHE_ACTIVE
    global _GIT_INDEX_CACHE, _GIT_INDEX_OID_CACHE
    global _GIT_INDEX_ALL_PATHS_CACHE, _GIT_HEAD_PATHS_CACHE, _GIT_HEAD_OID
    global _GIT_IGNORED_PREFIX_CACHE
    global _GIT_ARTIFACT_CACHE, _GIT_BLOB_CACHE
    global _GIT_STAGED_PARENTS_CACHE, _GIT_STAGED_SIDE_COMMITS_CACHE
    global _GIT_STAGED_SIDE_CREATION_CACHE, _GIT_TREE_PATH_ENTRY_CACHE
    global _GIT_REVISION_PARENTS_CACHE, _GIT_SCHEMA_ACTIVATION_CACHE
    global _TASK_SNAPSHOT_CACHE, _LIVE_QUEUE_PATHS_CACHE
    close_git_cat_file()
    _GIT_SNAPSHOT_CACHE_ACTIVE = False
    _GIT_INDEX_CACHE = None
    _GIT_INDEX_OID_CACHE = None
    _GIT_INDEX_ALL_PATHS_CACHE = None
    _GIT_IGNORED_PREFIX_CACHE = None
    _GIT_HEAD_PATHS_CACHE = None
    _GIT_HEAD_OID = None
    _GIT_ARTIFACT_CACHE = {}
    _GIT_BLOB_CACHE = {}
    _GIT_STAGED_PARENTS_CACHE = None
    _GIT_STAGED_SIDE_COMMITS_CACHE = None
    _GIT_STAGED_SIDE_CREATION_CACHE = {}
    _GIT_TREE_PATH_ENTRY_CACHE = {}
    _GIT_REVISION_PARENTS_CACHE = {}
    _GIT_SCHEMA_ACTIVATION_CACHE = {}
    _TASK_SNAPSHOT_CACHE = {}
    _LIVE_QUEUE_PATHS_CACHE = None


def close_git_cat_file():
    """Close every reusable cat-file reader this process holds open."""
    global _GIT_CAT_FILE_PROCESS, _GIT_RAW_CAT_FILE_PROCESS
    process = _GIT_CAT_FILE_PROCESS
    raw = _GIT_RAW_CAT_FILE_PROCESS
    _GIT_CAT_FILE_PROCESS = None
    _GIT_RAW_CAT_FILE_PROCESS = None
    close_git_reader(process)
    close_git_reader(raw)


def close_git_reader(process):
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


def parse_git_tree_blob_records(data):
    """Return path-to-(mode, object) blob entries from NUL-delimited ls-tree output."""
    entries = {}
    for record in data.split(b"\0"):
        metadata, separator, encoded_name = record.partition(b"\t")
        if not separator:
            continue
        parts = metadata.decode("ascii", errors="replace").split()
        if len(parts) != 3:
            continue
        mode, kind, oid = parts
        if kind != "blob":
            continue
        name = encoded_name.decode("utf-8", errors="surrogateescape")
        entries[name] = (mode, oid)
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
        [*RAW_GIT, "ls-tree", "-r", "--name-only", "-z", _GIT_HEAD_OID],
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


def compute_git_ignored_prefixes():
    """Return every Git-ignored path in the working tree, in one process call.

    ``--directory`` collapses a wholly-ignored directory (``tmp/``) to one entry
    instead of recursing into it — a stray scratch clone can be thousands of files —
    and still lists individual ignored files living inside an otherwise-tracked
    directory. Entries ending in ``/`` are directory prefixes; the rest are exact
    files.
    """
    if not (REPO / ".git").exists():
        return set()
    result = subprocess.run(
        [
            "git", "ls-files", "--others", "--ignored", "--exclude-standard",
            "--directory", "-z",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, "could not list Git-ignored paths"
        ))
    return {
        name.decode("utf-8", errors="surrogateescape")
        for name in result.stdout.split(b"\0")
        if name
    }


def load_git_ignored_snapshot():
    """Capture the ignored-path prefixes once per reconciler invocation."""
    global _GIT_IGNORED_PREFIX_CACHE
    if _GIT_IGNORED_PREFIX_CACHE is not None:
        return
    _GIT_IGNORED_PREFIX_CACHE = compute_git_ignored_prefixes()


def git_ignored_prefixes():
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        load_git_ignored_snapshot()
        return _GIT_IGNORED_PREFIX_CACHE
    return compute_git_ignored_prefixes()


def path_is_git_ignored(rel_posix):
    """Whether an untracked working-tree path is Git-ignored.

    Scratch discipline (root ``AGENTS.md``) puts throwaway files under git-ignored
    `tmp/`; the reconciler's untracked-file scans must not report findings for them.
    Only call this for a path already known to be untracked (not in the Git index or
    HEAD) — a *tracked* file must still be checked even if it also matches an ignore
    rule, and this predicate never runs against the index/HEAD halves of any check.
    """
    for prefix in git_ignored_prefixes():
        if prefix.endswith("/"):
            if rel_posix == prefix[:-1] or rel_posix.startswith(prefix):
                return True
        elif rel_posix == prefix:
            return True
    return False


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


def git_index_entry_mode(relative):
    """Return one exact candidate index mode without scanning the whole index.

    `git_index_entries` answers "what is under this prefix", so asking it about a
    single file filtered every captured path to reach one dictionary key. The
    captured index is already keyed by path, so an exact question is a lookup.
    """
    if not (REPO / ".git").exists():
        return None
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        return _GIT_INDEX_CACHE.get(relative)
    mode, _oid = git_index_path_entry(relative)
    return mode


def git_index_path_entry(path):
    """Return one exact staged (mode, object) pair from a single index query."""
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
    modes, oids, _ = parse_git_index_records(result.stdout)
    return modes.get(path), oids.get(path)


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
        prefix = prefix.rstrip("/")
        if prefix in ("", "."):
            return set(_GIT_HEAD_PATHS_CACHE)
        return {
            name for name in _GIT_HEAD_PATHS_CACHE
            if name == prefix or name.startswith(prefix + "/")
        }
    result = subprocess.run(
        [*RAW_GIT, "ls-tree", "-r", "--name-only", "HEAD", "--", prefix],
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
        returncode, detail = git_commit_available(revision)
        if returncode:
            raise GitSnapshotError(
                detail or f"--range {label} is not an available commit"
            )
    if base is not None:
        returncode, common, detail = git_merge_base_result(base, range_head)
        if returncode or not common.strip():
            raise GitSnapshotError(
                detail.strip() or "--range base and head have no merge base"
            )
    if _GIT_HEAD_OID != range_head:
        ancestry = subprocess.run(
            [*RAW_GIT, "rev-list", "--parents", "-n", "1", _GIT_HEAD_OID],
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
        [*RAW_GIT, "diff-index", "--cached", "--quiet", _GIT_HEAD_OID, "--"],
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
    returncode, detail = git_commit_available(displaced_tip)
    if returncode:
        raise GitSnapshotError(
            detail or "--displaced-tip is not an available commit"
        )
    returncode, _common, detail = git_merge_base_result(
        displaced_tip, range_head
    )
    if returncode:
        raise GitSnapshotError(
            detail.strip()
            or "--displaced-tip and --range head have no merge base"
        )


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
            if name in seen or name in committed:
                continue
            if path_is_git_ignored(name):
                continue
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
        if name in seen or name in committed:
            continue
        if path_is_git_ignored(name):
            continue
        yield path


def readable_queue_item(item):
    """Queue state must be stored in a repository-local regular file."""
    mode = git_index_entry_mode(item.relative_to(REPO).as_posix())
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


def human_header_block(text):
    """Return the source between the title and the first section heading."""
    clean = semantic_text(text)
    title = re.search(r"^#[ \t]+\S.*$", clean, flags=re.M)
    start = title.end() if title else 0
    heading = re.search(r"^##(?:\s|$)", clean[start:], flags=re.M)
    end = start + heading.start() if heading else len(clean)
    return clean[start:end]


def human_response_line_offset(clean):
    """Return where the answer line starts, or None when it is absent."""
    matched = HUMAN_RESPONSE_LINE_RE.search(clean)
    return matched.start() if matched else None


def human_attention_above_fold(text):
    """Return the visible source a human reads before the answer line."""
    clean = semantic_text(text)
    offset = human_response_line_offset(clean)
    return clean if offset is None else clean[:offset]


# ------------------------------------------- the record region and its fold

def blank_html_comments(view):
    """Blank HTML comments in a visible-HTML view, preserving line positions.

    `visible_html_text` deliberately keeps a line-initial `<!-- … -->` block
    standing, because `contains_raw_html` has to see one. Everything reading the
    *record* wants the opposite: `templates/README.md` makes an HTML comment the
    declared home of optional-field documentation, so a `**Key:**` written inside
    one is documentation and is not a field anybody lost. Mid-line comments are
    already blanked upstream, so the only spans left here start a line.
    """
    def spaces(value):
        return "".join(
            character if character == "\n" else " " for character in value
        )

    blanked = HTML_COMMENT_SPAN_RE.sub(lambda m: spaces(m.group()), view)
    unclosed = blanked.find("<!--")
    if unclosed < 0:
        return blanked
    # An unterminated comment runs to end of file, exactly as `_semantic_text`
    # treats one.
    return blanked[:unclosed] + spaces(blanked[unclosed:])


def record_visible_lines(text):
    """Return the lines a reader sees, minus code and HTML comments.

    Positional: index *i* here is line *i* of the source, of `semantic_text`, and
    of the raw file. That is what lets a check ask "this line renders as a field —
    does any check read it as one?" without parsing the document twice.

    Indented code is blanked here, exactly as `semantic_text` blanks it, because the
    question this view answers is what a reader is *shown*. GitHub renders a
    four-space-indented `**Filed:** …` as `<pre><code>` with two literal asterisks,
    which is a code sample and not a bold label. `visible_html_text` keeps it
    standing — that view exists to reason about markup, where an unread tag must
    still be seen — and the disagreement between the two is not a special case to
    exempt: it was one blocking false positive in `record-swallow` and one real
    corruption in the emitter, which promoted the sample to a column-0 field the
    reconciler then enforced. Both close by reading the same view `FIELD_RE` reads.
    """
    return blank_html_comments(
        strip_indented_code(visible_html_text(text))
    ).splitlines()


def record_region_lines(text):
    """Return the line indices where a queue item's machine record may live.

    The region is every line above the first `## ` heading, plus every line at or
    below the answer line. Nothing else: prose lives strictly between them, and no
    check in this file looks there.

    This is the whole reason the visibility rule can block. Scoping it by key name
    is impossible — `Status`, `Action`, `Check`, `Subject` and `Today` are declared
    field names *and* ordinary English words, with dozens of legitimate in-tree
    uses as bold labels inside a choice, a table cell or a blockquote. Position is
    decidable where the name is not.

    An item with no answer line — every `needs-agent` item, by design — has only
    the first half. The narrative fields that fall outside the region are not
    unprotected: `check_human_attention` and `check_queue_schema` require each of
    them to be *present and concrete*, which fails from the other direction the
    moment one is indented into invisibility.
    """
    clean = semantic_text(text)
    lines = clean.splitlines()
    region = set()
    heading = next(
        (
            index for index, line in enumerate(lines)
            if re.match(r"^##[ \t]", line)
        ),
        None,
    )
    region.update(range(len(lines) if heading is None else heading))
    offset = human_response_line_offset(clean)
    if offset is not None:
        region.update(range(clean.count("\n", 0, offset), len(lines)))
    return region


def record_region_is_truncated(text):
    """Whether the record region lost its lower half to an unreadable answer line.

    The region is "above the first `## `" plus "at or below the answer line". When
    `HUMAN_RESPONSE_LINE_RE` finds nothing — the line fenced, indented, commented
    out, or simply absent — the second half is empty and `## For the record` stops
    being checked at all. Growing the region to the whole file instead would police
    prose and reintroduce the false positives position scoping exists to remove, so
    the region still collapses; what may not happen is that it collapses *quietly*.
    Silent scope collapse is the failure class this check was written to end, and a
    check that goes blind without saying so is an instance of it.
    """
    return human_response_line_offset(semantic_text(text)) is None


def record_swallow_losses(text):
    """Return `(line number, key)` for every record field no check can read.

    Reads the same views `FIELD_RE` and a browser read, so what it reports is a
    disagreement between them rather than the presence of a construct. A bold label
    in a leading-pipe table row is read in any cell; a GFM row written without its
    outer pipes is not, and that limit is stated rather than implied.
    """
    visible = record_visible_lines(text)
    parsed = semantic_text(text).splitlines()
    losses = []
    for index in sorted(record_region_lines(text)):
        if index >= len(visible) or index >= len(parsed):
            continue
        shown = RECORD_FIELD_SHAPE_RE.match(visible[index])
        if shown is None:
            continue
        read = FIELD_RE.match(parsed[index])
        if read is not None and read.group(1) == shown.group("key"):
            continue
        losses.append((index + 1, shown.group("key")))
    return losses


def field_value_continuations(text):
    """Return `(line number, key)` for values that run past the line a check reads.

    `FIELD_RE` and `EXAMPLE_CONSEQUENCE_RE` are per-line patterns, so a value
    written as ordinary wrapped prose — which is how every style guide, this
    repository's included, teaches a person to write a paragraph — is parsed only as
    far as its first newline. CommonMark makes the next line a lazy continuation of
    the same paragraph, so the reader sees one sentence and the checker sees its
    first half: `Recommendation` can name a choice on the second line and the rule
    that it must name a shown choice never sees the name. Nothing rendered says the
    rest went missing, which is what puts this in the blocking tier rather than the
    advisory one.

    Only a genuine lazy continuation counts. A blank line, another field, a heading,
    a fence, a list marker, a quote, a table row, indented code, a thematic break, a
    setext underline and an emphasis label all open a new block, so the value ended
    where the checker thinks it ended and nothing was lost.

    The human's own response line is exempt, for the same reason it is exempt from
    the frozen-skeleton value rule: a person may wrap their sentence, their answer
    commit is immutable, and there would be no repair.
    """
    lines = semantic_text(text).splitlines()
    found = []
    for index, line in enumerate(lines):
        stripped = line.rstrip()
        matched = FIELD_RE.fullmatch(stripped)
        key = matched.group(1) if matched else None
        if matched is None:
            matched = EXAMPLE_CONSEQUENCE_RE.fullmatch(stripped)
            key = "Example consequence" if matched else None
        if matched is None or index + 1 >= len(lines):
            continue
        if HUMAN_RESPONSE_LINE_RE.match(stripped):
            continue
        following = lines[index + 1]
        if not following.strip() or FIELD_RE.match(following) \
                or BLOCK_START_RE.match(following):
            continue
        found.append((index + 2, key))
    return found


def fold_bounds(lines):
    """Return the `(open, close)` line indices of the one fold, or None."""
    opens = [
        index for index, line in enumerate(lines)
        if DETAILS_OPEN_TOKEN_RE.search(line)
    ]
    closes = [
        index for index, line in enumerate(lines)
        if DETAILS_CLOSE_TOKEN_RE.search(line)
    ]
    if len(opens) != 1 or len(closes) != 1 or closes[0] < opens[0]:
        return None
    return opens[0], closes[0]


def fold_shape_problems(text):
    """Return every way one item's fold departs from the canonical block.

    Two of these are the swallow points. A missing blank line after `</summary>`
    keeps the HTML block open, so `semantic_text` blanks every field below it and
    the record silently becomes empty; `</details>` is itself a CommonMark type-6
    start tag, so a field on the line straight after it is swallowed the same way.
    Neither is a style rule, and both are why this check blocks.
    """
    lines = record_visible_lines(text)
    opens = [
        index for index, line in enumerate(lines)
        if DETAILS_OPEN_TOKEN_RE.search(line)
    ]
    closes = [
        index for index, line in enumerate(lines)
        if DETAILS_CLOSE_TOKEN_RE.search(line)
    ]
    if not opens and not closes:
        return []
    problems = []
    if len(opens) != len(closes):
        problems.append("every `<details>` needs exactly one `</details>`")
    if len(opens) > 1 or len(closes) > 1:
        problems.append(
            "an item carries at most one fold, and it holds `## For the record`"
        )
    bounds = fold_bounds(lines)
    if bounds is None:
        if len(opens) == len(closes) == 1 and closes[0] < opens[0]:
            problems.append("`</details>` must follow its `<details>` opener")
        return problems
    opening, closing = bounds
    if lines[opening] != "<details>":
        problems.append(
            "the fold must open with `<details>` alone on its own line at "
            "column 0, with no attributes"
        )
    summary = lines[opening + 1] if opening + 1 < len(lines) else ""
    if not FOLD_SUMMARY_RE.match(summary):
        problems.append(
            "`<summary>…</summary>` must be the very next line, at column 0, "
            "with no nested tags"
        )
    elif opening + 2 >= closing:
        problems.append("the fold holds no field")
    else:
        if lines[opening + 2].strip():
            problems.append(
                "a blank line must follow `</summary>`, or every field below "
                "it is erased from the record"
            )
        elif opening + 3 < closing and not lines[opening + 3].strip():
            problems.append("exactly one blank line follows `</summary>`")
    if SUMMARY_TOKEN_RE.search(
        "\n".join(lines[:opening + 1] + lines[opening + 2:])
    ):
        problems.append("`<summary>` may appear only on the fold's second line")
    if lines[closing] != "</details>":
        problems.append(
            "the fold must close with `</details>` alone on its own line at "
            "column 0"
        )
    if closing - 1 > opening and lines[closing - 1].strip():
        problems.append("exactly one blank line must precede `</details>`")
    elif closing - 2 > opening + 1 and not lines[closing - 2].strip():
        problems.append("exactly one blank line precedes `</details>`")
    if any(line.strip() for line in lines[closing + 1:]) \
            and lines[closing + 1].strip():
        problems.append(
            "a blank line must follow `</details>`; `</details>` opens an HTML "
            "block of its own, so the line after it is erased too"
        )
    answer = next(
        (
            index for index, line in enumerate(lines)
            if HUMAN_RESPONSE_LINE_RE.match(line)
        ),
        None,
    )
    if answer is not None and opening <= answer <= closing:
        problems.append(
            "the answer line is inside the fold — the one line the reader must "
            "fill in may never be folded away"
        )
    elif answer is not None and opening < answer:
        problems.append(
            "the fold sits above the answer line; machine bookkeeping belongs "
            "under `## For the record`, below the line you answer on"
        )
    return problems


def unsanctioned_raw_html(text):
    """Whether raw HTML other than the sanctioned fold is present.

    This is `contains_raw_html` with exactly three anchored line shapes
    subtracted, computed over the same view, so it rejects everything the blanket
    ban rejected except a well-formed fold. Subtracting lines can only remove
    matches, which is what makes the narrowing a strict restriction rather than a
    weakening. Indentation is fatal to admission: ` <details>` is not the
    sanctioned form and falls straight through to rejection.
    """
    residual = []
    for line in visible_html_text(text).splitlines():
        stripped = line.strip()
        sanctioned = line == stripped and (
            FOLD_OPEN_RE.match(stripped)
            or FOLD_CLOSE_RE.match(stripped)
            or FOLD_SUMMARY_RE.match(stripped)
        )
        residual.append("" if sanctioned else line)
    return bool(RAW_HTML_TOKEN_RE.search("\n".join(residual)))


def hidden_from_the_reader(text):
    """Return the parsed fields, headings and choices a reader never sees.

    `<details>` folds; `display:none`, `hidden` and `aria-hidden` hide. The
    difference is the whole safety argument for admitting the first, so it is
    verified rather than assumed: everything a check obeys must also appear in the
    view that models what a browser paints.

    Two rendered views are consulted and something counts as hidden only when it
    is missing from both. `rendered_human_text` reads its input as HTML without
    removing code spans first, so a repository path written as `` `<head>` `` is
    parsed as a real `<head>` tag and blanks the rest of the document — 5 tracked
    files do exactly that today. Blanking code spans removes that misreading and
    introduces the opposite one, on a heading whose whole label is backticked.
    Requiring both views to agree keeps every real hide, because a `display:none`
    wrapper hides its content in both, while neither misreading can survive the
    other view.
    """
    painted = rendered_human_text(text)
    uncoded = rendered_human_text(strip_inline_code(text))
    clean = semantic_text(text)

    def hidden(needle):
        return needle not in painted and strip_inline_code(needle) not in uncoded

    fields_hidden = sorted({
        key for key, _value in FIELD_RE.findall(clean)
        if hidden(f"**{key}:**")
    })
    headings_hidden = [
        heading for heading in SECTION_HEADING_RE.findall(clean)
        if hidden(heading)
    ]
    choices_hidden = [
        " ".join(choice.split())
        for choice in CHOICE_HEADING_RE.findall(clean)
        if hidden(" ".join(choice.split()))
    ]
    return fields_hidden, headings_hidden, choices_hidden


def folded_record_block(field_lines):
    """Return the canonical fold, byte-exactly, around one run of fields.

    Every field line but the last ends in two spaces. That is a Markdown hard
    break, and inside a *collapsed* fold it costs no rendered height at all: a
    closed `<details>` paints only its summary. Applied to a visible block it does
    the opposite — N hard-broken lines wrap to the sum of their own wraps, which
    is never less than one run-on paragraph's — which is why nothing outside a
    fold ever gets them.
    """
    body = [
        line + ("  " if index + 1 < len(field_lines) else "")
        for index, line in enumerate(field_lines)
    ]
    return [
        "<details>",
        f"<summary>{FOLD_SUMMARY_TEXT}</summary>",
        "",
        *body,
        "",
        "</details>",
    ]


def refolded_record_text(text):
    """Return one queue document with its record block re-emitted canonically.

    Fence-, comment- and indented-code-aware by construction: it reads the record
    section through `record_visible_lines`, so a template quoted inside a fenced
    example, the optional-field documentation inside an HTML comment, and a code
    sample indented four spaces are carried through untouched rather than harvested
    into fields the reconciler would then enforce. Every malformed shape an agent
    can plausibly produce — no blank line after `</summary>`, no `<summary>` at all,
    `<details open>`, the one-line `<details><summary>…</summary>…</details>`, fields
    indented or written as list items, no fold whatsoever — converges here to the
    same bytes, so running it twice is a no-op and running it once loses nothing.

    **The answer line is never harvested.** It matches the bold-key shape like any
    other line, and folding it away hides the one line the reader must fill in
    behind a collapsed disclosure — a state `fold_shape_problems` calls the worst in
    the set and this function could not undo. It is carried, never folded, and
    `fix_queue_fold` additionally refuses to write any result that is still
    malformed, so following a finding's advice can no longer make an item worse.
    """
    lines = text.splitlines()
    visible = record_visible_lines(text)
    # Both boundaries are read from the fence- and comment-blanked view, so a
    # `## For the record` quoted inside a fenced example is neither mistaken for
    # the real section nor allowed to end it early.
    heading = next(
        (
            index for index, line in enumerate(visible)
            if line.rstrip() == RECORD_HEADING
        ),
        None,
    )
    if heading is None:
        return text
    end = next(
        (
            index for index in range(heading + 1, len(visible))
            if re.match(r"^##[ \t]", visible[index])
        ),
        len(lines),
    )
    fields = []
    carried = []
    for index in range(heading + 1, end):
        line = lines[index]
        if not line.strip():
            continue
        inert = index >= len(visible) or not visible[index].strip()
        if not inert and not HUMAN_RESPONSE_LINE_RE.match(line):
            # The one-line fold hides its fields behind a tag at column 0. Removing
            # the fold's own tags first is what lets that shape converge with every
            # other; a line that holds nothing else is scaffolding and is dropped.
            candidate = line
            if DETAILS_OPEN_TOKEN_RE.search(line) \
                    or DETAILS_CLOSE_TOKEN_RE.search(line) \
                    or SUMMARY_TOKEN_RE.search(line):
                candidate = FOLD_TOKEN_SPAN_RE.sub("", line).strip()
                if not candidate:
                    continue
            matched = RECORD_FIELD_LINE_RE.match(candidate)
            if matched is not None:
                fields.append(candidate[matched.start("field"):].rstrip())
                continue
            if DETAILS_OPEN_TOKEN_RE.search(line) \
                    or DETAILS_CLOSE_TOKEN_RE.search(line) \
                    or SUMMARY_TOKEN_RE.search(line) \
                    or line.strip() == RECORD_LEGACY_SUMMARY_PROSE \
                    or line.strip() == f"<summary>{FOLD_SUMMARY_TEXT}</summary>":
                continue
        carried.append(index)
    if not fields:
        return text
    block = [RECORD_HEADING, "", *folded_record_block(fields)]
    if carried:
        consumed = set(range(heading + 1, end)) - set(carried)
        block.append("")
        block.extend(
            lines[index]
            for index in range(min(carried), max(carried) + 1)
            if index not in consumed or not lines[index].strip()
        )
    if end < len(lines):
        block.append("")
    rebuilt = lines[:heading] + block + lines[end:]
    return "\n".join(rebuilt) + ("\n" if text.endswith("\n") else "")


def queue_fold_targets(explicit=()):
    """Return the files `--fix-queue-fold` rewrites.

    With no path given it rewrites the three human templates and every live human
    item that *already* carries a fold. It never introduces one into a live item
    that has none, because folding a live item changes `queue_action_identity`
    and `queue_mutation_problem` refuses that; re-emitting an existing fold is
    `rstrip`-invariant and therefore always legal, which is what makes the
    self-healing loop for a stripped hard break safe to run at any time.
    """
    if explicit:
        return [REPO / Path(path) for path in explicit]
    targets = [
        REPO / QUEUE_TEMPLATES / name
        for name in ("decision.md", "clarification.md", "review.md")
    ]
    for item in live_queue_items() or ():
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] != "needs-human":
            continue
        if DETAILS_OPEN_TOKEN_RE.search(visible_html_text(repo_text(item))):
            targets.append(item)
    return targets


def word_count_targets(explicit=()):
    """Return the files `--word-count` measures.

    With no path given: the three human templates, so an author can see what the
    empty shape already costs, and every live human item the current template
    governs, which is exactly the set `human-attention` counts. A path given
    explicitly is measured whether or not it is committed, tracked, or governed —
    the whole point is to answer "how am I doing" *before* the commit that would
    otherwise be the first place the number appears.
    """
    if explicit:
        return [REPO / Path(path) for path in explicit]
    targets = [
        REPO / QUEUE_TEMPLATES / name
        for name in ("decision.md", "clarification.md", "review.md")
    ]
    for item in live_queue_items() or ():
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] != "needs-human":
            continue
        text = repo_text(item)
        if human_attention_format_applies(parts[0], text):
            targets.append(item)
    return targets


def word_count_report(explicit=()):
    """Return one `(name, words, over)` row per target, in the order measured.

    The budget is the format's only threshold an author cannot see by reading their
    own file, and a held-out authoring run named that as one of two ambiguities that
    mattered: seven of ten items breached a ceiling nothing had shown them. A number
    a person can only discover by being refused is a wish, not a harness. This is the
    counter — it writes nothing, and it is deliberately not a check, because a count
    is information and only the ceiling is a rule.
    """
    rows = []
    for path in word_count_targets(explicit):
        if not path.is_file():
            continue
        try:
            name = path.relative_to(REPO).as_posix()
        except ValueError:
            name = path.as_posix()
        words = len(human_attention_above_fold(
            path.read_text(encoding="utf-8")
        ).split())
        rows.append((name, words, max(0, words - HUMAN_ATTENTION_WORD_BUDGET)))
    return rows


def fix_queue_fold(explicit=()):
    """Re-emit the canonical record fold; return what changed and what it refused.

    Returns `(changed, refused)`, where `refused` maps a path to the problems that
    would still stand after the rewrite. **Nothing is written unless the result is
    clean.** Three findings name this command and it cannot repair any of them —
    a fold above the answer line, a fold containing it, and (until the one-line form
    was taught) a shape with no harvestable field. A fixer that half-repairs one of
    those turns a one-line misplacement into a stuck item, and the last state is the
    one no rule can undo. Refusing out loud, naming what is wrong and leaving the
    bytes alone, is the only behaviour a weak model can follow without losing the
    owner's question.
    """
    changed = []
    refused = {}
    for path in queue_fold_targets(explicit):
        if not path.is_file():
            continue
        name = path.relative_to(REPO).as_posix()
        before = path.read_text(encoding="utf-8")
        after = refolded_record_text(before)
        problems = fold_shape_problems(after) + [
            f"line {line} renders as **{key}:** and no check reads it"
            for line, key in record_swallow_losses(after)
        ]
        if problems:
            refused[name] = problems
            continue
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed.append(name)
    return changed, refused


def unbroken_fold_field_lines(text):
    """Return the line numbers inside a fold that lost their Markdown hard break.

    Advisory forever, and this says why rather than pretending otherwise: an
    editor that trims trailing whitespace on save strips these, and blocking that
    would refuse the one-edit commit in which the owner answers. `.gitattributes`
    removes the most common stripper — Git's own `core.whitespace` — and
    `--fix-queue-fold` repairs the rest in one command, so a strip is a transient
    regression rather than permanent damage.
    """
    lines = text.splitlines()
    bounds = fold_bounds(record_visible_lines(text))
    if bounds is None:
        return []
    opening, closing = bounds
    unbroken = []
    for index in range(opening + 1, closing - 1):
        if index + 1 >= len(lines):
            break
        if not FIELD_RE.match(lines[index].rstrip()) \
                or not FIELD_RE.match(lines[index + 1].rstrip()):
            continue
        trailing = lines[index][len(lines[index].rstrip()):]
        if trailing != "  ":
            unbroken.append(index + 1)
    return unbroken


def human_choices_body(clean):
    """Return the choices source, joining every accepted heading alias.

    `templates/queue/decision.md` split the axis (`## Differences`) from the list
    (`## Options`), so counting under one heading alone would reject every legacy
    decision item. The union accepts both the old two-heading shape and the new
    single `## Your choices`.
    """
    bodies = []
    for heading in HUMAN_CHOICES_HEADINGS:
        body = level_two_section_body(clean, heading)
        if body is not None:
            bodies.append(body)
    return "\n\n".join(bodies) if bodies else None


def choice_sections(body):
    """Return each `### ` choice heading with the source that belongs to it."""
    matches = list(CHOICE_HEADING_RE.finditer(body or ""))
    for index, matched in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(body)
        )
        yield " ".join(matched.group(1).split()), body[matched.end():end]


def blockquote_runs(text):
    """Return each contiguous run of blockquote lines, marker stripped."""
    runs, current = [], []
    for line in commonmark_lines(text):
        if re.match(r"^[ \t]{0,3}>", line):
            current.append(re.sub(r"^[ \t]{0,3}>[ \t]?", "", line).rstrip())
            continue
        if current:
            runs.append(current)
        current = []
    if current:
        runs.append(current)
    return runs


def sourced_quotes(text):
    """Return (label, destination, quoted body) for every attributed quote.

    An unattributed blockquote is not a quote for this purpose: it is the author's
    own words in quotation marks, and nothing can check those.
    """
    found = []
    for run in blockquote_runs(text):
        body = [line for line in run if line.strip()]
        if len(body) < 2:
            continue
        attribution = body[-1].strip()
        linked = attribution.removeprefix("— ").strip()
        # Use the same destination grammar as ordinary prose links, including
        # CommonMark angle destinations and optional link titles.
        matched = MARKDOWN_LINK_RE.fullmatch(linked)
        links = markdown_links(linked) if matched and attribution.startswith("— ") else []
        if len(links) == 1:
            label, destination = links[0]
            found.append((" ".join(label.split()), destination, "\n".join(body[:-1])))

    return found


def external_quote_destination(destination):
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", destination)) \
        or destination.startswith("//")


def quote_link_target(item, destination):
    """Select a lexical repository path without consulting worktree symlinks.

    Queue-relative links take precedence; root-relative repository spellings are
    also accepted. Only captured regular-file modes and bytes establish a source.
    Keep a missing lexical target so the caller can report it instead of silently
    treating a bad local citation as an external link.
    """
    path = destination.partition("#")[0]
    if external_quote_destination(destination) or path.startswith("/"):
        return None
    bases = (item.parent.relative_to(REPO).parts, ()) if path else ((),)
    candidates = []
    for base in bases:
        parts = list(base)
        for part in PurePosixPath(path or item.relative_to(REPO).as_posix()).parts:
            if part == "..":
                if not parts:
                    break
                parts.pop()
            elif part != ".":
                parts.append(part)
        else:
            candidate = REPO.joinpath(*parts)
            if candidate not in candidates:
                candidates.append(candidate)
    for candidate in candidates:
        relative = candidate.relative_to(REPO).as_posix()
        if (REPO / ".git").exists():
            if git_index_entry_mode(relative) is not None:
                return candidate
        elif not any(parent.is_symlink() for parent in (candidate, *candidate.parents)
                     if parent != REPO and REPO in parent.parents):
            if candidate.is_file():
                return candidate
    return candidates[0] if candidates else None


def quote_source_text(target):
    """Read a candidate regular text blob, never repo_text's draft fallback."""
    if not (REPO / ".git").exists() and any(
        parent.is_symlink() for parent in (target, *target.parents)
        if parent != REPO and REPO in parent.parents
    ):
        return None
    raw = repo_artifact_bytes(target)
    if raw is None or b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def anchored_section_source(target, fragment, raw=None):
    """Select a Markdown heading section or an inclusive, bounded line range."""
    if raw is None:
        raw = quote_source_text(target)
    if raw is None:
        return None
    raw_lines = [line.removesuffix("\n") for line in commonmark_lines(raw)]
    line_range = re.fullmatch(r"L([1-9][0-9]*)(?:-L([1-9][0-9]*))?", fragment)
    if line_range:
        first, last = line_range.group(1), line_range.group(2) or line_range.group(1)
        # Bound the decimal strings before int(): an enormous malformed selector
        # is an advisory, not Python's integer-conversion-limit exception.
        digits = len(str(len(raw_lines)))
        if len(first) > digits or len(last) > digits:
            return None
        start, end = int(first), int(last)
        if 1 <= start <= end <= len(raw_lines):
            return "\n".join(raw_lines[start - 1:end])
        return None
    if target.suffix.lower() != ".md":
        return None
    semantic_lines = [line.removesuffix("\n") for line in commonmark_lines(semantic_text(raw))]
    heads = [
        (index, matched.group(1), matched.group(2))
        for index, line in enumerate(semantic_lines)
        for matched in [re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*$", line)]
        if matched
    ]
    slugs = anchor_slugs([
        re.sub(r"[ \t]+#+[ \t]*$", "", title) for _i, _h, title in heads
    ])
    if fragment not in slugs:
        return None
    position = slugs.index(fragment)
    start, hashes, _title = heads[position]
    end = next(
        (i for i, other, _t in heads[position + 1:] if len(other) <= len(hashes)),
        len(raw_lines),
    )
    return "\n".join(raw_lines[start + 1:end])


def quote_identifier_continue(character):
    """Do not manufacture word boundaries inside Unicode identifier spellings."""
    category = unicodedata.category(character)
    if character.isalnum() or category in {"Mn", "Mc", "Me", "Pc", "Cf"}:
        return True
    return category == "Cn" and any(
        start <= ord(character) <= end for start, end in QUOTE_IDENTIFIER_UNICODE16_ADDITIONS
    )


def quote_string_spans(value):
    """Find complete quoted literals without pairing ordinary prose apostrophes."""
    spans, index = [], 0
    prefixes = {"r", "u", "b", "f", "br", "rb", "fr", "rf", "l", "u8", "n", "x"}
    while index < len(value):
        if value[index] not in "\"'":
            index += 1
            continue
        preceding = index - 1
        while preceding >= 0 and value[preceding] == "\\":
            preceding -= 1
        if (index - 1 - preceding) % 2:
            index += 1
            continue
        start = index
        if index and quote_identifier_continue(value[index - 1]):
            word = index - 1
            while word and quote_identifier_continue(value[word - 1]):
                word -= 1
            if value[word:index].lower() in prefixes:
                start = word
            elif value[index] == "'":
                # Neither an intraword contraction nor a word-final possessive
                # starts a literal. Do not consume a later real quote opener.
                index += 1
                continue
        matched = SOURCE_STRING_RE.match(value, index)
        if matched and value[index] == "'" and matched.end() < len(value) \
                and quote_identifier_continue(value[matched.end()]):
            # The first unescaped closing candidate is inside/starts a word:
            # 'tis ... we're, or 'tis ... 'A  B'. Reject this opener and resume
            # without skipping the later apostrophe or genuine literal.
            matched = None
        if matched:
            spans.append((start, matched.end()))
            index = matched.end()
        else:
            index += 1
    return spans


def quote_number_spans(value):
    """Keep adjacent signs and numeric components inside one excerpt boundary."""
    spans = []
    for matched in SOURCE_NUMBER_RE.finditer(value):
        start = matched.start()
        if value[start] in "+-" and start and (
                quote_identifier_continue(value[start - 1]) or value[start - 1] in ")]}"):
            # A touching range/subtraction separator is not a unary sign.
            start += 1
        spans.append((start, matched.end()))
    return spans


def quote_presentation_text(value, normalize_whitespace=False, literal_bounds=None):
    """Normalize paired prose emphasis while preserving code's literal contents.

    This is deliberately a small presentation allowance, not a Markdown renderer.
    In particular, intraword underscores, operators, unmatched delimiters, and the
    contents of inline/fenced/indented code cannot disappear during comparison.
    """
    protected = []
    prefix = "\ue000QUOTE"
    while prefix in value:
        prefix += "Q"

    def protect(content):
        protected.append(content)
        return prefix + str(len(protected) - 1) + "\ue001"

    exposed = semantic_line_offsets(value)
    lines = commonmark_lines(value)
    fence = None
    for index, line in enumerate(lines):
        matched = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)(?:\n)?$", line)
        if fence is not None:
            if matched and matched.group(1)[0] == fence[0] \
                    and len(matched.group(1)) >= len(fence) and not matched.group(2).strip():
                fence = None
                lines[index] = "\n"
            else:
                lines[index] = protect(line)
        elif matched:
            fence = matched.group(1)
            lines[index] = "\n"
        elif index not in exposed:
            lines[index] = protect(line)
    value = "".join(lines)
    # The same complete literal spans govern whitespace, presentation and
    # omissions. Code prefixes and symbols inside strings cannot be restyled.
    for start, end in reversed(quote_string_spans(value)):
        value = value[:start] + protect(value[start:end]) + value[end:]
    for start, end in reversed(inline_code_spans(value)):
        value = value[:start] + protect(render_inline_code(value[start:end])) + value[end:]
    # Whole delimiter runs with word boundaries: never erase the underscore in
    # MAX_LIMIT or the multiplication operator in A*B.
    emphasis = re.compile(r"(?<![\w*\\])(?P<stars>\*{1,3})(?=\S)(?P<body>.+?)(?<=\S)(?P=stars)(?![\w*])"
                          r"|(?<![\w_\\])(?P<unders>_{1,3})(?=\S)(?P<ubody>.+?)(?<=\S)(?P=unders)(?![\w_])", re.S)
    while True:
        changed = emphasis.sub(lambda m: m.group("body") if m.group("stars") else m.group("ubody"), value)
        if changed == value:
            break
        value = changed
    if normalize_whitespace:
        # Literal code is still protected here. A second collapse after restoring
        # it would turn distinct code bytes such as `A  B` and `A B` into a match.
        value = quote_whitespace(value)
    for index in range(len(protected) - 1, -1, -1):
        content = protected[index]
        if literal_bounds and content.strip():
            content = literal_bounds[0] + content + literal_bounds[1]
        value = value.replace(prefix + str(index) + "\ue001", content)
    return value


def raw_quote_presentations(quoted, normalize_whitespace=False):
    """Permit quote presentation without normalizing raw source strings."""
    yield quote_whitespace(quoted) if normalize_whitespace else quoted
    yield quote_presentation_text(quoted, normalize_whitespace=normalize_whitespace)
    stripped = quoted.strip()
    if inline_code_spans(stripped) == [(0, len(stripped))]:
        yield render_inline_code(stripped)
    fenced = re.fullmatch(r"(`{3,}|~{3,})[^\n]*\n(.*?)\n\1", stripped, re.S)
    if fenced:
        yield fenced.group(2)
    for delimiter in ("***", "**", "*", "___", "__", "_"):
        if stripped.startswith(delimiter) and stripped.endswith(delimiter):
            body = stripped[len(delimiter):-len(delimiter)]
            if body and body == body.strip():
                yield quote_whitespace(body) if normalize_whitespace else body


def quote_literal_spans(value):
    """Locate literal bytes for quote comparison, without changing parser policy."""
    spans = quote_string_spans(value)
    spans.extend(inline_code_spans(value))
    fence, start, offset = None, 0, 0
    exposed = semantic_line_offsets(value)
    for index, line in enumerate(exact_source_lines(value)):
        matched = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)[\r\n]*$", line)
        if fence is not None:
            if matched and matched.group(1)[0] == fence[0] \
                    and len(matched.group(1)) >= len(fence) and not matched.group(2).strip():
                spans.append((start, offset + len(line)))
                fence = None
        elif matched:
            fence, start = matched.group(1), offset
        elif index not in exposed and re.match(r"^(?: {4}|\t)", line):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    if fence is not None:
        spans.append((start, len(value)))
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def quote_whitespace(value, literal_bounds=None, normalize=True):
    """Collapse wrapping outside literal strings and equal-width code spans."""
    literals = []
    prefix = "\ue000LITERAL"
    while prefix in value:
        prefix += "Q"
    for start, end in reversed(quote_literal_spans(value)):
        literals.append(value[start:end])
        value = value[:start] + prefix + str(len(literals) - 1) + "\ue001" + value[end:]
    if normalize:
        value = " ".join(value.split())
    for index, literal in enumerate(literals):
        if literal_bounds:
            literal = literal_bounds[0] + literal + literal_bounds[1]
        value = value.replace(prefix + str(index) + "\ue001", literal)
    return value


def quote_is_verbatim(quoted, source, markdown=True):
    """Compare bounded excerpts, allowing only omissions outside original literals."""
    prefix = "\ue000QUOTE_MATCH"
    while prefix in quoted or prefix in source:
        prefix += "Q"
    marker, opening, closing = (prefix + suffix + "\ue001" for suffix in ("OMISSION", "OPEN", "CLOSE"))
    bounds = (opening, closing)
    literal_spans = quote_literal_spans(quoted)
    marked = quoted
    # Mark omissions before removing any presentation delimiters: code/string
    # ellipses must stay literal through every comparison route.
    for match in reversed(list(QUOTE_ELISION_RE.finditer(quoted))):
        if not any(start < match.end() and match.start() < end for start, end in literal_spans):
            marked = marked[:match.start()] + " " + marker + " " + marked[match.end():]

    def source_view(value):
        # Presentation may remove code delimiters. Retain their source context
        # until matching, then remove only our collision-free bookkeeping marks.
        pieces, spans, cursor, offset, depth, start = [], [], 0, 0, 0, 0
        for match in re.finditer(re.escape(opening) + "|" + re.escape(closing), value):
            chunk = value[cursor:match.start()]
            pieces.append(chunk)
            offset += len(chunk)
            if match.group() == opening:
                if depth == 0:
                    start = offset
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    spans.append((start, offset))
            cursor = match.end()
        pieces.append(value[cursor:])
        return "".join(pieces), spans

    def occurrence(segment, haystack, spans, numbers, cursor=0, after_omission=False, before_omission=False):
        for found in re.finditer(re.escape(segment), haystack[cursor:]):
            first, last = cursor + found.start(), cursor + found.end()
            if (first and quote_identifier_continue(segment[0])
                    and quote_identifier_continue(haystack[first - 1])) or (
                    last < len(haystack) and quote_identifier_continue(segment[-1])
                    and quote_identifier_continue(haystack[last])):
                continue
            if any(start < first < end or start < last < end for start, end in numbers):
                continue
            if any((after_omission and start < first < end)
                   or (before_omission and start < last < end) for start, end in spans):
                continue
            return last
        return None

    def matches(needle, omissions, protected_source):
        haystack, spans = source_view(protected_source)
        numbers = quote_number_spans(haystack)
        if needle.strip() and occurrence(needle, haystack, spans, numbers) is not None:
            return True
        if marker not in omissions:
            return False
        parts = omissions.split(marker)
        segments = [(index, part.strip()) for index, part in enumerate(parts) if part.strip()]
        if not segments:
            return False
        cursor = 0
        for index, segment in segments:
            cursor = occurrence(segment, haystack, spans, numbers, cursor,
                                after_omission=index > 0, before_omission=index < len(parts) - 1)
            if cursor is None:
                return False
        return True

    if matches(quote_whitespace(quoted), quote_whitespace(marked), quote_whitespace(source, bounds)):
        return True
    if markdown:
        for normalized in (False, True):
            if matches(quote_presentation_text(quoted, normalize_whitespace=normalized),
                       quote_presentation_text(marked, normalize_whitespace=normalized),
                       quote_presentation_text(source, normalize_whitespace=normalized, literal_bounds=bounds)):
                return True
        return False
    for normalized in (False, True):
        haystack = quote_whitespace(source, bounds, normalize=normalized)
        for presentation, omissions in zip(raw_quote_presentations(quoted, normalized),
                                            raw_quote_presentations(marked, normalized)):
            if matches(presentation, omissions, haystack):
                return True
    return False


def has_no_source_statement(text):
    return any(run == [NO_SOURCE_LITERAL] for run in blockquote_runs(text))


def evidence_problems(item, text):
    """Return what a reader cannot check about one item's citations.

    Nothing here asks the author whether the reader can answer — a field holding
    that opinion is a wish, and a weak model writes `yes` in it every time. Every
    rule asks whether the bytes the answer turns on are in the file, and compares
    them against the bytes they claim to come from.
    """
    above = human_attention_above_fold(text)
    got = text_fields(text)
    problems = []

    quotes = sourced_quotes(above)
    shown, attributed = set(), set()
    for label, destination, quoted in quotes:
        attributed.add(destination)
        if external_quote_destination(destination):
            # This check never fetches external content or presents it as verified.
            continue
        target = quote_link_target(item, destination)
        path, _, fragment = destination.partition("#")
        if target is None:
            problems.append(f"quote `{label}` has a source outside the repository: `{path}`")
            continue
        raw = quote_source_text(target)
        if raw is None:
            problems.append(f"quote `{label}` source `{path}` is missing, nonregular, or not readable candidate text")
            continue
        if not fragment:
            problems.append(f"quote `{label}` points at the whole of `{path}`; select a heading or bounded line range")
            continue
        source = anchored_section_source(target, fragment, raw)
        if source is None:
            problems.append(f"quote `{label}` source selector `#{fragment}` does not select a heading or bounded line range in `{path}`")
            continue
        if not quote_is_verbatim(quoted, source, markdown=target.suffix.lower() == ".md" and not re.fullmatch(r"L[0-9]+(?:-L[0-9]+)?", fragment)):
            problems.append(
                f"quote `{label}` is not the words that stand at `{path}#{fragment}`; "
                "quote the source's own bytes, or drop the quotation marks and own the sentence yourself"
            )
        else:
            shown.add(target.relative_to(REPO).as_posix())

    for label, destination in markdown_links(above):
        if destination in attributed:
            continue
        if external_quote_destination(destination):
            continue
        problems.append(
            f"link `{' '.join(label.split())}` sends the reader to a file the "
            "item never quotes; show the passage or do not send them"
        )

    if item.parent.name == "reviews":
        target = context_path_candidates(got.get("Review target", ""))
        if len(target) == 1 and target[0] not in shown:
            problems.append(
                f"nothing from `{target[0]}` — the file this asks the reader to "
                "review — is quoted in it"
            )

    stray = sorted({
        token for token in CONTEXT_BACKTICK_RE.findall(above)
        if QUEUE_FILE_TOKEN_RE.match(token)
    })
    if stray:
        problems.append(
            "path(s) above the answer line that no reader can click: "
            + ", ".join(f"`{token}`" for token in stray[:3])
            + (f", and {len(stray) - 3} more" if len(stray) > 3 else "")
        )

    if not quotes and not has_no_source_statement(above):
        problems.append(
            "no quoted source and no `> " + NO_SOURCE_LITERAL + "` line; a blank "
            "where evidence goes reads the same as evidence nobody looked for"
        )
    return problems


def frozen_unanswerable_reason(item, text):
    """Return the one most decisive reason a frozen item cannot be answered.

    One reason, not a list, and never "this item is old": age is a fact about the
    file's history and tells a reader nothing about whether they can answer it.
    What they can act on is the missing thing itself. A renamed field is not
    reported — `Why-you-might-care` carries what `Why this matters` carries, so
    naming the spelling would be the nag this function exists to avoid.
    """
    got = text_fields(text)
    above = human_attention_above_fold(text)
    if item.parent.name == "reviews":
        target = context_path_candidates(got.get("Review target", ""))
        if len(target) == 1 and not sourced_quotes(above):
            return (f"asks for a verdict on `{target[0]}` without showing one "
                    "line of it")
    clean = semantic_text(text)
    if not list(choice_sections(human_choices_body(clean) or "")):
        return "offers no `### ` choices to pick between"
    if not any(field in got for field in HUMAN_VERDICT_FIELDS):
        return "carries no recommendation and no case against one"
    if not markdown_link_destinations(above):
        return "has no clickable pointer above the answer line"
    if not any(field in got for field in HUMAN_CONTEXT_FIELDS):
        return "never says what happens today"
    return None


def queue_superseded_paths():
    """Return every path a live queue item claims to supersede.

    A frozen record whose successor already exists is not an open ask, so the
    re-ask report goes quiet for it without anyone editing the record itself.
    """
    claimed = set()
    for other in live_queue_items() or ():
        if not readable_queue_item(other):
            continue
        value = text_fields(repo_text(other)).get("Supersedes", "")
        for target in context_files(value):
            try:
                claimed.add(target.relative_to(REPO).as_posix())
            except ValueError:
                pass
    return claimed


def section_headings(text):
    """Return the level-two headings of one document, in source order."""
    return SECTION_HEADING_RE.findall(semantic_text(text))


def queue_leaf_template_name(leaf):
    """Return the template filename one queue leaf folder is filled from.

    `templates/README.md` pairs each leaf with its template by singularizing the
    folder name, so this derives the pairing instead of storing a second copy of
    it: `decisions` is filled from `decision.md`, `retries` from `retry.md`.
    """
    singular = re.sub(r"ies$", "y", leaf)
    if singular == leaf:
        singular = re.sub(r"s$", "", leaf)
    return f"{singular}.md" if SLUG_RE.fullmatch(singular) else None


def queue_leaf_template_sections(leaf):
    """Return the sections one leaf's template declares, or None when it has none.

    An adopter's own typed leaf has no template here, and then it has no section
    requirement either — `automation/AGENTS.md` already says a new typed leaf
    inherits only the actor's generic schema.
    """
    name = queue_leaf_template_name(leaf)
    if name is None:
        return None
    path = REPO / QUEUE_TEMPLATES / name
    if not candidate_has_file(path):
        return None
    return section_headings(repo_text(path))


def current_queue_template_governs(actor, text):
    """Whether today's templates define this item's section shape.

    A written record is immutable, so an item filed under the earlier field
    spelling keeps the schema it was written under: asking it for today's sections
    would demand an edit the immutability rule forbids, and the repair would be to
    rewrite history rather than to write better.

    On the human side that judgment already exists, so this delegates to it rather
    than inventing a second one. On the agent side there was none, and a bare
    "carries a legacy field" test turned out to be a hole rather than a carve-out:
    the one live legacy request is exactly the file an agent copies as a model, so
    a brand-new request that inherited its `Why-you-might-care:` line would have
    switched the rule off for itself. The field alone is therefore not enough — the
    item must also have been *filed* before the rule existed. `Filed` is a real
    calendar date on every item, held there by a blocking `queue-schema` rule, and
    it is readable in a plain `--check` run, which the Git-range creation-commit
    helpers are not: they need a `--range` or a merge parent and return nothing in
    the pre-commit path, where this check does most of its work. An item with no
    readable date is checked, not excused.
    """
    if actor == "needs-human":
        return human_attention_format_applies(actor, text)
    got = text_fields(text)
    if not any(key in got for key in LEGACY_HUMAN_PROJECTION_FIELDS):
        return True
    filed = parse_leading_date(got.get("Filed", ""))
    return filed is None or filed >= EXPLANATION_SHAPE_ACTIVATION


def choice_labels(headings):
    """Return every name a recommendation may use for one shown choice."""
    labels = []
    for heading in headings:
        label = " ".join(heading.split())
        if not label:
            continue
        labels.append(label)
        for separator in (" — ", " – ", " - ", ": "):
            if separator in label:
                labels.append(label.split(separator, 1)[0].strip())
                break
    return [label for label in labels if label]


def projection_value(got, index):
    """Return the spelling one item actually uses for a projected sentence."""
    modern, legacy = HUMAN_PROJECTION_FIELD_PAIRS[index]
    if modern in got:
        return modern, got.get(modern, "")
    return legacy, got.get(legacy, "")


def human_attention_format_applies(actor, text):
    """Return whether one live item is written under the human-attention format.

    The test is the projection spelling the item itself uses, not whether it has
    been answered. The two renames are one schema generation: an item that says
    `Why this matters` also carries the whole unattended outcome in
    `If you do nothing`, and both are part of its frozen action identity, so the
    answer it receives later cannot move it back to the earlier schema. Keying
    this on answered-ness instead would demand `Until then` back from a migrated
    item the moment the owner replies — and adding it then is exactly what
    "timing never changes with or after the response" forbids.
    """
    if actor != "needs-human" or not human_attention_format_enabled():
        return False
    got = text_fields(text)
    return any(field in got for field in HUMAN_PROJECTION_FIELDS)


def queue_timing_fields_for(actor, text):
    """Return the timing fields one live item must carry for its prefix."""
    if human_attention_format_applies(actor, text):
        return HUMAN_QUEUE_TIMING_FIELDS
    return QUEUE_TIMING_FIELDS


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
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            mode = _GIT_INDEX_CACHE.get(relative)
            oid = _GIT_INDEX_OID_CACHE.get(relative)
        else:
            # One index query carries both the mode and the object to read, so
            # the staged bytes cost no second spawn.
            mode, oid = git_index_path_entry(relative)
        if mode not in ("100644", "100755"):
            if _GIT_SNAPSHOT_CACHE_ACTIVE:
                _GIT_ARTIFACT_CACHE[relative] = None
            return None
        value = git_blob_bytes(oid)
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
    """Read one captured object through the reusable cat-file process.

    Blob bytes are what their object ID says they are, so the reader stays open
    across reconciler invocations and every caller — index reads and historical
    tree reads alike — pays one ``fork``/``exec`` per repository instead of one
    ``git show`` per artifact. Every cached object read funnels through this one
    process, so it is launched outside ``refs/replace/*``: a replacement entry
    here would substitute forged bytes for every artifact the checker reads.
    """
    global _GIT_CAT_FILE_PROCESS
    if not oid:
        return None
    scope_immutable_git_caches()
    if oid in _GIT_BLOB_CACHE:
        return _GIT_BLOB_CACHE[oid]
    if _GIT_CAT_FILE_PROCESS is None:
        try:
            _GIT_CAT_FILE_PROCESS = subprocess.Popen(
                [*RAW_GIT, "cat-file", "--batch"],
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
    # Both decodes route through decode_utf8_artifact so an unreadable file is one
    # named GitSnapshotError, never a bare UnicodeDecodeError that exits like a finding.
    try:
        label = f"`{path.relative_to(REPO).as_posix()}`"
    except ValueError:
        label = f"`{path}`"
    artifact = repo_artifact_bytes(path)
    if artifact is not None:
        return decode_utf8_artifact(artifact, label)
    if (REPO / ".git").exists():
        relative = path.relative_to(REPO).as_posix()
        if git_index_has_path(relative) \
                or relative in git_head_paths(relative):
            raise GitSnapshotError(
                f"`{relative}` is tracked but not a readable regular candidate file"
            )
    return decode_utf8_artifact(path.read_bytes(), label)


def candidate_has_file(path):
    """Whether the commit candidate or the worktree carries this file.

    Existence gates read the Git index first: content checks read staged bytes, so
    deleting the worktree copy must not hide a violation the commit still carries.
    """
    return repo_artifact_bytes(path) is not None or path.is_file()


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


def read_raw_git_object(oid):
    """Return one immutable object's kind and bytes, or None when unreadable.

    The reader stays open for the whole process and ignores replacement refs,
    matching the ``--no-replace-objects ls-tree`` queries it serves. Every
    failure — a missing object, a reader that cannot start, a frame Git did not
    finish — answers ``None`` instead of raising, so a caller can always fall
    back to the Git query it would have run anyway.
    """
    global _GIT_RAW_CAT_FILE_PROCESS
    if not _GIT_RAW_READER_AVAILABLE:
        return None
    if _GIT_RAW_CAT_FILE_PROCESS is None:
        try:
            _GIT_RAW_CAT_FILE_PROCESS = subprocess.Popen(
                ["git", "--no-replace-objects", "cat-file", "--batch"],
                cwd=REPO,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            disable_raw_git_reader()
            return None
    process = _GIT_RAW_CAT_FILE_PROCESS
    try:
        process.stdin.write(oid.encode("ascii") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().rstrip(b"\n").split()
        if header[:1] != [oid.encode("ascii")] or len(header) != 3:
            # Git answers an absent object with one framed `<oid> missing`
            # line; anything else leaves the stream unusable.
            if len(header) != 2:
                disable_raw_git_reader()
            return None
        size = int(header[2])
        payload = process.stdout.read(size)
        if len(payload) != size or process.stdout.read(1) != b"\n":
            disable_raw_git_reader()
            return None
    except (BrokenPipeError, OSError, ValueError):
        disable_raw_git_reader()
        return None
    return header[1].decode("ascii", errors="replace"), payload


def disable_raw_git_reader():
    """Stop reading raw objects after the reader stopped framing answers."""
    global _GIT_RAW_CAT_FILE_PROCESS, _GIT_RAW_READER_AVAILABLE
    process = _GIT_RAW_CAT_FILE_PROCESS
    _GIT_RAW_CAT_FILE_PROCESS = None
    _GIT_RAW_READER_AVAILABLE = False
    close_git_reader(process)


def parse_raw_git_tree(payload, oid_width):
    """Return a raw tree's name-to-(mode, object) map, or None if malformed."""
    entries = {}
    offset = 0
    while offset < len(payload):
        space = payload.find(b" ", offset)
        nul = payload.find(b"\0", space + 1)
        if space <= offset or nul < 0 or nul + 1 + oid_width > len(payload):
            return None
        mode = payload[offset:space].decode("ascii", errors="replace")
        name = payload[space + 1:nul].decode("utf-8", errors="surrogateescape")
        if not GIT_TREE_MODE_RE.fullmatch(mode) or not name \
                or "/" in name or name in entries:
            return None
        entries[name] = mode, payload[nul + 1:nul + 1 + oid_width].hex()
        offset = nul + 1 + oid_width
    return entries


def parse_raw_git_commit_tree(payload, oid_length):
    """Return the tree a raw commit object names, or None if malformed.

    ``tree`` is a commit's first header, and it is the only one read here.
    Parent lists keep coming from ``git rev-list``, which honours grafts and a
    shallow clone's boundary while a raw commit object does not.
    """
    header = payload.split(b"\n", 1)[0]
    if not header.startswith(b"tree "):
        return None
    tree_oid = header[len(b"tree "):].decode("ascii", errors="replace")
    if len(tree_oid) != oid_length or not FULL_GIT_OID_RE.fullmatch(tree_oid):
        return None
    return tree_oid


def git_tree_entries(tree_oid):
    """Return one cached raw tree's entries, or None when it cannot be read."""
    entries = _GIT_TREE_ENTRIES_CACHE.get(tree_oid)
    if entries is None:
        read = read_raw_git_object(tree_oid)
        if read is None or read[0] != "tree":
            return None
        entries = parse_raw_git_tree(read[1], len(tree_oid) // 2)
        if entries is not None:
            _GIT_TREE_ENTRIES_CACHE[tree_oid] = entries
    return entries


def object_root_tree(revision):
    """Return the tree a captured commit or tree revision exposes."""
    if revision in _GIT_COMMIT_TREE_CACHE:
        return _GIT_COMMIT_TREE_CACHE[revision]
    if revision in _GIT_TREE_ENTRIES_CACHE:
        return revision
    read = read_raw_git_object(revision)
    if read is None:
        return None
    if read[0] == "tree":
        entries = parse_raw_git_tree(read[1], len(revision) // 2)
        if entries is None:
            return None
        _GIT_TREE_ENTRIES_CACHE[revision] = entries
        return revision
    if read[0] != "commit":
        return None
    tree_oid = parse_raw_git_commit_tree(read[1], len(revision))
    if tree_oid is not None:
        _GIT_COMMIT_TREE_CACHE[revision] = tree_oid
    return tree_oid


def object_path_entry(revision, path):
    """Return one `ls-tree` entry read from cached raw Git objects.

    Answers ``UNREAD_TREE_ENTRY`` whenever the reader cannot produce the answer
    an ``ls-tree`` query would, so the caller runs that query unchanged: this
    reader only makes an existing answer cheaper. It never decides one Git
    could not, and never turns a readable repository into a snapshot error.
    """
    parts = str(path).split("/") if path else []
    if not parts or not immutable_revision(revision) \
            or any(part in ("", ".", "..") for part in parts):
        return UNREAD_TREE_ENTRY
    tree_oid = object_root_tree(revision)
    for index, part in enumerate(parts):
        entries = git_tree_entries(tree_oid) if tree_oid else None
        if entries is None:
            return UNREAD_TREE_ENTRY
        entry = entries.get(part)
        if entry is None:
            return None
        mode, oid = entry
        kind = LS_TREE_KINDS.get(mode, "blob")
        if index == len(parts) - 1:
            return mode.zfill(6), kind, oid
        if kind != "tree":
            return None  # ls-tree cannot descend through a blob or a gitlink
        tree_oid = oid
    return UNREAD_TREE_ENTRY


def git_tree_blob_entry(revision, path):
    """Return one exact tree blob as (mode, object), or None when absent."""
    scope_immutable_git_caches()
    cache_key = (revision, path)
    if cache_key in _GIT_TREE_BLOB_ENTRY_CACHE:
        return _GIT_TREE_BLOB_ENTRY_CACHE[cache_key]
    found = object_path_entry(revision, path)
    if found is not UNREAD_TREE_ENTRY:
        entry = (found[0], found[2]) if found and found[1] == "blob" else None
        if immutable_revision(revision):
            _GIT_TREE_BLOB_ENTRY_CACHE[cache_key] = entry
        return entry
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
    entry = parse_git_tree_blob_records(tree.stdout).get(path)
    if immutable_revision(revision):
        _GIT_TREE_BLOB_ENTRY_CACHE[cache_key] = entry
    return entry


def git_artifact_bytes_at(revision, path):
    """Read one regular repository file at an exact commit, or return absent."""
    entry = git_tree_blob_entry(revision, path)
    if entry is None or entry[0] not in ("100644", "100755"):
        return None
    return git_blob_bytes(entry[1])


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


def human_attention_format_enabled():
    contract = repo_artifact_bytes(QUEUE / "AGENTS.md")
    return bool(
        contract is not None
        and text_fields(decode_utf8_artifact(
            contract, "candidate `message-queue/AGENTS.md`"
        )).get("Human-attention format", "").strip() == "v1"
    )


def human_attention_format_v1_at(revision):
    """Return whether one exact candidate or commit enables the human format."""
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
        )).get("Human-attention format", "").strip() == "v1"
    )


def human_gating_enabled():
    contract = repo_artifact_bytes(QUEUE / "AGENTS.md")
    return bool(
        contract is not None
        and text_fields(decode_utf8_artifact(
            contract, "candidate `message-queue/AGENTS.md`"
        )).get("Human gating schema", "").strip() == "v1"
    )


def human_gating_v1_at(revision):
    """Return whether one exact candidate or commit enables human gating v1.

    Deliberately a separate marker rather than a `Queue resolution schema` bump:
    three sites compare that field against the literal `v1`, one of them an
    anti-downgrade check, so raising it would break all three at once. The
    activation machinery underneath is the same.
    """
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
        )).get("Human gating schema", "").strip() == "v1"
    )


def schema_activation_commits(head, path, field, version="v1"):
    """Return every reachable marker-bearing commit, including merged branches."""
    if not head:
        return (), None
    scope_immutable_git_caches()
    cache_key = (head, path, field, version)
    cacheable = _GIT_SNAPSHOT_CACHE_ACTIVE or immutable_revision(head)
    if cacheable and cache_key in _GIT_SCHEMA_ACTIVATION_CACHE:
        return _GIT_SCHEMA_ACTIVATION_CACHE[cache_key]
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
        result = (), history.stderr.strip() or (
            f"could not inspect {field} activation history"
        )
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _GIT_SCHEMA_ACTIVATION_CACHE[cache_key] = result
        # A failed read is only reused inside the invocation that saw it.
        return result
    activations = []
    for commit in history.stdout.splitlines():
        artifact = git_artifact_bytes_at(commit, path)
        if artifact is None:
            continue
        text = decode_utf8_artifact(artifact, f"`{path}` at {commit}")
        if text_fields(text).get(field, "").strip() == version:
            activations.append(commit)
    result = tuple(activations), None
    if cacheable:
        _GIT_SCHEMA_ACTIVATION_CACHE[cache_key] = result
    return result


def queue_resolution_activation_commits(head):
    activations = []
    for candidate_head in candidate_activation_heads(head):
        found, error = schema_activation_commits(
            candidate_head,
            "message-queue/AGENTS.md",
            "Queue resolution schema",
        )
        if error:
            raise GitSnapshotError(error)
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


def human_attention_activation_commits(head):
    """Return every reachable commit that already carried the human format."""
    activations = []
    for candidate_head in candidate_activation_heads(head):
        found, error = schema_activation_commits(
            candidate_head,
            "message-queue/AGENTS.md",
            "Human-attention format",
        )
        if error:
            raise GitSnapshotError(error)
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


def human_gating_activation_commits(head):
    """Return every reachable commit that already carried human gating v1."""
    activations = []
    for candidate_head in candidate_activation_heads(head):
        found, error = schema_activation_commits(
            candidate_head,
            "message-queue/AGENTS.md",
            "Human gating schema",
        )
        if error:
            raise GitSnapshotError(error)
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


def candidate_activation_heads(head):
    """Return every committed head whose schema history joins the candidate."""
    if CHANGE_RANGE is None and head and head == _GIT_HEAD_OID:
        return staged_parent_oids()
    return (head,) if head else ()


def git_merge_base_result(base, head):
    """Return (returncode, stdout, stderr) for one merge-base question.

    A merge base of two full object IDs is a fact about immutable history, so a
    settled answer is reused for the repository. Failures are never cached: the
    objects they could not reach may still arrive.
    """
    scope_immutable_git_caches()
    cache_key = (base, head)
    cacheable = immutable_revision(base) and immutable_revision(head)
    if cacheable and cache_key in _GIT_MERGE_BASE_CACHE:
        return _GIT_MERGE_BASE_CACHE[cache_key]
    common = subprocess.run(
        [*RAW_GIT, "merge-base", base, head],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    answer = common.returncode, common.stdout, common.stderr
    if cacheable and common.returncode in (0, 1):
        _GIT_MERGE_BASE_CACHE[cache_key] = answer
    return answer


def git_commit_available(revision):
    """Return (returncode, detail) for one commit-availability probe.

    Only a present commit is remembered. An absent object may be written later,
    so a negative answer is always asked again.
    """
    scope_immutable_git_caches()
    cacheable = immutable_revision(revision)
    if cacheable and revision in _GIT_COMMIT_AVAILABLE_CACHE:
        return _GIT_COMMIT_AVAILABLE_CACHE[revision]
    probe = subprocess.run(
        [
            "git", "--no-replace-objects", "cat-file", "-e",
            f"{revision}^{{commit}}",
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    detail = probe.stderr.decode(
        "utf-8", errors="replace"
    ).strip() if probe.stderr else ""
    answer = probe.returncode, detail
    if cacheable and probe.returncode == 0:
        _GIT_COMMIT_AVAILABLE_CACHE[revision] = answer
    return answer


def git_object_kind(object_id):
    """Return (returncode, kind) for one object-type probe."""
    scope_immutable_git_caches()
    cacheable = immutable_revision(object_id)
    if cacheable and object_id in _GIT_OBJECT_KIND_CACHE:
        return _GIT_OBJECT_KIND_CACHE[object_id]
    result = subprocess.run(
        [*RAW_GIT, "cat-file", "-t", object_id],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    answer = result.returncode, result.stdout.strip()
    if cacheable and result.returncode == 0:
        _GIT_OBJECT_KIND_CACHE[object_id] = answer
    return answer


def git_repository_path(name):
    """Return one repository metadata location, resolved once per repository."""
    scope_immutable_git_caches()
    if name in _GIT_REPOSITORY_PATH_CACHE:
        return _GIT_REPOSITORY_PATH_CACHE[name]
    location = subprocess.run(
        ["git", "rev-parse", "--git-path", name],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if location.returncode:
        raise GitSnapshotError(
            location.stderr.strip() or f"could not locate {name}"
        )
    resolved = Path(location.stdout.strip())
    if not resolved.is_absolute():
        resolved = REPO / resolved
    _GIT_REPOSITORY_PATH_CACHE[name] = resolved
    return resolved


def git_ancestry_probe(ancestor, descendant):
    """Answer one ancestry question, reusing settled object-ID comparisons.

    Whether one commit reaches another is a fact about immutable history, so a
    definite answer between two full object IDs is kept for the repository.
    Errors are never cached: an object can still arrive later.
    """
    scope_immutable_git_caches()
    cache_key = (ancestor, descendant)
    cacheable = immutable_revision(ancestor) and immutable_revision(descendant)
    if cacheable and cache_key in _GIT_ANCESTRY_CACHE:
        return _GIT_ANCESTRY_CACHE[cache_key]
    relationship = subprocess.run(
        [*RAW_GIT, "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    detail = relationship.stderr.decode(
        "utf-8", errors="replace"
    ).strip() if relationship.stderr else ""
    probe = relationship.returncode, detail
    if cacheable and relationship.returncode in (0, 1):
        _GIT_ANCESTRY_CACHE[cache_key] = probe
    return probe


def descended_from_any(revision, ancestors):
    """Return whether revision descends from any ancestor, failing Git errors closed."""
    for ancestor in ancestors:
        returncode, detail = git_ancestry_probe(ancestor, revision)
        if returncode == 0:
            return True, None
        if returncode != 1:
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
        returncode, detail = git_ancestry_probe(revision, activation)
        if returncode == 1:
            # Neither commit descends from the other. The candidate that joins
            # them activates the schema for this newly admitted history.
            return True, None
        if returncode != 0:
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


def staged_deleted_queue_paths(parent):
    if not parent:
        return []
    deleted = subprocess.run(
        [
            *RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=DR", parent, "--", "message-queue",
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


def staged_mutated_queue_paths(parent):
    if not parent:
        return []
    changed = subprocess.run(
        [
            *RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=MRT", parent, "--", "message-queue",
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
        for commit in staged_side_commits():
            governed, governance_error = governed_by_activation_join(
                commit, activations
            )
            if governance_error:
                raise GitSnapshotError(governance_error)
            if not governed:
                continue
            parents = revision_parents(
                commit, f"parents of staged side commit {commit}"
            )
            if not parents:
                yield git_empty_tree(), commit
            for parent in parents:
                yield parent, commit
        for parent in staged_parent_oids():
            yield parent, None
        return
    if CHANGE_RANGE.startswith("root:"):
        range_head = CHANGE_RANGE[len("root:"):]
        revision_range = range_head
    else:
        base, range_head = CHANGE_RANGE.split("...", 1)
        returncode, common, detail = git_merge_base_result(base, range_head)
        if returncode or not common.strip():
            raise GitSnapshotError(
                detail.strip()
                or "could not find the queue-deletion range merge base"
            )
        revision_range = f"{common.strip()}..{range_head}"

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
        # Six independent checks walk this same edge set. `revision_parents` runs
        # the identical `git rev-list --parents -n 1` — so shallow boundaries and
        # grafts are still honoured — but answers the second and later asks about
        # one revision from its cache instead of another process.
        for parent in revision_parents(commit, f"parents of {commit}"):
            yield parent, commit


def queue_deletion_events(activations):
    """Yield prior/candidate revisions for every governed queue deletion."""
    for parent, revision in queue_revision_edges(activations):
        deleted = (
            staged_deleted_queue_paths(parent)
            if revision is None
            else deleted_paths_between(parent, revision)
        )
        for path in deleted:
            if candidate_paths_match_other_parent(
                parent, revision, (path,)
            ):
                continue
            yield path, git_text_at(parent, path), parent, revision


def queue_mutation_events(activations):
    """Yield both sides of every governed action modification or move."""
    for parent, revision in queue_revision_edges(activations):
        mutated = (
            staged_mutated_queue_paths(parent)
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
            if candidate_paths_match_other_parent(
                parent, revision, (source, destination)
            ) and queue_parent_state_regression_problem(
                before, after
            ) is None:
                continue
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


def staged_mutated_handover_paths(parent):
    if not parent:
        return []
    changed = subprocess.run(
        [
            *RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M",
            "--diff-filter=MRT", parent, "--",
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
            staged_mutated_handover_paths(parent)
            if revision is None
            else mutated_handover_paths_between(parent, revision)
        )
        for path in paths:
            if candidate_paths_match_other_parent(
                parent, revision, (path,)
            ):
                continue
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
    returncode, detail = git_ancestry_probe(DISPLACED_TIP, range_head)
    if returncode == 0:
        return None
    if returncode != 1:
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


def normalize_claim_binding(text):
    """Blank the agent-supplied review binding lines for claim comparison.

    The `waiting` -> `folding` claim is a one-line status commit for every actor
    except a review, where that same commit is also where the agent records the
    terminal binding. Only `review_terminal_binding_write` may unlock this, so the
    claim stays "status plus exactly the binding it is allowed to add".
    """
    return re.sub(
        r"^(\*\*(?:" + "|".join(AGENT_REVIEW_BINDING_FIELDS) + r"):\*\*)[ \t]*.*$",
        r"\1 <claim-binding>",
        text,
        flags=re.M,
    )


def claim_identity(text, actor, leaf):
    got = text_fields(text)
    keys = {
        "Filed", "Action", "Full context",
    }
    if actor == "needs-human":
        keys.update({
            # The human owns this field, so a committed claim freezes it with the
            # rest of the response.
            "Resolution evidence",
            "Your answer", "Your review", "Review target",
            "Review revision", "Reviewed revision", "Review outcome",
            "Successor action",
        })
    else:
        # `Resolution evidence` is deliberately absent here. The agent is this
        # item's actor and predeclares its own evidence, so claiming first and
        # working the evidence out second must stay legal; freezing it across the
        # claim closed every exit at once — the claim could not be re-established,
        # the item could not be deleted with the field, and deleting without it
        # failed the evidence check. What completion has to prove is unchanged:
        # `resolution_evidence_problem` still requires the declared non-queue
        # paths to change in the deletion commit.
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
    # A deadline and its re-ask are delivery state, not the ask. Holding them
    # immutable would make re-surfacing a lapsed question an identity change,
    # and the only legal repair would be to invent an answer nobody gave.
    "Answer by",
    "Re-asked",
}
AGENT_NOTES_SECTION_RE = re.compile(
    r"^## Agent notes\s*\n.*?(?=^##(?:\s|$)|\Z)",
    flags=re.M | re.S,
)


def lifecycle_mutable_fields(actor, leaf, extra_mutable_fields=()):
    """Return the fields one live item may change without changing its action."""
    mutable_fields = set(LIFECYCLE_MUTABLE_FIELDS)
    mutable_fields.update(extra_mutable_fields)
    if actor == "needs-agent":
        # The agent is this item's actor and owns its own predeclaration, so it
        # may establish or correct `Resolution evidence` while the item is live.
        # Holding it immutable made an item filed without the field undeletable
        # from birth: it could not be added, and deletion failed without it.
        # `queue-schema` still requires a concrete non-queue path on every
        # ordinary agent item, and `resolution_evidence_problem` still requires
        # the declared paths to change in the deletion commit. What defines the
        # action — `Action`, `Full context`, `Request kind` — stays immutable, so
        # a claim receipt still cannot be carried onto a different action.
        mutable_fields.add("Resolution evidence")
    if actor == "needs-human" and leaf == "reviews":
        mutable_fields.update({
            "Your review", "Review target", "Review revision",
            "Reviewed revision", "Review outcome", "Successor action",
            "Resolution evidence",
        })
    elif actor == "needs-human":
        mutable_fields.update({"Your answer", "Your review"})
    return mutable_fields


def immutable_action_text(text, actor, leaf, extra_mutable_fields=()):
    """Return action-defining visible text with lifecycle state removed."""
    mutable_fields = lifecycle_mutable_fields(
        actor, leaf, extra_mutable_fields=extra_mutable_fields
    )
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


def queue_frozen_skeleton(path, text):
    """Return the raw bytes a live item may not change, as `rstrip`ed lines.

    `immutable_action_text` computes identity over `semantic_text`, which is a
    *subtractive* view: it blanks fenced code, indented code and HTML comments so
    they cannot supply structural evidence, and the blanked lines then vanish from
    the joined identity string. That is right for admitting evidence and wrong for
    integrity — the very constructs the repository distrusts are the constructs
    its tamper check cannot see. Content can be appended to a frozen record
    carrying the owner's committed answer, in a shape no reader is shown and no
    check reads, without changing the item's action identity.

    This is total over the file's own lines instead. Only `rstrip`, exposed
    lifecycle-mutable field lines, and exposed retry diagnostic prose are discarded.
    Re-applying or stripping the fold's hard breaks stays legal at any time, while
    a comment, fence, indented block, or hidden `<div>` still moves the skeleton,
    even inside retry notes. Existing notes headings stay frozen.

    Dropping a mutable line is what makes the lifecycle legal, and it is also the
    one place bytes can hide: a payload appended to the *end* of `**Answer by:**`
    leaves with the line. So a line is dropped only when it is `exposed_field_value`
    — when every byte of its value is a byte a reader is shown and a parser reads.
    A line carrying anything else is frozen like any other. Retry notes use the
    same exposure rule plus a semantic section map, so protected bytes, mutable
    field values, and diagnostic prose account for the complete source.
    """
    return "\n".join(frozen_skeleton_lines(path, text)).strip()


def retry_reference_line_offsets(parsed_lines):
    """Protect definition paragraphs, including container and multiline labels.

    A definition's destination and optional title do not render as diagnosis.
    Recognize its label before allowing any line of that source paragraph to
    leave the frozen skeleton; seeing only its final `]:` line is too late.
    Container removal is detection-only and never supplies structural evidence.
    """
    protected = set()
    paragraph = []
    definition = re.compile(r"(?m)^\[(?:\\[^\n]|[^\[\]\\]){1,999}\]:")

    def flush():
        content = "\n".join(line for _index, line in paragraph)
        match = definition.search(content)
        if match:
            first = content.count("\n", 0, match.start())
            protected.update(index for index, _line in paragraph[first:])
        paragraph.clear()

    for index, line in enumerate(parsed_lines):
        content = re.sub(r"^" + RECORD_MARKER_PREFIX, "", line.rstrip("\r\n"))
        if content.strip():
            paragraph.append((index, content))
        else:
            flush()
    flush()
    return protected



def contains_invisible_source_characters(value):
    """Detect raw controls and active invisible entities, without rendering text.

    This queue-only predicate recognizes escapes, closed code spans, and complete
    CommonMark references solely to decide whether source can be omitted from a
    frozen skeleton. It never supplies parsed values or changes original bytes.
    Raw controls stay protected even in code or after a backslash.
    """
    if contains_default_ignorable_characters(value):
        return True
    source = value or ""
    entity = re.compile(r"&(?:#[xX][0-9A-Fa-f]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]*);")
    ticks = re.compile(r"`+")
    index = 0
    while index < len(source):
        if source[index] == "\\":
            # Consume a backslash pair outside code. An odd run escapes '&' or
            # '`'; an even run leaves the following punctuation active.
            index += 2
            continue
        opening = ticks.match(source, index)
        if opening:
            width = opening.end() - index
            closing = next((match for match in ticks.finditer(source, opening.end())
                            if match.end() - match.start() == width), None)
            # Backslashes inside a code span do not escape its closing run.
            index = closing.end() if closing else opening.end()
            continue
        matched = entity.match(source, index)
        if matched:
            reference = matched.group()
            # html.unescape accepts legacy partial names and missing semicolons;
            # only whole references recognized by CommonMark reach the decoder.
            if reference.startswith("&#") or reference[1:] in html.entities.html5:
                if contains_default_ignorable_characters(html.unescape(reference)):
                    return True
            index = matched.end()
            continue
        index += 1
    return False


def retry_notes_line_offsets(text):
    """Map real retry notes to source lines, without trusting a raw heading.

    Only exposed diagnostic prose and its paragraph separators are mutable.
    Existing headings, fields, comments, code, and raw HTML stay in the skeleton,
    including blank lines inside hidden blocks. The parser supplies those offsets;
    comparing a blank semantic line alone would lose that distinction.
    """
    raw_lines = commonmark_lines(text)
    parsed = commonmark_lines(semantic_text(text or ""))
    exposed = semantic_line_offsets(text or "")
    headings, body, diagnostics = set(), set(), set()
    in_notes = False
    references = retry_reference_line_offsets(parsed)
    for index, raw in enumerate(raw_lines):
        line = raw.rstrip()
        clean = parsed[index].rstrip() if index < len(parsed) else ""
        heading = re.match(r"^[ ]{0,3}(#{1,6})(?:[ \t]|$)", clean)
        if index in exposed and heading and len(heading.group(1)) <= 2:
            in_notes = clean == "## Agent notes" and line == clean
            if in_notes:
                headings.add(index)
            continue
        if not in_notes:
            continue
        body.add(index)
        # Setext headings introduce a new top-level section too. Freeze the
        # preceding title as well; a thematic break is conservatively a boundary.
        if index in exposed and re.fullmatch(r"[ ]{0,3}(?:=+|-+)[ \t]*", clean):
            title = index - 1
            while title in diagnostics and raw_lines[title].strip():
                diagnostics.remove(title)
                title -= 1
            in_notes = False
            continue
        if index in exposed and line == clean and not heading \
                and index not in references \
                and not contains_invisible_source_characters(line) \
                and not FIELD_RE.fullmatch(line) \
                and not RAW_HTML_TOKEN_RE.search(line):
            diagnostics.add(index)
    return headings, body, diagnostics


def exact_source_lines(text):
    """Split CommonMark line endings without normalizing any source bytes."""
    return [line for line in re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", text) if line]


def field_exposure_lines(path, text):
    """Make only the validated human record fold transparent to exposure checks.

    These lines never supply fields or frozen bytes. The original source still
    owns both; this local view only proves which mutable field lines are outside
    comments, code, and enclosing HTML. Outer/nested containers remain intact.
    """
    lines = exact_source_lines(text)
    if Path(path).parts[1:2] != ("needs-human",):
        return lines
    bounds = fold_bounds(record_visible_lines(text))
    if bounds is None or fold_shape_problems(text):
        return lines
    opening, closing = bounds
    indices = (opening, opening + 1, closing)
    forms = (FOLD_OPEN_RE, FOLD_SUMMARY_RE, FOLD_CLOSE_RE)
    if any(index >= len(lines) or not form.fullmatch(lines[index].rstrip("\r\n"))
           for index, form in zip(indices, forms)):
        return lines
    for index in indices:
        lines[index] = lines[index][len(lines[index].rstrip("\r\n")):]
    return lines


def field_source_line_exposed(actor, index, matched, view_lines, offsets):
    """Exempt a human response's own angle prose, never its outer context."""
    if actor != "needs-human" or not HUMAN_RESPONSE_LINE_RE.match(matched.group()):
        return index in offsets
    neutral = list(view_lines)
    start, end = matched.span(2)
    line = neutral[index]
    neutral[index] = line[:start] + "response" + line[end:]
    return index in semantic_line_offsets("".join(neutral))


def pure_first_human_response(source, before, destination, after):
    """Allow reclassification caused solely by the first response's own bytes.

    An unclosed angle phrase can hide later unchanged metadata from the exposure
    map. This pairwise exception keeps that first reply legal only when every byte
    outside its one value is identical, including CRLF/CR endings. It does not
    neutralize response values for later metadata edits or change action identity.
    """
    if source != destination or Path(source).parts[1:2] != ("needs-human",):
        return False
    if first_concrete_response(human_response_fields(before)) is not None \
            or first_concrete_response(human_response_fields(after)) is None:
        return False
    documents = []
    for text in (before, after):
        lines = exact_source_lines(text)
        parsed = commonmark_lines(semantic_text(text))
        responses = [
            (index, matched)
            for index, line in enumerate(lines)
            for matched in [FIELD_RE.fullmatch(line.rstrip())]
            if matched and HUMAN_RESPONSE_LINE_RE.match(matched.group())
        ]
        if len(responses) != 1:
            return False
        index, matched = responses[0]
        if not exposed_field_value(matched, parsed[index] if index < len(parsed) else ""):
            return False
        view = field_exposure_lines(source, text)
        if not field_source_line_exposed("needs-human", index, matched, view, set()):
            return False
        # A person's value is everything after the unchanged bold label on this
        # one physical line, including their leading/trailing spaces. Keep the
        # exact label and line terminator; neither belongs to the answer value.
        start = HUMAN_RESPONSE_LINE_RE.match(lines[index]).end()
        end = len(lines[index].rstrip("\r\n"))
        lines[index] = lines[index][:start] + "response" + lines[index][end:]
        documents.append("".join(lines))
    return documents[0] == documents[1]


def frozen_skeleton_lines(path, text):
    """Return the `rstrip`ed lines `queue_frozen_skeleton` freezes."""
    parts = Path(path).parts
    actor = parts[1] if len(parts) > 1 else ""
    leaf = parts[2] if len(parts) > 2 else ""
    mutable_fields = lifecycle_mutable_fields(actor, leaf)
    view = field_exposure_lines(path, text)
    offsets = semantic_line_offsets("".join(view))
    parsed = commonmark_lines(semantic_text(text or ""))
    _headings, notes_body, diagnostics = (
        retry_notes_line_offsets(text)
        if (actor, leaf) == ("needs-agent", "retries")
        else (set(), set(), set())
    )
    lines = []
    for index, line in enumerate(commonmark_lines(text)):
        stripped = line.rstrip()
        if index in diagnostics:
            continue
        matched = FIELD_RE.fullmatch(stripped)
        if index not in notes_body and matched \
                and matched.group(1) in mutable_fields \
                and field_source_line_exposed(actor, index, matched, view, offsets) \
                and exposed_field_value(
                    matched, parsed[index] if index < len(parsed) else ""
                ):
            continue
        lines.append(stripped)
    return lines


def introduces_final_retry_notes(source, before, destination, after):
    """Allow one new final diagnostic section, never an existing boundary edit."""
    if any(Path(path).parts[1:3] != ("needs-agent", "retries")
           for path in (source, destination)):
        return False
    before_headings, _body, _diagnostics = retry_notes_line_offsets(before)
    after_headings, _body, diagnostics = retry_notes_line_offsets(after)
    if before_headings or len(after_headings) != 1:
        return False
    heading = next(iter(after_headings))
    lines = commonmark_lines(after)
    if not any(index > heading and lines[index].strip() for index in diagnostics):
        return False
    if any(line.strip() and index not in diagnostics
           for index, line in enumerate(lines) if index > heading):
        return False
    # Compare the complete preexisting content, including its hidden bytes. Only
    # the appended heading and exposed diagnosis are new; no old prose can be
    # reclassified as mutable by inserting a heading before it.
    return queue_frozen_skeleton(source, before) == queue_frozen_skeleton(
        destination, "".join(lines[:heading])
    )


def exposed_field_value(matched, parsed_line):
    """Whether a field line's raw value is exactly the value checks read.

    `semantic_text` blanks an HTML comment wherever it sits, including mid-line, and
    blanks whole lines inside a fence or an indented block. So a raw value that does
    not survive that view byte for byte is carrying content no reader is shown and
    no parser reads — the injection shape `queue_frozen_skeleton` exists to refuse —
    and the same is true of a raw-HTML tag, which `semantic_text` leaves standing but
    a renderer can hide behind `display:none`.

    The human's own response line is exempt from the raw-HTML half. A person
    answering in one sentence may write `<the thing>` in it, and their answer commit
    is the one edit this repository can never refuse: their first response is
    immutable and no agent may repair it. The comment/fence half still applies there,
    because those hide bytes from the human as well as from the checker.
    """
    read = FIELD_RE.fullmatch(parsed_line.rstrip())
    if read is None or read.group(1) != matched.group(1) \
            or read.group(2) != matched.group(2):
        return False
    if HUMAN_RESPONSE_LINE_RE.match(matched.group(0)):
        return True
    value = matched.group(2)
    return not (
        RAW_HTML_TOKEN_RE.search(value)
        or contains_invisible_source_characters(value)
    )


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


def review_outcome_value(value):
    """Normalize a review outcome, reading every unfilled blank as `pending`.

    A filed review shows `Review outcome` as a slot the folding agent fills, so an
    empty value, `______`, and `<...>` all mean the same thing: nothing has been
    classified yet. Resolving them here keeps that judgment in one place instead of
    letting each reader invent its own comparison — the omission default was already
    `pending`, and a literal blank meant the same thing to a human but not to code.
    """
    value = (value or "").strip()
    return value if has_concrete_value(value) else "pending"


def unanswered_review(fields):
    return bool(
        first_concrete_response(fields) is None
        and not has_concrete_value(fields.get("Reviewed revision", ""))
        and review_outcome_value(fields.get("Review outcome", "")) == "pending"
    )


def review_terminal_binding_write(prior, current):
    """Whether `current` only adds the agent's one-time terminal review binding.

    The human answers a review in one edit — one sentence after `**Your review:**`
    and nothing else (`handbook/human-action-guide.md`). `Reviewed revision` and
    `Review outcome` are then supplied by the agent's `folding` claim, so exactly
    one committed edge may fill them, and it is admissible only when:

    * the human's own response was already committed in the parent, so an agent can
      never author a response and classify it in the same commit;
    * every other response field — including the response text itself and the
      `Review target`/`Review revision` binding the human answered against — stays
      byte-identical, so the classification cannot be re-pointed at other bytes;
    * the binding was previously unset, making the write once-only; and
    * the new binding repeats the already-frozen `Review revision` exactly.

    What this cannot check is whether the recorded outcome is a truthful reading of
    the human's sentence: no rule here understands English. It bounds the forgery to
    a separate, attributable commit sitting beside immutable human text
    (`memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`).

    Both arguments are `human_response_fields` mappings.
    """
    if first_concrete_response(prior) is None:
        return False
    for key in prior:
        if key in AGENT_REVIEW_BINDING_FIELDS:
            continue
        if prior.get(key, "") != current.get(key, ""):
            return False
    if has_concrete_value(prior.get("Reviewed revision", "")) \
            or review_outcome_value(prior.get("Review outcome", "")) != "pending":
        return False
    revision = current.get("Review revision", "").strip()
    return bool(
        REVIEW_REVISION_RE.fullmatch(revision)
        and current.get("Reviewed revision", "").strip() == revision
        and review_outcome_value(current.get("Review outcome", ""))
        in REVIEW_OUTCOMES
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
    for index in range(len(HUMAN_PROJECTION_FIELD_PAIRS)):
        _prior_key, prior_value = projection_value(prior, index)
        _current_key, current_value = projection_value(current, index)
        if not has_concrete_value(current_value):
            return False
        if has_concrete_value(prior_value) \
                and prior_value.strip() != current_value.strip():
            return False
    # Either spelling may carry the enriched sentence, so both are mutable here.
    mutable = HUMAN_PROJECTION_FIELDS + LEGACY_HUMAN_PROJECTION_FIELDS
    return queue_action_identity(
        source,
        before,
        extra_mutable_fields=mutable,
    ) == queue_action_identity(
        destination,
        after,
        extra_mutable_fields=mutable,
    )


def queue_gating_migration(
    source, destination, before, after, prior_revision, revision
):
    """Allow one live human item to drop an unspellable boundary, once.

    The monotonic timing ratchet is the queue's strongest invariant and this is
    the only edge that bends it. It is bounded the same way
    `human_projection_context_migration` is bounded: the weakening is legal only
    in the exact commit that activates the schema which forbids the old boundary,
    so it can be taken once and never again.

    Four things must hold together, and each one is what stops a different abuse:
    the old boundary must actually name a transition the new schema makes
    unspellable (so this cannot launder an ordinary weakening); the item must
    gain the concrete unattended outcome its own schema requires plus a
    parseable `Answer by:` (so nothing becomes quietly unowned); neither side may
    carry a concrete response (so a committed human answer can never be reframed);
    and the action identity must be unchanged (so the ask itself is untouched).
    """
    source_parts = Path(source).parts
    destination_parts = Path(destination).parts
    if len(source_parts) < 3 or len(destination_parts) < 3 \
            or source_parts[1] != "needs-human" \
            or destination_parts[1] != "needs-human" \
            or source_parts[2] != destination_parts[2] \
            or delivery_class(Path(source).name) != "future-blocking" \
            or delivery_class(Path(destination).name) != "non-blocking" \
            or human_gating_v1_at(prior_revision) \
            or not human_gating_v1_at(revision):
        return False
    prior = text_fields(before)
    current = text_fields(after)
    prior_transitions = boundary_transitions(
        future_boundary_tokens(prior.get("Blocks at", ""))
    )
    if not prior_transitions.intersection(HUMAN_UNSPELLABLE_TRANSITIONS):
        return False
    if first_concrete_response(human_response_fields(before)) is not None \
            or first_concrete_response(human_response_fields(after)) is not None:
        return False
    for key in queue_timing_fields_for("needs-human", after)["non-blocking"]:
        if not has_concrete_value(current.get(key, "")):
            return False
    if parse_date(current.get("Answer by", "").strip()) is None:
        return False
    # The unattended-outcome sentence is the one thing the weakening makes
    # false: an item that said "this does not merge until you answer" must not
    # keep saying it once merging no longer waits. Both spellings are mutable
    # here for that reason, and only that field is — `Why this matters` and the
    # ask itself stay frozen, so this cannot become a licence to reword a
    # question on the way past the ratchet.
    _key, outcome = projection_value(current, 1)
    if not has_concrete_value(outcome):
        return False
    mutable = (HUMAN_PROJECTION_FIELDS[1], LEGACY_HUMAN_PROJECTION_FIELDS[1])
    return queue_action_identity(
        source, before, extra_mutable_fields=mutable
    ) == queue_action_identity(
        destination, after, extra_mutable_fields=mutable
    )


def queue_parent_state_regression_problem(before, after):
    """Protect write-once responses and committed claims across merge parents."""
    prior = text_fields(before)
    current = text_fields(after)
    prior_response = human_response_fields(before)
    current_response = human_response_fields(after)
    if first_concrete_response(prior_response) is not None \
            and current_response != prior_response \
            and not review_terminal_binding_write(
                prior_response, current_response
            ):
        return (
            "human response or its immutable review binding changed "
            "after the first concrete response"
        )
    prior_status = prior.get("Status", "").strip()
    current_status = current.get("Status", "").strip()
    if prior_status in {"folding", "in-repair"} \
            and current_status != prior_status:
        return (
            f"committed {prior_status} lifecycle claim regressed to "
            f"{current_status or 'no status'}"
        )
    return None


def queue_mutation_problem(
    source, destination, before, after, prior_revision=None, revision=None
):
    """Reject action replacement while permitting lifecycle-only updates."""
    regression = queue_parent_state_regression_problem(before, after)
    if regression is not None:
        return regression
    # There is no presentation carve-out. A live item's visible text is its
    # identity, so reformatting one is an identity change and is refused: a
    # fence over field labels cannot protect the ask itself, which is the title,
    # the context block, the choices, and the recommendation.
    if queue_action_identity(source, before) != queue_action_identity(
        destination, after
    ) and not human_projection_context_migration(
        source,
        destination,
        before,
        after,
        prior_revision,
        revision,
    ) and not queue_gating_migration(
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
        binding_write = review_terminal_binding_write(
            prior_response, current_response
        )
        if binding_write and not (
            prior_status == "waiting" and current_status == "folding"
        ):
            # The binding is the folding claim's payload, so it has exactly one
            # legal edge. Allowing it later would let an agent classify a response
            # long after the claim receipt `claimed_lifecycle_problem` matched.
            return (
                "the agent review binding may only be recorded on the "
                "waiting -> folding claim edge"
            )
        if first_concrete_response(prior_response) is not None \
                and response_changed and not binding_write:
            return (
                "human response or its immutable review binding changed "
                "after the first concrete response"
            )
        if current_status == "folding" and response_changed \
                and not binding_write:
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
            < QUEUE_TIMING_ORDER[source_timing] \
            and not queue_gating_migration(
                source,
                destination,
                before,
                after,
                prior_revision,
                revision,
            ):
        return "dependency timing was weakened while the queue item remained live"
    if source_timing == destination_timing and prior_timing != current_timing:
        return "dependency timing changed without a matching timing-prefix rename"
    return None


def revision_parents(revision, label):
    scope_immutable_git_caches()
    if (_GIT_SNAPSHOT_CACHE_ACTIVE or immutable_revision(revision)) \
            and revision in _GIT_REVISION_PARENTS_CACHE:
        return _GIT_REVISION_PARENTS_CACHE[revision]
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
    parents = ancestry.stdout.split()[1:]
    if _GIT_SNAPSHOT_CACHE_ACTIVE or immutable_revision(revision):
        _GIT_REVISION_PARENTS_CACHE[revision] = parents
    return parents


def staged_parent_oids():
    """Return HEAD plus every committed MERGE_HEAD of the index candidate."""
    global _GIT_STAGED_PARENTS_CACHE
    if _GIT_SNAPSHOT_CACHE_ACTIVE \
            and _GIT_STAGED_PARENTS_CACHE is not None:
        return _GIT_STAGED_PARENTS_CACHE
    head = _GIT_HEAD_OID or committed_candidate_revision()
    parents = [head] if head else []
    if not (REPO / ".git").exists():
        return tuple(parents)
    merge_head = git_repository_path("MERGE_HEAD")
    try:
        lines = merge_head.read_text(encoding="ascii").splitlines()
    except FileNotFoundError:
        result = tuple(parents)
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _GIT_STAGED_PARENTS_CACHE = result
        return result
    except (OSError, UnicodeError) as error:
        raise GitSnapshotError(f"could not read MERGE_HEAD: {error}") from error
    for line in lines:
        oid = line.strip()
        if not FULL_GIT_OID_RE.fullmatch(oid):
            raise GitSnapshotError("MERGE_HEAD contains an invalid object ID")
        returncode, detail = git_commit_available(oid)
        if returncode:
            raise GitSnapshotError(
                detail or f"MERGE_HEAD {oid} is not a committed parent"
            )
        if oid not in parents:
            parents.append(oid)
    result = tuple(parents)
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        _GIT_STAGED_PARENTS_CACHE = result
    return result


def staged_side_commits():
    """Return commits imported only through the staged MERGE_HEAD parents."""
    global _GIT_STAGED_SIDE_COMMITS_CACHE
    if _GIT_SNAPSHOT_CACHE_ACTIVE \
            and _GIT_STAGED_SIDE_COMMITS_CACHE is not None:
        return _GIT_STAGED_SIDE_COMMITS_CACHE
    parents = staged_parent_oids()
    if len(parents) < 2:
        return ()
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "rev-list",
            "--reverse", "--topo-order", *parents[1:],
            "--not", parents[0],
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
            or "could not inspect staged merge-side history"
        )
    result = tuple(history.stdout.splitlines())
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        _GIT_STAGED_SIDE_COMMITS_CACHE = result
    return result


def staged_side_creation_commits(path):
    """Return side-only add commits supplying the exact staged path state."""
    if _GIT_SNAPSHOT_CACHE_ACTIVE \
            and path in _GIT_STAGED_SIDE_CREATION_CACHE:
        return _GIT_STAGED_SIDE_CREATION_CACHE[path]
    parents = staged_parent_oids()
    if len(parents) < 2:
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _GIT_STAGED_SIDE_CREATION_CACHE[path] = ()
        return ()
    candidate = candidate_path_entry(None, path)
    if candidate is None:
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _GIT_STAGED_SIDE_CREATION_CACHE[path] = ()
        return ()
    creations = []
    for side in parents[1:]:
        if git_tree_path_entry(side, path) != candidate:
            continue
        history = subprocess.run(
            [
                "git", "--no-replace-objects", "log", "--no-renames",
                "--reverse", "--format=%H", "--diff-filter=A",
                side, "--not", parents[0], "--", path,
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
                or f"could not inspect staged-side creation of `{path}`"
        )
        for created_at in history.stdout.splitlines():
            if created_at not in creations:
                creations.append(created_at)
    result = tuple(creations)
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        _GIT_STAGED_SIDE_CREATION_CACHE[path] = result
    return result


def staged_side_creation_commit(path):
    """Return the current side-only incarnation's creation commit."""
    commits = staged_side_creation_commits(path)
    return commits[-1] if commits else None


def candidate_parent_oids(revision):
    """Return every committed parent contributing to one candidate."""
    if revision is None:
        return staged_parent_oids()
    return tuple(revision_parents(
        revision, f"candidate parents for {revision}"
    ))


def git_tree_path_entry(revision, path):
    """Return one exact tree entry as (mode, object), or None when absent."""
    scope_immutable_git_caches()
    cache_key = (revision, path)
    cacheable = _GIT_SNAPSHOT_CACHE_ACTIVE or immutable_revision(revision)
    if cacheable and cache_key in _GIT_TREE_PATH_ENTRY_CACHE:
        return _GIT_TREE_PATH_ENTRY_CACHE[cache_key]
    found = object_path_entry(revision, path)
    if found is not UNREAD_TREE_ENTRY:
        if cacheable:
            _GIT_TREE_PATH_ENTRY_CACHE[cache_key] = found
        return found
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree", "-z",
            revision, "--", path,
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(git_failure(
            tree, f"could not inspect `{path}` at {revision}"
        ))
    records = [record for record in tree.stdout.split(b"\0") if record]
    if not records:
        if cacheable:
            _GIT_TREE_PATH_ENTRY_CACHE[cache_key] = None
        return None
    metadata, separator, encoded_name = records[0].partition(b"\t")
    fields = metadata.decode("ascii", errors="replace").split()
    name = encoded_name.decode("utf-8", errors="surrogateescape")
    if not separator or len(fields) != 3 or name != path:
        raise GitSnapshotError(
            f"Git returned a malformed tree entry for `{path}` at {revision}"
        )
    mode, kind, oid = fields
    result = mode, kind, oid
    if cacheable:
        _GIT_TREE_PATH_ENTRY_CACHE[cache_key] = result
    return result


def candidate_path_entry(revision, path):
    """Return one exact staged/committed candidate tree entry."""
    if revision is not None:
        return git_tree_path_entry(revision, path)
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        if path in _GIT_INDEX_ALL_PATHS_CACHE \
                and path not in _GIT_INDEX_CACHE:
            raise GitSnapshotError(
                f"staged candidate path `{path}` remains unmerged"
            )
        mode = _GIT_INDEX_CACHE.get(path)
        oid = _GIT_INDEX_OID_CACHE.get(path)
        return (mode, "blob", oid) if mode and oid else None
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", path],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitSnapshotError(git_failure(
            result, f"could not inspect staged candidate path `{path}`"
        ))
    modes, oids, all_paths = parse_git_index_records(result.stdout)
    if path in all_paths and path not in modes:
        raise GitSnapshotError(
            f"staged candidate path `{path}` remains unmerged"
        )
    mode = modes.get(path)
    oid = oids.get(path)
    return (mode, "blob", oid) if mode and oid else None


def parent_merge_base(parent, other):
    """Return two candidate parents' merge base, or None when unrelated."""
    returncode, common, _detail = git_merge_base_result(parent, other)
    return common.strip() if returncode == 0 else None


def parent_supplies_absent_path(parent, other, path, boundary=None):
    """Require an actual side-branch deletion before absence is provenance."""
    boundary = boundary or parent_merge_base(parent, other)
    if not boundary:
        return False
    boundary_entry = git_tree_path_entry(boundary, path)
    parent_entry = git_tree_path_entry(parent, path)
    if boundary_entry is None or parent_entry != boundary_entry:
        return False
    history = subprocess.run(
        [
            "git", "--no-replace-objects", "log", "--full-history",
            "--no-renames", "--format=%H", "--diff-filter=D",
            f"{boundary}..{other}", "--", path,
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
            or f"could not inspect absence provenance for `{path}`"
        )
    return bool(history.stdout.strip())


def candidate_paths_match_other_parent(parent, revision, paths):
    """Return whether one other parent exactly supplies all named path states."""
    candidate = {
        path: candidate_path_entry(revision, path)
        for path in set(paths)
    }
    for other in candidate_parent_oids(revision):
        if other == parent:
            continue
        boundary = parent_merge_base(parent, other)
        if not boundary:
            continue
        matches = True
        for path, state in candidate.items():
            if git_tree_path_entry(parent, path) != git_tree_path_entry(
                boundary, path
            ):
                matches = False
                break
            if git_tree_path_entry(other, path) != state:
                matches = False
                break
            if state is None and not parent_supplies_absent_path(
                parent, other, path, boundary=boundary
            ):
                matches = False
                break
        if matches:
            return True
    return False


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
                # A review's claim commit also carries the agent's terminal
                # binding, which is the only content a claim may add. Blank those
                # two lines for the comparison exactly when this edge earned it.
                normalize = (
                    normalize_claim_binding
                    if review_terminal_binding_write(
                        human_response_fields(previous),
                        human_response_fields(current),
                    )
                    else (lambda value: value)
                )
                if normalize_claim_status(normalize(previous)) \
                        != normalize_claim_status(normalize(current)):
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


def earlier_resolution_task_ids(path, text, prior_revision):
    """Return the tasks whose earlier commits may carry one item's evidence.

    A queue action can only be resolved by work the repository already
    attributes to it, so the admitted set starts from the tasks that linked
    this exact canonical path before the resolution edge, and subtracts the
    tasks the item's own timing boundary gates: work attributed to the
    boundary an action blocks may not also resolve that action.

    Every input this cannot read answers the empty set, which leaves the
    deletion-edge comparison as the only way to pass.
    """
    got = text_fields(text)
    timing = delivery_class(Path(path).name)
    if timing == "blocking":
        field = "Blocks now"
        tokens = blocking_boundary_tokens(got.get(field, ""))
    elif timing == "future-blocking":
        field = "Blocks at"
        tokens = future_boundary_tokens(got.get(field, ""))
    else:
        # `non-blocking-*` declares **If unanswered:**, prose that names no
        # boundary, and a name with no delivery class declares nothing at all.
        # Neither parses to a boundary this rule could bind work to.
        return set()
    if not tokens or not has_concrete_value(got.get(field, "")):
        return set()  # a timing value Git cannot parse admits nothing
    try:
        linking = task_ids_linking_queue_at(prior_revision, path)
    except GitSnapshotError:
        return set()
    own_boundary = boundary_task_ids(
        blocking_boundary_tokens(got.get("Blocks now", ""))
    )
    own_boundary.update(boundary_task_ids(
        future_boundary_tokens(got.get("Blocks at", ""))
    ))
    return linking - own_boundary


def evidence_landed_for_task(evidence, revision, task_ids):
    """Whether reachable history already carries one task's evidence change.

    ``git log`` decides what "changed this path" means, including its own
    merge simplification: a merge counts only when it is TREESAME to no
    parent. A commit qualifies when it also names one admitted task and that
    task was already picked up at that commit.

    This only ever answers "already resolved", so every failure — an
    unreadable revision, a Git call that exits non-zero, a malformed frame —
    answers ``False`` and leaves the caller's finding exactly as it was.
    """
    if not task_ids:
        return False
    tips = [
        tip for tip in (
            (revision,) if revision is not None else staged_parent_oids()
        ) if tip
    ]
    if not tips:
        return False
    log = subprocess.run(
        [
            "git", "--no-replace-objects", "log",
            "--format=%H%n%B%x00", *tips, "--", evidence,
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if log.returncode:
        return False
    for record in log.stdout.split(b"\0"):
        oid, separator, message = record.lstrip(b"\n").partition(b"\n")
        if not separator:
            continue
        commit = oid.decode("ascii", errors="replace")
        if not immutable_revision(commit):
            continue
        named = set(TASK_COMMIT_TAG_RE.findall(
            message.decode("utf-8", errors="replace")
        ))
        for task_id in sorted(named.intersection(task_ids)):
            status, _task = task_status_at(commit, task_id)
            if status in RESOLVING_TASK_STATUSES:
                return True
    return False


def resolution_evidence_landed_earlier(evidence, revision, task_ids):
    """Whether an admitted task already committed this evidence change.

    Only ever answers "already resolved", so every failure answers ``False``
    and leaves the caller's finding exactly as the deletion edge left it.
    """
    try:
        return evidence_landed_for_task(evidence, revision, task_ids)
    except (GitSnapshotError, OSError, ValueError, UnicodeError):
        return False


def resolution_evidence_problem(item_path, text, prior_revision, revision):
    paths = resolution_evidence_paths(text)
    if not paths:
        return "missing non-queue **Resolution evidence:** file path"
    unchanged = []
    admitted = None
    for path in paths:
        before = git_artifact_bytes_at(prior_revision, path)
        after = (
            repo_artifact_bytes(REPO / path)
            if revision is None
            else git_artifact_bytes_at(revision, path)
        )
        if after is None:
            unchanged.append(path)
            continue
        if after != before:
            continue  # the deletion edge itself carries the evidence
        if admitted is None:
            try:
                admitted = earlier_resolution_task_ids(
                    item_path, text, prior_revision
                )
            except (GitSnapshotError, OSError, ValueError, UnicodeError):
                admitted = set()
        if not resolution_evidence_landed_earlier(path, revision, admitted):
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
    global _GIT_STAGED_PARENTS_CACHE, _GIT_STAGED_SIDE_COMMITS_CACHE
    global _GIT_STAGED_SIDE_CREATION_CACHE, _GIT_TREE_PATH_ENTRY_CACHE
    global _GIT_REVISION_PARENTS_CACHE, _GIT_SCHEMA_ACTIVATION_CACHE
    global _TASK_SNAPSHOT_CACHE, _LIVE_QUEUE_PATHS_CACHE

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
        _GIT_STAGED_PARENTS_CACHE,
        _GIT_STAGED_SIDE_COMMITS_CACHE,
        _GIT_STAGED_SIDE_CREATION_CACHE,
        _GIT_TREE_PATH_ENTRY_CACHE,
        _GIT_REVISION_PARENTS_CACHE,
        _GIT_SCHEMA_ACTIVATION_CACHE,
        _TASK_SNAPSHOT_CACHE,
        _LIVE_QUEUE_PATHS_CACHE,
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
    # This context exposes a committed tree as both HEAD and index. The real
    # worktree's MERGE_HEAD must not become a synthetic parent of that history.
    _GIT_STAGED_PARENTS_CACHE = (revision,)
    _GIT_STAGED_SIDE_COMMITS_CACHE = ()
    _GIT_STAGED_SIDE_CREATION_CACHE = {}
    _GIT_TREE_PATH_ENTRY_CACHE = {}
    _GIT_REVISION_PARENTS_CACHE = {}
    _GIT_SCHEMA_ACTIVATION_CACHE = {}
    _TASK_SNAPSHOT_CACHE = {}
    _LIVE_QUEUE_PATHS_CACHE = None
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
            _GIT_STAGED_PARENTS_CACHE,
            _GIT_STAGED_SIDE_COMMITS_CACHE,
            _GIT_STAGED_SIDE_CREATION_CACHE,
            _GIT_TREE_PATH_ENTRY_CACHE,
            _GIT_REVISION_PARENTS_CACHE,
            _GIT_SCHEMA_ACTIVATION_CACHE,
            _TASK_SNAPSHOT_CACHE,
            _LIVE_QUEUE_PATHS_CACHE,
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
    returncode, detail = git_ancestry_probe(ancestor, descendant)
    if returncode not in (0, 1):
        raise GitSnapshotError(
            detail
            or f"could not compare Git ancestry for {ancestor} and {descendant}"
        )
    return returncode == 0


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
    """Return task ids whose exact revision links one canonical queue item.

    The one recursive listing already names every task record's object, so
    each `task.md` is read straight from that object through the reusable
    ``cat-file --batch`` reader instead of asking Git for the same entry a
    second time, once per task.
    """
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "-z", revision, "--", "tasks",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(
            tree.stderr.decode("utf-8", errors="replace").strip()
            or f"could not inspect task links in {revision}"
        )
    task_ids = set()
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
        candidate = encoded_name.decode("utf-8", errors="surrogateescape")
        matched = re.fullmatch(
            rf"tasks/(?:{'|'.join(TASK_STATUSES)})/"
            r"(\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)/task\.md",
            candidate,
        )
        if not matched or kind != "blob" \
                or mode not in ("100644", "100755"):
            continue
        artifact = git_blob_bytes(oid)
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


def negative_review_cancellation_problem(
    path, text, prior_revision, revision, boundary_tokens=()
):
    """Require a rejected artifact or task pursuit to be mechanically withdrawn."""
    evidence_problem = resolution_evidence_problem(
        path, text, prior_revision, revision
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
    # A boundary Git cannot un-cross must never be a cleanup condition. The
    # retired merge receipt demanded an exact two-parent merge in already-admitted
    # history carrying the approved bytes, which is unsatisfiable the moment the
    # merge happens before the answer — and that is the ordinary case in an
    # `async` repository. `merge` is no longer spellable on a human item; a
    # historical one loses only its own receipt route and falls through to the
    # ordinary evidence rules, so an item filed under the old grammar stays
    # deletable instead of stranding. `transitions` itself is left whole: the
    # tail rule below still demands durable evidence for a named boundary, and
    # narrowing it there would let a blocking merge review vanish silently.
    routed = transitions - (
        HUMAN_UNSPELLABLE_TRANSITIONS - TASK_LIFECYCLE_TRANSITIONS
    )
    if routed.intersection(TASK_LIFECYCLE_TRANSITIONS):
        target = review_target(got.get("Review target", ""))
        if target is None or target[0] != "local":
            return "task-boundary cleanup needs a stable local review target"
        return task_transition_receipt_problem(
            path, text, prior_revision, revision, tokens
        )
    if boundary_task_ids(tokens):
        return resolution_evidence_problem(
            path, text, prior_revision, revision
        )
    if timing == "future-blocking":
        first = tokens[0] if tokens else ""
        date_boundary = parse_date(first)
        if date_boundary is not None and date_boundary > TODAY:
            return "future review cannot close before its recorded date boundary"
        return resolution_evidence_problem(
            path, text, prior_revision, revision
        )
    if transitions or any(
        OPERATION_BOUNDARY_RE.fullmatch(token) for token in tokens
    ):
        problem = resolution_evidence_problem(
            path, text, prior_revision, revision
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
    # The reviewed item's own schema says what "the same dependency timing"
    # means, so nothing is loosened for an item that still carries the prose
    # field. Only an item written under the human-attention format has moved its
    # unattended outcome above the fold, and only that item is compared on the
    # boundary token alone; a legacy item keeps the full tuple it was written
    # with, including `Until then` and `If unanswered`.
    compared_timing_fields = queue_timing_fields_for("needs-human", text)
    for key in compared_timing_fields.get(timing, ()):
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
    for key in compared_timing_fields.get(timing, ()):
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


def review_reask_problem(path, text, prior_revision, revision):
    """Gate the deletion of a review the reader could not answer.

    `changes-requested` says the artifact was wrong and routes the repair to an
    agent. `unanswerable` says the *item* was wrong: nothing about the subject
    was decided, so the question survives its own file and is owed to a human
    again. The successor is therefore `needs-human`, not `needs-agent` — the
    artifact was never what was missing — and it keeps the same delivery prefix,
    because a question does not become less urgent by being asked badly
    (`message-queue/AGENTS.md`).

    Deliberately absent: any requirement that the successor read well. Coupling a
    blocking lifecycle edge to an advisory readability judgment could wedge two
    files, neither of which may be edited
    (`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).
    """
    got = text_fields(text)
    candidates = context_path_candidates(got.get("Successor action", ""))
    if len(candidates) != 1:
        return "unanswerable review needs exactly one **Successor action:**"
    successor_path = candidates[0]
    successor_parts = Path(successor_path).parts
    if successor_path == path or not valid_queue_item_path(successor_path) \
            or successor_parts[1:3] != ("needs-human", "reviews"):
        return "unanswerable review successor is not a distinct canonical needs-human action"
    successor_bytes = candidate_artifact_bytes(successor_path, revision)
    if successor_bytes is None:
        return "unanswerable review successor is not live in the deletion candidate"
    if git_artifact_bytes_at(prior_revision, successor_path) is not None:
        # Otherwise any unrelated question already open would satisfy the edge.
        return "unanswerable review successor was not introduced by the resolution edge"
    successor = text_fields(decode_utf8_artifact(
        successor_bytes, f"`{successor_path}` in the deletion candidate"
    ))
    if path not in context_path_candidates(successor.get("Supersedes", "")):
        return "unanswerable review successor does not point back with **Supersedes:**"
    if not has_concrete_value(successor.get("Action", "")):
        return "unanswerable review successor has no concrete **Action:**"
    if delivery_class(Path(successor_path).name) != delivery_class(Path(path).name):
        return "unanswerable review successor changes the dependency timing"
    timing = delivery_class(Path(path).name)
    for key in queue_timing_fields_for("needs-human", text).get(timing, ()):
        if successor.get(key, "").strip() != got.get(key, "").strip():
            return f"unanswerable review successor changes **{key}:**"
    for key in ("Full context", "Review target", "Review revision"):
        if successor.get(key, "").strip() != got.get(key, "").strip():
            return f"unanswerable review successor changes **{key}:**"
    if successor.get("Status", "").strip() != "waiting" or not unanswered_review(successor):
        return "unanswerable review successor must be a waiting unanswered review"
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
            if outcome in REVIEW_REASK_OUTCOMES:
                return review_reask_problem(
                    path, text, prior_revision, revision
                ) or resolution_evidence_problem(
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
            closed_on_a_boundary = False
            if historical_future is not None \
                    and outcome in REVIEW_TERMINAL_OUTCOMES:
                closed_on_a_boundary = True
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
                closed_on_a_boundary = True
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
            # Cleanup needs the crossed receipt for a boundary review and
            # changed evidence otherwise (`message-queue/AGENTS.md`). Only the
            # boundary branches above were enforced, so a review that never
            # carried one could be answered and deleted with nothing outside
            # the queue to show for it — and this model makes `non-blocking-`
            # the ordinary timing for a human review, so that is now the common
            # case rather than the rare one.
            if closed_on_a_boundary:
                return None
            return resolution_evidence_problem(
                path, text, prior_revision, revision
            )
        return resolution_evidence_problem(
            path, text, prior_revision, revision
        )
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
        path, text, prior_revision, revision
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


def check_queue_frozen_skeleton():
    """Refuse an edit identity calls a no-op while the bytes say otherwise.

    `queue-resolution` asks whether the *action* changed, and computes that over
    `semantic_text`. Everything that view blanks — an HTML comment, a fenced
    block, an indented block — can therefore be appended to a live item, or to a
    frozen record already carrying the owner's committed answer, and the gate
    that exists to notice exactly that reports nothing. The payload is invisible
    to the reader and legible to the next agent, which is the ordinary shape of
    an instruction-injection.

    So this runs only where the identity gate said "unchanged", and asks the
    complementary question over raw lines: did anything change at all? Sanctioned
    migrations change identity, so they are `queue-resolution`'s business and are
    never double-reported here. Exposed lifecycle fields and retry diagnoses
    remain editable; existing notes structure and hidden bytes stay protected.
    Re-applying or stripping the fold's hard breaks is `rstrip`-invariant too.
    """
    if not (REPO / ".git").exists():
        return
    activations = queue_resolution_activation_commits(_GIT_HEAD_OID)
    if not activations and queue_resolution_enabled() and _GIT_HEAD_OID:
        activations = (_GIT_HEAD_OID,)
    if not activations:
        return
    reported = set()
    for source, destination, before, after, _prior, _revision in \
            queue_mutation_events(activations):
        if queue_action_identity(source, before) \
                != queue_action_identity(destination, after):
            continue  # queue-resolution owns a changed action and its carve-outs
        if queue_frozen_skeleton(source, before) \
                == queue_frozen_skeleton(destination, after):
            continue
        if introduces_final_retry_notes(source, before, destination, after):
            continue
        if pure_first_human_response(source, before, destination, after):
            continue
        if destination in reported:
            continue
        reported.add(destination)
        yield Finding(
            "queue-frozen-skeleton",
            Path(destination),
            "live queue item changed bytes that its action identity cannot "
            "see; hidden content or protected structure changed in a frozen record",
            "revert the protected edit; only exposed lifecycle fields, retry "
            "diagnostic prose, and trailing whitespace may change while live; "
            "a new final Agent notes section may contain exposed prose only; "
            "anything else "
            "belongs in a distinct successor action",
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


def human_gating_problems(timing, got, records):
    """Yield why one live `needs-human/` item may not bind what it binds.

    The whole model is here: a human answer never holds a Git edge. Merging,
    moving a task through review, and recording it complete are all revertible,
    so none of them may wait on an answer that arrives whenever it arrives. What
    a human item may still withhold is the start of work nobody has begun, and
    one act with no undo — both satisfiable by a commit an agent can make at any
    time after filing, in every review outcome.
    """
    tokens = (
        future_boundary_tokens(got.get("Blocks at", ""))
        if timing == "future-blocking"
        else blocking_boundary_tokens(got.get("Blocks now", ""))
        if timing == "blocking"
        else []
    )
    transitions = boundary_transitions(tokens)
    task_ids = boundary_task_ids(tokens)
    for name in sorted(transitions.intersection(HUMAN_UNSPELLABLE_TRANSITIONS)):
        yield (
            f"human action may not bind transition:{name}; merging, reviewing, "
            "and completing are revertible Git edges",
            "drop the boundary and file it non-blocking-* with its unattended "
            "outcome, or bind transition:start on a 0_backlog task",
        )
    if timing == "blocking" and blocking_task_ids(got.get("Blocks now", "")):
        yield (
            "human action may not stop a whole task with **Blocks now:** "
            "task:<id>; no human answer justifies 2_blocked",
            "file it non-blocking-* with its unattended outcome, or name the "
            "one act with no undo as operation:<name>",
        )
    if timing == "future-blocking" and tokens and "start" not in transitions:
        # The contract admits exactly one future boundary on a human item, and it
        # is not a date: `**Blocks at:** 2026-09-01` used to be accepted, so an
        # item could sit in the blocking class on a deadline the queue already
        # carries elsewhere. A calendar date is `Answer by`, which re-surfaces the
        # question without holding anything.
        yield (
            "**Blocks at:** on a human action must be transition:start "
            "task:<id>; a calendar deadline is **Answer by:**, not a boundary",
            "file it non-blocking-* and set Answer by to that date, or bind "
            "transition:start on the 0_backlog task this gate withholds",
        )
    if "start" in transitions:
        if not task_ids:
            yield (
                "transition:start on a human action must name the task it "
                "holds unstarted",
                "append task:<id> for the 0_backlog task this gate withholds",
            )
        for task_id in sorted(task_ids):
            record = records.get(task_id)
            if record is None:
                continue  # queue-task-reciprocity owns a missing task record
            status = record[0]
            if status != "0_backlog":
                yield (
                    f"transition:start names task:{task_id} in {status}; a "
                    "start gate binds an unstarted 0_backlog task",
                    "return that task to 0_backlog and unclaim it, or drop the "
                    "boundary and file this non-blocking-*",
                )
    answer_by = parse_date(got.get("Answer by", "").strip())
    if answer_by is None:
        yield (
            "**Answer by:** must be one UTC YYYY-MM-DD date",
            "set the date this question is worth re-surfacing on — 90 days "
            "from Filed unless something real dates it",
        )
    else:
        # Both dates are in the file, so this compares the item against itself
        # and never against today: a clean tree cannot start failing on a
        # calendar date. One generated item shipped already lapsed, with the
        # deadline equal to the day it was filed.
        filed = parse_leading_date(got.get("Filed", ""))
        if filed is not None and answer_by <= filed:
            yield (
                f"**Answer by:** {answer_by} is not after **Filed:** {filed}, "
                "so this question is lapsed the moment it is asked",
                "set it 90 days from Filed unless something real dates it "
                "sooner; a deadline already behind the filing date gives the "
                "reader no time at all",
            )


def check_queue_schema():
    queue_v1 = queue_resolution_enabled()
    gating_v1 = human_gating_enabled()
    if not gating_v1 and (REPO / ".git").exists() \
            and git_index_entries("message-queue") \
            and human_gating_activation_commits(_GIT_HEAD_OID):
        # The marker selects the restricted boundary grammar. Letting it be
        # toggled off and back on would let one candidate file a human merge
        # gate and re-arm the refusal behind it.
        yield Finding(
            "queue-schema",
            Path("message-queue/AGENTS.md"),
            "Human gating schema v1 was removed after activation",
            "restore **Human gating schema:** v1 while the queue remains",
        )
    gating_records = task_records() if gating_v1 else {}
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        timing = delivery_class(item.name)
        if timing is None:
            continue  # queue-name owns the malformed-name finding
        text = repo_text(item)
        got = text_fields(text)
        location = item.parent.relative_to(QUEUE).parts
        item_actor = location[0] if len(location) == 2 else ""
        if "Blocking" in got:
            yield Finding(
                "queue-schema",
                item.relative_to(REPO),
                "obsolete **Blocking:** field conflicts with filename timing",
                "remove it and use only the field required by the filename prefix",
            )
        expected = set(queue_timing_fields_for(item_actor, text)[timing])
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
        if gating_v1 and item_actor == "needs-human":
            for message, fix in human_gating_problems(
                timing, got, gating_records
            ):
                yield Finding(
                    "queue-schema", item.relative_to(REPO), message, fix
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
            # Either spelling satisfies a projected slot; carrying both would
            # leave a handover no way to choose which sentence it must copy.
            for modern, legacy in HUMAN_PROJECTION_FIELD_PAIRS:
                present = [key for key in (modern, legacy) if key in got]
                if not present:
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        f"missing required field **{modern}:**",
                        "copy the base schema from templates/queue/ "
                        f"({rel})",
                    )
                    continue
                if len(present) == 2:
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        f"fields **{modern}:** and **{legacy}:** name the same "
                        "projected sentence twice",
                        "keep exactly one spelling per projected sentence",
                    )
                    continue
                if not has_concrete_value(got[present[0]]):
                    yield Finding(
                        "queue-schema",
                        item.relative_to(REPO),
                        f"field **{present[0]}:** is empty or a placeholder",
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
            # The merge-bound-review rule that stood here is gone with the
            # boundary it served: every review is a human item, and a human item
            # can no longer bind `transition:merge` at all, so the rule could
            # only ever fire beside the refusal above as a duplicate.
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
                "**Full context:** does not point to an existing root-relative file",
                "link one durable source as a path from the repository root; a ../ path is dropped, not resolved",
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
                "**Full context:** does not point to an existing root-relative file",
                "link one durable source as a path from the repository root; a ../ path is dropped, not resolved",
            )
        if leaf == "reviews" and "Review target" in got:
            status = got.get("Status", "").strip()
            target = got["Review target"].strip()
            revision = got.get("Review revision", "").strip()
            reviewed_revision = got.get("Reviewed revision", "").strip()
            # Pending delivery predates this response-classification field, and a
            # filed item shows it as a blank the folding agent fills. Omission,
            # emptiness, and a placeholder all read as pending.
            outcome = review_outcome_value(got.get("Review outcome", ""))
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
                        "use sha256:<64 hex digits>, git:<full 40- or 64-hex "
                        "commit id>, or git:<full id>...<full id>; a branch "
                        "name or an abbreviated id names something that can "
                        "move, so run `git rev-parse <ref>` and paste the "
                        "whole id on both sides of the range",
                    )
                elif revision.startswith("git:"):
                    problems = git_review_revision_problems(revision)
                    if problems:
                        yield Finding(
                            "queue-schema",
                            item.relative_to(REPO),
                            "**Review revision:** is not a reviewable Git artifact: "
                            + "; ".join(problems),
                            "an id that does not resolve in this repository was "
                            "invented, not read: paste `git rev-parse <ref>` "
                            "output on both sides of the range, and until the "
                            "artifact exists file the item with **Status:** "
                            "awaiting-artifact and both target and revision "
                            "literally `pending`",
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
                # The human answers in one edit and stops. `Reviewed revision` and
                # `Review outcome` are the folding agent's to supply, so a
                # `waiting` item carrying only a response is complete. `folding` is
                # the agent's own commit, so the binding is required there — which
                # is also what stops an agent from claiming an unclassified review
                # and stranding it, since `queue_deletion_problem` demands the
                # terminal outcome again before the item may resolve.
                bound = (
                    has_concrete_value(reviewed_revision)
                    or outcome != "pending"
                )
                if has_concrete_value(response):
                    if status == "folding" or bound:
                        if reviewed_revision != revision:
                            yield Finding(
                                "queue-schema",
                                item.relative_to(REPO),
                                "review response is not bound to the "
                                "requested revision",
                                "copy Review revision into Reviewed revision "
                                "with the folding claim",
                            )
                        if outcome not in REVIEW_OUTCOMES:
                            yield Finding(
                                "queue-schema",
                                item.relative_to(REPO),
                                "review response needs an explicit terminal "
                                "**Review outcome:**",
                                "use approved, changes-requested, rejected, "
                                "abandoned, or unanswerable when the reader "
                                "could not tell from what the item showed them "
                                "(legacy not-approved means changes-requested)",
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
        if human_attention_format_applies(actor, text):
            # One shape for every live ask: named choices, each carrying the
            # state it enters and one concrete consequence of choosing it.
            choices_body = human_choices_body(clean)
            if not has_concrete_value(choices_body):
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "missing a concrete ## Your choices section",
                    "open it with the axis the choices differ on, then show "
                    "each choice under its own `### ` heading",
                )
                continue
            choices = [
                value for value in CHOICE_HEADING_RE.findall(choices_body)
                if has_concrete_value(value)
            ]
            examples = [
                value
                for value in EXAMPLE_CONSEQUENCE_RE.findall(choices_body)
                if has_concrete_value(value)
            ]
            if len(choices) < 2:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "## Your choices needs at least two `### ` choices",
                    "show at least two materially different answers, or say in "
                    "the axis sentence why one is unavailable",
                )
            if len(examples) < 2:
                yield Finding(
                    "queue-schema",
                    item.relative_to(REPO),
                    "## Your choices needs a concrete *Example consequence:* "
                    "for each choice",
                    "include at least two non-placeholder example consequences",
                )
            continue
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


def check_human_attention():
    """Enforce the shape of a live ask, never the prose a renderer produces.

    Everything here is structural: which fields exist, where they sit, and
    whether a named choice was actually shown. Nothing depends on knowing what
    a browser renders, which is the boundary that keeps this check small.

    An answered item is a record, not an ask. Records are immutable, so the
    presentation rules stop applying to them and they keep the schema they were
    written under, including the pre-rename field spelling.

    The same reasoning covers a live item that predates the format. Nothing may
    rewrite a live ask in place, so an item written in the earlier spelling is
    governed by the schema it was written under and ages out as it resolves;
    every new item is written from `templates/queue/` and is checked here.
    """
    enabled = human_attention_format_enabled()
    if not enabled and (REPO / ".git").exists() \
            and git_index_entries("message-queue") \
            and human_attention_activation_commits(_GIT_HEAD_OID):
        # The marker selects a rejecting grammar for every new ask. Letting it
        # be toggled off and back on would let one candidate slip an ask past
        # the checks and re-arm them afterwards.
        yield Finding(
            "human-attention",
            Path("message-queue/AGENTS.md"),
            "Human-attention format v1 was removed after activation",
            "restore **Human-attention format:** v1 while the queue remains",
        )
    if not enabled:
        return
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] != "needs-human":
            continue
        rel = item.relative_to(REPO)
        text = repo_text(item)
        if not human_attention_format_applies(parts[0], text):
            continue  # an earlier-spelled live item keeps its own schema
        if first_concrete_response(human_response_fields(text)) is not None:
            continue
        clean = semantic_text(text)
        got = text_fields(text)

        if unsanctioned_raw_html(text):
            yield Finding(
                "human-attention",
                rel,
                "live human item contains raw HTML outside the sanctioned fold",
                "write it in Markdown only; the sole admitted HTML is the three "
                "exact lines of the `## For the record` fold in "
                "`templates/queue/`, which `--fix-queue-fold` writes for you",
            )
        fields_hidden, headings_hidden, choices_hidden = \
            hidden_from_the_reader(text)
        for label, lost in (
            ("field(s)", [f"**{key}:**" for key in fields_hidden]),
            ("section heading(s)", [f"## {name}" for name in headings_hidden]),
            ("choice(s)", [f"### {name}" for name in choices_hidden]),
        ):
            if lost:
                yield Finding(
                    "human-attention",
                    rel,
                    f"{label} the checks obey but the reader never sees: "
                    + ", ".join(lost),
                    "delete the `display:none`, `hidden` or `aria-hidden` that "
                    "hides it; a fold is legal because a reader can open it, "
                    "and hiding is not folding",
                )
        for key in BANNED_QUEUE_FIELDS:
            if key in got:
                yield Finding(
                    "human-attention",
                    rel,
                    f"deleted field **{key}:** is present",
                    "name the source once in the prose; For the record keeps "
                    "the machine copy in Full context",
                )

        header_fields = [
            key for key, _value in FIELD_RE.findall(human_header_block(text))
        ]
        if tuple(header_fields) != HUMAN_ABOVE_FOLD_FIELDS:
            yield Finding(
                "human-attention",
                rel,
                "the block above the first heading must be exactly "
                + ", ".join(f"**{key}:**" for key in HUMAN_ABOVE_FOLD_FIELDS)
                + ", in that order; found "
                + (
                    ", ".join(f"**{key}:**" for key in header_fields)
                    if header_fields else "no field"
                ),
                "move everything else below the answer line so the top of the "
                "file and the notification are the same three sentences",
            )

        above = human_attention_above_fold(text)
        machine_above = sorted({
            key for key, _value in FIELD_RE.findall(above)
            if key in HUMAN_MACHINE_FIELDS
        })
        if machine_above:
            yield Finding(
                "human-attention",
                rel,
                "machine field(s) above the answer line: "
                + ", ".join(f"**{key}:**" for key in machine_above),
                "move them under ## For the record; nothing a human answers "
                "with needs a status, a path, a hash, or a boundary token",
            )

        missing_context = [
            key for key in HUMAN_CONTEXT_FIELDS
            if not has_concrete_value(got.get(key, ""))
        ]
        if missing_context:
            yield Finding(
                "human-attention",
                rel,
                "missing or empty "
                + ", ".join(f"**{key}:**" for key in missing_context),
                "separate what happens now from what this would change and "
                "from what a reader will wrongly assume is in scope",
            )

        verdicts = [key for key in HUMAN_VERDICT_FIELDS if key in got]
        if len(verdicts) != 1 or not has_concrete_value(got[verdicts[0]]):
            yield Finding(
                "human-attention",
                rel,
                "needs exactly one concrete "
                + " or ".join(f"**{key}:**" for key in HUMAN_VERDICT_FIELDS),
                "recommend one of the choices shown, or in a clarification "
                "state the assumption you will act on",
            )
        elif not has_concrete_value(got.get(HUMAN_COUNTER_CASE_FIELD, "")):
            yield Finding(
                "human-attention",
                rel,
                f"**{verdicts[0]}:** has no "
                f"**{HUMAN_COUNTER_CASE_FIELD}:**",
                "a verdict a reader cannot argue with is an instruction; give "
                "the best case for a different answer beside it",
            )
        else:
            labels = choice_labels(
                CHOICE_HEADING_RE.findall(human_choices_body(clean) or "")
            )
            verdict = " ".join(got[verdicts[0]].split()).lower()
            if not any(label.lower() in verdict for label in labels):
                yield Finding(
                    "human-attention",
                    rel,
                    f"**{verdicts[0]}:** does not name any choice shown under "
                    "## Your choices",
                    "recommend one of the `### ` choices offered, or offer the "
                    "one you actually recommend",
                )

        confidence = got.get(HUMAN_CONFIDENCE_FIELD, "")
        if not CONFIDENCE_RE.match(confidence.strip()):
            yield Finding(
                "human-attention",
                rel,
                f"**{HUMAN_CONFIDENCE_FIELD}:** must read "
                "`high|medium|low — <what you checked, and what you did not>`",
                "a bare adjective is not a calibration signal; name the thing "
                "you did not check",
            )

        words = len(above.split())
        if words > HUMAN_ATTENTION_WORD_BUDGET:
            yield Finding(
                "human-attention",
                rel,
                f"{words} words before the answer line exceeds the "
                f"{HUMAN_ATTENTION_WORD_BUDGET}-word budget by "
                f"{words - HUMAN_ATTENTION_WORD_BUDGET}",
                f"cut {words - HUMAN_ATTENTION_WORD_BUDGET} of the {words} words "
                f"of background written above the answer line, down to "
                f"{HUMAN_ATTENTION_WORD_BUDGET}; never cut a choice or its "
                "example consequence",
            )

        status = got.get("Status", "").strip()
        for token in sorted(set(QUEUE_STATUS_TOKEN_RE.findall(above))):
            if token != status:
                yield Finding(
                    "human-attention",
                    rel,
                    f"prose above the answer line names lifecycle state "
                    f"`{token}` while **Status:** is `{status or 'absent'}`",
                    "delete the state-dependent sentence; the item's own "
                    "Status is the single source of when it can be answered",
                )


def check_record_swallow():
    """Refuse a record field a reader is shown and no check can read.

    This is the silent half of the failure class, and it is live in production
    today with nothing catching it. Indent a field by one space, or write it as a
    list item, and GitHub still renders a bold label while `FIELD_RE`'s column-0
    anchor stops seeing it: the field exists to the human and not to the gate that
    is supposed to enforce it. Every HTML-boundary swallow is loud by comparison —
    the lost labels render as literal asterisks — so what blocks here is not the
    presence of a construct but the disagreement between the two views.

    Scoped by *position*, never by key name: only the record region is read, so a
    bold label used as prose inside a choice, a table cell or a blockquote is out
    of scope because of where it sits and not because of what it is called.

    Two more shapes of the same loss are reported here rather than under ids of
    their own, because an id in this repository is a check and each would otherwise
    buy a third and fourth full pass over the queue for one predicate:

    * **the region collapsed.** The lower half is defined from the answer line, so
      an unreadable answer line silently stops `## For the record` being checked at
      all. The region still collapses — widening it would police prose — but it now
      says so.
    * **a value ran onto the next line.** `FIELD_RE` is per-line and CommonMark's
      lazy continuation is not, so wrapped prose renders whole and parses to its
      first line. Gated to items the current template governs, because two live
      items predate it, are frozen, and would be refused with no legal repair.
    """
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] not in ("needs-human", "needs-agent"):
            continue
        rel = item.relative_to(REPO)
        text = repo_text(item)
        for line, key in record_swallow_losses(text):
            yield Finding(
                "record-swallow",
                rel,
                f"line {line} renders as **{key}:** but no check reads it as a "
                "field",
                "put it at column 0 with no indent, no list marker and no table "
                "cell, and keep a blank line after `</summary>` and before "
                "`</details>`; `automation/reconcile/reconcile.py "
                "--fix-queue-fold` does all of that for an indented or listed "
                "field, and refuses rather than half-repairing anything else",
            )
        if parts[0] == "needs-human" and record_region_is_truncated(text):
            yield Finding(
                "record-swallow",
                rel,
                "no readable **Your answer:** / **Your review:** line, so every "
                "line of `## For the record` falls outside the checked region",
                "put the answer line back at column 0, outside every fence, "
                "comment and fold; the record below it is unchecked until it is "
                "there, and that is a hole rather than a pass",
            )
        if not current_queue_template_governs(parts[0], text):
            continue  # an earlier-spelled live item keeps its own schema
        for line, key in field_value_continuations(text):
            yield Finding(
                "record-swallow",
                rel,
                f"line {line} continues the value of **{key}:** onto a second "
                "line, where nothing reads it",
                "join it into one physical line — every **Key:** value and every "
                "*Example consequence:* is read by a per-line pattern, so a "
                "value that wraps is silently cut at the first newline; put a "
                "blank line before any paragraph that is not part of the value",
            )


def check_fold_shape():
    """Hold the one admitted `<details>` shape to the nine rules it must obey.

    Conditional on a fold being present, so every item written before the fold
    existed passes untouched and no live item is ever asked to be rewritten. An
    answered item is skipped for the same reason `check_human_attention` skips
    one: it is a record rather than an ask, and what protects a record is
    `queue-frozen-skeleton`.

    Each finding names the repair that actually works on it. Two of the nine rules
    are about *where* the fold sits, and no emitter can move a section without
    deciding where the question ends — so those two say "move it", not "run the
    fixer". Naming a command that cannot help is worse than naming none: a weak
    model runs it, and before this was repaired the command it named folded the
    answer line away irreversibly.
    """
    if not human_attention_format_enabled():
        return
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] != "needs-human":
            continue
        text = repo_text(item)
        if not human_attention_format_applies(parts[0], text):
            continue  # an earlier-spelled live item keeps its own schema
        if first_concrete_response(human_response_fields(text)) is not None:
            continue
        for problem in fold_shape_problems(text):
            yield Finding(
                "fold-shape",
                item.relative_to(REPO),
                f"malformed fold: {problem}",
                "move `## For the record` and its whole fold below the answer "
                "line, keeping the answer line outside it"
                if "answer line" in problem else
                "copy the block from `templates/queue/` unchanged, or run "
                "`automation/reconcile/reconcile.py --fix-queue-fold`",
            )


def check_queue_render():
    """Report a fold whose field lines lost their Markdown hard break.

    Advisory, permanently and by design. The repair is one command and the
    damage is cosmetic and transient, while blocking it would refuse the commit
    in which a human answers from an editor that trims trailing whitespace — and
    for that there is no repair at all, because their first response is
    immutable and no agent may edit it.
    """
    targets = [
        REPO / QUEUE_TEMPLATES / name
        for name in ("decision.md", "clarification.md", "review.md")
    ]
    targets.extend(live_queue_items() or ())
    for path in targets:
        if not candidate_has_file(path):
            continue
        rel = path.relative_to(REPO)
        lines = unbroken_fold_field_lines(repo_text(path))
        if lines:
            yield Finding(
                "queue-render",
                rel,
                "folded field line(s) "
                + ", ".join(str(line) for line in lines)
                + " lost the two trailing spaces that break them onto their "
                "own rendered lines",
                "run `automation/reconcile/reconcile.py --fix-queue-fold`; it "
                "is whitespace-only, idempotent, and identity-preserving",
            )


def check_explanation_shape():
    """Report the readability rules a program can see, and only those.

    `skills/explain-to-human/` says how everything a person reads is written.
    Three of its rules have a shape rather than a meaning: the sections a file
    carries, the order they come in, and whether each choice ends with a concrete
    consequence. Those are reported here. Whether an explanation is actually clear,
    or whether a consequence is real rather than hedged, stays a reviewer's job —
    the decision that created this check says so
    (`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).

    Every finding is advisory. A checker can see that a section is missing and not
    that the prose in it was worth writing, so refusing a commit over one would
    train agents to write for the checker. The pull-request half of the same
    standard lives in `automation/check_action_projection.py`, which is the only
    tracked program that ever holds a pull-request body.
    """
    sections_by_leaf = {}
    stuck = []
    superseded = None  # built once, and only if a frozen item is actually found
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] not in ("needs-human", "needs-agent"):
            continue
        actor, leaf = parts
        text = repo_text(item)
        rel = item.relative_to(REPO)
        for line, key in field_value_continuations(text):
            if current_queue_template_governs(actor, text):
                continue  # record-swallow blocks it where a repair is legal
            # An item written before the current template is frozen: refusing it
            # would demand an edit immutability forbids, and there is no repair.
            # Saying nothing is worse — the value really is cut mid-sentence and
            # a reader deserves to know before quoting it. So it is reported at
            # the one tier that never refuses a commit, and it stays reported
            # until the item resolves.
            yield Finding(
                "explanation-shape",
                rel,
                f"line {line} continues the value of **{key}:** onto a second "
                "line; the reader sees the whole sentence and every check reads "
                "only its first half",
                "leave this item alone — it is frozen and a rewrite is refused; "
                "read the file rather than the parsed value, and write new "
                "items with each value on one physical line",
            )
        if not current_queue_template_governs(actor, text):
            # The third path, and the one that was silence. A frozen record may
            # not be edited, so its reason is collected for one aggregate re-ask
            # report and never phrased as a repair. It goes quiet when the item
            # is answered — a record awaiting its fold is not an ask — and when a
            # live successor already names it.
            if actor == "needs-human" and first_concrete_response(
                human_response_fields(text)
            ) is None:
                if superseded is None:
                    superseded = queue_superseded_paths()
                if rel.as_posix() not in superseded:
                    reason = frozen_unanswerable_reason(item, text)
                    if reason:
                        stuck.append((rel, reason))
            continue
        if actor == "needs-human" \
                and rel.as_posix() not in git_head_paths("message-queue"):
            # Birth-time only, for the reason the source-link finding below
            # already gives: on a committed item, quoting a source in changes the
            # prose, which changes action identity, which `queue-resolution`
            # refuses. A finding nobody may act on is a nag.
            for problem in evidence_problems(item, text):
                yield Finding(
                    "explanation-shape",
                    rel,
                    problem,
                    "quote the words the answer turns on, inline, under "
                    "[<what this passage says>](<path>#<heading-anchor>); a "
                    "reader who must open something to answer cannot answer",
                )
        if actor == "needs-human" \
                and rel.as_posix() not in git_head_paths("message-queue") \
                and not markdown_link_destinations(
                    human_attention_above_fold(text)
                ) \
                and not has_no_source_statement(human_attention_above_fold(text)):
            # Birth-time only, and deliberately so. `handbook/human-action-guide.md`
            # asks for the source once, as one clickable link in the prose, with the
            # machine copy in `Full context` below the answer line — and nothing
            # checked it, so a held-out authoring run produced items with a path a
            # reader could not follow. Reporting it on an item already committed
            # would be a nag nobody may act on: adding the link changes the prose,
            # which changes action identity, which `queue-resolution` refuses. So it
            # is raised to the one author who can still fix it, in the one commit
            # where fixing it is legal.
            yield Finding(
                "explanation-shape",
                rel,
                "no source link in the prose above the answer line",
                "link the durable source once, in the prose, as "
                "[<label>](<path from this file>); `Full context` below the "
                "answer line keeps the machine copy, and a reader cannot click "
                "that one",
            )
        if leaf not in sections_by_leaf:
            sections_by_leaf[leaf] = queue_leaf_template_sections(leaf)
        required = sections_by_leaf[leaf]
        if not required:
            continue
        template = f"{QUEUE_TEMPLATES}/{queue_leaf_template_name(leaf)}"
        present = section_headings(text)
        for heading in required:
            if heading not in present:
                yield Finding(
                    "explanation-shape",
                    rel,
                    f"missing section `## {heading}`",
                    f"copy the sections and their order from `{template}`",
                )
        # Compare only the required sections an item actually carries, so a
        # missing one is reported once as missing rather than again as disorder.
        ordered = list(dict.fromkeys(
            heading for heading in present if heading in required
        ))
        expected = [heading for heading in required if heading in ordered]
        for found, wanted in zip(ordered, expected):
            if found != wanted:
                yield Finding(
                    "explanation-shape",
                    rel,
                    f"section `## {found}` comes before `## {wanted}`",
                    f"a reader scans these in one order; `{template}` sets it",
                )
                break

        clean = semantic_text(text)
        for label, body in choice_sections(human_choices_body(clean) or ""):
            if any(
                has_concrete_value(value)
                for value in EXAMPLE_CONSEQUENCE_RE.findall(body)
            ):
                continue
            yield Finding(
                "explanation-shape",
                rel,
                f"choice `### {label}` has no concrete "
                "*Example consequence:* line",
                "end the choice with one scenario of life after it is picked; a "
                "cost nobody can picture is a cost nobody weighs",
            )

    # One finding covers the frozen set. `aggregate_findings` keys on
    # (check, subject), so `--file-retries` projects one repair item for the
    # aggregate instead of a separate permanent item for each old question.
    if stuck:
        yield Finding(
            "explanation-shape",
            Path(QUEUE.name) / "needs-human",
            f"{len(stuck)} unanswered question(s) cannot be answered from their "
            "own bytes:\n"
            + "\n".join(f"    - `{rel}`: {reason}" for rel, reason in stuck),
            "these are frozen records and no agent may edit one; re-ask each as "
            "a new item that quotes what its answer turns on and names the old "
            "path in **Supersedes:**, or leave it and answer it as it stands",
        )


def check_stale_queue():
    # No worktree gate: live_queue_items() reads the Git index first, so a staged
    # item still ages when its worktree copy is gone, and yields nothing otherwise.
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        timing = delivery_class(item.name)
        if timing is None:
            continue
        got = fields(item)
        if item.parent.parent.name == "needs-human":
            # A human item ages on its own deadline, whatever its prefix. The
            # old rules never reached these at all: `non-blocking` was skipped
            # outright, and a `future-blocking` item was skipped unless its
            # boundary began with a date — which no named boundary does. Ten
            # live questions therefore carried no staleness pressure of any
            # kind, and "it blocks a merge" was the only alarm any of them had.
            #
            # `stale-queue` is advisory, so a lapse never blocks a commit or a
            # merge. That tier is what makes a deadline admissible here: the
            # answer is the human's to give, and a repository may notice that it
            # is late without ever deciding it for them.
            if first_concrete_response(human_response_fields(repo_text(item))) \
                    is not None:
                continue  # answered: a record awaiting its fold, not an ask
            deadline = parse_date(got.get("Answer by", ""))
            if deadline and deadline <= TODAY:
                yield Finding(
                    "stale-queue",
                    item.relative_to(REPO),
                    f"answer-by date {deadline} has passed",
                    "re-surface it in the next reply, then set a new "
                    "**Answer by:** with a **Re-asked:** line naming the "
                    "lapsed date; never write an answer nobody gave",
                )
            continue
        if timing == "non-blocking":
            continue
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


# ------------------------------------------------- the open-action list
#
# One generated digest of every live queue item, ordered so the first screen is
# the one that matters. It is a projection: every line is copied from the item it
# links, and nothing may be answered, decided, or recorded in it. That is the same
# contract `memory/index.md` has, and it is enforced the same way — `--fix-open-actions`
# writes it, `open-actions` refuses a commit once it stops matching its inputs.
#
# The one rule that is easy to get wrong: **nothing here may depend on today.**
# Rendering "overdue" or "due in nine days" would make the tracked bytes a function
# of the calendar, so a clean tree nobody touched would start failing the morning a
# deadline passed, and every commit for the rest of that day would carry an unrelated
# diff. Lateness already belongs to `stale-queue`, which is advisory for exactly that
# reason (`automation/AGENTS.md`). This check is blocking, so it states the date the
# item wrote and never compares it to anything.

OPEN_ACTIONS_PATH = "message-queue/open-actions.md"
OPEN_ACTIONS_NAME = "open-actions.md"
OPEN_ACTIONS_COMMAND = (
    "python3 automation/reconcile/reconcile.py --fix-open-actions"
)
OPEN_ACTIONS_BANNER = (
    f"<!-- GENERATED by reconcile.py --fix-open-actions"
    f" — answer the linked item, never this file -->"
)
OPEN_ACTIONS_TIMING_ORDER = ("blocking", "future-blocking", "non-blocking")
OPEN_ACTIONS_TIMING_HEADINGS = {
    "blocking": "Stops work now",
    "future-blocking": "Stops work at a named boundary",
    "non-blocking": "Never stops work",
}
# Two spellings of the same two slots are live at once, and neither may be rewritten
# in place: an unanswered item's visible text is its identity, so the older wording
# ages out as those items resolve (`handbook/human-action-guide.md`). The digest reads
# both rather than showing a blank for the ten items still carrying the old one.
OPEN_ACTIONS_WHY_FIELDS = ("Why this matters", "Why-you-might-care")
OPEN_ACTIONS_UNATTENDED_FIELDS = (
    "If you do nothing", "If-you-do-nothing", "If unanswered", "Until then",
)
# A human item at these statuses is not the human's move: one is mid-fold by an
# agent, the other is waiting on an artifact that does not exist yet.
OPEN_ACTIONS_HELD_STATUSES = ("folding", "awaiting-artifact")


def first_present_field(got, keys):
    for key in keys:
        value = got.get(key, "").strip()
        if value and not PLACEHOLDER_RE.fullmatch(value):
            return value
    return ""


def markdown_link_label(text):
    """Return link-label text whose own brackets cannot end the label early."""
    return text.replace("[", "\\[").replace("]", "\\]")


def counted(count, singular, plural=None):
    """Return `1 question` / `13 questions` — never `13 question(s)`.

    This file is read by a person on a phone. A parenthesized plural is the tell
    of a generator that could not be bothered, and it costs one function to not
    write it.
    """
    return f"{count} {singular if count == 1 else plural or singular + 's'}"


def open_action_entries():
    """Return one record per live queue item, already in digest order."""
    entries = []
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue  # queue-location owns unsafe or broken filesystem entries
        parts = item.parent.relative_to(QUEUE).parts
        if len(parts) != 2 or parts[0] not in ("needs-human", "needs-agent"):
            continue  # queue-location owns misfiled items; never guess where they go
        timing = delivery_class(item.name)
        if timing is None:
            continue  # queue-name owns a filename that declares no timing
        actor, leaf = parts
        text = repo_text(item)
        got = text_fields(text)
        status = got.get("Status", "").strip()
        answered = actor == "needs-human" and \
            first_concrete_response(human_response_fields(text)) is not None
        boundary = first_present_field(got, ("Blocks now", "Blocks at"))
        deadline = got.get("Answer by", "").strip() if actor == "needs-human" else ""
        sort_date = parse_date(deadline) or parse_leading_date(boundary) \
            or parse_date(got.get("Filed", "")) or datetime.date.max
        entries.append({
            "path": item.relative_to(QUEUE).as_posix(),
            "actor": actor,
            "leaf": leaf,
            "timing": timing,
            "status": status,
            "action": got.get("Action", "").strip(),
            "title": document_title(text) or item.stem,
            "why": first_present_field(got, OPEN_ACTIONS_WHY_FIELDS),
            "unattended": first_present_field(got, OPEN_ACTIONS_UNATTENDED_FIELDS),
            "deadline": deadline,
            "boundary": boundary,
            "pickup": got.get("Request kind", "").strip() == "task-pickup",
            "held": answered or status in OPEN_ACTIONS_HELD_STATUSES,
            "answered": answered,
            "sort": (OPEN_ACTIONS_TIMING_ORDER.index(timing), sort_date),
        })
    entries.sort(key=lambda e: (e["sort"], e["path"]))
    return entries


def document_title(text):
    for line in semantic_text(text).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def open_action_bullet(entry, note=""):
    """Render one item as a single sentence, with its depth folded underneath."""
    label = markdown_link_label(entry["action"] or entry["title"])
    suffix = f" — {note}" if note else ""
    lines = [f"- [{label}]({entry['path']}){suffix}"]
    detail = []
    if entry["why"]:
        detail.append(f"**Why this matters:** {entry['why']}")
    if entry["unattended"]:
        detail.append(f"**If you do nothing:** {entry['unattended']}")
    if not detail:
        return lines
    summary = "why, and what happens if nobody acts" if entry["why"] \
        else "what happens if nobody acts"
    # Indented to the bullet's own content column, with a blank line under the
    # summary, which is what makes GitHub render the Markdown inside rather than
    # printing it as literal text.
    lines.append(f"  <details><summary>{summary}</summary>")
    lines.append("")
    for paragraph in detail:
        lines.append(f"  {paragraph}")
        lines.append("")
    lines.append("  </details>")
    return lines


def open_action_note(entry):
    """Return the one trailing fact a reader needs before opening the item."""
    parts = []
    if entry["timing"] != "non-blocking" and entry["boundary"]:
        parts.append(f"blocks {entry['boundary']}")
    if entry["deadline"]:
        parts.append(f"answer by {entry['deadline']}")
    return " · ".join(parts)


def open_action_section(entries, heading, empty, intro=()):
    lines = [f"## {heading}", ""]
    if not entries:
        lines += [empty, ""]
        return lines
    lines += list(intro)
    for timing in OPEN_ACTIONS_TIMING_ORDER:
        group = [e for e in entries if e["timing"] == timing]
        if not group:
            continue
        lines.append(
            f"### {OPEN_ACTIONS_TIMING_HEADINGS[timing]} — {len(group)}"
        )
        lines.append("")
        for entry in group:
            lines += open_action_bullet(entry, open_action_note(entry))
        lines.append("")
    return lines


def open_action_pickup_lines(pickups):
    """Collapse the one action that repeats, so it cannot bury the rest.

    Every unclaimed backlog task carries a pickup request whose action is the same
    sentence with a different task in it. Listed one per line they are the largest
    block in the file and say the least, so they become one counted line that opens
    into the task names.
    """
    lines = [
        f"- **{len(pickups)} backlog tasks are waiting for an agent to pick one up.**",
        "  <details><summary>which tasks</summary>",
        "",
    ]
    for entry in pickups:
        slug = Path(entry["path"]).stem
        for prefix in ("non-blocking-pick-up-", "blocking-pick-up-",
                       "future-blocking-pick-up-"):
            if slug.startswith(prefix):
                slug = slug[len(prefix):]
                break
        lines.append(f"  - [{markdown_link_label(slug)}]({entry['path']})")
    lines += ["", "  </details>"]
    return lines


def generated_open_actions():
    entries = open_action_entries()
    yours = [e for e in entries if e["actor"] == "needs-human" and not e["held"]]
    held = [e for e in entries if e["actor"] == "needs-human" and e["held"]]
    agents = [e for e in entries if e["actor"] == "needs-agent"]
    pickups = [e for e in agents if e["pickup"]]
    other_agent = [e for e in agents if not e["pickup"]]
    stopping = [e for e in entries if e["timing"] == "blocking"]

    headline = (
        f"**{counted(len(stopping), 'action')} stopping work right now.**"
        if stopping else "**Nothing is stopping work.**"
    )
    tail = f" {counted(len(held), 'other')} not yours right now." if held else ""

    lines = [
        OPEN_ACTIONS_BANNER,
        "# Open actions",
        "",
        "Everything this repository is waiting on, in one list. Every line below is"
        " copied from the",
        "item it links, so this file decides nothing — an answer goes in the linked"
        " file, never here.",
        "Regenerate it with `" + OPEN_ACTIONS_COMMAND + "`.",
        "",
        f"{headline} {counted(len(yours), 'question')} waiting on you,"
        f" {counted(len(agents), 'action')} waiting on an agent.{tail}",
        "",
    ]

    lines += open_action_section(
        yours,
        "Waiting on you",
        "Nothing is waiting on you.",
        intro=[
            "To answer one, open it and write a sentence in its blank"
            " `**Your answer:**` or `**Your review:**`",
            "line. That is the whole protocol — one edit, and nothing else to"
            " fill in.",
            "",
        ],
    )

    lines += ["## Waiting on an agent", ""]
    if not agents:
        lines += ["Nothing is waiting on an agent.", ""]
    else:
        for timing in OPEN_ACTIONS_TIMING_ORDER:
            group = [e for e in other_agent if e["timing"] == timing]
            group_pickups = [e for e in pickups if e["timing"] == timing]
            if not group and not group_pickups:
                continue
            total = len(group) + len(group_pickups)
            lines.append(
                f"### {OPEN_ACTIONS_TIMING_HEADINGS[timing]} — {total}"
            )
            lines.append("")
            for entry in group:
                lines += open_action_bullet(entry, open_action_note(entry))
            if group_pickups:
                lines += open_action_pickup_lines(group_pickups)
            lines.append("")

    if held:
        lines += ["## Not yours right now", ""]
        for entry in held:
            note = "already answered — an agent owes the fold" if entry["answered"] \
                else f"status {entry['status']}"
            lines += open_action_bullet(entry, note)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def check_open_actions():
    indexed = bool(git_index_entries("message-queue")) \
        if (REPO / ".git").exists() else False
    if not indexed and not QUEUE.is_dir():
        return  # an adopter without a queue owes no digest of it
    artifact = repo_artifact_bytes(QUEUE / OPEN_ACTIONS_NAME)
    current = artifact is not None and decode_utf8_artifact(
        artifact, f"`{OPEN_ACTIONS_PATH}`"
    ) == generated_open_actions()
    if not current:
        yield Finding(
            "open-actions",
            Path(OPEN_ACTIONS_PATH),
            "the open-action list does not match the queue",
            f"run: {OPEN_ACTIONS_COMMAND}",
        )


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
    # Any phrasing that names the task inside `Filed:` proves provenance. The
    # field is the provenance clause and it is immutable, so pinning one exact
    # preposition means an item written as "from the owner's review of task `x`"
    # can never prove what it plainly says — and cannot be reworded to. That
    # mattered the moment a human item lost its boundary: the boundary token was
    # its other ownership proof, and dropping it must not orphan the item.
    return bool(re.search(
        r"(?<![A-Za-z0-9_-])task[ \t]+`"
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
        returncode, kind = git_object_kind(object_id)
        if returncode:
            problems.append(f"{object_id} is unavailable")
        elif kind != "commit":
            problems.append(f"{object_id} is {kind}, not a commit")
    if len(object_ids) == 2 and not problems:
        returncode, _common, _detail = git_merge_base_result(
            object_ids[0], object_ids[1]
        )
        if returncode:
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
            *RAW_GIT, "ls-tree", "-r", "--name-only", head, "--", "tasks",
        ]
        log_range = head
    else:
        base, head = change_range.split("...", 1)
        changed_command = [
            *RAW_GIT, "diff", "--no-renames", "--name-only",
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
        [*RAW_GIT, "log", "--format=%B", log_range],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if messages.returncode == 0:
        task_ids.update(TASK_COMMIT_TAG_RE.findall(messages.stdout))
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


def change_range_base():
    """Return the base the candidate is measured against, when one exists."""
    if CHANGE_RANGE is None or CHANGE_RANGE.startswith("root:"):
        return None
    return CHANGE_RANGE.split("...", 1)[0]


def queue_action_identities_at(revision):
    """Return every governed queue action identity present at one revision.

    Identity, not path: escalating `non-blocking-` to `future-blocking-` to
    `blocking-` renames the file while the action stays the same one, and that
    escalation must not read as a newly filed action.
    """
    cached = _QUEUE_IDENTITY_CACHE.get(revision)
    if cached is not None:
        return cached
    tree = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "-z", revision, "--", "message-queue",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tree.returncode:
        raise GitSnapshotError(git_failure(
            tree, f"could not list queue actions at {revision}"
        ))
    identities = set()
    for path, mode in parse_git_tree_records(tree.stdout).items():
        if mode not in ("100644", "100755") or not governed_queue_path(path):
            continue
        artifact = git_artifact_bytes_at(revision, path)
        if artifact is None:
            continue
        identities.add(queue_action_identity(
            path, decode_utf8_artifact(artifact, f"`{path}` at {revision}")
        ))
    _QUEUE_IDENTITY_CACHE[revision] = identities
    return identities


def unanswered_action_filed_inside_change_range(item):
    """Return whether this range filed this action, and no human has answered it.

    A boundary check asks whether an action that was *already* pending slipped
    past its stop. An action created inside the range was not pending before it.
    Filing is also the only way one comes into existence, and
    `check_queue_task_reciprocity` requires the reciprocal `Queue actions` link
    in the named task's record — which is exactly what puts that task in a
    non-task branch's inferred scope. Without this, a
    `transition:<name> task:<id>` action could never be introduced through any
    merged candidate at all, and would be stranded the moment it was written. It
    is still reported at every later boundary it reaches.

    An action carrying a committed human response is different: it is the
    boundary's receipt, and whether that receipt still covers the candidate is
    precisely what this boundary validates. Those are never skipped.
    """
    base = change_range_base()
    if base is None:
        return False  # No base to compare against: report, do not assume.
    if not unanswered_review(fields(item)):
        return False
    rel = item.relative_to(REPO).as_posix()
    if git_artifact_bytes_at(base, rel) is not None:
        return False
    return queue_action_identity(
        rel, repo_text(item)
    ) not in queue_action_identities_at(base)


def check_active_queue_boundaries():
    if not ACTIVE_TRANSITIONS:
        return
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        if unanswered_action_filed_inside_change_range(item):
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
            if path_is_git_ignored(entry.relative_to(REPO).as_posix()):
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
                if path_is_git_ignored(item.relative_to(REPO).as_posix()):
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
                    # `4_done` is an agent's `git mv`, so it tests the agent's
                    # obligation, never the human's satisfaction. Done means the
                    # work is merged, `verification.md` carries real output, and
                    # nothing is left for an agent to do. A live human question
                    # stays listed and outlives the task: the queue is the single
                    # source of truth for open questions, and holding a task in
                    # review until someone answers is exactly the wait this model
                    # removes.
                    if len(live_queue_paths) != len(queue_paths):
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            "done task lists a **Queue actions:** path that is "
                            "not a live queue item",
                            "drop the resolved path, or restore the item it names",
                        )
                    for target in live_queue_paths:
                        rel_target = target.relative_to(REPO).as_posix()
                        if Path(rel_target).parts[1] != "needs-agent":
                            continue
                        if delivery_class(target.name) == "non-blocking":
                            continue
                        yield Finding(
                            "task-structure",
                            rel / "task.md",
                            f"done task still owes agent action `{rel_target}`",
                            "resolve or transfer it, or reclassify its timing; a "
                            "task is done when the agent owes nothing",
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


def check_stale_task():
    """Advisory: an in-progress task nobody has touched has probably lost its claim.

    Registered under its own id so the retry garbage collector — which only clears
    findings whose `Check` is a `CHECKS` key — can retire its items, and so one id
    maps to exactly one severity tier.
    """
    for task in sorted(live_task_directories()):
        rel = task.relative_to(REPO)
        if rel.parts[1] != "1_in-progress" or not task.is_dir():
            continue
        if days_old(task) > STALE_TASK_DAYS:
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
    activations = []
    for candidate_head in candidate_activation_heads(head):
        found, error = schema_activation_commits(
            candidate_head,
            "tasks/AGENTS.md",
            "Task admission schema",
        )
        if error:
            raise GitSnapshotError(error)
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


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
            *RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M",
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
    cache_key = (revision, task_id)
    if _GIT_SNAPSHOT_CACHE_ACTIVE and cache_key in _TASK_SNAPSHOT_CACHE:
        return _TASK_SNAPSHOT_CACHE[cache_key]
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
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _TASK_SNAPSHOT_CACHE[cache_key] = None
        return None
    task_path = Path(incarnations[0])
    task_bytes = (
        repo_artifact_bytes(REPO / task_path)
        if revision is None
        else git_artifact_bytes_at(revision, task_path.as_posix())
    )
    if task_bytes is None:
        if _GIT_SNAPSHOT_CACHE_ACTIVE:
            _TASK_SNAPSHOT_CACHE[cache_key] = None
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
    result = allowed, artifacts
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        _TASK_SNAPSHOT_CACHE[cache_key] = result
    return result


def task_action_origin_problems(parent, revision):
    """Yield newly introduced unprojected human actions on one task edge."""
    for task_id in sorted(task_ids_changed_on_edge(parent, revision)):
        after = task_snapshot(revision, task_id)
        after_allowed, after_artifacts = after or (set(), {})
        before_counts = {}
        after_counts = {}
        after_paths = {}
        baselines = candidate_parent_oids(revision) or (parent,)
        for baseline in baselines:
            before = task_snapshot(baseline, task_id)
            before_allowed, before_artifacts = before or (set(), {})
            parent_counts = {}
            for _filename, (before_path, before_text) in sorted(
                before_artifacts.items()
            ):
                for excerpt, count in task_action_unit_counts(
                    before_text,
                    before_path,
                    before_allowed,
                    repo=REPO,
                    candidate_revision=baseline,
                ).items():
                    parent_counts[excerpt] = (
                        parent_counts.get(excerpt, 0) + count
                    )
            for excerpt, count in parent_counts.items():
                before_counts[excerpt] = max(
                    before_counts.get(excerpt, 0), count
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


def task_recorded_at_other_parent(task_id, parent, revision):
    """Return whether another parent of one candidate already recorded a task."""
    for other in candidate_parent_oids(revision):
        if other == parent:
            continue
        if task_id in task_record_paths_at(other):
            return True
    return False


def task_status_at_other_parent(task_id, status, parent, revision):
    """Return whether another parent of one candidate already held this status.

    The transition half of `task_recorded_at_other_parent`. A merge that only
    inherits a task took no lifecycle step for it: the parent that already sat at
    this status reached it through its own governed edges, which
    `queue_revision_edges` yields for the same candidate, so every step is still
    validated by the transition table there. Without this, merging a trunk into a
    branch reports every trunk merge whose incoming side advanced a task two
    statuses as a jump on the trunk-side edge
    (`tasks/4_done/2026-07-25-fix-merge-parent-task-topology/design.md` chose the
    same shape for creations).

    The status must match exactly. A sibling parent holding the task at some other
    status justifies nothing about the status the merge produced, so an illegal
    advance no parent had reached is still reported. A single-parent edge has no
    sibling to consult, so linear behaviour is unchanged.
    """
    for other in candidate_parent_oids(revision):
        if other == parent:
            continue
        records = task_record_paths_at(other).get(task_id, [])
        # One incarnation only, matching the duplicate guard in the caller;
        # `task-structure` owns a task recorded in two statuses at once.
        if len(records) == 1 and records[0][0] == status:
            return True
    return False


def task_artifact_renames_on_edge(parent, revision):
    """Return detected task-local renames on one exact Git/index edge."""
    command = (
        [
            *RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M",
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
            # A merge parent that predates a task is no lifecycle step for it;
            # the parent holding the record supplies the validating edge.
            if status != "0_backlog" and not task_recorded_at_other_parent(
                task_id, parent, revision
            ):
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
            # A merge parent that already sat at this status is no lifecycle step;
            # the parent holding it supplies the validating edges.
            if task_status_at_other_parent(task_id, status, parent, revision):
                continue
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
    if not activations and enabled and _GIT_HEAD_OID:
        activations = (_GIT_HEAD_OID,)
    edges = task_admission_edges(activations)
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
            name = path.as_posix()
            if name in committed or path_is_git_ignored(name):
                continue
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


def handover_schema_version(field, versions):
    """Return one declared handover schema version from the candidate contract."""
    contract = repo_artifact_bytes(REPO / "history" / "AGENTS.md")
    if contract is None:
        return None
    version = text_fields(
        contract.decode("utf-8")
    ).get(field, "").strip()
    return version if version in versions else None


def handover_action_entry_version():
    return handover_schema_version(HANDOVER_ENTRY_FIELD, HANDOVER_ENTRY_VERSIONS)


def handover_liveness_version():
    return handover_schema_version(
        HANDOVER_LIVENESS_FIELD, HANDOVER_LIVENESS_VERSIONS
    )


def schema_version_at_least(version, floor, versions):
    """Compare two declared schema versions; an unknown one counts as older."""
    if version not in versions or floor not in versions:
        return False
    return versions.index(version) >= versions.index(floor)


def entry_version_at_least(version, floor):
    return schema_version_at_least(version, floor, HANDOVER_ENTRY_VERSIONS)


def liveness_version_at_least(version, floor):
    return schema_version_at_least(version, floor, HANDOVER_LIVENESS_VERSIONS)


def handover_action_entry_enabled():
    return handover_action_entry_version() is not None


def history_service_present():
    if (REPO / ".git").exists():
        return bool(git_index_entries("history"))
    return (REPO / "history").is_dir()


def handover_schema_activations(field, version="v1"):
    """Return committed activations of one schema version, including merges."""
    revision = committed_candidate_revision()
    if revision is None:
        return ()
    activations = []
    for candidate_head in candidate_activation_heads(revision):
        found, _error = projection_schema_activation_commits(
            candidate_head,
            field=field,
            version=version,
        )
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


def handover_action_entry_activations(version="v1"):
    """Return committed entry-version activations, including merged branches."""
    return handover_schema_activations(HANDOVER_ENTRY_FIELD, version)


def handover_liveness_activations(version="v1"):
    """Return committed liveness-version activations, including merged branches."""
    return handover_schema_activations(HANDOVER_LIVENESS_FIELD, version)


def handover_projection_activations():
    """Return committed queue-projection activations, including merged branches."""
    revision = committed_candidate_revision()
    if revision is None:
        return ()
    activations = []
    for candidate_head in candidate_activation_heads(revision):
        found, _error = projection_schema_activation_commits(
            candidate_head,
            field="Queue projection schema",
        )
        activations.extend(found)
    return tuple(dict.fromkeys(activations))


def handover_creation_contract_version(rel, field, versions):
    """Return the version this record's own creation snapshot declared.

    An author can read exactly one marker while writing: the one in
    `history/AGENTS.md` in the tree that carries the record. That value already
    accounts for every activation *and every withdrawal* on the record's own
    line of history, so a number that was activated, rolled back, and later
    reused governs nothing in between. No parallel or later commit can change
    it, which is what makes it the only grammar an immutable record can be held
    to (`automation/AGENTS.md`, `history/AGENTS.md`).
    """
    if CHANGE_RANGE is None:
        created_at = staged_side_creation_commit(rel.as_posix())
        if created_at is None:
            return handover_schema_version(field, versions), None
    else:
        created_at, creation_error = handover_creation_commit(rel)
        if creation_error:
            return None, creation_error
    contract = git_artifact_bytes_at(created_at, "history/AGENTS.md")
    if contract is None:
        return None, None
    version = text_fields(decode_utf8_artifact(
        contract, f"`history/AGENTS.md` at {created_at}"
    )).get(field, "").strip()
    return version if version in versions else None, None


def handover_schema_version_for(rel, field, versions):
    """Return the highest version of one schema the admission edge raises.

    This is the anti-dodge floor, not the record's grammar: a history joined
    with an activation is governed by it, so cutting a branch before a version
    that rejects more cannot escape those rejections. It only ever ratchets up,
    so it can never demand bytes an already-committed record lacks — that is
    `handover_creation_contract_version`'s job.
    """
    current_version = handover_schema_version(field, versions)
    activation_map = {
        version: handover_schema_activations(field, version)
        for version in versions
    }
    if current_version is None and not any(activation_map.values()):
        return None, None
    if CHANGE_RANGE is None:
        return handover_creation_contract_version(rel, field, versions)
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
    for version in versions:
        activations = activation_map[version]
        if not activations:
            activations, activation_error = projection_schema_activation_commits(
                candidate,
                field=field,
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


def handover_action_entry_version_for(rel):
    """Return this handover's entry rejection floor, then its written grammar.

    The floor ratchets at the admission edge and selects which rejecting
    clauses apply. The grammar is what the record's creation snapshot declared
    and selects how its suffix is spelled — the one obligation a committed
    record can never satisfy after the fact, because its bytes are immutable.
    The floor is never below the grammar: a snapshot that declares a version is
    itself an activation of it.
    """
    floor, floor_error = handover_schema_version_for(
        rel, HANDOVER_ENTRY_FIELD, HANDOVER_ENTRY_VERSIONS
    )
    if floor_error:
        return None, None, floor_error
    grammar, grammar_error = handover_creation_contract_version(
        rel, HANDOVER_ENTRY_FIELD, HANDOVER_ENTRY_VERSIONS
    )
    return floor, grammar, grammar_error


def handover_liveness_version_for(rel):
    """Return the highest liveness schema governing this handover's creation."""
    return handover_schema_version_for(
        rel, HANDOVER_LIVENESS_FIELD, HANDOVER_LIVENESS_VERSIONS
    )


def newly_added_handovers():
    """Return handovers added in the staged diff or an explicit CI range."""
    if CHANGE_RANGE is None and not (REPO / ".git").exists():
        return set(), None
    if CHANGE_RANGE is None:
        parent_paths = set()
        for parent in staged_parent_oids():
            tree = subprocess.run(
                [
                    "git", "--no-replace-objects", "ls-tree", "-r",
                    "--name-only", "-z", parent, "--",
                    "history/conversations",
                ],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if tree.returncode:
                return set(), git_failure(
                    tree, f"could not inspect handovers at {parent}"
                )
            parent_paths.update(
                raw.decode("utf-8", errors="surrogateescape")
                for raw in tree.stdout.split(b"\0")
                if raw
            )
        indexed = {
            name
            for name, mode in git_index_entries(
                "history/conversations"
            ).items()
            if mode in ("100644", "100755")
        }
        lines = sorted(
            name
            for name in indexed
            if name not in parent_paths
            or staged_side_creation_commit(name) is not None
        )
    elif CHANGE_RANGE and CHANGE_RANGE.startswith("root:"):
        command = [
            *RAW_GIT, "ls-tree", "-r", "--name-only",
            CHANGE_RANGE[len("root:"):], "--", "history/conversations",
        ]
    else:
        command = [
            *RAW_GIT, "diff", "--no-renames", "--name-only", "--diff-filter=A",
        ]
        command.append(CHANGE_RANGE if CHANGE_RANGE else "--cached")
        command.extend(["--", "history/conversations"])
    if CHANGE_RANGE is not None:
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
        returncode, common, detail = git_merge_base_result(base, head)
        tree = subprocess.run(
            [
                *RAW_GIT, "ls-tree", "-r", "--name-only", head, "--",
                "history/conversations",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if returncode or tree.returncode:
            return set(), detail.strip() or tree.stderr.strip() \
                or "could not inspect range handover incarnations"
        boundary = common.strip()
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
            returncode, _detail = git_ancestry_probe(creation, boundary)
            if returncode != 0:
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


def live_queue_paths_by_actor():
    """Return the readable needs-human and needs-agent path sets in one walk.

    Which queue files exist is a property of the bound candidate — the captured
    index, the captured HEAD path set, and the untracked queue files on disk — not
    of the check asking, yet every governed handover asks for both sets. The answer
    is therefore derived once per candidate. `git_revision_candidate` drops it with
    the other candidate-scoped caches, so a rebound historical tree can never read
    the answer another tree produced.
    """
    global _LIVE_QUEUE_PATHS_CACHE
    if _GIT_SNAPSHOT_CACHE_ACTIVE and _LIVE_QUEUE_PATHS_CACHE is not None:
        return _LIVE_QUEUE_PATHS_CACHE
    human = set()
    agent = set()
    for item in live_queue_items() or ():
        if not readable_queue_item(item):
            continue
        actor = item.relative_to(QUEUE).parts[0]
        if actor == "needs-human":
            human.add(item.relative_to(REPO).as_posix())
        elif actor == "needs-agent":
            agent.add(item.relative_to(REPO).as_posix())
    result = (human, agent)
    if _GIT_SNAPSHOT_CACHE_ACTIVE:
        _LIVE_QUEUE_PATHS_CACHE = result
    return result


def live_human_queue_paths():
    """Return every readable needs-human item, whatever state it is in.

    This answers "does the file exist", not "does it still await its owner" —
    `human_action_unresolved` answers that, and a projection governed by
    action-entry v3 applies it on top of this set (history/AGENTS.md).
    """
    # A fresh set per caller: the shared answer is derived once, but a caller that
    # narrows or extends its copy must not edit the next caller's view.
    return set(live_queue_paths_by_actor()[0])


def live_agent_queue_paths():
    return set(live_queue_paths_by_actor()[1])


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
        created_at = staged_side_creation_commit(rel.as_posix())
        if created_at is not None:
            artifact = git_artifact_bytes_at(created_at, rel.as_posix())
            tree = subprocess.run(
                [
                    "git", "--no-replace-objects", "ls-tree", "-r", "-z",
                    created_at, "--", "message-queue",
                ],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if artifact is None or tree.returncode:
                return None, None, None, git_failure(
                    tree, "could not read the staged-side creation snapshot"
                )
            live_human, live_agent = split_live_queue_entries(
                parse_git_tree_records(tree.stdout)
            )
            return (
                decode_utf8_artifact(
                    artifact, f"`{rel}` at {created_at}"
                ),
                live_human,
                live_agent,
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
        [*RAW_GIT, "show", f"{created_at}:{rel.as_posix()}"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    tree = subprocess.run(
        [
            *RAW_GIT, "ls-tree", "-r", "-z", created_at, "--",
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


def handover_queue_text_at_creation(rel, queue_path):
    """Read one queue item from the handover's immutable creation snapshot."""
    if CHANGE_RANGE is None:
        created_at = staged_side_creation_commit(rel.as_posix())
        artifact = (
            git_artifact_bytes_at(created_at, queue_path)
            if created_at is not None
            else repo_artifact_bytes(REPO / queue_path)
        )
    else:
        created_at, creation_error = handover_creation_commit(rel)
        if creation_error:
            return None, creation_error
        artifact = git_artifact_bytes_at(created_at, queue_path)
    if artifact is None:
        return None, f"`{queue_path}` is absent from the creation snapshot"
    return decode_utf8_artifact(
        artifact, f"`{queue_path}` in the handover creation snapshot"
    ), None


def human_action_unresolved(text):
    """Return whether a needs-human item still owes its owner an action.

    An item awaits its owner until a concrete ``**Your answer:**`` or
    ``**Your review:**`` is committed; the later ``waiting`` -> ``folding``
    claim only moves an already-answered item to the agent. ``awaiting-artifact``
    binds nothing to judge, so it is an agent's turn from the start. Anything
    else — an absent, empty, or unrecognised ``**Status:**``, a blank response
    placeholder, or text that could not be read at all — stays unresolved, so a
    malformed item is repeated to its owner rather than silently withheld.
    """
    if text is None:
        return True
    status = text_fields(text).get("Status", "").strip().strip("`")
    if status == QUEUE_UNBOUND_HUMAN_STATUS:
        return False
    if status not in QUEUE_ANSWERABLE_HUMAN_STATUSES:
        return True
    return first_concrete_response(human_response_fields(text)) is None


def unresolved_human_queue_paths(rel, paths):
    """Keep only the creation-snapshot human actions that still await the human."""
    unresolved = set()
    for path in sorted(paths):
        text, read_error = handover_queue_text_at_creation(rel, path)
        if read_error or human_action_unresolved(text):
            unresolved.add(path)
    return unresolved


def handover_queue_fields_at_creation(rel, queue_path, required):
    """Read projection fields from the handover's immutable creation snapshot."""
    text, read_error = handover_queue_text_at_creation(rel, queue_path)
    if read_error:
        return None, read_error
    counts = field_counts(text)
    got = text_fields(text)
    projected = {}
    for slot in required:
        # A slot may accept several spellings of one sentence. The snapshot must
        # settle on exactly one of them, and the caller reads it by canonical
        # name, so a legacy record projects correctly under a later grammar.
        aliases = (slot,) if isinstance(slot, str) else tuple(slot)
        present = [alias for alias in aliases if counts.get(alias, 0) >= 1]
        if len(present) != 1 or counts.get(present[0], 0) != 1:
            return None, (
                f"`{queue_path}` must contain exactly one **{aliases[0]}:**"
            )
        value = got.get(present[0], "").strip()
        if not has_concrete_value(value):
            return None, (
                f"`{queue_path}` has no concrete **{present[0]}:**"
            )
        projected[aliases[0]] = value
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
    candidate_revision = revision if CHANGE_RANGE is not None else None
    candidate = candidate_path_entry(candidate_revision, rel.as_posix())
    for parent in candidate_parent_oids(candidate_revision):
        if git_tree_path_entry(parent, rel.as_posix()) == candidate:
            revision = parent
            break
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
    # The creation commit is a full object ID, so its bytes come from the reusable
    # `cat-file --batch` reader rather than one `git show` per handover. That reader
    # is launched with `--no-replace-objects`, so routing this read through it is
    # strictly stronger than hardening a per-handover `git show`.
    artifact = git_artifact_bytes_at(created_at, rel.as_posix())
    if artifact is None:
        return None, "could not read creation bytes"
    return decode_utf8_artifact(
        artifact, f"`{rel.as_posix()}` at {created_at}"
    ), None


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
    entry_grammar,
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
    if entry_version_at_least(entry_version, "v2") \
            and action_like_rendered_prose(raw_outside):
        problems.append(
            "contains an action-like rendered question or directive outside "
            "the top-level action list"
        )
    for index, entry in enumerate(entries, start=1):
        raw_entry = raw_entries[index - 1] if index <= len(raw_entries) else ""
        if entry_version_at_least(entry_version, "v2") \
                and contains_raw_html(raw_entry):
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
            ("Action",) + HUMAN_PROJECTION_FIELD_PAIRS
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

        if actor != "needs-human":
            expected_context = ""
        elif entry_grammar == "v3":
            # v3 renders the two sentences in English. Every record keeps the
            # suffix its own creation snapshot declared, byte for byte: a later
            # or parallel rename cannot be applied to bytes that are immutable.
            expected_context = (
                "— Why this matters: "
                + queue_fields[HUMAN_PROJECTION_FIELDS[0]]
                + " — If you do nothing: "
                + queue_fields[HUMAN_PROJECTION_FIELDS[1]]
            )
        else:
            expected_context = (
                "— Why-you-might-care: "
                + queue_fields[HUMAN_PROJECTION_FIELDS[0]]
                + " || If-you-do-nothing: "
                + queue_fields[HUMAN_PROJECTION_FIELDS[1]]
            )
        expected_context = render_inline_code(expected_context)
        for context in (
            copied_prose_without_links(entry),
            copied_prose_without_links(rendered_human_text(entry)),
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
                        "why-this-matters and if-you-do-nothing fields "
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


def handovers_created_in_commit(revision):
    """Return exact handover paths whose incarnation starts at one commit."""
    parents = revision_parents(
        revision, f"handover creation parents for {revision}"
    )
    if parents:
        changed = subprocess.run(
            [
                "git", "--no-replace-objects", "diff-tree", "-m", "-r",
                "--no-commit-id", "--name-only", "-z", "--no-renames",
                "--diff-filter=A", revision, "--", "history/conversations",
            ],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if changed.returncode:
            raise GitSnapshotError(git_failure(
                changed,
                f"could not inspect handover creations in {revision}",
            ))
        candidates = {
            raw.decode("utf-8", errors="surrogateescape")
            for raw in changed.stdout.split(b"\0")
            if raw
        }
    else:
        tree = subprocess.run(
            [
                "git", "--no-replace-objects", "ls-tree", "-r",
                "--name-only", "-z", revision, "--",
                "history/conversations",
            ],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if tree.returncode:
            raise GitSnapshotError(git_failure(
                tree,
                f"could not inspect root handover creations in {revision}",
            ))
        candidates = {
            raw.decode("utf-8", errors="surrogateescape")
            for raw in tree.stdout.split(b"\0")
            if raw
        }
    created = set()
    for path in candidates:
        if not governed_handover_path(path) \
                or git_tree_path_entry(revision, path) is None:
            continue
        if any(
            git_tree_path_entry(parent, path) is not None
            for parent in parents
        ):
            continue
        created.add(Path(path))
    return created


def handover_creation_events(activations):
    """Yield every governed committed handover incarnation admitted now."""
    seen_revisions = set()
    seen_events = set()
    for _parent, revision in queue_revision_edges(activations):
        if revision is None or revision in seen_revisions:
            continue
        seen_revisions.add(revision)
        for rel in handovers_created_in_commit(revision):
            event = (rel, revision)
            if event not in seen_events:
                seen_events.add(event)
                yield event


def current_handover_creation_commit(rel):
    """Return the committed add represented by the final candidate path."""
    if repo_artifact_bytes(REPO / rel) is None:
        return None
    if CHANGE_RANGE is None:
        return staged_side_creation_commit(rel.as_posix())
    created_at, error = handover_creation_commit(rel)
    return None if error else created_at


def check_handover_queue_projection():
    global _HANDOVER_HISTORY_RECHECK_ACTIVE
    if not history_service_present():
        return
    projection_activations = handover_projection_activations()
    entry_version_now = handover_action_entry_version()
    activated_entry_versions = [
        version for version in HANDOVER_ENTRY_VERSIONS
        if handover_action_entry_activations(version)
    ]
    if projection_activations \
            and not handover_projection_enabled():
        yield Finding(
            "handover-queue-projection",
            Path("history/AGENTS.md"),
            "Queue projection schema v1 was removed after activation",
            "restore **Queue projection schema:** v1 while history remains",
        )
    if activated_entry_versions:
        highest_activated = activated_entry_versions[-1]
        if not entry_version_at_least(entry_version_now, highest_activated):
            yield Finding(
                "handover-queue-projection",
                Path("history/AGENTS.md"),
                f"Queue action-entry schema {highest_activated} was removed "
                "or downgraded after activation",
                f"restore **Queue action-entry schema:** {highest_activated} "
                "or upgrade it further while history remains",
            )
    liveness_version_now = handover_liveness_version()
    activated_liveness_versions = [
        version for version in HANDOVER_LIVENESS_VERSIONS
        if handover_liveness_activations(version)
    ]
    if activated_liveness_versions:
        highest_liveness = activated_liveness_versions[-1]
        if not liveness_version_at_least(liveness_version_now, highest_liveness):
            yield Finding(
                "handover-queue-projection",
                Path("history/AGENTS.md"),
                f"Queue liveness schema {highest_liveness} was removed "
                "or downgraded after activation",
                f"restore **Queue liveness schema:** {highest_liveness} "
                "or upgrade it further while history remains",
            )
    if not handover_projection_enabled() and not projection_activations:
        return
    reported_mutations = set()
    mutation_activations = projection_activations
    if not mutation_activations and handover_projection_enabled() \
            and _GIT_HEAD_OID:
        mutation_activations = (_GIT_HEAD_OID,)
    if not _HANDOVER_HISTORY_RECHECK_ACTIVE:
        reported_history = set()
        _HANDOVER_HISTORY_RECHECK_ACTIVE = True
        try:
            for rel, revision in handover_creation_events(
                mutation_activations
            ):
                if current_handover_creation_commit(rel) == revision:
                    continue
                with git_revision_candidate(revision):
                    historical = list(
                        check_handover_queue_projection()
                    )
                for finding in historical:
                    identity = (
                        finding.check,
                        str(finding.subject),
                        finding.message,
                    )
                    if finding.subject != rel \
                            or identity in reported_history:
                        continue
                    reported_history.add(identity)
                    yield finding
        finally:
            _HANDOVER_HISTORY_RECHECK_ACTIVE = False
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
        entry_grammar = None
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
            entry_version, entry_grammar, strict_error = (
                handover_action_entry_version_for(rel)
            )
            if strict_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify strict action-entry activation: "
                    + strict_error,
                    "preserve the schema activation and handover creation commits",
                )
            liveness_version, liveness_error = handover_liveness_version_for(rel)
            if liveness_error:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "could not verify liveness schema activation: "
                    + liveness_error,
                    "preserve the schema activation and handover creation commits",
                )
            if liveness_version_at_least(
                liveness_version, UNRESOLVED_HUMAN_LIVENESS_VERSION
            ):
                # Only handovers governed by the liveness schema project the
                # narrowed set; every older record keeps the liveness rule it was
                # written and admitted under (history/AGENTS.md immutability).
                # This is a separate marker from the entry schema on purpose:
                # projection syntax and projected membership version apart, and
                # an in-flight branch already owns entry-schema version numbers.
                live_human = unresolved_human_queue_paths(rel, live_human)
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
            side_prior_incarnation = None
            if CHANGE_RANGE is None:
                side_creations = staged_side_creation_commits(
                    rel.as_posix()
                )
                for commit in side_creations[:-1]:
                    artifact = git_artifact_bytes_at(
                        commit, rel.as_posix()
                    )
                    if artifact is None:
                        continue
                    prior_text = decode_utf8_artifact(
                        artifact, f"`{rel}` at {commit}"
                    )
                    if text_fields(prior_text).get(
                        "Queue projection", ""
                    ).strip() != "v1":
                        continue
                    governed, governance_error = governed_by_activation_join(
                        commit, mutation_activations
                    )
                    if governance_error:
                        yield Finding(
                            "handover-queue-projection",
                            rel,
                            "could not verify prior side handover "
                            "incarnations: " + governance_error,
                            "preserve the side history or use a new "
                            "conversation folder",
                        )
                        break
                    if governed:
                        side_prior_incarnation = commit
                        break
            if side_prior_incarnation \
                    and side_prior_incarnation != prior_incarnation:
                yield Finding(
                    "handover-queue-projection",
                    rel,
                    "reuses a path that already has a committed governed v1 "
                    "side handover incarnation at "
                    f"{side_prior_incarnation}",
                    "keep committed handover paths single-incarnation; record "
                    "the correction in a new conversation handover",
                )
        else:
            text = candidate_text
        strict_entries = entry_version is not None
        if entry_version_at_least(entry_version, "v2") \
                and contains_raw_html(text):
            yield Finding(
                "handover-queue-projection",
                rel,
                "strict handover contains raw HTML outside code",
                "replace raw HTML with structural Markdown; arbitrary HTML "
                "cannot define or preserve queue-projection boundaries",
            )
            continue
        outside_sections = visible_outside_action_sections(
            text, ("Needs your attention", "Next steps")
        )
        if entry_version_at_least(entry_version, "v2") \
                and action_like_rendered_prose(outside_sections):
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
                            entry_grammar,
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
                entry_grammar,
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
    # A partial reversal keeps the old ADR `decided` — the clauses it did not overturn
    # still bind — so it cannot be marked superseded, and leaving it unmarked would
    # advertise the overturned clause to every booting agent. `Amends:` records that
    # middle state (`memory/AGENTS.md`); the amended entry is marked, not retired.
    amended = set()
    for zone, decision in memory_entries():
        if zone == "decisions":
            metadata = fields(decision)
            superseded.update(context_files(metadata.get("Supersedes", "")))
            amended.update(context_files(metadata.get("Amends", "")))
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
            elif zone == "decisions" and entry in amended:
                status = " **[amended]**"
            desc = metadata.get("Description", "").strip()
            lines.append(f"- [{title}]({entry.relative_to(MEMORY)}){status} — {desc}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def check_memory_index():
    index = MEMORY / "index.md"
    indexed = bool(git_index_entries("memory")) \
        if (REPO / ".git").exists() else False
    if not indexed and not MEMORY.is_dir():
        return
    artifact = repo_artifact_bytes(index)
    if artifact is None \
            or artifact.decode("utf-8") != generated_index():
        yield Finding("memory-index", index.relative_to(REPO),
                      "index does not match the memory files",
                      "run: python3 automation/reconcile/reconcile.py --fix-index")


def markdown_headings(text):
    """Return ATX heading titles in document order."""
    return [
        re.sub(r"[ \t]+#+[ \t]*$", "", matched.group(1))
        for matched in re.finditer(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", text, flags=re.M)
    ]


def anchor_slugs(headings):
    """Return GitHub heading anchors, numbering repeats in document order."""
    taken, slugs = {}, []
    for heading in headings:
        label = MARKDOWN_LINK_RE.sub(lambda m: m.group("label"), heading)
        base = re.sub(r"[^\w\- ]", "", label.lower()).replace(" ", "-")
        slug = base
        while slug in taken:
            taken[base] += 1
            slug = f"{base}-{taken[base]}"
        taken[slug] = 0
        slugs.append(slug)
    return slugs


def anchor_resolves(target, fragment):
    """Whether a Markdown target defines the anchor; an unreadable target passes."""
    if target is None or target.suffix != ".md":
        return True
    try:
        text = semantic_text(repo_text(target))
    except (GitSnapshotError, OSError, UnicodeDecodeError):
        return True
    return fragment in anchor_slugs(markdown_headings(text))


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
            # These lifecycle paths deliberately name artifacts that need not be
            # present in the current tree. Resolution evidence is predeclared and
            # must change when the action closes. A changes-requested review names
            # its successor before the resolution edge creates it; successor and
            # follow-up records retain historical lineage after their predecessors
            # are deleted. Queue lifecycle checks validate those relationships
            # against Git history instead of current-tree link existence.
            text = re.sub(
                r"^\*\*(?:Resolution evidence|Successor action|"
                r"Supersedes|Follow-up review|Depends on):\*\*[^\n]*$",
                "",
                text,
                flags=re.M,
            )
            # A human answers in one edit, and naming a file in that sentence is
            # the most natural thing to write — often a file the answer is asking
            # someone to create, which by definition does not exist yet. Their own
            # commit must not be rejected for it, and no repair exists if it is:
            # the first response is immutable and agents may not edit human text
            # (`message-queue/AGENTS.md`). The path stays readable to the agent
            # folding the answer; only its existence stops being a commit gate.
            text = re.sub(
                r"^\*\*(?:Your answer|Your review):\*\*[^\n]*$",
                "",
                text,
                flags=re.M,
            )
        candidates = set(BACKTICK_RE.findall(text))
        candidates.update(markdown_link_destinations(text))
        quoted_sources = {
            destination for _label, destination, _body in sourced_quotes(text)
        } if parts[:2] == ("message-queue", "needs-human") else set()
        for destination in sorted(candidates):
            cand, _, fragment = destination.partition("#")
            if cand.startswith(LINK_SKIP_PREFIXES) or any(c in cand for c in "*<>{}$"):
                continue
            if cand.count("/") < 1 or (cand.count("/") == 1 and cand.endswith("/")):
                continue
            if not re.fullmatch(r"[\w./-]+", cand):
                continue
            if PurePosixPath(cand).is_absolute():
                # An absolute path cannot name a repository artifact, so resolving one
                # falls through to probing the host filesystem — the only part of this
                # check whose answer depends on the machine running it. Two CI failures
                # came from records that named a real local binary: green on the author's
                # machine, red on the runner. Decide it here so the verdict is the same
                # everywhere and lands on the commit that introduces it.
                yield Finding(
                    "link-check", rel,
                    f"`{cand}` is an absolute path, so it names a machine and not "
                    "this repository",
                    "unquote it — backticks assert a repository path, and this one "
                    "resolves differently on each machine",
                )
                continue
            if cand.startswith(("message-queue/needs-human/", "message-queue/needs-agent/")):
                # A queue action is resolved by deleting its file
                # (`message-queue/AGENTS.md`), so any citation of one — from a
                # design doc's evidence trail, not only from the queue's own
                # predeclared fields above — names history, not a live link.
                continue
            if destination in quoted_sources:
                # The quote and the ordinary link scan must select the same
                # captured artifact. Generic links retain their existing path
                # policy; a source citation never follows an unstaged symlink
                # or switches from a queue-local source to a root-name collision.
                target = quote_link_target(md, destination)
                relative = target.relative_to(REPO).as_posix() if target is not None else None
                exists = bool(relative is not None and (
                    git_index_entry_mode(relative) is not None or bool(git_index_entries(relative))
                )) if (REPO / ".git").exists() else target is not None and quote_source_text(target) is not None
                if not exists:
                    yield Finding("link-check", rel, f"`{cand}` does not exist",
                                  "fix the path, create the target, or unquote if not a path")
                    continue
                raw = quote_source_text(target)
                # Line fragments are not heading names. Their bounds and quoted
                # content belong to the advisory source-evidence check.
                line_fragment = re.fullmatch(r"L[0-9]+(?:-L[0-9]+)?", fragment)
                if fragment and not line_fragment and target.suffix.lower() == ".md" \
                        and raw is not None and anchored_section_source(target, fragment, raw) is None:
                    yield Finding("link-check", rel,
                                  f"`{cand}` has no `{fragment}` heading anchor",
                                  f"point the link at a heading in `{cand}` or add "
                                  f"one whose slug is `{fragment}`")
                continue
            if PurePosixPath(cand).suffix not in LINK_PATH_EXTENSIONS:
                top = cand.split("/", 1)[0]
                # Tracked content only, matching `repo_artifact_bytes` — otherwise
                # VCS-internal paths such as `.git/objects` would count as a known
                # prefix just because that directory happens to exist on disk.
                known_top = bool(git_index_entries(top)) if (REPO / ".git").exists() \
                    else (REPO / top).exists()
                if not known_top:
                    continue  # ordinary prose (`24/7`, `and/or`): no known
                              # extension and no real top-level entry to root it
            try:
                root_target = REPO / cand
                local_target = (md.parent / cand).resolve()
                target = None
                root_exists = repo_artifact_bytes(root_target) is not None \
                    or bool(git_index_entries(cand))
                if root_exists:
                    target = root_target
                local_exists = False
                try:
                    local_rel = local_target.relative_to(REPO.resolve()).as_posix()
                    local_exists = repo_artifact_bytes(REPO / local_rel) is not None \
                        or bool(git_index_entries(local_rel))
                    if local_exists and target is None:
                        target = REPO / local_rel
                except ValueError:
                    local_exists = local_target.exists()
                if root_exists or local_exists:
                    if fragment and not anchor_resolves(target, fragment):
                        yield Finding("link-check", rel,
                                      f"`{cand}` has no `{fragment}` heading anchor",
                                      f"point the link at a heading in `{cand}` or add "
                                      f"one whose slug is `{fragment}`")
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
    if not candidate_has_file(root):
        return
    mode = fields(root).get("Collaboration mode", "").strip("`* ").split("`")[0].strip("` ")
    if mode not in ("autonomous", "async", "pair"):
        yield Finding("mode-valid", "AGENTS.md",
                      f"collaboration mode {mode!r} is not autonomous|async|pair",
                      "fix the **Collaboration mode:** line")


def check_roadmap_fresh():
    current = REPO / "roadmap" / "current-state.md"
    done = TASKS / "4_done"
    if not candidate_has_file(current):
        return
    updated = parse_date(fields(current).get("Last-updated", ""))
    if (REPO / ".git").exists():
        done_ids = {
            Path(name).parts[2]
            for name in git_index_entries("tasks/4_done")
            if len(Path(name).parts) >= 4
            and TASK_ID_RE.fullmatch(Path(name).parts[2])
        }
        # TASK_ID_RE accepts an impossible calendar date such as 2026-02-30, and
        # parse_date returns None for it; max() must never compare None to a date.
        newest = max(
            (filed for filed in map(parse_date, done_ids) if filed),
            default=None,
        )
    elif done.is_dir():
        newest = max((parse_date(t.name) for t in done.iterdir()
                      if t.is_dir() and parse_date(t.name)), default=None)
    else:
        return
    if updated and newest and updated < newest:
        yield Finding("roadmap-fresh", "roadmap/current-state.md",
                      f"Last-updated {updated} predates the newest done task ({newest})",
                      "re-read current-state.md against reality and bump Last-updated")


# ---------------------------------------- owner words, labelled criteria, goal fit


def task_id_date(task_id):
    """Return the filing date a task id carries, or None for an impossible one."""
    try:
        return datetime.date.fromisoformat(task_id[:10])
    except ValueError:
        return None


def task_is_new(task_id):
    """Whether a task was filed under the provenance grammar.

    The date prefix of the immutable folder id decides it, on or after
    `TASK_PROVENANCE_SINCE`; an older record is judged by the grammar it was written
    under and only receives `task-provenance-advice`
    (`memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md`).
    """
    filed = task_id_date(task_id)
    return filed is not None and filed >= TASK_PROVENANCE_SINCE


def fenced_words_follow(raw_lines, start):
    """Whether a ```text fence holding at least one non-blank line opens at `start`.

    Blank lines between an entry heading and its fence are allowed; anything else in
    between is not, because an entry holds the owner's words and nothing of the
    agent's. The fence is read from the raw lines: `semantic_text` blanks it, which is
    exactly why the words inside are data to every other check.
    """
    index = start
    while index < len(raw_lines) and not raw_lines[index].strip():
        index += 1
    if index >= len(raw_lines):
        return False
    opening = REQUIREMENTS_FENCE_OPEN_RE.match(raw_lines[index])
    if not opening:
        return False
    closing = re.compile(r"^ {0,3}`{%d,}[ \t]*$" % len(opening.group("fence")))
    words = False
    for line in raw_lines[index + 1:]:
        if closing.match(line):
            return words
        if line.strip():
            words = True
    return False


def requirements_record(text):
    """Parse one requirements.md into its dated entries and its no-owner-words line.

    Returns `(entries, unfenced, no_words, other)`: `entries` lists `(date, source)`
    for every well-formed entry, `unfenced` lists entry headings not followed by a
    ```text fence holding words, `no_words` counts the exact
    `No owner words — filed by … from `…`.` line, and `other` lists level-two
    headings that are not dated entries. Fenced content is never parsed.
    """
    raw_lines = [line.removesuffix("\n") for line in commonmark_lines(text)]
    clean_lines = [
        line.removesuffix("\n") for line in commonmark_lines(semantic_text(text))
    ]
    entries, unfenced, other = [], [], []
    no_words = 0
    for index, line in enumerate(clean_lines):
        if NO_OWNER_WORDS_RE.match(line):
            no_words += 1
            continue
        heading = SECTION_HEADING_RE.match(line)
        if not heading:
            continue
        entry = REQUIREMENTS_ENTRY_RE.match(heading.group(1))
        if not entry:
            other.append(heading.group(1))
        elif fenced_words_follow(raw_lines, index + 1):
            entries.append((entry.group(1), entry.group(2)))
        else:
            unfenced.append(heading.group(1))
    return entries, unfenced, no_words, other


def task_criteria(task_text):
    """Return the checkbox lines under `## Acceptance criteria`, boxes stripped."""
    body = level_two_section_body(task_text, "## Acceptance criteria")
    if body is None:
        return []
    criteria = []
    for line in body.splitlines():
        matched = CRITERION_LINE_RE.match(line)
        if matched:
            criteria.append(matched.group(1))
    return criteria


def criterion_provenance(criterion):
    """Classify one criterion's label.

    Returns `("user", date)` for `[user <date>]`, `("derived", has_reason)` for
    `[derived]` — the reason is whatever follows a ` — ` later on the line — and
    `(None, None)` for an unlabelled line.
    """
    matched = CRITERION_USER_RE.match(criterion)
    if matched:
        return "user", matched.group(1)
    matched = CRITERION_DERIVED_RE.match(criterion)
    if matched:
        return "derived", " — " in criterion[matched.end():]
    return None, None


def task_fit(task_text):
    """Return the bold-key fields of `## Fit`, or None when the section is absent.

    Read from the section body, not from the whole file: `text_fields` keeps the last
    duplicate of a key, and nothing outside the section may speak for it.
    """
    body = level_two_section_body(task_text, "## Fit")
    return None if body is None else text_fields(body)


def fit_value(value):
    """Return the fit word before its dash, lowercased: `aligned` from `aligned — …`."""
    return re.split(r"\s+(?:—|-)\s+", (value or "").strip(), maxsplit=1)[0].lower()


def fit_required(scope, status):
    """Whether `## Fit` is required: behaviour-changing scope, at or past the start."""
    return bool(scope) and scope != "records-only" and status in FIT_REQUIRED_STATUSES


def fit_queue_paths(task_text):
    """Return the task's `Queue actions` paths; a malformed field is task-structure's."""
    try:
        return list(task_queue_action_paths_from_text(task_text))
    except ValueError:
        return []


def level_two_sections(text):
    """Return `[(heading, body)]` for every level-two section, in document order."""
    clean = semantic_text(text)
    matches = list(SECTION_HEADING_RE.finditer(clean))
    sections = []
    for index, matched in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
        sections.append((matched.group(1), clean[matched.end():end]))
    return sections


def roadmap_goals():
    """Return `{goal id: (title, fields)}` from the candidate roadmap; `{}` without one."""
    roadmap = REPO / ROADMAP_DESIRED_STATE
    if not candidate_has_file(roadmap):
        return {}
    goals = {}
    for heading, body in level_two_sections(repo_text(roadmap)):
        matched = GOAL_HEADING_RE.match(heading)
        if matched and matched.group(1) not in goals:
            goals[matched.group(1)] = (matched.group(2), text_fields(body))
    return goals


def provenance_task_records():
    """Yield `(task, status, task text)` for every live task folder with a task.md."""
    for task in sorted(live_task_directories()):
        rel = task.relative_to(REPO)
        if len(rel.parts) != 3 or rel.parts[1] not in TASK_STATUSES:
            continue
        if not TASK_ID_RE.fullmatch(task.name):
            continue
        if repo_artifact_bytes(task / "task.md") is None:
            continue
        yield task, rel.parts[1], repo_text(task / "task.md")


def requirements_findings(task, rel, task_text):
    """Yield the blocking findings for one new task's owner words and labels.

    Whether the record says there are no owner words is read separately, by
    `requirements_no_words`.
    """
    requirements = task / "requirements.md"
    # A `[user <date>]` label is resolved only against a file that has at least one
    # dated heading, fenced or not: a missing file, or one with no entry at all, is
    # already one finding, and the label's problem is that same missing entry.
    entry_dates = None
    if repo_artifact_bytes(requirements) is None:
        yield Finding(
            "task-provenance", rel, "missing requirements.md",
            "copy templates/task/requirements.md: quote the owner's words verbatim "
            "under a dated heading, or write the single no-owner-words line",
        )
    else:
        entries, unfenced, no_words, other = requirements_record(
            repo_text(requirements)
        )
        dated = [date for date, _source in entries] + [
            REQUIREMENTS_ENTRY_RE.match(heading).group(1) for heading in unfenced
        ]
        entry_dates = set(dated) if dated else None
        for heading in unfenced:
            yield Finding(
                "task-provenance", rel / "requirements.md",
                f"entry `## {heading}` is not followed by a ```text fence holding "
                "the owner's words",
                "put the words, exactly as written, in a ```text fence directly "
                "under the dated heading",
            )
        for heading in other:
            yield Finding(
                "task-provenance", rel / "requirements.md",
                f"heading `## {heading}` is not a dated owner entry",
                "requirements.md holds owner words only, under "
                "`## <YYYY-MM-DD> — <source>` headings each over a ```text fence; "
                "interpretation belongs in task.md",
            )
        if (entries or unfenced) and no_words:
            yield Finding(
                "task-provenance", rel / "requirements.md",
                "carries both dated owner entries and the no-owner-words line",
                "keep the dated entries and delete the no-owner-words line",
            )
        elif not entries and not unfenced and not no_words:
            yield Finding(
                "task-provenance", rel / "requirements.md",
                "holds neither a dated owner entry nor the no-owner-words line",
                "quote the owner under `## <YYYY-MM-DD> — <source>` in a ```text "
                "fence, or write exactly `No owner words — filed by <who> from "
                "`<durable source path>`.`",
            )
        if no_words > 1:
            yield Finding(
                "task-provenance", rel / "requirements.md",
                "the no-owner-words line appears more than once",
                "keep exactly one",
            )
    for criterion in task_criteria(task_text):
        kind, detail = criterion_provenance(criterion)
        excerpt = criterion if len(criterion) <= 60 else criterion[:57] + "..."
        if kind is None:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"acceptance criterion lacks a provenance label: {excerpt}",
                "open every criterion with `[user <YYYY-MM-DD>]`, the requirements.md "
                "entry it traces to, or `[derived]` with its reason after ` — `",
            )
        elif kind == "user" and entry_dates is not None \
                and detail not in entry_dates:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"criterion cites `[user {detail}]` but requirements.md has no "
                f"entry dated {detail}",
                "append the owner's words of that date to requirements.md, or label "
                "the criterion `[derived]` with a reason",
            )
        elif kind == "derived" and not detail:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"`[derived]` criterion gives no reason: {excerpt}",
                "end the line with ` — <why the owner's words need this>`",
            )


def requirements_no_words(task):
    """Whether a task's requirements.md says there are no owner words."""
    requirements = task / "requirements.md"
    if repo_artifact_bytes(requirements) is None:
        return False
    return requirements_record(repo_text(requirements))[2] > 0


def fit_findings(rel, fit, queue_paths, goals):
    """Yield the blocking findings for one `## Fit` section, in any task."""
    serves = fit.get("Serves", "").strip()
    goal_match = FIT_SERVES_GOAL_RE.match(serves)
    none_match = FIT_SERVES_NONE_RE.match(serves)
    if goal_match:
        goal_id = goal_match.group(1)
        if goal_id not in goals:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"**Serves:** names {goal_id}, which is not a `## {goal_id} — ` "
                f"heading in {ROADMAP_DESIRED_STATE}",
                "name a goal that exists, add the goal from "
                "templates/roadmap/goal.md, or write `none — `<clarification path>``",
            )
    elif none_match:
        path = none_match.group(1)
        if not path.startswith(CLARIFICATIONS_PREFIX) \
                or repo_artifact_bytes(REPO / path) is None:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"**Serves:** none names `{path}`, which is not a live item under "
                f"{CLARIFICATIONS_PREFIX}",
                "file the clarification from templates/queue/clarification.md, "
                "asking which goal this task serves, and name its path",
            )
        elif path not in queue_paths:
            yield Finding(
                "task-provenance", rel / "task.md",
                f"**Serves:** none names `{path}`, which **Queue actions:** does "
                "not list",
                "list the clarification in Queue actions so the task carries its "
                "open question",
            )
    elif has_concrete_value(serves):
        yield Finding(
            "task-provenance", rel / "task.md",
            "**Serves:** is neither `G<n> — <the goal's title>` nor "
            "`none — `<clarification path>``",
            f"copy the goal's heading text from {ROADMAP_DESIRED_STATE}, or file "
            "the clarification and name it",
        )
    value = fit_value(fit.get("Fit", ""))
    if not has_concrete_value(fit.get("Fit", "")):
        return
    if value not in FIT_VALUES:
        yield Finding(
            "task-provenance", rel / "task.md",
            f"**Fit:** {fit.get('Fit', '').strip()!r} does not open with aligned, "
            "extends, conflicts, or unclear",
            "write `**Fit:** <aligned | extends | conflicts | unclear> — <one "
            "sentence>`",
        )
    elif value in ("conflicts", "unclear") and not any(
        path.startswith((CLARIFICATIONS_PREFIX, DECISIONS_PREFIX))
        for path in queue_paths
    ):
        yield Finding(
            "task-provenance", rel / "task.md",
            f"**Fit:** {value} without a needs-human clarification or decision in "
            "**Queue actions:**",
            "file the item from templates/queue/ that puts the conflict in front of "
            "the owner and list it; a conflict is decided by the owner, never worked "
            "around",
        )


def check_task_provenance():
    """Blocking: a new task keeps the owner's words, labels its criteria, states a fit.

    New means filed on or after `TASK_PROVENANCE_SINCE`; an older record only receives
    `task-provenance-advice`. A `## Fit` section, in any task, must name a goal that
    exists or a listed clarification, and a `conflicts`/`unclear` fit must name the
    queue item that puts the conflict in front of the owner.
    """
    goals = roadmap_goals()
    for task, status, task_text in provenance_task_records():
        rel = task.relative_to(REPO)
        scope = fields(task / "task.md").get("Repository scope", "").strip()
        fit = task_fit(task_text)
        queue_paths = fit_queue_paths(task_text)
        required = fit_required(scope, status)
        if task_is_new(task.name):
            for finding in requirements_findings(task, rel, task_text):
                yield finding
            if required and fit is None:
                yield Finding(
                    "task-provenance", rel / "task.md",
                    "missing `## Fit` section",
                    "copy `## Fit` from templates/task/task.md in the claim commit: "
                    "the goal served, the current-state fact this task changes, and "
                    "how the request fits",
                )
            elif required:
                for key in ("Serves", "Today", "Fit"):
                    if not has_concrete_value(fit.get(key, "")):
                        yield Finding(
                            "task-provenance", rel / "task.md",
                            f"`## Fit` needs a concrete **{key}:** line",
                            "copy the line from templates/task/task.md and fill it",
                        )
            serves_none = fit is not None and bool(
                FIT_SERVES_NONE_RE.match(fit.get("Serves", "").strip())
            )
            if requirements_no_words(task) and (
                (required and fit is None) or serves_none
            ):
                yield Finding(
                    "task-provenance", rel / "task.md",
                    "neither owner words nor a goal: requirements.md says there are "
                    "no owner words and the fit names no goal",
                    "name the goal this task serves in `## Fit`, or quote the owner "
                    "words that asked for it",
                )
        if fit is not None:
            for finding in fit_findings(rel, fit, queue_paths, goals):
                yield finding


def check_task_provenance_advice():
    """Advisory: provenance signals an agent should see that cannot refuse a commit.

    Registered under its own id so one id maps to exactly one severity tier (see
    `check_stale_task`). A task filed before the provenance grammar is asked for
    nothing except this reminder while it is still being worked (in progress or
    blocked); one already in review, done, or still in backlog is exempt, because
    nobody is editing it and its author could not have met the rule when writing.
    """
    goals = roadmap_goals()
    for task, status, task_text in provenance_task_records():
        rel = task.relative_to(REPO)
        scope = fields(task / "task.md").get("Repository scope", "").strip()
        fit = task_fit(task_text)
        if not task_is_new(task.name) and status in PRE_ACTIVATION_ADVICE_STATUSES:
            if repo_artifact_bytes(task / "requirements.md") is None:
                yield Finding(
                    "task-provenance-advice", rel,
                    "filed before the provenance grammar and has no requirements.md",
                    "when next touched, copy templates/task/requirements.md and quote "
                    "the owner's words from the source `Filed:` names, or write the "
                    "no-owner-words line",
                )
            if fit is None and fit_required(scope, status):
                yield Finding(
                    "task-provenance-advice", rel / "task.md",
                    "filed before the provenance grammar and has no `## Fit` section",
                    "when next touched, copy `## Fit` from templates/task/task.md and "
                    "name the goal this task serves",
                )
        if fit is None:
            continue
        goal_match = FIT_SERVES_GOAL_RE.match(fit.get("Serves", "").strip())
        if not goal_match:
            continue
        goal_id, copied_title = goal_match.groups()
        criteria = task_criteria(task_text)
        if criteria and all(
            criterion_provenance(criterion)[0] == "derived" for criterion in criteria
        ):
            yield Finding(
                "task-provenance-advice", rel / "task.md",
                f"every acceptance criterion is `[derived]` while the task serves "
                f"{goal_id}",
                "trace at least one criterion to the owner's words in requirements.md, "
                "or ask the owner to confirm the derived criteria in a non-blocking "
                "clarification",
            )
        goal = goals.get(goal_id)
        if goal is None:
            continue  # `task-provenance` owns a goal that does not exist
        title, goal_fields = goal
        if copied_title.strip() != title.strip():
            yield Finding(
                "task-provenance-advice", rel / "task.md",
                f"**Serves:** copies a title that differs from the current "
                f"`## {goal_id} — {title}`",
                "re-read the goal and update the copy, or the fit if the goal moved",
            )
        if GOAL_CONFIRMED_NO_RE.match(goal_fields.get("Confirmed", "").strip()):
            yield Finding(
                "task-provenance-advice", rel / "task.md",
                f"{goal_id} is agent-proposed and not yet confirmed by the owner",
                f"re-surface the clarification named on {goal_id} in "
                f"{ROADMAP_DESIRED_STATE}, or point the fit at a confirmed goal",
            )


def check_roadmap_goals():
    """Blocking: every entry of the full picture says who asked and whether the owner agreed."""
    roadmap = REPO / ROADMAP_DESIRED_STATE
    if not candidate_has_file(roadmap):
        return
    rel = Path(ROADMAP_DESIRED_STATE)
    seen = set()
    for heading, body in level_two_sections(repo_text(roadmap)):
        matched = GOAL_HEADING_RE.match(heading)
        if not matched:
            yield Finding(
                "roadmap-goals", rel,
                f"heading `## {heading}` is not a goal entry",
                "write every level-two heading as `## G<n> — <title>`; copy "
                "templates/roadmap/goal.md",
            )
            continue
        goal_id = matched.group(1)
        if goal_id in seen:
            yield Finding(
                "roadmap-goals", rel,
                f"goal id {goal_id} appears more than once",
                "ids are never reused; give the newer entry the next unused number",
            )
        seen.add(goal_id)
        got = text_fields(body)
        if parse_date(got.get("Asked", "")) is None:
            yield Finding(
                "roadmap-goals", rel,
                f"{goal_id} lacks a dated **Asked:** line",
                "write `**Asked:** <YYYY-MM-DD>, by <the owner | agent <who>>, from "
                "<chat | answer to `<queue path>` | `<design or handover path>`>`",
            )
        confirmed = "Confirmed" in got
        retired = "Retired" in got
        if confirmed == retired:
            yield Finding(
                "roadmap-goals", rel,
                f"{goal_id} needs exactly one of **Confirmed:** and **Retired:**",
                "a live goal carries `**Confirmed:** <YYYY-MM-DD> by owner` or "
                "`no — agent-proposed, clarification `<path>``; a retired one "
                "replaces it with `**Retired:** <YYYY-MM-DD> — <decision path>`",
            )
            continue
        if retired:
            if parse_date(got.get("Retired", "")) is None:
                yield Finding(
                    "roadmap-goals", rel,
                    f"{goal_id} carries an undated **Retired:** line",
                    "write `**Retired:** <YYYY-MM-DD> — <decision path>`",
                )
            continue
        value = got.get("Confirmed", "").strip()
        proposed = GOAL_CONFIRMED_NO_RE.match(value)
        if GOAL_CONFIRMED_OWNER_RE.match(value):
            continue
        if not proposed:
            yield Finding(
                "roadmap-goals", rel,
                f"{goal_id} has an unreadable **Confirmed:** value {value!r}",
                "write `<YYYY-MM-DD> by owner` when the owner stated the goal, or "
                "`no — agent-proposed, clarification `<needs-human path>``",
            )
            continue
        path = proposed.group(1)
        if not path.startswith(CLARIFICATIONS_PREFIX) \
                or repo_artifact_bytes(REPO / path) is None:
            yield Finding(
                "roadmap-goals", rel,
                f"{goal_id} names clarification `{path}`, which is not a live item "
                f"under {CLARIFICATIONS_PREFIX}",
                "file the clarification asking the owner to confirm the goal, from "
                "templates/queue/clarification.md, and name its path",
            )


def check_roadmap_goals_advice():
    """Advisory: a goal the owner has not confirmed for long, or a fit to a retired goal.

    Registered under its own id so one id maps to exactly one severity tier (see
    `check_stale_task`).
    """
    goals = roadmap_goals()
    rel = Path(ROADMAP_DESIRED_STATE)
    for goal_id, (_title, got) in goals.items():
        proposed = GOAL_CONFIRMED_NO_RE.match(got.get("Confirmed", "").strip())
        asked = parse_date(got.get("Asked", ""))
        # The clock starts when the owner was actually asked: the clarification's
        # filing date. A goal transcribed from an older record falls back to `Asked`.
        if proposed:
            clarification = REPO / proposed.group(1)
            filed = (
                parse_date(fields(clarification).get("Filed", ""))
                if candidate_has_file(clarification) else None
            )
            asked = filed or asked
        if proposed and asked and (TODAY - asked).days > UNCONFIRMED_GOAL_DAYS:
            yield Finding(
                "roadmap-goals-advice", rel,
                f"{goal_id} has been agent-proposed for {(TODAY - asked).days} days "
                "without the owner's confirmation",
                f"re-surface `{proposed.group(1)}` to the owner, or retire the goal "
                "through a decision",
            )
    retired = {goal_id for goal_id, (_title, got) in goals.items() if "Retired" in got}
    if not retired:
        return
    for task, status, task_text in provenance_task_records():
        if status == "4_done":
            continue
        fit = task_fit(task_text)
        if fit is None:
            continue
        goal_match = FIT_SERVES_GOAL_RE.match(fit.get("Serves", "").strip())
        if goal_match and goal_match.group(1) in retired:
            yield Finding(
                "roadmap-goals-advice", task.relative_to(REPO) / "task.md",
                f"**Serves:** names {goal_match.group(1)}, which is retired",
                "point the fit at the goal that replaced it, or file a clarification "
                "asking which goal this task serves",
            )


# Check id -> the function that emits findings carrying that id. Retry clearance
# (`generated_retry_clear`), deletion certification (`queue_deletion_problem`), and
# retry garbage collection all look an id up here, so an emitted id that is missing
# is not cosmetic: its retry can never be certified as cleared and never collected,
# and a `blocking-*` one then stops every merge forever. One function may answer to
# several ids: `test_every_emitted_check_id_is_registered` holds every id the source
# emits to this map, and the runner deduplicates by function identity so a shared
# function still runs once.
CHECKS = {
    "queue-name": check_queue_name,
    "queue-location": check_queue_location,
    "queue-schema": check_queue_schema,
    "human-attention": check_human_attention,
    "record-swallow": check_record_swallow,
    "fold-shape": check_fold_shape,
    "queue-render": check_queue_render,
    "explanation-shape": check_explanation_shape,
    "queue-resolution": check_queue_resolution,
    "queue-frozen-skeleton": check_queue_frozen_skeleton,
    "queue-boundary": check_active_queue_boundaries,
    "queue-task-reciprocity": check_queue_task_reciprocity,
    "open-actions": check_open_actions,
    "stale-queue": check_stale_queue,
    "task-structure": check_task_structure,
    "task-admission": check_task_admission_history,
    "task-action-origin": check_task_action_origin,
    # One function per id: `stale-task` used to be an alias of `check_task_structure`,
    # which both double-reported every task-structure finding and gave one function
    # two severity tiers. It is its own function so its retries can be collected.
    "stale-task": check_stale_task,
    "handover-present": check_handover_present,
    "handover-queue-projection": check_handover_queue_projection,
    "memory-schema": check_memory_schema,
    "memory-expiry": check_memory_expiry,
    "memory-index": check_memory_index,
    "link-check": check_links,
    "agents-budget": check_agents_budget,
    "mode-valid": check_mode_valid,
    "roadmap-fresh": check_roadmap_fresh,
    "roadmap-goals": check_roadmap_goals,
    "roadmap-goals-advice": check_roadmap_goals_advice,
    "task-provenance": check_task_provenance,
    "task-provenance-advice": check_task_provenance_advice,
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


# A generated retry normally resolves by finding clearance, so this starts as a
# placeholder rather than a guess: the subject is often a queue path, which is never
# valid evidence. It is written anyway because clearance is not always available —
# a `queue-resolution` retry is deliberately excluded from it — and then the only
# exit is a manual resolution that names real evidence. The line makes that exit
# discoverable in the item itself, and `refresh_retry_text` never overwrites the
# concrete value an agent puts here.
RETRY_EVIDENCE_PLACEHOLDER = (
    "<the named finding clears, or name the non-queue file your repair changed>"
)


def retry_timing(f):
    """Return the timing prefix a generated retry earns from its finding.

    An advisory finding reports drift the calendar alone can create, so a clean
    tree must never start failing on a date. Filing its retry as `blocking-*`
    would smuggle exactly that failure back in through a second door: the
    blocking header carries `Blocks now: transition:merge`, and the advisory
    would stop a merge the check itself is not allowed to stop.
    """
    return "non-blocking" if f.advisory else "blocking"


def retry_text(f):
    timing = retry_timing(f)
    boundary = (
        "**Blocks now:** transition:merge\n"
        if timing == "blocking"
        else "**If unanswered:** The advisory finding stays reported and "
             "unrepaired; nothing stops.\n"
    )
    return (
        f"# {retry_title(f)}\n\n"
        f"**Status:** open\n"
        f"**Filed:** {TODAY}, by reconciler\n"
        f"**Generated by:** {RETRY_GENERATOR}\n"
        f"**Finding identity:** sha256:{finding_identity(f.check, f.subject)}\n"
        f"**Check:** {f.check}\n"
        f"**Subject:** `{f.subject}`\n"
        f"**Action:** {retry_action(f)}\n"
        f"**Resolution evidence:** {RETRY_EVIDENCE_PLACEHOLDER}\n"
        f"{boundary}\n"
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
    if "Resolution evidence" not in got:
        # Only ever added, never rewritten: whatever an agent declares here is
        # what its deletion must prove, and this writer must not retarget it.
        additions.append(
            f"**Resolution evidence:** {RETRY_EVIDENCE_PLACEHOLDER}"
        )
    if timing == "blocking" and "Blocks now" not in got:
        additions.append("**Blocks now:** transition:merge")
    if timing == "non-blocking" and "If unanswered" not in got:
        additions.append(
            "**If unanswered:** The advisory finding stays reported and "
            "unrepaired; nothing stops."
        )
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

    timing = retry_timing(finding)
    base = RETRIES / f"{timing}-{key}.md"
    existing = [base]
    existing.extend(sorted(RETRIES.glob(f"{timing}-{key}-[0-9]*.md")))
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
        candidate = RETRIES / f"{timing}-{key}{disambiguator}.md"
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        suffix += 1


def generated_retry_collectable(check):
    """Return whether garbage collection may delete this retry's check id.

    Deleting a retry is itself a queue deletion, so collection is only safe where
    `queue_deletion_problem` will certify it — that is, where
    `generated_retry_clear` can name a checker and re-run it. Deleting anything
    else replaces a stale retry with an uncertified deletion, which is a worse
    finding than the one it cleared. `queue-resolution` is excluded on purpose:
    its checker reads the very deletion being judged, so it can never certify its
    own retry, which is why `retry_text` also predeclares a manual evidence line.
    Keep this in step with `queue_deletion_problem`, and keep every emitted check
    id registered in `CHECKS` — `test_every_emitted_check_id_is_registered` and
    `test_queue_resolution_retry_is_never_garbage_collected` fail otherwise.
    """
    return check in CHECKS and check != "queue-resolution"


def committed_retry_text(finding):
    """Return the last committed generated retry for one finding, if any.

    `--file-retries` refiles a still-live finding whose retry is gone from the
    working tree. Writing a virgin item there discards the actor-owned status and
    `## Agent notes` — an agent's rejection reason — that an in-place refresh
    preserves, so recover the committed text and refresh that instead.
    """
    revision = committed_candidate_revision()
    if revision is None:
        return None
    prefix = RETRIES.relative_to(REPO).as_posix()
    listing = subprocess.run(
        [
            "git", "--no-replace-objects", "ls-tree",
            "-r", "--name-only", "-z", revision, "--", prefix,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if listing.returncode:
        return None  # no committed retries to recover from
    for name in sorted(entry for entry in listing.stdout.split("\0") if entry):
        artifact = git_artifact_bytes_at(revision, name)
        if artifact is None:
            continue
        try:
            text = artifact.decode("utf-8")
        except UnicodeDecodeError:
            continue
        candidate = REPO / name
        if delivery_class(candidate.name) is None:
            continue
        if not (
            reconciler_owned_retry(candidate, text)
            or legacy_reconciler_retry(candidate, text)
        ):
            continue  # never resurrect an untrusted lookalike
        if retry_identity_matches(text, finding):
            return text
    return None


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
        recovered = committed_retry_text(f)
        if recovered is not None:
            desired.write_text(
                refresh_retry_text(recovered, f, delivery_class(desired.name)),
                encoding="utf-8",
            )
            continue  # a deleted-then-refiled retry keeps its status and notes
        desired.write_text(retry_text(f), encoding="utf-8")
    generated = set(RETRIES.glob("*.md"))
    for item in generated:
        if item.is_symlink() or not item.is_file():
            continue
        text = item.read_text(encoding="utf-8")
        if not reconciler_owned_retry(item, text):
            continue
        check = text_fields(text).get("Check", "").strip()
        if not generated_retry_collectable(check):
            continue
        if item not in active_paths:
            item.unlink()
            removed += 1
    return len(wanted), removed


def run_checks():
    """Yield findings check by check, naming any check that cannot run.

    A generator, so callers can print each finding as it is produced: one crashing
    check must never discard the findings the earlier checks already reported.
    """
    for name, check in CHECKS.items():
        try:
            for finding in check():
                yield finding
        except GitSnapshotError:
            raise
        except Exception as error:
            raise CheckFailure(
                f"check `{name}` failed: {type(error).__name__}: {error}"
            ) from error


def reconcile(argv=None):
    global ACTIVE_TASK_ID, ACTIVE_TRANSITIONS, CHANGE_RANGE, DISPLACED_TIP
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report findings (default)")
    parser.add_argument("--file-retries", action="store_true",
                        help="write repair items for findings; gc fixed ones")
    parser.add_argument("--fix-index", action="store_true",
                        help="regenerate memory/index.md")
    parser.add_argument("--fix-open-actions", action="store_true",
                        help="regenerate message-queue/open-actions.md")
    parser.add_argument(
        "--fix-queue-fold",
        nargs="*",
        metavar="PATH",
        help="re-emit the ## For the record fold; default targets are the three "
             "human queue templates and every live human item already folded",
    )
    parser.add_argument(
        "--word-count",
        nargs="*",
        metavar="PATH",
        help="print words before the answer line against the budget; default "
             "targets are the three human queue templates and every live human "
             "item the current template governs",
    )
    parser.add_argument(
        "--fail-on-advisory",
        action="store_true",
        help="also exit 1 on advisory findings; for maintenance runs, never the gate",
    )
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
        if not (args.check or args.file_retries or args.fix_open_actions):
            return 0

    if args.fix_queue_fold is not None:
        changed, refused = fix_queue_fold(args.fix_queue_fold)
        for name in changed:
            print(f"{name} refolded")
        for name, problems in refused.items():
            print(f"{name} NOT rewritten — refolding it would not make it valid:")
            for problem in problems:
                print(f"    {problem}")
            print("    fix: move `## For the record` and its fold below the "
                  "answer line by hand, or copy the block from "
                  "`templates/queue/` — this command will not write a file it "
                  "cannot leave clean")
        print(f"queue fold: {len(changed)} file(s) rewritten"
              + (f", {len(refused)} refused" if refused else ""))
        if refused:
            return 1
        if not (args.check or args.file_retries or args.fix_open_actions):
            return 0

    if args.word_count is not None:
        rows = word_count_report(args.word_count)
        for name, words, over in rows:
            spare = HUMAN_ATTENTION_WORD_BUDGET - words
            print(
                f"{name}: {words} of {HUMAN_ATTENTION_WORD_BUDGET} words "
                + (f"— cut {over}" if over else f"— {spare} to spare")
            )
        breached = [name for name, _words, over in rows if over]
        print(f"word count: {len(rows)} file(s), {len(breached)} over budget")
        if breached:
            return 1
        if not (args.check or args.file_retries or args.fix_open_actions):
            return 0

    if args.fix_open_actions:
        (QUEUE / OPEN_ACTIONS_NAME).write_text(
            generated_open_actions(), encoding="utf-8"
        )
        print(f"{OPEN_ACTIONS_PATH} regenerated")
        if not (args.check or args.file_retries):
            return 0

    findings = []
    blocking = 0
    for f in run_checks():
        # Printed as produced, so a later crash cannot discard what is already found.
        findings.append(f)
        blocking += 0 if f.advisory else 1
        print(f"{f}  (advisory)" if f.advisory else str(f))
        print(f"    fix: {f.fix}")

    if args.file_retries:
        filed, removed = file_retries(findings)
        print(f"retries: {filed} filed/refreshed, {removed} cleared")

    advisory = len(findings) - blocking
    summary = f"reconcile: {blocking} blocking finding(s)"
    if advisory:
        summary += (
            f", {advisory} advisory"
            + (" (also failing)" if args.fail_on_advisory else " (not blocking)")
        )
    print(summary)
    return 1 if blocking or (advisory and args.fail_on_advisory) else 0


def main(argv=None):
    try:
        start_git_snapshot_cache()
        return reconcile(argv)
    except GitSnapshotError as error:
        print(f"reconcile: Git snapshot error: {error}", file=sys.stderr)
        return 2
    except CheckFailure as error:
        print(f"reconcile: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        # Exit 2, never 1: a crash must never be indistinguishable from findings.
        print(
            f"reconcile: aborted, {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 2
    finally:
        stop_git_snapshot_cache()


if __name__ == "__main__":
    sys.exit(main())
