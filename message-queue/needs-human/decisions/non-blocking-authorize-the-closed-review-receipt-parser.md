# May I apply the closed review-receipt parser and template change?

**Action:** Authorize the closed review-receipt parser and template change, or decline it.
**Why this matters:** Without this authorization, completed independent review verdicts cannot be recorded without either a false human-action failure or an unsafe parsing exception.
**If you do nothing:** The parser repair and the dependent stale-base and bootstrap merges remain unpublished; current `main` stays unchanged and green.

## What you need to know

**Today:** The repository requires `core-fit / reviewer: approve — finding` as formal
review evidence, but its human-action detector interprets the structural word `approve` as
a new request. Three increasingly broad parsing repairs were rejected after adversarial
review found ambiguous Markdown-container cases.
**What this would change:** The formal receipt becomes a closed contiguous block: the
Review verdicts heading, one full reviewed-revision field, then consecutive one-line
core-fit verdicts. Both gates share that parser, and the template states the closed shape.
**What this does not decide:** It does not weaken detection inside reviewer names or findings,
change who may review, alter merge policy, or approve any pull request by itself.

The [current merge-session handover](../../../history/conversations/2026-08-04-0018PDT-merge-multi-worktree-safety-stack/handover.md)
records the exact dependency chain and the adversarial findings. The workspace safety
reviewer requires a fresh owner authorization before this security-sensitive parser and
template edit can be applied.

## Your choices

The choices differ on whether to adopt the narrow closed grammar or leave the conflicting
gates unchanged.

### Option A — Authorize the closed grammar

Allow the exact parser/template change described above, followed by focused, full, and
independent review before publication. The cost is intentionally rejecting embellished
receipt blocks that insert prose or subheadings before verdict lines.
*Example consequence:* An agent records one revision field and three consecutive verdicts;
the core gate accepts them while a later human request remains visible to task admission.

### Option B — Decline the parser change

Keep both current gates unchanged. The cost is that formal revision-bound core review
remains unusable for newly admitted tasks, so the current repair chain cannot publish under
the requested review standard.
*Example consequence:* The stale-base and bootstrap branches remain open even though their
code tests pass, because their required review evidence cannot cross the commit gate safely.

## What I recommend

**Recommendation:** Option A — the closed grammar matches the existing template, removes
Markdown-container ambiguity, and still scans every reviewer name and finding for real asks.
**Strongest case against this:** A deliberately decorated review section becomes invalid and
must be simplified to the canonical contiguous form.
**Confidence:** high — three adversarial panels identified the unsafe parser edges, and the
closed form removes the need to interpret headings, lists, block quotes, or thematic breaks.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will show
you how it read your words before acting.

**Your answer:** Option A — authorize the closed review-receipt parser and template change.

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-04, by codex, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Full context:** `history/conversations/2026-08-04-0018PDT-merge-multi-worktree-safety-stack/handover.md`
**Resolution evidence:** `memory/decisions/2026-08-04-review-receipt-parser-authorization.md`
**Answer by:** 2026-11-02
