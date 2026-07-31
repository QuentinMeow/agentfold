# Let a queue item be resolved by the work that already landed for its task

**Claimed-by:** claude
**Filed:** 2026-07-30, by claude, from chat
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`resolution_evidence_problem` in `automation/reconcile/reconcile.py` requires the file named
in an item's `Resolution evidence` to differ between the deletion commit and its immediate
parent. The window is exactly one commit wide, so work that merged earlier is byte-identical
on both sides and the item can never be deleted honestly.
`message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
has been in that state since 2026-07-26: its repair merged in `6d4e337`, before the deletion
could be attempted, and the task that would clear it is pinned by it.

Widening the window to "the evidence changed at some point" was measured to make 14 of 14
live ordinary requests deletable with no work at all, including gates whose stated
precondition is a task still unclaimed in `tasks/0_backlog/`. This task ships the narrow
widening instead: the evidence may have landed earlier only in a commit the repository
already attributes, by `task:<id>` in its own message, to a task that linked this exact queue
path and was already past pickup at that commit — and never to the task the item's own timing
boundary gates.

## Acceptance criteria

- [ ] WHEN an item's declared evidence exists in the candidate and a reachable commit
      carrying `task:<id>` for a linking, already-picked-up, non-self-gating task changed
      that path, THE SYSTEM SHALL accept the deletion.
- [ ] WHEN the evidence never changed anywhere reachable, or the only commit that changed it
      names the item's own boundary task, or that task was still in `tasks/0_backlog/` at
      that commit, or the commit carries no `task:` token, THE SYSTEM SHALL still refuse.
- [ ] THE SYSTEM SHALL report a finding set that is a subset of the pre-change checker's on
      every input, so no already-committed history can turn red.
- [ ] THE SYSTEM SHALL never raise from the new rule and never emit a finding from it: an
      unreadable revision, a non-zero `git log`, or an unparseable timing value admits
      nothing and leaves the deletion-edge verdict untouched.
- [ ] Deleting the stuck request together with its reciprocal task backlink SHALL pass
      `queue-resolution` without touching `automation/reconcile/reconcile.py` in that edge,
      and the same deletion SHALL fail on the pre-change checker.
- [ ] `reconcile.py --check`, the full test suite, and a shallow clone SHALL behave exactly
      as they did before, with the same exit codes and no new `GitSnapshotError`.

## Links

- The design that measured the choice space, landed separately on main:
  docs/designs/queue-resolution-order-independence.md
- The governing decision the rule still serves: `memory/decisions/2026-07-23-queue-resolution-is-git-evidence.md`
- The stuck item: `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
- Stack base task `2026-07-30-cache-reconciler-git-object-reads`, whose `cat-file --batch`
  reader this task reuses inside `task_ids_linking_queue_at`
