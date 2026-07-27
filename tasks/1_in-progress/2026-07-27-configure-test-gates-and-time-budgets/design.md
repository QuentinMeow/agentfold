# Design notes — configurable test gates and time budgets

**Status:** decided
**Authorization:** `memory/decisions/2026-07-27-trusted-pull-request-gate-boundary.md`

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
automatic at a schema-supported final-stage boundary backed by a controlled adapter. Preserve
honesty by reporting deferred coverage, and require stronger behavior for one-way-door scopes.
This is the recommended option.

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
and provider workflows. The tracked `agentfold.toml` is the schema example and starter policy;
automation validates it with vendored Tomli 2.0.1 so Python 3.7 and bare clones need no installed
dependency.

The schema is closed and versioned. Unknown tables and keys fail rather than being ignored.
Routine and final targets each have a positive finite `target_seconds` investigation threshold
and a positive finite `maximum_seconds` execution ceiling, with target no greater than maximum;
booleans do not count as numbers. The starter routine target and maximum are both 60 seconds.
The starter final target is 300 seconds and its maximum is 900 seconds. Exceeding a target files
performance work but does not turn functional success into failure. Reaching a maximum stops
cleanly: routine reversible work becomes explicitly deferred, while incomplete final or critical
work blocks a hard boundary.

Final mode has exactly two values. `manual` omits a trigger and runs only by explicit command.
In schema version 1, `hard` requires the sole supported trigger, `pull-request`, and blocks it
on functional failure or incomplete required evidence only through a provider-controlled
adapter. The included GitHub adapter has three trust zones: a base-code, read-only-token
preparer verifies and bundles exact Git identities; a fresh `permissions: {}` runner verifies
the artifact and executes the base controller in a digest-pinned, no-network, read-only Docker
boundary; and a protected-environment publisher uses a statuses-only dedicated GitHub App token
to create `AgentFold trusted hard final gate` on the exact synthetic merge. Inside the container,
a root judge with only KILL, SETGID, and SETUID creates root-owned immutable per-test views. Only
candidate test children run as UID 65532 with zero active capabilities and no-new-privileges;
candidate-UID processes are killed and reaped after every file. The publisher has
`permissions: {}`, receives no candidate artifact, and can mint the token only through the
main-restricted `agentfold-trusted-publisher` environment. The status becomes enforcement only
when protected-branch policy requires its exact context and dedicated App source, requires a
current branch, and prohibits direct pushes and bypasses. The repository-local report remains
`unobserved` because it cannot prove those provider settings.
Other automatic boundaries require both a controlled adapter and a future schema version;
version 1 rejects their trigger names rather than claiming enforcement it cannot provide.
Neither mode turns complete verification back into an every-commit gate. The only initial
budget-breach action is `file-task`.

Risk policy is a set of executable path bindings, not category labels or semantic detectors.
Every critical binding names one of the six mandatory categories, one or more relative POSIX
path globs, and one or more known check ids from `core-scope`, `reconcile`, and
**repository-tests/full**. Reversible bindings separately name known ordinary repository scopes.
A critical match wins over a reversible match, multiple critical matches union their required
checks, and a path matching neither class is critical. The first implementation does not claim
that filename globs detect secret, privacy, authorization, destructive, publication, or
deployment semantics; semantic detectors and derived assurance remain separate future work.

The parser normalizes validated policy into sorted, separator-minimized JSON and identifies it
by that JSON's SHA-256 digest. Formatting, comments, and table order therefore do not change the
policy identity, while a semantic setting does.

Admission evaluates both the trusted base policy and candidate policy before accepting a policy
change. Critical and reversible bindings are unioned for reporting, but each path is classified
against both complete policies: critical or unmatched in either one wins. Thus a candidate cannot
delete a critical glob, add a reversible glob, switch `hard` to `manual`, remove the supported
hard boundary, or raise a time ceiling to weaken the boundary evaluating that same candidate.
The base hard boundary remains live and the smaller base/candidate time limits apply at this
admission edge.

### Gate sequencing

The routine sequence is: start the monotonic end-to-end clock; identify the candidate bytes and
risk class; validate the policy;
run core-scope admission; run an incremental reconciler; select affected pure tests and a small
integration smoke set; then report the result and deferred coverage. The target measures from
before candidate/config discovery through subprocess cleanup and the final report, so setup,
policy loading, selection, termination, and reporting time cannot be hidden outside the budget.

