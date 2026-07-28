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

## 2026-07-27 — immutable-checkpoint-panel-repair (codex and delegated agents)

- A fresh panel reviewed immutable checkpoint `78a5ba2` and returned two P1 blockers, so the
  task remains in progress and the affected final-lane, provider-adapter, and verification plan
  steps have been reopened.
- The first blocker is an oracle-integrity flaw: candidate-controlled tests and helpers can be
  deleted or weakened, so trusted-base tests/support must become a non-erasable floor executed
  against exact candidate product bytes, with candidate test changes run only as supplemental
  evidence.
- The second blocker is a provider-event/history flaw: metadata-only pull-request events and
  non-fast-forward rewrites must never prepare, execute, publish, or replace the stable hard-gate
  success. One condition will restrict all three jobs to same-repository `task/**` pull requests
  opened once or synchronized by a verified fast-forward.
- Implemented an exact-base composite test plan. Base tests and directory-local support bytes
  form a non-erasable floor over exact candidate product bytes; candidate-added or changed tests
  run separately. The v2 receipt and report identity binds both lanes, the overlay, both views,
  policy, runner, and environment.
- Restricted prepare, credential-free execution, and App publication to one shared event/source
  contract: default-base, same-repository `task/**` pull requests on open or a strict verified
  fast-forward synchronize. All other pull-request events remain projection-only.
- Added exploit and event/history matrix regressions. The combined isolated run passed 49 gate,
  46 runner, and 16 workflow tests in 16.59 seconds; reconciliation, YAML parsing, compilation,
  and whitespace validation also passed. Exact staged final verification follows in the next
  evidence block.
- The exact composite run then blocked after 398.22 seconds because four immutable base
  assertions encode the provider behavior this security repair must replace. This proves the
  repair cannot be honestly admitted as one pull request; it needs a transitional-test pull
  request followed by the production/strict-test pull request targeted at that new base.
- Kept the original waiting activation decision immutable. Filed a separate future-boundary
  clarification requiring explicit acceptance of same-repository `task/**` protection and fork
  exclusion before activation; its safe unattended outcome remains manual verification.

## 2026-07-27 — manual-only replan stopping boundary (codex and delegated reviewers)

- A new security review blocked the current automatic design on two P1 findings. The base-pinned
  floor cannot prove that its same-interpreter assertions completed after candidate code calls
  `os._exit(0)`, and the publisher has no independent oracle that can distinguish that exit from
  controlled completion before posting a merge-authorizing status.
- Added test-only migration commit `499b0e2`: exact current triad or complete removal are the only
  accepted regimes. Follow-up reviews found and repaired job-name-only scanning, an unbound
  absent-runner read, contradictory absent-event expectations, and duplicate authority hidden
  inside an existing publisher job.
- A later adversarial canary found that `499b0e2` still does not prove complete authority removal:
  a renamed generic job can request `statuses: write`, use the default GitHub token, and call the
  statuses API without matching the current literal fragments. The migration floor therefore
  remains incomplete and needs a closed absence rule, not more ad hoc literals.
- A managed safety check then refused the requested hard-to-manual production edit because no
  human response yet authorizes that persistent security-policy change. All tentative production
  edits were reverted; the hard workflow and policy remain unchanged.
- Filed one plain yes/no clarification at the review boundary and two unclaimed core follow-ups:
  an external test oracle with staged migration, then an independently controlled OIDC-backed
  GitHub App publisher. No external service, credential, branch rule, or provider setting changed.
- The records-only commit attempt ran the normal routine hook and stopped safely after its
  required trusted-floor component exceeded the bounded interval. No commit was created and the
  hook was not bypassed.

## 2026-07-27 — manual-test-gate replan handover (codex)

- Two independent reviewers approved the test-only migration snapshot `21d5a24`; its change is
  intentionally limited to the migration floor and leaves production policy unchanged.
- Ran an exact staged final prewarm for the records-only package. Candidate
  `aa1815f2d5fbd81d63becdc08101cca9621bae1948b1ec9f53b593b642a68242` received receipt
  `4cc6c4a986628b2e3cc26c355bd7ac7cf2f19300b35c33a1c3a07b5e9a324951`: core scope took
  0.35 seconds, reconciliation 14.00 seconds, and the trusted floor 452.26 seconds; total
  time was 468.19 seconds.
- The final target of 300 seconds was exceeded, so the append-only final-budget evidence now
  records occurrence 6. The journal remains deliberately unstaged for a later records commit.
- Committed the records-only package as `13a60b8` (`harness: stop unsafe automatic test-gate
  activation`). Its normal hook reused the exact receipt and passed in 15.17 seconds; no push or
  merge occurred.

## 2026-07-27 — manual-only replan confirmation folded (codex)

- The owner's plain `yes` answer was transcribed without interpretation in commit `bed486c` and
  the waiting action was claimed for folding in commit `a789631`.
- Recorded the authorized manual-only decision in
  `memory/decisions/2026-07-27-manual-only-test-gate-replan.md` and superseded the earlier trusted
  pull-request gate decision. The starter must be manual, hard invocations must fail closed,
  complete results must remain cooperative, and automatic enforcement stays with the two ordered
  follow-up tasks.
- Updated the task acceptance criteria, design authorization, and remaining plan. This resolving
  checkpoint changes records only: no production policy, configuration, workflow, publisher, or
  runner behavior is claimed as implemented.
