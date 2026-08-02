# Plan — Correct the contract text that no longer matches the code or itself

Small verifiable steps, each with a named artifact or check. Check off as completed —
this file is the task's progress bar. Replan by editing; note big replans in worklog.md.

- [x] 1. Re-verify all fourteen findings against current `main` before any edit — quote both
      sides again from the files and from `automation/reconcile/reconcile.py`. Any finding
      already fixed or refutable is recorded in `design.md` as such and not repaired.
- [x] 2. Finding 1 — file `message-queue/needs-human/decisions/` item from
      `templates/queue/decision.md` asking how the instruction-file review in
      `handbook/principles/provenance-over-position.md` should be spelled under gating v1.
      The principle stays unedited; the item is listed in this task's `Queue actions`.
- [x] 3. Finding 3 — choose between rewriting the `pair` column of
      `handbook/collaboration-modes.md` and scoping the reconciler restriction by mode.
      Argue it in `design.md`; leave the `pair` row, `README.md`, `message-queue/AGENTS.md`,
      and `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md` agreeing.
- [x] 4. Finding 2 — correct the `needs-human/` timing-field grammar in
      `templates/README.md` so it matches the three templates in `templates/queue/`.
- [x] 5. Findings 4 and 6 — document what the link check actually exempts in
      `handbook/naming-conventions.md`, shorten the `README.md` copy to a pointer, and
      replace the restated queue timing-escalation rule with a link.
- [x] 6. Findings 7 and 8 — add the two legal status transitions to the `tasks/AGENTS.md`
      lifecycle diagram and make the `open` → `in-repair` claim rule name its real subject.
- [x] 7. Findings 5 and 10 — remove the dead decision path from `roadmap/current-state.md`
      and repoint the stale citation in
      `2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack`.
- [x] 8. Findings 9, 11, 12 and 14 — rewrite `memory/facts/archived-refs-outside-core.md`,
      correct the ADR-immutability clause in the root `AGENTS.md`, correct the retries
      `README.md` garbage-collection claim, and remove the empty untracked skills directory
      after confirming it holds nothing.
- [x] 9. Finding 13 — correct or route the hard-coded root budget in
      `handbook/principles/progressive-disclosure.md`; the call and its argument go in
      `design.md` either way.
- [x] 10. Verification — write a real `needs-human` item exactly as the corrected
      `templates/README.md` table describes and show `reconcile.py --check` accepting it;
      record that plus `automation/run_tests.py` output in `verification.md`.
- [x] 11. Findings 15-22, added mid-task from a cold-boot trial: verify each in a scratch
      clone or against the source, take the ones that hold, and record any refutation in
      `design.md`. Finding 15 — the missing installer step — is the one with a
      demonstrable failure, so it gets real output in `verification.md`.
