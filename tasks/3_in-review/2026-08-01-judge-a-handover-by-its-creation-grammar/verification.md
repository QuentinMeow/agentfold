# Verification — judge a handover by its creation grammar

**Verified:** 2026-08-01 by claude (worktree agent-a3dd7926a22a81287)

Only commands actually run and their real output. Elisions are marked `[... N identical
lines elided ...]` and never hide a different message; everything else is verbatim.
Git 2.50.1 (/usr/bin/git) throughout, because the PATH git is 2.23.0.

Commits: `0aeb7ff` = `origin/main` at start. `ac5dae2` file, `863810f` claim,
`71fb066` the repair. `99a2c84` is the PR #44 merge probe (below). This worktree does
not push; every commit is local.

## 1. Baseline on the unmodified tree (`0aeb7ff`)

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/run_tests.py
[... lane and shard output elided ...]
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 49.78s
```

## 2. Failure 1 reproduced — PR #44 cannot merge

At `HEAD = e4e631c` (the existing merge; first parent `0aeb7ff`, second `6c723ef`),
unmodified tree:

```
$ /usr/bin/git checkout --detach e4e631c
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-31-let-a-human-answer-in-one-edit \
    --range 0aeb7ff7b88d8670bae7962c6fe026ecfeb8522f...e4e631cd5806418071bce91a9ae89d9cacee3216
[handover-queue-projection] history/conversations/2026-07-31-0910PDT-let-a-human-answer-in-one-edit/handover.md: Needs your attention entry 1 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
[... entries 2-8: the same message, differing only in the entry number ...]
[handover-queue-projection] history/conversations/2026-07-31-0910PDT-let-a-human-answer-in-one-edit/handover.md: Needs your attention entry 9 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
reconcile: 9 blocking finding(s)
```

## 3. Failure 2 reproduced — already latent on `main`

`b98621f` created the `2026-08-01-1522PDT-admit-a-candidates-whole-task-scope` handover
and is an ancestor of `main`; `b4f3667` is `main` immediately before PR #52 merged it in.
At `HEAD = 0aeb7ff`, unmodified tree:

```
$ python3 automation/reconcile/reconcile.py --check \
    --range b4f36671311d3bb6d90409cecccc16031615d643...0aeb7ff7b88d8670bae7962c6fe026ecfeb8522f
[handover-queue-projection] history/conversations/2026-08-01-1522PDT-admit-a-candidates-whole-task-scope/handover.md: Needs your attention entry 1 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
[... entries 2-8: the same message, differing only in the entry number ...]
[handover-queue-projection] history/conversations/2026-08-01-1522PDT-admit-a-candidates-whole-task-scope/handover.md: Needs your attention entry 9 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
reconcile: 9 blocking finding(s)
```

## 4. Diagnosis — the reused version number, from Git

Both handovers declare `v2` in their own creation snapshot, and both descend from a
commit that once declared `v3` before it was withdrawn:

```
$ /usr/bin/git show 03ec388:history/AGENTS.md | grep -n "action-entry"
4:**Queue action-entry schema:** v3
$ /usr/bin/git show b4c6627:history/AGENTS.md | grep -n "action-entry"
4:**Queue action-entry schema:** v2
$ /usr/bin/git show 219ae1f:history/AGENTS.md | grep -n "action-entry"
4:**Queue action-entry schema:** v3
$ /usr/bin/git show b4c6627:automation/reconcile/reconcile.py | grep -n "HANDOVER_ENTRY_VERSIONS\s*="
230:HANDOVER_ENTRY_VERSIONS = ("v1", "v2")
```

```
$ /usr/bin/git show 0177331:history/AGENTS.md | grep -n "action-entry"
4:**Queue action-entry schema:** v2
$ /usr/bin/git show b98621f:history/AGENTS.md | grep -n "action-entry"
4:**Queue action-entry schema:** v2
$ /usr/bin/git merge-base --is-ancestor 03ec388 0177331 && echo ancestor
ancestor
$ /usr/bin/git merge-base --is-ancestor 03ec388 b98621f && echo ancestor
ancestor
$ /usr/bin/git merge-base --is-ancestor 219ae1f 0177331 || echo "not an ancestor"
not an ancestor
```

So both records are respelled twice over: by the **withdrawn** `v3` they descend from,
and by the **parallel** `v3` joined at the admitting merge.

## 5. Ground truth — every reachable handover already matches its own creation marker

Script: a throwaway audit.py outside the repository. For each handover in `0aeb7ff`, it reads
`history/AGENTS.md` at the commit that added the record and compares the marker there
with the suffix the record actually uses.

```
$ python3 audit.py
handovers reachable from 0aeb7ff: 66
  creation-snapshot marker   v1 -> suffix OLD  : 27
  creation-snapshot marker   v2 -> suffix OLD  : 26
  creation-snapshot marker   v3 -> suffix NEW  : 1
  creation-snapshot marker None -> suffix OLD  : 1
  creation-snapshot marker None -> suffix none : 11
