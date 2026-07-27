# Writing decisions humans can actually answer

A decision file is an interface between an agent with full context and a human who may
have none. Its job is not to prove how much research happened. Its job is to make one
choice understandable, comparable, and safe to answer. General rules for every human
action live in `human-action-guide.md`; the exact decision schema lives in
`templates/queue/decision.md`.

## Write for a reader who was not in the room

Assume the human has not read the codebase, may skim one screen on a phone, and wants
to understand consequences rather than internal terminology. The file must therefore:

1. Ask one clear question in the title and repeat the requested choice under `What I
   need from you`.
2. Explain the practical stakes and the no-response behavior before background detail.
3. Separate `Today` from `Future behavior being decided`. Never describe a proposal as
   if it already exists.
4. Present at least two genuinely distinct options with the same structure: meaning,
   benefits, costs and risks, and a concrete example consequence.
5. Recommend an option only after presenting them all. Show, in order, the evidence
   checked, assumptions, confidence, rationale, and what would change the recommendation;
   put the recommended option last so the reader sees calibration before conclusion.
6. Accept a plain answer. The reader may name an option, propose another choice, or ask
   a question without copying hashes or editing lifecycle metadata.
7. Link each reference once. The explanation remains sufficient even if the links are
   not opened; tracking details come last.

## Compare options symmetrically

Use neutral option names and parallel examples. If one option gets operational costs,
failure modes, and an example, every option gets those things. Avoid a false binary:
add another option when it is genuinely viable, and explicitly say when two ideas can
be combined.

Distinguish design rationale from recommendation. The rationale explains why each
option exists and the trade-off it makes. The recommendation explains which trade-off
best fits the current goal. A recommendation should be easy to challenge because its
evidence, assumptions, confidence, rationale, and reversal conditions appear before the
agent's preferred answer. This order reduces anchoring without hiding the agent's view.

## Make consequences observable

Replace abstract labels with a short scenario a reader can picture. For example:

> Today, quotes are stored only in memory and disappear when the service restarts.
> Option A writes a readable JSON file; a simultaneous write can lose data. Option B
> uses SQLite; simultaneous writes are safe, but reviewing the stored data needs a
> tool. The agent recommends JSON while writes are single-threaded, with medium
> confidence; evidence of concurrent writes would change the recommendation.

This example identifies current behavior, future alternatives, user-visible
consequences, the recommendation, and the condition that could reverse it. It does not
require the reader to infer which sentences describe the present.

## After the answer

A response is immutable while the item is `waiting`. An agent then changes only status
to `folding`, records the answer in the declared resolution evidence, and writes an ADR
from `templates/memory/adr.md` when a decision was made. A counter-question is a valid
response: answer it durably, then create a same-timing successor whose `Supersedes`
field names the old item. Never rewrite the human's words.
