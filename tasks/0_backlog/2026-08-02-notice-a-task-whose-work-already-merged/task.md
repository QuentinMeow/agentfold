# Report a task still filed as unfinished whose work is already on main

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from a status audit that found 22 of 24 open task folders holding merged work
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-notice-a-task-whose-work-already-merged.md`

## Goal

`tasks/AGENTS.md` says the status folder a task sits in **is** its status, with no field to
drift. On 2026-08-02 an audit found that promise broken in bulk: `tasks/1_in-progress/` and
`tasks/3_in-review/` together held 24 folders, 22 of them work already merged into `main`
with every branch deleted. `python3 automation/reconcile/reconcile.py --check` reported
`0 blocking finding(s)` throughout, because no check compares a task's folder against
whether its work has landed.

That is a hole in the referee, not a one-off mistake. Nothing stops it recurring the next
time a run of pull requests merges — and the record it corrupts is the one every agent reads
to decide what to pick up.

Build the check. A task under `1_in-progress/` or `3_in-review/` whose work is demonstrably
on `main` — its `task/<id>` branch merged, or every `task: <id>`-tagged commit an ancestor
of `main` — and which carries a `verification.md` with real recorded output, is a task whose
folder is lying. Report it, naming the task and the evidence.

## Design questions this task must settle and record in `design.md`

- **Severity tier.** A blocking finding would fire in the ordinary window between merging a
  pull request and moving the folder, and would then refuse every unrelated commit until
  somebody did the paperwork. Advisory prints and never exits 1
  (`ADVISORY_CHECKS` in `automation/reconcile/reconcile.py`). Weigh the false-positive cost
  against the fact that this drift went 22 tasks deep while the tree stayed green, and say
  which you chose and why.
- **What counts as "merged".** Branch-based detection breaks once a branch is deleted, which
  is exactly the state the audit found. Commit-token detection (`task: <id>`) depends on
  commit discipline. Decide what evidence the check actually reads, and what it does when
  a task has neither signal — silence is the safe answer for an unstarted task, and a
  false accusation is worse than a miss.
- **Cost.** The reconciler runs on every commit through the pre-commit hook, and a previous
  task existed purely to cut its recomputation
  (`2026-07-31-cut-reconciler-recomputation`). Whatever Git reads this check needs must be
  batched or cached the way the existing checks are; measure the before and after.

## Acceptance criteria

- [ ] WHEN a task folder sits in `1_in-progress/` or `3_in-review/`, its work is on `main`
      by the evidence rule chosen in `design.md`, and it carries a `verification.md` with
      real output, THE RECONCILER SHALL emit one finding naming the task id and the
      evidence that its work landed.
- [ ] WHEN a task folder sits in `1_in-progress/` with no merged work, THE RECONCILER SHALL
      emit nothing for it. This is the false-positive criterion and needs a test of its own.
- [ ] WHEN a task has merged work but no real `verification.md`, THE RECONCILER SHALL NOT
      report it as ready to move, because `tasks/AGENTS.md` bars `4_done` without one.
- [ ] The check id is a key in `CHECKS`, and its severity tier matches what `design.md`
      argues for. If advisory, it is a member of `ADVISORY_CHECKS`.
- [ ] Running the reconciler against the repository as it stands after the 2026-08-02
      cleanup emits no finding from this check — the tree is the fixture that proves the
      rule does not fire on correct state.
- [ ] A test reconstructs the 2026-08-02 drift (a task in `3_in-review` whose branch merged)
      and asserts the check reports it. Without that test the check is not shown to catch
      the failure it exists for.
- [ ] Reconciler wall-clock before and after is measured and recorded in `verification.md`
      with the real numbers.
- [ ] `python3 automation/run_tests.py` passes, real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## Links

- The drift this exists to catch: the 2026-08-02 status audit, and the cleanup commits that
  moved the affected tasks to `tasks/4_done/`
- Invariant being defended: `tasks/AGENTS.md`, "the status folder it sits in **is** its status"
- Severity tiers: `automation/AGENTS.md`, and the backlog task `2026-07-22-severity-tiers-for-reconciler-findings`
- Reconciler cost precedent: `tasks/*/2026-07-31-cut-reconciler-recomputation`
