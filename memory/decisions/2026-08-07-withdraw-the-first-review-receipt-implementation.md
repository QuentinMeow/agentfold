# Withdraw the first review-receipt implementation and rebuild to the authorized shape

**Status:** decided
**Date:** 2026-08-07
**Decided-by:** human (owner deferred to the recommendation in the canonical decision item, recorded before folding)
**Description:** The first closed-receipt implementation is discarded and rebuilt to the narrow authorized grammar, with the character alphabet, reviewer-similarity rule, and second panel grammar excluded unless a demonstrated failure forces them back.
**Amends:** `memory/decisions/2026-08-04-review-receipt-parser-authorization.md` — the Consequences clause stating that the parser becomes deliberately smaller and fail-closed
**Review-by:** 2027-02-07

## Context

The 2026-08-04 decision authorized one closed contiguous receipt grammar and said the
parser would become deliberately smaller and fail-closed. The implementation that followed
grew instead: roughly 495 new lines against the twenty it replaced, across sixteen
adversarial review rounds, each round finding a new hole and each repair widening the
surface further.

A three-lens independent panel on revision `ccbb9e4854faf42dc423638e6b6b39a284608f4b`
returned zero approve and three block. The decisive finding is a fail-open on the merge
gate's own output: a verdict whose finding text leaves a closed character set ends the
receipt and discards that verdict together with every later one, so a panel of one approve
and two block is reported as one approve and zero block. Reviewers also found that the
token-only neutralizer the 2026-08-04 decision describes is imported by the action gate and
never called, that a second undocumented panel grammar grants receipt neutrality with no
heading, revision binding, claimant, or independence check, and that widening the action
vocabulary flags ordinary prose in eleven existing files. Evidence and reproductions are in
the task's verification record.

## Decision

The 2026-08-04 grammar stands unchanged: an exact top-level Review verdicts heading, one
full reviewed-revision field, then consecutive one-line core-fit verdicts, shared by both
gates. What is withdrawn is the implementation, not the decision.

The rebuild starts from the previous parser and adds only what the authorized grammar
needs. These are out of scope unless a demonstrated failure forces one back, and any such
return needs its own decision:

- a closed character alphabet constraining reviewer identities or finding text;
- reviewer independence by character-multiset similarity, containment, or edit distance;
- composite claimant separators and component ceilings;
- a second `adversarial panel` receipt grammar;
- raw-HTML open-container tracking and structural-versus-rendered view agreement;
- adding `block` to the general human-action command vocabulary.

Neutralization blanks only the structural verdict token, never the whole line, so reviewer
identities and finding text stay under ordinary human-action detection. A verdict that
cannot be parsed fails the receipt loudly rather than being dropped from the tally.

## Alternatives considered

- Repair the shipped implementation in place — rejected because sixteen rounds of a new
  hole per repair is evidence about the approach rather than about any single bug, and the
  implementation already exceeded what was authorized.
- Leave the work as it stands — rejected because the two finished repairs behind it cannot
  record their own review evidence without it.

## Consequences

Sixteen rounds of implementation work are spent, and the dependent stale-base and
linked-worktree repairs wait longer. The rebuilt parser will accept fewer exotic inputs and
reject them visibly instead of silently. Revisit if the narrow grammar proves unable to
distinguish a real request inside a reviewer identity or finding from the structural token,
which is the one problem the excluded mechanisms were reaching for.
