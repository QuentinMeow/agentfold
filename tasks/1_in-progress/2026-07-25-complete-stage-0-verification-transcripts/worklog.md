# Worklog — Record the missing Stage 0 verification transcripts as real command output

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stage-0-transcripts (claude)

- Claimed from `0_backlog` in one coordination commit: `Claimed-by` set, `Queue actions`
  reduced to `none`, the folder moved to `1_in-progress`, and the pickup request
  `message-queue/needs-agent/requests/non-blocking-pick-up-complete-stage-0-verification-transcripts.md`
  deleted.
- The pickup request's prose was already stale. It says the mining task "is still in
  progress and still owns that file, so the ordering dependency is carried by a separate
  future-blocking action listed in this task's `Queue actions`". Neither holds any more:
  the mining task sits in `4_done`, and the future-blocking ordering action was resolved
  in commit `5e94ef7` earlier today, so `Queue actions` listed nothing but the pickup
  request itself. A live queue item's prose is frozen, so it was deleted with the claim
  rather than corrected.
- The approach is salvaged from an earlier cold-boot trial that ran this task inside a
  disposable clone under this session's scratchpad and was never pushed. Its commits
  (`fce3805`, `095866d`, `d3e76bb` in that clone) are the source of two ideas kept here:
  that the before-state needs a control run, and that the fixture cannot live under
  git-ignored `tmp/`. No output was copied from it — every command is re-run in this
  session's own worktree and pasted from this session's terminal.
- Replan on plan step 1. The plan copied the scratch-discipline guardrail and said fixtures
  would live under git-ignored `tmp/`. They cannot. `live_markdown_files` calls
  `path_is_git_ignored` and skips every ignored untracked path, so a fixture there is never
  scanned: a clean report over it is byte-for-byte what an unscanned file prints, and a
  fixture meant to produce a finding produces none. Fixtures were written instead as
  untracked files under `docs/`, checked, and deleted on one shell line; nothing was
  committed, and every transcript ends with the clean `git status --short` that proves it.
  The contradiction is filed as
  `message-queue/needs-agent/requests/non-blocking-let-a-reconciler-fixture-obey-scratch-discipline.md`
  and deliberately not fixed here — which of the two rules gives is a separate decision.
- The before-state needs a control, and this is the cold-boot trial's idea rather than mine.
  A clean reconciler report over a fixture cannot be told apart from the fixture never being
  scanned, so the same absent path with the fragment removed was written to the same
  filename at the same commit; it does produce a finding. Both runs are in the transcript.
- Re-ran every command the trial ran, in this session's own worktrees, and got the same
  results it reported: the anchor hole reproduces at `17c1e16` and is closed today, both
  `link-check` findings appear with the wording it recorded, and `automation/AGENTS.md`
  measures 60 lines against a 60-line budget. The one thing added beyond it: the budget
  boundary is demonstrated rather than asserted, by staging the file with one extra line,
  recording the finding, and restoring it.
- The append tripped `task-action-origin`. The phrase `Creation, run, and deletion were a
  single shell line` is read as an imperative because a bare command verb sits in a
  comma-separated list slot. The check was not weakened; the sentence was reworded and the
  trigger is probed one clause at a time in this task's `verification.md`. It is a second
  symptom of the word-position confusion filed as task
  2026-08-02-stop-a-wrapped-line-from-reading-as-a-command, which reports it arriving from a
  line wrap and against the pull-request body gate rather than a task artifact.
- The pre-existing 906 lines are byte-identical by digest, and `--numstat` reports 164
  insertions with zero deletions.
