# Stop a restack from being blamed for a queue deletion another branch made

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from an adversarial review of pull request #65 that reproduced it deterministically
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-restack-from-being-blamed-for-another-branchs-deletion.md`

## Goal

Restacking a task branch onto current `main` produces a blocking finding accusing that
branch of discarding a live queue action it never touched.

Reproduced deterministically, on a branch whose only commit touched `PROBE.md` and which
never touched `message-queue/` at all:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/... --range 8b2361f...<new head> --displaced-tip <old tip>
[queue-resolution] message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md:
  deleted unresolved queue item: divergent update discarded a live old-tip action
reconcile: 1 blocking finding(s)

$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/... --range 8b2361f...<new head>
reconcile: 0 blocking finding(s)
```

The branch was built off a commit where that queue item existed, then restacked onto the
commit where a different agent had deleted it **with proper evidence**. The deletion is
inherited from the moved base; the finding blames the restacking branch.

`--displaced-tip` is passed on every force-push, and restacking a branch onto a newly merged
parent is what `handbook/git-workflow.md` calls expected. So this fires on ordinary work, and
its repair is to force-push again and hope — which is how a real finding gets ignored.

## Root cause, already localised

`check_queue_resolution` assigns the continuity-edge problem as a constant string with no
evidence check, and `committed_queue_deletion_events` in `automation/reconcile/reconcile.py`
is a plain two-dot `git diff-tree` between the displaced tip and the new head. A deletion
inherited from the moved base is therefore indistinguishable from one this branch made.

The fix probably already exists in the same file: the non-continuity path guards with
`candidate_paths_match_other_parent`, and the continuity path has no equivalent. Read both
before writing anything — the asymmetry may be deliberate, and if it is, the repair is to
say why in a comment and find a different discriminator.

## The protection this preserves

The check exists so a force-push cannot quietly discard a live action that the old tip
carried. That is a real protection, and weakening it is not an acceptable outcome here. The
distinction being drawn is between an action the branch discarded and one the new base
resolved legitimately with its own evidence — not between "noisy" and "quiet".

## Acceptance criteria

- [ ] WHEN a branch is restacked onto a base that legitimately resolved a queue item with
      committed evidence, and the branch itself never touched `message-queue/`, THE
      RECONCILER SHALL emit no `queue-resolution` finding. Use the reproduction above as
      the regression fixture.
- [ ] WHEN a force-push genuinely discards a live action the displaced tip carried, THE
      RECONCILER SHALL still report it. Prove the guard still bites by removing the new
      discrimination in a copy and showing the test go red.
- [ ] WHEN the base resolved the item but without the evidence its own lifecycle requires,
      THE RECONCILER SHALL still report something. Silence here would let a bad deletion
      launder itself through a restack.
- [ ] `design.md` states whether the continuity path's lack of a
      `candidate_paths_match_other_parent` guard was deliberate, with the evidence for
      that reading.
- [ ] `python3 automation/run_tests.py` passes, real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## Links

- The reproduction's origin: the adversarial review of pull request #65
- Why restacking is expected rather than exceptional: `handbook/git-workflow.md`
- The sibling stale-base defect, which is separate: task `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
