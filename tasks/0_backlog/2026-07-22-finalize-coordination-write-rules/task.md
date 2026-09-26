# Finalize the coordination write rules so doc and practice match

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-finalize-coordination-write-rules.md`; `message-queue/needs-agent/requests/non-blocking-track-github-issue-77-coordination-publication.md`

## Goal

`handbook/git-workflow.md` says coordination writes go "directly on main," but the
repo's own history put them on a session branch merged via PR — and task-folder
files straddle the split: claims are coordination, yet `verification.md` describes
branch code main doesn't have yet (the issue-state-vs-code-state race the beads
tracker documents). Decide and write down one model. Recommended: claims and status
moves are `harness:` commits on main, pushed immediately (make the push explicit);
task content files ride the task branch; the move to `4_done` lands in the same
push as the merge so task state never outruns code state. Also define claim retirement and takeover through positive stop or revocation evidence;
quiet time alone cannot prove a writer stopped. The later multi-worktree design treats
stale or missing authority evidence as unknown. The task also defines what "a task branch
touches one service" means for harness work that touches no service. Under the current
contract, `2_blocked` represents a reciprocal immediate agent blocker; a human action
may withhold only an unstarted task or a named act with no undo.

## Acceptance criteria

- [ ] `handbook/git-workflow.md` describes a workflow the next session can follow
      literally, including where each of the five task files is committed
- [ ] The done-move-rides-the-merge rule is stated where task lifecycle lives
      (`tasks/AGENTS.md`), with the race it prevents named
- [ ] [derived] Claim retirement and takeover require positive stop or revocation evidence;
      inactivity alone never transfers authority — stale observations do not prove exclusion.
- [x] [derived] `2_blocked` permits only a reciprocal live `blocking-*` agent action —
      the current task contract and human-gating decision supersede the July scope.

## Links

- Design review, finding 1.3: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
- Blocking-scope implementation: task `2026-07-23-first-class-message-queue`

## Planning correction — 2026-09-25

The older agent-authored timeout suggestion and human-blocker description above were
replaced to match the later design in task
`2026-08-03-plan-multi-worktree-safety-remediation` and the accepted decision
`memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`.
This is a backlog interpretation correction; no claim, lease or publication mechanism
was implemented by the audit.
