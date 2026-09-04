# Verification — Stop a restack from being blamed for another branch's deletion

**Verified:** 2026-09-04 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Environment: the clean task worktree
`.git/agents/worktrees/2026-08-31-prove-the-correct-restack-queue-201c/_clean` on branch
`task/2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`, cut from the
owner-words branch at 6598e40; no private overlay; macOS host; Python 3.14; one local process
at a time unless the pre-commit hook chose otherwise. Earlier sections quote the writer's
worktree and the original branch, which the archive tag preserves.

## Regression fixture red before the repair (writer worktree at c22475e, production code unchanged)

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest automation.tests.test_reconcile_queue -k continuity
FAIL: test_continuity_edge_accepts_a_restack_over_a_valid_base_resolution (automation.tests.test_reconcile_queue.ReconcileQueueTests.test_continuity_edge_accepts_a_restack_over_a_valid_base_resolution)
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x106cb46e0>]
+ [<reconcile_queue.Finding object at 0x106cb46e0>] : ['deleted unresolved queue item: divergent update discarded a live old-tip action']
Ran 1 test in 0.234s
FAILED (failures=1)
```

## Observed red: the guard still bites (scratch copies of `automation/`, never committed)

```
(a) silence no longer requires a same-identity resolution:
FAIL: test_continuity_edge_keeps_finding_when_the_base_resolved_a_rewritten_action
AssertionError: 1 != 0 : []
(b) the real deletion edge is no longer validated:
FAIL: test_continuity_edge_reports_an_inherited_deletion_without_evidence
FAIL: test_continuity_edge_reports_an_invalid_redeletion_after_reintroduction
FAIL: test_continuity_edge_validates_a_pre_activation_base_deletion
AssertionError: 1 != 0 : []
(c) the old-tip-equals-merge-base guard removed:
FAIL: test_continuity_edge_keeps_finding_when_old_lineage_changed_the_action
AssertionError: 1 != 0 : []
ERROR ... GitSnapshotError: could not read <action> from <C>  (three tests whose action never existed at C)
(d) the merge-propagation skip removed:
FAIL: test_continuity_edge_accepts_a_base_resolution_merged_from_a_side_branch
(e) identity-preserving moves no longer followed:
FAIL: test_continuity_edge_follows_a_timing_move_before_the_base_resolution
(f) only each commit's first parent examined:
+ [<reconcile_queue.Finding object at 0x109232660>] : ['deleted unresolved queue item: divergent update discarded a live old-tip action']
FAIL: test_continuity_edge_judges_a_deletion_reachable_only_through_a_second_parent
Ran 1 test in 0.539s
FAILED (failures=1)
```

Mutation (a) leaves the existing divergent-range test and the mixed-drop test green because their
dropped action is absent at the merge base, so the old-tip guard already returns the constant
finding; the same-identity requirement is pinned by the rewritten-identity test instead.

## Fresh-context panel on the reviewed diff (three lenses; findings r46–r48 in the orchestration run)

- correctness / r46: `approve` — could not break the continuity deletion path on seventeen probed histories (evil merge with both parents carrying the item, absence adopted from a pre-merge-base fork, criss-cross bases, rename kinds, second-parent-only deletion edges); missing objects raise `GitSnapshotError` and exit 2; a 1,516-commit walk took 0.61 s; six of seven guard removals turned named tests red, and the seventh gained its test (mutation f above).
- requirements match / r47: `approve` — AC1–AC4 and AC6 met with re-verified evidence; the `git log -S` sentences in the design hold with the `-- automation/reconcile/reconcile.py` and `--all -m` qualifiers.
- blast radius / r48: `block` on one finding — two follow-ups were named but not filed; remedied by filing both as backlog tasks (carried on this branch). Everything else held: one call site, no `--range` dependence, no retry-identity change, the merge-transition reconciler reported 0 blocking findings.

Panel result after the remedy: 2 approve, 1 block resolved. The cross-vendor refuter: DID NOT RUN (no read-only Codex permission granted in this session).

## The clean branch carries the reviewed repair byte for byte

```
$ git diff 6598e40 5407000 -- automation/ > patch-clean.diff
$ git diff c22475e 3153f7d -- automation/ > patch-reviewed.diff
$ diff <(grep -v '^index \|^@@' patch-clean.diff) <(grep -v '^index \|^@@' patch-reviewed.diff) && echo "identical except blob ids and hunk offsets"
identical except blob ids and hunk offsets
```

The two patches differ only in blob ids and hunk line numbers, because the owner-words branch
added lines earlier in the same file; every added and removed line is the same.

## Commit gate on the repair commit 5407000 (pre-commit hook, staged lane at its default parallelism)

```
pre-commit: core scope
core-scope: pass (2 core path(s), task 2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion; independent review manual; not invoked)
pre-commit: reconciler
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
pre-commit: staged-path repository tests
test workers: 15
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_provenance.py
PASS automation/tests/test_reconcile_queue.py
tests: 4/4 files passed
test elapsed: 43.03s
pre-commit: OK
```

## Gates at the repair commit 5407000 on the clean branch (serial)

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest automation.tests.test_reconcile_queue -k continuity -k displaced -k divergent
Ran 17 tests in 4.598s

OK

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
tests: 1/1 files passed
test elapsed: 0.07s
PASS automation/tests/test_second.py
tests: 2/2 files passed
test elapsed: 0.00s
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_provenance.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 17/17 files passed
test elapsed: 243.87s

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion --range 6598e4076fbe417117f89500f789e29238ccd355...5407000ff0bbc2a75b0fa983b80c5b7010f84aa3
reconcile: 0 blocking finding(s), 6 advisory (not blocking)

$ python3 automation/check_core_scope.py --range 6598e4076fbe417117f89500f789e29238ccd355...5407000ff0bbc2a75b0fa983b80c5b7010f84aa3 --branch task/2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion
core-scope: pass (2 core path(s), task 2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion; independent review manual; not invoked)
```

