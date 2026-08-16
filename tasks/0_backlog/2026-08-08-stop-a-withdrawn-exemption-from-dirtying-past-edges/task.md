# Stop a withdrawn exemption from dirtying past commit edges

**Claimed-by:** unclaimed
**Filed:** 2026-08-08, by claude, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-withdrawn-exemption-from-dirtying-past-edges.md`

## Goal

`task-action-origin` judges each commit edge on that commit's own bytes. When a parser
exemption is later withdrawn, every historical edge that relied on it becomes dirty, even
though the branch head is clean and every commit was green when it was made. The
review-receipt task hit this: two of its intermediate commits carry panel transcript lines
that a since-removed grammar exempted, so a range check over the whole branch reports two
findings no head-side edit can repair.

Decide and implement what a merge-time check should judge: the merge candidate's resulting
state, the edges as they were green when authored, or something else. A repair must not
require rewriting published history, because that strands the exact revisions review
receipts are bound to.

## Acceptance criteria

- [ ] A branch whose head introduces no unqueued human action passes the merge-transition
      check even when an intermediate commit relied on an exemption later withdrawn.
- [ ] A branch whose head does introduce one still fails.
- [ ] The chosen rule is recorded as a decision, with the alternative it rejected.
- [ ] Real output for both cases is recorded in `verification.md`.

## Links

- Known issue: the withdrawn-panel-grammar record that lands with pull request 82
- Advisory merge gate: `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`
