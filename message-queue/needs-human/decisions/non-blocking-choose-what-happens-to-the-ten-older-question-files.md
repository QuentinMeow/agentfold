# Ten of the seventeen questions in your queue still open with a wall of bookkeeping — rewrite them, or let them go?

**Action:** Choose whether the ten older question files are rewritten to hide their bookkeeping, migrated one at a time with your sign-off, or left alone.
**Why this matters:** Ten of the seventeen questions in your queue put a screen of paths and checksums above the ask, so on a phone the question starts below the fold.
**If you do nothing:** Nothing stops. Those ten keep the shape you saw, and every question written from today's template already hides its bookkeeping behind one line.

## What you need to know

**Today:** seventeen questions sit in your queue, fifteen of them waiting on your answer. Seven carry the bookkeeping under the line you answer on; ten carry it above, beneath the title, because they predate the change.

**What this would change:** only those ten existing files, and only their layout — never a word of the question, and never a word you have written.

**What this does not decide:** anything about new questions, already born collapsed, or about the checks, which are built and unaffected by your answer.

Measured on the ten: 106 bookkeeping lines, 7,385 painted characters, 252 lines of screen at phone width. Collapsed: 740 characters, 30 lines — 90% fewer characters, 88% less screen. Here is the worst of the ten — 1,013 characters and 33 lines of screen on its own — and what it would show instead.

```
BEFORE — the top of non-blocking-review-layered-development-workspace.md, above the question it asks
**Status:** waiting
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.
**Full context:** task `2026-07-24-layered-development-workspace`; `docs/designs/layered-development-workspace.md`; `automation/inspect_workspace_boundaries.py`
**Resolution evidence:** `memory/decisions/2026-07-24-layered-development-workspace-review-disposition.md`
**Review target:** git:d87b755e6259101bf76b0a2783b35dfb3f163fb0...8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b
**Review revision:** git:d87b755e6259101bf76b0a2783b35dfb3f163fb0...8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-22
   ... four more lines of the same ...

AFTER — the same bookkeeping, below the question, as one line you can tap open
> For the record — bookkeeping the reconciler reads. Nothing here needs you.
```

Rewriting is not free, and that is the question. A file's identity is its own bytes, so moving lines changes what the repository thinks the question *is*, and the rule against rewriting a live one exists to stop an agent quietly altering what you were shown. Collapsing also moves the block from above your answer to below it — a reordering, not a fold. [The template new questions copy](../../../templates/queue/decision.md) shows the shape. A cheaper repair was investigated and rejected: making the rule ignore blank lines buys these ten nothing.

## Your choices

The choices differ in who authorises changing a file you were already shown.

### Option A — Rewrite all ten in place
An agent collapses and reorders all ten, and the rule against rewriting a live question gains a narrow written exception. Costs: the exception is permanent, and that rule is the one thing stopping an agent editing what you were shown.
*Example consequence:* you open the oldest review next week and see the question first — and the rule that would have refused that edit now has a permanent hole in it.

### Option B — Approve each file yourself
You are shown one before-and-after per file and say yes or no; approved ones are rewritten. Costs: ten small approvals from you.
*Example consequence:* you approve six on a Sunday and ignore the rest; those six read cleanly, the other four are untouched, and no rule is weakened.

### Option C — Leave them to age out
Nothing is rewritten. Each disappears the moment you answer it. Costs: those ten stay hard to read for as long as they stay unanswered.
*Example consequence:* six months from now the last of the ten is answered and deleted, and the problem is gone without any rule having been relaxed.

## What I recommend

**Recommendation:** Option C — the ten are the last of their kind, and buying their layout costs either a permanent hole in the rule that protects what you were shown, or ten approvals for a problem that resolves itself.
**Strongest case against this:** ten unreadable questions is the complaint that started this, and they only age out if you answer them; all ten have been open since July. If you want the win now, B buys it without weakening anything.
**Confidence:** medium — I measured the ten files and the collapsed alternative and confirmed a rewrite is refused today; I did not build the migration, and the phone-width figures are a text wrap at 40 columns, not a screenshot.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** 2026-08-18, by claude, from task `2026-08-18-fold-the-queue-machine-record`  
**Full context:** `templates/queue/decision.md`  
**Resolution evidence:** `memory/decisions/2026-08-18-legacy-human-item-fold-disposition.md`  
**Answer by:** 2026-11-16

</details>
