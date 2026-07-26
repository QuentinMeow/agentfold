# Plan — Let a queue item resolve when its resolution evidence landed in an earlier commit

- [x] 1. Map the current ordinary `needs-agent` request deletion and claim evidence paths, including the live stuck item.
- [x] 2. Compare lineage-window designs and choose a fail-closed baseline tied to the item's unique current-incarnation creation snapshot.
- [x] 3. Implement the chosen ordinary-request-only rule: every declared evidence path must have readable surviving final bytes that differ from its creation-snapshot bytes; paths must fail closed on absence or unreadability.
- [x] 4. Preserve the independent status-only `open` → `in-repair` claim requirement and leave needs-human, generated-retry, task-pickup, and custom paths unchanged.
- [x] 5. Correct and document the contradictory acceptance wording on the task branch: the comparison begins after creation, not before it.
- [x] 6. Add discriminating regression tests, including merged-before-claim evidence, unchanged evidence, reverted evidence, and unavailable evidence paths.
- [x] 7. Resolve the live ordinary request only after the checker admits its already-merged evidence; complete the dependent task lifecycle records.
- [x] 8. Record full verification and the three blocked independent review rounds, including an explicit per-method pre-repair test matrix; repair every accepted finding.
- [ ] 9. Obtain approving independent review of the final immutable revision and publish the reviewed branch.
