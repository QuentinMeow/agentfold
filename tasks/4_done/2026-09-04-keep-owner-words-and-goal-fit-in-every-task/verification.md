# Verification — Keep the owner's words and a goal fit in every task

**Verified:** 2026-09-04 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Environment: the task worktree
`.git/agents/worktrees/task-2026-09-04-keep-owner-words-and-goal-fit-in-every-task` on branch
`task/2026-09-04-keep-owner-words-and-goal-fit-in-every-task` at c42fbd6, no private overlay,
macOS host, Python 3.14, one local process at a time unless the pre-commit hook chose otherwise.

## Observed green then red per check id (writer worktree, before landing; fixtures from the test module)

```
$ PYTHONDONTWRITEBYTECODE=1 python3 <scratch>/observed_red.py
valid: task-provenance -> no finding
damaged (requirements.md deleted): task-provenance -> ['[task-provenance] tasks/1_in-progress/2026-09-10-example: missing requirements.md']
damaged (criterion unlabelled): task-provenance -> ['[task-provenance] tasks/1_in-progress/2026-09-10-example/task.md: acceptance criterion lacks a provenance label: WHEN asked, THE SYSTEM SHALL make it.']
damaged (Fit: conflicts, no queue item): task-provenance -> ['[task-provenance] tasks/1_in-progress/2026-09-10-example/task.md: **Fit:** conflicts without a needs-human clarification or decision in **Queue actions:**']
valid: task-provenance-advice -> no finding
damaged (all criteria derived): task-provenance-advice -> ['[task-provenance-advice] tasks/1_in-progress/2026-09-10-example/task.md: every acceptance criterion is `[derived]` while the task serves G1']
grandfathered (2026-07-23 task, no files, in-progress): task-provenance -> no finding
grandfathered (2026-07-23 task, no files, in-progress): task-provenance-advice -> ['[task-provenance-advice] tasks/1_in-progress/2026-07-23-example: filed before the provenance grammar and has no requirements.md', '[task-provenance-advice] tasks/1_in-progress/2026-07-23-example/task.md: filed before the provenance grammar and has no `## Fit` section']
grandfathered (2026-07-23 task, no files, done): task-provenance-advice -> no finding
valid: roadmap-goals -> no finding
damaged (Confirmed: yes): roadmap-goals -> ["[roadmap-goals] roadmap/desired-state.md: G4 has an unreadable **Confirmed:** value 'yes'"]
valid (TODAY 2026-09-20): roadmap-goals-advice -> no finding
damaged (TODAY 2026-10-15, G2 asked 2026-09-01): roadmap-goals-advice -> ["[roadmap-goals-advice] roadmap/desired-state.md: G2 has been agent-proposed for 44 days without the owner's confirmation"]
```

## Focused tests at the tip

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest automation.tests.test_reconcile_provenance
----------------------------------------------------------------------
Ran 25 tests in 0.107s

OK
```

## Commit gate on the reconciler commit (pre-commit hook, staged lane at its default parallelism)

```
pre-commit: core scope
core-scope: pass
pre-commit: reconciler
reconcile: 0 blocking finding(s)
pre-commit: staged-path repository tests
test workers: 15
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_provenance.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_run_tests.py
tests: 5/5 files passed
test elapsed: 48.13s
pre-commit: OK
```

The first attempt at that commit was refused by the same hook because one selection expectation
in `automation/tests/test_run_tests.py` still lacked the new test file; the expectation was
corrected and the hook rerun. The runner lists the new file (`test_reconcile_provenance.py`) in
its own output, so it is collected, not merely present on disk.

## Full repository suite, serial, at c42fbd6

```
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
PASS automation/tests/test_second.py
tests: 2/2 files passed
test elapsed: 0.00s
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_probe.py
..................................................
----------------------------------------------------------------------
Ran 67 tests in 2.354s

OK (skipped=1)
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
.....
----------------------------------------------------------------------
Ran 5 tests in 0.058s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.124s

OK
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
test elapsed: 227.43s

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-09-04-keep-owner-words-and-goal-fit-in-every-task --range 7e1a251734f751a29a1f3ab8e267bb53a3588e35...c42fbd6f5fc1624a83ea24d81ac7b8232e082197
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
```

