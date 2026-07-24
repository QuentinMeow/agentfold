# Resolve the manifest prerequisite before recovery-evidence work starts

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming recovery-evidence work.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-record-layered-recovery-evidence
**Until then:** Keep the recovery task unclaimed and make no backup or loss claim; other work may continue.

## What you need to know

Recovery evidence binds exact declared targets and policy references. The manifest must
own those identities before evidence templates or loss evaluation can be stable.

## Done when

The manifest task is in `4_done` with passing verification, and this action and its
exact task `Queue actions` link are removed in one commit before a later claim.
