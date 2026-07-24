# Publish the layered-workspace follow-up tasks after parent admission

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After the layered-workspace parent PR is admitted, publish the six preserved follow-up backlog tasks, pickup requests, and dependency actions through the live main coordination lane, then resolve this action.
**Full context:** `roadmap/current-state.md`
**Why-you-might-care:** The six follow-up tasks must become discoverable without smuggling live coordination through an implementation PR.
**If-you-do-nothing:** The parent stays short of completion and the preserved follow-up records remain inactive.
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:complete task:2026-07-24-layered-development-workspace
**Until then:** The parent design and read-only inspector may proceed through review; the follow-up drafts remain inactive.

## What you need to know

The task-pure implementation branch excludes six backlog task files, six pickup
requests, and six dependency actions because those records belong directly on the
live coordination lane. Their exact final source is immutable commit
9d7bb1d7fd48384611593b43d240a258de2f096a.

Publish those records only after the parent design is admitted so another agent cannot
claim work against an unmerged contract. Verify every reciprocal link and commit them
directly to main; do not merge the backup branch's implementation history.

## Done when

All 18 coordination files are present on main, each backlog task has its pickup and
applicable dependency action, the reconciler is clean, the roadmap links the live
follow-ups, and this request plus its parent-task backlink are removed.
