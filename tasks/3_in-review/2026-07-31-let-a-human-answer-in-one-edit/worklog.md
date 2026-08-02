# Worklog — let a human answer in one edit

## 2026-07-31 — claude

Claimed the task from branch task/2026-07-31-let-a-human-answer-in-one-edit, stacked on
task/2026-07-30-clear-the-stuck-queue-items.

Reproduced all three defects against the real repository before changing anything; the
exact commands and output are in `verification.md`.

Fixed all three. `Reviewed revision` and `Review outcome` moved from the human's commit
to the agent's `folding` claim, which is admitted only over a response the parent commit
already carried, only on that one edge, only once, and only repeating the frozen
`Review revision`. A backticked path inside a response is now prose rather than a link
claim. Every queue template became copy-and-fill valid, defaulting to `non-blocking-`
because live timing may only escalate. The schema-marker fields that no template creates
are indexed in `templates/README.md`.

Two things the reproduction found that the audit had not named: `**Status:** <waiting |
folding>` was itself copy-invalid in every template, and a naive filler that substitutes
every `<...>` span corrupts any HTML comment containing `->`, so that arrow is gone from
template guidance.

The classification of a human sentence into an outcome cannot be checked mechanically.
That is recorded in `memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`
with what *is* enforced, and the aggressive alternative is written up in `design.md` for
the owner rather than shipped.

Making the queue templates real test inputs required teaching `prune_inert_projection`
that `INPUT_TEST_OWNERS` outranks an inert prefix; without it the narrow staged lane
deleted the templates the new test reads.

## 2026-08-01 — claude (merge `origin/main`)

Merged `origin/main` (`8811770`) into the branch as `b01636b`. Eleven pull requests had
landed, and #42 — "state each contract rule once, and only where it is true" — had
rewritten the same seven files this branch rewrote.

The two intents compose. #42 owns *where a rule lives*, so the prefix meanings, the
escalation rule, and what a boundary can attest went back to `message-queue/AGENTS.md`
and were removed from `templates/README.md` and the five template headers. This branch
owns *whether a copied template validates*, so the shipped `non-blocking-` fields, the
copy-and-fill contract, and the one timing table survived. The table now carries only
field syntax, which is a schema and therefore templates' own to state; collapsing the
five per-template copies of that syntax into it advances #42 rather than fighting it.
Nothing #42 deleted came back. Details and the per-file resolution are in the merge
commit message; the copy-validity re-proof is in `verification.md`.

One thing the merge surfaced: `message-queue/needs-human/reviews/README.md` still told
the reader to copy `Review revision` into `Reviewed revision` themselves. This branch had
made that the folding agent's job everywhere else. Corrected in place. The stale
instruction also survives inside seven already-filed live review items, which are not
this branch's to edit — human-facing prose in a live item is frozen once filed.

The merge also exposed a reconciler false positive that blocked its own commit.
`task_topology_problems` evaluates every merge-parent edge as a lifecycle step, so
merging a trunk re-audits the trunk's merge commits and any branch that advanced a task
two legal statuses reads as a jump on the trunk-side edge. Confirmed independent of the
conflict resolution: a mechanically resolved `merge -X theirs` produces the identical
finding. `task_status_at_other_parent` is the transition half of the repair
`tasks/4_done/2026-07-25-fix-merge-parent-task-topology/` already made for creations, and
its design's reasoning covers this case verbatim. It rides in the merge commit only
because the pre-commit hook cannot pass without it, and `--no-verify` was never used.
