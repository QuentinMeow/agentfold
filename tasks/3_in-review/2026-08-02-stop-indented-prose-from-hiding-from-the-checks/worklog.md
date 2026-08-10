# Worklog — Stop indented prose from hiding from every repository check

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stop-indented-prose-from-hiding-from-the-checks (claude)

- Reproduced the report against `main`: `semantic_text('- a\n    hidden ...')` returns
  `'- a\n\n'`, so a list-item continuation line is invisible to every gate that reads the
  semantic view.
- Filed the task and claimed it on branch
  `task/2026-08-02-stop-indented-prose-from-hiding-from-the-checks`.
- Took the correct route rather than the interim one. The interim rule (blank only after a
  blank line with no list open) fixes both reported shapes but stops recognising real
  indented code inside a list item, which is the commonest shape in `plan.md` and the
  handbook; the correct rule carries paragraph state and a stack of list-item content
  columns, and costs about forty lines.
- `indentation_width` moved into `automation/markdown_semantics.py` and
  `automation/check_action_projection.py` now imports it. `section_entries` was
  deliberately left alone: its content-indent arithmetic is not the CommonMark rule, and
  sharing one function would silently change which continuation lines belong to a
  projection entry. Reasoning is in `design.md`.
- A hand-written matrix of thirty CommonMark cases caught two things the reported
  reproductions did not: a thematic break was not closing the list above it, and one
  "obviously prose" expectation was in fact genuine indented code. Both are now named
  tests.
- One existing fixture relied on the old rule.
  `test_handover_ignores_commented_and_fenced_fake_links` listed a four-space link
  directly after prose among its hidden links; that is a paragraph continuation, so the
  fixture now separates it with a blank line. Its assertion did not change.
- The whole-tree reconciler reports 0 blocking findings both before and after, including
  with `--fail-on-advisory`, so the narrower rule surfaced nothing on any existing file.
  Full suite: 13/13 files.
- Six of the seven named consumers are demonstrably un-blinded. `field_counts` is the
  seventh and could never have been blinded: `FIELD_RE` is anchored at column zero, so a
  field on an indented line was never a field. A test pins that.
