# Verification — Stop a human answer from holding any Git edge

**Verified:** 2026-08-01 by claude

Only commands actually run and their real output. Long output is trimmed, and every
trim is marked `[… N lines elided …]` on its own line; nothing else is edited.

Two disclosures up front, because both change how this file should be read.

**The lifecycle rehearsal in §5 ran in a throwaway `git clone`, never in this
repository.** It needs an owner's answer to exist, and inventing one here would put
fabricated human text into the repository permanently. The clone is at
`…/scratchpad/rehearsal`, the invented answer is spelled
`REHEARSAL INPUT, NOT A REAL ANSWER — looks right, keep it` so it can never be mistaken
for the owner's words, and none of it was pushed or merged. In this repository both
stranded reviews are still `**Your review:** ______`, proven in §6.

**`--at-transition merge` with no scope still reports one finding, and it is an agent
item.** §3 gives the full output and §8 explains why it is not this task's to clear.

Unless stated otherwise, `git` below is the system git, 2.50.1; the one on `PATH` here is
2.23.0 and lacks flags several of these commands need.

## The deadlock, reproduced on `main` before any change

```
$ git rev-parse origin/main
0e63bbe69981c55a5436b27dfcc1976ccb763920

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
EXIT=0

$ python3 automation/reconcile/reconcile.py --check --at-transition merge
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 4 blocking finding(s)
EXIT=1
```

A tree that passes every check cannot be merged, on four questions.

## Acceptance test 1 — plain `--check`

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
EXIT_1=0
```

## Acceptance test 2 — the full suite

```
$ python3 automation/run_tests.py
[… 3 lines elided: the probe pre-flight …]
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
test elapsed: 52.84s
```

`test_reconcile_queue.py` went from 400 tests to 424: ten that pinned the retired merge
receipt were rewritten into the same assertion about the surviving rule, and fourteen are
new.

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 424 tests in 83.753s
OK
```

## Acceptance test 3 — the merge boundary

Every human item is gone from this output. One agent item remains.

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 1 blocking finding(s)
EXIT_2=1
```

That bare invocation is the all-scopes pessimistic run. The one CI actually runs is
scoped, and it is clean for this branch:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-08-01-stop-human-answers-from-gating-git-edges \
    --range 0e63bbe69981c55a5436b27dfcc1976ccb763920...0747f5480b76c552a112a9aec1cfda1a89e0012b
reconcile: 0 blocking finding(s)
PR-shaped exit=0
```

Scoped to the task the surviving agent boundary actually names, it fires — which is the
whole point of it:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-23-first-class-message-queue \
    --range 0e63bbe69981c55a5436b27dfcc1976ccb763920...0747f5480b76c552a112a9aec1cfda1a89e0012b
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
reconcile: 1 blocking finding(s)
exit=1
```

## The migration edge, re-validated PR-shaped

The one commit that carries the schema activation and all four renames:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-08-01-stop-human-answers-from-gating-git-edges \
    --range 0e63bbe69981c55a5436b27dfcc1976ccb763920...4d2f8aaae95528f1dedb6ed2d3e386756272feaa
reconcile: 0 blocking finding(s)
EXIT=0
```

## Acceptance test 4 — the whole lifecycle of a stranded review

Run in `git clone --no-hardlinks` at `…/scratchpad/rehearsal`, at branch head `0747f54`.
See the disclosure at the top of this file: the answer in step 2 is invented, labelled as
such, and never entered this repository.

