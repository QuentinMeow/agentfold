# Recover useful local and open-PR changes into a mergeable stack

**Claimed-by:** codex
**Mode:** autonomous
**Filed:** 2026-08-30, by codex, from the owner request to recover the open pull requests
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/decisions/blocking-authorize-the-external-recovery-review.md`
## Goal

Assess PRs 88 and 89 together with the unfinished local merge and retained experiments. Preserve useful behavior in a shallow, verified PR stack, excluding superseded experiments without losing recoverable source state. Existing PRs may be repaired or replaced; the delivered implementation remains open for review.

## Acceptance criteria

The recovery inventory distinguishes verified observations from assumptions.

- [x] Every useful PR and local change has a documented disposition and source reference.
- [x] The delivered PR layers have explicit bases and GitHub reports them mergeable.
- [x] Repository checks and full tests pass on each delivered layer and the combined result.
- [x] Fresh-context reviews, cross-vendor refutation, and cold-clone verification are recorded honestly.
- [x] Original state remains recoverable and closing records identify retained and superseded work.

## Links

- [Open pull requests](https://github.com/QuentinMeow/agentfold/pulls)

- [Captured owner request](requirements.md)
- [Recovery inventory and original staged files](recovery-inventory.md)
- [Retained and rejected choices](recovery-decisions.md)
- [Executed checks](verification.md)
