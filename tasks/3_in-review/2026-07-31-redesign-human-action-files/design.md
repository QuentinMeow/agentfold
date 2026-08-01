# Design notes — Redesign every file that asks a human for attention

**Status:** decided

## Problem

The owner rejected the shape of every file that asks him for something: broken English,
past and current and proposed behavior indistinguishable, ambiguous choices, and
parser-style labels, excessive metadata, and duplicate links standing in front of the
decision. The repair has to change presentation without touching two things that must not
move — the immutable identity of a live action, and the exact bytes of a committed human
response.

Three constraints shaped every choice below. Reformatting a live item is by construction
an identity change, because `immutable_action_text` hashes every visible line that is not
lifecycle state. The projected fields are rendered into every handover and every
end-of-session reply, so renaming them touches immutable records. And the previous
attempt at this repair died by reasoning about rendered prose: it rewrote
`automation/markdown_semantics.py` by 1,849 lines and was blocked three times by its own
adversarial panel.

## Options considered

### Option A — Enforce the format on rendered output

Check what a reader actually sees: parse the Markdown, resolve the HTML, and judge the
resulting document. This is what the abandoned branch did.

*Example consequence:* the checker must decide what a browser does with an unclosed tag,
and every disagreement with a real renderer is a false verdict on a real file.

### Option B — Enforce structure only, and never rendered prose

Check which fields exist, where they sit relative to the answer line, and whether a named
choice was actually shown. Quality of the title, honesty of `Today`, and truthfulness of
the counter-case stay review matters.

*Example consequence:* an agent can still write a confidently-hedged, useless
`Confidence` line, and only a reviewer will catch it — but no check ever has to model a
renderer, and `automation/markdown_semantics.py` is not touched at all.

### Option C — Leave every live item alone and let the old ones age out

Two formats already coexist legally; new items land in the new shape and the eight
existing files resolve over time.

*Example consequence:* the seven files the owner opens next are exactly the ones he
already rejected.

## Chosen

**Option B for enforcement, and Option C for the existing files.**

Structure-only enforcement is the whole reason the mechanism is a few hundred lines in
`reconcile.py` rather than +3,238 plus a parser rewrite. Each of the owner's complaints
maps to a structural rule: exactly three fields above the first heading, no machine field
above the answer line, `Today` / `What this would change` / `What this does not decide`
present, two or more `### ` choices each with an example consequence, a recommendation
that names a choice actually shown, no raw HTML, no `Look-at`, and 700 words before the
answer. Judgment questions — is the title answerable, is `Today` honest — are stated in
`handbook/human-action-guide.md` as review matters, not machine matters.

Option C was chosen for the live files against this task's own first judgment, and the
reason is recorded next because it is the most important thing in this file.

### Why the migration and its carve-out were cut

This task first implemented Option C's opposite: a one-shot carve-out in
`queue_mutation_problem` admitting exactly the edge that activates
`**Human-attention format:** v1`, so all seven unanswered live items could be rewritten in
one commit. It was fenced hard — same path, `needs-human/` only, refused outright on any
item carrying a human answer, seventeen fields frozen byte-exactly, two more frozen by
resolved path set, both projected sentences append-only, and no parent of the candidate
allowed to already carry the marker. Sixteen adversarial mutations were refused.

An independent adversarial review broke it anyway, and the way it broke is the point.
With every one of those fences satisfied — all seventeen frozen fields byte-identical,
both path-frozen fields identical, both projected sentences whitespace-normalised
prefixes of their committed values, and `reconcile.py --check` reporting `0 finding(s)` —
a migration changed the H1 question, inverted the `What this does not decide` sentence and
so erased a scope limit the owner had actually set, deleted one of the offered choices,
flipped the recommendation from "Request changes" to "Approve", and raised the stated
confidence.

The fences guard field labels. The ask a human reads is the title, the context block, the
choices, and the recommendation, and every one of those is unfrozen by construction —
they are exactly the prose the reformat exists to rewrite. No list of frozen fields can
close that, because the fix and the exploit are the same operation. The claim in the
reviewed spec that "it is impossible to use this to silently alter a real human ask" was
wrong, and it was wrong for a structural reason, not a missing field.

