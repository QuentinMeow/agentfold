# Rewrite the guides a human reads so they obey their own readability rules

**Claimed-by:** claude (session 2026-08-01-2317PDT)
**Filed:** 2026-08-01, by claude, from the owner's chat request to make messages readable
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`handbook/human-action-guide.md` tells agents to write for a non-expert who will answer
from a phone. It is itself 130 lines of unbroken specialist prose: single paragraphs that
chain provider-adapter identity, review binding, merge-queue replay, and GitHub ruleset
names without a heading, an example, or a gloss. `message-queue/AGENTS.md` has the same
problem in its "Lifecycle and content" list. An agent that reads them cannot reliably
extract the rules, and a human who opens them learns nothing.

Rewrite them under the skill's own rules — lead with the rule, gloss the jargon, put the
provider-specific and edge-case depth behind its own heading — while changing no normative
content. Every rule that exists today must still exist, in the same file or in a file this
one links, and the reconciler checks that depend on these documents must still pass.

This is a rewrite for readability, not a redesign. Any rule that seems wrong gets filed,
not silently dropped.

## Acceptance criteria

- [ ] `handbook/human-action-guide.md` is restructured with a stated rule per section,
      at least one concrete example per non-obvious rule, and provider-specific depth in
      its own linked section.
- [ ] Every normative statement present before the rewrite is still present after it —
      proven by a rule-by-rule inventory recorded in `verification.md`.
- [ ] `handbook/decision-guide.md` and the `templates/queue/` guidance comments agree with
      the rewritten guide and restate none of it.
- [ ] Uncommon terms are glossed in parentheses at first use in each rewritten file.
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [ ] `python3 automation/run_tests.py` passes.

## Links

- `handbook/human-action-guide.md` — the document under rewrite
- `handbook/principles/progressive-disclosure.md` — the rule this rewrite applies
- skills/explain-to-human/ — the craft the rewrite follows
