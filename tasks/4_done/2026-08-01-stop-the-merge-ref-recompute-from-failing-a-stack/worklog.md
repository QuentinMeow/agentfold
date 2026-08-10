# Worklog — Stop the merge-ref recompute race from failing every stacked pull request

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stop-the-merge-ref-recompute-from-failing-a-stack (claude)

- Claimed the task and moved it to `1_in-progress`; resolved and deleted
  `message-queue/needs-agent/requests/non-blocking-pick-up-stop-the-merge-ref-recompute-from-failing-a-stack.md`
  in the same coordination commit.
- Claimed from an isolated detached worktree rather than the shared `main` checkout,
  which had another agent's uncommitted edits in it at the time.
- Confirmed the defect by reading the two projection jobs side by side.
  `authoritative-external-action-projection` had already been repaired for the same class
  of problem and binds its candidate through the merge commit's own parents;
  `review-state-action-projection` still asserted bare equality with `github.sha`. Reused
  that binding rather than inventing a second mechanism.
- Rejected the shape the phrase "recompute race" invites — retry until the two values
  agree. After a recompute they never agree, because `github.sha` names a merge onto a base
  the pull request no longer has; that loop would spend its bound and fail anyway. Recorded
  it as the rejected option in `design.md`.
- The `MergeRefFixture` harness already in
  `automation/tests/test_github_action_projection_workflow.py` runs a step's literal `run:`
  block against a local bare repository, so the new tests exercise the real shell rather
  than a paraphrase of it. Added three: the recompute is admitted, every genuine mismatch
  still fails, and the bound is a counted loop with fail-closed bounds.
- Proved the guard bites by mutation instead of assertion: deleting the head comparison
  from a copy of the workflow turns the genuine-mismatch test red. The transcript is in
  `verification.md`.
- Two stale numbers found in the task record and left for their owners: the premise cites
  a decision queue item that was answered and deleted (its outcome is
  `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`,
  and another agent is repairing the citation), and the acceptance criterion asks for
  `11/11` test files when the suite now has 12.
- Filed nothing in `message-queue/`: the task's `Queue actions` is `none` and this change
  raises no question for the owner.
- Opened PR #65 and captured its own CI run as evidence. `Current review-state action
  projection` passed on a real runner with the rewritten step, but its job log shows the
  candidate equalled `github.sha`, so it took the fast path — the re-resolution branch has
  still only run in the fixture. Recorded that distinction rather than letting a green check
  imply more than it proves.
- Two CI failures on PR #65 came from the shared trunk moving under an open branch, not
  from this change, and both are worth someone's attention:
  - `reconcile-and-test` exited 2 with `Git snapshot error: captured candidate is neither
    the --range head nor an exact base+head synthetic merge`. GitHub had computed
    `refs/pull/65/merge` against a `main` newer than the `base.sha` in the same event
    payload, so the checked-out merge commit's first parent was not the declared base. That
    is the same stale-base race this task repairs in `review-state-action-projection`,
    reached through a different job; the fix here does not touch it. Restacking the branch
    onto current `main` cleared it.
  - The restack's force push then produced `[queue-resolution] ... deleted unresolved queue
    item: divergent update discarded a live old-tip action` for
    `message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md`.
    Another agent deleted that item on `main` between the two bases, so the displaced-tip
    comparison read someone else's evidenced deletion as this branch discarding a live
    action. An ordinary push whose previous tip already carries the deletion does not
    reproduce it.
- The stale-base failure recurred a third time (job `91494071784`) on a later push, which
  settles it as reproducible rather than incidental: `main` advances every few minutes while
  several agents merge, and each advance can leave an open branch's `pull_request` payload
  naming an older base than the merge ref GitHub computes. Stopped re-pushing to chase a
  green board and left the branch published with the cause recorded. Filed no queue item for
  it — the session that owns coordination decides whether this becomes its own task, and
  filing it here risked duplicating one.

## 2026-08-02 (continued) — the bound's missing upper end (claude)

This entry continues the session above, which ended when the machine it ran on crashed. The
repair below was in the worktree uncommitted at that point; it is committed here with the
design and verification records it needed and did not have.

- Re-read the branch against its own fail-closed constraint and found the bound guarded at
  one end only. `[` reports **status 2**, not 1, when an operand overflows `intmax_t`, and
  `if` and `while` both read that as false — so a bound above 2^63-1 skipped the lower
  guard *and* every loop iteration, and the step fell out of the loop and published the
  empty string. Exit 0, `revision=`, no guard having rejected anything.
- That is a real fail-open in the step as pull request #65 published it, not a
  hypothetical. Both directions are recorded in `verification.md` as run output: the
  pre-repair script from `HEAD` exiting 0 with `revision=`, and the repaired script exiting
  1 with `no candidate revision was bound`.
- Two independent changes close it. `-gt 100` beside `-lt 1` makes the guard a range, which
  is what it always meant — 9223372036854775807 is a number `[` accepts and a loop that
  long is `while :` with extra steps. The load-bearing one is the positive check after the
  loop: reaching the `printf` must *mean* a candidate was bound, because every guard inside
  the loop is a way to reject one and a path that skips the loop skips all of them.
- Deliberately did not probe 9223372036854775807 itself. Any value over the cap reaches the
  same guard and `101` does it in a microsecond, where that one would hang the suite if a
  later edit removed the cap. The reasoning is written beside the case in the test.
- Added a fidelity warning to `step_shell_script`'s docstring: the block ends at the first
  under-indented line, so an indent broken mid-script yields a silent *prefix* of the step
  that can still satisfy every assertion made about the surviving part. The new test pins
  the script's last lines, so a truncated block no longer contains them.
- `python3 automation/run_tests.py` green, 12/12 files; `reconcile.py --check` 0 blocking.
- The two red `reconcile-and-test` checks on pull request #65 are unchanged and are still
  not this branch's: both are the stale-base race recorded above, now filed as its own task
  (`2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`). No check was weakened
  and no `--no-verify` bypass was used.

## 2026-08-09 — close-tasks-whose-work-already-merged (claude)

- The work merged to `main` in pull request #65 on 2026-08-03; only the folder never moved,
  so its status has misreported reality since. Moved to `4_done` to match.
- Verified before moving: `verification.md` holds real command output, the merge-ref
  re-resolve lives in `.github/workflows/harness.yml` on `main`, and no live blocking agent
  action names this task.
