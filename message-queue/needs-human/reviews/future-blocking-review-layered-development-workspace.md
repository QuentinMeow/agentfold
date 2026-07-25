# Is the layered workspace design and read-only first slice ready to merge?

**Status:** awaiting-artifact
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.
**Full context:** task `2026-07-24-layered-development-workspace`; `docs/designs/layered-development-workspace.md`; `automation/inspect_workspace_boundaries.py`
**Resolution evidence:** `memory/decisions/2026-07-24-layered-development-workspace-review-disposition.md`
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:merge task:2026-07-24-layered-development-workspace
**Until then:** The draft PR may be inspected and revised, but this layer does not merge.
**Look-at:** the zone/authority model in `docs/designs/layered-development-workspace.md`; the bounded claims and failure behavior in `automation/inspect_workspace_boundaries.py`; focused cases in `automation/tests/test_inspect_workspace_boundaries.py`
**Why-you-might-care:** This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries.
**If-you-do-nothing:** This PR remains unmerged, and the deferred coordination tasks are not published.

## What you need to know

The durable design favors a private integration checkout inside a non-Git workspace
envelope, with external no-Git zones and a physically separate public publisher. This
PR implements only a manually invoked, read-only topology inspector. It reports
stronger content, capability, backup, scan, instruction, and publication claims as
uninspected, unverified, or blocked instead of authorizing them.

## Differences

- **Approve:** accept the exact design and bounded read-only inspector as the first
  reversible slice; later capabilities still require separate tasks and reviews.
- **Request a named change:** keep the merge boundary closed while the specific
  contract, confidentiality, portability, or failure-mode issue is repaired.
- **Reject:** decline this architecture/first slice; no publisher, mount, migration,
  or automatic public operation is authorized by this proposal.

## Example

If a declared private root overlaps the public publisher or shares its object store,
the inspector blocks rather than calling the layout safe. Even when roots are
topologically separate, it still refuses to claim that content was scanned, backups
were observed, instructions were admitted, or publication is authorized.

Do not answer this item while its status is `awaiting-artifact`. After the isolation PR
merges and the exact base is bound, copy `Review revision` into `Reviewed revision`
with the answer.

**Your review:** ______
