# Complete staged-merge provenance admission

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from the publication audit of task `2026-07-23-first-class-message-queue`
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-staged-merge-provenance-admission.md`

## Goal

Finish the staged-merge and committed-range provenance work preserved in the publication
stack. Every governed history edge imported by a merge must receive the same admission
checks as the corresponding committed range, including handovers that are later deleted
or independently created with byte-identical paths.

## Acceptance criteria

- [ ] Staged merges and explicit committed ranges validate every governed handover add
      edge against that add commit's exact handover, queue, and schema snapshot.
- [ ] A handover added and deleted before the candidate tip cannot bypass projection
      admission.
- [ ] Independent same-path, same-bytes handover creations cannot hide an invalid
      parent history or create an ambiguous immutable incarnation.
- [ ] Unrelated-history roots and exact-parent queue resolutions retain staged/range
      parity without dropping post-fork human responses.
- [ ] Focused regressions, the complete queue suite, the repository runner, and the
      reconciler all pass with their real output recorded.

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- Preserved implementation: publication PR for staged-merge provenance compatibility
