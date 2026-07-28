# Use a trusted preparer and credential-free runner for hard pull-request tests

**Status:** superseded
**Date:** 2026-07-27
**Decided-by:** human
**Description:** Hard pull-request tests use trusted base code to prepare the exact candidate, then run candidate tests in a fresh job with no repository permissions or secrets
**Review-by:** 2027-01-23
**Superseded-by:** `memory/decisions/2026-07-27-manual-only-test-gate-replan.md`

## Context

AgentFold's test policy can require complete tests before a pull request merges. A normal
`pull_request` workflow cannot prove that boundary because the pull request can modify or skip
the workflow and gate code judging it. The approved design and threat boundary are described in
`handbook/testing-gates.md`.

## Decision

Install a split GitHub pull-request gate. A trusted base-revision preparer verifies the event's
exact base, head, synthetic merge, and displaced-tip identities and packages the Git objects
without executing candidate code. A separate fresh job with no repository permissions, no
secrets, and no persisted credentials runs the trusted base controller against that exact
candidate with provider-hard behavior.

The stable result becomes hard enforcement only when repository settings require it and prevent
direct pushes. Schema version 1 continues to reject merge queues because it has no
`merge_group` candidate adapter.

## Alternatives considered

- Keep complete tests manual or externally enforced — safer to install, but it leaves the
  starter hard pull-request policy without an included trusted GitHub boundary.
- Run the complete gate directly from the pull request checkout — rejected because the
  candidate can replace or skip its own judge.
- Execute candidate tests in the token-bearing trusted job — rejected because untrusted code
  could read or misuse trusted event credentials.

## Consequences

The workflow must keep candidate execution out of the trusted preparer and must test the exact
candidate identity carried between jobs. Provider settings remain part of the assurance claim;
without the required check and direct-push protection, reports stay `unobserved`. Any future
merge-queue support needs a separately designed and reviewed adapter.
