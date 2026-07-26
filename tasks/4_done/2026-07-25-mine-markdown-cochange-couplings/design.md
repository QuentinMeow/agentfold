# Design notes — mine markdown co-change couplings and validate heading anchors

**Status:** decided

## Problem

The architecture is already settled in `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`,
so this task chooses nothing about edges, vocabulary, or freshness. Three narrower choices
were still open, and each of them decides where code and state live:

1. Where the mined co-change layer runs. The design describes it as "one reconciler check
   of roughly 120 stdlib lines", which would make it a `CHECKS` entry.
2. Where the accepted/rejected ledger lives, given that it has to outlive every agent that
   writes to it and stay readable on a bare clone.
3. How heading-anchor validation reaches the existing link check without changing what that
   check already reports.

The files this task creates, none of which exist yet:

```
automation/mine_cochange.py             the mining and ledger CLI
automation/cochange-ledger.txt          the append-only verdict ledger
automation/tests/test_mine_cochange.py  CLI unit tests
automation/tests/test_reconcile_links.py  anchor-validation unit tests
```

## Options considered

### Option A — mining as a reconciler `CHECKS` entry

What the design text suggests. Every finding in `automation/reconcile/reconcile.py` blocks
the commit, because findings carry no severity yet — that is exactly the gap the separate
backlog task 2026-07-22-severity-tiers-for-reconciler-findings exists to close. A mined
coupling is a suggestion with a measured false-positive rate in the 10–25% band that the
design's own governance rules call "probation". Shipping suggestions through a blocking gate
converts an advisory into ~2 hard stops per fifth commit, which is the failure mode the
rejected digest-pin mechanism died of. There is a second cost: a whole-history `git log` walk
inside a check is quadratic here, because `check_task_admission_history` re-enters the check
registry once per admitted Git edge under `git_revision_candidate`.

### Option B — mining as a standalone advisory CLI (chosen)

A separate `automation/` tool whose report verb always exits 0. It runs when an agent or CI
asks for it, walks history once, and costs the pre-commit path nothing. The reconciler keeps
its ~5-second budget and its property that every finding is structural. The advisory tier
can move into the reconciler later, without rewriting the miner, once severities exist.
Honest cost: an ignored advisory leaves no trace in the repository until repair-item filing
exists, and repair-item filing is deferred past this task.

### Option C — ledger under `memory/`

The ledger is durable project knowledge, so `memory/` is the obvious home. It is the wrong
one. Entries there carry `Review-by` dates and are re-verified, compacted, or deleted by the
memory-gardener pass; a rejected coupling is a permanent verdict, not an expiring fact.
Machine-appended rows would also churn `memory/index.md` on every dismissal.

### Option D — ledger as a tracked text file beside the tool (chosen)

`automation/core-scope-paths.txt` is the standing precedent: a tracked, plain-text data file
that lives next to the gate that reads it, with no schema ceremony and no expiry. The
ledger follows it — append-only, one line per verdict, diffable, and present on a bare
clone. The rejection count is then a `wc`-able number rather than a derived query, which is
what makes the governance threshold self-measuring.

### Option E — anchor validation as a new check versus inside `check_links`

A new check id would report anchors separately from paths, and would double the work of the
`live_markdown_files` walk. The hole is inside `check_links` itself:
`re.fullmatch(r"[\w./-]+", cand)` rejects any candidate containing `#`, so today a link
whose path *and* anchor are both wrong produces no finding at all. Fixing it where it broke
keeps one check id — which matters, because retry filenames embed check ids
(`memory/lessons/automation/deterministic-finding-keys.md`) — and it makes the fix a strict
increase in what `link-check` catches rather than a new surface.

## Chosen

Option B, Option D, and Option E. Mining is a standalone advisory CLI with a
report verb that always exits 0; its ledger is an append-only tracked text file beside it;
anchor validation lands inside the existing `check_links` and keeps the `link-check` id.

The fragment half reuses `semantic_text` from `automation/markdown_semantics.py`, so fenced
code blocks and HTML comments cannot donate headings the renderer never emits — the same
blanking pass the rest of the reconciler already trusts. Slugs follow GitHub's algorithm
because that is the renderer every reader of this repository actually uses.

