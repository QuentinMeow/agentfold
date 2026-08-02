# Should the plan for keeping private and public work in physically separate places stand?

**Action:** After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.
**Why this matters:** This decides how public, private, and restricted material may sit side by side, and it refuses to treat ordinary version-control conveniences as real confidentiality boundaries.
**If you do nothing:** Nothing stops; the design and its tool stand as they are, and the task that produced them finishes without your judgment on record.

## What you need to know

**Today:** the design and the tool that comes with it are already merged. The tool is run by hand, reads the layout, and reports — it moves nothing, publishes nothing, changes nothing. Nothing waits on your answer.

**What this would change:** your verdict goes on the record. Approving accepts the direction, and this first piece as a reversible starting point.

**What this does not decide:** no later capability is authorized by this. No publishing, no mounting one place inside another, no migration, no automatic public operation; each needs its own task and review.

The direction is a private working copy inside an envelope that is not itself version-controlled, separate outside zones carrying no version control at all, and a physically separate publisher for anything public. The piece that exists is only the reporter. Where it cannot verify something — whether content was scanned, whether backups exist, whether outside instructions were admitted, whether publishing is permitted — it says so rather than granting it, and if a declared private area overlaps the public publisher or shares its storage it refuses the layout instead of calling it safe. The plan is [the layered workspace design](../../../docs/designs/layered-development-workspace.md).

## Your choices

The choices differ in what happens to work that is already merged and running: it is accepted as the direction, repaired first, or taken back out.

### Approve
The direction stands and later pieces build on it. The cost is that much follows from it: the physical separation shapes where everything lives afterwards, and changing your mind later is a migration rather than an edit.
*Example consequence:* the next several tasks assume separate roots and a separate publisher, and any tool wanting to see everything at once must be taught to reach across them.

### Request changes
The direction is roughly right but something specific is wrong — a claim the tool makes, a confidentiality assumption, or how it behaves when it cannot tell. Name it; an agent repairs it and brings it back, and dependent work waits meanwhile.
*Example consequence:* you say it should refuse rather than warn when it cannot read a declared area, that changes, and layouts that used to pass now stop.

### Reject
The architecture is wrong. What is merged gets taken back out — possible, because the tool only reports — but the follow-on tasks planned around it are wasted.
*Example consequence:* the separation idea is dropped, the tool is removed, and how to hold private and public material together is an open question again.

## What I recommend

**Recommendation:** Approve — the merged piece only looks and reports, so it cannot cause the harm the design is about, and a reporter that refuses to claim what it did not verify is the right first thing to build.
**Strongest case against this:** the direction is the expensive half, not the tool. Physical separation makes every later convenience harder, and if you would rather have one working copy with careful rules inside it, now is the moment to say so.
**Confidence:** low — I am reading a file a previous session wrote rather than the design and tool themselves; I confirmed the change is merged and its task still parked in review, but did not read or run the tool.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Full context:** task `2026-07-24-layered-development-workspace`; `docs/designs/layered-development-workspace.md`; `automation/inspect_workspace_boundaries.py`
**Resolution evidence:** `memory/decisions/2026-07-24-layered-development-workspace-review-disposition.md`
**Review target:** git:d87b755e6259101bf76b0a2783b35dfb3f163fb0...8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b
**Review revision:** git:d87b755e6259101bf76b0a2783b35dfb3f163fb0...8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-22
