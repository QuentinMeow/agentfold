# Majority over single agent

Any single agent run can be confidently wrong. For judgments that matter — merge
reviews, risky-claim verification, ambiguous design calls — use several independent
agents and take the majority, instead of trusting one agent's assertion.

## Rules

- **Independence is the point.** Reviewers get fresh context and must not see each
  other's verdicts (or the author's self-assessment) before forming their own. Three
  agents sharing one context are one agent with extra steps.
- **Diverse lenses beat clones.** Give each reviewer a distinct angle — correctness,
  security, simplicity, does-it-match-the-plan — rather than the same prompt three
  times. Redundancy catches noise; diversity catches blind spots.
- **Adversarial framing.** Ask reviewers to *refute* ("find a concrete input where this
  breaks"), not to appraise. Tell them to flag only findings with a failure scenario —
  reviewers over-report when asked for opinions.
- **Majority decides, human breaks ties.** In `autonomous` mode a majority verdict
  merges or blocks; a split vote becomes a human-review queue item whose filename says
  whether the current or a future transition waits.
- **Reserve it for stakes.** Voting is expensive. Typo fixes need one agent; anything
  hard to reverse (see `../collaboration-modes.md`) deserves a panel. The protocol
  lives in `skills/adversarial-review/`.

## Why

Wrong-but-plausible is the signature failure of AI agents, and it is exactly the
failure independent sampling repairs: errors are random, so they disagree; truths are
stable, so they agree. Majority behavior drives the system toward correctness without
requiring any individual run to be trustworthy — the same bet as
`eventual-consistency.md`, applied to judgment instead of state.
