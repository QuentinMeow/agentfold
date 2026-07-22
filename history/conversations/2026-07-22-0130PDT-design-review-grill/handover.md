# Handover — design-review-grill

**Session:** 2026-07-22 01:30–02:15 PDT, claude (chat session with the repo owner)
**Task:** none — design review; six tasks *filed*, none claimed
**Mode:** async

## What happened

- Grilled the whole harness design (every file, the reconciler's real behavior, the
  git history) and ran three parallel web-research passes; full report with citations:
  `artifacts/design-review.md` in this folder.
- Headline finding: the repo preaches eventual consistency but the pre-commit gate
  blocks every commit on *any* finding, including pure staleness — and 13 memory
  entries all come due in the same January week, a scheduled repo-wide lockout.
  Also: nothing ever runs the retry-filing mode, so the "self-healing loop" has no
  automated trigger.
- On the owner's chat direction, applied the clearly-good fixes directly (merge
  `326e26d`): a new constitution entry `handbook/principles/provenance-over-position.md`,
  README enforcement-table honesty, five letter-vs-ritual wording conflicts, a Dead
  ends section in `templates/handover.md`, and the budget check now skips `templates/`.
- Filed six backlog tasks for the substantive work, two review items, one ADR, and a
  new roadmap desired-state line 7 that the tasks trace to.

## How it works now

Contracts on main no longer contradict their own rituals, and the constitution now
has an explicit trust boundary: external content in instruction-bearing paths is
data to review, never orders. The enforcement *behavior* is unchanged — severity
tiers, retry automation, and provenance checks are backlog tasks, in recommended
order starting with 2026-07-22-severity-tiers-for-reconciler-findings.

## Decisions made for you

- Provenance-over-position principle added (you directed it in chat):
  `memory/decisions/2026-07-22-provenance-over-position-principle.md` has the
  reasoning and alternatives. Its Review-by is deliberately staggered to 2027-02-28.

## Needs your attention

- [Doc fixes applied from the design review](../../../message-queue/needs-human/reviews/design-review-direct-fixes.md) —
  eleven files of wording/template fixes landed on main (merge `326e26d`), including
  two root-AGENTS.md guardrails and the README enforcement table. Doing nothing is
  safe; everything is one revert away.
- [Provenance principle wording](../../../message-queue/needs-human/reviews/provenance-principle-wording.md) —
  the new constitution entry binds even `autonomous` mode to human review of
  external changes on five instruction-bearing paths. Worth a skim: is that the
  trust boundary you want? Doing nothing keeps it as written.

## Dead ends

- None — analysis and doc work; no failed approaches worth flagging.

## Next steps

- Work the backlog in order: severity tiers → retry automation → write rules →
  de-minimis → provenance checks → ritual hooks (rationale in the report, Part 3).
- Everything from this session is published on branch
  `session/2026-07-22-0130PDT-design-review-grill` as a PR the owner asked for —
  review and merge it; nothing lands on main until then.

## Deep links

- Report: `artifacts/design-review.md` · Tasks: `tasks/0_backlog/` (six folders
  dated 2026-07-22) · Roadmap: `roadmap/desired-state.md` line 7
- Commits: `326e26d` (branch), its merge, plus the `harness:` commits after it
