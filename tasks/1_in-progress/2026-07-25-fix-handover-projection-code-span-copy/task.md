# Let a handover project a queue field that contains an inline code span

**Claimed-by:** claude
**Filed:** 2026-07-25, by claude, from the end-of-session handover of the markdown edge graph Stage 0 work — `docs/designs/markdown-edge-graph.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`

## Goal

A new handover cannot be committed while any live `needs-human/` item carries an inline code
span in its `Why-you-might-care:` or `If-you-do-nothing:` field. The item that was live when
this task was filed has since been folded and deleted, so no session is blocked at this
moment, but nothing prevents the next such field from blocking the end-of-session ritual
again for every session until this is repaired.

The asymmetry is inside `handover_projection_entries` in
`automation/reconcile/reconcile.py`. The expected context is assembled from the queue item's
raw field bytes, read through `text_fields`, which preserves backticks. The handover entry it
is compared against is read through `prose_without_links` in
`automation/check_action_projection.py`, which calls `strip_inline_code` from
`automation/markdown_semantics.py` and blanks every closed code span, delimiters included.
The two sides therefore disagree by exactly the code spans, and the entry is reported as not
copying the creation-snapshot fields.

No handover text can satisfy both sides. A backtick survives `strip_inline_code` only when
its run never finds a closing run of equal width, and the required literal — a single
backtick, the span content, a single backtick — is by construction a closed pair. Five
encodings were tried against both comparison variants and all five failed: literal
backticks, no backticks, backslash-escaped backticks, `&#96;` character references, and
double-backtick wrapping.

Nor can the queue item be changed instead. `Why-you-might-care` and `If-you-do-nothing` are
part of `immutable_action_text`, so editing them yields `queue-resolution`, "live queue
action was rewritten: action identity changed while the queue item remained live". Deleting
the item yields `queue-resolution`, "deleted unresolved queue item: human action was not
committed as folding with a concrete response". The one-time
`human_projection_context_migration` exemption applies only on the queue-v1 activation edge,
which is long past. The repair therefore belongs in the checker.

The blocker that exposed this was the edge-graph freshness-mode decision under
`message-queue/needs-human/decisions/`, whose `Why-you-might-care` opened with a code span
and whose `If-you-do-nothing` contained two more. That item is now folded into
`memory/decisions/2026-07-25-edge-graph-freshness-modes-after-measurement.md` and deleted,
which removes the instance and not the asymmetry, and its exact bytes stay readable in git
history. Nothing in `templates/queue/decision.md`, `templates/handover.md`, or
`history/AGENTS.md` forbids a code span in those fields, and no existing test in
`automation/tests/` exercises one, which is why the path was never covered.

The session that hit this left its handover uncommitted rather than bypassing the hook. The
handover text is reconstructable from that session's commits on `main`, `2abead8` through
`e53371a`.

## Acceptance criteria

- [ ] A new handover whose `Needs your attention` entry copies a queue field containing an
      inline code span passes `python3 automation/reconcile/reconcile.py --check`, with the
      real output recorded in `verification.md`
- [ ] The two sides of the comparison are normalised the same way, so a code span in the
      queue field and the identical code span in the handover entry compare equal, and the
      chosen normalisation is stated in `design.md` rather than left implicit
- [ ] The check still rejects an entry whose copied context differs from the queue field in
      any way other than whitespace reflow, demonstrated by a test that fails before the fix
      and after a deliberate wording change
- [ ] `automation/tests/` gains a regression test covering a code span in
      `Why-you-might-care` and in `If-you-do-nothing`, and it fails against the pre-fix
      checker
- [ ] The same asymmetry is checked for and, where present, repaired in the `needs-agent`
      entry path and in the link-label comparison, or `design.md` records why those paths are
      already safe
- [ ] The blocked session's handover is committed at a fresh conversation path, projecting
      the human queue live at its own creation commit
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0 and
      `python3 automation/run_tests.py` passes, with both outputs recorded in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The comparison that disagrees with itself: `automation/reconcile/reconcile.py`
- The stripping side: `automation/check_action_projection.py` and
  `automation/markdown_semantics.py`
- The item that triggered it, now folded and deleted; its decision record is
  `memory/decisions/2026-07-25-edge-graph-freshness-modes-after-measurement.md`
- Handover schema and its projection rule: `templates/handover.md` and `history/AGENTS.md`
- Guardrail that forbids weakening a check to pass: `automation/AGENTS.md`
