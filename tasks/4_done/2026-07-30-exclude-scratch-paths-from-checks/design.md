# Design notes — exclude scratch paths from the reconciler's filesystem walks

**Status:** decided

## Problem

Several reconciler functions look for "live" content by combining the Git index with a
direct filesystem walk of the working tree, so newly-created files are checked before
they are staged (this is deliberate — it is what lets `--check` warn before `git add`).
That second, filesystem half of each function has no idea what Git ignores, so a
git-ignored file under `tmp/` is indistinguishable from real new content.

Four call sites do this, gated only by `CHANGE_RANGE is None` (a `--range` invocation
already only trusts the Git index, so it is unaffected):

- `live_markdown_files()` — `REPO.rglob("*.md")`, feeds `check_agents_budget` and
  `check_links`.
- `live_queue_items()` — `QUEUE.rglob("*")`, feeds six queue checks
  (`check_queue_name`, `check_queue_location`, `check_queue_schema`,
  `check_stale_queue`, `check_active_queue_boundaries`,
  `check_queue_task_reciprocity`) plus `live_human_queue_paths`/
  `live_agent_queue_paths`.
- `live_handover_paths()` — `CONVERSATIONS.glob("*/handover.md")`, feeds
  `check_handover_queue_projection`.
- `check_task_structure()`'s own inline `TASKS.iterdir()` / `entry.iterdir()` walk
  (not extracted into a `live_*` helper).

`check_links` already papers over one instance of this with its own `LINK_SKIP_DIRS =
{"templates", "history", "tmp"}` special case — but that constant conflates "tmp is
scratch" with two unrelated reasons (`templates/` is schemas, not live contracts;
`history/` cites historical paths on purpose), and `check_agents_budget` has no such
guard at all, which is exactly the reported bug.

## Options considered

### Option A — Hardcode a `tmp/` (and dotfile) skip in every affected walk
Cheap, but is exactly the "sprinkling special cases" the task asks to avoid, and it only
covers the one path the contract names today — a future git-ignored scratch
convention (or a repository-specific `.gitignore` addition) would need its own copy of
the same special case again.

### Option B — Ask Git once per invocation what is ignored, filter every walk through it
`git ls-files --others --ignored --exclude-standard --directory -z` returns, in one
process call, every git-ignored path — collapsed to the top of an ignored directory
(e.g. `tmp/`) rather than recursing into it, and to individual ignored files inside an
otherwise-tracked directory. Cache it exactly like the existing index/HEAD snapshot
(`load_git_index_snapshot`/`load_git_head_snapshot`, populated once in
`start_git_snapshot_cache`), so a run with hundreds of candidate files still spawns Git
once, not once per file. A single predicate (`path_is_git_ignored`) is then the one
exclusion every untracked-scan site calls.

### Option C — Skip any path Git would refuse to `add` (`git check-ignore --stdin`)
Equivalent in spirit to B (also one process, fed every candidate over stdin instead of
listing directories up front), but it needs every candidate path gathered first and one
process per *check invocation* rather than one process per *reconciler run* — the walk
itself (`rglob`) still has to run before we know what to feed it. `--directory` mode
answers the same question before any filesystem walk happens, and collapses a whole
ignored subtree (a stray scratch clone can be thousands of files) to one line.

## Chosen

Option B. It matches the "ask Git, no per-file spawn" preference exactly: one
`git ls-files --directory` call per reconciler invocation, cached alongside the index
and HEAD snapshots the file already maintains. `path_is_git_ignored(rel_posix)` is the
one shared primitive; it is applied only to the untracked/filesystem half of each of the
four sites above; the Git-index half of each function (which already runs
unconditionally) is untouched, so a tracked file is still checked even if it happens to
sit under a path that also matches an ignore rule (the `tmp/AGENTS.md` case if someone
force-added it — force-adding a git-ignored path is exactly the "tracked despite the
ignore rule" case the constraint protects). `check_links`'s `LINK_SKIP_DIRS` keeps
"templates" and "history" (unrelated reasons); the redundant "tmp" entry was removed —
it is now covered by the shared predicate one layer down, and leaving it in place would
have kept a second, inconsistent special case (it would still exempt a force-added
tracked `tmp/` file from `check_links`, while `check_agents_budget` — which had no such
special case — would already check it under the fix).

`live_task_directories()`, `live_conversation_directories()`, and `memory_entries()` were
checked too: each returns from the Git-index branch before reaching its own
filesystem-walking fallback, which only runs when `.git` is absent entirely (a no-Git
adopted repository). No live scratch content reaches those, so they are unchanged.

## Core fit

**Agent substitution:** pass — the reconciler is a plain Python/argparse/subprocess script every agent runtime invokes the same way; nothing here is IDE- or agent-specific
**Provider substitution:** not-applicable — nothing here reads or writes any external provider
**Repository substitution:** pass — any adopted repository that follows the same `tmp/`-is-scratch convention (or any other `.gitignore` rule) gets the same exclusion for free, since it is derived from Git's own ignore rules rather than a name baked into this repository
**User-global writes:** none
**Why AgentFold core:** The reconciler is the referee every adopter relies on for repository invariants (`AGENTS.md` guardrail: "the reconciler is the referee"); a referee that reports findings against the contract's own designated scratch space is a bug in the referee, not in the scratch convention
**Thin adapter:** none
