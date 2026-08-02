# Pick up making a handover still true one commit after it is written

**Status:** open
**Filed:** 2026-08-02, by claude, from a cold-boot trial that broke its own handover inside one session
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-make-a-handover-survive-the-next-commit/task.md`
**Request kind:** task-pickup
**If unanswered:** Handovers keep being written with links that die at the session's next status move, unverified when written and unrepairable afterwards, so the record the next reader depends on decays with nothing reporting it.

## What you need to know

`templates/handover.md` asks for a task-folder link; `tasks/AGENTS.md` says to reference a
task by id and never by path, because paths change with status. An agent following the
template writes links that the next status move kills. `check_links` skips `history/`
wholesale and `history/AGENTS.md` forbids editing a committed record, so the breakage is
invisible when written and permanent afterwards. A cold-boot trial did this to its own
handover inside one session.

Separately, the template says one screen but requires projecting every unresolved
`needs-human/` item verbatim — 11 items and about 750 words today, mostly unrelated to any
given session. Whether that duplication is deliberate may be the owner's call rather than
the claimant's; the task says how to route it if so.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
