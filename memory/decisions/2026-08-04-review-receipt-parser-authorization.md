# Use a closed contiguous grammar for formal review receipts

**Status:** decided
**Date:** 2026-08-04
**Decided-by:** human (Option A, recorded in the canonical decision item before folding)
**Description:** Formal core-review receipts use one closed contiguous block so verdict tokens can be distinguished from human requests without interpreting general Markdown structure.
**Amended-by:** `memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md` — the Consequences clause stating that the parser becomes deliberately smaller and fail-closed
**Review-by:** 2027-02-07

## Context

The core-scope gate requires revision-bound reviewer verdicts, while the human-action gate
treated the required structural word `approve` as a new request. Three broader parser
repairs remained unpublished because adversarial reviewers found ambiguous filename,
section-boundary, and CommonMark-container cases. The canonical decision item explained
that the dependent stale-base and linked-worktree repairs could not publish safely while
the two gates disagreed.

## Decision

Formal review evidence uses a closed contiguous block: an exact top-level Review verdicts
heading, one full reviewed-revision field, then one or more consecutive canonical
one-line core-fit verdicts. The block ends at the first nonblank line that is not a
canonical verdict. Both gates share this interpretation.

Only the structural `approve` or `block` token inside a valid receipt is neutral evidence.
Reviewer identities and findings remain subject to ordinary human-action detection.
Malformed, decorated, duplicated, nested, or misplaced near-misses receive no exemption.
The task must still pass focused and full tests plus independent review before publication;
this decision approves the parser and template design, not any pull request or review
outcome.

## Alternatives considered

- Keep both gates unchanged — rejected because the required formal receipt would remain
  unusable and the dependent repair chain could not publish under the repository's review
  standard.
- Infer receipt boundaries from general CommonMark section structure — rejected because
  independent reviewers repeatedly found container and heading ambiguities that widened
  the exemption surface.

## Consequences

Receipt writers must use the canonical contiguous form and cannot insert prose or
subheadings inside it. The parser becomes deliberately smaller and fail-closed, while real
requests in reviewer names or findings remain visible. The change is reversible through a
new ADR and parser/template revision if the canonical form proves too restrictive.
