# automation/ — things that run

The mechanical half of `handbook/principles/systems-over-instructions.md`: everything
here executes; nothing here is advice. Python stdlib only — automation must run on a
bare clone.

| Piece | What it does | Runs |
|-------|--------------|------|
| `check_action_projection.py` | binds provider asks and task actions to live canonical queue items for the selected next actor | PR/provider boundary, on demand |
| `check_core_scope.py` | gates core diffs on substitution evidence and repo-local state; `--require-review` validates a revision-bound manual review receipt | pre-commit, PR CI, on demand |
| `core-scope-paths.txt` | registers thin agent/provider adapter files whose changes need the same core-scope check | read by the core-scope gate |
| `reconcile/reconcile.py` | checks every harness invariant; `--file-retries` turns findings into blocking repair items in `message-queue/needs-agent/retries/` and garbage-collects fixed ones; `--fix-index` regenerates `memory/index.md` | pre-commit (`--check`), CI, on demand |
| `hooks/pre-commit` | blocks commits when core scope, repository invariants, or tests fail | every commit (installed) |
| `install.py` | idempotent setup: git hooks path, agent-adapter symlinks (`CLAUDE.md` shims, skill dirs) | once per clone |
| `run_tests.py` | runs test files under services, canonical skills, and automation | pre-commit, CI, on demand |

Rules:

- A new repository-state invariant = a `CHECKS` entry in `reconcile.py` plus the rule
  where agents read it. External artifact boundaries use a canonical standalone gate,
  tests, and thin adapters. Check ids stay stable because retry filenames embed them
  (`memory/lessons/automation/deterministic-finding-keys.md`).
- Queue checks enforce the filename delivery class, its matching fields, actor/typed-leaf
  shape, and task↔blocker links. Known leaves add schemas; new typed leaves inherit the
  actor's generic schema. Sticky `queue-resolution` checks every staged/range deletion
  against its one-line claim and changed resolution evidence; requested review changes
  require an agent repair plus a dependent artifact-pending re-review. `stale-queue` age-checks
  `blocking-*`, never
  hard-stales `non-blocking-*`, and checks `future-blocking-*` only when `Blocks at`
  starts with a reached UTC `YYYY-MM-DD`; event boundaries require actor reclassification.
- Admission adapters pass `--displaced-tip <full oid>` for a replaced ref. The range
  head remains the candidate; a divergent old-tip snapshot must retain every live action,
  and an unavailable nonzero old tip fails closed.
- PR adapters treat titles as summaries, bind one task from the trusted base/candidate
  range, require and cross-check that evidence even for a task-named branch, and
  project the task completely. Scoped external assignments require distinct task-owned
  queue actions with exact opaque adapter bindings. Inbound sources are unscoped:
  their own asks remain enforceable without claiming to represent a task. Versioned
  source bindings let an agent transcribe uneditable provider prose; current review
  state is replayed on direct events and every candidate update. Summary mode allows
  ordinary change titles while rejecting asks. Candidate-context direct-event checks
  are not hostile-workflow evidence without a separately controlled provider gate.
- Task status enforces `transition:start`, `transition:review`, and
  `transition:complete`; admission adapters pass `--at-transition <name>` for external
  boundaries such as merge. Handover projection checks activate from the repository
  schema in `history/AGENTS.md`; staged/CI diffs make each new handover exactly project
  the current live human queue while leaving old records stable.
- Retry filing preserves claimed/rejected content on rerun; garbage collection removes
  only exact generator identities whose named finding cleared. Active legacy output may
  be migrated, but untrusted legacy lookalikes are never garbage-collected.
- Adopters may delete an empty/resolved harness folder; the deletion edge may not erase
  live actions, and removing only the queue v1 marker remains an anti-downgrade failure.
  After clean removal, its registry check no-ops with the absent folder.
- Tracked executables use repository-local state only. Agent/provider shims are thin,
  optional, policy-free forwarders to canonical behavior; personal installers stay
  outside AgentFold (`templates/task/design.md` carries the core-fit receipt).
- Never weaken a check to make a commit pass; fix the finding or file the reason as a
  decision.
