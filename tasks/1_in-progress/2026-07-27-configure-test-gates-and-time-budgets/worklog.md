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
  message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md.
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

## 2026-07-28 — staged cleanup-bridge evidence (codex)

- The earlier test-only approval is no longer sufficient. The staged cleanup bridge comes before
  the full manual-v3 production pivot and makes no ADR change: it only admits the cleanup-fixed
  hard-v2 snapshot and the manual-v3 snapshot, rejecting the original hard state and every other
  unlisted state.
- The first pre-repair exact `final --explicit --staged` candidate `53213fc…` failed after
  483.20 seconds:
  core scope passed in 0.36 seconds, reconciliation passed in 11.70 seconds, and the trusted
  floor failed after 469.53 seconds at
  `TestGateTests.test_maximum_terminates_the_whole_component_process_group` when `os.killpg`
  raised `EPERM`. Fourteen of 15 files passed; no receipt or commit was created.
- One deliberately bounded byte-identical pre-repair retry failed: the retained machine report
  records 499.307663 seconds (about 499.31 seconds), while the timing journal records
  499.207190 seconds (about 499.21 seconds). Core scope passed in 0.35 seconds, reconciliation
  passed in 12.35 seconds, and the trusted floor failed after 484.97 seconds at the different test
  `TestGateTests.test_index_drift_during_selected_test_timeout_blocks`, again on `EPERM` from
  `os.killpg`. Fourteen of 15 files passed. No third retry was run.
- This is a real legacy Darwin/macOS cleanup-portability defect, not a changed-test regression.
  The staged bridge repairs that path in focused checks by tolerating `PermissionError` only
  when signalling the process group or owned descendants; direct-child `PermissionError` and
  unrelated `OSError` remain fail-closed. Existing real tests were not changed. No exact
  post-repair final gate has run, so that gate remains unverified rather than proven blocked.
- Focused evidence passed: deterministic checks 4/4; real timeout checks 2/2; classifier checks
  5 direct and 5 package; configuration checks 28 direct and 28 package; selected gate checks;
  reconciliation with zero findings; compilation and diff checks. The actual composite plan has
  15 base-floor tests and only 3 supplemental tests.
- Two independent revision-bound reviews of implementation diff `4ab89f5c…`, one on cleanup
  semantics and one on migration/provider boundaries, both approved. The reviewed implementation
  scope was four files. They rejected 14 crossed states, the original hard state, 8 unknown
  states, and 8 one-byte mutations, with no authority, configuration, workflow, or
  `run_tests.py` drift. The current staged revision adds only `plan.md`, `worklog.md`, and
  `verification.md` to those four implementation files, for seven staged files total.

## 2026-07-28 — authorized manual-only production pivot (codex and delegated implementation)

- Replaced the hard workflow byte-for-byte with the base-pinned manual fixture. The retained
  `pull_request_target` jobs project durable actions, while a credential-free `pull_request` job
  runs cooperative complete-test diagnostics. The workflow has no hard-gate triad, publisher
  environment, GitHub App credential, status-writing permission, or direct status API call.
- Changed the starter policy to `mode = "manual"` with no trigger while retaining validation of
  the reserved `hard` plus `pull-request` syntax. Every named transition and every
  `--provider-hard` request now returns `blocked-incomplete` before candidate discovery or
  execution and before receipt access.
- Bumped reports to v2 and receipts to v3. Both bind
  `evidence_authority: cooperative-same-interpreter`, `controlled_completion: false`, and
  `enforcement_eligible: false`; reports also say `enforcement: not-enforced`. Old or incomplete
  receipts cannot be reused.
- Added the adversarial `os._exit(0)` canary. It demonstrates that the cooperative runner can
  return zero before a later completion marker, paired with a gate regression proving that an
  automatic transition never starts that candidate-controlled interpreter.
- The first combined focused run exposed a pre-existing macOS cleanup edge where process-group
  signaling can return `PermissionError` even though the individual process remains killable.
  Cleanup now treats that group-level result like an unavailable group and continues with the
  individual process signal; the focused gate suite then passed.
- Focused configuration, gate, runner, workflow, and queue regressions passed, as did structural
  reconciliation, compilation, YAML parsing, exact workflow comparison, and the closed publisher-
  authority search. The full suite was deliberately not run at this implementation checkpoint;
  plan step 12 remains open for independent review and complete verification.
- The required normal commit attempt ran the routine hook once and stopped safely after 60.19
  seconds: core scope and reconciliation passed, but the base-pinned floor exhausted the routine
  interval after 42.44 seconds. The commit was not created, the hook was not bypassed or rerun,
  and the staged implementation remains ready for an exact final prewarm at the next boundary.

## 2026-07-28 — manual-boundary documentation repair (codex)

- A provider review found a P2 documentation error: the staged handbook and automation contract
  still described a configured final adapter and a live hard admission boundary after the
  authorized manual-only pivot.
- Repaired the active documentation and plan. Final evidence is explicit-only; `hard` and its
  pull-request trigger are retained only as future-compatible policy syntax; named transitions
  and `--provider-hard` fail closed before candidate execution. The base-pinned floor now says it
  checks cooperatively and cannot admit or reject a protected transition.
- Focused configuration/workflow tests, reconciliation, whitespace checks, and targeted wording
  assertions passed. No full suite, commit, push, queue record, or immutable history was changed.

