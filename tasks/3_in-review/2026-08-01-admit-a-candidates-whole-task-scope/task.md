# Let a candidate carry more than one task, and stop a range failing the boundary it files

**Claimed-by:** claude (session 2026-08-01, branch task/2026-08-01-admit-a-candidates-whole-task-scope)
**Filed:** 2026-08-01, by claude, from six pull requests blocked by two gates that require opposite things
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Two gates in this repository require opposite things of the same commit.

`automation/reconcile/reconcile.py`'s `check_queue_task_reciprocity` **requires** that a
live queue item declaring `task:<id>` be listed in that task's `Queue actions`. Filing an
item bound to another task therefore forces an edit to that other task's `task.md`.

`automation/check_action_projection.py`'s `inferred_changed_task_id` then **refuses** the
resulting candidate with a hard input error — exit 2, not a finding — because its diff
touches more than one `tasks/<status>/<task-id>/` folder:

```
action-projection: input error: candidate maps to multiple task scopes: <id>, <id>
```

The same shape appears without any reciprocity link: a task that files a follow-up task, a
task that checks off an acceptance criterion another task shipped, and a parent claimed
together with its child all produce a plural scope. Six open pull requests are stopped by
it.

A second failure has the same root. `check_active_queue_boundaries` fires
`transition:merge` against every task whose records the candidate touched. A candidate that
*files* a `future-blocking … transition:merge task:<id>` action must, by the reciprocity
rule above, also touch that task's record — so the action is judged to have reached a
boundary in the very range that created it. No such action can be introduced through any
merged candidate at all.

## Acceptance criteria

- [ ] WHEN a candidate's diff maps to several tasks, THE SYSTEM SHALL bind every one of
      them and require the declared action section to project the union of their live
      scoped queue actions, instead of refusing the candidate with exit 2.
- [ ] WHEN the branch is `task/<id>`, THE SYSTEM SHALL still refuse a candidate that
      carries no evidence for `<id>`, naming the scope it did find.
- [ ] WHEN the change range introduces a queue action, THE SYSTEM SHALL not report that
      action as having reached a boundary inside that same range; an action already live
      at the range base is still reported exactly as today.
- [ ] A renamed action — the permitted `non-blocking` → `future-blocking` → `blocking`
      escalation — SHALL NOT count as introduced, so escalating inside the crossing range
      cannot dodge the boundary.
- [ ] Each rule change has a test that fails before it and passes after, with the real
      output recorded in `verification.md`.
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes 11/11.

## Links

- Blocked pull requests: #36, #41, #42, #45, #46, #48
- Boundary trap already worked around by hand twice:
  `docs/designs/queue-resolution-order-independence.md`
- Adapter contract that states the current one-task rule: `automation/AGENTS.md`
