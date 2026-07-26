# Edge-graph coverage fraction is stated inconsistently

**Status:** in-repair
**Filed:** 2026-07-25, by Codex while explaining the pending edge-graph artifact-storage decision
**Action:** When folding the artifact-storage decision, replace “a sixth of the repository” with the exact measured coverage — 17 of 172 files, or 9.9% — and preserve that number in the resulting decision record.
**Check:** manual
**Subject:** `message-queue/needs-human/decisions/future-blocking-commit-or-generate-the-edge-graph-artifact.md`
**Resolution evidence:** `memory/decisions/2026-07-25-edge-graph-artifact-storage.md`
**Blocks at:** transition:fold-edge-graph-artifact-storage-decision
**Until then:** Treat the repeated 17-of-172 measurement as authoritative and “a sixth” as a wording error; the error does not change the Option B recommendation.

## Broken invariant

One decision item repeatedly gives the measured coverage as 17 of 172 in-scope Markdown
files, which is 9.9%, but its comparison section calls the same coverage “a sixth of the
repository.” The pending action and its eventual decision record must describe one
measurement consistently.

## Fix

Preserve the human's answer, replace the incorrect fraction with “17 of 172 files (9.9%,
about one tenth),” and record the exact measurement in the new artifact-storage ADR. The
arithmetic repair is the same whether the human selects Option A or Option B.

## Agent notes

None yet.
