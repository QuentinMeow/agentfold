# Configurable test gates and time budgets

`agentfold.toml` is the repository-owned policy for the two test lanes. The
routine lane gives fast, bounded feedback for staged work; the final lane gives
complete evidence only when a maintainer runs it explicitly. The gate runner is the
[test-gate runner](../automation/run_test_gate.py).

## Policy schema

The current schema is version 1 and is deliberately closed: unknown tables and
keys are errors, rather than ignored future settings. Start from the tracked
[`agentfold.toml`](../agentfold.toml) and retain all required tables:

```toml
schema_version = 1

[testing.routine]
target_seconds = 60
maximum_seconds = 60
service_dependencies = { quote-api = ["quote-cli"] }

[testing.final]
mode = "manual"
target_seconds = 300
maximum_seconds = 900

[testing.performance]
on_budget_exceeded = "file-task"

[testing.risk]
unmatched = "critical"

[[testing.risk.critical]]
category = "credentials-and-secrets"
path_globs = ["**/*secret*"]
required_check_ids = ["core-scope", "reconcile", "repository-tests/full"]

[[testing.risk.reversible]]
id = "ordinary-repository-work"
path_globs = ["services/quote-api/quote_api.py"]
```

`target_seconds` and `maximum_seconds` are positive, finite numbers (booleans
do not count), every maximum is at least 5 seconds, and the target cannot exceed the maximum. A target breach is a
performance finding; reaching the maximum ends remaining work. The only
current breach action is `file-task`.

The maximum is an absolute decision deadline. A small supervisor starts the cross-process
clock before filesystem or Git discovery. It rejects reserved hard syntax, then starts one
owned worker. That worker gets exactly 5 seconds to capture one authoritative candidate index,
materialize `agentfold.toml` and the parser/Tomli closure from both that index and the exact base
revision, and return a size-capped policy frame. Only the trusted base parser runs during this
discovery; it parses both configuration files and applies the stricter union. The candidate
parser is recorded but cannot execute while the worker holds the supervisor channel. The
supervisor checks the frame and derives the absolute deadline from the smaller base/candidate
maximum. A configured maximum of exactly 5 seconds is valid; a smaller one is not.

The same worker reuses that authoritative index for freezing, materialization, sealing,
controller planning, and tests; it never recaptures the candidate after policy discovery.
The decision interval continues through component execution, cleanup, bounded final validation,
and the one terminal outcome claim. Separate cutoffs reserve time for each of those stages. Final
validation runs in a killable helper; a timeout blocks rather than being deferred. The worker
retains the outer supervisor socket and gives the controller a distinct inner socket; the
controller and test components never receive the outer descriptor, and components receive
neither descriptor. The controller sends its immutable decision claim over a nonblocking,
deadline-bounded channel. After validating the claim, the worker brokers a distinct terminal
frame to the supervisor. Both sends must finish before their cutoffs, and the supervisor frame
must arrive strictly before the absolute deadline; arrival at the deadline is late. Missing,
malformed, oversized, or late frames block, even if the worker exits zero.

Only after the claim is frozen and sent does the controller attempt budget-task filing and
evidence projection. Budget filing has its own bound and is best-effort. If it times out after a
write may have started, the report records the mutation state as unknown instead of claiming that
nothing changed. Filing and projection cannot change the frozen gate decision, its measured
duration, or its gate exit code. Publication failure can still make the overall command return an
error and prevents receipt reuse. Slow external projection I/O may therefore make wall-clock
return exceed the maximum without changing the already-frozen gate result.

If the worker itself misses the absolute boundary, the supervisor freezes and flushes a static
blocked decision with the already-validated policy digest, target, maximum, candidate-index
identity, and elapsed time sampled from the invocation clock at the freeze boundary. If that
measurement is unavailable or contradicts the proven deadline crossing, duration is null rather
than replaced by the configured maximum. A killable writer gives the static claim a separate
bounded delivery attempt; failure returns command error 2, always cleans the worker, and does not
file because the claim was not sent. After successful delivery, cleanup, timing-task filing, and
human telemetry have separate bounds and cannot rewrite the frozen decision. A timeout before a
valid policy frame has no authoritative budget or candidate identity, so it does not guess either
value or invoke the filer.

The supervisor samples `CLOCK_MONOTONIC` with `clock_gettime` and hands that source,
start value, and absolute deadline to the worker and controller, so freezing and startup time cannot
disappear across `exec`. On POSIX systems lacking that Python clock API, it falls
back to the monotonic elapsed field from `os.times()`. A source mismatch, rollback,
invalid value, or unavailable source blocks the gate. On a missed terminal boundary it kills
the worker process group and also searches for same-user descendants carrying the invocation's
unguessable ownership token. This exact-token escapee cleanup is honest POSIX containment, not
a claim of kernel-enforced isolation: process discovery can be incomplete, especially without
Linux `/proc`, and the gate fails closed when it cannot establish required completion.

