# Worklog — complete staged-merge provenance admission

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — backlog disposition audit (claude)

- Claimed to audit rather than to implement. A backlog triage suggested the four
  behavioural criteria already map onto regressions on `main`; a triage note is a lead, so
  the session's job was to read each named test and decide whether it asserts what the
  criterion claims.
- The implementation is on `main`. `handover_current_incarnation_text`,
  `newly_added_handovers` and `check_handover_queue_projection` all live in
  `automation/reconcile/reconcile.py`; the commit that introduced the incarnation
  resolution is `aca7014 harness: harden queue snapshot boundaries`, and
  `git branch --contains aca7014` lists `main`. The parent's publication branch merged as
  PR #7 on 2026-07-24, so "preserved in the publication stack" is no longer where this
  work lives.
- The pickup request stated the remaining gap more precisely than the task did: creation
  checks were selected from the final path set, so a governed handover add followed by a
  delete, or one of two byte-identical parallel additions, could escape exact
  creation-snapshot validation. Both are now caught, and both are caught in the staged
  merge and in the committed range.
- One named regression looked weaker than its name.
  `test_staged_merge_rechecks_duplicate_path_side_handover_creation` asserts a disjunction
  of three substrings, and one disjunct ("reuses a path") would fire on the path collision
  alone without proving anything about creation snapshots. Printing the real findings
  settled it: the check emits both `reuses a path that already has a committed governed v1
  handover incarnation` and `new handover is not an exact projection of the live human
  queue: not live message-queue/needs-human/reviews/future-blocking-review-release.md`.
  The second is only reachable if the side branch's add was validated against the side
  branch's own queue snapshot — the merged tree contains that queue file. The criterion is
  genuinely discharged; the assertion is just looser than the behaviour.
- Criterion 4 is the one whose named regressions do not reach all of it. Two of the three
  assert only on the staged merge, and none of them builds an unrelated-history root. A
  probe reproduced both fixtures and carried them one commit further into a committed
  range, and built an orphan root imported with `--allow-unrelated-histories`. All three
  behave correctly — the real findings are in `verification.md`. The behaviour is present;
  what is missing is a committed regression pinning it. That gap is filed as task
  `2026-08-02-pin-the-unproven-merge-provenance-cases` rather than left inside this record.
- Closed as already shipped. Nothing in this task was implemented by this session; the
  evidence is entirely a reading and a re-run of `main`.
