# Worklog — report work back to the owner

## 2026-08-01 23:17 PDT — claude

Filed and claimed. Top of the stack: it changes the rituals that the skill, the PR schema,
and the rewritten guidance all feed into.

## 2026-08-02 02:40 PDT — claude

Added publish and report as steps 8 and 9 of the end-of-session ritual, stated the
stack-or-branch rule as a table in `handbook/git-workflow.md`, recorded the ADR, and updated
the roadmap and the README map.

The plan's third step failed, and the failure is the most useful thing this task produced.
Nine live unanswered questions were drafted in the readable shape with every machine field
copied byte for byte; the reconciler refused all nine, because a live item's visible text is
its identity and there is no presentation carve-out. That is the right rule — the drafts had
changed several titles into different questions — so the edits were reverted, the drafts kept
as a session artifact, the choice filed for the owner, and the rule written down as a lesson.

Two smaller findings came out of generating the handover: an `awaiting-artifact` item is not
projected, and one dead-end bullet written as an instruction was refused as an action-like
directive outside the projection sections.

## 2026-08-02 03:55 PDT — claude

Published the stack as pull requests #61 to #64 and iterated until every check on all four
was green. Two of the failures were real and are now recorded as dead ends in the handover.

The first: task admission checks every commit edge, not only the branch tip. A rebase left
one intermediate commit holding a task file whose `task.md` had already moved, and the merge
boundary refused the branch even though its tip was clean. The repair was to rebuild the
branch so no intermediate tree is invalid.

The second: closing and reopening a pull request to re-trigger its checks recomputes
`refs/pull/<N>/merge`, so a run that started before the recomputation fetches a different
commit than its event bound and fails on the mismatch. Repeating the re-trigger made it
worse, not better.

The stack is published as pull requests #61 (the explanation skill), #62 (the pull-request
schema), #63 (the guidance rewrite), and #64 (this ritual). Each targets the branch below
it, so the stack lands bottom-up, and no base branch may be deleted while a child is open.

The handover for this session could not be updated with those numbers: committed handover
bytes are immutable, and the reconciler refused the edit. That is the rule working — a
handover is a record of what a session knew when it wrote it, and this worklog is the
mutable place for what came after.