Nothing here is a one-way door under `handbook/collaboration-modes.md`: no `templates/`
schema changes, no `handbook/principles/` file changes, no dependency added, and both new
files can be deleted without migrating anything. The one-way-door decisions this stage
depends on are already recorded as ADRs.

## Core fit

**Agent substitution:** pass — the report is derived from the repository's own Git history by a stdlib script and a tracked ledger file, so any runtime that can run `python3` and `git` reproduces the same ranked pairs and the same verdicts; nothing depends on a model, a prompt, or one agent's recollection
**Provider substitution:** not-applicable — both halves read the local Git object store and the working tree, and no hosting provider supplies, gates, or versions either input; CI merely invokes the same local commands
**Repository substitution:** pass — every adopted repository accumulates markdown whose real dependencies are recorded nowhere and whose cross-file heading links rot silently; the miner learns its couplings from that repository's own history, and the floors are flags rather than constants fitted to this one
**User-global writes:** none
**Why AgentFold core:** `check_links` is the mechanism that keeps this framework's file-based coordination honest, and its `#`-fragment blind spot means a contract can cite a heading that no longer exists and no gate notices; the miner is the evidence source that decides whether the declared-edge schema is ever built, so keeping it in a private overlay would move the harness's own next design decision out of the repository that has to live with it
**Thin adapter:** none

## The gating experiment

Step 9 of `plan.md` is what makes this stage falsifiable, and its result is written back
into this section. For the two hottest markdown files, each top-ranked coupling gets two
recorded judgments: whether it is a real dependency, and whether a hand-authored edge would
have said anything the mined pair plus its shared commit subjects did not. A finding that
the mined list is already sufficient ends the project at Stage 1 — the advisory is then the
whole feature, and the typed schema, the artifact, the join, and the viewer are all
unjustified.

**Ran:** 2026-07-25 at commit e52f68e. Every command and its real output is in
`verification.md`; this section states only what the outputs decided.

The two hot files were chosen on measured in-scope revision counts, not on the brief's
guess: `automation/AGENTS.md` at 19 revisions and `message-queue/AGENTS.md` at 14.
`handbook/git-workflow.md` measures 14, not the 16 the design claims, so it is not one of
the two hottest. Twenty-seven candidates touch the two chosen files at confidence ≥ 0.5,
and all twenty-seven were judged by reading the files and the shared diffs.

### Verdict 1 — the mined signal is accurate enough to be worth running

**Effective false positives: 1 of 29 judged candidates, 3.4%. Governance state: on
target** (under 10%). One reading note the ledger cannot carry itself: no typed schema
exists, so the 28 accepts do not mean "an edge was declared" the way the design's ledger
section defines accept. Each means *judged a real dependency, to be declared if and when
Stage 2 ships.* The ledger is a judgment record, not a declaration record.

The single rejection is the pair whose coupling the reconciler
already enforces bidirectionally through a task's queue-actions field and a queue item's
blocking field — a coupling the design's own vocabulary rule says the generic graph must
not restate.

Three results carry that verdict, and one qualifies it.

- **Mining sees what nothing else in this repository can.** 25 of the 27 hot-file pairs
  have zero occurrences of the partner path in either file — 93% disjoint, stronger than
  the design's 78-85% figure. The one pair that is mutually mentioned is the only one grep
  could have found.
- **The decisive example holds up under verification.** `templates/queue/review.md`
  contains the string `message-queue` zero times while restating the prefix rule that
  `message-queue/AGENTS.md` owns five lines in. The experiment also found what the design
  missed: the restatement is *fivefold* — all five queue templates carry the identical
  six-line comment, none links its owner, and mining surfaced all five in the top eight of
  the default view.
- **It found a live drift nothing else had noticed**, recorded below in full so it can be
  repaired from this text alone.
- **The qualification: precision here is high and information content is low.** 27 of the
  52 candidates at confidence ≥ 0.5 come from about twelve commits of one task, each
  touching 5 to 16 of the same markdown contracts, none large enough for the 40-path cap
  to skip. A 12-file commit creates 66 pairs by itself. So the accepts are true but they
  are one fact — "these eleven contracts are one subsystem, edited as a unit" — reported
  twenty-seven times. Coverage is 17 of 172 in-scope files, so "available on day one for
  every file" is available, not informative, for the other 90%.

