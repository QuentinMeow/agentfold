# Worklog — clear the four stuck queue items against real repository state

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — clear-the-stuck-queue-items (claude)

- Claimed the task on branch task/2026-07-30-clear-the-stuck-queue-items, stacked on
  task/2026-07-30-admit-evidence-that-landed-earlier, which carries the widened
  `resolution_evidence_problem`.
- The stack base already proved the mechanism on a scratch clone. This session applies it to
  the live repository state instead, and separates the one item the rule admits from the
  three it cannot reach.
- The acceptance test passed on live state: the merged code-span repair request and its
  reciprocal task backlink were deleted in one commit, with no evidence file in the edit and
  the whole reconciler at 0 findings. The same edit against the pre-widening checker, in a
  disposable clone at `bceb632`, still reports the finding the widening removes.
- Audited task 2026-07-25-fix-handover-projection-code-span-copy before moving it rather
  than assuming completion, then advanced it to `3_in-review` and `4_done` in two commits.
  Its work was genuinely finished on 2026-07-25; only the queue link had been holding it.
- The three merge reviews turned out not to be a variant of the same problem. Their bound
  ranges and the merge commits that carried them are all ancestors of `main`, so the
  boundary is crossed, and three separate measurements say no repository action can close
  them: the merge replay reports all three unresolved, a properly staged synthetic approval
  in a clone still fails for want of an active base-to-head range at a real merge, and
  supplying that merge's exact range fails because the captured candidate is not that head.
- The surprise was on the deletion path. Staging one review's deletion produced not only the
  expected refusal but a second finding: the task's own acceptance criterion turned back
  into an unqueued human action. The repository refuses to let the ask disappear even when
  the file does, which is a strong argument against clearing these by hand.
- Left all three live, unanswered, and byte-identical. Filed one canonical decision item for
  their disposition, named the three tasks in its boundary, linked it reciprocally from each,
  and appended the measurement to each task's worklog. The recommendation inside it is
  retract-and-refile; the choice is not an agent's.
- Deliberately did not move the three tasks. `3_in-review` is not their false state — their
  worklogs already recorded the merges, and `4_done` is unreachable while a live review sits
  in `Queue actions`. What was missing was evidence that the state is permanent, which is
  now in each worklog and in `verification.md`.
- Noted in passing: task 2026-07-26-resolve-queue-items-whose-evidence-already-merged, still
  claimed by codex in `1_in-progress`, states this same acceptance criterion for the
  code-span item. The stack shipped a narrower rule under a different task, so that record
  now describes work that has already happened by another route. Its disposition was left
  to its claimant.
