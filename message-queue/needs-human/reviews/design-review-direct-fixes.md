# Doc fixes applied from the design review — sanity-check the wording

**Status:** waiting
**Filed:** 2026-07-22, by claude (design-review session — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Look-at:** `git show 326e26d` — the fix/design-review-hardening merge, 11 files
**Why-you-might-care:** it edits load-bearing wording: two root-AGENTS.md guardrails, the README enforcement table, the queue's scope claim, CONTRIBUTING's schema-change rule, and the handover template (new Dead ends section); plus one roadmap line added for the six new backlog tasks
**If-you-do-nothing:** everything stands — all changes are wording/template fixes for contradictions the review documented, each reversible with a one-commit revert

Highlights, if you only skim one thing each: the "never edit or delete text the
human wrote" guardrail now permits deleting an answered decision file *after
folding* (the old letter forbade the prescribed ritual); the README no longer
claims handover coverage and adversarial review are fully machine-enforced (they
aren't); and `memory/AGENTS.md` no longer states a +90-day default that
contradicted the templates.

**Resolution:** ______ <human: anything here counts as acknowledged>