## 2026-07-28 — manual-boundary line-budget repair (codex)

- The first post-repair reconciler run reported one finding: `automation/AGENTS.md` had grown to
  61 lines, exceeding its 60-line budget. The prior documentation repair remains intact.
- Compressed the manual-boundary rule to 60 lines without restoring any configured-adapter or
  live-hard-boundary claim. The staged rerun is recorded below with the repaired zero-finding
  result.

## 2026-07-28 — portable cleanup snapshot repair (codex)

- Replaced non-`/proc` serial process discovery with one bounded `ps eww` snapshot that supplies
  both descendant ancestry and exact same-UID ownership-token matching. Linux `/proc` discovery
  remains unchanged.
- Cleanup now caps its first snapshot at 300 ms and keeps 100 ms before the cleanup deadline;
  it grants at most 50 ms for `SIGTERM`, kills the initial owned set before any rescan, and keeps
  a final 50 ms for unconditional `SIGKILL` and reaping. Permission-error handling remains
  bounded.
- Added deterministic portable-snapshot, exclusion, timing-reserve, initial-kill, and Linux-path
  tests. The first focused run exposed only a test simulation mistake: the host lacked `/proc`
  despite a mocked Linux platform. The test now mocks the Linux `/proc` branch explicitly.
- Focused tests, three sequential real cleanup-fixture repetitions with their built-in residue
  checks, direct gate tests, configuration/runner/workflow regressions, compilation, and
  reconciliation passed. No full repository suite, commit, push, stash, or ref change occurred.
- Ran the package-form gate suite sequentially after the direct run: 63 tests passed with one
  platform skip in 17.106 seconds. Its expected argument-validation diagnostics and a pre-existing
  subprocess `ResourceWarning` appeared on stderr; neither is a test failure. The staged records
  continue to claim no exact-final gate or full repository suite.

## 2026-07-28 — cleanup bootstrap completion and phase-2 reapplication (codex)

- The cleanup bridge was subsequently verified and committed as `c78a8d6`. Its exact candidate
  `2c7bcc1366ea9611976de5989d3e3fcc079a9870ecb6072a7d9e1b6c1d7e0af6` passed the final gate in
  525.67 seconds: core scope 0.44 seconds, reconciliation 14.76 seconds, base-pinned floor
  484.83 seconds, supplemental tests 23.91 seconds, and 16 selected / 0 deferred / 0 incomplete.
  The commit hook then reused that exact full evidence and passed in 16.63 seconds.
- Reapplied the staged manual-v3 production pivot onto `c78a8d6`, retaining the cleanup
  `PermissionError` behavior and its deterministic `EPERM` regressions. The completed bridge-only
  migration classifier was removed so production assertions now require manual-v3 behavior
  unconditionally in both direct and package test imports.
- Phase 2 remains unverified beyond its focused checks. No production full-suite pass, commit,
  push, or provider enforcement is claimed.
- Correction to the earlier cleanup-bridge scope note: before this record-only edit, phase 2 had
  14 staged paths, including deletion of the automation/tests/test_gate_migration_snapshots.py
  helper. Its exact candidate was
  `c1cebf0973d6791824f10ee752b972f590712689768629a2dfe8a4ad32217b0a`.
  This supersedes the historical seven-file statement only for the current phase-2 scope.
- During the record repair, the wider gate module failed in both an interference-prone concurrent
  run and a direct sequential retry. The sequential retry ran 58 tests with two failures and one
  skip; the failures were the reparented-daemon and escaped-setsid cleanup tests. The smaller
  six-test cleanup/boundary selection still passed, but phase 2 is not ready for complete
  verification and has no full-suite or exact-final pass.

## 2026-07-28 — portable cleanup late-discovery repair (codex)

- A blocking review found that the portable cleanup loop performed a second discovery into
  `live_owned` and could exit without merging or killing a PID found only by that scan. Replaced
  the two-scan iteration with one discover, merge, `SIGKILL`, and reap sequence before any exit
  decision or next scan.
- Strengthened the portable union fixture with distinct ancestry-only and out-of-ancestry exact-
  token PIDs plus foreign-UID, near-token, and self exclusions. Added delayed-`ps`, timeout,
  fake-clock ordering, late-PID, deadline-reserve, and Linux-path coverage.
- The escaped-setsid and reparented-daemon fixtures now register finalizers before execution.
  A finalizer can signal only the exact recorded PID after verifying both the current UID and a
  per-fixture unguessable command marker; the escaped child now carries that marker.
- The first seven-test focused run had one test-only error because Python 3.7 mock calls expose
  keyword arguments through tuple position rather than `.kwargs`; the corrected rerun passed.
  Both real fixtures then passed three sequential repetitions with their residue assertions.
- Correction to the prior portable-cleanup record: its claimed “direct” 63-test invocation used
  package-form syntax. The actual direct-script run now passed 65 tests with one skip in 16.789
  seconds, followed sequentially by the package-form run passing 65 with one skip in 18.430
  seconds. Phase 2 still has no exact-final gate or full repository-suite result.

## 2026-07-28 — completed-snapshot deadline repair (codex)

- A blocking review found one remaining exact-deadline edge: portable snapshot acquisition could
  finish at its deadline, then both parsers would reject the already-acquired rows without
  examining them. Deadline gates now apply only to a new snapshot acquisition and Linux `/proc`
  traversal; a supplied portable snapshot is always parsed.
