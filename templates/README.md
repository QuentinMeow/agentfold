# templates/ — every file schema lives here

The single source of truth for file formats. To create any item, **copy its template
and fill the blanks** — never write one from memory, never restate a field list in
another doc (link here instead). To change a format, change the template and the
matching reconciler check in the same commit.

| Template | Creates a file in |
|----------|-------------------|
| `task/` (five files) | `tasks/<status>/<task-id>/` |
| `queue/decision.md` | `message-queue/needs-human/decisions/` |
| `queue/clarification.md` | `message-queue/needs-human/clarifications/` |
| `queue/review.md` | `message-queue/needs-human/reviews/` |
| `queue/request.md` | `message-queue/needs-agent/requests/` |
| `queue/retry.md` | `message-queue/needs-agent/retries/` |
| `handover.md` | `history/conversations/<timestamp>-<slug>/` |
| `pull-request.md` | the body of a pull request (no repository file — see below) |
| `memory/fact.md` | `memory/facts/` |
| `memory/adr.md` | `memory/decisions/` |
| `memory/lesson.md` | `memory/lessons/<area>/` |
| `memory/known-issue.md` | `memory/known-issues/` |
| `service/AGENTS.md` | `services/<new-service>/` |

Placeholders look like `<this>`; every `**Key:**` line shown is required unless marked
optional. The reconciler (`automation/reconcile/reconcile.py`) validates required keys
on real files and skips this folder.

**Copy the template, never the nearest existing file.** The live corpus is mid-migration
by design — a filed item is immutable, so items written under an earlier shape stay as
they are and age out as they resolve. Copying one therefore reproduces a format the
current checks reject, and the newest shapes have no live example at all until the next
item is filed. The template is the schema; a neighbouring file is only evidence of what
was true when it was written.

**Copy-and-fill is the contract.** Copying a template, replacing its `<placeholders>`,
and committing must produce a valid item with no further edits. So every required field
is a real Markdown line: nothing a check reads is ever hidden inside an HTML comment,
because `semantic_text()` blanks comments before `fields()` parses. Comments carry only
guidance and optional-field syntax, and deleting them changes nothing.

**A value is one physical line.** Every `**Key:** value` and every `*Example
consequence:*` is read by a per-line pattern, and CommonMark joins the next non-blank
line into the same rendered paragraph. So a value written as ordinary wrapped prose
renders whole and parses only as far as its first newline: the rest is visible to the
reader and invisible to every check, including the one that requires a recommendation to
name a choice actually shown. Keep the value on one line however long it gets, and put a
blank line before any paragraph that is not part of it. On queue items `record-swallow`
blocks the wrap; nowhere else does, so nowhere else is it safe.

A bare `<word>` placeholder is deleted by GitHub's HTML sanitizer, which reads it as an
unknown tag, so a copying agent reading the rendered page sees an empty slot. Where the
angle brackets have to survive on screen they are backticked, or spaced as `< like this >`
— neither shape parses as a tag, and both still read as one placeholder to fill.

## The one schema whose artifact is not a repository file

`pull-request.md` is the body of a pull request, so nothing in this repository holds a
filled copy. Two files project it: `.github/pull_request_template.md`, which GitHub uses
to pre-fill a new pull request, and `skills/explain-to-human/scenarios/pull-request.md`,
which says how to write the prose in each slot. Change this schema first; the other two
follow it. Its `What to review` section is the only part a check reads
(`automation/check_action_projection.py`), and `handbook/git-workflow.md` owns what that
check requires.

## Queue delivery timing

Every live queue filename starts with exactly one delivery prefix. What the prefixes
mean, how live timing may change, and what evidence a boundary needs are stated once in
`message-queue/AGENTS.md`; this folder does not restate them. What is template-local:
each queue template ships filled in for `non-blocking-`, the one class live timing may
always escalate away from, so a copy is valid before you have thought about timing at
all. The filename is the canonical delivery class, so a second `Blocking` field is never
added back. To file one of the other two, rename the file and write that class's timing
field — the field syntax, which is a schema and so lives here:

| Filename prefix | `needs-agent/` timing fields | `needs-human/` timing field |
|-----------------|------------------------------|-----------------------------|
| `blocking-` | `**Blocks now:** <task:<id> \| transition:<name> \| operation:<name>>`, replacing `If unanswered` | `**Blocks now:** operation:<name>` alone, added below the answer |
| `future-blocking-` | `**Blocks at:** <UTC YYYY-MM-DD \| event:<name> \| transition:<name>> [task:<id>]` and `**Until then:** <the explicit safe path while work continues>`, replacing `If unanswered` | `**Blocks at:** transition:start task:<id>` alone, added below the answer |
| `non-blocking-` | `**If unanswered:** <the explicit safe outcome>` (already shipped) | none — `If you do nothing` above the fold already states it |

