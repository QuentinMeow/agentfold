# Configurable test gates and time budgets

`agentfold.toml` is the repository-owned policy for the two test lanes. The
routine lane gives fast, bounded feedback for staged work; the final lane gives
complete evidence at an explicit or configured boundary. The gate runner is the
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
mode = "hard" # or "manual"
trigger = "pull-request" # required only for hard mode
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

There are exactly two final modes. `manual` omits `trigger` and runs only with
an explicit command. In schema version 1, `hard` requires the sole supported
trigger, `pull-request`. The runner knows how to verify that exact base/head
synthetic merge, but policy is not provider enforcement: an adopter must connect
it to independently controlled admission as described below. `task-review`,
`merge`, `merge-group`, and any other trigger are rejected because version 1
has no controlled adapter for them. Neither mode makes complete testing an
every-commit operation.

Risk bindings use relative POSIX path globs. Every policy must include each
critical category exactly once: `credentials-and-secrets`, `pii`,
`authorization`, `destructive-operations`, `external-publication`, and
`production-deployment`. Each has nonempty globs and one or more known check
ids: `core-scope`, `reconcile`, and/or **repository-tests/full**. Reversible
bindings have a unique kebab-case `id` and nonempty globs. A critical match
wins over a reversible match; unmatched paths are always critical.

The gate validates the policy before it runs. For a candidate that changes the
policy, it classifies paths against both the trusted base and candidate policy;
critical or unmatched in either one wins, the base hard boundary remains live,
and the smaller time limits apply. This prevents the policy change from weakening
the boundary that admits it. Policy identity is a SHA-256 of normalized policy
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

Run a complete final gate explicitly from a clean checkout (or provide a
revision range):

```bash
python3 automation/run_test_gate.py final --explicit
python3 automation/run_test_gate.py final --at-transition pull-request \
  --base-revision <base-commit> --head-revision <head-commit> \
  --candidate-revision <synthetic-merge-commit> \
  --branch task/<task-id>
```

Named transitions require that exact base, head, ordered two-parent synthetic
merge candidate, and branch. Transition final testing uses an immutable committed
range; explicit prewarming and routine testing use the immutable staged index.
In every case, tests run in a separately materialized view and the
report names both the candidate and tested-view digests. Source/index drift
during a run blocks reuse rather than treating another view as equivalent.
Tracked symlinks are rejected before materialization. Absolute, escaping,
dangling, and looping links could otherwise introduce bytes outside the Git
objects bound by the candidate and tested-view digests.

### Provider enforcement boundary

The included GitHub adapter is split across three trust zones. A
`pull_request_target` preparer checks out only the exact base revision, uses its
read-only repository token to fetch and verify the event's base, head, ordered
two-parent synthetic merge, and displaced tip, then uploads a one-run Git bundle
and SHA-256. It never checks out or executes candidate code. Every action in this
transfer boundary is pinned to a full commit SHA.

A fresh runner has `permissions: {}`, verifies the artifact digest and bundled
refs on the trusted host, then executes the base controller inside one one-shot
Docker container pinned by a full image digest. The container has no network,
host PID namespace, Docker socket, workspace, or home mount. Its root filesystem
and trusted inputs are read-only. Root-owned work and bounded scratch live on
tmpfs, resource limits are explicit, and an outer timeout plus validated cidfile
removes a surviving container.

The root judge has only KILL, SETGID, and SETUID capabilities with
no-new-privileges. It creates a fresh root-owned, non-writable view for each
test. Only the test child drops groups/GID/UID to 65532. Before loading candidate
code, a trusted probe requires UID/GID 65532, zero effective, permitted, and
ambient capabilities, and `NoNewPrivs: 1`. Each child receives a new writable
home and temporary directory. After every file the judge kills and reaps every
process with UID 65532 before creating the next view.

A final publisher also has `permissions: {}`, receives no bundle, checks out no
code, and enters only the protected `agentfold-trusted-publisher` environment. A
full-SHA-pinned token action mints a repository-scoped installation token for a
dedicated GitHub App with only Commit statuses write permission. That App posts
the stable `AgentFold trusted hard final gate` context on the exact synthetic
merge SHA. The publisher never uses `GITHUB_TOKEN`, so an ordinary Actions job
cannot satisfy protection configured for the dedicated App source.

