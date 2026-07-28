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
path_globs = ["services/**"]
```

`target_seconds` and `maximum_seconds` are positive, finite numbers (booleans
do not count), and the target cannot exceed the maximum. A target breach is a
performance finding; reaching the maximum ends remaining work. The only
current breach action is `file-task`.

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
python3 automation/run_test_gate.py routine --staged
```

The routine gate runs core-scope admission, reconciliation, and the smallest
known owned test set. It reports selected, deferred, and incomplete coverage.
If reversible test work reaches the maximum, it is deferred to the final lane;
critical work and non-test admission work block instead.

For a critical staged change whose full suite cannot fit inside the routine
maximum, prewarm exact full-suite evidence before committing:

```bash
git add <candidate paths>
python3 automation/run_test_gate.py final --explicit --staged
git commit
```

The explicit final run uses the final-lane budget but captures the same semantic
index candidate as the hook. Git may refresh internal index stat/cache bytes when
`git commit` starts; those storage-only bytes are not candidate identity. The raw
index fingerprint is retained only to detect drift during one invocation. The
subsequent routine gate still runs admission and reconciliation inside its own
60-second interval, and reuses the full-suite receipt only if the staged object
ids, modes, paths, base, tested view, test manifest, policy, runner bytes, and
the digest of every caller variable admitted by the sanitized component
environment boundary are unchanged.
That digest includes every inherited `PYTHON*` setting, so interpreter behavior
such as `PYTHONPATH` cannot reuse evidence from a different environment.
Restaging changed content or topology invalidates that binding and requires
another prewarm; there is no override for missing critical evidence.

Run a complete final gate explicitly from a clean checkout:

```bash
python3 automation/run_test_gate.py final --explicit
```

Explicit prewarming and routine testing use an immutable staged index. The
parser retains exact-range arguments for the reserved future pull-request
adapter, but this repository blocks every named transition before candidate
execution.
In every case, tests run in a separately materialized view and the
report names both the candidate and tested-view digests. Source/index drift
during a run blocks reuse rather than treating another view as equivalent.
Tracked symlinks are rejected before materialization. Absolute, escaping,
dangling, and looping links could otherwise introduce bytes outside the Git
objects bound by the candidate and tested-view digests.

Complete final or critical testing is a two-lane composite, not a test list supplied solely by
the candidate. The base-pinned revision contributes an immutable anti-deletion floor: every discovered base
test plus every file in those tests' directories is copied from exact base Git objects over the
exact candidate product view. Only those reserved test directories are overlaid; a product file
deleted elsewhere by the candidate stays deleted. Deleting, renaming, emptying, or shadowing a
base test or helper therefore cannot remove the floor. Candidate-added or byte-changed tests run
afterward as supplemental evidence from a separate exact candidate view. Each lane still gives
every test file its own fresh sealed view and cleanup cycle.
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

The included workflow is the exact base-pinned manual snapshot. It keeps
`pull_request_target` action projection and adds a credential-free
`pull_request` complete-test diagnostic, but it contains no hard-gate job
triad, publisher environment, GitHub App credential, status-writing authority,
or required-check claim.

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

Every invocation prints a human summary and writes a machine-readable v2 report
under ignored `tmp/test-gate-reports/`. Its outcome has these exit codes:

The measured interval starts before argument/candidate discovery and is
re-accounted after report persistence, budget-task filing, and summary output.
If one of those finalization steps crosses the maximum, the runner persists the
stricter outcome, prints a final-outcome correction, and returns its blocking
exit code. The duration stored in any atomic report necessarily stops at the
measurement immediately before that particular persistence; later persistence
and output are included by the following accounting pass.

| Outcome | Exit code |
| --- | ---: |
| `pass`, `deferred`, or `not-run` | 0 |
| `blocked-failed` or `blocked-incomplete` | 1 |
| `invalid` or `error` | 2 |

Full-suite pass receipts are stored only in ignored
`tmp/test-gate-receipts/`. A receipt can be reused only when its exact candidate
and candidate-view fingerprints, base-pinned revision, immutable floor/support records,
supplemental records, overlay algorithm and floor-view digest, full manifests, policy digest,
runner revision, and Python/Git environment identity all match. Version 3 receipts bind the cooperative authority fields and invalidate
the earlier candidate-only evidence. A selected routine
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
sanitized environment evidence. Filing is best-effort: it never changes the
functional outcome, stages nothing, and does not require the tests to run a
second time. New records are rendered from the repository's canonical task and
request templates. The task body remains stable after filing; later occurrences
are bounded JSON records in task-local `timing-evidence.jsonl`, appended without
replacing actor-written task bytes. In a read-only checkout, the report records
the filing disposition instead of failing a successful gate. If the report path
itself is unwritable, the human summary says the machine report is unavailable
and preserves the gate's functional exit status.

## Compatibility

The runner supports CPython 3.7 or newer on POSIX and Windows clones. It uses
the standard library plus the pinned, policy-free Tomli 2.0.1 parser vendored
with the automation code;
no package installation is required to parse `agentfold.toml`. Evidence-journal
preservation assumes ordinary local-filesystem `O_APPEND` behavior: each bounded
record is issued in one write, then the pathname/inode and receipt are verified.
Network filesystems that do not preserve those semantics are outside the v1
portability claim; filing retries or aborts when verification fails.
