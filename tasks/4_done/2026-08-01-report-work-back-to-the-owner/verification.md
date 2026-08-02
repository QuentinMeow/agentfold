# Verification — report work back to the owner

## Repository invariants and tests

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)

$ python3 automation/run_tests.py
tests: 12/12 files passed
```

## Line budgets

The root `AGENTS.md` is budgeted at 140 lines and a `SKILL.md` at 70; both new ritual steps
had to fit inside those.

```
$ wc -l AGENTS.md skills/session-handover/SKILL.md
     136 AGENTS.md
      54 skills/session-handover/SKILL.md
```

## The queue rewrite the repository refused

Nine live unanswered `needs-human/` items were drafted in the current readable shape, with
every machine field copied byte for byte. Staging them produced nine identical findings:

```
$ git add -A message-queue/ && python3 automation/reconcile/reconcile.py --check
[queue-resolution] message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md: live queue action was rewritten: action identity changed while the queue item remained live
    fix: preserve the action and response identity; file a distinct successor action when the requested work changes
...
reconcile: 9 blocking finding(s)
```

The rule is deliberate and is stated in `queue_mutation_problem`
(`automation/reconcile/reconcile.py`): *"There is no presentation carve-out. A live item's
visible text is its identity, so reformatting one is an identity change and is refused."*
The one exception, `human_projection_context_migration`, is legal only in the commit that
activated queue-resolution v1, which has already landed.

The refusal was correct. Several drafts replaced an abstract title with a concrete one,
which reads as an improvement and may equally be a different question; no check can tell
"clearer" from "different".

All nine edits were reverted. The drafts are kept at
`history/conversations/2026-08-01-2317PDT-make-agent-reports-readable/artifacts/proposed-queue-rewrites/`,
the choice of whether to withdraw and re-ask the originals is filed for the owner, and the
rule is recorded at `memory/lessons/message-queue/a-live-question-cannot-be-reworded.md`.

A tenth item was not drafted at all: `future-blocking-review-detector-failure-state.md`
already carries a committed human response, which makes it a record rather than an ask, and
`handbook/human-action-guide.md` forbids reformatting one.

## The handover projection

The "Needs your attention" section is generated from the live queue rather than written by
hand, and the reconciler checks it against the queue at the handover's creation commit. Two
findings shaped the final list:

- `non-blocking-rereview-human-action-files.md` is `awaiting-artifact`, which binds nothing
  to judge, so the liveness rule excludes it. Twelve entries remain, not thirteen.
- One "Dead ends" bullet was flagged as an action-like directive outside the projection
  sections. Rewriting it in the indicative cleared the finding — the same rule the
  pull-request scenario documents.

## Acceptance criteria

- [x] The root `AGENTS.md` end-of-session ritual requires publishing and reporting.
- [x] `skills/session-handover/SKILL.md` ends at the same place, as steps 8 and 9.
- [x] `handbook/git-workflow.md` states when a task stacks and when it branches from `main`.
- [~] The live `needs-human/` items were examined; nine rewrites were refused by the
      repository and the choice was filed for the owner rather than forced.
- [x] An ADR records the reporting decision.
- [x] `roadmap/current-state.md` and `README.md` reflect what now exists.
- [x] Reconciler reports 0 blocking findings; the suite passes 12/12.

## Not verified

Nothing checks that an agent actually publishes or actually reports — both new steps are
prose. The one honest mechanical proxy, "a task in review has a pushed branch", was
considered and rejected in `design.md`.
