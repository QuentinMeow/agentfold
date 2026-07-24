# automation/ — things that run

The mechanical half of `handbook/principles/systems-over-instructions.md`: everything
executes; Python stdlib only, so automation runs on a bare clone.

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
  actor's generic schema. Timing only escalates while live and freezes on human response.
  `queue-resolution` checks staged/range deletion against its claim and evidence;
  historical future reviews survive escalation. Task reviews bind local artifacts;
  merge reviews bind Git ranges. Cleanup proves a still-crossed receipt or withdrawn
  target/task plus distinct evidence. Requested changes require repair plus re-review. `stale-queue`
  checks reached dates, not `non-blocking-*`; event boundaries require reclassification.
- Admission adapters pass `--displaced-tip <full oid>` for a replaced ref. The range
  head remains the candidate; a divergent old-tip snapshot must retain every live action,
  and an unavailable nonzero old tip fails closed.
- PR adapters treat titles as summaries, bind one task from the trusted base/candidate
  range, require and cross-check that evidence even for a task-named branch, and
  project the task completely. Scoped external assignments require distinct task-owned
  queue actions bound to the stable artifact, role, actor kind, and principal. Inbound
  sources are unscoped; forced directionless sources let the bound queue path select
  the actor. Structural issues/comments replay current event-artifact state. Removing
  the final versioned source binding needs a closed current/released attestation from
  the provider adapter at exact-tree admission; current or unknown blocks. Summary mode
  allows ordinary PR titles while rejecting asks. GitHub thread state has no Actions
  transition trigger: hard assurance needs native conversation resolution, a protected
  required release check, and separately controlled provider code.
- Task admission rechecks every post-activation Git edge and every task-local Markdown
  artifact, so reversion/deletion cannot hide a crossing or human ask; exact links project.
  Adapters pass `--at-transition <name>` for external boundaries such as merge.
  Handover projection activates from `history/AGENTS.md`; staged/CI diffs make each new
  handover project the live human queue. Git-edge checks freeze every pre-existing handover at
  adoption, including legacy records and intermediate/parallel history. Entry schema
  versions preserve creation-time grammar; a newly rejecting grammar needs a new
  version instead of retroactive validation.
- Retry filing preserves claimed/rejected content on rerun; garbage collection removes
  only exact generator identities whose named finding cleared. Active legacy output may
  be migrated, but untrusted legacy lookalikes are never garbage-collected.
- Adopters may delete an empty/resolved harness folder; the deletion edge may not erase
  live actions, and removing only the queue v1 marker remains an anti-downgrade failure.
  After clean removal, its registry check no-ops with the absent folder.
- Tracked executables use repository-local state only. Agent/provider shims are thin,
  policy-free forwarders; personal installers stay outside AgentFold (`templates/task/design.md`).
- Never weaken a check to pass; fix it or file the reason as a decision.
