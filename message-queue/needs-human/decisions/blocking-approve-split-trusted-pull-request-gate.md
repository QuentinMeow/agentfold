# Should AgentFold install the split trusted pull-request gate?

**Status:** folding
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** Choose whether to authorize the split trusted pull-request gate or keep final verification manual/external.
**Full context:** `handbook/testing-gates.md`
**Why-you-might-care:** This decides whether AgentFold may claim a hard pull-request boundary instead of only producing candidate-controlled execution evidence.
**If-you-do-nothing:** The task remains blocked and no trusted provider workflow is installed.
**Resolution evidence:** `memory/decisions/2026-07-27-trusted-pull-request-gate-boundary.md`
**Blocks now:** task:2026-07-27-configure-test-gates-and-time-budgets

## What you need to know

The current pull-request workflow is part of the proposed change, so the candidate can replace
or skip the code judging itself. The safe proposed design uses a trusted base-revision job only
to verify exact identities and prepare a Git bundle; a separate fresh job with no repository
permissions or secrets runs the trusted base controller against the candidate bytes.

## Differences

- **Authorize the split gate:** AgentFold installs the trusted preparer plus credential-free
  candidate runner and can support the configured hard pull-request mode once its stable check
  is required by branch protection. Candidate code never runs in the token-bearing preparer.
- **Keep manual/external final verification:** AgentFold does not add the sensitive provider
  workflow and reports enforcement as unobserved. Repositories may run the complete lane
  explicitly or supply another controlled adapter, but this task cannot claim an included hard
  GitHub boundary.

## Options

### Option A — Authorize split gate
Add the least-privilege two-job GitHub adapter and review it as a security boundary.
*Example consequence:* A pull request cannot approve itself by replacing the gate script;
candidate tests run only in the fresh job with no secrets and `permissions: {}`.

### Option B — Keep manual/external
Ship the local lanes and provider-hard controller without installing the trusted GitHub adapter.
*Example consequence:* The final suite remains available, but repository settings or another
adapter must enforce it and AgentFold reports the included workflow as untrusted evidence.

## Recommendation

Option A, because the starter policy already selects hard pull-request mode and the split design
keeps candidate execution out of the token-bearing trusted preparer.

**Your answer:** option A.