The `needs-human/` column is narrower on purpose, and those two spellings are the whole
of it: one act with no undo, or the start of a task still in `0_backlog`. Every other
human question is `non-blocking-`, because nothing a human owes holds a Git edge
(`message-queue/AGENTS.md`). A human item also carries `**Answer by:**` at every prefix.

Every `**Your answer:**`/`**Your review:**` blank is the only line a human fills, so a
review ships `Reviewed revision` and `Review outcome` as slots the folding agent
completes (`handbook/human-action-guide.md`).

## The record region, and the one fold that may carry it

A queue item's **record region** is every line above the first `## ` heading, plus every
line at or below the answer line. That is where machine bookkeeping lives and the only
place any visibility check looks; prose sits strictly between the two, so a bold label
used as a pro/con inside a choice, a table cell or a blockquote is out of scope because
of *where* it is, never because of what it is called. Inside the region a field must be a
plain `**Key:** value` line at column 0 — indent it by one space, or write it as a list
item, and it still renders bold while `record-swallow` blocks the commit that hid it.

The three `needs-human/` templates carry that block inside one collapsed `<details>`, so
a reader sees one tappable line instead of a dozen. It is the only raw HTML a live human
item may contain, and its nine rules are enforced by `fold-shape`, not by memory:

1. `<details>` alone on its line, column 0, no attributes.
2. `<summary>…</summary>` on the very next line, column 0, no nested tags.
3. Exactly one blank line after `</summary>` — omitting it erases every field below.
4. Every field at column 0: no indentation, no list markers.
5. Exactly one blank line before `</details>`.
6. `</details>` alone on its line, column 0.
7. A blank line after `</details>` if anything follows — it is itself an HTML block
   start, so a field on the next line is swallowed too.
8. One fold per item, never nested.
9. The fold sits below the answer line and never contains it.

Nothing inside those three lines is a placeholder, so copy-and-fill cannot break the
shape. Every field line but the last ends in two spaces, a Markdown hard break that costs
no height while the fold is closed; `.gitattributes` stops Git stripping them, and
`automation/reconcile/reconcile.py --fix-queue-fold` re-emits the whole block from
whatever shape it is in — except where refolding could not leave the file valid, which is
rules 9 and 4-in-a-table: it then rewrites nothing, prints what is wrong, and exits 1,
because the fold and the answer line are the two things a half-repair loses. A live item
is never retro-folded: folding changes its action identity, which the queue's own
resolution gate refuses, so **the two `needs-agent/` templates carry no fold and no
three-field header on purpose** — their reader is an agent reading raw bytes, there is no
rendered-height complaint to answer, and wrapping an agent item in the human fold would
add a construct with no beneficiary and a shape to get wrong.

## Fields with no template of their own

These are single-instance markers on files that already exist, so nothing copies them
and no template can show them. Each one's meaning lives in the contract that carries it;
this table only says where to look.

| Field | Lives on | Why it exists |
|-------|----------|---------------|
| `Collaboration mode` | `AGENTS.md` | `handbook/collaboration-modes.md` |
| `Task admission schema` | `tasks/AGENTS.md` | versions task admission |
| `Queue resolution schema` | `message-queue/AGENTS.md` | versions queue resolution |
| `Human-attention format` | `message-queue/AGENTS.md` | versions the shape of a live ask |
| `Human gating schema` | `message-queue/AGENTS.md` | versions what a human item may gate |
| `Queue projection schema` | `history/AGENTS.md` | versions handover projection |
| `Queue action-entry schema` | `history/AGENTS.md` | versions projection entry syntax |
| `Queue liveness schema` | `history/AGENTS.md` | versions which actions project |
| `Last-updated` | `roadmap/current-state.md` | freshness against real state |

A schema marker is removed only by the commit that retires the rule it versions; the
reconciler rejects deleting one while the records it governs are still live.

`queue/retry.md` writes a manual retry. The reconciler writes its own retries and adds
`Generated by` and `Finding identity`, which no hand-written item carries; that template
says so where it matters.

`task/task.md` lists its live dependencies in `Queue actions`. `handover.md` projects
unresolved human queue items in delivery order; it never originates an action.
