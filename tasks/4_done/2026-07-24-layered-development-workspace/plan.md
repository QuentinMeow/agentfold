# Plan — design the layered development workspace and prove its first safe slice

- [x] 1. Audit the queue, branches, worktrees, changes, and open review state.
- [x] 2. Write the layered storage, authority, recovery, and publication design.
- [x] 3. Repair every concrete blocker from the immutable multi-lens review.
- [x] 4. Implement the reversible read-only topology inspector and focused tests.
- [x] 5. Obtain an approve-majority on one repaired immutable candidate.
- [x] 6. Publish the preserved follow-up tasks through the live coordination lane
      after the parent PR is admitted. Confirmed 2026-08-02: all seven sit in
      `tasks/0_backlog/` (`2026-07-24-declare-layered-workspace-manifest`,
      `-record-layered-recovery-evidence`, `-review-layered-instruction-admission`,
      `-review-layered-publication-boundary`, `-route-layered-cross-zone-operations`,
      `-track-layered-override-lineage`, `2026-07-24-complete-staged-merge-provenance-admission`),
      each with its `non-blocking-pick-up-*` request live under
      `message-queue/needs-agent/requests/`.
- [x] 7. Record final verification and leave a complete session handover. Confirmed
      2026-08-02: `verification.md` carries real command output, and the handover is
      `history/conversations/2026-07-24-2305PDT-recover-stranded-merged-prs/handover.md`.
