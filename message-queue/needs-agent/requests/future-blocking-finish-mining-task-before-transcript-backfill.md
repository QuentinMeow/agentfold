# Finish the mining task before the transcript backfill starts

**Status:** in-repair
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** After 2026-07-25-mine-markdown-cochange-couplings reaches `4_done`, confirm which transcript sections its verification file is still missing, then remove this dependency action and its reciprocal task link before the backfill task is claimed.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:start task:2026-07-25-complete-stage-0-verification-transcripts
**Until then:** The backfill task stays unclaimed in backlog. The mining task keeps sole ownership of its own verification file, so no two sessions append to it at once.

## What you need to know

The transcript backfill appends to the verification file of task
2026-07-25-mine-markdown-cochange-couplings, and that task is still in progress and still
writing to the same file. Two sessions in one file is the collision this repository's
one-item-one-file rule exists to avoid, so the ordering is carried mechanically here rather
than as prose in the pickup request.

The mining task may also close some of the gap itself before it finishes — its own plan
step 10 owes exactly these transcripts. Whoever resolves this action therefore re-reads the
verification file first and narrows the backfill task's scope to what is genuinely still
missing, rather than assuming all four sections are outstanding.

The canonical pickup request for the backfill task is
`message-queue/needs-agent/requests/non-blocking-pick-up-complete-stage-0-verification-transcripts.md`;
a task pickup is required to be non-blocking, so this separate action is what carries the
dependency timing.

## Done when

After a committed status-only claim moves this action from `open` to `in-repair`, the
mining task is in `4_done` with its verification recorded, and the backfill task's scope
has been narrowed to the sections still missing. The resolving commit updates
`roadmap/current-state.md` and removes this action plus its reciprocal `Queue actions`
link, before any later claim of the backfill task.
