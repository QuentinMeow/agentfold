# Handover — fold edge graph decisions and ship Stage 0

**Session:** 2026-07-25 11:40–15:15 PDT, local time, claude
**Task:** 2026-07-25-mine-markdown-cochange-couplings
**Mode:** async
**Queue projection:** v1

## What happened

- Your answers to all eight open markdown-edge-graph decisions were transcribed into their
  queue items, claimed, and folded into three ADRs: the accepted architecture, the repo-root
  path-type default, and edges authored in one direction only. Your handwritten answers are
  committed verbatim, and the design was aligned with the two that diverged from the
  recommendation — three per-folder freshness modes with a seven-day default window, and a
  justified per-file cap exception.
- Stage 0 of that design was built on a task branch and is open as pull request 13, all four
  CI checks green. It adds heading-anchor validation, a stdlib advisory co-change mining
  command, and an append-only accept/reject ledger. Nothing from it is on `main` yet.
- The anchor work closed a live hole rather than adding a feature: any link candidate
  carrying a `#` fragment failed the checker's character-class guard, so an anchored link had
  neither its path nor its anchor validated.
- The gating experiment that decides whether the rest of the design gets built ran, and it
  went partly against the design. Accuracy holds — one rejection in 29 judged candidates,
  3.4% effective false positives — but the same single rejection is 10.0% over the default
  report's top ten, which is exactly the probation trigger. The verdict of record is to
  **narrow**: a reduced Stage 2, no Stage 3 at all, half of Stage 4.
- From that result: two new decisions for you, three backlog tasks with their pickup
  requests, and five deferred-stage requests were filed. The third backlog task is a live CI
  defect found while opening pull request 13, not part of the design.

## How it works now

The three ADRs are the accepted architecture, and the design document matches them. The
mining command and its ledger run today on the task branch: the ledger holds 29 real
verdicts, and a decided pair never re-surfaces in a later report. Two things are still owed
before the narrowing can proceed — your two decisions below, and the Stage 0 verification
transcripts, which were never recorded when that code landed and are now their own backlog
task. Separately, both required admission checks fail on every freshly opened pull request,
because the merge revision the webhook has not computed yet is read as empty by one job and
replaced by the base-branch tip in the other; the only current workaround is to fire a second
event by hand.

## Decisions made for you

- Mining ships as a standalone advisory command rather than a reconciler check, because every
  reconciler finding blocks a commit and a suggestion measured in the probation band would
  become roughly two hard stops per fifth commit — recorded in the task's `design.md`.
- The ledger lives beside the tool as a tracked append-only text file rather than under
  `memory/`, because a rejected coupling is a permanent verdict and not an expiring fact that
  the gardener should re-verify or delete — same file.
- Anchor validation landed inside the existing link check rather than as a new check id,
  because retry filenames embed check ids and the hole was inside that check already.

## Needs your attention

- [keep the committed byte-exact artifact as answered in N6, or generate it on demand and name the size at which committing is revisited](../../../message-queue/needs-human/decisions/future-blocking-commit-or-generate-the-edge-graph-artifact.md) — Why-you-might-care: Committing the artifact is the single most expensive stage in the plan — six separate mechanisms — and the measured graph it would serve currently spans 17 of the repository's 172 in-scope markdown files. || If-you-do-nothing: No graph artifact is generated or committed, and in-edges stay answerable only by running a command; at the named boundary the storage question cannot be deferred any further and the artifact work stops there.
- [keep all three freshness modes as answered in N5, or drop `each-run` and ship review-window plus advisory-only](../../../message-queue/needs-human/decisions/future-blocking-keep-or-drop-the-each-run-freshness-mode.md) — Why-you-might-care: `each-run` is the most expensive third of the freshness surface — a git history pass on every run plus the per-folder configuration that exists mainly to switch it off — and the measurement says it would have produced nothing at all on the design's own strongest case. || If-you-do-nothing: No freshness mechanism is implemented and `Update-when:` stays prose a reader acts on, which is the `advisory` mode by default; at the named boundary the mode set cannot be fixed and the freshness work stops there.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- **Applying two of your own answers as written.** The experiment reversed part of N5 and part
  of N6 after you had already answered them. Rather than quietly implement something other
  than what you decided, or quietly implement a mechanism the measurement had just killed,
  both went back as new decisions — the two items at the top of the list above. Neither
  original answer was overwritten; the ADRs still record exactly what was decided.