At the configured maximum, reversible remaining work is terminated cleanly or not started and
is transferred to the final manifest. A critical obligation is never converted into a pass or a
defer solely to satisfy the clock: its protected transition blocks until complete evidence
exists.

When a critical staged candidate's complete suite cannot fit inside the routine maximum, an
explicit `final --staged` invocation may prewarm the full-suite receipt under the final budget.
The commit hook still performs candidate-bound admission and reconciliation, and accepts that
receipt only for the byte-identical staged closure, tested view, full manifest, policy, runner,
and environment. This is a supported sequencing path, not a bypass: any restaged byte invalidates
the receipt and missing exact evidence blocks the critical commit.

The final sequence consumes the deferred manifest, runs every required complete test and guard,
and writes a content-bound receipt. Local gates test an isolated projection of the selected
working-tree bytes; Git and provider boundaries test the exact candidate tree named by that
boundary. The result names which view was tested. A mixed or changed view fails closed instead
of producing reusable evidence.

Complete final and critical testing uses an immutable trusted-base floor plus a candidate
supplemental lane. Exact base tests and their directory-local helpers/fixtures are overlaid only
onto those reserved test namespaces in an exact candidate product view. Candidate product
deletions outside those namespaces remain deleted. Candidate-added or changed tests run
separately afterward. Receipts bind the base revision, exact floor/support and supplemental
records, overlay algorithm, both tested views, manifests, policy, runner, and environment. This
means incompatible API changes use two merges: introduce compatibility plus updated tests, then
remove the old API only after those tests have become the trusted floor.

The GitHub hard path is further restricted to same-repository `task/**` pull requests on
`opened` or verified fast-forward `synchronize`. Prepare, run, and publish share that condition;
a synchronize must identify a nonzero prior head that is a strict ancestor of the current head.
Metadata events and history rewrites cannot replace success. Activation therefore also requires
source-branch protection against force-push, deletion, and bypass. Forks and merge queues remain
manual boundaries.

### Avoiding duplicate work

A successful local gate receipt may be reused only when the exact tested-view fingerprint, selected or
full test manifest, canonical config digest, runner revision, and relevant interpreter/Git
identity plus the digest of every caller variable admitted by the sanitized component
environment boundary all match. Any
mismatch, including `PYTHONPATH`, reruns the affected gate. Each test file runs from a fresh
materialization so an earlier test cannot rewrite a later test's inputs. This prevents the common waste of
manually running the full suite and then immediately running the same suite again in a commit or
final transition, without allowing a receipt for working-tree bytes to stand for different index
or commit bytes. Ignored JSON receipts are cooperative same-user cache entries rather than
authorization evidence. Provider-hard runs ignore them and rely on provider-bound results for
the exact candidate, because a repository process could forge local ignored state.

Linux provider-hard execution additionally requires child-subreaper process containment; the
adapter refuses to execute candidate components when that strong boundary is unavailable. Local
gates on other supported hosts retain portable process-group cleanup and report detached-child
cleanup as best-effort rather than claiming containment they cannot provide.

### Automatically filing time regressions

Every gate records monotonic wall-clock duration by component. If elapsed time is greater than
its configured target, the runner invokes one deterministic budget-task filer. Its identity is
the gate name plus the stable budget/config identity, not the date or run number.

The generated task contains the target, actual duration, candidate fingerprint, component
breakdown, environment summary, and the command or trigger. It also creates the required
non-blocking pickup request. A later run updates the generated evidence block of the same open
task while preserving human/agent notes. If the prior task is done and the regression returns,
the filer creates a new dated task linked to the previous one.

The filer may create files in a writable checkout, but it never stages or commits them. Its task
and pickup request are non-blocking records: filing failure or unstaged generated files are
reported but do not change the gate's functional result or force a second commit attempt. The
exact test receipt remains reusable, so later recording work does not repeat the slow suite.
Read-only environments emit the same finding as machine-readable output for a thin provider
adapter rather than pretending a task was filed.

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
**Provider substitution:** pass — local gates work without CI; another provider can replace the thin GitHub adapter while preserving the version 1 pull-request boundary, and any future boundary still requires a controlled adapter
**Repository substitution:** pass — adopted repositories need fast feedback, configurable final assurance, and performance-regression work without inheriting AgentFold's exact test suite
**User-global writes:** none
**Why AgentFold core:** this defines the portable relationship between local feedback, final assurance, repository policy, and durable task filing rather than a personal optimization or example-service behavior
**Thin adapter:** canonical=automation/run_test_gate.py; optional=yes; policy=none; writes=repo-only
