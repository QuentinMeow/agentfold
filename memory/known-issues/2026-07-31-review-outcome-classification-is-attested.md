# A review outcome is an agent's attested reading of the human's sentence, not a proof

**Status:** open
**Severity:** medium — cost or manual workaround
**Description:** Nothing mechanical verifies that a recorded Review outcome matches what the human actually wrote.
**Review-by:** 2026-10-29

## Symptom

A human answers a review with `**Your review:** Looks good to me, ship it.` The folding
agent records `**Review outcome:** approved`. The reconciler accepts it. It would also
accept `approved` for `**Your review:** This is not ready.`, because no check reads
English — `review_terminal_binding_write` validates the shape of the write, never the
truth of the classification.

## Impact

Every boundary that requires `approved` — a merge, a task transition — ultimately rests
on one agent's reading of one sentence. The blast radius is bounded by what *is*
enforced, and that is a lot:

- The outcome cannot exist unless the human's response was already committed in the
  parent commit, so no single commit can both author a response and approve it.
- The outcome may only be written on the `waiting` → `folding` claim edge, which changes
  nothing else, so it is a separate, attributable commit in the history.
- `Reviewed revision` must repeat the frozen `Review revision`, so an approval can never
  be re-pointed at bytes the human did not see.
- Both fields are write-once, and the human's sentence is immutable and stays in the file
  until the item resolves — so the claim and the words it claims to classify sit side by
  side in the diff forever.

What remains is a lie that is visible, attributable, and permanent, rather than one that
is impossible. That is a deliberate trade: the alternative made the repository's central
interaction impossible to use (task 2026-07-31-let-a-human-answer-in-one-edit).

## Workaround

Read the response text next to the outcome when auditing a resolved review; the history
preserves both. Boundary crossings that matter more than this can require independent
review of the folding commit itself.

## Suggested fix

The next mechanical step, if the trade stops being acceptable, is to require the human's
own text to carry a recognized token before an agent may record `approved` specifically —
the one outcome that crosses a boundary; the other three preserve or decline it. That
puts a second word back on the human ("approved: looks good"), so it should only ship
with evidence that the extra word is cheaper than the risk it removes. The alternative
is written up in full in that task's `design.md`.

## Owner disposition (2026-08-02)

The owner was asked whether recording `approved` should require a recognized word in his own
committed text. He chose to keep it attested, verbatim: *"for task 2, let's keep it default
way (option A). I don't really think this will be a big problem."*

So this stays open by decision, not by neglect. An approval remains an agent's reading of the
owner's sentence, recorded next to it and permanently attributable. Revisit if a
misclassification is ever observed.
