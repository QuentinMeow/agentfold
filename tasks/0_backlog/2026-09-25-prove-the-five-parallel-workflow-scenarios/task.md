# Five parallel-workflow acceptance scenarios with observed evidence

**Claimed-by:** unclaimed
**Filed:** 2026-09-25, by codex, from the audit of roadmap goal G9
**Parent:** 2026-08-03-plan-multi-worktree-safety-remediation
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-five-parallel-workflow-scenarios.md`

## Goal

Produce the five disposable acceptance experiments and short operations manual required
by the confirmed multi-agent collaboration goal in `roadmap/desired-state.md`.
The parent task owns the original requirements and designed cycles. This child owns
runtime evidence, not a new scheduler, identity schema or coordination database.

## Acceptance criteria

- [ ] [derived] Two sessions demonstrate non-overlapping edits and a detected same-path collision — the parallel-edit requirement needs observed behavior.
- [ ] [derived] Two competing claims and an unrelated coordination update produce one claimant without losing the unrelated change, and refreshed sessions agree on task state — shared visibility needs concurrency evidence.
- [ ] [derived] Interruption and resume preserve committed intent and distinguish observed process/worktree loss from untested machine-loss recovery; stale observations never authorize takeover — recovery claims need explicit limits.
- [ ] [derived] Dependent changes restack without re-resolving an unchanged conflict, and a stale publisher cannot overwrite an intervening update — dependent work needs both continuity and publication proof.
- [ ] [derived] Individually green but jointly failing branches are rejected before the observed landing target advances — combined-failure detection alone is not landing prevention.
- [ ] [derived] Each scenario records exact commands, outputs, immutable Git IDs, environment, observed failures and unverified scope — the owner requested real evidence rather than design assertions.
- [ ] [derived] A short repository-local operations manual covers create, pause, resume, checkpoint, integrate and cleanup using the proven workflow — the goal requires a usable handoff.

## Implementation boundary

This task has not started. The audit's next-task sequence links the existing continuity,
expected-tip publication, coordination and durable-record work that feeds these scenarios.
A missing protection is an observed gap with its own canonical follow-up, never a passing
scenario. Tests use disposable repositories and a local remote unless a separately
required provider boundary has already been authorized. This task grants no external
code-review transmission or provider-setting changes.

## Links

- `roadmap/desired-state.md`
- Parent task `2026-08-03-plan-multi-worktree-safety-remediation`
