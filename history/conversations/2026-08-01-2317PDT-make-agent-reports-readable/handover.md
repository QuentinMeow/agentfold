# Handover — make agent reports readable

**Session:** 2026-08-01 23:17 – 2026-08-02 HH:MM PDT, claude
**Task:** 2026-08-01-write-the-explanation-skill, 2026-08-01-standardize-pull-request-bodies, 2026-08-01-rewrite-human-facing-guidance, 2026-08-01-report-work-back-to-the-owner
**Mode:** async
**Queue projection:** v1

## What happened

- Nothing is in flight. Four branches are pushed, four pull requests are open as a stack,
  and every check is green on each.
- Added `skills/explain-to-human/`: one standard for anything a human reads, routing to one
  file per surface — pull-request body, chat reply, human queue item, handover. Before, the
  rules were split across four documents that each owned one surface and none stated the
  craft all four need.
- Added `templates/pull-request.md` and its GitHub projection, with ten tests that run the
  real action-projection gate over bodies in that shape. The tests rejected the first draft
  three times and all three were real defects.
- Rewrote `handbook/human-action-guide.md`, `message-queue/AGENTS.md`, and
  `handbook/decision-guide.md` against a 163-row inventory of every rule they contained. An
  independent audit of the rewrite found 151 kept, 9 moved to the owning file, 1 deleted
  because it was false, and 2 corrected.
- Made publishing and reporting steps 8 and 9 of the end-of-session ritual, and reformatted
  the ten questions already waiting on the owner into the readable shape.

## How it works now

An agent about to write anything a human reads opens `skills/explain-to-human/SKILL.md`,
follows its routing table to one scenario file, and writes in three layers: one sentence
saying whether anything needs the reader, one paragraph of before-and-after, then the depth
behind a fold or a link. A pull-request body copies `templates/pull-request.md`. A session
that did work ends by pushing its branch, opening its pull request, and reporting in chat.

None of it is machine-checked. The two things near it that are checked — the pull-request
action section and the 700-word budget on a queue item — were already checked before this
session and are unchanged.

## Decisions made for you

- One skill with a router and four scenario files, rather than four skills or more handbook
  prose — `memory/decisions/2026-08-02-explaining-and-publishing-are-part-of-the-work.md`.
- The pull-request body schema lives in `templates/` with a thin GitHub adapter, rather than
  only in `.github/` — `tasks/*/2026-08-01-standardize-pull-request-bodies/design.md`.
- Two statements in the rewritten contracts were corrected rather than preserved, because
  they contradicted the reconciler and the templates —
  `tasks/*/2026-08-01-rewrite-human-facing-guidance/verification.md`.
- Readability rules are not machine-checked for now; whether they should be is filed as a
  decision rather than assumed.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Choose whether readability rules stay judgment, become advisory warnings, or become commit-blocking checks.](../../../message-queue/needs-human/decisions/non-blocking-check-the-readability-rules-or-leave-them-to-review.md) — Why this matters: Nothing currently stops an agent from ignoring the whole standard, so the quality you get still depends on which agent wrote the message. — If you do nothing: The rules stay written-only and enforced by review; agents that follow them produce better messages and agents that do not are caught only when you notice.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Choose whether the nine older waiting questions are left as written, replaced with plainer versions, or replaced only where their wording is now stale.](../../../message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md) — Why this matters: Nine of the questions in your queue were written in a format that buries the choice under bookkeeping, and four of them still ask about a moment that has already passed. — If you do nothing: They stay exactly as written and stay answerable; only questions filed from now on use the readable shape.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.
- [Say whether this is the standard every human-facing message is held to, or name what to change.](../../../message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md) — Why this matters: Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message. — If you do nothing: The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.
- [Say whether this pull-request shape works for you, or name the section to move, add, or drop.](../../../message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md) — Why this matters: This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything. — If you do nothing: The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## Dead ends

- Pinning a pull-request body's queue links to the branch head does not work: the gate
  builds its one allowed prefix from the commit at `refs/pull/<N>/merge`, which GitHub
  computes and which no local revision matches. The working form is
  `git ls-remote origin refs/pull/<N>/merge` after the pull request exists. That commit
  recomputes whenever the base or head moves, so a merged parent in a stack leaves its
  children's bodies stale and the gate says so.
- A relative link in a pull-request body is not a workaround: the gate accepts it, but
  GitHub does not rewrite relative links there, so the reader gets a 404.
- Rewriting a review item's binding in place is refused. An unanswered review whose artifact
  changes must retract to `awaiting-artifact` in one commit and republish in the next; the
  skill's own review did exactly that when the skill was repaired.

## Next steps

None.

## Deep links

- Task folders: `tasks/3_in-review/2026-08-01-*` · Design: `docs/designs/explaining-work-to-the-owner.md`
- Commits: `main..task/2026-08-01-report-work-back-to-the-owner`