- Added an integration regression in which snapshot completion advances the clock exactly to the
  deadline. The returned union retains ancestry-only PID 202 and out-of-ancestry exact-token PID
  505, and the test verifies that both are subsequently sent `SIGKILL`.
- Eight focused cleanup tests and both real fixtures passed. The actual direct script then passed
  66 tests with one skip in 16.548 seconds, followed sequentially by package form passing 66 with
  one skip in 16.716 seconds. Config, runner, and workflow regressions also passed.
- No exact-final gate, full repository suite, commit, push, stash, or ref change was performed.

## 2026-07-28 — phase-2 cleanup chronology correction (codex)

- The causal sequence after phase 2 was: the real setsid/reparented cleanup failures; the initial
  single portable-snapshot repair; the late-discovery merge-and-kill repair; then the completed-
  snapshot-at-deadline repair. This correction supersedes the ordering implied by the locations
  of earlier append-only entries without changing their historical bytes.
- The reviewed production candidate has 14 staged paths and candidate identity
  `12a68bf00510…`. A runtime review then found that the immutable base-floor helper still rejects
  current gate hash `a27b85…`; exact final verification is therefore blocked pending a small
  base-floor compatibility commit.
- This record makes no readiness, full repository-suite, exact-final, commit, push, or provider-
  enforcement claim for the current phase-2 candidate.

## 2026-07-28 — refreshed compatibility floor and protected production reapplication (codex)

- Resolved the compatibility blocker with test-only commit `7d580d3`, a one-file change with 14
  additions and one deletion. Its refreshed immutable helper admits the repaired manual tuple
  containing gate hash `a27b85…` and rejects the superseded manual runner tuple.
- The refresh candidate
  `ac6b07653007b516efaabb23f78e91ca3dcb25e9ad082681b2cc37b9b317d094` passed its exact final gate
  in 497.64 seconds: core scope 0.49 seconds, reconciliation 16.49 seconds, immutable floor
  477.62 seconds, supplemental tests 0.86 seconds, and 16 selected / 0 deferred / 0 incomplete.
  The commit hook then reused repository-tests/full evidence and passed in 15.28 seconds.
- Reapplied only the protected production stash's staged tree onto `7d580d3`; its unstaged timing
  journal delta was not applied. The refreshed helper is deleted from the production candidate
  but remains in the base-pinned floor for this transition.
- Phase 2 still has no production exact-final or full-suite result and is not marked complete.
  No production commit, push, or provider-enforcement claim was made.
- Focused verification passed the refreshed helper floor, exact four-suite supplemental run,
  direct and package gate/config/runner/workflow tests, deterministic and real cleanup fixtures,
  compilation, workflow/hash assertions, reconciliation, and staged/unstaged diff checks.

## 2026-07-28 — unanimous merge review recorded (codex)

- Five independent reviewers unanimously blocked merge of `e530c428..64490ab5`; no reviewer
  approved it. Their findings cover authority before imports, immutable executed evidence,
  provider admission, terminal reporting, new test namespaces, and stale human asks.
- Filed one self-contained manual retry and linked it from the task. The retry blocks the merge
  operation, not ongoing repair, so the task remains in progress.

## 2026-07-28 — superseded hard-gate asks retired (codex)

- Recorded the authorized manual-only disposition while both human asks were waiting in commit
  `b826df7`, then claimed both with status-only transitions in commit `d5aefe3`.
- Folded the withdrawal into
  `memory/decisions/2026-07-27-github-hard-test-gate-activation.md` and removed the two resolved
  queue items. Future enforcement remains with the existing external-oracle and OIDC-publisher
  tasks; no workflow, provider rule, or retry was changed.

## 2026-07-28 — unanimous-blocker repair and record reconciliation (codex and delegated agents)

- Repaired all six findings from the 0-approve/5-block review of `e530c428..64490ab5`. The
  bootstrap now rejects reserved automatic authority before candidate imports. Allowed runs use
  one sealed controller/index snapshot, a disposable index per component, a sanitized Python/Git
  environment, and separately recorded controller and child interpreter identities.
- Replaced the obsolete pull-request check with three clearly non-enforcing workflow diagnostics:
  push repository diagnostics, trusted PR core/merge diagnostics, and cooperative PR complete
  tests. Candidate workflow text is not treated as evidence of provider branch or ruleset policy.
- The complete plan now includes candidate-only test namespaces. Terminal reporting freezes one
  v3 report before a v4 receipt can attest its path, publication id, and digest. The composite
  plan moved to v2 and the overlay algorithm to exact union namespaces v3, invalidating older
  incomplete cache identities.
- Three focused repair reviews followed the panel. Round 1 fixed pass-report/receipt-failure
  contradiction, nested-namespace failure, successful exit with a detached child, mutable
  `PYTHONPATH` source bytes, and false drift from sealed modes. Round 2 fixed unavailable process
  discovery being read as an empty scan and a receipt surviving failed rollback. Round 3 fixed a
  mutable component index and incomplete isolated-child interpreter identity.
- Focused evidence passed the authority, correctness, evidence-integrity, gate, runner,
  configuration, workflow, snapshot-mutation, quote-service, and reconciler groups recorded in
  `verification.md`. The critical routine timing case blocked as expected at 60.15 seconds and
  created neither a receipt nor a timing task.