There are exactly two final modes. The starter uses `manual`, omits `trigger`,
and runs only with an explicit command. Schema version 1 reserves `hard` with
the sole syntax `trigger = "pull-request"` so future installations do not need
a policy migration. This repository does not include the controlled completion
oracle or independently controlled publisher needed to execute that transition.
Every named transition and every `--provider-hard` invocation therefore fails
closed before candidate-controlled code runs. `task-review`, `merge`,
`merge-group`, and other trigger names remain invalid. Neither mode makes
complete testing an every-commit operation.

Risk bindings use relative POSIX path globs. Every policy must include each
critical category exactly once: `credentials-and-secrets`, `pii`,
`authorization`, `destructive-operations`, `external-publication`, and
`production-deployment`. Each has nonempty globs and one or more known check
ids: `core-scope`, `reconcile`, and/or **repository-tests/full**. Reversible
bindings have a unique kebab-case `id` and nonempty globs. A critical match
wins over a reversible match; unmatched paths are always critical.

Risk classification is path-based ownership, not semantic analysis. A reversible glob is an
affirmative claim that changes to every matched path are eligible for deferred coverage. Avoid
broad executable-root globs such as `services/**` or `automation/**`; enumerate known-reversible
files or narrow subtrees so newly introduced paths fail closed. If an ordinary file gains
credential, authorization, destructive, publication, deployment, or PII responsibility, add its
critical binding in the same candidate. The base/candidate policy union then applies the stricter
classification to that change. The starter treats `agentfold.toml` and the complete test-gate
execution, parser, hook, filing, and manifest closure as authorization-sensitive control-plane
paths.

`testing.routine.service_dependencies` is a closed map from a lowercase kebab-case service name
to downstream services whose tests must also run. Any path under `services/<name>/` owns tests
under `services/<name>/tests/` without an automation-code change; dependencies are followed
transitively. Base and candidate dependency edges are unioned, so a policy edit cannot remove
coverage from the candidate that edits it.

The gate validates the policy before it runs. For a candidate that changes the
policy, it classifies paths against both the base-pinned and candidate policy;
critical or unmatched in either one wins, and the smaller time limits apply.
This prevents a policy change from weakening the coverage checked by that run.
Policy identity is a SHA-256 of normalized policy
JSON, so comments, table order, and numeric spelling do not affect it.

## Running the lanes

The installed pre-commit hook invokes the routine lane. It needs staged content
because it tests an immutable copied Git index, not the live working tree:

```bash
python3 -I -S automation/run_test_gate.py routine --staged
```

Use that isolated, no-site interpreter form for every direct gate invocation. The
small supervisor is standard-library-only and checks raw arguments before it imports
any candidate-controlled module. Reserved automatic transitions and
`--provider-hard` therefore fail before Git discovery, configuration loading,
candidate imports, reports, receipts, or budget-task state are read.

The routine gate runs core-scope admission, reconciliation, and the smallest
known owned test set. It reports selected, deferred, and incomplete coverage.
If reversible test work reaches the maximum, it is deferred to the final lane;
critical work and non-test admission work block instead.

For a critical staged change whose full suite cannot fit inside the routine
maximum, prewarm exact full-suite evidence before committing:

```bash
git add <candidate paths>
python3 -I -S automation/run_test_gate.py final --explicit --staged
git commit
```

The explicit final run uses the final-lane budget but captures the same semantic
index candidate as the hook. Git may refresh internal index stat/cache bytes when
`git commit` starts; those storage-only bytes are not candidate identity. The raw
index fingerprint is retained only to detect drift during one invocation. The
subsequent routine gate still runs admission and reconciliation inside its own
60-second interval, and reuses the full-suite receipt only if the staged object
ids, modes, paths, base, tested view, test manifest, policy, runner bytes, and
the sanitized component-environment identity are unchanged. Inherited `PYTHON*`
settings are removed; fixed isolated/no-site interpreter flags and the remaining admitted
environment are bound instead. Caller-supplied `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`,
`GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` values pass through the component boundary and
remain bound.
When they are absent, the test runner supplies a fixed `AgentFold Tests` identity rather than
reading repository-local or user-global Git configuration, so those untracked settings cannot
silently change a cached test execution.
Restaging changed content or topology invalidates that binding and requires
another prewarm; there is no override for missing critical evidence.

Run a complete final gate explicitly from a clean checkout:

```bash
python3 -I -S automation/run_test_gate.py final --explicit
```

