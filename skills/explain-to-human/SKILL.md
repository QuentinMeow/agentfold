---
name: explain-to-human
description: Write anything a human will read — a chat reply, a pull-request body, a queue item, a handover — so they can act on it without opening the diff or asking a follow-up question. Use before sending a final reply, before opening or updating a pull request, when filing a decision or review, and when writing a handover.
---

# Explain to a human

The reader did not watch you work, will not read the diff, and is deciding rather than
implementing. Write what they cannot reconstruct, and make the next action unmissable.

## The three layers, in this order, always

1. **One sentence** — what changed, and whether anything needs the reader. This is the
   pull-request title, the first line of a reply, the `Action` field of a queue item. A
   reader who stops here still knows whether to act.
2. **One short paragraph** — how it behaved before, how it behaves now, and what forced
   the change. At most four moving parts, because that is what a reader holds at once.
3. **The depth** — full explanation, worked examples, before/after comparison, tables.
   Folded, linked, or last, so a reader who does not want it never pays for it.

Never invert this. The order you did the work in is not the order the reader needs it in.

## Rules that hold on every surface

- **State the effect, not the mechanism.** "`resolve_queue()` now calls `freeze()`" tells
  a reader nothing. Say what goes in, what comes out, and what is different now.
- **Every change claim carries a before and an after.** If you cannot name an observable
  difference, the change belongs in the depth layer, not the summary.
- **Gloss an uncommon term in parentheses at first use** — "the reconciler (the script
  that checks every repository invariant before a commit is allowed)". Gloss once, never
  twice, and never gloss ordinary engineering words such as commit, test, or branch.
- **One worked example per non-obvious claim**, with a real input and its real result. A
  second example of the same point is noise, not reinforcement.
- **Name the actor.** "The check was updated" hides both who changed it and who must act.
- **State uncertainty as a number, not a hedge.** "Probably flaky (~40%, low confidence —
  it failed once, passed on retry, and I did not investigate)" beats "might be flaky".
- **Self-contained on the decision, linked on the evidence.** Anything whose difference
  would change the reader's answer goes in the file. How you know goes behind a link, and
  every link says what it holds and why the reader need not open it.

## Before → after

- Mechanism-first: *"Refactored `check_queue_schema` to take a candidate revision and
  moved the `Reviewed revision` validation behind it."*
- Effect-first: *"A review can no longer be approved against bytes that changed after you
  read them. Before, editing the reviewed file left your approval attached to it; now the
  approval is refused and the review is re-asked against the new bytes."*

## Route to the surface you are writing

Open the row's file before drafting. Do not improvise the format.

| You are writing | Read | It owns |
|---|---|---|
| a pull-request body | `scenarios/pull-request.md` | section order, folds, the change table |
| the final chat reply | `scenarios/chat-reply.md` | what to report, in what order |
| a decision, review, or clarification | `scenarios/queue-item.md` | making one file answerable alone |
| a handover | `scenarios/handover.md` | what the next reader needs from you |
| anything else a human reads | `reference.md` | the craft in full |

`reference.md` holds the depth behind every rule above, and the failure each one stops.

## Before you send

- [ ] The first sentence says what changed and whether anything needs the reader.
- [ ] Every change line names an observable difference, not a renamed symbol.
- [ ] Every uncommon term is glossed at first use.
- [ ] Every pending human item is a link plus enough context to act from this text alone.
- [ ] Nothing above the fold requires opening another file to understand.
- [ ] No "just", "simply", "obviously", or "as discussed".
