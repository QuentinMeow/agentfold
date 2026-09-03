# Resume the serial v15 production-contract review when the reviewer service is available

**Status:** open
**Filed:** 2026-09-03, by codex, from task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`
**Action:** When the reviewer service accepts a normal read-only task again, run three fresh v15 reviews one at a time and resolve this item only if all three accept the same immutable commit.
**Full context:** `docs/designs/restack-queue-provenance/pocs/production-contract/README.md`
**Resolution evidence:** `docs/designs/restack-queue-provenance/pocs/production-contract/README.md`
**Blocks at:** event:production-contract-poc-acceptance
**Until then:** Continue reversible workflow planning only; do not integrate the v15 POC, repair the semantic POC, select the final Strategy A design, or start production implementation.

## What you need to know

Production-contract v15 is frozen at local commit
7e47b5b66b579e01e82bb4cbb9e5e622580d4800. Its writer and root checks pass,
including serial repository tests under the owner's 8 GB combined-memory limit.
Three fresh reviewer starts across two available model lineages then returned
the same HTTP 404 before producing a verdict. No platform safety warning
occurred, and those starts count as zero votes.

The run's stricter rule requires every fresh reviewer to accept. Prior approvals
belong to burned v13 and do not carry. Use ordinary software-QA wording, run
exactly one reviewer and one local command at a time, and stop rather than retry
if a platform safety warning appears.

## Done when

Three fresh read-only reviewers independently accept exact commit
7e47b5b66b579e01e82bb4cbb9e5e622580d4800 under the API/session,
evidence/publication, and workflow/public-surface lenses; their commands,
omissions, and 3/3 result are appended to task verification; the production POC
is merged normally into the task integration branch; and this action plus its
exact task Queue actions link are removed in that same committed transition.
