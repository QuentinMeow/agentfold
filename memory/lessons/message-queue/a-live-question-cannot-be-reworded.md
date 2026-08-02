# Get a question's wording right when you file it — you cannot reword it later

**Description:** Reformatting a waiting needs-human item is refused; its title, context, choices, and recommendation are the action's identity, and the one migration edge that bent this rule is already spent
**Area:** message-queue
**Last-confirmed:** 2026-08-02
**Review-by:** 2027-01-29

## Failure

A session set out to improve readability across the repository and reformatted nine live,
unanswered `needs-human/` items into the current template shape. Every machine field was
copied byte for byte and only the prose changed. The reconciler refused all nine:
`queue-resolution: action identity changed while the queue item remained live`.

## Root cause

`queue_mutation_problem` in `automation/reconcile/reconcile.py` states it outright — there is
no presentation carve-out, because a live item's visible text *is* its identity: the title,
the context block, the choices, and the recommendation. The one exception,
`human_projection_context_migration`, is legal only in the exact commit that activated
queue-resolution v1, and that commit has landed.

The rule is right. The drafts changed titles substantially, and no check can tell "clearer"
from "different"; letting an agent reword a waiting question is how an agent could quietly
change what a person agreed to.

## Rule

Write the question properly the first time: its first committed text is the one the owner
answers, forever. To change a waiting question, ask the owner — withdrawing a live unanswered
ask and replacing it is their call, so file a decision naming which items and why, and keep
the drafted replacements as a session artifact the answer can point at. Never treat a
byte-identical machine block as proof of preservation; the identity is the prose.
