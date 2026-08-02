# Worklog — judge a handover by its creation grammar

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-01 — judge-a-handover-by-its-creation-grammar (claude, worktree agent-a3dd7926a22a81287)

- Claimed the task and cut `task/2026-08-01-judge-a-handover-by-its-creation-grammar`
  from `0aeb7ff`. This worktree cannot push, so the claim is committed locally only.
- Reproduced both failures on the unmodified tree before touching any code; transcripts
  are in `verification.md`.
- Diagnosis went one level deeper than the filing: the parallel join is only half of it.
  `03ec388` is a plain **ancestor** of both failing records, so the withdrawn `v3` alone
  already respells them. Fixing only the join would have left both failures live.
- The decisive evidence was an audit of all 66 handovers reachable from `main`: every one
  matches the marker in its own creation snapshot, including the single `v3`+new-suffix
  record. That killed the "renumber the rename to v4" option and settled the design.
- Wrote the four tests first and recorded them failing, then split the governing version
  into an admission-edge rejection floor (unchanged) and a creation-snapshot written
  grammar (new).
- Surprise found on the way: the two v2 rejecting clauses were gated on `entry_version ==
  "v2"`, so once `main` moved to v3 the raw-HTML and origin checks were silently **off** —
  while `history/AGENTS.md` says v3 keeps both. Fixed with `entry_version_at_least`, which
  is also what keeps the anti-dodge ratchet turning past a rename.
- Dead end worth not repeating: merging `6c723ef` straight onto the repaired tip conflicts
  in seven files, because PR #44's own conflicts with `main` were already resolved inside
  `e4e631c`. The probe reuses that resolved tree and re-parents it instead.
- Left `handover_liveness_version_for` on the floor deliberately — same defect is possible
  in principle, no reproduction exists, and narrowing it without evidence would weaken a
  live check. Recorded in `design.md` and in the ADR's consequences.
- Local only: this worktree cannot push, so `71fb066` and the probe merge `99a2c84` are
  not on any remote and no CI has seen them.
