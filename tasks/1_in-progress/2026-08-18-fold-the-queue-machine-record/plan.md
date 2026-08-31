# Plan — fold the machine record on new human queue items

Small verifiable steps, each with a named artifact or check.

- [x] 1. `visible_html_text()` in `markdown_semantics.py`, with `contains_raw_html`
      rebuilt on it so no caller reaches into a private name.
- [x] 2. The record region and `record-swallow` in `reconcile.py`, measured unscoped over
      every tracked Markdown file before it is registered.
- [x] 3. `fold-shape` and the narrowed `unsanctioned_raw_html`, replacing the blanket ban
      inside `check_human_attention`, plus the `parsed ⊆ rendered` findings.
- [x] 4. `queue-frozen-skeleton` over mutation events, re-measured against the whole
      repository history for new refusals.
- [x] 5. `--fix-queue-fold` and the advisory `queue-render`.
- [x] 6. The fold in the three human templates, and `.gitattributes`.
- [x] 7. Tests for each of the above, in the existing file's style.
- [x] 8. `verification.md` with the real output of every command run.
