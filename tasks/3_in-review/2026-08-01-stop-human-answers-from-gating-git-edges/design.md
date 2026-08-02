# Design notes — Stop a human answer from holding any Git edge

**Status:** decided

## Problem

The queue's boundary grammar lets a `needs-human/` item bind any transition,
including `transition:merge`. In an `async` repository whose declared merge gate
is "tests + reconciler; panel for one-way doors", that grammar lets an agent
file a human merge gate one file at a time — a `pair`-mode behaviour smuggled
into an `async` repository.

It has already produced a deadlock that no commit can clear. Two live reviews
bind `transition:merge` on ranges that are already ancestors of `main`;
`review_cleanup_boundary_problem` routed an approved merge review to
`approved_review_merge_receipt_problem`, which required an exact two-parent
merge *in previously admitted history* carrying the approved bytes. Once the
merge happens before the answer, that condition is permanently unsatisfiable in
both directions: the item cannot be resolved, and it cannot be deleted. The
decision item filed to escape the deadlock then bound `transition:complete` on
the same three tasks it asks about, so filing the escape re-created the trap.

Two constraints shaped every option. The owner answers durable questions late,
never before a merge. And `main` runs `reconcile --check` in the pre-commit hook,
so every commit in the repair must itself be green.

## Options considered

### Option A — Rename the timing prefixes
Replace `blocking-` / `future-blocking-` / `non-blocking-` with names that carry
the new semantics (`whenever-`, `before-start-`, `before-door-`), so an agent
cannot read the old meaning back in. *Consequence:* every live queue item is
renamed, and each rename fans out across its link-checked references —
`task.md`, `design.md`, and recorded `verification.md` files whose command output
should not be edited at all. Migrating four items in this task already required
rewriting eleven files; the vocabulary rename multiplies that across every live
item, and buys semantics a refusal message can teach instead.

### Option B — Add a fourth timing class for "answer whenever"
File merge-first human questions under a new `deferred-` prefix, exempt from
every boundary rule. *Consequence:* four regexes, two constant tables, the
handover projection schema version, and ten templates change to build a class
whose job `non-blocking-` plus `If unanswered:` already does — and has done since
2026-07-23, in a live item nothing forced to be `future-blocking-`.

### Option C — Restrict the admissible boundary *values* for `needs-human/` only
Keep the three prefixes and the whole filename grammar. Make
`transition:merge|review|complete` and `Blocks now: task:<id>` unspellable on a
`needs-human/` item, leaving `transition:start` on a `0_backlog` task and
`operation:<name>`. Leave `needs-agent/` untouched. *Consequence:* the taxonomy
does not change, so no live item outside the migrated four moves; the reconciler
teaches the new rule at the moment of violation, on the author's own pre-commit
hook.

## Chosen

Option C. The taxonomy was never missing a term — the grammar was admitting a
boundary it should not. Scoping the restriction to `needs-human/` is what keeps
it honest: an agent obligation is discharged by an agent at any time, so an agent
boundary cannot strand, and agent deletions route through changed evidence rather
than through any merge receipt. Eleven live `future-blocking` agent requests keep
working unchanged.

The generalised rule this rests on, recorded as a lesson: *a queue item may bind
only a boundary all four of whose review outcomes are satisfiable by a commit an
agent can make at any time after filing; no boundary's closure may require text
inside a commit the human did not write.* The retired merge receipt is the worked
counter-example, and applying the rule is also why the `1_in-progress → 0_backlog`
unstart edge had to be added: without it, two of the four outcomes of the one
surviving human gate were unreachable.

Two consequences were accepted rather than designed around. Between a merge and
the owner's answer `main` may carry a change he would have rejected — bounded by
`git revert -m 1` and by the surviving start gate, which still stops any *task*
that depends on the unanswered judgment from beginning. And a lapsed `Answer by:`
is advisory, so a determined backlog can still rot — visibly, with a date, in
every reply and every handover, which is strictly better than the state it
replaces, where two questions sat for eight days with no mechanism that would
ever have noticed.

Rejected inside Option C: making a lapsed deadline *decide* by falling through to
`If unanswered:`. It is not mechanically legal — deletion needs a concrete
response, and writing into the human's answer slot violates both "never edit text
the human wrote" and "never fabricate" — and it is the wrong policy. The owner's
model is "I will answer, later," not "decide for me if I am slow." A lapse
re-surfaces and re-asks; it never answers.

## Core fit

**Agent substitution:** pass — every mechanism is a rule inside
`automation/reconcile/reconcile.py` over committed repository bytes and Git
history. No runtime, model, or agent product is named, and any agent that can
write files and run the reconciler participates identically.
**Provider substitution:** pass — the surviving enforcement runs on a bare local
`--check` with no adapter. `check_task_structure`'s boundary-crossing rule reads
task folders and queue files only. The GitHub-specific part of the model is a
recommendation recorded in an ADR, not code, precisely because a repository
cannot verify a provider setting.
**Repository substitution:** pass — any adopting repository whose owner answers
asynchronously inherits the same deadlock the moment a reviewer files a
merge-bound question, because the grammar that permits it is the shipped grammar.
The fix is a restriction on that shipped grammar, so it travels with it.
**User-global writes:** none
**Why AgentFold core:** this is the queue's boundary grammar and the task
lifecycle — the two contracts the harness exists to enforce. It cannot be local
config (it must bind every agent in every checkout), it is not a product service,
and a private overlay would leave the shipped grammar still able to spell the
deadlock for the next adopter.
**Thin adapter:** none
