# Use the existing atomic claim lane for the first proof-of-concept task

**Status:** decided
**Date:** 2026-08-31
**Decided-by:** human (owner selected Strategy A in chat, transcribed before folding)
**Description:** The first proof-of-concept task uses AgentFold's existing narrow direct-main claim lane; substantive work stays in its pull request
**Review-by:** 2027-02-27

## Context

The selected task could not cross its start boundary until the owner chose between the
repository's existing atomic claim transaction and a not-yet-designed pull-request claim
protocol. The owner selected Strategy A and required verified proof of concepts before any
production implementation.

## Decision

Apply the existing Git workflow to task
`2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`: its atomic claim
and required initial task records use the already-documented direct-`main` coordination lane.
Proof-of-concept artifacts, design choices, production code, tests, and verification evidence
remain reviewed work on the task branch and pull request.

This record authorizes no new direct-`main` write category and changes no repository contract.

## Alternatives considered

- Invent a pull-request claim transaction before starting: rejected for this task because no
  one-winner protocol has been designed or fault-tested.
- Start proof-of-concept writers before the claim: rejected because the repository contract
  requires its claim lifecycle to complete first.

## Consequences

The task can begin without weakening claim exclusivity. Its implementation cannot begin until
competing proof-of-concept results are captured and independently verified. Any future change
to the repository-wide claim protocol remains separate reviewed work.
