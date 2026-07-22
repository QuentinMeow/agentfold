# Define a de-minimis path for micro-changes

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none

## Goal

Every change today carries full ceremony — task folder, branch, worklog,
verification, handover. Measured practitioner data puts file-driven process at ~4×
overhead on small tasks, and this repo's own history (three one-line-rule changes,
each fully dressed) is the local exhibit. Define a micro-change: e.g. ≤ ~20 changed
lines touching no `templates/`, no `handbook/principles/`, no `automation/` check
logic — committed directly with a descriptive message, no task folder, no handover
when the session filed no queue items and made no decisions. This also resolves the
standing contradiction between `handbook/git-workflow.md` ("every change traceable
to a task") and `CONTRIBUTING.md` (which already permits untracked small-fix
branches): one definition, stated once, both docs linking it.

## Acceptance criteria

- [ ] "Micro-change" defined in exactly one place; `handbook/git-workflow.md` and
      `CONTRIBUTING.md` both link it and no longer conflict
- [ ] "Session that did work" (the handover trigger in `history/AGENTS.md`) defined
      so a micro-only session is exempt and a decision-making session is not
- [ ] The boundary is judgment-proof enough that two agents classify the same change
      the same way (worked examples included in the doc)

## Links

- Design review, finding 1.5 and Part 2 (ceremony overhead): `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
