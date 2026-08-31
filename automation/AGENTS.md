# automation/ — things that run

This is the mechanical half of `handbook/principles/systems-over-instructions.md`.
Everything here executes, uses repository-local state, and stays Python-stdlib-only so
it works on a bare clone. Use each command's `--help` and tests for option-level behavior.

| Entry point | Contract |
|-------------|----------|
| `check_action_projection.py` | Bind external asks and task actions to live canonical queue items; PR-body shape findings are advisory. |
| `check_core_scope.py` | Gate core diffs on the task's portability receipt; `--require-review` validates a revision-bound independent receipt. |
| `core-scope-paths.txt` | Register thin adapter paths that belong to the core-scope gate. |
| `reconcile/reconcile.py` | Run repository invariants; regenerate indexes and file/clear generated retries through explicit flags. |
| `hooks/pre-commit` | Run core scope, reconciliation, and the staged test lane before each commit. |
| `install.py` | Idempotently configure the shared hooks path and the current worktree's agent-adapter symlinks; run it once per linked worktree, concurrently safe, failing closed on a stale link or a real local path. |
| `inspect_workspace_boundaries.py` | Report layered-workspace Git and capability boundaries without mutation. |
| `integrate.py` | `plan` pins and screens a landing set, `build` verifies it in `tmp/`, and `verify` proves the landed tree matches. |
| `mine_cochange.py` | Rank Markdown co-change candidates and append accepted/rejected evidence to the ledger. |
| `run_tests.py` | Run tests from an isolated repository-byte view; full is the default and `--staged` selects conservatively by input ownership. |

## Editing rules

- A new repository-state invariant needs a stable `CHECKS` id, the agent-facing rule in
  its owning contract, and tests. External artifact boundaries use a standalone gate and
  thin adapters. Retry filenames embed ids, so never casually rename one
  (`memory/lessons/automation/deterministic-finding-keys.md`).
- Register every new test input in `run_tests.py` ownership data or its owning group.
  Unknown or removed non-record inputs fall back to the full suite; never narrow that
  fallback. Keep quarantined-test reasons explicit.
- Admission adapters preserve exact candidate/base identities and pass transition data
  explicitly: use `--displaced-tip <full-oid>` when replacing a ref and
  `--at-transition <name>` at an external boundary. Fail closed when required evidence
  is unavailable.
- Queue, task, handover, and provider gates enforce the contracts in their owning
  `AGENTS.md` files. Preserve action identity, immutable historical records, plural task
  scope, and exact-tree/range evidence when changing an adapter.
- Generated retry reruns preserve claimed or rejected content and remove only the exact
  generated identity whose finding cleared. Never garbage-collect an untrusted lookalike.
- Agent/provider shims remain policy-free forwarders; personal installers and user-global
  state stay outside AgentFold (`templates/task/design.md`).
- Never weaken a check to pass; fix it or file the reason as a decision.