So the carve-out is gone, `queue_mutation_problem` has no presentation carve-out at all,
and the seven rewritten files are restored to their baseline bytes. Cutting it also
removes a second exposure the reviewed spec had noted and accepted: a branch cut before
activation and merged after presents a parent without the marker, which is a live
allowance sitting in the repository waiting for a merge topology to arm it. With no
carve-out there is nothing to arm.

The eight existing items therefore keep the schema they were written under and age out as
they resolve. Every new ask is written from `templates/queue/` in the new format. Two
formats coexisting is already legal — there is no per-item format version — and the cost
is stated plainly: the files the owner opens next are the ones he already rejected. The
countersigned migration that fixes that is filed as task
`2026-08-01-countersign-the-live-human-item-migration`, and the only safe shape for it is
an answer committed before the rewrite, not a fence around it.

Because no live item is migrated, every new presentation check is gated twice: on the
repository marker, and on the projection spelling the item itself uses. An item written
before the format is skipped, so activating the format neither rewrites an existing ask
nor starts rejecting one.

### Three sub-decisions worth recording

**The rename is not cosmetic.** `Why-you-might-care` / `If-you-do-nothing` are rendered
into every handover and every end-of-session reply. Keeping them would mean the single
most visible symptom of the format survives the repair. They are renamed with a permanent
legacy alias, gated by handover entry schema `v3`, so no record created under v1 or v2 is
retroactively invalidated — `history/AGENTS.md` already required exactly that. The alias
is permanent rather than transitional precisely because no live item is being migrated:
the eight existing files project correctly under v3 using their own spelling.

**No `<details>` block, and raw HTML is banned outright.** A `<summary>` with no blank
line after it opens a CommonMark type-6 HTML block that swallows every field below it:
`text_fields` returns `{}`, `Status` and the review binding cease to exist, and the file
still renders identically. That is the worst class of bug this repository can have, and a
cosmetic reflow is enough to cause it. The check forbids the construct rather than
requiring the blank line. No live item contains raw HTML today, so the ban costs nothing.

**`Reviewed revision` is kept, and its deletion is deferred to its own task.** It is
forced equal to `Review revision` whenever a response exists, so it carries no
independent information — but deleting it opens `human_response_fields`,
`claim_identity`, `immutable_action_text`, and three branches of the review-binding
lifecycle inside a presentation change. Deferred to task
`2026-08-01-derive-the-reviewed-revision-field`, with its own review.

### What was left for other tasks rather than fixed here

- `has_concrete_value` reads the literal words the placeholder vocabulary lists as
  unanswered, so a review answered "none" — the natural reply to a request to name a
  missing obligation — reads as no answer at all, and everything protecting a committed
  response keys on that predicate. Task
  `2026-08-01-stop-reading-none-as-an-unanswered-field`.
- Any future mechanism that admits rewriting live items admits only the marker-activation
  edge, so reverting such a commit is itself a refused rewrite. Task
  `2026-08-01-record-that-a-format-migration-is-one-way`.
- `message-queue/needs-human/reviews/README.md` still tells a human to copy
  `Review revision` into `Reviewed revision`, matching the eight live files it describes.
  The templates no longer ask for it. Rewriting the leaf README belongs with the files it
  describes, so it moved into the countersigned-migration task rather than landing here
  and describing files that do not exist yet.

## Core fit

**Agent substitution:** pass — every rule is a property of committed Markdown checked by
`automation/reconcile/reconcile.py`. No behavior depends on which agent runtime wrote the
file, and nothing reads an agent-specific path, tool, or protocol.
**Provider substitution:** not-applicable — nothing here reads or writes a hosting
provider. The handover suffix is rendered from repository files only, and the format
marker is read from `message-queue/AGENTS.md` through Git.
**Repository substitution:** pass — any adopted repository that asks a human for a
decision needs those asks to be answerable, and needs a committed answer to be immutable.
The format activates from a repository-local `**Human-attention format:** v1` marker, so
a fork that does not want it simply omits the marker and every new check no-ops.
**User-global writes:** none
**Why AgentFold core:** the message queue is core, and this is the schema of its human
half plus the reconciler rules that enforce it. It is not local configuration (the marker
and every rule are repository state), not a product service, not a private overlay, and
not separable into a plugin: `check_queue_schema` and `queue_mutation_problem` are the
same functions that already own live-action identity.
**Thin adapter:** none
