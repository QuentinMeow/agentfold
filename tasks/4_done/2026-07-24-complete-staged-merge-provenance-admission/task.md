# Complete staged-merge provenance admission

**Claimed-by:** claude
**Mode:** async
**Filed:** 2026-07-24, by codex, from the publication audit of task `2026-07-23-first-class-message-queue`
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** core
**Queue actions:** none

## Goal

Finish the staged-merge and committed-range provenance work preserved in the publication
stack. Every governed history edge imported by a merge must receive the same admission
checks as the corresponding committed range, including handovers that are later deleted
or independently created with byte-identical paths.

> **Closed as already shipped, 2026-08-02, by audit rather than implementation.** The work
> is not preserved in a publication stack any more: it is on `main`, having landed with
> `aca7014 harness: harden queue snapshot boundaries` and merged with the parent as PR #7
> on 2026-07-24. Each criterion below is ticked against a regression that was read, not
> just named, and re-run; `verification.md` carries the real output and the criterion-to-
> evidence map. One coverage gap the audit found is filed separately rather than ticked
> away — see the last criterion's note.

## Acceptance criteria

- [x] Staged merges and explicit committed ranges validate every governed handover add
      edge against that add commit's exact handover, queue, and schema snapshot.
      *Discharged by a family rather than by one test: the staged and committed-range
      halves, the exact-bytes incarnation assertion, the queue snapshot at the add commit,
      and the schema snapshot each have their own regression. The queue-snapshot half was
      proved by printing the real finding, because the named test's assertion is a
      disjunction whose weakest branch would have passed without it.*
- [x] A handover added and deleted before the candidate tip cannot bypass projection
      admission.
      *`test_merge_rechecks_invalid_deleted_side_handover_creation` asserts the same
      subject and message in the staged merge and in the committed range. Exact fit.*
- [x] Independent same-path, same-bytes handover creations cannot hide an invalid
      parent history or create an ambiguous immutable incarnation.
      *Both halves fire in the duplicate-path fixture — the hidden invalid history as a
      creation-snapshot projection failure, the ambiguity as a path-reuse refusal.*
- [x] Unrelated-history roots and exact-parent queue resolutions retain staged/range
      parity without dropping post-fork human responses.
      *Behaviour verified in full, coverage partial. Exact-parent parity has committed
      regressions on both sides. The two post-fork human-response fixtures assert only on
      the staged merge, and no unrelated-history root appears in the queue-resolution or
      handover-projection suites at all. A probe built both and the behaviour holds — the
      committed range emits exactly the staged finding, and an orphan root imported with
      `--allow-unrelated-histories` is refused by both checks. The missing regressions are
      filed as task `2026-08-02-pin-the-unproven-merge-provenance-cases`.*
- [x] Focused regressions, the complete queue suite, the repository runner, and the
      reconciler all pass with their real output recorded.
      *Seven focused regressions, 438 queue tests, 12/12 runner files, 0 blocking
      findings. All output in `verification.md`.*

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- Where the implementation actually landed: `automation/reconcile/reconcile.py`
- The coverage gap this closure found: task `2026-08-02-pin-the-unproven-merge-provenance-cases`