The tracked adapter becomes hard enforcement only after this fail-closed setup:

1. Create a private GitHub App, install it only on this repository, and grant it
   Commit statuses read/write plus implicit Metadata read. Grant no Checks,
   Contents, Pull requests, Actions, Workflows, Deployments, or Issues write.
2. Create the repository environment `agentfold-trusted-publisher`. Set its
   deployment branch policy to selected branches with exactly `main` and no tag
   pattern. Store the client ID as the environment variable
   `AGENTFOLD_PUBLISHER_CLIENT_ID` and its private key only as the environment
   secret `AGENTFOLD_PUBLISHER_PRIVATE_KEY`.
3. Merge the pinned workflow through an explicitly reviewed, manually verified
   bootstrap change. Missing environment configuration, App installation,
   variable, key, token permission, image, or Docker capability fails closed;
   there is no Actions-token or direct-host candidate-execution fallback.
4. Open a diagnostic pull request and confirm the dedicated App publishes
   `AgentFold trusted hard final gate` on its current synthetic merge SHA.
5. Protect `main`: require pull requests and current branches; require that exact
   context with the dedicated App selected as source; prohibit direct pushes,
   force pushes, deletion, and every bypass.
6. Keep merge queues disabled. `merge_group` fails in the credential-free runner
   and intentionally never enters the main-only publisher environment.
7. Keep the default Actions token read-only, disable write tokens for fork pull
   requests, and disable Actions creating or approving pull requests.
8. Run canaries: a candidate workflow posting the same context through
   `GITHUB_TOKEN` must not satisfy protection; failed/skipped tests and stale
   merge SHAs must not satisfy it; candidate attempts to reach the network,
   Docker socket, host workspace/home/PIDs, future test views, or the root judge
   must fail.

The workflow and App environment must already exist on the trusted base revision,
so their introducing change cannot be protected by its future status. Until the
diagnostic status and App-selected protection rule both work, treat final
verification as manual regardless of configured target mode and do not describe
the repository as hard-enforced.

An adopter who needs another automatic boundary must first provide a controlled
adapter and introduce that trigger through a future schema version; the version
1 policy cannot select it. The runner's repository-local report keeps
`enforcement: unobserved`: it cannot inspect rulesets or prove that bypasses are
disabled. `explicit` and `transition` describe invocation, not enforcement. The
provider-bound exact-SHA App status plus the settings above establish the external
boundary; never reinterpret the JSON report alone as that proof.

## Results, receipts, and budget work

Every invocation prints a human summary and writes a machine-readable v1 report
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
and tested-view fingerprints, full test manifest, policy digest, runner
revision, and Python/Git environment identity all match. A selected routine
test result is not a reusable full receipt; a different index, working tree, or
commit is never covered by an earlier receipt.

Each selected test file receives a newly materialized metadata-free projection.
Writes made by one test process therefore cannot alter the source bytes supplied
to a later test and turn its failure into a pass.

Timeout cleanup always terminates the component process group and descendants
that remain observable through the portable process-tree/ownership mechanisms.
On Linux, the gate additionally becomes a child subreaper, so double-forked,
new-session descendants remain contained after re-exec and environment scrubbing.
`--provider-hard` refuses to start candidate-controlled components unless that
strong Linux containment is available. Local gates remain usable elsewhere, but
their report records `portable-process-group` with
`detached_descendants: best-effort`; it is not evidence of hostile
detached-process containment.

These JSON receipts are a cooperative same-user optimization, not an
authorization artifact. Another process with the same workspace account can
forge or replace ignored local state; directory and file hardening prevents
accidental path redirection, not same-user malice. A `--provider-hard` run
therefore neither reads nor writes local receipts. Provider admission must use
the provider-bound job/check result for the exact candidate, never a JSON file
supplied by the repository or candidate.

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
