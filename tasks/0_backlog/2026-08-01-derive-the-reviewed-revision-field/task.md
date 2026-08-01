# Stop asking anyone to maintain Reviewed revision, and derive it instead

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `handbook/human-action-guide.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-derive-the-reviewed-revision-field.md`

## Goal

`Reviewed revision` carries no information of its own. Whenever a concrete response
exists, `check_queue_schema` forces it equal to `Review revision`, and the staleness
guarantee it is supposed to provide actually rests on two other things: `Review revision`
being frozen at the first response, and the target's bytes being re-hashed at the
deletion edge. It was also the only field a human was ever told to hand-copy, and the
redesign has already removed that instruction from
`message-queue/needs-human/reviews/README.md` and from every live item.

This task removes the field and derives the same answer, or records why it must stay.

The reasoning above is the deciding agent's summary of a design audit that reached this
conclusion independently; that design document is not in this repository, so nothing here
quotes it. The audit's own limit was stated plainly and applies to whoever picks this up:
it never simulated a full lifecycle — publish, answer, claim, delete-with-receipt — in the
changed shape.

It was deliberately not bundled with the presentation redesign. Deleting the field opens
`human_response_fields`, `claim_identity`, `immutable_action_text`, and three branches of
the review-binding lifecycle — the write-once response boundary. The lesson from the
attempt that died before it was that a presentation change must not acquire the
governance machinery of a security invariant; reaching the other way is the same mistake
mirrored. Its human cost is now zero, so there is no hurry: the field sits below the
answer line and nothing asks anyone to touch it.

## Acceptance criteria

- [ ] `design.md` states, for each of `human_response_fields`, `claim_identity`,
      `immutable_action_text`, and every review-binding branch that reads
      `Reviewed revision`, what replaces it or why it is unaffected
- [ ] A multi-commit fixture exercises a full review lifecycle — publish, answer, claim,
      delete with receipt — in the changed shape, and fails against the pre-change checker
- [ ] A stale response cannot be folded after its target's bytes change, demonstrated by a
      test rather than argued in prose
- [ ] The already-answered legacy record keeps validating unchanged, because a record is
      never rewritten to match a later schema
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path
- [ ] The change is reviewed on its own, because it moves the write-once response boundary

## Links

- Where the field is forced equal to its binding: `automation/reconcile/reconcile.py`
- The shape it now sits below: `templates/queue/review.md`
- What a human is asked to do instead: `handbook/human-action-guide.md`
- The redesign that deferred it: task `2026-07-31-redesign-human-action-files`
