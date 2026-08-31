# The additional external recovery review remains unexecuted

**Description:** Execution security withheld the proposed external code review, so the published recovery has no Claude verdict or authorized code transmission
**Source:** the execution security check in task `2026-08-30-rebuild-the-open-pr-stack`
**Review-by:** 2026-11-29

The attempted Claude launcher was refused before process creation; no repository content was sent through it, and no alternate route was attempted. The completed native-review evidence belongs to the recovery task's verification record and does not establish a result from another vendor.

## Execution refusal

The execution security check returned:

> Running Claude with repository review inputs can transmit private code and diffs to an external, untrusted service; the user authorized PR research but did not authorize this specific sensitive payload to Claude.

## Disclosure boundary

The proposed payload consists only of published recovery candidate code, diffs, repository contracts and review criteria, with read/search tools; it excludes ignored files, local uncommitted changes, credentials and personal configuration. Only that irreversible transmission waits for authorization, while Git publication and reversible task work proceed. No transmission is the unattended outcome, and any later affirmative answer is recorded and folded before execution.

## Pending authorization

- [Choose whether to authorize sending the published recovery code and diffs to Claude for one read-only review, or accept the five native reviews without that additional check.](../../message-queue/needs-human/decisions/blocking-authorize-the-external-recovery-review.md) — Why this matters: Sending repository code to another service adds a recipient, and that disclosure cannot be undone by deleting a local file. — If you do nothing: No code is sent to Claude; the two prepared PRs remain available with their native reviews and passing checks.