```
$ bash …/scratchpad/rehearse.sh
########## STEP 0 — the base this rehearsal starts from
0747f54 reconcile: make a folded human review land somewhere durable

########## STEP 1 — the task reaches 4_done while its human question is live and unanswered
3:**Status:** waiting
11:**Review outcome:** pending
45:**Your review:** ______
reconcile: 0 blocking finding(s)
check exit=0
8:**Queue actions:** `message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md`
reconcile: 0 blocking finding(s)
merge-boundary exit=0

########## STEP 2 — the owner answers late, in ONE edit, while the item is still waiting
 .../non-blocking-review-test-runner-git-environment-isolation.md    | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)
reconcile: 0 blocking finding(s)
check exit=0

########## STEP 3 — the one-line waiting -> folding claim
 .../non-blocking-review-test-runner-git-environment-isolation.md        | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
reconcile: 0 blocking finding(s)
check exit=0

########## STEP 4a — delete it with UNCHANGED evidence (must refuse)
[queue-resolution] message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md: deleted unresolved queue item: resolution evidence was not created or changed in the deletion commit: `roadmap/current-state.md`
    fix: commit the required claim/response evidence before deleting it
[task-structure] tasks/4_done/2026-07-24-isolate-test-git-environment/task.md: Queue actions path `message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md` is not in the Git index
    fix: stage the queue item or remove the stale task reference
[task-structure] tasks/4_done/2026-07-24-isolate-test-git-environment/task.md: done task lists a **Queue actions:** path that is not a live queue item
    fix: drop the resolved path, or restore the item it names
reconcile: 3 blocking finding(s)
check exit=1

########## STEP 4b — delete it with CHANGED evidence, and drop the task-local restatement
reconcile: 0 blocking finding(s)
check exit=0

########## STEP 5 — both gates, at the end of the whole lifecycle
reconcile: 0 blocking finding(s)
plain --check exit=0
reconcile: 0 blocking finding(s)
PR-shaped merge-boundary exit=0

base=0747f5480b76c552a112a9aec1cfda1a89e0012b
head=53b339fcf58cd95bb63e0bf043b40ea36b1f6f11
```

Step 1 is the state that was previously impossible: a task in `4_done`, listing a live
and unanswered human review, passing both gates. Before this change that exact tree
produced `done task must declare **Queue actions:** none`.

Step 4a found something worth keeping. The first rehearsal of this, run before commit
`0747f54`, deleted the review with *nothing* outside the queue changing and reported
`0 blocking finding(s)` — a `non-blocking-` human review could be answered and folded into
thin air, because only the boundary-bearing branches of `queue_deletion_problem` enforced
the changed-evidence rule the contract has always stated. `0747f54` closes that, and the
output above is the re-run.

## Acceptance test 5 — the negative tests

Four probes, each identical to a valid item except for one boundary line, run against a
clone of `main` @ `0e63bbe` and a clone of this branch @ `0747f54`. The
`queue-task-reciprocity` finding appears in every probe on both sides — the probe item is
not linked from any task record — so it is the constant, and the difference between the
two runs is the change.

```
$ python3 …/scratchpad/negatives.py …/neg-before      # main @ 0e63bbe
########## revision under test
0e63bbe Merge pull request #56 from QuentinMeow/task/2026-07-31-redesign-human-action-files
a task that has already started: 2026-07-25-single-source-queue-prefix-rule
a task still in backlog:         2026-07-22-agent-adapter-ritual-hooks

===== N0  CONTROL — a start gate on an unstarted 0_backlog task (must pass) =====
[queue-task-reciprocity] …/future-blocking-probe-control.md: task:2026-07-22-agent-adapter-ritual-hooks does not link this live queue action
reconcile: 1 blocking finding(s)

===== N1  a human review that binds transition:merge =====
[queue-task-reciprocity] …/future-blocking-probe-merge-gate.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
reconcile: 1 blocking finding(s)

===== N2  a human start gate on a task that has already started =====
[queue-task-reciprocity] …/future-blocking-probe-start-gate.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
reconcile: 1 blocking finding(s)

===== N3  a human item that stops a whole task with Blocks now =====
[queue-task-reciprocity] …/blocking-probe-stop-a-task.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
[queue-task-reciprocity] …/blocking-probe-stop-a-task.md: blocking task:2026-07-25-single-source-queue-prefix-rule may remain in 1_in-progress only during a committed active repair/folding claim: status is not folding
reconcile: 2 blocking finding(s)

===== N4  an agent item that binds transition:merge (must STILL gate the merge) =====
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
reconcile: 2 blocking finding(s)
```

N1, N2 and N3 pass unchallenged before the change: a human merge gate, a start gate on a
task that started days ago, and a human item that stops a whole task are all spellable.