- **Clause-scoped review debt derived each run — measured dead, not argued dead.** The prefix
  definitions in `message-queue/AGENTS.md` changed in 2 of its 14 in-scope revisions, and in
  both of those commits every template that restates them was edited in the same commit.
  Derived debt closes when the dependent is touched, so across the whole history of the
  design's own strongest case the mode would have filed zero items. Worse, the one live drift
  it exists to catch happened inside one of those two commits (aca7014): the dependents were
  touched for a neighbouring reason while the restated sentence went stale, so the mechanism
  would have been silent on the only failure in its own domain.
- **A unit test that forbade using the feature it tested.** Shipped in the same session as the
  ledger, it asserted the tracked ledger held no verdicts, so the first real verdict made the
  suite fail and the repository uncommittable. It was repaired in `35582c2` to assert that
  every verdict line parses, rather than worked around; the refused commit is recorded in the
  task's `verification.md` instead of bypassed.
- **Declaring the flagship duplication as an edge.** The prefix rule is restated in all five
  queue templates, none of which names its owner. A restatement edge preserves the duplication
  and adds a permanent maintenance duty on top of it; deleting the restatement and linking the
  owner removes both. That is now its own backlog task.
- **Committing this handover at all, until the gate that blocked it was repaired.** Every
  session's end-of-session ritual was blocked for as long as any live `needs-human/` item
  carried an inline code span in `Why-you-might-care` or `If-you-do-nothing`, and the second
  entry above carries three. The handover projection built its expected context from the queue
  item's raw field bytes, backticks intact, and compared it against entry prose whose code
  spans had already been blanked, so no handover text could satisfy it; five encodings were
  tried and all five failed. The gate was repaired under task
  2026-07-25-fix-handover-projection-code-span-copy rather than bypassed with `--no-verify`,
  which is why this file lands on `main` only when that task's branch merges.
- **The first diagnosis of that defect — wrong in its mechanism, though right that the checker
  was at fault.** It read the two-element loop over the raw and the rendered entry form as a
  raw-versus-rendered choice that wrongly demanded both, and concluded that accepting either
  form would repair it. Both elements use the same prose view, so both blank code spans, both
  branches fail, and accepting either is a measured no-op; the two forms differ only when the
  entry carries raw HTML, which is what that loop actually guards. The asymmetry is between
  the expected context and the entry, not between the two entry forms, and the repair that
  follows from the correct mechanism is a different change: both sides are normalised through
  `render_inline_code`, matching the action-label check three lines above, which already
  renders code spans and is why the same item's backticked `Action` projected while its
  context could not. The wrong mechanism is recorded here because acting on it would have
  produced a no-op patch and a second blocked session.

## Next steps

- [After 2026-07-25-mine-markdown-cochange-couplings reaches `4_done`, confirm which transcript sections its verification file is still missing, then remove this dependency action and its reciprocal task link before the backfill task is claimed.](../../../message-queue/needs-agent/requests/future-blocking-finish-mining-task-before-transcript-backfill.md)
- [Build the typed edge schema in the reduced form the gating experiment supports: the relation vocabulary and its one-question test, one `Because:` line per edge, a clause anchor only where the target has two or more headings, `Update-when:` as prose the query prints, `handbook/` activated alone, and edges authored from the mined candidate list rather than from memory.](../../../message-queue/needs-agent/requests/non-blocking-build-the-reduced-stage-2-edge-schema.md)
- [After the mining task is done and its dependency action is resolved, claim this backlog item and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-complete-stage-0-verification-transcripts.md)
- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-fix-pull-request-admission-event-race.md)
- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-single-source-queue-prefix-rule.md)

## Deep links

- Task folder: `tasks/1_in-progress/2026-07-25-mine-markdown-cochange-couplings/` · Worklog, design, and verification live there, on branch `task/2026-07-25-mine-markdown-cochange-couplings`
- Design: `docs/designs/markdown-edge-graph.md` · Owner summary and answers: `docs/designs/markdown-edge-graph-decisions.md`
- Commits on `main`: 2abead8..e53371a · On the task branch: e52f68e, 35582c2 · Pull request 13
