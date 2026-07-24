# Resolve the manifest prerequisite before override-lineage work starts

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming the override-lineage task.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-track-layered-override-lineage
**Until then:** Keep the override-lineage task unclaimed in backlog; other work may continue.

## What you need to know

Override records and leases consume the canonical manifest generation and status model.
Starting first would create a competing schema and an admission claim with no stable
control plane.

## Done when

The manifest task is in `4_done` with passing verification, this action and its exact
task `Queue actions` link are removed in one commit, and override-lineage pickup may
proceed in a later claim commit.
