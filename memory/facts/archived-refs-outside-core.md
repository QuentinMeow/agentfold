# Work that will not merge is preserved as an `archive/*` annotated tag, not a branch

**Description:** Work that will never land — refused by Core admission, superseded, or orphaned — is kept on annotated `archive/*` tags whose message carries the reasoning; list them with `git tag -l 'archive/*'` before rebuilding something that looks unprecedented
**Source:** task 2026-07-22-prevent-false-github-reauth; decision `memory/decisions/2026-07-26-agent-specific-guidance-stays-out-of-core.md`; re-verified 2026-08-02 by task 2026-08-02-reconcile-the-contracts-with-the-code
**Review-by:** 2026-11-05

Work that is well built but will not land on `main` is not deleted and not left on a
branch. It is preserved as an annotated tag under `archive/`, and the tag message states
why. Branches are swept by routine merged-branch cleanup and tags are not; the first such
ref was nearly lost that way.

The convention started with one **Core admission** refusal — a runtime-specific guard whose
installer wrote under a user-global directory, so the `User-global writes: none` receipt in
`templates/task/design.md` could not be filled honestly — but it is no longer only that.
It now also holds an implementation that was redone from `main` and kept as design input, a
design rule that was rejected on the record, a commit reachable from no ref that held the
only copy of two required handovers, and an unmerged branch whose ADRs and verification
output exist nowhere else. The common test is not *why* it was refused: it is that the work
will not merge and something in it must survive.

Read them with `git tag -l 'archive/*'` and then `git show <tag>`. The tag message is the
record, so this file deliberately does not enumerate the refs — an enumeration goes stale
the next time one is added, which is how this entry was wrong before. Paths and refs inside
those messages are also deliberately unquoted: they resolve on the archived ref, not on
`main`, and backticking them would make `link-check` read them as live repository paths.

Do two things differently because of this. Before designing a mechanism that feels
unprecedented here, run that command — the analysis may already exist, including the reason
it was refused. And when proposing a runtime guard, split it: the portable mechanism can be
proposed with a complete `## Core fit` receipt, while the runtime adapter belongs in that
runtime's own configuration, outside this repository.
