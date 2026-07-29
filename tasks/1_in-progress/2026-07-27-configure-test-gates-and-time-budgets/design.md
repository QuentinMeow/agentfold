# Design — configurable test gates and time budgets

**Status:** decided
**Authorization:** `memory/decisions/2026-07-27-manual-only-test-gate-replan.md`

## Decision in plain English

Use one repository-owned `agentfold.toml` to define two test lanes.

- The routine lane runs automatically for staged work. Its default target and maximum are both
  60 seconds for the decision interval: invocation and bootstrap, discovery, admission, tests,
  cleanup, budget-task filing, final validation, and terminal outcome freeze.
- The final lane runs the complete suite only when a maintainer asks for it explicitly. Its
  starter mode is manual.
- Work that is ordinary and reversible may be deferred from the routine lane to the final lane.
  Work involving credentials, PII, authorization, destructive actions, publication, deployment,
  or an unmatched path is critical and cannot be made safe merely by deferring it.
- A matching complete result may be reused, but only when the candidate and everything that
  affected the execution are unchanged.
- Exceeding a target files or updates one deduplicated investigation task with actual timing
  evidence. The filer never stages or commits that task.

The original design explored an automatic GitHub hard gate. Security review showed that the
same-interpreter runner cannot prove that all trusted assertions finished: candidate code can
exit the interpreter successfully before later assertions run. A repository workflow also
cannot provide an independently controlled completion oracle or publisher. The owner therefore
authorized the manual-only endpoint. Automatic syntax remains reserved for future compatibility,
but every named transition and provider-hard request fails before candidate imports.

## Policy and risk rules

The configuration schema is closed and versioned. Unknown safety-relevant tables, keys, modes,
or triggers fail with a specific error. Targets and maximums must be positive finite numbers,
and a target cannot exceed its maximum. The starter values are 60/60 seconds for routine and
300/900 seconds for final. `file-task` is the only budget-breach action in version 1.

Every policy names all six critical categories exactly once: credentials and secrets, PII,
authorization, destructive operations, external publication, and production deployment.
Critical rules contain path globs and required checks. Reversible rules name ordinary scopes.
A critical match wins, and an unmatched path is critical. These are explicit path bindings, not
a claim that filenames can discover every security-sensitive semantic change.

When the candidate changes `agentfold.toml`, the gate evaluates both the trusted base policy and
the candidate policy. The stricter classification and smaller time limits win. Policy identity
is the SHA-256 of normalized policy data, so formatting does not change identity but a semantic
change does.

## One captured candidate

The canonical direct command is `python3 -I -S automation/run_test_gate.py …`. The small
supervisor uses only the standard library. It checks raw arguments first, so reserved automatic
modes are rejected before Git discovery, configuration reads, candidate imports, report or
receipt access, and budget-task state.

The supported runtime is CPython 3.7 or newer on POSIX. Windows is not supported: the gate's
process containment and its cross-process budget clock require POSIX primitives. The supervisor
prefers `clock_gettime(CLOCK_MONOTONIC)` and passes that identified source, start value, and
deadline across `exec`; when that API is unavailable on POSIX, it uses `os.times().elapsed`.
The worker and controller reject a changed source, invalid or reversed values, or total clock
unavailability.

For an allowed run, the worker captures one authoritative Git index during bounded discovery.
It materializes the exact base parser closure separately from the candidate parser closure and
runs only the base parser to read both configurations and compute their strict union. It then
reuses the same index—without recapture—to seal and dispatch the gate controller and its
dependency closure. The controller reproduces the policy with the candidate parser or blocks.
Each component receives a
disposable index copy and a sanitized environment. The execution identity records the controller
interpreter separately from the isolated, no-site child interpreter. Any source, index,
controller-closure, interpreter, or admitted-environment drift blocks the result and receipt.
The supervisor kills the worker group and exact-token same-user escapees on a missed deadline.
Portable discovery can be incomplete outside Linux `/proc`; this is an explicit POSIX limitation,
not a kernel-isolation claim. Forced termination can leave system-temporary snapshot files for
the operating system to reap, but it writes no reusable receipt before a terminal decision.

This structure addresses the central authority question: the candidate may supply code for an
explicit cooperative run, but it cannot turn reserved hard syntax into an execution path before
the supervisor has rejected it.

## Complete coverage

Complete testing combines two views:

1. The trusted base contributes every base test and the support files in its test namespaces.
   Those exact bytes are overlaid onto the candidate product.
2. Candidate-added or byte-changed tests run as supplemental evidence from an exact candidate
   view. Candidate-only test namespaces are included, so a new directory cannot hide new tests.

Only test namespaces are overlaid. Product deletions elsewhere remain deletions. A changed helper
under a trusted test namespace reruns the candidate tests in that namespace. Each test file gets
a fresh sealed projection, so one test cannot rewrite the inputs of the next.

This supports a two-step incompatible API migration: first add compatible behavior and updated
tests; after those tests enter the trusted base, remove the deprecated behavior. It still does
not create controlled completion. Reports and receipts therefore say the evidence is
`cooperative-same-interpreter`, controlled completion is false, and enforcement eligibility is
false.

