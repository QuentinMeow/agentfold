# Handover — layered workspace research and agent transfer

**Session:** 2026-07-24 02:02–02:36 PDT, codex
**Task:** none — exploratory
**Mode:** async

## What happened

- Audited the active queue, handovers, worktrees, PR #7 state, and known branch tips;
  PR #7 remains in review and must not merge before its queue-owned reviews resolve.
- Independent research compared Git-history composition, materialized views,
  resolver-native layering, patch stacks, nested repositories, symlinks, and union
  filesystems for public/private/restricted/raw/temp development.
- Folded the owner's platform answer into the new task: macOS and Linux are the
  baseline; Windows is included only when cheap and non-distorting.
- Filed one backlog task with the complete workspace requirements and a separate
  blocking repair for the test runner's inherited Git environment.

## How it works now

No layered-workspace architecture has been admitted or implemented. The leading
hypothesis is a private integration checkout plus physically separate restricted/raw/
temp roots and a sealed clean public publisher, but the next agent must challenge it
through the queued design and adversarial review. Linked-worktree hook runs are unsafe
until the separate test-runner repair is verified.

## Decisions made for you

The owner selected macOS/Linux as the baseline and optional low-cost Windows support;
that requirement is folded into
`tasks/0_backlog/2026-07-24-layered-development-workspace/task.md`.

## Needs your attention

- [Assurance-profile ceilings](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Confirm whether each guard profile's advertised claim matches its real enforcement ceiling. If untouched, guardrail implementation waits at its start boundary and the proposal remains unchanged.
- [Detector failure state](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Confirm that failed or incomplete detection remains distinct from a clean result and has the proposed mode-dependent behavior. If untouched, guardrail implementation waits at its start boundary.
- [First-class message queue](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Review PR #7's queue ownership, timing prefixes, and enforcement only after its final artifact is bound. If untouched, the PR stays unmerged.
- [Guardrail authority boundary](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Confirm that an agent may record its judgment but may not authorize its own confirmed critical finding. If untouched, guardrail implementation waits and the proposed authority split stands.
- [Sensitive-data recovery](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Confirm the proposed incident-recovery boundary and sequence. If untouched, guardrail implementation waits and the recovery sequence remains a proposal.
- [Template-first explanation](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Optionally review whether the documentation explains the already-decided template-first guardrail policy. If untouched, AgentFold continues with the decided four-mode policy.

## Dead ends

An ignored nested private repository, symlink farm, linked worktree, private branch,
local hook, sparse checkout, or Git LFS pointer cannot be the confidentiality boundary.
A test-runner fix only in the pre-commit hook is also insufficient because other
callers can carry the same Git-local environment.

## Next steps

- [Finish the test-runner Git-environment isolation repair](../../../message-queue/needs-agent/requests/blocking-finish-test-runner-git-environment-isolation.md)
- [Pick up the layered development workspace task](../../../message-queue/needs-agent/requests/non-blocking-pick-up-layered-development-workspace.md)

## Deep links

- Task folder: `tasks/0_backlog/2026-07-24-layered-development-workspace/` · Worklog:
  `tasks/0_backlog/2026-07-24-layered-development-workspace/worklog.md` · Verification:
  not yet created
- Commits: this handover's coordination commit