```
$ python3 …/scratchpad/negatives.py …/neg-after       # this branch @ 0747f54
########## revision under test
0747f54 reconcile: make a folded human review land somewhere durable
a task that has already started: 2026-07-25-single-source-queue-prefix-rule
a task still in backlog:         2026-07-22-agent-adapter-ritual-hooks

===== N0  CONTROL — a start gate on an unstarted 0_backlog task (must pass) =====
[queue-task-reciprocity] …/future-blocking-probe-control.md: task:2026-07-22-agent-adapter-ritual-hooks does not link this live queue action
reconcile: 1 blocking finding(s)

===== N1  a human review that binds transition:merge =====
[queue-schema] …/future-blocking-probe-merge-gate.md: human action may not bind transition:merge; merging, reviewing, and completing are revertible Git edges
[queue-task-reciprocity] …/future-blocking-probe-merge-gate.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
reconcile: 2 blocking finding(s)

===== N2  a human start gate on a task that has already started =====
[queue-schema] …/future-blocking-probe-start-gate.md: transition:start names task:2026-07-25-single-source-queue-prefix-rule in 1_in-progress; a start gate binds an unstarted 0_backlog task
[queue-task-reciprocity] …/future-blocking-probe-start-gate.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
reconcile: 2 blocking finding(s)

===== N3  a human item that stops a whole task with Blocks now =====
[queue-schema] …/blocking-probe-stop-a-task.md: human action may not stop a whole task with **Blocks now:** task:<id>; no human answer justifies 2_blocked
[queue-task-reciprocity] …/blocking-probe-stop-a-task.md: task:2026-07-25-single-source-queue-prefix-rule does not link this live queue action
[queue-task-reciprocity] …/blocking-probe-stop-a-task.md: blocking task:2026-07-25-single-source-queue-prefix-rule may remain in 1_in-progress only during a committed active repair/folding claim: status is not folding
reconcile: 3 blocking finding(s)
```

N0 is byte-identical on both sides: the one surviving human gate is untouched. N4 is
identical on both sides: an agent boundary still gates its own task's merge exactly as
before.

A lapsed `Answer by` is advisory and never blocks, so a clean tree cannot start failing on
a date:

```
$ python3 automation/reconcile/reconcile.py --check --fail-on-advisory
reconcile: 0 blocking finding(s)
EXIT_3=0
```

(Exit 0 because no live item has lapsed yet — the earliest `Answer by` is 2026-10-21.
The lapse path itself is pinned by `test_a_lapsed_answer_by_is_advisory_and_never_blocks`,
which asserts the finding is produced, that `finding.advisory` is true, and that
`finding.severity` is `advisory`.)

## Every committed human answer, byte-identical

For each live `needs-human/` item at `main` @ `0e63bbe`, the exact bytes of its response
block — the answer line plus the immutable review binding — hashed at the base and at
this branch's head, following the four renames.

```
$ python3 …/scratchpad/answer_blobs.py 0747f5480b76c552a112a9aec1cfda1a89e0012b
base = 0e63bbe69981c55a5436b27dfcc1976ccb763920
head = 0747f5480b76c552a112a9aec1cfda1a89e0012b

OK   future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md
       response sha256 base=4fc08f976f2dd620  head=4fc08f976f2dd620
       file blob        base=5aa39e54c53c5d26  head=424001dcb18685c7
OK   non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md
       response sha256 base=4fc08f976f2dd620  head=4fc08f976f2dd620
       file blob        base=12cde4590f0a92e6  head=32b89d2fc0d61b3f
OK   future-blocking-rereview-human-action-files.md
       response sha256 base=b15b85311ab380d4  head=b15b85311ab380d4
       file blob        base=0fa85c78c9547bb1  head=011334a5a0190a48
OK   future-blocking-review-detector-failure-state.md
       response sha256 base=2f136f1e540433fc  head=2f136f1e540433fc   <-- carries a committed answer
       file blob        base=0392d6ed28206b91  head=e655ed23c3d75a88
OK   future-blocking-review-guardrail-authority-boundary.md
       response sha256 base=1476dca05f35b46e  head=1476dca05f35b46e
       file blob        base=ddff37f1aa26bbd0  head=10f65acccd233577
OK   future-blocking-review-layered-development-workspace.md
       response sha256 base=d9ff39a808924622  head=d9ff39a808924622
       file blob        base=19fe289c8a9b9c62  head=e84a17fbb6a75bc3
OK   future-blocking-review-revised-assurance-profile-scope-and-egress.md
       response sha256 base=1476dca05f35b46e  head=1476dca05f35b46e
       file blob        base=a3bc506338762e39  head=41b51e84b7736159
OK   future-blocking-review-sensitive-data-recovery.md
       response sha256 base=1476dca05f35b46e  head=1476dca05f35b46e
       file blob        base=6b1a52f5cc1d0075  head=309be961b52478a7
OK   future-blocking-review-test-runner-git-environment-isolation.md
       response sha256 base=11402aae38352513  head=11402aae38352513
       file blob        base=dc4154cf4a852ffc  head=7a0bb52ed489e6eb
OK   non-blocking-review-template-first-explanation.md
       response sha256 base=1476dca05f35b46e  head=1476dca05f35b46e
       file blob        base=aaccc7a9820846dd  head=a7ae937930f71257

response blocks that changed: 0
```