Before the closer's adjustment commit the plain check reported 31 advisories (the 6 pre-existing
`explanation-shape` records, 8 `roadmap-goals-advice` on the July goals, 17 `task-provenance-advice`
on in-review tasks); after it, 6.

## Cold clone (fresh archive of the tip, single commit, no history)

```
$ git archive HEAD | tar -x -C <scratch>/coldclone-prov && cd <scratch>/coldclone-prov && git init -q && git add -A && git commit -qm coldclone
$ python3 automation/install.py
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md: **Review revision:** is not a reviewable Git artifact: d87b755e6259101bf76b0a2783b35dfb3f163fb0 is unavailable; 8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b is unavailable
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md: **Review revision:** is not a reviewable Git artifact: 25d03257b5ee61753fa9bada609722c4e84a8064 is unavailable; fd2374d99796300ed4325c2961e696092c17875e is unavailable
reconcile: 2 blocking finding(s), 6 advisory (not blocking)
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
tests: 17/17 files passed
test elapsed: 227.90s
```

The two cold-clone findings are pre-existing review items on `main` whose Git ranges name commits
that a history-less archive does not contain; they are not produced by this change and do not
appear in the real worktree. The suite, the installer, and every new check behave the same in
the cold clone as in the worktree.

## Fresh-context panel on the diff 7e1a251..c42fbd6 (three lenses, findings p2-* in the orchestration run)

- correctness: `block` — three verified defects: a `[user <date>]` criterion produced no finding when `requirements.md` held only the no-owner-words line; `fit_findings` judged an untouched template `## Fit` section (nested placeholders unrecognised) in backlog, records-only, and pre-activation tasks; an absolute clarification path raised inside `check_roadmap_goals_advice` (exit 2). Fixed in cbdde8a: labels resolve against any well-formed file, a placeholder-aware fit is judged only where a fit is due, and the path is checked before it is read; four tests added (29 in the module).
- requirements match: `block` — the 2026-08-03 task's chat entry dropped the owner's opening clause and paragraph breaks, and G9's quote spliced a chat sentence and a document sentence; also noted: a paraphrase in this task's owner-words file, and a derived mechanisation under a `[user]` label. Fixed in cbdde8a: both entries and G10 now quote one complete owner message each, the paraphrase moved to `design.md`, and the criteria separate the owner's four asks from the agent's mechanisation. Copy-and-fill of the three templates, the clarification's nine authoring checks (748 of 800 words), the G1–G8 provenance claims against `git blame`, and the core-fit gate all passed.
- blast radius: `approve` — could not break it: no existing check reads the new keys, the ask scanner treats the fenced words and comments as data, `task-admission` replays only `task-structure` by design, generated files regenerate byte-identically, budgets hold (root 84 of 140, tasks 60 of 60), retry filing handles the new ids. Its documentation-drift notes (claim recipe, file lists, roadmap line references, adoption guide) are fixed in cbdde8a.

Panel result after the remedies: 1 approve, 2 blocks resolved by a later commit. The cross-vendor refuter: DID NOT RUN (no read-only Codex permission granted in this session).


## Final tip cbdde8a: the panel's fixes, re-verified

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest automation.tests.test_reconcile_provenance
Ran 29 tests in 0.130s

OK

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
tests: 1/1 files passed
test elapsed: 0.06s
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
test elapsed: 197.00s

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)

$ PYTHONDONTWRITEBYTECODE=1 python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-09-04-keep-owner-words-and-goal-fit-in-every-task --range 7e1a251734f751a29a1f3ab8e267bb53a3588e35...cbdde8a383e18b5d817be9561f0003087e8c7917
reconcile: 0 blocking finding(s), 6 advisory (not blocking)

$ python3 automation/check_core_scope.py --range 7e1a251734f751a29a1f3ab8e267bb53a3588e35...cbdde8a383e18b5d817be9561f0003087e8c7917 --branch task/2026-09-04-keep-owner-words-and-goal-fit-in-every-task
core-scope exit=0
```

Cold clone of cbdde8a (fresh archive, single commit, no history):

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
test elapsed: 0.06s
tests: 2/2 files passed
test elapsed: 0.00s
tests: 1/1 files passed
test elapsed: 0.00s
tests: 17/17 files passed
test elapsed: 197.61s
```

The cold-clone reconciler findings, when present, are the two pre-existing review items whose
Git ranges a history-less archive cannot resolve; the worktree run above shows none.
