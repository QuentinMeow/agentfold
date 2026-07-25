# Resolve the manifest prerequisite before cross-zone planning starts

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming the cross-zone planner.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-route-layered-cross-zone-operations
**Until then:** Keep the cross-zone planner unclaimed in backlog and all operations manual; other work may continue.

## What you need to know

Operation plans need canonical role, origin, and policy identities from the manifest.
Without them, a planner would infer zone ownership from paths and undermine the design.

## Done when

The manifest task is in `4_done` with passing verification, and this action and its
exact task `Queue actions` link are removed in one commit before a later claim.
