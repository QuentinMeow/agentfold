# Worklog — Stop indented prose from hiding from every repository check

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stop-indented-prose-from-hiding-from-the-checks (claude)

- Reproduced the report against `main`: `semantic_text('- a\n    hidden ...')` returns
  `'- a\n\n'`, so a list-item continuation line is invisible to every gate that reads the
  semantic view.
- Filed the task and claimed it on branch
  `task/2026-08-02-stop-indented-prose-from-hiding-from-the-checks`.