records whose suffix disagrees with their own creation-snapshot marker: 0
```

The single `v3`+new-suffix record is `2026-08-01-1030PDT-stop-human-answers-from-gating-git-edges`
(created at `9c0c7e6`). It is why renumbering the rename off the burned `v3` was rejected.

## 6. New tests fail before the change

Run at `863810f` (task claimed, tests added, `reconcile.py` untouched):

```
$ python3 -m unittest \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_withdrawn_entry_version_does_not_respell_a_later_record \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_parallel_entry_bump_does_not_respell_a_merged_record \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_branch_cut_early_cannot_evade_a_later_rejection \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v3_admission_keeps_every_v2_rejection
FAIL: test_a_withdrawn_entry_version_does_not_respell_a_later_record
AssertionError: Lists differ: [] != ['Needs your attention entry 1 must copy t[95 chars]fix']
FAIL: test_a_parallel_entry_bump_does_not_respell_a_merged_record
AssertionError: Lists differ: [] != ['Needs your attention entry 1 must copy t[95 chars]fix']
FAIL: test_a_branch_cut_early_cannot_evade_a_later_rejection
AssertionError: False is not true : ['Needs your attention entry 1 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix']
FAIL: test_v3_admission_keeps_every_v2_rejection
AssertionError: False is not true : []
----------------------------------------------------------------------
Ran 4 tests in 4.340s

FAILED (failures=4)
```

`test_a_branch_cut_early_cannot_evade_a_later_rejection` is a `subTest` over
`("v1","v2")` and `("v2","v3")`. Re-run alone, only the second case fails before the
change — the classic v1 -> v2 anti-dodge property already held, and the v2 -> v3 case
shows it had stopped holding once a version renamed instead of rejecting:

```
$ python3 -m unittest ...test_a_branch_cut_early_cannot_evade_a_later_rejection -v
FAIL: test_a_branch_cut_early_cannot_evade_a_later_rejection (initial='v2', bumped='v3')
AssertionError: False is not true : ['Needs your attention entry 1 must copy the creation-snapshot why-this-matters and if-you-do-nothing fields using the fixed handover suffix']
----------------------------------------------------------------------
Ran 1 test in 1.969s

FAILED (failures=1)
```

## 7. The same four tests pass after the change (`71fb066`)

```
$ python3 -m unittest \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_withdrawn_entry_version_does_not_respell_a_later_record \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_parallel_entry_bump_does_not_respell_a_merged_record \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_branch_cut_early_cannot_evade_a_later_rejection \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v3_admission_keeps_every_v2_rejection
....
----------------------------------------------------------------------
Ran 4 tests in 5.756s