Cold clone of the same commit (fresh archive, single commit, no history):

```
$ python3 automation/install.py
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md: **Review revision:** is not a reviewable Git artifact: d87b755e6259101bf76b0a2783b35dfb3f163fb0 is unavailable; 8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b is unavailable
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md: **Review revision:** is not a reviewable Git artifact: 25d03257b5ee61753fa9bada609722c4e84a8064 is unavailable; fd2374d99796300ed4325c2961e696092c17875e is unavailable
[explanation-shape] message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md: line 44 continues the value of **Example consequence:** onto a second line; the reader sees the whole sentence and every check reads only its first half  (advisory)
[explanation-shape] message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md: line 51 continues the value of **Example consequence:** onto a second line; the reader sees the whole sentence and every check reads only its first half  (advisory)
[explanation-shape] message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md: line 59 continues the value of **Example consequence:** onto a second line; the reader sees the whole sentence and every check reads only its first half  (advisory)
[explanation-shape] message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md: line 68 continues the value of **Example consequence:** onto a second line; the reader sees the whole sentence and every check reads only its first half  (advisory)
[explanation-shape] message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md: line 78 continues the value of **Example consequence:** onto a second line; the reader sees the whole sentence and every check reads only its first half  (advisory)
[explanation-shape] message-queue/needs-human: 9 unanswered question(s) cannot be answered from their own bytes:
reconcile: 2 blocking finding(s), 6 advisory (not blocking)
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
tests: 1/1 files passed
test elapsed: 0.08s
tests: 2/2 files passed
test elapsed: 0.00s
tests: 1/1 files passed
test elapsed: 0.00s
tests: 17/17 files passed
test elapsed: 237.75s
```

The cold-clone reconciler findings are the pre-existing review items on `main` whose Git ranges
a history-less archive cannot resolve; the worktree run shows none. The six advisories
everywhere are the frozen older human-question records reported on every run. The records
commit that follows changes no tested byte.
