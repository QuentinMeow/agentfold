# Plan — mine markdown co-change couplings and validate heading anchors

Ten steps, ordered so the cheap fix lands first and the gating experiment lands last.
Each step names what exists or passes when it is done. New paths this task creates are
written without backticks until they exist, so the `link-check` pass stays honest.

- [ ] 1. Capture the live anchor hole as recorded output: a scratch fixture under `tmp/`
      containing a link of the form `<absent-path>.md#<absent-anchor>` passes
      `python3 automation/reconcile/reconcile.py --check` today, and that transcript sits in
      `verification.md` as the before-state.
- [x] 2. Split path from fragment in `check_links` so the existing root/local existence
      logic runs on the path half. Milestone: the same fixture now yields a `link-check`
      finding naming the missing path, and `--check` on the real repository still reports
      the findings it reported at step 1.
- [x] 3. Add ATX heading extraction and a GitHub slug function to the reconciler — lowercase,
      spaces to hyphens, punctuation dropped, duplicate slugs suffixed `-1`, `-2` — reusing
      `semantic_text` from `automation/markdown_semantics.py` so fenced code and HTML
      comments cannot donate fake headings. Milestone: a fixture link to an existing file
      with a wrong fragment yields a second, distinct finding that names the fragment, and a
      correct fragment yields nothing.
- [x] 4. Cover both halves with unit tests. Corrected 2026-07-25 to name where they actually
      landed: the eight anchor tests were appended to `automation/tests/test_reconcile_queue.py`
      rather than put in a separate file, so they ride the suite's slowest file — roughly 98
      seconds of the ~205 — instead of avoiding it. Milestone: `python3 automation/run_tests.py`
      green, with that file in its PASS lines.
- [x] 5. Add the mining CLI automation/mine_cochange.py: stdlib only, a `report` verb that
      always exits 0, walking `git log --name-only` over markdown-touching commits, counting
      directed file-pair co-occurrence, and printing pairs at support ≥ 3 commits and
      confidence ≥ 0.8 with a 40-file commit-size cap, a stop-list for files the contract
      requires to change every session, same-directory pairs suppressed, and the shared
      commit subjects printed as each pair's evidence. Milestone: the report runs on this
      repository and its output is pasted verbatim into `verification.md`.
- [x] 6. Add the append-only ledger beside the tool and the verbs that write one durable
      verdict per candidate — accepted, or rejected with a one-line reason. Milestone: a
      rejected pair is absent from the next report, re-recording the same pair is refused
      rather than silently appended, and the report prints the rejection rate against the
      design's bands (under 10% on target, 10–25% probation, above 25% off).
- [x] 7. Unit-test the CLI in a new file automation/tests/test_mine_cochange.py against a
      fixture repository built in a temporary directory: the support floor, the confidence
      floor, the commit-size cap, the stop-list, same-directory suppression, ledger
      suppression, rejection-rate arithmetic, and exit code 0 on a report that has
      couplings to show. Milestone: `python3 automation/run_tests.py` green.
- [ ] 8. Free one line in `automation/AGENTS.md` by tightening existing prose, then add the
      CLI's row to its tool table. Milestone: the file is at most 60 lines, `agents-budget`
      passes, and the diff shows a prose reflow rather than a deleted rule.
- [x] 9. Run the gating experiment and write it down: for the two hottest markdown files in
      this repository, take the top-ranked couplings and record, per coupling, whether it is
      a real dependency and whether a hand-authored edge would have said anything the mined
      pair plus its shared commit subjects did not. Milestone: `design.md` carries the
      verdict, including the explicit finding if the mined list is already sufficient, in
      which case the later stages are unjustified and the project stops here.
- [ ] 10. Record every command and its real output in `verification.md`, note the warm-up
      limitation there, and move the task to `3_in-review`. Milestone: `--check` and
      `run_tests.py` transcripts present, `worklog.md` appended, the task folder in
      `tasks/3_in-review/`.

Steps 1, 8, and 10 stay unchecked at `4_done`. Step 1's before-state transcript and step 8's
`agents-budget` output never reached `verification.md`, and step 10 owed exactly those
sections; backlog task 2026-07-25-complete-stage-0-verification-transcripts carries them. The
step 8 code did land — `automation/AGENTS.md` names the CLI in its tool table and the diff
was a prose reflow, not a dropped rule — so only its recorded output is outstanding. The task
also went to `4_done` directly rather than through `3_in-review`, because its pull request had
already merged by the time its status was reconciled.

## Known obstacles

- `automation/AGENTS.md` sits at exactly 60 of its 60 permitted lines, and its own contract
  requires a table row for every tool. Step 8 therefore buys the new row by tightening
  prose. Deleting a rule to make room is not an option — `automation/AGENTS.md` itself says
  a check is never weakened to pass.
- Everything under `automation/` is a core path, so `automation/check_core_scope.py` requires
  the branch named task/2026-07-25-mine-markdown-cochange-couplings, this task folder,
  `Repository scope: core`, and the completed substitution receipt in `design.md`. Tracked
  executables also stay on repository-local state: no home directory, no `expanduser`, no
  user-global cache for the ledger.
- A full `git log` walk inside a reconciler check would be quadratic, because
  `check_task_admission_history` re-enters the checks under `git_revision_candidate`. That
  cost, together with the absence of finding severities, is why mining stays a standalone
  advisory CLI at this stage rather than a `CHECKS` entry.
- The repository test suite runs about 205 seconds, dominated by
  `automation/tests/test_reconcile_queue.py`, and the pre-commit hook runs it on every
  commit. Both new test files are therefore separate files, and commits are batched at the
  milestones above rather than per edit.
- This repository holds only four days and roughly 107 in-scope markdown-touching commits,
  while the published work in this area discards the first few hundred change records as
  warm-up. Every mined number from step 5 onward is provisional and will move as history
  grows, in an unknown direction. That belongs in `verification.md` as a stated limitation
  of the measurement, not as a defect of the tool.
