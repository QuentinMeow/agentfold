# Design notes — let a human answer in one edit

**Status:** decided

## Problem

Three defects, one root cause: the schema a human or agent is told to satisfy is not the
schema the code actually enforces.

**Defect 1.** Root `AGENTS.md` says the response is committed while status is `waiting`.
A review answered exactly that way is rejected, because `check_queue_schema` demanded
`Reviewed revision` and `Review outcome` in the same commit as the response. Nothing
visible said so: the instruction lived in an HTML comment in `templates/queue/review.md`,
and filed items carry no comments because the filing agent strips them. What the owner
saw was two unexplained blanks. A backticked path in the answer added a third rejection
from `link-check`. Every repair was then contract-forbidden — the first response is
immutable and human text is not agent-editable — so the item was permanently wedged.

**Defect 2.** `fields()` runs `semantic_text()` first, which blanks HTML comments. Every
timing field lived only inside a comment, so copying any template and filling it in
produced a guaranteed failure. Measured, not assumed: the pre-fix templates failed 2, 2,
5, 2, and 2 findings respectively, and `**Status:** <waiting | folding>` was copy-invalid
too — an angle-bracket placeholder is not one of the allowed statuses.

**Defect 3.** Seven schema-marker fields and two reconciler-only retry fields are
required by code with no template showing them, against `templates/README.md`'s claim to
be the single source of truth for every file schema.

## Options considered

### Option A — Teach the human the two extra fields
Make the blanks self-describing in the filed item and document them in the handbook.
*Consequence:* the interaction still takes three edits, one of which is copying a 64-hex
digest by hand from a phone. The `link-check` trap remains, and so does the wedge: get
any of it wrong and there is no legal repair.

### Option B — Delete the two fields
Drop the revision binding and the terminal outcome entirely.
*Consequence:* a review approval stops naming what it approved. Deletion and boundary
crossing lose their only evidence that the answer judged the exact bytes on offer. This
throws away the thing the fields genuinely buy.

### Option C — Move who supplies them and when (chosen)
The human writes one sentence. The agent supplies `Reviewed revision` and
`Review outcome` in the `waiting` → `folding` claim it already has to commit.
*Consequence:* one edit answers any item; both invariants still hold at the edges that
depend on them.

## Chosen

Option C. The decisive observation is that the two invariants were never enforced by
`check_queue_schema` in the first place — `queue_deletion_problem` already refuses to
resolve a review that is unbound or lacks a terminal outcome, and boundary crossing
already requires `approved`. `check_queue_schema` was only enforcing them *earlier* than
necessary, at the one moment the human is holding the pen. Moving the fields costs
nothing an edge does not re-check.

### What is enforced mechanically

`review_terminal_binding_write` admits the agent's write only when all of these hold:

1. **A human response was already committed in the parent.** An agent cannot author a
   response and classify it in the same commit; that path returns "the waiting → folding
   claim changed more than status".
2. **The write happens only on the `waiting` → `folding` claim edge.** Earlier or later
   returns "the agent review binding may only be recorded on the waiting → folding claim
   edge". `claimed_lifecycle_problem` blanks exactly these two lines for its status-only
   comparison, and only when the edge earned it, so the claim receipt still proves that
   nothing else moved.
3. **Every other response field stays byte-identical** — including the response sentence
   and the `Review target`/`Review revision` the human answered against. An approval can
   never be re-pointed at bytes the human did not see.
4. **The binding was previously unset and repeats the frozen `Review revision`.**
5. **Write-once.** Any later change returns "human response or its immutable review
   binding changed after the first concrete response".
6. **`folding` requires the full binding**, so an agent cannot claim a review and leave
   it unclassified — the pre-commit hook rejects that commit rather than stranding an
   item that `queue_deletion_problem` would later refuse to resolve.

### What is not enforced, stated plainly

Nothing verifies that `approved` is a truthful reading of "Looks good to me, ship it."
The reconciler does not understand English, and no rule here pretends to. The human's
text remains authoritative in the sense that it is immutable, permanent, and sits beside
the outcome in the same file and the same history — but the mapping from sentence to
outcome is an agent attestation, not a proof.

This is recorded, not hidden, in
`memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`. It is also
not a regression: before this change an agent could already write both the response and
the approval in a single commit. The change strictly narrows that — forgery now requires
two separate, individually attributable commits, and the second cannot rebind or reword
the first.

### The aggressive alternative, for the owner

The conservative version shipped. The aggressive version, deliberately not shipped:

> Require the human's own committed text to contain a token from a small closed
> vocabulary before an agent may record `approved` specifically. `changes-requested`,
> `rejected`, and `abandoned` all preserve or decline the boundary and stay free-form;
> only the outcome that lets work cross a boundary would need the human to have typed a
> recognized word.

It would make the most dangerous outcome mechanically derivable from human text rather
than attested. It is not shipped because it puts a second required word back into the
one interaction this task exists to make single-edit, and because the closed vocabulary
is a new failure mode of its own — "yes, ship it" is a perfectly clear approval that no
short token list will reliably contain. Shipping it should follow evidence that a
misclassification actually happened, not a hypothesis that one could.

### Defect 2: why default to non-blocking

Every template now ships filled in for `non-blocking-`, with all three timing blocks
shown once in `templates/README.md` instead of five times in comments. `non-blocking` is
the right default because live timing may only escalate — `non-blocking` →
`future-blocking` → `blocking` — so starting at the weakest class is the only choice
that is always legal to correct later. Starting at `blocking` and discovering the item
does not block requires an authorized replacement.

The rule this establishes: **no field a check reads may live inside an HTML comment.**
Comments carry guidance and optional-field syntax only, and deleting them changes
nothing. `test_every_queue_template_survives_copy_and_fill` is the standing guarantee,
and `test_a_queue_template_hiding_a_required_field_in_a_comment_fails` proves it has
teeth. Filling the templates also surfaced a second fragility: a naive filler that
substitutes every `<...>` span corrupts any comment containing `->`, so the guidance no
longer uses that arrow.

### Defect 3: documented, not restated

`templates/README.md` gains one table naming each marker field and the file that carries
it, plus a pointer for the two reconciler-only retry fields. It says where to look, never
what the field means — that stays in the contract that owns it, per the single-source
guardrail.

## Core fit

**Agent substitution:** pass — every rule is enforced by the reconciler over committed
Git state, so a different agent runtime writing the same files gets the same verdict.
**Provider substitution:** not-applicable — nothing here touches a provider surface.
**Repository substitution:** pass — the human-answer interaction and the queue templates
are the adopted repository's own coordination surface; an adopter with no reachable human
is exactly who a fail-closed answer path hurts most.
**User-global writes:** none
**Why AgentFold core:** this is the repository's central human interface and the schema
source of truth for it; both live in core by definition, and neither is local config nor
a product service.
**Thin adapter:** none
