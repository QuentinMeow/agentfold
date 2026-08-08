# Two commits on the review-receipt branch fail the merge reconciler at their own edge

**Status:** open
**Severity:** medium — cost or manual workaround
**Description:** Withdrawing the `adversarial panel` receipt grammar re-exposes two panel transcripts that its own commits recorded, and a task edge cannot be repaired from a later commit.
**Review-by:** 2026-11-05

## Symptom

On branch `task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks`, the
command a pull request runs exits 1 with two `task-action-origin` findings, both naming
`- adversarial panel / core fit reviewer: approve — …` lines in the task's
`verification.md`:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks \
    --range <main>...<branch head>
reconcile: 2 blocking finding(s)
```

Both lines are fenced at the branch head, and the same command over
`679a62a...<branch head>` — the withdrawal baseline forward — reports 0 blocking
findings. The two edges that fail are `50f2cf5` and `df0a5de`, the commits that first
wrote those transcripts.

## Impact

The branch cannot be merged through CI until the two edges are cleared, so the two
finished repairs that depend on it stay unpublished. Nothing else is affected: the
working tree, the pre-commit hook, and every range from the withdrawal baseline forward
are clean.

The cause is not a defect in the repaired parser. Those commits committed cleanly because
the implementation they carried exempted `- adversarial panel / …` lines under a second
receipt grammar. `memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md`
withdrew that grammar, and a task edge is evaluated against the bytes of its own commit,
so a fence added later cannot repair it. Both properties are deliberate: an ask must not
be committable and then hidden by a follow-up.

## Workaround

None that clears the edges. Fencing at the head keeps every later edge clean, which is
what the branch does now.

## Suggested fix

Three options, none of them an agent's to choose alone:

- Rewrite the unpushed branch history so the fence lands in `50f2cf5` and `df0a5de`
  themselves. `handbook/git-workflow.md` forbids rewriting *pushed* history and this
  branch has never been pushed, so the rule does not bar it — but every commit id
  changes, and `verification.md` binds sixteen panels to exact revisions that would stop
  existing. Needs the owner's decision because it is one-way.
- Merge with the two findings recorded and accepted as history, which needs a decision
  about how such an acceptance is expressed, since no mechanism exists for it today.
- Restore a grammar that exempts `- adversarial panel / …` lines. The 2026-08-07 decision
  forbids this; re-admitting it needs its own decision and would reopen the surface that
  decision closed.

Whichever is chosen, the general lesson is separate and cheap to act on: a check that
evaluates per-commit edges makes any exemption a *retroactive* commitment, so withdrawing
one strands every record that relied on it.
