# Complete the layered-workspace parent before manifest work starts

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-layered-development-workspace` is reviewed, verified, and done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming the manifest task.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-declare-layered-workspace-manifest
**Until then:** Keep the manifest task unclaimed in backlog; the bounded topology inspector may still be used manually.

## What you need to know

The manifest must implement the final reviewed zone/status contract rather than an
in-progress draft. This start-boundary action makes that parent dependency mechanical
instead of relying on prose in the pickup request.

## Done when

After a committed status-only claim moves this action from `open` to `in-repair`, the
parent task is in `4_done` with review and verification recorded. The resolving commit
then updates `roadmap/current-state.md` and removes this action plus its exact
manifest-task `Queue actions` link before a later claim.