OK
```

## 8. Failure 2 fixed — before and after over the identical range and HEAD

`tmp/reconcile/reconcile.py` is `git show 0aeb7ff:automation/reconcile/reconcile.py`
placed under git-ignored `tmp/` at the depth the script derives `REPO` from, with
`automation/*.py` beside it. Both runs use `HEAD = 71fb066` and the same `--range`, so
the only variable is the reconciler itself.

```
$ python3 tmp/reconcile/reconcile.py --check \
    --range b4f36671311d3bb6d90409cecccc16031615d643...71fb06666d5563f1c7fd85f90c683b0921be5346
[... the same 9 findings on 2026-08-01-1522PDT-admit-a-candidates-whole-task-scope/handover.md ...]
reconcile: 9 blocking finding(s)
```

```
$ python3 automation/reconcile/reconcile.py --check \
    --range b4f36671311d3bb6d90409cecccc16031615d643...71fb06666d5563f1c7fd85f90c683b0921be5346
reconcile: 0 blocking finding(s)
```

## 9. Failure 1 fixed — the PR #44 merge probe

`e4e631c` does not merge cleanly onto the repaired tip (PR #44 and this task both touch
`reconcile.py`, and PR #44's own conflicts with `main` were resolved when `e4e631c` was
made). The probe therefore reuses `e4e631c`'s already-resolved tree and applies this
task's three commits to it, then records the result as a merge whose **first parent is
the repaired main** and whose second parent is `6c723ef`:

```
$ /usr/bin/git checkout --detach e4e631c
$ /usr/bin/git cherry-pick -n ac5dae2 863810f 71fb066
Auto-merging automation/reconcile/reconcile.py
Auto-merging automation/tests/test_reconcile_queue.py
Auto-merging memory/index.md
$ /usr/bin/git write-tree
e4253728939cf63e592e1a55ee4450974e8de098
$ /usr/bin/git commit-tree e4253728939cf63e592e1a55ee4450974e8de098 \
    -p 71fb06666d5563f1c7fd85f90c683b0921be5346 \
    -p 6c723eff9edc8f46746c76aaf1f39a72b5fbd951 \
    -m "Merge the one-edit answer branch onto the repaired main"
99a2c849366a772cb81006515c82101ad5e3c208
$ /usr/bin/git log -1 --format='%H %P %s' 99a2c84
99a2c849366a772cb81006515c82101ad5e3c208 71fb06666d5563f1c7fd85f90c683b0921be5346 6c723eff9edc8f46746c76aaf1f39a72b5fbd951 Merge the one-edit answer branch onto the repaired main
```

Same probe, same HEAD, pre-fix reconciler versus post-fix reconciler:

```
$ python3 tmp/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-31-let-a-human-answer-in-one-edit \
    --range 71fb06666d5563f1c7fd85f90c683b0921be5346...99a2c849366a772cb81006515c82101ad5e3c208
[... the same 9 findings on 2026-07-31-0910PDT-let-a-human-answer-in-one-edit/handover.md ...]
reconcile: 9 blocking finding(s)
```

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-31-let-a-human-answer-in-one-edit \
    --range 71fb06666d5563f1c7fd85f90c683b0921be5346...99a2c849366a772cb81006515c82101ad5e3c208
reconcile: 0 blocking finding(s)
```

The probe merge is also clean on its own terms:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
$ python3 automation/run_tests.py
[... lane and shard output elided ...]
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 47.95s
```

## 10. Gates on the task branch (`71fb066`)

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/check_core_scope.py
core-scope: pass (2 core path(s), task 2026-08-01-judge-a-handover-by-its-creation-grammar; independent review manual; not invoked)
```

```
$ python3 automation/run_tests.py
[... lane and shard output elided ...]
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 75.99s
```

The pre-commit hook ran core scope, the reconciler, and the staged test lane on every
commit here; none was made with `--no-verify`.

## 11. The re-enabled v2 rejection fired on this session's own handover

Unplanned but conclusive. The first `--check` after staging this session's handover — a
record whose creation snapshot declares `v3` — rejected it under the origin clause that
was switched off before this change:

```
$ python3 automation/reconcile/reconcile.py --check
[handover-queue-projection] history/conversations/2026-08-01-2100PDT-judge-a-handover-by-its-creation-grammar/handover.md: action-like question or directive exists outside the queue-owned projection sections
    fix: move the pending action into a canonical queue item and project it only from Needs your attention or Next steps
[... two link-check findings on verification.md, both since fixed ...]
reconcile: 3 blocking finding(s)
```

Two rhetorical questions in `How it works now` and one sentence in `Dead ends` triggered
it. They were reworded — a live record, still being written, so no immutable bytes were
touched — and the check went clean.

## 12. No committed record bytes changed

```
$ /usr/bin/git diff --stat 0aeb7ff 71fb066 -- history/conversations
$
```

Empty: not one handover byte differs.

```
$ /usr/bin/git diff --stat 0aeb7ff 71fb066
 automation/AGENTS.md                               |   6 +-
 automation/reconcile/reconcile.py                  | 101 ++++++++---
 automation/tests/test_reconcile_queue.py           | 196 +++++++++++++++++++++
 history/AGENTS.md                                  |  12 +-
 ...-records-are-judged-at-their-written-grammar.md |  58 ++++++
 memory/index.md                                    |   2 +
 .../never-reuse-a-withdrawn-schema-version.md      |  33 ++++
 .../design.md                                      |  94 ++++++++++
 .../plan.md                                        |  19 ++
 .../task.md                                        |  49 ++++++
 .../worklog.md                                     |  10 ++
 11 files changed, 544 insertions(+), 36 deletions(-)
```

## 13. Repeated at the commit that carries this file (`eae7a62`)

Sections 1–12 were run at `71fb066`, before the record commit existed. Everything was
re-run at `eae7a62`, the tip that carries this `verification.md`, with the merge probe
rebuilt the same way on top of it (`93f8802`, first parent `eae7a62`).

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/run_tests.py
[... lane and shard output elided ...]
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 31.44s
```

```
$ /usr/bin/git log -1 --format='%H %P %s' 93f8802
93f8802a3f3a60df6d27e0964faf3beffddb2155 eae7a62c09a817bd324da43c1d30067fda7710d8 6c723eff9edc8f46746c76aaf1f39a72b5fbd951 Merge the one-edit answer branch onto the repaired main
```

```
$ python3 tmp/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-31-let-a-human-answer-in-one-edit \
    --range eae7a62c09a817bd324da43c1d30067fda7710d8...93f8802a3f3a60df6d27e0964faf3beffddb2155
[... the same 9 findings on 2026-07-31-0910PDT-let-a-human-answer-in-one-edit/handover.md ...]
reconcile: 9 blocking finding(s)
```

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-31-let-a-human-answer-in-one-edit \
    --range eae7a62c09a817bd324da43c1d30067fda7710d8...93f8802a3f3a60df6d27e0964faf3beffddb2155
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/reconcile/reconcile.py --check \
    --range b4f36671311d3bb6d90409cecccc16031615d643...93f8802a3f3a60df6d27e0964faf3beffddb2155
reconcile: 0 blocking finding(s)
```

## What this run did not verify

- **Nothing was pushed.** `71fb066` and the probe merge `99a2c84` exist only in this
  worktree, so no CI, no GitHub adapter, and no real merge of PR #44 was exercised.
- **The probe merge is reconstructed, not the original `e4e631c`.** Its tree is
  `e4e631c`'s tree plus this task's commits; its first parent is the repaired main.
  A real PR #44 merge after this lands would resolve `reconcile.py` the same way, but
  that resolution has not been performed by a human or by GitHub.
- **`handover_liveness_version_for` is untouched** and still governs by the admission
  floor. The same unsatisfiability is possible there in principle; no reproduction exists
  on `main` or in the PR #44 range, so nothing was changed on evidence.
- **Independent core-fit review was not invoked** — `check_core_scope.py --require-review`
  launches no reviewer and was not run with that flag.