- At 2026-07-28 22:21:12–22:21:54 UTC, a fresh GitHub inspection of
  [QuentinMeow/agentfold](https://github.com/QuentinMeow/agentfold) found no classic branch
  protection for `main`. The sole default-branch ruleset, `main-projection` (id 19582703), was
  disabled and contained no required status checks; the current task branch had no open pull
  request. This is a time-bounded observation, not a claim about future provider state.
- Removed the now-resolved manual retry and cleared the task's reciprocal queue action. The task
  remains in progress: no post-repair exact final gate, full repository suite, production commit,
  or fresh revision-bound merge review has run yet.

## 2026-07-28 — start-handoff and verification-contract correction (codex)

- Corrected the preceding entry's premature retry-resolution statement. The unanimous-review
  retry is restored exactly at status `in-repair`, and the task again links it as a live queue
  action. It remains blocking until a committed repaired range receives the fresh revision-bound
  panel required by the retry.
- Clarified the timing mathematics in the contracts. The configured maximum runs from invocation
  start through bootstrap capture, controller startup, fallible gate work, cleanup, task filing,
  validation, and terminal outcome freeze. Atomic receipt/report/stdout projection follows the
  freeze outside that decision interval; external projection I/O can delay wall-clock return but
  cannot change the frozen outcome.
- Replaced the new summary-only verification block with retained command output from the current
  staged bytes. Direct and package gate suites each ran 92 tests and were OK with one skip. Direct
  and package runner suites each ran 52 tests and were OK. Direct and package configuration suites
  each ran 28 tests and were OK. Workflow checks ran 18 legacy diagnostic tests with six skips
  plus eight snapshot tests; the combined package command ran 26 and was OK with six skips.
- Two standalone quote selector runs supplied the same files in opposite argument orders. Both
  selected the canonical API-then-CLI order, ran five plus three tests, and passed both files.
  Fresh read-only GitHub commands and their exact outputs are recorded in `verification.md` at
  the UTC marker shown there.
- No exact final gate, full repository suite, production commit hook, commit, or fresh
  revision-bound review ran. The two timing journals and all stashes remain preserved.

## 2026-07-28 — POSIX clock and committed-publication contract sync (codex)

- Narrowed the documented runtime to CPython 3.7+ on POSIX. Windows is unsupported because the
  gate depends on POSIX process-containment and cross-process clock primitives. The bootstrap now
  carries `CLOCK_MONOTONIC` into the controller, with `os.times().elapsed` as the POSIX fallback,
  so bootstrap freezing and startup count in the configured decision interval.
- Updated the cache contract to receipt v5 plus the matching terminal v3 pass report and a v1
  publication commit marker written last. The marker binds the receipt and report digests, paths,
  publication id, candidate, and authority. Missing or mismatched members cannot be reused.
- Separated the immutable gate decision from the publication/command outcome. Receipt, report,
  marker, or stdout failure returns a command error and leaves no reusable evidence, but does not
  rewrite the gate outcome that was frozen at the measured boundary.
- The preceding 92-test gate results are superseded for the current implementation bytes. Fresh direct
  and package runs each executed 98 tests and were OK with one skip. A focused ten-test clock,
  terminal-publication, stdout, and commit-marker command was also OK; exact retained output is
  in `verification.md`.
- The unanimous-review retry remains live at status `in-repair`. No exact final gate, full
  repository suite, production commit hook, commit, or fresh revision-bound review ran. The two
  timing journals and all stashes remain preserved.

## 2026-07-28 — atomic publication exact-output sync (codex)

- Fresh direct and package gate runs each executed 102 tests and were OK with one skip; the
  focused clock/publication command executed 14 tests and was OK. After atomic rename makes the
  marker visible, directory-fsync or descriptor-close failures are advisory because the logical
  publication is already committed; every pre-rename write, file-sync, or close failure remains
  fatal. This evidence-only sync did not run an exact final/full gate or close the live retry.

## 2026-07-28 — exact final stopped by core-scope receipt (codex)

- The canonical `python3 -I -S automation/run_test_gate.py final --explicit --staged` attempt
  exited 1 before reconciliation or repository tests. Candidate `e5283a…` reached core-scope in
  0.77 seconds, which rejected the punctuation-wrapped `User-global writes` value and the
  backticked, period-terminated thin-adapter value with the two findings retained verbatim in
  `verification.md`. Coverage was 16 selected, 0 deferred, and 3 incomplete; total duration was
  4.63 seconds. The v3 report was written, while receipt and publication marker were null.
- Corrected only those fields to the template's canonical forms: `User-global writes` is exactly
  `none`, and the thin adapter uses exact unquoted canonical/optional/policy/writes pairs. This
  failed attempt produced no commit, receipt, marker, or new retry. The existing unanimous-review
  retry remains live, and no final/full pass is claimed.

## 2026-07-28 — exact compatibility bridge committed (codex and delegated agents)

- The next final attempt, candidate `a6bd61f9…`, passed core scope and reconciliation but failed
  its trusted floor after 544.18 seconds. Eleven of 15 floor files passed; the four failures were
  the workflow, queue, gate, and test-runner modules that still expected the old contract. No
  receipt, marker, or commit was created.
- The first bridge candidate, `11bd3c5c…`, proved the repaired floor: all 15 floor files passed.
  It still hit the 900-second final maximum because a migration-helper name matched a critical
  glob and a changed shared support file caused all 14 automation modules to run again. The
  supplemental lane was incomplete; no receipt, marker, or commit was created.
- Reworked the bridge into closed old/new generation tests without widening the supplemental
  manifest. Direct tests and reconciliation passed, as recorded in `verification.md`. The normal
  hook deferred only reversible unfinished coverage after 59.758121 seconds and created commit
  `fcc8d8d` (`test: bridge gate contract generations`).
- Reapplied the protected production change on top of that bridge. It remains staged and still
  needs an exact final pass, a production commit, and a fresh revision-bound merge review. The
  live unanimous-review retry remains `in-repair`.

## 2026-07-28 — product commit and blocking final review recorded (codex and delegated agents)

- Exact candidate `843a44a38f328ebde40d34f759d8592847175bd4e9d65f27301f5c6d9b710b53`
  passed the explicit final gate in 432.51825652701 seconds. The run exceeded the configured
  300-second target, so the existing final-budget journal gained occurrence 5 with the component
  timings and its timing-filer receipt field.
- The original final stdout was not retained, and the fixed `latest-final.json` path was later
  overwritten. The surviving v5 receipt, v1 marker, timing journal, and routine report preserve
  the candidate, closure, binding, publication, timing, and reuse identities recorded in
  `verification.md`; they do not recreate the missing byte-exact report or output.
- The normal commit hook reused the exact full-test binding, passed in 14.980103 seconds, and
  created product commit `3a342013063f37516b8f65e707e26e4f0c655e0a`.
- Five independent reviewers examined that immutable revision. Security/authority,
  provider/core/workflow, and migration/test-completeness approved. Gate semantics blocked on a
  P1 gap where potentially unbounded Git/materialization/controller work can precede creation of
  the configured absolute deadline. Records/contracts also blocked because the durable task
  state was stale, the original final report could not be reconstructed, and the claimed retry
  still said `Unclaimed`.
- Reconciled the task, plan, verification, worklog, and retry wording from surviving evidence.
  This repairs the stale description but not the P1 product flaw or the lost report. The merge
  retry remains `in-repair`; a P1 repair, new exact final run, new commit, and fresh panel remain
  mandatory before merge.

## 2026-07-28 — isolated absolute-deadline repair (delegated implementation)

- Built an uncommitted repair from clean revision `19ca430` in an isolated worktree. The shared
  task worktree was not changed.
- Replaced the pre-deadline bootstrap gap with a small standard-library supervisor and one owned
  POSIX worker. Policy discovery now has a five-second ceiling, uses exact base/candidate config
  and the canonical parser closure, and returns a bounded frame from which the supervisor derives
  the absolute deadline. A maximum of exactly five seconds is valid; a smaller one is rejected.
- The same worker continues snapshot and controller execution. The controller rechecks the policy
  frame against its frozen inputs and sends one bounded terminal-decision frame before publication.
  The supervisor accepts it only strictly before the deadline. A late, absent, contradictory, or
  oversized frame blocks and triggers process-group plus exact-token same-user cleanup.
- Advanced reports to v4, receipts to v6, and handoffs to v2. Receipt identity binds both lane
  budgets, config and policy identities, parser and launcher identities, and the controller
  closure. It deliberately excludes invocation clock values, preserving exact final-prewarm reuse
  by a later routine hook.
- Focused protocol tests, canonical config tests, the exact prewarm/reuse integration, nine
  existing safety regressions, compilation, whitespace checks, and reconciliation passed. One
  broader ten-test batch hit the existing macOS descendant-cleanup flake; the same prewarm/reuse
  test passed alone before and after that batch. No full repository suite, exact final gate,
  commit, or fresh panel ran, so plan step 16 and the merge retry remain open.

## 2026-07-28 — isolated deadline-protocol hardening (delegated implementation)

- Reworked authoritative discovery after two blocking reviews. Discovery now materializes the
  exact base parser/Tomli closure and base configuration from the base revision, materializes the
  candidate configuration and parser closure from one captured candidate index, and executes
  only the trusted base parser. Missing base inputs, malformed candidate configuration, or a
  closure mutation blocks; there is no fallback to live or candidate-controlled parser bytes.
- Reused that exact authoritative index for the later sealed controller snapshot. The candidate
  parser must reproduce the signed policy in the frozen controller or the run blocks.
- Split control authority into two sockets. The worker alone keeps the outer supervisor socket;
  the controller receives a new inner socket; components receive neither. The worker validates
  the controller claim and sends a distinct broker decision to the supervisor.
- Added an immutable decision object and digest to normal v4 reports and bound v6 receipts to the
  hardened protocol identity. The worker verifies the fixed-lane report after controller exit.
  Normal process exit must equal the gate exit; only post-freeze publication may turn gate exit
  0 or 1 into command exit 2. Missing frames, signals, and contradictory exits are errors.
- The focused protocol suite passed 26/26, the policy suite passed 28/28, and the real final
  prewarm-to-routine-hook integration passed in 8.991 seconds. Compilation, diff checks, the
  60-line automation contract, and reconciliation also passed. No broad suite or final gate ran.
- An existing nine-test safety subset passed eight tests. Its receipt-marker test exposed one
  additional compatibility-bridge item: `_publish_receipt_pair` still constructs a legacy report
  without the now-required `decision_digest`. This is added to the explicit task-branch migration
  list; the isolated product contract was not weakened to accept that legacy report.

## 2026-07-28 — honest supervisor-static telemetry (delegated implementation)

- Removed the static report's fabricated zero duration and `none-started` containment claim.
  Static results now retain the supervisor clock source/start, measure current elapsed time when
  possible, and use null when it is not. They record the real worker-started state and structured
  process-group and ownership-token cleanup attempts, results, and discovery completeness.
- Timeout, EOF, protocol-error, unsupported-host, control-channel, and worker-start failures now
  pass the facts available at their exact boundary. The fixed-lane v4 shape and immutable
  decision digest remain intact.
- The focused protocol suite passed 27/27, configuration passed 28/28, compilation passed, and
  the real prewarm-to-hook reuse test passed in 5.898 seconds. No broad suite or final gate ran.

## 2026-07-28 — integrated final evidence exposed reversible reuse gap (codex)

- Integrated the absolute-deadline supervisor/worker repair and the old/new generation bridge on
  the task branch. Exact staged candidate `44963ec4…` passed the explicit final gate in
  552.679782 seconds with 18 selected files and no deferred or incomplete coverage.
- Preserved the ignored v6 full receipt `08dbee980350…` and its matching v4 report and v1 marker.
  Read-only validation still accepts that evidence for the exact staged candidate.
- The following real routine hook classified the candidate as reversible, built a selected lane,
  and started the deadline-protocol, gate-runner, and configuration tests instead of reading the
  full receipt. It missed the supervisor deadline at 60.26752 seconds and created no commit.
- Traced the miss to two separate issues. Full-receipt reuse is reached only after planning a
  full component, so reversible selected planning bypasses it. The selected path also leaves only
  half a second for cleanup and terminal brokering, which this real run proved insufficient.
- Approved the bounded repair sequence: validate an exact latest-final full evidence set before
  selected execution, and leave a larger explicit terminalization reserve for the selected
  fallback. Focused regressions come first, followed by one exact final run for the complete
  repaired candidate, no further staging, one normal hook reuse attempt, and a fresh panel.
- No repair result, commit, or review is claimed here. The live merge retry remains `in-repair`.

## 2026-07-28 — focused receipt and deadline repair verified (delegated implementation)

- Moved exact latest-final receipt validation ahead of reversible selected execution. An exact
  complete evidence set now satisfies the routine gate without rerunning selected tests; missing
  or mismatched evidence still falls back to ordinary planning.
- Split the remaining decision time into explicit execution, cleanup, final-validation, and
  terminal-delivery windows. Final validation is killable and bounded, and terminal delivery uses
  a nonblocking deadline-bounded channel.
- Froze and sent the terminal claim before budget-task filing or result projection. Filing is a
  bounded post-claim attempt and cannot change the decision, duration, or gate exit code. A filer
  timeout reports mutation as unknown when a write may already have started.
- Seven new focused regressions passed. The 10-second no-receipt path deferred in 6.608 seconds,
  and the exact prewarm path reused its full receipt in 5.587 seconds without selected execution.
  The broader focused modules passed 34 protocol tests, 103 gate tests with one skip, 28
  configuration tests, and 6 generation tests. Reconciliation reported zero findings.
- An independent focused rereview returned `APPROVE`. One new exact final run, an unchanged normal
  commit attempt, and a fresh five-reviewer revision-bound panel remain pending. The live retry
  continues to block merge.

## 2026-07-28 — handover checkpoint (codex)

- Paused with `HEAD` at `a89eccc`; no deadline-repair commit was created. The earlier normal
  commit attempt failed honestly at 60.26752 seconds, and no hook was bypassed.
- The reviewed repair, plain-English records, queue note, two automation lessons, memory index,
  and handover are staged as one candidate. The two generated timing journals remain unstaged and
  are deliberately excluded. See the latest conversation handover for the exact status split.
- The next safe sequence is: verify that staged/unstaged split without changing staged bytes; run
  one exact explicit final gate; make one normal commit so the hook reuses the receipt; then run a
  fresh five-reviewer panel.
- Do not reuse the historical `44963ec4…` receipt for the repaired bytes, do not rerun the full
  suite before the staged candidate is final, and do not resolve the blocking retry before the
  new commit and panel both succeed.

## 2026-07-29 — exact final gate and receipt-bound product commit (codex and delegated diagnosis)

- Audited the live branch and PR graph. Draft PR 16 remains the only supported prerequisite; this
  task branch is its direct descendant. Unfinished message-queue and queue-resolution branches
  remain outside this stack.
- Added two test-only migration bridges after real base-pinned failures. `8cd250c` updates the
  admitted repaired-controller generation, and `84c4a90` makes the bounded filing fixture pass
  both the committed split generation and the intended deadline generation. Both commits ran the
  normal hook; no hook was bypassed.
- Rebuilt the production index to the preserved tree `188b359c…`. The first retry inside the
  restricted command sandbox failed closed because macOS `ps` access was denied. Independent
  diagnosis confirmed an observability restriction, not surviving processes or a cleanup defect.
- Reran the unchanged exact command with read-only process-table access. Candidate `d9d630b3…`
  passed all 18 selected files in 657.548652 seconds with no deferred or incomplete coverage.
- Committed the unchanged candidate as `d966c19`. The ordinary routine hook matched the same
  digest, reused the full receipt, passed core scope and reconciliation, and completed in 24.56
  seconds. A fresh five-reviewer revision-bound panel remains the only merge blocker.

## 2026-07-29 — five-panel blocker repair (codex and delegated review)

- The fresh revision-bound panel did not approve `e530c428..8fcebbe`. Its five valid blockers
  were broad reversible authorization paths, an unbound repository-local Git identity, lost
  policy facts on a post-policy static timeout, destructive check-then-replace budget-task
  publication, and quote-specific service ownership that failed repository substitution.
- Repaired the policy with critical gate-authority paths and an exact ordinary-file allowlist.
  Unmatched and new paths remain critical, and a candidate policy change is unioned with the
  trusted base policy before it can classify the same candidate.
- Replaced repository-config Git identity reads with a fixed isolated fallback while preserving
  and binding caller-supplied safe identity variables. Preserved validated lane, target, maximum,
  policy, candidate, and semantic-index facts on post-policy supervisor timeouts; the immutable
  claim now flushes before cleanup and a one-second post-claim filing attempt.
- Replaced budget-task check-and-replace writes with exclusive publication and inode-owned
  rollback, so a losing writer cannot overwrite or recursively remove another actor's data.
  Replaced quote-specific selection with the generic `services/<name>/tests` convention and a
  closed, strict-union `service_dependencies` policy.
- Landed test-only generation bridge `aba7e38` through the normal hook before production bytes.
  The focused configuration, runner, filer, deadline, and generation modules passed 152/152;
  the complete gate module passed 103 tests with one platform skip; the real reversible timeout
  integration passed in 6.620 seconds; and runtime compilation passed. A new exact final gate,
  normal commit, and fresh panel remain pending.

## 2026-07-29 — pre-final rereview and parser compatibility floor (codex and Sol reviewers)

- Three exact-staged rereviews blocked the first five-finding repair before its final gate. The
  trusted base parser rejected the new dependency key; caller Git identity never crossed the
  real safe-environment filter; canonical rollback still had pathname check/use races; static
  timeout duration was fabricated as exactly the maximum; and static stdout could block forever
  behind worker output.
- Repaired publication to use exclusive no-replace creation with no canonical deletion after any
  write, truthful partial mutation reporting, and reciprocal-request validation before append.
  Static timeouts now bind one real freeze-time sample and use killable bounded writer children
  for the claim and telemetry. Failed claim delivery still cleans the worker, skips filing, and
  returns command error 2. Focused filer and deadline modules passed 28/28 and 40/40.
- Added the four safe Git author/committer variables to the actual component allowlist; their
  values are receipt-bound and local Git config remains irrelevant.
- The first parser-floor final attempt failed in 339.07 seconds because the committed generation
  and risk tests did not recognize the compatibility endpoint. Test bridge `5397fc5` made both
  files exact-endpoint aware. The next attempt failed in 384.72 seconds because one synthetic
  timeout fixture inherited repository-wide path risk; bridge `68af0e4` gave its smoke files
  an explicit reversible policy.
- The third unchanged parser-floor candidate `c122a31f…` passed all 18 files in 442.08 seconds.
  Its ordinary hook reused the exact receipt in 17.29 seconds and created production commit
  `236b90d`. The restored remaining repair passes 42/42 exact config/generation tests. Its own
  expanded focused set, exact final gate, normal commit, and fresh panel remain pending.
- The expanded remaining-repair set now passes 42 configuration/generation, 28 filer, 40
  deadline, 53 runner, and 105 gate tests with one platform skip. The first full gate-module run
  exposed three stale fixture assumptions; keyword policy construction, explicit synthetic risk
  bindings, and one shared caller Git identity fixed them. No product contract was weakened.
- Final blocker-only rereview approved the security and correctness/cache boundaries. The
  concurrency lens found one unbounded `waitpid(..., 0)` after the bounded writer's `SIGKILL`.
  Replacing it with one nonblocking reap observation and adding a never-reaps regression raised
  the deadline module to 41 passing tests; all 105 gate tests then passed again in 30.231 seconds
  with one platform skip.

## 2026-07-29 — dual-generation final-repair bridge (codex and delegated verification)

- The first exact final run of the remaining product repair blocked after 267.99 seconds because
  the committed base-pinned tests described the parser-compatible product while the candidate
  supplied the review-repair product. The candidate's focused tests were already passing; no
  product bytes were weakened and no product commit was attempted.
- Two Sol-high compatibility passes split the bridge by boundary. Publication/deadline tests now
  retain rollback and direct-output coverage at the parser-compatible endpoint and no-delete,
  reciprocal-request, bounded-writer coverage at the review endpoint. Runner/controller tests
  retain repository-config identity and old ownership at the former endpoint and fixed/caller
  identity, generic ownership, dependency closure, and receipt binding at the latter. Exact
  product tuples are required before product import, so hybrids fail closed.
- A Terra read-only combined run exposed only the documented restricted-process-table failures;
  the unchanged command passed 274 tests with five skips once macOS process observation was
  available. Independent detached checks also passed both exact endpoints and rejected a
  deliberate hybrid.
- Exact bridge candidate `2d3e00c9…` passed its 290.71-second base floor but failed one copied-
  policy fixture because immutable candidate permissions were preserved. The fixture now makes
  only its temporary copy owner-writable, and its named integration passes in 5.490 seconds.
- Exact bridge candidate `bb4a6cef…` passed all 18 files in 349.75 seconds with no deferred or
  incomplete coverage. Its normal hook reused the exact receipt in 10.81 seconds and created
  test commit `01a58fd`. The full repair snapshot is restored, both timing journals remain
  unstaged, and the next boundary is the product candidate's exact final gate.

## 2026-07-29 — final product receipt and normal commit (codex)

- Product candidate `677e74a3…` passed the complete exact final gate in 308.12 seconds, but the
  first normal hook correctly refused that receipt because Git supplied a different bound
  environment. It started the full base floor and blocked at 56.58 seconds; no commit was made.
- Repeating the unchanged final with all four author/committer variables passed in 310.81
  seconds, but another normal hook still blocked at 56.68 seconds. Receipt comparison proved
  every product, policy, view, plan, manifest, and controller input matched; only the component
  environment digest differed.
- A deliberately aborting temporary hook observed the documented safe variables without running
  candidate code: Git populated author name and email but did not populate either committer
  variable. The hook was deleted and created no commit. This diagnosis avoided another guessed
  invocation.
- The unchanged candidate passed again in 308.25 seconds with exactly the two author variables,
  producing the hook's `d95f9678…` environment digest. The next ordinary hook reused the exact
  full receipt in 13.78 seconds and created product commit `962cca3`; no hook was bypassed. The
  fresh revision-bound panel is now the only live merge blocker.

## 2026-07-29 — first post-product panel and repair (codex and Sol reviewers)

- The five independent lenses reviewed `e530c428…d63e230`. Correctness/cache approved. Four
  accepted issues remained: descriptor-unbound journal append with symlink escape and false
  mutation reporting, reversible classification of root `AGENTS.md`, silent unknown dependency
  targets, and an unusable first-project hook-install order. The evidence lens's restricted-`ps`
  result was adjudicated as intentional fail-closed behavior; cleanup completeness is not claimed
  when the platform denies observation.
- Journal access now pins a no-follow regular descriptor, validates the exact prior inode and
  bytes before append, and truthfully reports every post-write uncertainty as mutated without
  deleting canonical paths. Focused coverage passes 34 cases with one historical-endpoint skip.
- Root `AGENTS.md` is authorization-critical. Routine service dependencies must resolve to
  discovered test namespaces. The adoption guide configures and adapts a history-free copy before
  creating its baseline and installing the hook. Configuration, controller, adoption, syntax,
  diff, and reconciliation checks pass.
- A six-file closed bridge admits only the old review tuple and combined panel-repair tuple.
  Exact candidate `477ebfb0…` passed all 18 files in 346.56 seconds; its ordinary hook reused the
  full receipt in 10.81 seconds and created `63b12b7`. The restored combined product repair is
  staged except for the two generated timing journals.

## 2026-07-29 — combined panel repair committed (codex)

- Immutable staged tree `ed3650f6…` passed exact final candidate `6b159196…` in 309.88
  seconds: 19 selected files, none deferred or incomplete. The base-pinned floor took 294.65
  seconds and candidate supplemental coverage took 0.64 seconds.
- The unchanged normal pre-commit hook reused the exact full receipt, reran core-scope and
  reconciliation, and passed in 13.94 seconds. Product commit `d513a70` was created without
  bypassing the hook. Both generated timing journals remain deliberately unstaged.
- A fresh five-reviewer revision-bound panel is the only remaining repair boundary before the
  retry can be resolved and the task can move to review.

## 2026-07-29 — second post-product panel (codex and Sol reviewers)

- Five independent lenses reviewed exact range `e530c428…e87cef8` without task evidence or prior
  opinions. All five blocked. Reproductions exposed intermediate-directory publication
  redirection, unbound process umask, reversible nested instruction contracts, active Git
  replacement objects, broken final-to-final receipt projection, unclean supervisor interruption,
  and literal-`python3` relaunches.
- The main agent accepted all seven findings. Three bounded Sol-high implementation owners are
  repairing descriptor-relative publication, cache/policy identity, and supervisor/Git behavior
  in non-overlapping files. No new task or feature has been started.

## 2026-07-29 — second-panel repair bridge (codex and Sol implementers)

- Implemented all seven accepted repairs and passed a process-enabled 304-test combined matrix
  with five intentional skips. The closed classifier admits exact old and repaired tuples and
  rejects single-file and mixed hybrids.
- The first bridge final failed one candidate-supplemental test after the 294.82-second base
  floor because a repaired-only assertion still ran on the old endpoint. Restricting that block
  to the repaired tuple made the focused old integration pass in 5.578 seconds.
- Corrected bridge candidate `0135d142…` passed the exact final gate in 353.14 seconds with all
  19 files complete. Normal receipt reuse passed in 11.17 seconds and created `40500b9`; no hook
  was bypassed. The exact product/records snapshot is restored for its own final boundary.

## 2026-07-29 — second-panel repaired product committed (codex)

- Immutable product-and-records tree `d0ea4b17…` passed exact final candidate `2b2b2eec…` in
  313.32 seconds with all 19 files complete and none deferred or incomplete.
- The unchanged normal hook reused the exact full receipt in 13.77 seconds and created product
  commit `f748887`; no hook was bypassed. The temporary repair stash was removed only after HEAD
  hashes matched the closed product tuple. Both generated timing journals remain unstaged.
- A completely fresh five-reviewer panel is the sole remaining merge-review boundary.
