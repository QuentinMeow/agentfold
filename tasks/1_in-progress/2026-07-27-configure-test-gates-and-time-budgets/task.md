# Keep routine harness feedback within a configurable time budget

**Claimed-by:** codex
**Filed:** 2026-07-27, by codex, from the owner's test-cycle request in chat
**Parent:** 2026-07-26-continue-development-cycle-acceleration
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/retries/blocking-repair-unanimous-test-gate-merge-review.md`

## Goal

Make the routine local harness cycle finish in less than 60 seconds by default, while
preserving complete verification at a configurable final boundary. Put the time targets
and final-gate policy in one repository-local configuration file so an adopted repository
can choose its own budgets without editing automation code. When a named gate exceeds its
configured target, automatically file one deduplicated investigation task with real timing
evidence so slowdowns cannot become the unnoticed new normal.

## What the investigation found

The current pre-commit hook always runs core-scope admission, the reconciler, and the full
isolated repository suite in sequence. The latest recorded clean measurements put the
reconciler at about 5.28 seconds and the full suite at 214.62–221.17 seconds. Two Git-heavy
automation test files account for about 89% of suite time; one queue test file has varied
from 91.73 to 311.67 seconds on active branches. The runner executes test files serially,
and those tests repeatedly create real temporary Git repositories and subprocesses.

A staged service-only selector has demonstrated roughly 1.06–1.27-second test selection,
but automation and cross-cutting changes still fall back to the full suite. The bottleneck
is therefore not ordinary assertions. It is repeated, serial, process-heavy integration
setup combined with running complete coverage at an inner-loop boundary where most changes
need only focused evidence.

## Required behavior

The system will have two plainly named lanes:

- **Routine gate:** automatically runs the smallest safe checks for the candidate change.
  Its default decision budget is 60 seconds from invocation through bootstrap, admission,
  reconciliation, test selection, selected tests, cleanup, final validation, and the terminal
  outcome claim. It freezes and sends that claim first. Bounded budget-task filing and evidence
  publication happen afterward and cannot change the decision, measured duration, or gate exit
  code. Publication can delay process return, and publication failure still makes the command
  fail and prevents cache reuse. Reversible coverage that cannot finish in the decision budget
  is reported as deferred, never mislabeled as complete.
- **Final gate:** runs complete verification only when explicitly requested. The starter is
  manual because the included same-interpreter runner cannot independently prove controlled
  completion. An exact matching result may be reused instead of running the same suite twice.

For changes affecting credentials, secrets, PII, authorization, destructive operations,
external publication, production deployment, or other configured one-way-door scopes,
reversible deferral is unavailable. Automatic critical transitions remain unavailable and
blocked in this task; cooperative manual evidence must not be promoted into enforcement proof.

## Current state

The earlier manual-only product implementation is committed as `3a342013`. Its blocking review
led to the absolute-deadline supervisor/worker repair, which is now integrated on this task
branch together with the old/new generation test bridge. Exact staged candidate
`44963ec447ee095dcdedd6fb7eacc903526b2eaddcc6ae54356c670f654a28cb` passed the explicit
final gate in 552.679782 seconds. Its ignored v6 full-test receipt has binding
`08dbee980350296d54930c01f51d2d7ba3e917820a63d6502a48a6a74f86f2fa`; the matching v4
report and v1 publication marker remain present and the receipt still validates.

The following real routine commit hook did not reuse that evidence. Because every changed path
was reversible, routine planning chose the repository-tests/selected component. The cache lookup
accepts only repository-tests/full, so it was never asked to read the valid full receipt. The hook started
the deadline-protocol, gate-runner, and configuration tests instead, then failed to freeze a
terminal decision before the absolute deadline; the supervisor observed 60.26752 seconds and no
commit was created.

That focused repair is now implemented. A bounded lookup through the fixed latest-final
projection lets an exact, fully validated full receipt satisfy a reversible routine candidate
before selected tests start. The fallback now has separate limits for execution, cleanup, final
validation, and terminal delivery. Final validation runs in a killable helper, and terminal
delivery uses a nonblocking deadline-bounded channel. The claim freezes first; bounded
budget-task filing and all result projection happen afterward and cannot rewrite it.

The seven new deadline and receipt regressions pass. The no-receipt fallback deferred truthfully
in 6.608 seconds under a 10-second maximum, and the exact prewarmed receipt was reused in 5.587
seconds without starting selected tests. The full focused modules also pass: 34 protocol tests,
103 gate tests with one skip, 28 configuration tests, and 6 generation tests. Reconciliation
reported zero findings, and an independent focused rereview returned `APPROVE`.

This is not yet the final evidence for the complete candidate. The remaining sequence is one new
exact final run, no staged changes afterward, one normal commit attempt proving receipt reuse,
and a fresh five-reviewer revision-bound panel. The live retry continues to block merge until
that sequence succeeds.

## Acceptance criteria

- [ ] A documented, versioned repository config defines the routine-gate target, final-gate
      target, final-gate mode and trigger, critical scopes, and the action taken after a time
      budget breach. The starter routine target is 60 seconds; invalid or unknown safety-
      relevant values fail with a specific explanation.
- [ ] WHEN a representative small reversible service change or automation change enters the
      routine gate, THE SYSTEM SHALL freeze a result within the configured decision budget and
      report the checks run, checks deferred, reason, and measured decision time. Post-freeze
      projection may delay wall-clock return but may not change that result.
- [ ] WHEN routine work reaches its budget before all noncritical coverage completes, THE
      SYSTEM SHALL stop or avoid the remaining work, mark that coverage as deferred, and
      require it at the configured final boundary rather than claiming a full pass.
- [ ] The starter final mode is `manual`, omits an automatic trigger, and runs only by an
      explicit command. The schema reserves `hard` for compatibility, but every automatic or
      provider-hard invocation fails closed until a controlled external oracle and publisher
      are installed by the two follow-up tasks. No supported setting silently turns the complete
      suite back into an every-commit gate.
- [ ] Final evidence and cached evidence bind to the exact tested bytes, test manifest,
      policy configuration, runner version, and relevant toolchain identity. Reuse also requires
      one matching v6 receipt, terminal v4 pass report, and last-written publication marker. A
      changed or missing input invalidates reuse. An exact full receipt may satisfy either a
      critical or reversible routine candidate before narrower selected work starts.
- [ ] Complete results from the included same-interpreter runner are labeled cooperative and
      `enforcement_eligible: false`; they can support a maintainer's manual judgment but cannot
      authorize an automatic transition.
- [ ] Critical scopes cannot inherit a weaker reversible deferral. A missing, incomplete, or
      failed critical check blocks its protected final transition with a clear explanation, and
      automatic critical transitions remain unavailable while hard mode lacks its external
      enforcement dependencies.
- [ ] Every named gate reports component timings in deterministic human-readable and machine-
      readable form, without writing routine timing noise into tracked files.
- [ ] WHEN a gate exceeds its configured target in a writable checkout, THE SYSTEM SHALL
      create one backlog investigation task and its required pickup request from canonical
      templates. Repeated breaches of the same open finding update its evidence rather than
      create duplicates; recurrence after resolution creates a new task.
- [ ] The budget-task filer never stages or commits on the user's behalf. If durable filing
      requires a follow-up commit, it explains that once and reuses exact matching test
      evidence so recording the regression does not repeat the slow suite.
- [ ] Focused tests cover configuration validation, routine selection and deferral, explicit
      manual final execution, reserved hard mode failing closed, cooperative evidence labels,
      same-interpreter early exit, complete publisher/status-authority removal, critical
      automatic transitions remaining unavailable, exact-evidence reuse, timeout cleanup,
      budget-task creation, deduplication, and recurrence after resolution.
- [ ] Verification records before-and-after timings for representative service, automation,
      and cross-cutting changes. The routine examples meet the configured 60-second starter
      target; any exception is explicitly classified as critical rather than hidden in an
      average.

## Links

- Design and rationale: `design.md`
- Implementation plan: `plan.md`
- Parent acceleration task: `2026-07-26-continue-development-cycle-acceleration`
- Existing selector task: `2026-07-26-accelerate-development-feedback`
- Full test runner: `automation/run_tests.py`
- Pre-commit hook: `automation/hooks/pre-commit`
- Configurable guard-mode decision: `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`
- Deterministic auto-filing lesson: `memory/lessons/automation/deterministic-finding-keys.md`
