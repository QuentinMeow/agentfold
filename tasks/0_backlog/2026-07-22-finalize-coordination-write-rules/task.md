# Finalize the coordination write rules so doc and practice match

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none
**Repository scope:** core

## Goal

`handbook/git-workflow.md` says coordination writes go "directly on main," but the
repo's own history put them on a session branch merged via PR — and task-folder
files straddle the split: claims are coordination, yet `verification.md` describes
branch code main doesn't have yet (the issue-state-vs-code-state race the beads
tracker documents). Decide and write down one model. Recommended: claims and status
moves are `harness:` commits on main, pushed immediately (make the push explicit);
task content files ride the task branch; the move to `4_done` lands in the same
push as the merge so task state never outruns code state. Also finalize: when a
claim dies (a lease — e.g. unclaim after N quiet days, replacing the current
mtime-based guess); what `2_blocked` covers (today only human decisions — broaden
to blocked-on-task/external, or document the narrowness); and what "a task branch
touches one service" means for harness work that touches no service.

## Acceptance criteria

- [ ] `handbook/git-workflow.md` describes a workflow the next session can follow
      literally, including where each of the five task files is committed
- [ ] The done-move-rides-the-merge rule is stated where task lifecycle lives
      (`tasks/AGENTS.md`), with the race it prevents named
- [ ] Claim-death rule stated and mechanically checkable (feeds the stale-task check)
- [ ] `2_blocked` scope decision recorded (ADR if it changes)

## Links

- Design review, finding 1.3: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
