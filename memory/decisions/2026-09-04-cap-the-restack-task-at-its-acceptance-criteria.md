# Cap the restack task at its acceptance criteria and park the classifier line

**Status:** decided
**Date:** 2026-09-04
**Decided-by:** human (the owner chose on 2026-09-04, in chat, to land only the repair and keep the design history out of main; transcribed into the task's requirements before folding)
**Description:** The restack false-accusation task is fixed by the minimal evidence-validated continuity-edge repair; the 35-amendment classifier design and the v11–v15 production-contract prototype line are preserved under archive tags, not merged
**Review-by:** 2027-03-03

## Context

Task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion` localised a
reconciler defect to two functions in one file. Between 2026-08-31 and 2026-09-03 the task
branch grew four proof-of-concept programs, a 5,619-line design with 35 amendments, and
fifteen revisions of a production-contract prototype, without changing production. On
2026-09-04 nine review agents found the work had drifted from the owner's request, that the
selected classifier contract left the defective path unchanged, and that prototype v15 failed
three fresh reviews on concrete defects.

## Decision

The task is capped at its six acceptance criteria and fixed by the continuity-edge repair on a
clean branch stacked on the owner-words pull request. The original branch tip and the v15
prototype are kept as annotated tags `archive/2026-09-04-restack-provenance-design-history`
and `archive/2026-09-04-production-contract-poc-v15`; pull request #95, which carried all of
it, is closed unmerged. Nothing was deleted from history.

## Alternatives considered

- Merge the whole branch (#95 as it was): rejected by the owner, because 36,000 lines of
  prototypes and design history would sit on `main` as records nobody runs.
- Repair v15 and restart its panel: rejected, because no acceptance criterion needs the
  classifier.

## Consequences

`main` gains about 130 production lines and twelve tests for this defect. Reopening the
classifier line means a new task traced to a confirmed goal, starting from the archive tag.
Two follow-up defects the review found are filed as backlog tasks.