## Reports, receipts, and timing

Cache reuse has a simple rule: skip the complete suite only when this is provably the same test
job. The code, selected tests, policy, runner, tools, admitted environment, and published pass
evidence must all match. If any part changed or is missing, the suite runs again. This saves a
duplicate run; it does not turn cooperative local evidence into permission to merge or deploy.

The repaired formats are report schema v4, receipt schema v6, handoff schema v2,
publication-commit schema v1,
composite-plan schema v2, and overlay algorithm
candidate-product-with-exact-union-test-namespaces/v3. The version bumps
invalidate older evidence that did not bind the repaired execution closure and candidate-only
namespace behavior.

The decision clock starts in a small POSIX supervisor before filesystem or Git discovery. One
owned worker has exactly five seconds to capture the authoritative index, materialize the exact
base/candidate configuration and their separate parser closures, execute the base parser, and
return a bounded policy frame. The supervisor validates that frame,
requires a maximum of at least five seconds, derives the absolute deadline, and lets the same
worker continue freezing and controller execution. Bootstrap freezing, materialization, sealing,
and controller startup consume the same configured maximum as tests and cleanup. All fallible gate
work, budget filing, publication preparation, and final accounting finish before one gate outcome
is frozen. The worker owns the supervisor socket; the controller gets a separate inner socket;
components get neither. The controller submits an immutable decision claim, and the worker
validates and brokers a distinct terminal frame. Publication has a separate command outcome. The
receipt and pass report are projected
afterward, followed by stdout. Only after those projections succeed is the atomic commit marker
that attests them written last. A self-report cannot include its own completed projection. That
external I/O may delay
wall-clock return beyond the maximum, without a gate-supplied bound, but it cannot change the
frozen gate decision. Receipt, report, stdout, or marker failure returns a command error and
leaves no reusable evidence. Normal exits equal the frozen gate exit; publication alone may turn
a frozen 0 or 1 into command exit 2. Missing frames, signals, and contradictory exits are protocol
errors. The normal v4 report includes the immutable decision object and digest checked by the
worker after controller exit.

Supervisor-static v4 reports use the same identified invocation clock for real elapsed time.
When timing or process facts cannot be observed, they are null or explicitly unavailable rather
than fabricated. Post-start failures include the worker-started fact plus process-group and
ownership-token cleanup attempts, results, and discovery completeness.

A reusable evidence set consists of a matching v6 receipt, terminal v4 pass report, and v1
publication commit marker. The marker binds both file digests, paths, publication id, candidate,
and evidence authority, and is written last. The receipt also binds the candidate closure,
policies, manifests, trusted floor and supplemental
records, overlay algorithm and view digests, controller closure, disposable-index identity,
controller and child interpreters, Git identity, sanitized component environment, both lane
budgets, exact configuration, both parser closures, authoritative index, launcher, immutable
decision, and supervised protocol.
Invocation start and absolute-deadline values are intentionally excluded so the same job can be
reused at a later start time. It is an
exact cooperative cache entry, not an authorization artifact. Different bytes, topology, tools,
or admitted environment require another complete run.

The whole decision interval is measured. Reversible routine work that cannot finish is reported
as deferred. Incomplete final or critical work blocks. A target breach creates or refreshes one
non-blocking investigation task from canonical templates, appends bounded timing evidence, and
never stages or commits the result. Post-freeze projection latency is not gate decision time.

## Provider boundary

The workflow exposes three diagnostics: push repository diagnostics, trusted pull-request
core/merge diagnostics, and cooperative pull-request complete tests. They are deliberately not
merge gates. The workflow has no status publisher or required-check claim, and candidate workflow
text cannot prove the provider's live branch or ruleset configuration. Provider state must be
checked independently at the boundary where it matters.

Automatic enforcement remains separate work: one follow-up must provide a controlled external
completion oracle, and another must publish through independently controlled OIDC identity and
replay state. Until both exist and are verified, the final lane stays manual.

## Repair chronology

Security review changed the endpoint from an automatic hard gate to manual final verification.
A later five-reviewer merge panel blocked the first manual implementation, and focused repair
reviews found more execution, cleanup, and publication problems. The current candidate contains
those repairs and a test-only bridge for the old and new contracts, but it still needs a complete
final run and a fresh merge review. See `worklog.md` for the chronology and `verification.md` for
the exact commands, timings, failures, and review verdicts.

## Core fit

**Agent substitution:** pass — selection, timing, receipts, and task filing are repository
mechanisms independent of the agent runtime.

**Provider substitution:** pass — local gates work without CI; providers may supply thin
diagnostic adapters, but automatic enforcement requires a separately controlled boundary.

**Repository substitution:** pass — adopted repositories can choose budgets and risk bindings
without inheriting AgentFold's exact service layout.

**User-global writes:** none

**Why AgentFold core:** this is the portable contract between fast local feedback, complete
manual evidence, repository policy, and durable regression work.

**Thin adapter:** canonical=automation/run_test_gate.py; optional=yes; policy=none; writes=repo-only
