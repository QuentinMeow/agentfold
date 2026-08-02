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
2. **One short paragraph** — how it behaved before, how it behaves now, and what forced the
   change. At most four moving parts, because that is what a reader holds at once.
3. **The depth** — full explanation, worked examples, comparison tables — folded, linked,
   or last, so a reader who does not want it never pays for it.

Never invert this order. The order you worked in is not the order the reader needs.

## Rules that hold on every surface

- **State the effect, not the mechanism.** "`resolve_queue()` now calls `freeze()`" tells
  a reader nothing. Say what goes in, what comes out, and what is different now.
- **Every change claim carries a before and an after.** If you cannot name an observable
  difference, say so plainly rather than manufacturing one.
- **Gloss a repository-local term in parentheses at first use**, once per document — "the
  reconciler (the script that checks every repository invariant)". `reference.md` lists the
  ordinary engineering words that never need it.
- **One worked example per non-obvious claim**, with a real input and its real result.
  Replaying that same example to show the after state is part of it, not a second example.
- **Name the actor.** "The check was updated" hides both who changed it and who must act.
- **State uncertainty as a number, or say you did not measure.** "Probably flaky (~40%,
  low confidence — failed once, passed on retry)" and "unknown — I did not measure this"
  are both honest. Inventing a number to satisfy the rule is not.
- **Self-contained on the decision, linked on the evidence.** Anything whose difference
  would change the reader's answer goes in the text. Every *evidence* link says what it
  holds and why the reader need not open it.

## Before → after

- Mechanism-first: *"Refactored `check_queue_schema` to take a candidate revision."*
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

Precedence: a scenario file wins on its own surface; `reference.md` wins over this file.

## Before you send

- [ ] The first sentence says what changed and whether anything needs the reader.
- [ ] Every change line names an observable difference, or says there is none.
- [ ] Every term local to this repository is glossed at first use.
- [ ] Every pending human item is a link plus enough context to act from this text alone.
- [ ] Nothing above the fold requires opening another file to understand.
- [ ] No "just", "simply", "obviously", or "as discussed".
