# Let a queue item resolve when its resolution evidence landed in an earlier commit

**Claimed-by:** unclaimed
**Filed:** 2026-07-26, by claude, from the coordination session that claimed and then could not resolve the handover code-span repair — `handbook/git-workflow.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-resolve-queue-items-whose-evidence-already-merged.md`

## Goal

A `needs-agent` request whose work merged before its claim edge was committed can never be
deleted by any honest commit. The deletion check requires the item's predeclared resolution
evidence to change *in the deletion commit itself*, and evidence that already merged cannot
change again. One item is in that state on `main` today, and it keeps declaring a blocker
that its own repair has already cleared.

### The defect, measured

`resolution_evidence_problem` in `automation/reconcile/reconcile.py` (defined at line 2614,
comparison at lines 2618 to 2626) reads the evidence file twice: `before` at
`prior_revision`, which for a staged deletion is `HEAD`, and `after` at the deletion
revision or from the worktree. Identical bytes yield
`resolution evidence was not created or changed in the deletion commit`. The window is one
commit wide, so evidence that changed at any earlier point in the item's lineage — including
the commit that actually performed the requested work — counts for nothing.

`queue_deletion_problem` (lines 3478 to 3594) routes a plain request under
`message-queue/needs-agent/requests/` through `status != "in-repair"`, then
`claimed_lifecycle_problem`, then
`resolution_evidence_problem`. The first two are satisfiable after the fact by committing the
one-line `open` to `in-repair` claim. The third is not.

Two escapes exist in that function and neither reaches this case:

- `generated_retry_clear` applies only when `actor == "needs-agent"`, `leaf == "retries"`,
  and `reconciler_owned_retry` recognises the item, so it covers reconciler-filed repairs and
  not requests.
- `pickup_completed` applies only when the item carries `Request kind: task-pickup`.

An ordinary request filed by an agent for another session has neither property, so it has no
path to resolution once its evidence has merged.

### The live instance

The item `blocking-repair-handover-projection-code-span-copy.md` under
`message-queue/needs-agent/requests/` sits at `in-repair` as of commit `5bf0bba`. Its action
was completed by commit `6d4e337`, merged into `main` through pull request 14, and all three
of its own `Done when` clauses are satisfied on `main`: the repaired comparison, six
regression tests of which four fail against the pre-fix checker, and the previously blocked
handover committed at a fresh conversation path. Its predeclared evidence is
`automation/reconcile/reconcile.py`, which now holds the repair, so a deletion commit has
nothing left to change there.

The consequences are both live. The item still declares
`Blocks now: operation:session-handover`, a blocker the merged repair removed, so the queue
overstates what is blocked. And task 2026-07-25-fix-handover-projection-code-span-copy names
that item in its `Queue actions`, so it stays at `1_in-progress` for as long as the item
does — `4_done` normally requires `Queue actions: none`, and `2_blocked` is unavailable
because the item's `Blocks now` names an operation rather than that task id.

### The contract already reads the way the fix needs to read

`handbook/git-workflow.md` states the rule as "Delete only after a one-line claim **and**
changed durable evidence". The evidence did change; the implementation additionally requires
it to change in one specific commit. Widening the implementation to match the prose it
enforces is the smaller of the two possible repairs, and the alternative — restating the
prose as a single-commit rule — would leave the live item permanently unresolvable.

The implementation shape is deliberately left open. The criteria below fix what the repair
proves, not how.

## Acceptance criteria

- [ ] WHEN an item's resolution evidence changed in any commit at or after its committed
      `open` to `in-repair` claim edge, and no later commit reverted that change, THE CHECK
      SHALL admit the deletion
- [ ] WHEN an item's resolution evidence never changed in any commit anywhere in its
      lineage, THE CHECK SHALL still report
      `deleted unresolved queue item: resolution evidence was not created or changed`
- [ ] WHEN an item declares no non-queue resolution evidence, or names a path that is
      unreadable, absent from every revision examined, or fails to resolve, THE CHECK SHALL
      report rather than admit the deletion — an unavailable evidence path fails closed
- [ ] WHEN an item was never committed at `in-repair`, or its claim edge changed more than
      the status line, THE CHECK SHALL still report, so widening the evidence window does not
      widen the claim requirement
- [ ] The `needs-human` folding path, the `generated_retry_clear` retry escape, and the
      `pickup_completed` task-pickup escape reach the same verdicts they reach today, each
      covered by a test that passes before and after the repair
- [ ] `automation/tests/test_reconcile_queue.py` gains tests for the admitted case, the
      never-changed case, and the unavailable-evidence case, and `verification.md` records
      each new test's verdict against the pre-repair checker so the discriminating ones are
      identifiable
- [ ] The live item named above is deleted in a commit that passes
      `python3 automation/reconcile/reconcile.py --check`, and task
      2026-07-25-fix-handover-projection-code-span-copy reaches `Queue actions: none`
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0 and
      `python3 automation/run_tests.py` passes, with both outputs recorded in
      `verification.md`
- [ ] `design.md` states which lineage window was chosen and what a reverted evidence change
      does under it, and carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The check and both functions involved: `automation/reconcile/reconcile.py`
- The prose rule the implementation is stricter than: `handbook/git-workflow.md`
- Queue resolution lifecycle this preserves: `message-queue/AGENTS.md`
- Guardrail that forbids weakening a check to pass, which is why the window is widened with
  tests rather than removed: `automation/AGENTS.md`
- The task held at `1_in-progress` by the live item: 2026-07-25-fix-handover-projection-code-span-copy
