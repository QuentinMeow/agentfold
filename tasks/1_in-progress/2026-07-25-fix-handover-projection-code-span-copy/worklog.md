# Worklog — let a handover project a queue field that contains an inline code span

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — fix-handover-projection-code-span-copy (claude)

- Claimed the task on `main` and removed its completed pickup request in the same
  coordination commit.
- Disproved the incoming diagnosis before changing anything. It read the two-element loop
  over `prose_without_links(entry)` and `prose_without_links(rendered_human_text(entry))`
  as a raw-versus-rendered choice that wrongly demanded both. Both elements run
  `prose_without_links`, so both blank code spans, and the two forms differ only when the
  entry carries raw HTML. Accepting either instead of both was measured as a no-op.
- Repaired the real asymmetry instead: both sides of the copy comparison now normalise
  through `render_inline_code`, matching the adjacent action-label check, which already
  renders code spans via `normalized_action_tokens`. The rendered-HTML guard is untouched.
- Measured the unguarded `needs-agent` tightening rather than deciding it from first
  principles: zero new findings on `--check`, on both CI range forms, and on the maximal
  `root:` sweep, whose 55 pre-existing findings are byte-identical before and after. The
  tightening was taken and pinned with a test.
- Added six regression tests; the three code-span projection tests and the agent-entry
  test fail against the pre-fix checker, while the two rejection tests pass on both sides.
