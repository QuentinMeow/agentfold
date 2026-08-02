# Should recording `approved` require a word the human actually typed?

**Status:** waiting
**Filed:** 2026-07-31, by claude, from task 2026-07-31-let-a-human-answer-in-one-edit
**Action:** Choose Option A or Option B, or state another rule for how an approval is derived from human text.
**Full context:** [what a human action must contain, and what an outcome is worth](handbook/human-action-guide.md)
**Why-you-might-care:** Every boundary that requires `approved` currently rests on one agent's reading of one English sentence, and no check can tell a truthful reading from a false one.
**If-you-do-nothing:** Option A stays. Approvals remain agent-attested readings of immutable human text, and the known-issue file keeps saying so.
**Resolution evidence:** `memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`
**If unanswered:** Option A stays in force indefinitely; nothing stops, and the trade stays recorded rather than hidden.
**Answer by:** 2026-10-29

## What you need to know

You can now answer any queued item by typing one sentence and committing — that is the
whole point of the change that shipped today. The agent then classifies your sentence
into `approved`, `changes-requested`, `rejected`, or `abandoned` when it claims the item.

The reconciler cannot read English, so it cannot check that classification. It can and
does check everything around it: the outcome cannot exist until your response is already
committed, it lands in a separate commit, it can never be re-pointed at different bytes,
and it can never be amended. What it cannot do is prove that `approved` is what "Looks
good to me" meant. This asks whether that is good enough for the one outcome that lets
work cross a boundary.

## Differences

Option A keeps answering effortless and accepts that an approval is an attested reading.
Option B makes `approved` mechanically derivable from your own words, at the cost of
making you type a second, specific word — which is the exact friction this whole change
removed. The other three outcomes are unaffected either way, because they preserve or
decline the boundary rather than crossing it.

## Options

### Option A — Keep approvals attested (what ships today)
The agent reads your sentence and records the outcome. Forgery is impossible to prevent
but is visible, attributable to a specific commit, and permanent next to your own words.
*Example consequence:* you write "yes, ship it" from your phone and it just works. If an
agent ever recorded `approved` over "this is not ready", nothing would stop the commit —
you would find it later by reading the diff, where both lines sit side by side.

### Option B — Require an approval token in your own text
An agent may only record `approved` when your committed response contains a word from a
short recognized list. Anything else can still be `changes-requested` or `rejected`.
*Example consequence:* "yes, ship it" is rejected by the reconciler because "yes" is not
on the list, and your commit fails until you rewrite it as "approved: ship it". In
exchange, no agent can ever mark something approved that you did not word that way.

## Recommendation

A, because the failure Option B prevents has not happened, while the friction it adds is
the exact failure this task existed to fix. Revisit if a misclassification ever occurs.
The full write-up of both options is in the `design.md` of task
2026-07-31-let-a-human-answer-in-one-edit.

**Your answer:** Option A — keep it the default way. I don't really think this will be a big problem.
