# Only bind a boundary every review outcome can still close

**Description:** A queue item may bind only a boundary all four review outcomes can satisfy with a commit an agent can make at any time after filing; a receipt Git cannot re-issue makes cleanup permanently unsatisfiable
**Area:** message-queue
**Last-confirmed:** 2026-08-01
**Review-by:** 2027-02-11

## Failure

Three human reviews bound `Blocks at: transition:merge` on exact Git ranges. Every range
was merged into `main` before its answer arrived. From that moment the items could not be
resolved *and* could not be deleted: cleanup ran through
`approved_review_merge_receipt_problem`, which demanded an exact two-parent merge already
present in admitted target history and carrying the approved bytes. No future commit can
produce a merge that already happened.

The decision item filed to escape the deadlock then bound `transition:complete` on the
same three tasks it asked about — so the escape re-created the trap, and the PR carrying
it could not merge past the reviews whose disposition it existed to ask about.

Nothing detected any of it for eight days. `reconcile --check` was clean the whole time;
only `--check --at-transition merge` saw it, and that runs on a pull request.

## Root cause

The boundary's closure condition lived outside the set of things an agent can still do.
Filing was checked; closing was not. A grammar that admits a boundary whose receipt Git
cannot re-issue will eventually be handed a repository where the receipt was needed after
the event that would have produced it.

## Rule

Before binding any boundary, name all four review outcomes — approved,
changes-requested, rejected, abandoned — and for each, name the commit an agent could
make today that closes the item. If any outcome's closure needs a specific Git topology
to exist in the future, or text inside a commit the human did not write, the boundary is
not bindable: file it `non-blocking-` with its unattended outcome instead.

The two symptoms to check for by name: a receipt that names a *past* event Git cannot
re-issue, and a gate whose satisfaction requires the very thing it is gating.
