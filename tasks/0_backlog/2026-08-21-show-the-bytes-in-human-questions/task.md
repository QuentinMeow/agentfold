# Make a human question answerable from its own bytes

**Claimed-by:** unclaimed
**Filed:** 2026-08-21, by claude, from chat — the owner rejected four live review items as unanswerable
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-show-the-bytes-in-human-questions.md`

## Goal

The owner read four live `needs-human/reviews/` items and could not answer them: "There are
absolutely no reasoning explanation of what's the effect and consequence... There's no
clickable pointers to context, nor localized short explanation." Measured, the four are 241
to 297 words against an 800-word budget, carry 52 bare backtick paths that are clickable
nowhere, and carry zero line- or anchor-precise pointers between them. Each asks for a
verdict on a 710-line design document without reproducing one line of it.

The rules that would have caught this already exist in `skills/explain-to-human/`. The
check that enforces them, `check_explanation_shape()`, skips every item not written under
the current template — 60 governed, 10 skipped, and the 10 skipped are exactly the 10 the
owner complains about. This task makes a source a question turns on appear *in* the
question, as the source's own bytes behind a resolving anchor, and makes the checker
report the items it currently cannot see without demanding an edit to an immutable record.

## Acceptance criteria

- [x] A queue item that asks for a verdict on a repository file quotes that file, and the
      quoted words are a verified substring of the text under the anchor it links.
- [x] A paraphrased quote, a deleted anchor, a misspelled anchor, a backticked path above
      the answer line, and a real sentence taken from the wrong section of the right file
      each produce a finding.
- [x] The owner has a sanctioned way to answer "this did not give me enough to decide"
      that copies no vocabulary, settles nothing about the subject, and obliges a fresh
      question.
- [x] Findings the ten frozen items produce demand no edit to any committed record.
- [x] Every finding is advisory; no commit or merge is refused by this change.
- [x] `skills/explain-to-human/SKILL.md` stays within its 70-line budget.

## Links

- `memory/decisions/2026-08-02-readability-enforcement-disposition.md` — why advisory
- `handbook/principles/eventual-consistency.md` — the loop these findings feed
