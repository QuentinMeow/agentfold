# Plan — Let a queue item resolve when its resolution evidence landed in an earlier commit

**Superseded 2026-08-02 — none of the eight steps below was completed, and none is
checked.** Step 1 is the only one with any surviving product, and it survives inside
another task's records rather than here. The defect these steps were written against was
repaired by `2026-07-30-admit-evidence-that-landed-earlier` (pull request 38) with a
deliberately narrower rule, and the creation-snapshot baseline chosen in step 2 was
afterwards discarded by name: `tasks/4_done/2026-07-30-cache-reconciler-git-object-reads/design.md`
calls this branch's resolution-evidence rule "found harmful", and
`2026-07-31-finish-the-replacement-ref-boundary` records that it and its 24 evidence-lineage
tests were "NOT ported — rejected by measurement". Steps 6 through 8 therefore describe
tests and a review that do not exist anywhere. `verification.md` holds the commands that
establish each of those claims.

- [ ] 1. Map the current ordinary `needs-agent` request deletion and claim evidence paths, including the live stuck item.
- [ ] 2. Compare lineage-window designs and choose a fail-closed baseline tied to the item's unique current-incarnation creation snapshot.
- [ ] 3. Implement the chosen ordinary-request-only rule: every declared evidence path must have readable surviving final bytes that differ from its creation-snapshot bytes; paths must fail closed on absence or unreadability.
- [ ] 4. Preserve the independent status-only `open` → `in-repair` claim requirement and leave needs-human, generated-retry, task-pickup, and custom paths unchanged.
- [ ] 5. Correct and document the contradictory acceptance wording on the task branch: the comparison begins after creation, not before it.
- [ ] 6. Add discriminating regression tests, including merged-before-claim evidence, unchanged evidence, reverted evidence, and unavailable evidence paths.
- [ ] 7. Resolve the live ordinary request only after the checker admits its already-merged evidence; complete the dependent task lifecycle records.
- [ ] 8. Record full verification, independent review, and publish the reviewed branch.
