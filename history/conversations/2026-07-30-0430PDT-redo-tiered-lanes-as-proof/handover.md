# Handover — redo tiered lanes as proof

**Session:** 2026-07-30 04:30–12:10 PDT, local time, claude
**Task:** 2026-07-29-run-repository-tests-in-parallel, 2026-07-30-report-unrun-coverage-honestly, 2026-07-30-stop-background-git-maintenance, 2026-07-30-write-fixture-git-objects-in-process, 2026-07-30-flag-machine-specific-paths-in-link-check, 2026-07-25-fix-pull-request-admission-event-race
**Mode:** async
**Queue projection:** v1

## What happened

- The complete local suite went from 198.57s to **38.31s** measured against 124.77s
  serial in the same session, a 3.26x ratio that an independent profile reproduced at
  3.27x by a different method. Every one of the eleven files passes in every run.
- The tiered-lane experiment was rebuilt as its useful parts rather than taken whole. Its
  central rule turned out to convert eleven fail-closed selector branches into an empty
  selection: deleting a service source file would have passed the gate with no test run.
  An ADR records why that rule is unsound. Its reporting instinct survives.
- The two admission checks that were red on every freshly opened pull request are fixed
  and merged, and the first pull requests opened afterwards are green on both.
- A flaky CI failure was diagnosed to Git's detached auto-maintenance writing a lock file
  inside the directory the test then removes, and **reproduced live on CI during this
  session** on a branch that lacks the fix.
- Fixture history is now written as Git objects in process rather than by spawning add
  and commit, verified byte for byte against real Git.

## How it works now

`automation/run_tests.py` takes `--jobs`, shards below the file by test name, and prints
the same `tests: N/M files passed` line whether it ran everything or nothing. Child Git
processes read an isolated configuration that disables background maintenance, and that
configuration is actually reachable because `GIT_CONFIG_GLOBAL` names it rather than
`os.devnull`. The reconciler rejects a backticked absolute path instead of asking the
host filesystem whether it exists. None of this is merged yet: five stacked pull requests
carry it, and only the admission repair is on main.

## Decisions made for you

- The skip rule for a local gate is now evidence, not deferral: nothing is left out
  except where running it cannot change the outcome —
  `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`.
- Per-test result caching, the one approach that would stop cost scaling with suite size,
  is ruled out by measurement rather than by opinion; the evidence and what would revive
  it are in `docs/designs/fast-local-test-feedback.md`.

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- **Merging the tiered-lane branch, in any form.** Its rule was written against a selector
  that escalated for everything; after input-ownership selection landed it would have
  turned the symlink, index-race and removed-source guards into silence. Its own test for
  the rule now fails, because the escalation it avoided no longer happens.
- **Reporting improvements copied from that branch.** They were already delivered by the
  selector that merged. Only the destination of deferred coverage was missing, and that
  is one string.
- **Per-test result caching via audit hooks.** The API does not exist on the interpreter
  the suite runs on, metadata reads emit no event where it does exist, and the alternative
  capture mechanism costs 11.65x. Reviving it depends on an interpreter floor this
  repository has not set, and on closing the metadata-read gap.
- **Disabling background Git maintenance by writing the setting into the isolated HOME
  alone.** On Git 2.32 and newer `GIT_CONFIG_GLOBAL` replaces the global scope, so leaving
  it at `os.devnull` silently discards the setting on exactly the versions that have the
  bug.
- **Building the fixture writer without an index.** The reconciler queries `git ls-files
  --stage` and both diff plumbing commands, and the fixtures use real `git checkout`,
  `git merge` and `git rm` between in-process commits.
- **`git init --template=<empty>` as a substitute for copying a skeleton.** 1.15x against
  9.58x; the empty template shrinks what init writes and does nothing about the two config
  spawns that dominate.

## Next steps

None.

## Deep links

- Task folders: `tasks/1_in-progress/2026-07-29-run-repository-tests-in-parallel/` · `tasks/1_in-progress/2026-07-30-write-fixture-git-objects-in-process/` · `tasks/1_in-progress/2026-07-30-flag-machine-specific-paths-in-link-check/`
- Design: `docs/designs/fast-local-test-feedback.md` · Decision: `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`
- Commits: 9af1074..d4d23c5 on main; pull requests 24 through 29
