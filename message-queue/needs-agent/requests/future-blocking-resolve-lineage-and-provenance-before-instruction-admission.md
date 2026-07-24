# Resolve lineage and provenance prerequisites before instruction admission

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After override lineage and the repository provenance mechanism are done, verify both completion records and remove this dependency action and its reciprocal task link before claiming instruction-admission review.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-24-review-layered-instruction-admission
**Until then:** Keep instruction admission unenforced and the review task unclaimed; other work may continue.

## What you need to know

Layered instruction receipts must bind the actual lineage format and reuse the one
repository maintainer/provenance source. Starting early would duplicate authority or
review a receipt shape that the effective tree cannot produce.

## Done when

Tasks `2026-07-24-track-layered-override-lineage` and
`2026-07-22-provenance-checks-for-instruction-files` are in `4_done` with passing
verification, and this action and its exact task link are removed in one commit.