The rate is also population-dependent in a way the governance rule does not admit: 0.0%
over the 27 hot-file candidates, 3.4% over the whole ledger, and **10.0% — the probation
trigger — over the default report's top ten**, which is what an agent actually sees. At
these volumes one verdict crosses a band boundary. Two further honesty notes: the same
agent authored the report and judged it, where the published definition assumes the judge
is the tool's user; and the support floor is nearly inert here, since raising it from 3 to
5 removes only 9-17% of candidates at every confidence while confidence alone moves the
set 4.7×.

### The live drift, stated so it can be repaired without re-deriving it

Commit aca7014, "harness: harden queue snapshot boundaries", tightened the future-blocking
boundary to require a UTC date. It edited seven files in one commit. Four of the seven took
the tightening; five prose comments did not, and the inconsistency is live at this commit.

Owner of the rule, which now says UTC:

- `message-queue/AGENTS.md` line 17 — "work continues until an explicit **UTC** date, event, or"

Check summary, which took it in the same commit:

- `automation/AGENTS.md` — "starts with a reached **UTC** `YYYY-MM-DD`; event boundaries require actor reclassification."

The five templates were all edited in that same commit and each took UTC in its field line
while keeping the older wording in its filename comment. In every one of the five the two
lines are:

- line 4 — "- future-blocking-: work may continue, but must stop at **a named date**, event, or transition."
- the `Blocks at` line — "<**UTC** YYYY-MM-DD | event:<name> | transition:<name>>"

The five files, all with the drifted sentence at line 4 and byte-identical to each other:

- `templates/queue/review.md`
- `templates/queue/clarification.md`
- `templates/queue/decision.md`
- `templates/queue/request.md`
- `templates/queue/retry.md`

The repair worth making is not five edits but one deletion: the six-line filename comment at
the head of each template restates a rule `message-queue/AGENTS.md` owns and names no source,
against the guardrail that every fact lives in exactly one file. Replacing those six lines
with a single link to the routing section of the owning contract removes the drift, removes
its four siblings, and brings the reference inside `link-check`'s reach — where the anchor
validation added by this same task will then keep the heading honest.

### Verdict 2 — a hand-authored typed edge would have added something, but far less than the design spends on it

Not "mostly no", and not the design's case either. Splitting it by field, because the
fields do not stand or fall together:

**What the mined pair plus its commit subjects genuinely cannot say — the relation type.**
All 27 candidates draw their evidence from the same pool of twelve commit subjects.
"harness: bind actions and reviews to exact boundaries" is the leading evidence line for
the pair that copies a prefix rule, for the pair that summarises a reconciler check, and
for the pair that restates provider admission. Those are three different relationships and
one indistinguishable sentence. The subjects convey *which feature landed*; they never
convey *what the relationship is*. And the type changes the disposition: a restatement is a
candidate for deletion, a dependency is a candidate for review, an enforcement link is a
candidate for keeping. The design's claim that shared subjects are "already-written,
never-stale rationale" is measurably weaker than it reads — which is an argument *for*
authoring one sentence per edge, and it is the strongest thing this experiment found in the
schema's favour.

**What the clause anchor is worth: real on one hot file, unavailable on the other.** On
`message-queue/AGENTS.md`, 13 of 14 in-scope revisions touched only its lifecycle section
and just 3 touched the routing section that owns the prefix rule, so a clause-anchored edge
fires 3 times instead of 14 — a 4.7× noise reduction, confirmed. On `automation/AGENTS.md`
— the hottest markdown file in the repository — every one of its 22 revisions reports one
section of one, because the file has exactly one heading. The design requires an anchor
only when a target has two or more headings, so for the busiest target in the repository
there is no anchor to require and clause scoping degenerates to file scoping. Twelve of the
29 judged candidates (41%) point at that file.

