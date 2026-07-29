# Design — configurable test gates and time budgets

**Status:** decided
**Authorization:** `memory/decisions/2026-07-27-manual-only-test-gate-replan.md`

## Decision in plain English

Use one repository-owned `agentfold.toml` to define two test lanes.

- The routine lane runs automatically for staged work. Its default target and maximum are both
  60 seconds for the decision interval: invocation and bootstrap, discovery, admission, tests,
  cleanup, final validation, and the terminal outcome claim. Bounded budget-task filing and
  evidence projection happen only after that claim is frozen and sent.
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

Reversible bindings are deliberately narrow. Configuration, hooks, gate launchers, policy
parsing, selection, manifests, and budget-task publication are critical authorization paths;
ordinary reversible entries name the exact known support and example-service files. New paths
are therefore critical until the policy change that classifies them is present in the same
candidate and survives the base/candidate policy union. The gate performs no semantic inference
from source text.

When the candidate changes `agentfold.toml`, the gate evaluates both the trusted base policy and
the candidate policy. The stricter classification and smaller time limits win. Policy identity
is the SHA-256 of normalized policy data, so formatting does not change identity but a semantic
change does.

Routine service selection follows the portable `services/<name>/tests` convention. The closed
routine policy may declare downstream service dependencies; the base/candidate union retains
every edge from either policy, and selection takes their transitive closure. The starter policy
states that `quote-cli` depends on `quote-api`, but the controller contains no quote-specific
ownership rule.

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

Routine risk classification does not narrow already-complete evidence. Before starting selected
tests for a reversible candidate, the gate may inspect only the fixed latest-final projection.
If that projection names the same candidate and closure, the gate validates its complete v6
receipt, v4 report, and v1 marker and compares the stored full binding with the current tested
view, policy, both lane budgets, protocol, runner and controller closure, admitted environment,
and composite test plan. An exact match records the repository-tests/full component as reused, clears
deferred coverage, and does not start selected tests. A missing or mismatched artifact falls back
to ordinary selected planning. The lookup never scans an unbounded receipt directory and never
treats a selected receipt as full evidence.

The repaired formats are report schema v4, receipt schema v6, handoff schema v2,
publication-commit schema v1,
composite-plan schema v2, and overlay algorithm
candidate-product-with-exact-union-test-namespaces/v3. The version bumps
invalidate older evidence that did not bind the repaired execution closure and candidate-only
namespace behavior.

The decision clock starts in a small POSIX supervisor before filesystem or Git discovery. One
owned worker has exactly five seconds to capture the authoritative index, materialize the exact
base/candidate configuration and their separate parser closures, execute the base parser, and
return a bounded policy frame. The supervisor validates that frame, requires a maximum of at
least five seconds, derives the absolute deadline, and lets the same worker continue freezing and
controller execution. Bootstrap freezing, materialization, sealing, and controller startup
consume the same configured maximum as tests and cleanup.

The controller uses separate cutoffs for component execution, cleanup, final validation, and
terminal delivery. Final validation runs in a killable bounded helper; a timeout blocks rather
than being deferred. The worker owns the supervisor socket, the controller gets a separate inner
socket, and components get neither. The controller sends an immutable decision claim through a
nonblocking, deadline-bounded channel. The worker validates that claim and brokers a distinct
terminal frame to the supervisor before the absolute deadline.

Only after the claim is frozen and sent does bounded budget-task filing begin. Filing may create
or refresh the investigation records, so a timeout records its mutation state as unknown rather
than falsely claiming that nothing changed. The report can describe that post-claim attempt, but
the decision digest excludes it. Receipt, report, stdout, and final commit-marker projection also
happen after the claim. This work may delay wall-clock return beyond the maximum, but it cannot
change the frozen decision, measured duration, or gate exit code. Publication failure can still
turn the command outcome into an error and leaves no reusable evidence. Missing frames, signals,
and contradictory exits are protocol errors. The normal v4 report includes the immutable
decision object and digest checked by the worker after controller exit.

Supervisor-static v4 reports use the same identified invocation clock for real elapsed time.
When timing or process facts cannot be observed, they are null or explicitly unavailable rather
than fabricated. Post-start failures include the worker-started fact plus process-group and
ownership-token cleanup attempts, results, and discovery completeness.

Once the supervisor has validated a policy frame, a later static timeout retains the candidate,
lane, target, maximum, policy, and semantic index facts already known. It freezes and flushes the
decision before cleanup and before a separately bounded budget-task filing attempt. A filing
timeout reports unknown mutation and cannot rewrite the claim. Pre-policy failures do not invent
those facts or file a policy-directed task.

Static duration is sampled once from the invocation clock at freeze time; the configured maximum
is never substituted for an observation. Reaching the validated absolute deadline proves the
target and maximum were exceeded even if the clock becomes unavailable, but unavailable or
contradictory elapsed time remains null and is not sent to the filer. Static stdout uses a
killable bounded writer child. Failed claim delivery returns a command error, still cleans the
worker, and skips filing; post-claim telemetry uses the same bounded mechanism. Timeout cleanup
sends `SIGKILL` and performs only nonblocking reap observation, so an uninterruptible writer
cannot recreate an unbounded wait after the delivery deadline.

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

Isolated test execution uses a fixed repository-independent fallback Git author and committer.
Exactly `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and
`GIT_COMMITTER_EMAIL` may be supplied by the caller; they survive the component allowlist and
remain part of the bound environment. Local or global Git configuration is never consulted as a
hidden execution input.

The whole decision interval is measured. Reversible routine work that cannot finish is reported
as deferred. Selected execution ends early enough to leave explicit bounded intervals for
process cleanup, final validation, and worker-to-supervisor terminal brokering; the old
half-second reserve was not enough in the observed 60.26752-second hook failure. Incomplete final
or critical work blocks. After the claim freezes, a target breach starts a bounded attempt to
create or refresh one non-blocking investigation task from canonical templates and append timing
evidence. The filer never stages or commits the result, and its outcome cannot alter the frozen
gate result. Post-claim filing and projection latency are not gate decision time.

Budget-task creation publishes every canonical file exclusively. It first claims a new task
directory, then uses hard-link or exclusive-create publication without replacement. Once any
canonical path exists, error handling never unlinks, removes, replaces, or recursively deletes
it: a partial state is reported truthfully as mutated and later scans require a valid reciprocal
request before treating the task as deduplicated evidence. Private scratch remains removable.

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
those repairs and test-only bridges for the old and new contracts. The focused deadline and
receipt repair passed its regression set, and an independent rereview approved it. The complete
candidate then passed an exact final run, and the unchanged normal commit hook reused that full
receipt. A fresh five-reviewer revision-bound panel is the remaining merge boundary. See
`worklog.md` for the chronology and `verification.md` for the exact commands, timings, failures,
and review verdicts.

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
