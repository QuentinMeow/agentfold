# Worklog — Keep the owner's words and a goal fit in every task

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-09-04 — claim and design (claude)

- Filed in backlog and claimed in the next coordination commit, from the owner's 2026-09-04 chat request quoted verbatim in `requirements.md`.
- Design input: an online survey of lightweight open-source spec and requirements tools (OpenSpec, GitHub spec-kit, Kiro specs, Agent OS, Cline Memory Bank, Conductor, Doorstop, StrictDoc) and two 2026 papers on specification drift; the borrowed pieces are spec-kit's verbatim input line and dated clarification ledger, Doorstop's `derived` label and suspect-link idea, and Cline's start-of-task re-read, turned into reconciler checks. The survey is recorded in the orchestration run's findings and summarised in `design.md` when it is written.
- Chosen shape: a separate per-task `requirements.md` for owner words (the owner's standing preference), labelled criteria and a `## Fit` section in `task.md`, goal entries with provenance in `roadmap/desired-state.md`, four reconciler check ids activated by task-id date.

## 2026-09-04 — implement, verify, and publish (claude)

- A writer agent implemented the whole change in an orchestration child worktree; the
  repository's core-scope gate accepts core changes only on the `task/` branch, so its two
  records commits were cherry-picked and its three core patches applied and committed in this
  task's worktree through the pre-commit hook. One selection expectation in
  `automation/tests/test_run_tests.py` had to name the new test file before the hook passed.
- Closer adjustments after the writer's report: the pre-activation reminder now fires only for
  tasks still in progress or blocked (17 advisories on finished in-review tasks disappeared),
  the unconfirmed-goal clock starts at the clarification's filing date (8 day-one advisories on
  the July goals disappeared), and this task lists the clarification it filed on its queue line.
- Verified at c42fbd6: 25 focused tests, the serial suite (17 files), the plain and
  merge-transition reconciler runs, and a cold clone whose only findings are two pre-existing
  review items with Git ranges a history-less archive cannot resolve; details in
  `verification.md`.
- Fresh three-lens panel on the diff 7e1a251..c42fbd6 (its first launch was cut off by an API
  session limit and re-run): correctness blocked on three defects — a `[user <date>]` label
  passed when `requirements.md` held only the no-owner-words line, an untouched template Fit
  section was refused where no fit is due, and an absolute clarification path crashed the
  advisory roadmap check; requirements match blocked on two quotations that were not the
  owner's complete words (the 2026-08-03 task's chat entry, and G9 spliced from two sources)
  and noted that this task's own record held a paraphrase and mixed a derived mechanisation
  into a `[user]` criterion; blast radius accepted and listed documentation drift. Every
  finding is fixed in cbdde8a with tests; the verdicts and the fixes are in `verification.md`.
- Filed for the owner: one non-blocking clarification asking whether the eight July goals still
  describe where the repository should go. Recorded as ADR: owner statements transcribe straight
  into confirmed goal entries.
