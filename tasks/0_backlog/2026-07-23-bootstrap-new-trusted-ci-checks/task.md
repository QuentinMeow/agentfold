# Bootstrap new trusted CI checks without candidate-code execution

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-23, by codex, from failing checks on PR #7
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-bootstrap-new-trusted-ci-checks.md`

## Goal

Define a safe first-activation path for trusted-base workflow checks whose checker does
not yet exist on the target branch, and make repository link validation hermetic across
developer and CI machines. Do not solve bootstrap by executing unreviewed candidate
code in a trusted context.

## Acceptance criteria

- [ ] A regression reproduces a trusted-base workflow invoking a checker that exists
      only on the candidate branch.
- [ ] The activation protocol either supplies trusted checker code independently or
      stages enforcement without overstating first-PR assurance.
- [ ] A regression proves that developer-local absolute paths produce the same
      link-check result locally and in CI.
- [ ] PR #7's two recorded failing checks have an explicit disposition and rerun
      evidence.
- [ ] Implementation begins only after the parent change's first human review.

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- Failing workflow:
  https://github.com/QuentinMeow/agentfold/actions/runs/30070821441
- Failing publication run:
  https://github.com/QuentinMeow/agentfold/actions/runs/30070769357
