# May this task switch the starter final gate to manual-only verification?

**Status:** waiting
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** Answer yes or no: may this task switch the starter final mode from hard to manual, remove the unsafe automatic publisher, keep hard syntax reserved and fail-closed, and move real automatic enforcement to the two follow-up tasks?
**Full context:** `handbook/testing-gates.md`
**Why-you-might-care:** The current runner can report success after candidate code exits its own interpreter early, so its result cannot safely authorize an automatic merge.
**If-you-do-nothing:** The task remains in progress, final verification stays manual in practice, the automatic publisher is not activated, and no hard-enforcement claim is made.
**Resolution evidence:** `memory/decisions/2026-07-27-manual-only-test-gate-replan.md`

**Blocks at:** transition:review task:2026-07-27-configure-test-gates-and-time-budgets
**Until then:** Test-only migration work and follow-up planning may continue, but the production policy and workflow do not switch and this task does not enter review.

## What you need to know

The base-pinned test floor prevents a pull request from deleting the trusted tests, but those
tests still run inside a Python interpreter the candidate can terminate with `os._exit(0)`
before later assertions execute. The current publisher cannot independently tell that apart
from controlled completion, so automatic enforcement needs an external test oracle and a
separately controlled publisher before it is safe.

## Differences

Answer **yes** to finish this task with explicit manual final verification, remove its unsafe
automatic publisher, and leave hard transition invocations blocked until the two follow-up
tasks deliver an external completion oracle and an OIDC-backed App publisher. Answer **no** to
keep the current hard-mode proposal in progress while another safe plan is designed; it still
must not be activated or described as enforced.

## Example

With **yes**, a maintainer deliberately runs the complete final gate and judges its cooperative
evidence, while GitHub receives no automatic hard status from this task. With **no**, this task
does not enter review and neither the current publisher nor a manual-only replacement ships.

**Your answer:** ______

<!-- A concrete response is immutable. If it is a counter-question, fold the answer into
Resolution evidence and create a same-timing successor with **Supersedes:** `<this path>`. -->
