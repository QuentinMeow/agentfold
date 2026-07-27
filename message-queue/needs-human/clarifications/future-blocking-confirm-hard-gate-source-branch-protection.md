# Before activation, should the hard gate exclude forks and protect every `task/**` branch?

**Status:** waiting
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** Confirm that automatic enforcement may cover only same-repository `task/**` pull requests and that those source branches will prohibit force pushes, deletion, and bypasses.
**Full context:** `handbook/testing-gates.md`
**Why-you-might-care:** Without protected source history, an old successful result could be replaced or misapplied after a branch rewrite; fork pull requests do not share this controlled boundary.
**If-you-do-nothing:** Keep the complete final test manual and do not activate or describe the GitHub hard gate as enforced.
**Resolution evidence:** `memory/decisions/2026-07-27-github-hard-test-gate-activation.md`

**Blocks at:** transition:activate-github-hard-pull-request-gate
**Until then:** The implementation may be reviewed and merged, but GitHub enforcement stays off.

## What you need to know

The earlier activation choice did not say that the pull request's own source branch also needs
protection. The repaired workflow publishes its hard result only when a same-repository branch
named `task/**` opens a pull request or advances normally to a descendant commit. It ignores
forks, rewritten history, and metadata-only events.

## Differences

Answer **yes** to accept that narrower automatic boundary and configure the matching source-
branch rules. Answer **no** if forks, other branch names, force pushes, deletions, or bypasses
must remain supported; the final test then stays manual until another controlled design exists.

## Example

With **yes**, a force-pushed `task/**` branch cannot replace earlier history, and a fork pull
request needs a maintainer-run final test. With **no**, GitHub does not claim this status is a
safe automatic merge requirement.

**Your answer:** ______
