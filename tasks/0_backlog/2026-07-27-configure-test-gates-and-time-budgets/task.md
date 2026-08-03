# Keep routine harness feedback within a configurable time budget

**Claimed-by:** unclaimed
**Filed:** 2026-07-27, by codex, from the owner's test-cycle request in chat
**Parent:** 2026-07-26-continue-development-cycle-acceleration
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-configure-test-gates-and-time-budgets.md`

## Goal

Make the routine local harness cycle finish in less than 60 seconds by default, while
preserving complete verification at a configurable final boundary. Put the time targets
and final-gate policy in one repository-local configuration file so an adopted repository
can choose its own budgets without editing automation code. When a named gate exceeds its
configured target, automatically file one deduplicated investigation task with real timing
evidence so slowdowns cannot become the unnoticed new normal.

## What the investigation found

> **Stale as of 2026-08-02 — re-measure before implementing.** This section describes the
> serial, process-heavy runner as it was on 2026-07-27. Parallelisation and staged
> selection have merged since, and the full suite now measures 75.87 seconds. The 60-second
> routine target in the Goal and in the first acceptance criterion was derived from the old
> numbers and is not a decided target; `worklog.md` records the measurement and what it
> unsettles.

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
  Its default end-to-end budget is 60 seconds, including admission, reconciliation, test
  selection, and selected tests. Reversible coverage that cannot finish in the budget is
  reported as deferred to the final gate, never mislabeled as complete.
- **Final gate:** runs complete verification either only when explicitly requested or
  automatically at one configured final-stage boundary. It does not run on every normal
  commit. An exact matching result may be reused instead of running the same suite twice.

For changes affecting credentials, secrets, PII, authorization, destructive operations,
external publication, production deployment, or other configured one-way-door scopes,
reversible deferral is unavailable. Their protected-boundary outcome remains blocked unless
the configured critical checks produce complete final evidence.

## Acceptance criteria

- [ ] A documented, versioned repository config defines the routine-gate target, final-gate
      target, final-gate mode and trigger, critical scopes, and the action taken after a time
      budget breach. The starter routine target is 60 seconds; invalid or unknown safety-
      relevant values fail with a specific explanation.
- [ ] WHEN a representative small reversible service change or automation change enters the
      routine gate, THE SYSTEM SHALL report a result within the configured end-to-end budget,
      including the checks run, the checks deferred, the reason, and wall-clock time.
- [ ] WHEN routine work reaches its budget before all noncritical coverage completes, THE
      SYSTEM SHALL stop or avoid the remaining work, mark that coverage as deferred, and
      require it at the configured final boundary rather than claiming a full pass.
- [ ] A repository can configure complete verification as `manual` or as an automatic `hard`
      gate at one named final-stage trigger such as task review or merge. No supported setting
      silently turns the complete suite back into an every-commit gate.
- [ ] Final evidence and cached evidence bind to the exact tested bytes, test manifest,
      policy configuration, runner version, and relevant toolchain identity. A changed input
      invalidates reuse.
- [ ] Critical scopes cannot inherit a weaker reversible deferral. A missing, incomplete, or
      failed critical check blocks its protected final transition with a clear explanation.
- [ ] Every named gate reports component timings in deterministic human-readable and machine-
      readable form, without writing routine timing noise into tracked files.
- [ ] WHEN a gate exceeds its configured target in a writable checkout, THE SYSTEM SHALL
      create one backlog investigation task and its required pickup request from canonical
      templates. Repeated breaches of the same open finding update its evidence rather than
      create duplicates; recurrence after resolution creates a new task.
- [ ] The budget-task filer never stages or commits on the user's behalf. If durable filing
      requires a follow-up commit, it explains that once and reuses exact matching test
      evidence so recording the regression does not repeat the slow suite.
- [ ] Focused tests cover configuration validation, routine selection and deferral, manual and
      final-stage modes, critical overrides, exact-evidence reuse, timeout cleanup, budget-
      task creation, deduplication, and recurrence after resolution.
- [ ] Verification records before-and-after timings for representative service, automation,
      and cross-cutting changes. The routine examples meet the configured 60-second starter
      target; any exception is explicitly classified as critical rather than hidden in an
      average.

## The earlier attempt's states are archived, not lost

An earlier run of this task left eight Git stashes in the owner's working clone and a branch
that never merged. None of it is on `main`, and all of it predates the staleness notice
above, so a future claimant should treat it as reference rather than as a starting point —
re-measure first, as that notice says.

The branch's committed content is `archive/2026-07-27-configure-test-gates-and-time-budgets`.
The eight stashes held intermediate states that tag does **not** contain, and a stash is
reachable only through the reflog, so they sat one `git gc` or one stray `git stash drop`
away from being gone. They are now `archive/2026-07-27-test-gate-stash-<0..7>-<slug>`, and
every archive tag is pushed to `origin` — before 2026-08-02 only one of the six existing
ones had been, so the rest existed on a single laptop.

What those states carry and `main` does not: a test-gate runner, a gate controller, a gate
configuration module, and a testing-gates handbook page, together with their tests. Their
exact paths are readable from any of the tags above; they are not written here as paths,
because none of them resolves against this tree and the link check is right to say so.

## Links

- Design and rationale: `design.md`
- Implementation plan: `plan.md`
- Parent acceleration task: `2026-07-26-continue-development-cycle-acceleration`
- Existing selector task: `2026-07-26-accelerate-development-feedback`
- Full test runner: `automation/run_tests.py`
- Pre-commit hook: `automation/hooks/pre-commit`
- Configurable guard-mode decision: `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`
- Deterministic auto-filing lesson: `memory/lessons/automation/deterministic-finding-keys.md`
