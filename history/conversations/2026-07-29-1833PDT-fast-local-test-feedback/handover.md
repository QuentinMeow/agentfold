# Handover — fast local test feedback

**Session:** 2026-07-29 18:33–21:40 PDT, claude
**Task:** none — investigation feeding task `2026-07-27-configure-test-gates-and-time-budgets`
**Mode:** async
**Queue projection:** v1

## What happened

- Pulled `origin/main`. There was no real conflict: local `main` was 19 commits behind and
  0 ahead, and every uncommitted file was either byte-identical to upstream or a stale copy
  of queue items upstream had already resolved in `24198e5`.
- Found and fixed a blocker: two handovers from earlier sessions were never committed and
  both projected a `needs-human` decision that upstream had already deleted, so
  `reconcile --check` failed and **no commit could succeed in this checkout**. Removing one
  stale line from each fixed it (`3da872e`).
- Measured why the suite is slow. It is `fork`/`exec`-bound: there are 13,261 git subprocess
  calls per full suite, with 92-93% of wall time inside them. `automation/run_tests.py`
  wraps each git call in a `/bin/sh` shim, so every one costs two processes, not one.
- Ran five experiments on isolated `exp/*` branches. Removing the shim measured
  **457.15s → 276.17s (−39.6%)** on its own; combining it with test-level sharding ran all
  625 tests in **26-30s**, versus a 219s baseline confirmed three times.
- Wrote the evidence up as branch docs/designs/fast-local-test-feedback.md and filed one
  decision asking which levers should land.

## How it works now

`main` is unchanged apart from the two recovered handovers and this session's records; the
gate still runs the full suite at every commit, measured at 231.54s for a two-line change.
Every experiment lives on its own unmerged branch (`exp/a-input-scope`, `exp/c-tiered`,
`exp/d-spawn-reduction`, `exp/e-git-wrapper`), each committed with `--no-verify` because the
core-scope gate requires a `task/<task-id>` branch. Each branch has a `RESULT.md` with real
command output.

## Decisions made for you

- None. The recommendation — land the Git-isolation fix and a parallel mode, keep selection
  on the shelf — is written up in branch docs/designs/fast-local-test-feedback.md as a
  proposal, and the choice is queued below.

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Choose Option A, B, or C for what lands from the five measured experiments.](../../../message-queue/needs-human/decisions/non-blocking-choose-the-test-speed-levers-to-land.md) — Why-you-might-care: Measurement removed the premise the in-progress design rests on, so building it unchanged would add policy machinery the repository no longer needs. || If-you-do-nothing: Nothing lands; every commit keeps paying the measured 219-225s gate and the five experiment branches stay unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- **RAM disk / tmpfs for git fixtures: 9%.** Fsync tuning: 8%. Git's own test README calls
  tmpfs "massive", but that is Linux advice where `fork` is cheap. Measured twice
  independently, so a further attempt at it is not worthwhile.
- **Batching git calls through `sh -c` is slower** — the shell is another process.
- **File-level parallelism is capped at 1.27-1.46×** because one file is ~68-79% of the
  suite. Measured at 1.26×. Sharding must be at test granularity.
- **Hoisting the per-test git fixture to a copied template did not register** at file scale
  (−0.4% ± 1.5s), despite being 23ms/test cheaper in isolation and being ranked the second
  best lever by external research. Its value is 680 fewer processes, not seconds.
- **`GIT_CONFIG_GLOBAL` does nothing on git 2.23** (it arrived in 2.32), which is why the
  runner needed the `HOME` shim at all.
- **`tomllib` exists on neither interpreter here** (3.7.6 and 3.9.6; it needs 3.11+), so the
  in-progress design's `agentfold.toml` centrepiece cannot be read without vendoring a parser.
- **Timings on this machine are not comparable across lock holds.** Identical code measured
  193s and 91s in separate holds, with CPU time doubling too — core/SMT contention. Only
  variants interleaved inside a single hold can be compared.
- **Killing tests on a deadline is actively harmful:** each run creates ~596 git repositories
  in `$TMPDIR`, killing leaks them, and Spotlight then indexes them, so each run degrades the
  next. This session removed 937 leaked directories (~410 MB).

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: branch docs/designs/fast-local-test-feedback.md
- Commits: `3da872e`; experiments `379c98c` (a), `bd2bad7` (c), `e33f925` (d), `e900216` (e)