Ten of ten unchanged. The file blobs all differ because every item gained an `Answer by:`
line and four were also renamed — which is precisely why the response block is hashed
separately rather than the file. The one item carrying the owner's committed answer
(`…detector-failure-state.md`, `**Your review:** partially reviewed, mostly correct,
continue`) hashes identically at both revisions. `4fc08f97…` and `1476dca0…` recur because
several items share the same unanswered response block byte-for-byte.

Both stranded reviews are still unanswered — made answerable, not answered:

```
$ grep -n 'Your review' message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md
45:**Your review:** ______

$ grep -n 'Your review' message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md
46:**Your review:** ______
```

## A fresh question filed, merged, and left open

`message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md`
was created on this branch and is live and unanswered. It appears nowhere in the
merge-boundary output in §3 — the forward path works, not just the migration.

## Contract line budgets

The budget is 60 and both files were at 60/60 before this task.

```
$ wc -l message-queue/AGENTS.md tasks/AGENTS.md
      60 message-queue/AGENTS.md
      59 tasks/AGENTS.md
```

`message-queue/AGENTS.md` fits because commit `752ddef` cut its `## Standard endpoints`
table, which restated the five leaf `README.md` files.

## Every stage independently green

Each commit below was made through the pre-commit hook, which runs `check_core_scope`,
`reconcile --check`, and the staged-path tests. No `--no-verify` was used anywhere.

```
$ git log --oneline 0e63bbe..HEAD
c5e5601 harness: file the two pieces this model needs but does not build
0747f54 reconcile: make a folded human review land somewhere durable
c3887a3 harness: ask the owner to turn on the merge gate this repo already runs
09ad486 harness: record that nothing a human owes holds a Git edge
1c40c3f reconcile: make a human merge gate unspellable, and give every ask a date
4d2f8aa harness: activate human gating v1 and free four crossed boundaries
8e908b1 reconcile: read a task's Filed provenance however it is phrased
540361d reconcile: let the gating migration correct the sentence it makes false
752ddef harness: stop restating the five queue leaves in the queue contract
33afca3 harness: give every live human action an answer-by date
2472259 reconcile: widen the rules the human-gating model needs
5af0b37 harness: claim stopping a human answer from holding a Git edge
ffc7cfe harness: file stopping a human answer from holding a Git edge
```

The two orderings that are load-bearing held: `33afca3` (the `Answer by` backfill) lands
before `1c40c3f` (the grammar), and `4d2f8aa` (the migration) is exactly one commit,
because `queue_gating_migration` recognises the weakening only in the commit that adds
the schema marker.

## Core-scope gate

```
$ python3 automation/check_core_scope.py
core-scope: pass (2 core path(s), task 2026-08-01-stop-human-answers-from-gating-git-edges; independent review manual; not invoked)
EXIT=0
```

## What is not verified here

- **Branch protection is not enabled and cannot be.** The `main-projection` ruleset is
  `enforcement: disabled` with no required check, read directly from the provider:
  `gh api repos/:owner/:repo/rulesets/19582703` → `"enforcement": "disabled"`, rules
  `deletion` and `non_fast_forward` only. Every gate this task repairs is therefore
  advisory until the owner answers the decision item filed for it. That is the single
  largest unverified thing here, and no commit can change it.
- **The `--file-retries` path** for the advisory-retry change (`retry_timing`) is covered
  by three unit tests but was not exercised end to end by running `--file-retries` against
  a real advisory finding on this repository.
- **Independent core-fit review** was not invoked; `check_core_scope.py` reports the
  deterministic boundary only.

## Review verdicts (when a review was explicitly run)

None. No independent reviewer was invoked for this task.
