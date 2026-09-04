# Worklog — Stop a restack from being blamed for another branch's deletion

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-31 — Strategy A claim (codex)

- Claimed the task through the repository's atomic direct-`main` coordination lane after the human explicitly selected Strategy A.
- Kept substantive proof-of-concept work, implementation, tests, design evidence, and verification assigned to the task pull request.
- Linked decision receipt: `message-queue/needs-human/decisions/future-blocking-choose-whether-task-claims-must-use-pull-requests.md`.

## 2026-09-04 — review the handoff, cap the task, land the repair on a clean branch (claude)

- Correction to the 2026-09-02–03 record in the archived branch: after v15 froze at
  7e47b5b66b579e01e82bb4cbb9e5e622580d4800, four serial reviewer starts across three model
  lineages returned backend HTTP 404 before execution, not three across two; none produced a
  vote. That record and its immutable handover live under the archive tag named below.
- The owner asked for the handed-off design to be reviewed by a large agent team and revised or
  pushed back as needed. Nine read-only reviewers ran in parallel (orchestration run
  `2026-08-31-prove-the-correct-restack-queue-201c`, findings r37–r45, rulings C17–C22): the run
  had drifted from the owner's request (60 wall-clock hours, 104 commits, 35,463 lines, no
  production change); the label "Strategy A" had moved from the owner's claim-lane answer to the
  classifier design; the selected classifier contract left the defective path unchanged; v15
  failed all three fresh reviews on concrete defects. The design attack (r41) and an executed
  reproduction in a disposable repository (r45) converged on the minimal evidence-validated
  repair, which a writer agent implemented and three fresh reviewers then checked (r46 approve,
  r47 approve, r48 block on unfiled follow-ups, remedied by filing them).
- The owner chose to land only the repair. This branch is cut from the owner-words pull request
  (#96) and carries the repair (`5407000`, twelve `continuity` tests), a one-page design, this
  record, and two follow-up backlog tasks. The original branch tip (bcf7fa3, four prototypes,
  35 amendments, 35 review panels) is tag `archive/2026-09-04-restack-provenance-design-history`;
  the v15 prototype is tag `archive/2026-09-04-production-contract-poc-v15`; pull request #95 is
  closed unmerged. Nothing was deleted from history.
- Fixture lesson from the writer: `fixture_git` collapses two commits with the same parent,
  tree, and message into one object, so the old-tip claim in the "old lineage changed the
  action" test carries its own message.
- After #96 merged into `main` (4ed04f4), this pull request (#97) was retargeted from the
  owner-words branch to `main` and that merged branch was deleted from the remote; the stack
  note left the pull-request body. GitHub's first check runs after the retarget compared a
  merge candidate still built on the old base with the new one and reported "merge candidate
  does not contain this event's base"; this commit refreshes the candidate.
