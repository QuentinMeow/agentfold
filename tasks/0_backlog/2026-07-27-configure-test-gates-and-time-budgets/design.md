# Design notes — configurable test gates and time budgets

**Status:** decided

## Problem

AgentFold currently pays complete-suite cost at every commit. Recorded clean runs need about
four minutes, and Git-heavy branches have shown substantially higher variance. That gives high
confidence eventually, but it is the wrong sequencing for routine reversible work: feedback
arrives too late, agents avoid checkpoints, and a single test-fixture mistake can waste minutes
before producing its first useful signal.

The design must satisfy four constraints at once:

1. Routine harness feedback is less than 60 seconds by default and configurable per repository.
2. Complete coverage remains available as a trustworthy final gate without running after every
   edit or commit.
3. Security, privacy, destructive, and publication boundaries cannot be weakened merely to meet
   a speed target.
4. Time regressions create durable, deduplicated investigation work rather than depending on a
   person noticing a slow run.

## Options considered

### Option A — Keep the complete suite in every commit gate

This preserves the current sequence and requires the least code. Its consequence is also the
current problem: a small reversible change waits roughly four minutes in recorded clean runs,
and slow Git integration tests dominate every iteration even when unrelated to the change.

### Option B — Budgeted routine gate plus configurable final gate

Run admission, reconciliation, and only the smallest safely selected tests during ordinary
development. Move complete coverage to an explicit final lane whose mode is either manual or
automatic at one named final-stage boundary. Preserve honesty by reporting deferred coverage,
and require stronger behavior for one-way-door scopes. This is the recommended option.

The consequence is that an ordinary commit no longer proves the entire repository correct. It
proves the named selected checks passed and identifies what remains for the final gate. That is
an intentional exchange of immediate breadth for much faster feedback, with complete evidence
still required at the configured boundary.

### Option C — Remove local harness tests and rely on CI

This makes local commits fast but moves even obvious failures to a remote queue. It increases
the edit-to-diagnosis interval, depends on a provider, and gives adopted offline repositories no
useful local assurance. It is rejected.

## Chosen

Choose Option B and implement it through one root-level, repository-owned `agentfold.toml`.
One policy surface is easier to discover and audit than constants spread across hooks, scripts,
and provider workflows. TOML is preferred because the file is primarily edited by humans; the
implementation must either declare a compatible Python baseline for `tomllib` or provide a
small isolated compatibility adapter without adding runtime-specific policy.

A representative configuration should read approximately as follows; the implementation may
refine names while preserving these semantics:

```toml
[testing.routine]
mode = "hard"
trigger = "pre-commit"
target_seconds = 60
maximum_seconds = 60
on_reversible_timeout = "defer-to-final"

[testing.final]
mode = "manual"                 # manual | hard | soft | off
trigger = "task-review"         # used when automatic
target_seconds = 300

[testing.performance]
on_budget_exceeded = "file-task"
breaches_before_task = 1

[testing.critical]
final_mode = "hard"
categories = [
  "credentials-and-secrets",
  "pii",
  "authorization",
  "destructive-operations",
  "external-publication",
  "production-deployment",
]
```

The starter recommendation is a 60-second routine target and a five-minute final target. The
final target is deliberately configurable: it is an investigation threshold, not permission to
skip correctness. Exceeding either target files performance work; a functionally successful run
does not become a functional failure solely because it was slow.

### Gate sequencing

The routine sequence is: identify the candidate bytes and risk class; validate the policy;
run core-scope admission; run an incremental reconciler; select affected pure tests and a small
integration smoke set; then report the result and deferred coverage. The target measures from
the beginning of candidate identification through the final report, so setup time cannot be
hidden outside the budget.

At the configured maximum, reversible remaining work is terminated cleanly or not started and
is transferred to the final manifest. A critical obligation is never converted into a pass or a
defer solely to satisfy the clock: its protected transition blocks until complete evidence
exists.

The final sequence consumes the deferred manifest, runs every required complete test and guard,
and writes a content-bound receipt. `manual` means it runs only through an explicit command.
`hard` means it launches automatically only at the configured final-stage trigger and blocks
that transition on functional failure or incomplete critical coverage. `soft` and `off` remain
available for consistency with the guard-mode decision, but must visibly lower the reported
assurance; the starter template recommends `manual` until a repository chooses automatic final
enforcement.

### Avoiding duplicate work

A successful gate receipt may be reused only when the exact tested-byte fingerprint, selected
or full test manifest, config digest, runner revision, and relevant interpreter/Git identity all
match. Any mismatch reruns the affected gate. This prevents the common waste of manually running
the full suite and then immediately running the same suite again in a commit or final transition.

### Automatically filing time regressions

Every gate records monotonic wall-clock duration by component. If elapsed time is greater than
its configured target, the runner invokes one deterministic budget-task filer. Its identity is
the gate name plus the stable budget/config identity, not the date or run number.

The generated task contains the target, actual duration, candidate fingerprint, component
breakdown, environment summary, and the command or trigger. It also creates the required
non-blocking pickup request. A later run updates the generated evidence block of the same open
task while preserving human/agent notes. If the prior task is done and the regression returns,
the filer creates a new dated task linked to the previous one.

The filer may create files in a writable checkout, but it never stages or commits them. When a
hook requires the new records to become durable, it stops once with a precise instruction to
include them; the exact test receipt is then reusable, so the developer does not pay for the
same slow run twice. Read-only environments emit the same finding as machine-readable output
for a thin provider adapter rather than pretending a task was filed.

### Test architecture direction

Meeting the target should prioritize sequencing before sacrificing coverage:

- separate pure policy tests from real-Git adapter tests;
- map source paths to affected tests with an explicit fail-closed ownership table;
- reuse immutable Git fixtures where isolation remains valid;
- run independent integration shards concurrently only after measuring contention;
- keep a small topology and projection smoke set in the routine lane;
- keep exhaustive, generated, and cross-history cases in the final lane; and
- stop rerunning a content-identical final result.

These are optimization choices, not permission to delete tests. The first implementation should
use the smallest combination that meets the configured target with measured evidence.

## Core fit

**Agent substitution:** pass — selection, timing, receipts, and task filing are repository mechanisms independent of the agent runtime
**Provider substitution:** pass — local gates work without CI; a provider only needs a thin adapter to persist read-only findings or enforce a named final boundary
**Repository substitution:** pass — adopted repositories need fast feedback, configurable final assurance, and performance-regression work without inheriting AgentFold's exact test suite
**User-global writes:** none
**Why AgentFold core:** this defines the portable relationship between local feedback, final assurance, repository policy, and durable task filing rather than a personal optimization or example-service behavior
**Thin adapter:** canonical=`automation/run_tests.py`; optional=yes; policy=none; writes=repo-only