**What the experiment killed outright: clause-scoped review debt derived each run.** The
numbers, inline, because they are the whole reason the mode is struck. `message-queue/AGENTS.md`
has 14 in-scope revisions in the walk. Its routing section changed in 3 of them, and the
prefix definitions the five templates restate changed in exactly **2 of 14** — aca7014 and
3f4f1df. In **both** of those commits every restating template was edited in the same commit:
aca7014 touched all five, 3f4f1df touched all five plus `templates/handover.md`. Derived debt
closes when the dependent is next modified, so across the entire history of the design's
strongest candidate — its single decisive example — the `each-run` mode would have filed
**0 items**.

Worse than useless: the one real drift it exists to catch happened *inside* aca7014, one of
those two commits. The dependents were touched for a neighbouring reason — their `Blocks at`
field lines — while the restated sentence three dozen lines above went stale. Touched is what
closes debt, so the mechanism would have reported nothing on the only failure in its own
domain, in the very commit that caused it. A mode that fires zero times on the best case and
is blind to the one live defect is not a mechanism worth a per-folder configuration surface.

**What the experiment reframed: the right disposition for the flagship case is deletion,
not declaration.** The prefix rule is duplicated in five templates with no link to its
owner, against this repository's own guardrail that every fact lives in exactly one file
and other places link to it. Replacing the six lines with one link single-sources the fact,
brings it inside `link-check`'s reach, and removes the coupling entirely — whereas a
restatement edge preserves the duplication and adds a permanent maintenance duty on top of
it. The design's own rejected list already says declaring duplication needs lexical
detection instead. So on the case the design leads with, the typed edge is not just
optional, it is the wrong instrument.

### Recommendation — narrow, sharply

Build Stage 2 in a reduced form; **do not build Stage 3; build only half of Stage 4.**
"Build everything" is not supported by anything measured here, and "stop at Stage 1" is
refuted by the relation-type finding.

Survives:

- The relation vocabulary and the one-question test. This is the only thing mining
  demonstrably cannot express, and it decides the disposition.
- One `Because:` line per edge, because the free evidence is measurably non-discriminating.
- The clause anchor where the target has two or more headings, for the impact query only.
- `Update-when:` as prose the query prints, on the two relations that already require it.
- The three-way join report — confirmed, undeclared, suspect — which is nearly free once
  edges exist and is what surfaced the fivefold duplication above.
- The ledger, unchanged. It worked.
- Per-directory activation, unchanged, and `handbook/` first as planned.

Does not survive, and should be struck from the plan rather than deferred:

- **The whole of Stage 3.** A committed text projection, a byte-exact gate, determinism
  and foreign-environment tests, a generated-file attribute, a writer refusal rule, and a
  regenerate-on-conflict merge procedure, for a graph whose measured candidate set spans 17
  files. The in-edge query it exists to serve is a `git grep` over the edge sections at the
  same 40 ms the design already measured for backticked paths. Build the graph on demand;
  commit nothing.
- **The `each-run` freshness mode.** Measured silent across the whole history of the
  strongest case, and blind to the one real drift. The `review-window` mode the accepted
  decision already made the default is what should ship; `advisory` stays as the cheap
  option. Removing `each-run` also removes the per-folder configuration surface's most
  expensive third.
- **Repair-item filing for review debt**, since the debt it would file does not exist.
  Filing for the join's undeclared list survives.
- **The viewer**, already deferred, with nothing here to justify reopening it.

One recommendation that belongs to a different task: the five-way duplication of the prefix
rule and the live UTC drift should be repaired by single-sourcing the rule, not recorded as
edges. That repair is worth more than any of Stage 2, and it is available today.

Finally, an operational defect the experiment hit and could not repair inside its own
boundary: the shipped ledger's unit test asserts that the tracked ledger holds no verdicts,
so the mechanism's first real use makes the test suite fail and the repository
uncommittable. The transcript is in `verification.md`. Whatever is decided about Stages 2
to 4, that assertion has to change before the ledger can be used at all.

One limitation applies to every number the experiment produces. This repository holds four
days of history and roughly 107 in-scope markdown-touching commits, while the published work
this technique borrows from discards the first few hundred change records as warm-up. Every
support, confidence, and precision figure is therefore provisional and will move as history
grows, in a direction nobody can predict from here. Mining is also indifferent to quality:
it learns established bad practice as readily as good, so a reported coupling may be a
duplication worth removing rather than a dependency worth declaring.
