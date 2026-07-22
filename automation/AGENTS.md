# automation/ — things that run

The mechanical half of `handbook/principles/systems-over-instructions.md`: everything
here executes; nothing here is advice. Python stdlib only — automation must run on a
bare clone.

| Piece | What it does | Runs |
|-------|--------------|------|
| `check_core_scope.py` | gates core diffs on substitution evidence and repo-local state; `--require-review` validates a revision-bound manual review receipt | pre-commit, PR CI, on demand |
| `core-scope-paths.txt` | registers thin agent/provider adapter files whose changes need the same core-scope check | read by the core-scope gate |
| `reconcile/reconcile.py` | checks every harness invariant; `--file-retries` turns findings into repair items in `message-queue/needs-agent/retries/` and garbage-collects fixed ones; `--fix-index` regenerates `memory/index.md` | pre-commit (`--check`), CI, on demand |
| `hooks/pre-commit` | blocks commits when core scope, repository invariants, or tests fail | every commit (installed) |
| `install.py` | idempotent setup: git hooks path, agent-adapter symlinks (`CLAUDE.md` shims, skill dirs) | once per clone |
| `run_tests.py` | runs test files under services, canonical skills, and automation | pre-commit, CI, on demand |

Rules:

- A new invariant = a new entry in the `CHECKS` registry in `reconcile.py` + the rule
  stated where agents will read it (folder contract or template). Check ids are stable
  — retry-item filenames embed them (`memory/lessons/automation/deterministic-finding-keys.md`).
- Adopters deleting a harness folder delete its checks — the registry is a plain dict,
  and every check no-ops when its folder is absent.
- Tracked executables use repository-local state only. Agent/provider shims are thin,
  optional, policy-free forwarders to canonical behavior; personal installers stay
  outside AgentFold (`templates/task/design.md` carries the core-fit receipt).
- Never weaken a check to make a commit pass; fix the finding or file the reason as a
  decision.
