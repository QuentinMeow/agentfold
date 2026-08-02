# Stop indented prose from hiding from every repository check

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from a reported guardrail bypass — `automation/markdown_semantics.py`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-indented-prose-from-hiding-from-the-checks.md`

## Goal

`strip_indented_code` in `automation/markdown_semantics.py` blanks every line that begins
with four spaces or a tab. That is not what an indented code block is. CommonMark says an
indented code block cannot interrupt a paragraph, and that inside a list item the code
threshold moves to the item's content column plus four. So an ordinary list-item
continuation line is prose a human reads, and the checker sees nothing:

```
source  : '- a\n    hidden `docs/missing.md` and **Field:** value\n'
semantic: '- a\n\n'
```

`semantic_text` composes `strip_indented_code`, so this blind spot is inherited by every
gate that reads the semantic view — the reconciler, the core-scope gate, and the action
projection gate — and `automation/check_action_projection.py` applies it a second time to
an explicitly rendered-human view. Three consequences are reproduced end to end: a live
queue item can be rewritten without tripping `queue-resolution`, an unqueued human ask in
a task record escapes `task-action-origin`, and `link-check` misses a broken link one
level inside a list. The same blindness reaches `task_tokens`,
`task_status_references`, `human_header_block`, `human_attention_above_fold`,
`field_counts`, `section_body`, and `level_two_section_body`.

The rule this task lands: a line is blanked as indented code only when CommonMark would
parse it as one — four columns past the enclosing list item's content column, and not
interrupting an open paragraph. The docstring on `semantic_text` currently claims "only
genuine indented-code lines change"; it becomes true or it is corrected.

## Acceptance criteria

- [ ] `semantic_text("- a\n    b\n")` retains `b`, and a regression test asserts it
- [ ] Rewriting a live queue item's `Action` line, written as a four-space continuation
      under a list item, changes `queue_action_identity` and makes `queue_mutation_problem`
      return a problem, exactly as the same edit at top level already does
- [ ] An unqueued human ask written as a four-space continuation under a list item in a
      task record is reported by `task-action-origin`, exactly as the same sentence at top
      level already is
- [ ] A broken repository link written as a four-space continuation under a list item is
      reported by `link-check`, exactly as the same link at top level already is
- [ ] `task_tokens`, `task_status_references`, `human_header_block`,
      `human_attention_above_fold`, `field_counts`, `section_body` and
      `level_two_section_body` each read text that a four-space list continuation carries,
      with a test per consumer group
- [ ] A genuine top-level indented code block — a blank line followed by a four-space
      indented line — is still blanked, and the existing case in
      `automation/tests/test_reconcile_queue.py` passes unmodified
- [ ] `python3 automation/reconcile/reconcile.py --check` on the whole tree reports no
      finding that the pre-change tree did not already report, so the narrower rule adds no
      false positive to any existing file
- [ ] New tests live in a new markdown-semantics test file under `automation/tests/` and
      register their owning inputs in the input-ownership table in `automation/run_tests.py`
- [ ] `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/markdown_semantics.py` is a core path

## Links

- The function and its false docstring: `automation/markdown_semantics.py`
- The gates that inherit the view: `automation/reconcile/reconcile.py`,
  `automation/check_action_projection.py`, `automation/check_core_scope.py`
- The invariant a hidden line evades: `message-queue/AGENTS.md`
- Why a check is never weakened to pass: `automation/AGENTS.md`
