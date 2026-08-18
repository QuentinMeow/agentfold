# Fold the machine record on new human queue items, and gate the shape that carries it

**Claimed-by:** claude
**Filed:** 2026-08-18, by claude, from chat
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Every question an agent files the owner ends with ten to fifteen labelled bookkeeping
lines under the line he answers on, and on a phone that is more screen than the question.
This task collapses that block into one tappable `<details>` fold in the three
`needs-human` templates, so items born from today's templates print one grey summary line
instead of a wall of paths and checksums — and it adds the gates that make the new shape
safe to write: a positional record-region check that refuses a field a renderer shows and
no check can read, a shape check for the fold itself, a narrowed raw-HTML rule that admits
exactly the sanctioned fold and nothing else, and a raw-line skeleton gate that closes a
pre-existing hole letting invisible content be appended to a frozen record without
changing its action identity. No live queue item is edited: folding one changes its
identity and `message-queue/AGENTS.md` forbids rewriting a live ask.

## Acceptance criteria

- [x] `templates/queue/{decision,clarification,review}.md` carry the sanctioned fold,
      with two trailing spaces on every field line but the last inside it.
- [x] `record-swallow` blocks a field line the record region shows and `semantic_text()`
      cannot read, scoped by line position rather than by key name.
- [x] `fold-shape` blocks every deviation from the nine fold rules.
- [x] `queue-frozen-skeleton` blocks an edit that leaves `queue_action_identity()`
      unchanged while changing the raw bytes of a live item.
- [x] `check_human_attention`'s raw-HTML rule admits exactly the three anchored fold line
      shapes and nothing else, and adds `parsed ⊆ rendered` visibility findings.
- [x] `--fix-queue-fold` re-emits the canonical block idempotently, losing no field.
- [x] `.gitattributes` opts the queue paths out of `blank-at-eol`.
- [x] `python3 automation/run_tests.py` stays at 15/15 files, and
      `python3 automation/reconcile/reconcile.py --check` stays at 0 blocking findings.
- [x] The new predicates report zero findings when run unscoped over every tracked
      Markdown file in the repository.

## Links

- this task's own `design.md` — what was decided, and the external specification it
  implements, identified by content digest because it is a session artifact
- `memory/decisions/2026-08-02-readability-enforcement-disposition.md` — the live ADR
  that keeps every readability rule out of the blocking tier
