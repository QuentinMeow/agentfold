# Worklog — stale-base pull-request admission

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-04 — claim for stack landing (codex planner)

- Claimed the task after pull request #79 reproduced the same stale event-base failure
  already recorded from pull request #65.
- Kept GitHub issue #78 as the external projection and resolved only the task-pickup
  request in this claim commit.
- Planned the repair as a separate task branch from the newly merged planning revision,
  before pull request #79 is allowed to land on `main`.

## 2026-08-04 — implementation (sol-high implementer)

- Reproduced the stale event-base shape in the existing local merge-ref fixture: event
  base `B`, checked-out candidate parents `B2,H`, with `B` an ancestor of `B2`.
- Kept `validate_range_candidate` unchanged. The pull-request workflow now binds checked-out
  `HEAD` by exactly two parents, event-head equality, and event-base ancestry, then passes
  `actual_parent1...event_head` to preserve PR-leg range semantics.
- Added literal-workflow-block tests for the direct-head and advanced-base paths; wrong
  second parent, non-merge, third parent, non-descendant base, and missing payload fields;
  absence of mutable-ref polling; and mutation proofs that the new admission and head guard
  are load-bearing.
- Chose no retry because `actions/checkout` has already pinned the immutable candidate and
  the preceding core-scope step has inspected that same tree. A later refetch would make
  the two gates judge different candidates.
- Did not investigate the separate displaced-tip finding described in `task.md`; this
  implementation changed no displaced-tip behavior.
- Verified the five focused fixtures, all 25 workflow-adapter tests, all 15 repository
  test files, the reconciler with zero blocking findings, and the staged core-scope receipt.
  Independent core-fit review, publishing, and merging remain for the parent session.

### Correction after first adversarial review

- The preceding statement that core scope had inspected the same tree was wrong. It ran in
  the candidate checkout, but `event_base...event_head` made its candidate-side content
  reads come from the stale event head. Two of three reviewers blocked revision `1da29e9`
  because an advanced base could add a protected-path registration that core scope missed.
- Moved candidate binding into its own step immediately after checkout. It now emits
  `actual_parent1...candidate` for core scope and `actual_parent1...event_head` for the
  reconciler, so both consumers share one bound checkout while retaining their distinct
  range semantics.
- The separate displaced-tip observation in `task.md` is already owned by task
  `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion` and projected
  to GitHub issue #75 by
  `message-queue/needs-agent/requests/non-blocking-track-github-issue-75-restack-provenance.md`;
  this task does not duplicate that repair.
- Re-ran the five focused fixtures, all 25 workflow-adapter tests, all 15 repository test
  files, core scope, the reconciler, and diff whitespace checks after the review repair;
  every command passed.
