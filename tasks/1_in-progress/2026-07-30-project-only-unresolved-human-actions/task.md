# Project only the human actions that still await the human

**Claimed-by:** claude
**Filed:** 2026-07-30, by claude, from chat — the owner reported the repeated ask
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-project-unresolved-actions-in-provider-bodies.md`

## Goal

Every handover and every chat reply must project the `message-queue/needs-human/` queue,
and the reconciler decides which items belong in that projection. It decided by path
alone: `live_human_queue_paths()` returned every readable item under `needs-human/`
whatever state it was in. An item the owner had already reviewed and approved was
therefore byte-identical, in their inbox, to one nobody had touched.
`message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`
has carried `Status: folding`, `Review outcome: approved` and a filled `**Your review:**`
since 2026-07-24, and it has been re-asked in every handover since. Make the projection
state-aware so the list the owner reads contains only what still needs them, without
retroactively invalidating a single already-committed handover.

## Acceptance criteria

- [ ] WHEN a `needs-human` item is `folding`, `awaiting-artifact`, or `waiting` with a
      concrete committed `**Your answer:**`/`**Your review:**`, THE RECONCILER SHALL
      treat it as resolved and reject a new handover that projects it.
- [ ] WHEN a `needs-human` item is `waiting` with no concrete response, or its state is
      absent, malformed, or unreadable, THE RECONCILER SHALL still require it to be
      projected.
- [ ] WHEN every live `needs-human` item is resolved, THE RECONCILER SHALL accept a
      handover whose `Needs your attention` section is exactly `None.`
- [ ] The rule is gated by a new `**Queue action-entry schema:** v3` activation, so no
      handover created before that activation changes verdict.
- [ ] Re-running the projection check at the creation commit of every handover in
      `history/` produces the identical finding set before and after the change.
- [ ] `templates/handover.md` and the root `AGENTS.md` chat-reply sentence name the same
      set, defined in exactly one place.
- [ ] The full test suite passes and `automation/reconcile/reconcile.py --check` reports
      0 findings.

## Links

- Rule and schema markers: `history/AGENTS.md`
- Queue state machine: `message-queue/AGENTS.md`, `templates/queue/`
