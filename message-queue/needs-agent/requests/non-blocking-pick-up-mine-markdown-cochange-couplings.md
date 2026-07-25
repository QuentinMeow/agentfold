# Pick up the markdown co-change mining task

**Status:** open
**Filed:** 2026-07-25, by claude, from task `2026-07-25-mine-markdown-cochange-couplings`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-25-mine-markdown-cochange-couplings/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog and nothing stops, because the mined report is advisory and is wired into no gate.

## What you need to know

This is Stage 0 and Stage 1 of the approved markdown edge graph, and nothing beyond them.
Three pieces land: heading-anchor validation inside the existing `check_links` in
`automation/reconcile/reconcile.py`, which today skips any candidate containing `#` and so
checks neither the path nor the anchor of a link like a missing file plus a missing heading;
a standalone stdlib co-change mining CLI under `automation/` whose report verb always exits
0; and an append-only accepted/rejected ledger that makes each mined verdict durable and
turns the rejection rate into the effective-false-positive rate.

The stage ends with a written experiment over two hot files that can legitimately end the
whole project: if the mined list already says what a hand-authored edge would have said, the
typed schema is unjustified and the advisory is the entire feature. Everything past that —
the `## Edges` schema, the committed artifact, the `impact` query, per-folder freshness,
repair-item filing, the pre-commit advisory, further directories, and the viewer — is
deferred and filed separately.

Scope is core, so the work rides the branch named
task/2026-07-25-mine-markdown-cochange-couplings, against the completed substitution
receipt that already sits in the task's `design.md`.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
