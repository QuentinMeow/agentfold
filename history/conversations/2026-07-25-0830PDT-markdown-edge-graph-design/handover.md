# Handover — markdown edge graph design

**Session:** 2026-07-25 08:30–11:10 PDT, local time, claude
**Task:** none — exploratory design, no task claimed
**Mode:** async
**Queue projection:** v1

## What happened

- Designed a repository knowledge graph over markdown docs and wrote it to
  `docs/designs/markdown-edge-graph.md`, with a self-contained owner-facing summary and
  decision list at `docs/designs/markdown-edge-graph-decisions.md`. Nothing was implemented.
- Ran nine subagents across two rounds: four prior-art/approach research passes and five
  adversarial or design reviews (maintenance cost, parser implementability, agent retrieval
  value, revised-architecture attack, end-to-end workflow).
- v1 was rejected by measurement and rewritten. The owner then redirected to one-directional
  edges with a CLI-generated graph artifact as the core mechanism, recommended actions on
  change, test/commit gates, and explicit tolerance for agents forgetting.
- v2 architecture: three layers — declared one-way edges as source, a derived committed text
  projection holding both directions, and consumers (queries, a blocking structural gate, and
  a repair loop that files retry items for everything judgment-shaped).
- Replaced stored content digests with **clause-scoped review debt** derived from git: map the
  target's headings to line ranges, intersect with changed lines, and raise debt only for
  dependents of the section that actually changed. No stored state, so no churn.
- Measured the decisive alternatives instead of arguing them. SQLite was disqualified as the
  artifact (optional CPython module, and not byte-reproducible across insert orders); a text
  projection costs **~16k tokens** against pretty JSON's ~57k for the same graph.
- **Reversed a rejection.** Co-change mining was first dismissed at 7.4% precision, measured
  against a reference set of files that textually cite the target. Re-measurement showed
  mention-edges and co-change-edges are roughly 95% disjoint here — Jaccard 0.049 to 0.051,
  with 78 to 85% of co-change pairs mentioned nowhere — so that figure was precision against
  the wrong yardstick. The decisive verified case: `templates/queue/review.md` restates the
  prefix rule that `message-queue/AGENTS.md` owns, never names it, and co-changes at
  confidence 0.81 over 13 commits.
- v3 therefore adds a **mined layer that ships before the schema**, with declaration as the
  residue, a three-way confirmed/undeclared/suspect join borrowed from reflexion models, and
  an append-only accepted/rejected ledger so a dismissal survives the agent that made it.

## How it works now

Nothing executes yet. Two design documents exist under `docs/designs/`, three `needs-human/`
items are live, and all of it is staged and uncommitted. No pre-existing repository file was
modified, no template or contract changed, and no checker was added, so the proposal is fully
reversible by deleting files.

## Decisions made for you

- Two one-way doors were answered by the owner in chat and transcribed into their queue items:
  the repo-root path-type default, and authoring one direction only with the reverse derived.
- The v1 review binding was **retired rather than re-pointed**: it was approved against exact
  bytes that the v2 rewrite replaced, and re-binding an `approved` outcome to a document the
  owner has not seen would have falsified the record. A fresh v2 review item carries the new
  binding and preserves the v1 approval as context.
- Two-way calls recorded in the design: `## Edges` rather than `## Links` (27 files already use
  the latter under a free-form schema); `references` reinstated as a graph-only relation, since
  one-way edges remove the reason it was dropped; blocking checks placed in the reconciler
  (~5 s) rather than the test suite (measured **205 s**).

## Needs your attention

- [confirm the repo-root default, or keep the relative default you specified](../../../message-queue/needs-human/decisions/future-blocking-choose-edge-path-type-default.md) — Why-you-might-care: A relative default requires the checker to rewrite paths whenever a file moves, and this repository's rename detection is measurably unreliable, so a wrong guess would silently repoint a correct link. || If-you-do-nothing: No path-type vocabulary is fixed and no checker is written; the proposal stays documentation only.
- [choose Option A or Option B, or state another model](../../../message-queue/needs-human/decisions/future-blocking-choose-edge-reciprocity-model.md) — Why-you-might-care: Every later choice about the edge schema, the checker, and the query tool follows from this one, and reversing it means rewriting every declared edge. || If-you-do-nothing: No edge schema exists and nothing is built; the proposal stays documentation only.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [approve the revised architecture and answer decisions N1 to N8, or request a named change](../../../message-queue/needs-human/reviews/future-blocking-review-markdown-edge-graph-v2-direction.md) — Why-you-might-care: A measurement reversal means mining git history — not declared links — is now the cheap half that ships first, and decision N1 decides whether it gets to prove the schema unnecessary before the schema is built. || If-you-do-nothing: Nothing is built and no pre-existing file changes; the design and its decision list stay proposals.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- **Reciprocal edge blocks written into both files (v1).** Unsatisfiable: `tasks/AGENTS.md`,
  `message-queue/AGENTS.md`, and `automation/AGENTS.md` sit at exactly 60 of 60 permitted lines,
  so injecting backlinks produces a budget finding fixable only by deleting contract prose. Do
  not re-propose without first resolving the line budgets.
- **Stored content digests as freshness pins.** Non-convergent for mutual dependencies, and
  ~200 merge-blocking findings/day modelled against real history. Superseded by clause-scoped
  debt that is derived from git each run rather than stored in the files.
- **A lexical undeclared-link signal.** An earlier revision reported inline links with no
  declared edge as the completeness hint; 78 to 85% of real co-change pairs are mentioned
  nowhere, so that block would have been mostly wrong. Co-change is the signal instead.
- **SQLite as the stored graph artifact.** Optional CPython module, and byte-nondeterministic
  across insert orders even after a full vacuum, so it cannot sit behind a byte-exact check.
- **Declaring duplication.** The agent who restates a rule is the one who did not know another
  file owned it; duplication needs lexical detection, not declaration.
- **Reusing the canonical bold-key field regex.** Anchored at column zero with a key class that
  excludes parentheses, so indented edge fields are invisible to it while column-zero repeated
  keys are rejected by an existing check. The schema therefore requires a separate parser that
  operates over the shared semantic view, leaving fenced examples inert.

## Next steps

None.

## Deep links

- Design: `docs/designs/markdown-edge-graph.md` · Owner summary and decisions: `docs/designs/markdown-edge-graph-decisions.md`
- Commits: none — all new files staged and uncommitted, pending owner review
