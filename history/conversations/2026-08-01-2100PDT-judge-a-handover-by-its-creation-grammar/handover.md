# Handover — judge-a-handover-by-its-creation-grammar

**Session:** 2026-08-01 21:00–21:55 PDT, local time, claude (worktree agent-a3dd7926a22a81287)
**Task:** 2026-08-01-judge-a-handover-by-its-creation-grammar
**Mode:** async
**Queue projection:** v1

## What happened

- A check was demanding that finished session records be rewritten. It judged each
  handover by the newest schema version it could find anywhere in the repository's
  history, including versions that arrived after the record was written. Since a
  committed handover may never be edited, the only repair it offered was one the
  repository forbids, so the branch carrying that record could never merge.
- Two real failures came from this. PR #44 reported nine blocking findings even though it
  merged cleanly and passed every other check. The same trap was already sitting on
  `main`, waiting to fire on one August 1st record the next time anything looked at it.
  Both were reproduced first, on the untouched tree, and both now report zero.
- The cause was a version number used twice for two different things. `v3` was switched
  on, switched back off a day later, and then handed to an unrelated change a week after
  that. The check could not tell the two meanings apart.
- A record is now judged by the version written in the repository at the moment that
  record was created. Nothing that happens later can change it.
- Found and fixed on the way: two safety checks — one that rejects hidden HTML in a
  handover, one that rejects a request smuggled in outside the proper section — had
  silently switched themselves off when the version moved to v3, even though the contract
  says v3 keeps both. They are back on.

## How it works now

Every new handover is now measured against two separate things. Its wording is measured
against the schema version the repository declared at the moment that record was created,
and that measure is fixed forever after. The rules it may not break come from the newest
version reachable at the merge, so a branch cut before a stricter rule still does not
escape it, and a later version can never turn a rule off. Nothing about a committed
record's bytes was touched: all 66 existing records already match the version they were
written under.

## Decisions made for you

- An obligation may only be placed on an already-committed record if its author could
  have satisfied it while writing. Reasoning and the rejected alternatives:
  [memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md](../../../memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md).
- Renumbering the reused version was considered and rejected, because one record already
  on `main` was written under the reused number and would break. Same file.
- Liveness governance was deliberately left alone: the same flaw is possible there in
  theory, but nothing reproduces it, and changing it without evidence would weaken a
  live check. Recorded in the task's `design.md`.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Decide whether the repository should refuse to merge a pull request whose `reconcile-and-test` check has not passed, and say which of the options below you want.](../../../message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md) — Why this matters: Every safety rule in this repository is currently a suggestion — the checks run, they can go red, and the merge button works anyway. — If you do nothing: The checks keep running and keep being ignorable, and a branch that goes red can still land on `main` exactly as one did on 2026-08-01.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.

## Dead ends

- Fixing only the parallel-branch half of the problem would not have worked. The commit
  that first declared the reused version is a plain ancestor of both failing records, so
  each one was being mis-versioned twice over. Both halves had to go.
- Renumbering the reused version to a fresh number looked clean until the records were
  counted: one handover already on `main` was written under the reused number and uses
  the newer wording, so renumbering would have broken a record to fix a check.
- Merging PR #44's branch straight onto the repaired tip conflicts in seven files,
  because that branch's conflicts with `main` were already resolved inside the existing
  merge commit. The probe was built from that already-resolved tree.

## Next steps

None.

## Deep links

- Task folder: [2026-08-01-judge-a-handover-by-its-creation-grammar](../../../tasks/3_in-review/2026-08-01-judge-a-handover-by-its-creation-grammar) · Worklog: [worklog.md](../../../tasks/3_in-review/2026-08-01-judge-a-handover-by-its-creation-grammar/worklog.md) · Verification: [verification.md](../../../tasks/3_in-review/2026-08-01-judge-a-handover-by-its-creation-grammar/verification.md)
- Commits: `ac5dae2`, `863810f`, `71fb066` on `task/2026-08-01-judge-a-handover-by-its-creation-grammar`, plus the local merge probe `99a2c84`. Nothing was pushed.
