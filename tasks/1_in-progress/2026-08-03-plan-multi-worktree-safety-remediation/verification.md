# Verification — multi-worktree safety remediation plan

**Verified:** 2026-08-31 by codex

Only commands actually run and their real output are recorded here. This verifies the
records-only design candidate; it does not verify the deferred behavior changes or
disposable workflow scenarios.

## Initial repository regression suite

This run preceded the final source-link and exact-byte-evidence repair. It is retained as
real history but is not the final candidate-bound result.

```
$ python3 automation/run_tests.py --verbose
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 16/16 files passed
test elapsed: 52.40s
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
```

The six advisories predate this candidate: five describe line continuations in two frozen
human decisions, and one groups nine older questions that cannot be rewritten in place.

## Staged-path gate

```
$ python3 automation/check_core_scope.py --staged
core-scope: no core changes (independent review manual; not invoked)
$ python3 automation/run_tests.py --staged --verbose
test lane: staged
test reason: every staged path is a record path no test reads
selected test files:
  (none)
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.01s
```

The `0/0` result is an explicit empty selection, not evidence that a test exercised these
records; the complete suite above is the repository-wide regression check.

## Initial clean Git clone

This branch-named clone preceded the final repair. It proved clean-clone discovery for that
draft, not immutable binding for the final candidate.

```
$ git clone --no-local --branch agents/2026-08-31-prove-and-land-the-common-8dba/parent-design /Users/quentinmiao/code/agentfold /private/tmp/agentfold-git-clone.yEORUx
Cloning into '/private/tmp/agentfold-git-clone.yEORUx'...
$ python3 automation/install.py
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 16/16 files passed
test elapsed: 52.13s
```

## Final candidate-bound clean clone

The empty lines after `git replace -l` and `git status --porcelain=v1` are the commands'
real output: no replace ref and no dirty byte were present. The immutable commit and tree
printed before bootstrap are the bytes tested below.

```
$ git clone --no-local --branch task/2026-08-03-plan-multi-worktree-safety-remediation /Users/quentinmiao/code/agentfold /private/tmp/agentfold-integration-clone.Xw8o9o
Cloning into '/private/tmp/agentfold-integration-clone.Xw8o9o'...
$ git checkout --detach e0d2a70ef31efb09779ec5cb8f13686ffd22e6a9
HEAD is now at e0d2a70 Make candidate evidence replay resistant
$ git rev-parse HEAD
e0d2a70ef31efb09779ec5cb8f13686ffd22e6a9
$ git rev-parse HEAD^{tree}
bbd00d6de9ee62c4798af0eec86fea4c0489c495
$ git replace -l
$ git status --porcelain=v1
$ python3 --version
Python 3.14.6
$ git --version
git version 2.55.0
$ uname -srm
Darwin 25.5.0 arm64
$ python3 automation/install.py
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 16/16 files passed
test elapsed: 50.67s
```

## Final five-lens fresh-context panel

Every reviewer received only the pass criteria, verbatim requirements, and raw diff emitted
by `verify.sh`; no worker rationale or earlier verdict was supplied.

```
$ /Users/quentinmiao/code/dotagents/skills/agent-orchestration/scripts/verify.sh --diff '8e24d09^..9e78d85' --request /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-and-land-the-common-8dba/requirements.md --criteria tmp/orchestration/2026-08-31-prove-and-land-the-common-8dba/verification-criteria.md --repo /Users/quentinmiao/.codex/worktrees/162f/agentfold
```

**Reviewed candidate:** `e0d2a70ef31efb09779ec5cb8f13686ffd22e6a9`, tree
`bbd00d6de9ee62c4798af0eec86fea4c0489c495`. The verifier command consumed the raw
diff from isolated unit revision `9e78d8598f373140d0abd186c4b3e215543d88b6` before integration. The following
mechanical check proves the integrated candidate has exactly the reviewed bytes; the empty
`git diff` output is the real result.

```
$ git rev-parse e0d2a70^{tree}
bbd00d6de9ee62c4798af0eec86fea4c0489c495
$ git rev-parse 9e78d85^{tree}
bbd00d6de9ee62c4798af0eec86fea4c0489c495
$ git diff --exit-code 9e78d85^{tree} e0d2a70^{tree}
```

- requirements / fresh Sol xhigh: `approve` — 8/8 criteria; design/research completion and deferred implementation are separated.
- repository contract / fresh Sol xhigh: `approve` — the exact start boundary, reciprocity, immutable records, and current cardinality contract are consistent.
- human workflow and product effect / fresh Sol xhigh: `approve` — ten cycles and the practical Vibe, Beads, harness, Claude, and Codex tradeoffs are actionable.
- evidence and verifiability / fresh Sol xhigh: `approve` — sources are dated; empty test selection is honest; single-use authenticated receipts reject same-candidate replay.
- adversarial blast radius / fresh Sol xhigh: `approve` — unknown liveness refuses takeover, adapters cannot dual-write authority, and self-evolution cannot approve itself.

## Cross-provider refuter

`DID NOT RUN` — the installed Claude CLI was discovered, but sending candidate repository
bytes to another service is a separate publication boundary that the owner has not
authorized. The attempted invocation was rejected before execution; no candidate bytes were
sent. The five native fresh-context verdicts above are not presented as cross-provider
diversity.
