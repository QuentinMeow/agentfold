# Plan — let a handover project a queue field that contains an inline code span

- [x] 1. Claim the task, move it to `1_in-progress`, and resolve its pickup request in one
      coordination commit on `main`.
- [x] 2. Normalise both sides of the handover projection's context comparison through
      `render_inline_code`, leaving the two-element rendered-HTML guard intact.
- [x] 3. Measure whether dropping the code-span blanking changes any existing `needs-agent`
      entry verdict, on the newly-added-handover path and over a `--range` of recent history.
- [x] 4. Take the measured branch: keep the fix unguarded if no existing record changes
      verdict, otherwise scope it to `needs-human` and file the agent-side hole separately.
- [x] 5. Add regression tests in `automation/tests/test_reconcile_queue.py` covering the raw
      backticked spelling, the rendered spelling, a non-copy, a code-span-free item, and a
      projectable code-spanned `needs-human` item.
- [x] 6. Record the chosen normalisation and both rulings in `design.md` with a complete
      `## Core fit` receipt.
- [x] 7. Commit the blocked session's handover at a fresh conversation path on this branch.
- [ ] 8. Record real `--check` and test output in `verification.md` and open the pull request.