Explicit prewarming and routine testing use one immutable snapshot. Bounded policy discovery
captures the authoritative index once; the same owned worker seals and reuses it, materializes
the controller from those staged objects, and hands both to that controller. The report records the supervised
launcher identity separately from the isolated child-interpreter identity. Each
component gets a disposable copy of the sealed index and a sanitized Git/Python
environment; mutations block the run and receipt rather than changing what a later
component executes. Forced supervisor termination may leave system-temporary snapshot files for
the operating system to reap, but it cannot publish a reusable receipt without a timely terminal
decision.

The parser retains exact-range arguments for a future pull-request adapter, but
this repository blocks every named transition before candidate execution. In every
allowed run, tests use separately materialized views and the report names both the
candidate and tested-view digests. Source, index, controller-closure, interpreter,
or admitted-environment drift blocks reuse rather than treating another execution
as equivalent.
Tracked symlinks are rejected before materialization. Absolute, escaping,
dangling, and looping links could otherwise introduce bytes outside the Git
objects bound by the candidate and tested-view digests.

Complete final or critical testing is a two-lane composite, not a test list supplied solely by
the candidate. The base-pinned revision contributes an immutable anti-deletion floor: every
discovered base test plus every file in those test namespaces is copied from exact base Git
objects over the exact candidate product view. Only those reserved namespaces are overlaid; a
product file deleted elsewhere by the candidate stays deleted. Deleting, renaming, emptying, or
shadowing a base test or helper therefore cannot remove the floor. Candidate-added or
byte-changed tests run afterward as supplemental evidence from a separate exact candidate view.
Candidate-only test namespaces are included in that supplemental lane, so moving new tests under
a new directory cannot hide them. Each lane still gives every test file its own fresh sealed
view and cleanup cycle.
When only test files change, that lane runs exactly the changed or added candidate tests; if any
non-test helper, fixture, path, mode, or byte changes beneath a base-pinned test namespace, it reruns
every candidate test in that namespace.

This cooperatively checks backwards-compatible two-stage API changes. First merge the new
product behavior while the old API still works, together with the new or updated tests. Once
that revision becomes the base-pinned floor, a later pull request may remove the deprecated API;
its floor now contains the updated tests. A one-step incompatible product-and-test rewrite is
reported as failed when the older base-pinned tests reach their assertions against the candidate
product. This compatibility check is not proof that every assertion completed and cannot reject
or admit a protected transition.

### Automatic enforcement is intentionally unavailable

The included workflow has three visible, non-enforcing diagnostics: push repository
diagnostics, trusted pull-request core/merge diagnostics, and cooperative pull-request
complete tests. It also retains the separate action-projection machinery. None of these
jobs is a hard-gate publisher: the workflow contains no publisher environment, GitHub App
credential, status-writing authority, or required-check claim. A candidate workflow file
also cannot prove which workflow or branch/ruleset policy the provider actually used, so
provider configuration must be inspected independently at the relevant time.

The base-pinned test floor prevents a candidate from deleting or replacing the
older test files and directory-local support bytes. It does not establish
controlled completion: those tests import candidate Python in the same
interpreter, and candidate code can terminate that interpreter with a zero exit
status before the trusted assertions finish. Candidate supplemental tests share
the same limitation and cannot upgrade the result.

Accordingly, explicit final reports and receipts say
`evidence_authority: cooperative-same-interpreter`,
`controlled_completion: false`, `enforcement_eligible: false`, and
`enforcement: not-enforced`. They are useful inputs to a maintainer's manual
judgment and exact-evidence cache, never authorization for an automatic merge or
other protected transition.

Automatic enforcement requires both follow-up projects: a protected process
that owns completion assertions and never imports candidate bytes, and an
external OIDC publisher whose signing key and replay state are outside the
candidate-controlled repository. Until both are installed and independently
verified, keep final mode manual.

## Results, receipts, and budget work

Every invocation attempts to print a human summary and write a machine-readable v4 report
under ignored `tmp/test-gate-reports/`. Its outcome has these exit codes:

The measured decision interval starts at invocation and covers bootstrap, component work,
cleanup, final validation, and the terminal claim. The gate freezes and sends that claim before
it files a timing investigation or projects results. Filing and publication occur outside the
measured decision interval and cannot change its decision, duration, or gate exit code. The
publication commit marker is atomically written last and attests that the required earlier
projections succeeded. A receipt, report, stdout, or marker failure makes the command return an
error and prevents reuse, while leaving the frozen gate result intact.

| Outcome | Exit code |
| --- | ---: |
| `pass`, `deferred`, or `not-run` | 0 |
| `blocked-failed` or `blocked-incomplete` | 1 |
| `invalid` or `error` | 2 |

