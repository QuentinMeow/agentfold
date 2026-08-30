# Plan — Record the missing Stage 0 verification transcripts as real command output

Four transcripts are appended to the `verification.md` of task
2026-07-25-mine-markdown-cochange-couplings. Every fenced block is pasted terminal output
from a run made in this session. Fixtures are untracked Markdown files written at a path
the reconciler actually scans, run, then deleted in the same command — git-ignored `tmp/`
cannot hold them, because `live_markdown_files` skips ignored paths and a fixture there
would never be scanned at all.

- [x] 1. Reproduce the anchor-hole before-state in a detached worktree at `e52f68e^`: one
      fixture link of the form `<absent-path>.md#<absent-anchor>`, the real
      `reconcile.py --check` output that lets it pass, and a control run at the same commit
      proving the file was scanned at all
- [x] 2. Run the same fixture at today's tip and paste the `link-check` finding naming the
      missing path
- [x] 3. Run a fixture whose path exists but whose fragment does not, and paste the second,
      distinct `link-check` finding naming the fragment
- [x] 4. Measure `agents-budget` against `automation/AGENTS.md` and paste both the budget
      and the real line count
- [x] 5. Append the four sections to the mining task's `verification.md`, leaving its
      existing 906 lines byte-identical (digest + `git diff` prove it)
- [x] 6. Re-file the scratch-discipline contradiction as a `needs-agent` request from
      `templates/queue/request.md`
- [x] 7. Write this task's own `verification.md`: the staged `reconcile.py --check` run and
      the `run_tests.py` run, both as real output
