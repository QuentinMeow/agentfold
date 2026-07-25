# Resolve lineage and instruction prerequisites before publication review

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After override lineage and the layered instruction policy are approved and done, verify both completion records and remove this dependency action and its reciprocal task link before claiming publication-boundary review.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-review-layered-publication-boundary
**Until then:** Keep publication review unclaimed and publication blocked; other work may continue.

## What you need to know

The export threat model must consume the real candidate lineage and an approved
instruction-admission result. A rejected or absent authority policy cannot be treated
as a satisfied publication prerequisite.

## Done when

Override lineage is in `4_done`, the instruction-admission task records revision-bound
human approval and is in `4_done`, and this action and its exact task link are removed
in one commit before a later claim.