The table maps the frozen gate outcome to `gate_exit_code`. The command normally
returns that code. If post-freeze publication fails, `command_outcome` becomes
`error` and the command returns 2 while the gate outcome and gate exit code remain
unchanged; the incomplete publication is not reusable. Signal exits, a zero exit without a
terminal frame, and any worker/controller exit that contradicts the frozen gate exit are
protocol errors and return 2. Each normal v4 report carries the frozen decision object and its
digest, which the worker verifies after the controller exits.

When the supervisor must return a static v4 result instead, it reports elapsed time from the
same invocation clock when that measurement remains available; otherwise the value is null. It
also records whether a worker started and whether process-group and ownership-token cleanup were
attempted, their observed results, and whether token discovery was complete, best-effort, or
unavailable. Deadline crossing still proves the target and maximum were exceeded when duration is
unavailable. A post-start timeout never reports zero duration or claims that no process started.

Full-suite pass receipts are stored only in ignored
`tmp/test-gate-receipts/`. A receipt can be reused only when its exact candidate
and candidate-view fingerprints, base-pinned revision, immutable floor/support records,
supplemental records, overlay algorithm and floor-view digest, full manifests, policy digest,
controller closure, disposable-index identity, and controller/child Python and Git environment
identity all match. Version 6 receipts bind the v2 handoff protocol, both configured lane budgets,
base and candidate config digests, normalized policy, launcher, separate trusted and candidate
parser closures, the authoritative candidate-index identity, controller
closure, and execution inputs. They deliberately do not bind an invocation's absolute clock values,
so otherwise exact evidence remains reusable across different start times. A v6 receipt requires
the matching terminal v4 pass report and the
matching v1 publication commit marker written last. The marker binds both file digests, their
paths, publication id, candidate identity, and authority. A missing or mismatched member makes
the evidence ineligible; older receipts and earlier overlay plans are invalid. A selected routine
test result is not a reusable full receipt; a different index, working tree, or
commit is never covered by an earlier receipt.

Each selected test file receives a newly materialized metadata-free projection.
Writes made by one test process therefore cannot alter the source bytes supplied
to a later test and turn its failure into a pass.

Timeout cleanup always terminates the component process group and descendants
that remain observable through the portable process-tree/ownership mechanisms.
On Linux, the gate additionally becomes a child subreaper, so double-forked,
new-session descendants remain contained after re-exec and environment scrubbing.
Local gates remain usable on supported hosts, and
their report records `portable-process-group` with
`detached_descendants: best-effort`; it is not evidence of hostile
detached-process containment.

These JSON receipts are a cooperative same-user optimization, not an
authorization artifact. Their binding includes the evidence authority,
controlled-completion state, and enforcement eligibility; an older receipt or
one missing those exact fields is invalid. Another process with the same workspace account can
forge or replace ignored local state; directory and file hardening prevents
accidental path redirection, not same-user malice. A `--provider-hard` request therefore fails closed before discovery,
preflight, candidate execution, or receipt access. The retained isolation and
cleanup helpers are defense in depth for cooperative local execution; they do
not create a provider enforcement boundary.

When elapsed time is above the target, the runner tries to file or refresh one
non-blocking investigation task and pickup request with timing components and
sanitized environment evidence. This happens only after the terminal claim has been
frozen and sent. Filing is bounded and best-effort: it never changes the functional
outcome, stages nothing, and does not require the tests to run a second time. New
records are rendered from the repository's canonical task and request templates. The
task body remains stable after filing; later occurrences are bounded JSON records in
task-local `timing-evidence.jsonl`, appended without replacing actor-written task
bytes. Initial task and request publication uses no-replace creation. Once any canonical path is
created, a later failure never deletes or rolls it back by pathname: the filer reports the real
mutation and leaves the partial pair visible rather than risking another actor's replacement.
An open backlog task is refreshed only while its reciprocal generated pickup request is still
present and valid. In a read-only checkout, the report records the filing disposition instead of
failing a successful gate. A filing timeout records an unknown mutation state because
the helper may have started a write. If the report path itself is unwritable, the human
summary says the machine report is unavailable and preserves the gate's functional
exit status.

## Compatibility

The runner supports CPython 3.7 or newer on POSIX. Windows is unsupported because
the gate depends on POSIX process-containment and cross-process monotonic-clock
primitives; no Windows cleanup or budget-boundary claim is made. The runner uses
the standard library plus the pinned, policy-free Tomli 2.0.1 parser vendored
with the automation code;
no package installation is required to parse `agentfold.toml`. Evidence-journal
preservation assumes ordinary local-filesystem `O_APPEND` behavior: each bounded
record is issued in one write, then the pathname/inode and receipt are verified.
Network filesystems that do not preserve those semantics are outside the v1
portability claim; filing retries or aborts when verification fails.
