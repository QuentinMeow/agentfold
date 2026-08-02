# A live queue item's immutable fields cannot be corrected, even when they are wrong

**Status:** open
**Severity:** low
**Description:** Cross-reference and provenance fields are part of a live item's frozen action identity, so a dangling link, a pointer to a renamed sibling, and a question whose subject became moot all have no legal repair while the item is live
**Review-by:** 2026-10-30

## Symptom

Three concrete instances on `main` today, all the same shape:

1. `message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md`
   declares `**Depends on:** …/future-blocking-revise-assurance-profile-scope-and-egress.md`,
   a file that has never existed at any revision. Correcting it would change
   `queue_action_identity`, so `queue_mutation_problem` refuses the edit.
2. `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
   declares `**Follow-up review:** …/future-blocking-rereview-human-action-files.md`,
   which was renamed to `non-blocking-rereview-human-action-files.md` when the
   human-gating migration removed its merge boundary. The pointer now names a path that
   no longer exists, and `Follow-up review` is likewise identity-frozen.
3. There is no legal way to withdraw an unanswered `needs-human/` item whose subject
   became moot. Deletion needs a concrete human response, and an agent may never write
   one.

## Impact

Low, and deliberately so. `check_links` already exempts every queue-path citation
because "a queue action is resolved by deleting its file… so any citation of one names
history, not a live link", and it exempts `Supersedes`/`Depends on`/`Follow-up review`
by name for the same reason. So none of these fails a check; they mislead a reader.

Instance 3 is the one with teeth, and it is bounded: since a live human item no longer
holds any Git edge, a moot question costs one line in a reply and one entry in a
handover until someone answers it — it stops nothing.

## Workaround

For 1 and 2: read the field as historical lineage, which is how the reconciler already
treats it. For 3: re-surface the item with a new `Answer by:` and a `Re-asked:` line
saying the subject is moot and a one-word answer will close it.

## Suggested fix

Two candidates, and the choice between them is the actual open question.

The narrow one: add a `Superseded-by`-style *append-only* correction field
(`**Corrected link:**`) that is lifecycle-mutable, so a dangling cross-reference can be
repaired forward without rewriting the original. Cheap, and it does not weaken identity,
because the original text still stands beside the correction.

The broader one: give the queue a `withdrawn` disposition that an agent may set on an
*unanswered* item, deleting it against changed `Resolution evidence` that records why the
question stopped mattering. This is the only fix for instance 3. It must not become a
back door for discarding inconvenient questions: gate it on the item being unanswered,
require the evidence to name the change that mooted it, and keep the deletion visible in
Git history like every other resolution.
