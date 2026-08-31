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
because `semantic_text()` blanks comments before `fields()` parses. Human templates
contain no instructional HTML comments: their authoring instructions live below, so the
copy also obeys the live-human HTML restriction. Agent-template comments carry only
guidance and optional-field syntax; leaving them in changes no parsed field.

**A value is one physical line.** Every `**Key:** value` and every `*Example
consequence:*` is read by a per-line pattern, and CommonMark joins the next non-blank
line into the same rendered paragraph. So a value written as ordinary wrapped prose
renders whole and parses only as far as its first newline: the rest is visible to the
reader and invisible to every check, including the one that requires a recommendation to
name a choice actually shown. Keep the value on one line however long it gets, and put a
blank line before any paragraph that is not part of it. On queue items `record-swallow`
blocks the wrap; nowhere else does, so nowhere else is it safe.

**A threshold you cannot see is a wish.** The word budget on a live human item is the
one rule of that format an author cannot check by reading their own file, and a held-out
authoring run breached it seven times out of ten because nothing ever showed them the
number. `automation/reconcile/reconcile.py --word-count <file>` prints the count against
the budget for any file, committed or not; with no path it measures the three human
templates and every live item the format governs. The budget's single source of truth is
`HUMAN_ATTENTION_WORD_BUDGET`, which the finding, that command, and a test that would
fail if this guide stated a different number all read.

A bare `<word>` placeholder is deleted by GitHub's HTML sanitizer, which reads it as an
unknown tag, so a copying agent reading the rendered page sees an empty slot. Where the
angle brackets have to survive on screen they are backticked, or spaced as `< like this >`
— neither shape parses as a tag, and both still read as one placeholder to fill.

## Before filing a human question

Read this guide before copying a human queue template. Its filename uses one delivery
prefix from `message-queue/AGENTS.md` and a slug from `handbook/naming-conventions.md`.
The template carries the fields; `handbook/human-action-guide.md` owns their lifecycle.
Check the filled item against this authoring checklist:

1. The title is a question the owner can answer without knowing this repository.
2. Exactly three fields appear above the first heading: Action, Why this matters, and
   If you do nothing.
3. Today, What this would change, and What this does not decide are true and specific.
4. Two or more choices each state a cost and a concrete *Example consequence:*.
5. The sentence opening Your choices says what the choices differ on.
6. Recommendation repeats one displayed `### ` choice label exactly, with its strongest
   counter-case beside it. For a clarification, My working assumption repeats a displayed
   reading: state what you will assume and do, rather than recommend the owner's intent.
7. No machine field, hash, or token appears above the answer line.
8. Include the decisive source passage and attribution as described under Source excerpts
   in human items; For the record keeps the machine copies.
9. Under 800 words before the answer. Run
   `python3 automation/reconcile/reconcile.py --word-count <this file>` to see the count
   and remaining budget. Keep every meaningful choice, its consequence, and decisive source quotations; shorten
   background instead.

Keep every field value and every *Example consequence:* on one physical line as described
above. Confidence is exactly `high`, `medium`, or `low`, then a space, an em dash (U+2014),
another space, and what you checked and did not. A hyphen or a bare adjective is refused.
There is no `Look-at` field: put the reader's source link in the prose and its machine
copy in Full context.

Decision and clarification templates start with `waiting`; the folding agent changes that
to `folding` on its separate claim edge. Use only the timing fields in the table below.
Add `External assignment` or `External source` only for a provider binding. A concrete
human response is immutable. To answer a counter-question, fold it into Resolution
evidence and create a successor with the same delivery timing and `Supersedes` naming
the original item; never rewrite the response.

## Review bindings and optional fields

The review template ships `waiting` with a local file target and the SHA-256 of that
file's bytes. Before the artifact exists, use `awaiting-artifact` with both `Review target`
and `Review revision` literally `pending`. Publish a binding in a later commit that moves
the status to `waiting`; the folding agent claims it with a separate `folding` edge.

A Git range uses `Review target: git:<base>...<head>` with a byte-identical
`Review revision`, both unbackticked and naming full 40- or 64-hex object IDs. A branch
name or abbreviated ID can move. An HTTPS artifact uses one URL and a `sha256:` revision.
The actual fields retain the bold-key syntax shown in the template. Full context explains
the judgment and never replaces the target.

`Reviewed revision` and `Review outcome` belong to the folding agent. Once the human's
response is committed, it copies `Review revision` into `Reviewed revision` and replaces
`pending` with `approved`, `changes-requested`, `rejected`, `abandoned`, or `unanswerable`
exactly once. The last means the human lacked enough context to decide; it settles nothing
about the subject and requires a fresh question.
A changes-requested resolution also adds `Successor action` and `Follow-up review` to the
record. Provider bindings use `External assignment` or `External source` only when needed.
Timing uses the table below. The retraction and republication procedure when an artifact
changes is owned by `handbook/human-action-guide.md`.

For an unanswerable resolution, add `**Successor action:** <new needs-human/reviews path>`
to the resolving record. Create that distinct new review in the same resolution commit,
with `**Supersedes:** <old review path>` pointing back. Preserve Full context, the exact
Review target and Review revision, the delivery prefix, and every dependency-timing field
used by the original item’s schema, including any task boundary.

The successor is `waiting`, with a blank Your review, blank Reviewed revision, and
`pending` Review outcome. An existing, answered, or `awaiting-artifact` item cannot serve
as this successor. Supply the missing context without changing the judgment or artifact;
a later artifact change follows retraction and publication. The original human response
stays immutable, and its predeclared Resolution evidence changes on the resolving commit.

## The one schema whose artifact is not a repository file

`pull-request.md` is the body of a pull request, so nothing in this repository holds a
filled copy. Two files project it: `.github/pull_request_template.md`, which GitHub uses
to pre-fill a new pull request, and `skills/explain-to-human/scenarios/pull-request.md`,
which says how to write the prose in each slot. Change this schema first; the other two
follow it. Its `What to review` section is the only part a check reads
(`automation/check_action_projection.py`), and `handbook/git-workflow.md` owns what that
check requires.

## Source excerpts in human items

The three human templates show the quotation and attribution together. Copy the decisive
passage, then name its location with `> — [what this passage says](destination#anchor)`.
CommonMark angle destinations, such as
`> — [selected lines](<../../../docs/source notes.txt#L2-L4>)`, are also accepted. Resolve
local paths from the queue item's folder or the repository root. Select a Markdown heading
or bounded text/code lines with `#Lx` or `#Lx-Ly`: line numbers start at one, run forwards,
and cannot exceed the file. A bare file link does not select a passage.

Preserve the source's wording, identifier spelling, and case, including in short quotes.
Wrapping and Markdown emphasis may change presentation. Mark omissions with `…`, `...`,
`[…]`, or `[...]`, keeping the remaining passages in source order. Quote both sides of a
comparison. Optional annotated background belongs below the answer inside the record fold
and needs no quotation; the reader must be able to decide without opening it.

When no source wording decides the answer, replace the whole source block with exactly
`> No source document — everything you need is above.` Keep the required context fields.
A review of a local file still quotes its target; the no-source sentence cannot replace
that evidence.

Source findings are advisory. Local comparisons use the captured candidate's regular-file
bytes; missing, outside-repository, nonregular, binary, and invalidly selected sources do
not count as verified evidence. External content is not fetched or machine-verified.
Matching text establishes neither its relevance nor its truth; the author still checks
whether the selected passage supports the judgment.

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
