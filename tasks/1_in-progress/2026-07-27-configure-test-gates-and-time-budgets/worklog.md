# Worklog — configurable test gates and time budgets

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-27 — file-configurable-test-budget-task (codex)

- Reviewed the current hook and full runner, the existing development-feedback task, recorded
  timing evidence, the configurable guard-mode decision, and the deterministic-filing lesson.
- Chose a budgeted routine lane plus configurable final lane, with explicit critical-scope
  exceptions, exact-evidence reuse, and automatic deduplicated investigation-task filing.
- Filed this focused child task and its pickup request. No implementation was started.

## 2026-07-27 — configurable-test-gates-coordination (codex)

- Audited the live GitHub stack and confirmed draft PR 16 is the only open prerequisite; the
  implementation branch must start from its head and target its task branch.
- Recorded the owner's Option A authorization through the human-action lifecycle, preserving
  the original dirty `main` checkout while publishing the validated coordination commits.
- Claimed the task for codex and removed its pickup request. Independent design review blocked
  the original underspecified contract; implementation starts only from the resolved contract
  covering whole-interval timing, explicit critical bindings, exact tested views, and
  nonblocking regression filing.

## 2026-07-27 — configurable-test-gates-implementation (codex)

- Implemented the versioned root policy, two test lanes, exact candidate and tested-view
  manifests, receipt reuse, bounded cleanup, timing reports, and deterministic regression-task
  filing on the task branch stacked above PR 16.
- Repaired two adversarial-review rounds and disposable-candidate failures, including frozen
  reconciliation, symlink and Git-metadata escape prevention, provider-hard environment and
  identity checks, portable append-only evidence, report-path safety, and semantic staged
  identity across Git's pre-commit index refresh.
- Verified 297 repository tests, Python 3.7 focused suites, live daemon cleanup, three routine
  scenarios under ten seconds, one critical full prewarm, exact unchanged reuse, and stale-byte
  rejection within 60 seconds. The durable details are in `verification.md`.
- Paused before staging because the candidate-controlled GitHub workflow cannot honestly claim
  hard enforcement. Filed the blocking decision on whether to authorize a split trusted
  preparer and credential-free candidate runner; no provider workflow was added without that
  approval.
- Preserved the exact pre-approval implementation and blocking records in checkpoint
  `f2d220b1ae9ddc0f47d54252c4804c356ee780c1`. Its complete staged prewarm passed in 218.94
  seconds, and the real commit hook reused that receipt and passed in 6.93 seconds.
- Folded the owner's Option A response into the trusted pull-request gate ADR. Work resumes with
  a base-controlled preparer and a separate credential-free candidate test job; the answered
  queue item is archived by Git history.

## 2026-07-27 — trusted-provider-boundary-repair (codex and delegated agents)

- A blocking review identified five independent gaps: cached evidence did not bind the complete
  child execution environment; a double-forked process could scrub its ownership marker and
  escape timeout cleanup; all test files shared one mutable projected view; `env -i` did not
  make the credential-free runner a real candidate-code isolation boundary; and a check
  published by the workflow token could not be required from a dedicated publisher identity.
- Repaired the three local gaps by binding the safe child-environment digest (including
  `PYTHONPATH`) into receipts, requiring Linux child-subreaper containment for provider-hard
  components while retaining an honest best-effort label locally, and materializing a fresh
  immutable-input view for every test file.
- Repaired the provider gaps with a digest-pinned, no-network, read-only one-shot Docker
  boundary; a root judge limited to KILL, SETGID, and SETUID; UID 65532 candidate children with
  zero active capabilities and per-file process cleanup; and a separate protected-environment
  publisher that posts the exact-candidate status through a statuses-only dedicated GitHub App.
- The final diff audit found and repaired a real-container capability mismatch before handoff:
  provider scratch no longer requires absent CAP_CHOWN, sealed views are restored only after
  candidate processes are reaped, and arbitrary `PYTHON*` names no longer cross the exact child
  environment allowlist.
- Final focused verification passed 14 workflow tests, 44 gate tests (3 platform skips), and 46
  runner tests in an isolated 3-file run lasting 10.64 seconds. The full reconciler regression
  had already passed 297 tests in 113.574 seconds; the final structural check reported zero
  findings. Docker was unavailable locally, so no live Linux-container execution is claimed.
- External activation remains a separate future boundary owned by
  `message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md`.
  Until its GitHub App, protected environment, diagnostic pull request, and branch-protection
  setup are completed and verified, the status is not described as enforced.

## 2026-07-27 — human-readable decision and exact hook reuse repair (codex)

- Rewrote the future GitHub activation request so the merge consequence and the manual
  alternative are understandable without provider terminology, while preserving every v1
  lifecycle field and the fail-safe manual default.
- Reproduced a real commit-hook cache miss after an exact final prewarm. A blocked diagnostic
  commit isolated the only difference: Git prepends its own internal executable directory to
  `PATH` for hooks, changing the bound child environment and causing a duplicate full run.
- Repaired both execution and identity through one shared canonical environment function. It
  removes only a verified Git-owned hook prefix whose executable path and repository index both
  match Git's configuration; attacker-supplied or mismatched prefixes and indexes stay bound.
- Added an actual `git commit` regression for ordinary repositories and verified the same reuse
  in this linked worktree. The focused gate suite passed 46 tests with three platform skips.
- Preserved the automatic timing investigation generated when a later exact gate took 309.58
  seconds and failed on a test-fixture assumption. The task, append-only timing evidence, and
  pickup request remain staged for the next checkpoint. Corrected the fixture to create its own
  temporary Git repository without changing production behavior.
