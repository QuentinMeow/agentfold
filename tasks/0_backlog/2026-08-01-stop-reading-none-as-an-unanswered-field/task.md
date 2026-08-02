# Stop treating "none" as an unanswered field

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `automation/reconcile/reconcile.py`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-reading-none-as-an-unanswered-field.md`

## Goal

`has_concrete_value` in `automation/reconcile/reconcile.py` decides whether a field has
been filled in. It answers no for an empty value, for the `______` template blank, and
also for six unfilled-slot words and for anything wrapped in angle brackets:

```
PLACEHOLDER_RE = re.compile(r"^(?:_+|<[^>]*>|tbd|todo|none|n/?a|unknown)$", re.I)
```

That is right for a template slot nobody filled in. It is wrong for an answer. "None" is
the natural, complete reply to a review that asks the reader to name the obligation a
sequence misses, and "n/a" is the natural reply to a question that turns out not to apply.
A check keyed on answered-ness therefore reads a real human answer as no answer at all,
and the consequence is not cosmetic: the checks that protect a committed response —
write-once identity, frozen dependency timing, the claim edge — all key on
`first_concrete_response`, so an answer of "none" leaves the item looking unanswered and
still mutable.

The rule this task lands: anything keyed on whether a human has responded keys on the
field being non-blank and not the literal template blank. Nothing else. Placeholder
vocabulary stays where it belongs — on slots an agent is supposed to fill in, not on the
line the owner writes on.

## Acceptance criteria

- [ ] Every reader of `has_concrete_value` is enumerated in `design.md` and classified as
      "template slot" or "human response", with the second group moved to a
      response-specific predicate
- [ ] A review answered with the single word "none", and a decision answered with the
      single token "n/a", are recognised as concrete responses: the item is write-once
      from that commit, its timing is frozen, and its `waiting` → `folding` claim is the
      only edge that may follow
- [ ] `**Your review:** ______` is still recognised as unanswered
- [ ] A test covers each word in the current placeholder vocabulary as a human response,
      and fails against the pre-change checker
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The predicate and its vocabulary: `automation/reconcile/reconcile.py`
- What a human is asked to write: `handbook/human-action-guide.md`
- The lifecycle a concrete response freezes: `message-queue/AGENTS.md`
- The redesign that found it: task `2026-07-31-redesign-human-action-files`
