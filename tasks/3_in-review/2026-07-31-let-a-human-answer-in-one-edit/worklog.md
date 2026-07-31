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
