# Give the retry loop an automated trigger, merge-safe filing, and waivers

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-retry-filing-automation-and-waivers.md`

## Goal

The self-healing loop in `handbook/principles/eventual-consistency.md` promises
"retry item auto-filed," but nothing runs `--file-retries`: the pre-commit hook and
CI both run `--check` only — the centerpiece of systems-over-instructions is itself
an instruction. Wire filing to something that runs (a post-commit hook in
`automation/hooks/`, or a scheduled CI job that commits the items). The first-class
queue work now preserves actor-owned status/notes and refreshes only a marked machine
projection; the remaining lifecycle gap is rejection/waiver authority. Add a
`**Waived-until:** <date> — <reason>` field
the reconciler respects, making rejection a real terminal state. Depends on the
severity-tier task (2026-07-22-severity-tiers-for-reconciler-findings) landing
first, so advisory findings can be filed while commits still pass.

## Acceptance criteria

- [ ] A finding left unfixed appears in `message-queue/needs-agent/retries/` without
      any human or agent invoking the reconciler by hand
- [x] Re-running the filer preserves an existing item's `**Status:**` line and any
      agent-written text below the generated sections
- [ ] An item with a future `**Waived-until:**` is neither refiled nor counted as a
      finding; a past date revives it
- [ ] `templates/queue/retry.md` documents the waiver field; `automation/AGENTS.md`
      table updated in the same change

## Links

- Design review, finding 1.2: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
- Lesson that shaped the key scheme: `memory/lessons/automation/deterministic-finding-keys.md`
- Preservation implementation: task `2026-07-23-first-class-message-queue`
