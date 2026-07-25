# Markdown edge graph — declared one-way edges, a derived graph, and a convergent repair loop

**Status:** proposal, not an accepted decision
**Open questions:** `docs/designs/markdown-edge-graph-decisions.md`
**Revision:** v3 — adds a mined co-change layer that ships before the schema, after
measurement showed textual mention and real coupling are nearly disjoint here. v2 kept
one-directional edges, the graph artifact as the product, and eventual consistency through
the retry queue. v1's reciprocal-metadata model is recorded under "Rejected by measurement"
because it is intuitive and will be proposed again.

A portable contract for recording *why* two documents are related and *when* changing one
obliges revisiting the other, so an agent about to edit a file can ask the repository —
not its own memory — what else must be reviewed.

## Outcome

Four layers, each with one job:

0. **Mined.** Co-change coupling read from git history — which files have actually changed
   together, with what support and confidence. Zero annotation, never stale, available on
   day one for every file.
1. **Declared.** A markdown file declares its outgoing edges in an `## Edges` section.
   Forward direction only; no inverse relation is ever written in any file. Declaration is
   the *residue* — it records what mining cannot express, for the couplings mining surfaced.
2. **Derived.** A stdlib CLI joins the two into a graph holding **both** directions, plus a
   generated text projection that renders on GitHub and reads cheaply as tokens.
3. **Consumers.** Queries answer "what must I review if I change this"; a blocking gate
   rejects what is objectively wrong; everything judgment-shaped becomes a repair item that
   a later session picks up.

The design assumes agents forget. Layer 0 does not depend on anyone remembering anything,
and layer 3's repair loop — not layer 1's discipline — is what makes the declared half
converge.

## What is actually new here, and what is borrowed

Borrowed, because it is settled elsewhere: forward-only authoring with a derived reverse
direction (Backstage forbids authoring the reverse; RFC 8288 deprecates it; Sphinx-Needs
recomputes it); the inverse name declared once in the schema (StrictDoc, PROV-O);
relationship names echoing Dublin Core; generated-artifact discipline (this repo's own
generated memory index).

New, and therefore the part with no external validation: **a per-edge sentence explaining
the relationship, a per-edge update condition, and clause-level scoping.** No surveyed
system carries any of the three. They are the design's contribution and also its
unverifiable surface — both facts belong in the same sentence.

## Honest baseline: git already knows, and text does not

This must be stated before any schema, because it changes what the schema is *for*.

The intuitive baseline is the repository's own prose: **451 backticked repo-root paths**
against 4 relative markdown links, invertible by `git grep` in about 40 ms. That baseline
is a trap, and the measurement is unambiguous.

**Mined co-change and textual mention are nearly disjoint signals on this repository:**

| Measured (support ≥ 3, confidence ≥ 0.5, commits capped at 40 files; identical scope both sides) | `templates/` in | `templates/` out |
|---|---|---|
| mention-derived edges | 184 | 154 |
| co-change-derived edges | 84 | 40 |
| intersection | **13** | **9** |
| Jaccard | **0.051** | **0.049** |
| co-change pairs mentioned nowhere in prose | **71 (85%)** | **31 (78%)** |

Both columns are reported because scope changes the magnitude and not the conclusion; an
earlier asymmetric run that excluded `templates/` from one side only overstated the gap
slightly, at 0.041 and 86%.

The single decisive example: `templates/queue/review.md` restates, in its own opening
lines, the exact `blocking-` / `future-blocking-` / `non-blocking-` prefix semantics that
`message-queue/AGENTS.md` owns — and **never names that file, zero occurrences**. It
co-changes with it at confidence 0.81 over 13 commits. That is a real, load-bearing
dependency that no link checker, no grep, and no graph derived from declared links can
see, and git records it for free.

The same query recovers the design's own motivating claim. For `handbook/git-workflow.md`
(16 in-scope revisions) mining returns **8 partners** — `automation/AGENTS.md` at 0.88,
`handbook/human-action-guide.md` at 0.81, four queue templates, `message-queue/AGENTS.md`
— which is the dependency set this design was written to make visible.

Three consequences follow, and they reshape the plan:

1. **Mining is the cheap half and it ships first.** It needs zero annotation, cannot go
   stale, covers every file on day one, and its native output *is* the impact query.
2. **Declaration owns what mining cannot express**: the relation *type*, the *clause*, the
   *reason*, and the *trigger*. Co-change cannot distinguish `depends-on` from `restates`
   from `generated-from`, and it never says why.
3. **A lexical "undeclared link" signal is noise.** An earlier draft reported inline links
   with no declared edge as the completeness hint; at 78-85% disjointness that block would be
   mostly wrong. Co-change replaces it as the signal.

**The two layers have deliberately different scope.** Declaration excludes `templates/`,
because a schema file's every value is a placeholder. Mining must *include* it — the
decisive example above is a template, and template-to-contract coupling is exactly the
restatement drift this design exists to catch. Same asymmetry for the record folders: they
are excluded from both, since their coupling is an artifact of when they were written.

## What can and cannot be enforced

| Property | Mechanically checkable |
|---|---|
| Edge record well-formed; relation and path type in the closed vocabulary | **yes**, exactly |
| Target exists (in-repo path or logical id), against the git index | **yes** |
| The named `#clause` exists as a heading in the target | **yes** |
| Declared path type matches the target string's shape | **yes** |
| `Update-when` present where required, absent where forbidden | **yes** |
| `supersedes` / `restates` chains acyclic | **yes** |
| The derived projection matches the declared edges | **yes**, byte-exact |
| **The target's named clause changed and the dependent has not been touched since** | **yes** — from git alone; see "Review debt" |
| A pair co-changes in git history with no declared edge | **yes** — reported as *undeclared*, never as an error; this is the completeness signal |
| An inline link to an in-scope node has no declared edge | yes, but **78-85% disjoint from real coupling** — not used as a signal |
| A relationship that exists in reality but was never declared | **no** — undecidable |
| Whether a `Because` sentence is true | **no** |
| Whether a change actually triggered the update condition | **no** — judgment |

The system enforces the **consistency** of declared edges and **detects** review debt. It
reports, never enforces, **completeness**. Every query prints what it does not know.

## Node and scope

A **node** is a tracked markdown file in an activated directory — plus, for `enforced-by`
only, a non-markdown file with an optional `::symbol`.

Scope is **per-directory opt-in**, activated by a schema field in that directory's
`AGENTS.md`, following the pattern the conversation-history contract already uses.
Activation is sticky: removing the marker after activation is itself a finding.

Activation is not caution about breaking the repository — the owner has accepted that the
current repository does not conform. It is load-bearing for a different reason: the
pre-commit hook is `set -e` and bypassing it is forbidden, so the checker and the edges
**must be able to land in separate commits**. Without activation, the commit that
introduces the checker cannot itself be committed.

Permanently out of scope, matching exemptions the reconciler already declares:
`history/`, `memory/decisions/`, `message-queue/needs-agent/retries/`, `templates/`,
`tmp/`, dot-directories, and symlinks. These are records that legitimately cite paths that
have moved, or schemas whose every value is a placeholder.

## Edge record schema

One list item per edge; one field per line; **never wrapped**. Long lines are legal;
ambiguity is not.

```markdown
## Edges

- **depends-on** `handbook/git-workflow.md#conflict-avoidance-by-construction-not-by-care` (repo-path)
  **Because:** this checker's rewrite rules assume concurrent agents never edit files another task owns.
  **Update-when:** that section changes which lane may write contracts, or drops the one-item-one-file rule.

- **enforced-by** `automation/reconcile/reconcile.py::check_links` (repo-path)
  **Because:** the claim that every in-scope cross-reference resolves is true only while that check runs.
  **Update-when:** the check's exemption list changes, or it is renamed or removed.
```

A file with no edges writes `## Edges` and `None.` — one line. An absent section in an
activated directory is a finding; `None.` never is. Forcing a *decision* rather than a
*sentence* is deliberate: requiring a justification for having no edges would manufacture
vacuous prose, which is the failure this design spends most of its effort avoiding.

| Field | Required on | Meaning |
|---|---|---|
| relation | every edge | one verb from the closed vocabulary; its name carries the direction |
| target | every edge | backticked path or logical id, optional `#clause`, optional `::symbol` |
| path type | every edge | how to read the target string, in parentheses |
| `Because` | every edge | one line: what the relationship *is* |
| `Update-when` | `depends-on`, `enforced-by` | one line: the condition obliging a change here |

`Update-when` is **forbidden** on the other relations, where every honest answer is either
"never" or a restatement of the relation name.

### Parsing rules that survived attack

- **The parser runs over the repository's shared semantic view of the file**, which blanks
  fenced code blocks and HTML while preserving line numbers. This is not optional: the
  five edge-shaped lines in this repository today all sit at column 0 inside fences, and
  they are inert *because of fence blanking*, not because of any indent rule.
- **Nothing indented four or more spaces is structural** — a second layer, not a
  replacement for the above.
- **No arrow.** The relation name carries direction, and an arrow adds a
  homoglyph-spoofing surface for no information.
- **Backticked target, not a markdown link.** Repo-root targets need no rewriting when the
  declaring file moves, which matters because git rename detection misses 15% of this
  repository's real moves and a false positive would silently repoint a correct link.
- **The schema needs its own parser.** The repository's canonical bold-key regex is
  anchored at column zero and its key class excludes parentheses, so indented edge fields
  are invisible to it, while column-zero repeated keys are rejected by an existing check.
  Key names avoid parentheses anyway, so they degrade gracefully rather than half-parse.
- **A finding's subject is `<path>#<relation>:<target>` and never contains a line number.**
  Retry filenames embed a hash of the subject, so a line number would file a new repair
  item every time an unrelated edit moved the record. The line number goes in the message.

## Relation vocabulary — forward only

Only the left column is ever written in a file. The right column exists in the CLI and the
future viewer as a display label, so a reverse query reads naturally.

| Authored | Reverse label (display only) | Means | `Update-when` | In impact output |
|---|---|---|---|---|
| `depends-on` | required by | this file becomes **wrong** if the target changes | required | must review |
| `enforced-by` | enforces | a prose rule ↔ the code or test that makes it true | required | must review |
| `restates` | restated by | deliberate copy of a rule the target owns | forbidden | must review |
| `supersedes` | superseded by | replacement; acyclic | forbidden | informational |
| `decided-by` | decides | proposal ↔ the record that ruled on it | forbidden | informational |
| `generated-from` | generates | derived artifact ↔ its source | forbidden | informational |
| `references` | referenced by | contextual link, no obligation | forbidden | **never** — graph only |

**One authoring rule covers all seven: the file that would become wrong declares the
edge.** `supersedes` is the single exception — the superseded record is immutable, so the
replacement declares it.

`references` is included, reversing v1's decision, because the reason for excluding it has
gone. Its problem was that an obligation-free relation absorbs every edge an agent is
unsure about and silently pollutes impact answers. With impact output filtered by relation,
a mis-typed `references` is inert: it populates the knowledge graph the owner wants to
render and never appears in a recommendation. `Update-when` is forbidden on it, and it
costs two lines.

### The one-question test

> If the target changed without my knowing, would this file become **wrong**?

Yes → `depends-on`. No → `references`, or nothing at all. An obligation-bearing edge costs
three lines and a permanent duty; a `references` edge costs two and none.

`blocked-by` is deliberately absent. The repository already enforces it bidirectionally
between a task's queue actions and a queue item's blocking fields, checking the task id
token *and* the timing class — strictly stronger than anything here. **Where a
domain-specific typed field already exists and is checked, it stays canonical and the
generic graph does not restate it.** The generic vocabulary exists for the documents that
have no such field.

## Path types

| Value | Target is | Existence check |
|---|---|---|
| `repo-path` | repo-root-relative, no leading slash (**default**) | hard, against the git index |
| `file-relative` | relative to the declaring file's directory | hard, against the git index |
| `logical-id` | a task id, record slug, or check id that survives `git mv` | hard, against the id's registry |
| `outside-repo` | an absolute path outside the repository | **never** |
| `url` | http(s) | never, and never fetched |

Three consequences worth stating:

- **`logical-id` is the type this repository needs most.** Its own contract says to
  reference tasks by id and never by path, and there were 73 task-folder renames in four
  days — every rename in the repository's history was a task folder.
- **Existence is checked against the git index, never the filesystem.** On a
  case-insensitive filesystem a case-wrong path exists on disk and would pass locally, then
  fail in CI.
- **`outside-repo` targets are opaque strings the checker never resolves.** It must not
  expand `~` or read outside the repository: the core-admission gate rejects tracked
  executables touching user-global state, and a check whose answer depends on which machine
  ran it cannot gate anything.

## The graph artifact

**One committed, line-oriented text projection**, generated and byte-exact verified —
the mechanism the repository's generated memory index already runs successfully. A
structured form is emitted on demand, never stored.

Format chosen on measurement, at 250 nodes and 400 edges:

| Candidate | Size | Tokens | Verdict |
|---|---|---|---|
| text projection, structure only | 56 KB | ~16k | **chosen** |
| text projection + all prose | 132 KB | ~38k | prose served per-query instead |
| pretty JSON | 198 KB | ~57k | 3.5× the tokens for identical information |
| SQLite | 252 KB | — | **disqualified**, see below |
| GraphML / JSON-LD / Turtle | 130-200 KB | 38-57k | verbose conformance nobody consumes |

- **Prose stays out of the whole-graph projection.** It more than doubles the artifact, and
  an agent editing one file needs three edges' worth of prose, not four hundred.
- **SQLite is disqualified as the stored artifact on two independent grounds.** Python
  documents its `sqlite3` module as *optional* — "if it is missing from your copy of
  CPython, look for documentation from your distributor" — which fails a contract of
  running on a bare clone anywhere. And it is not byte-reproducible: rebuilding the same
  logical rows in a different insert order produced different bytes even after a full
  vacuum, so it cannot sit behind a byte-exact gate.
- **Never intern node ids in the committed file.** Integer ids save 33-45% of tokens and
  renumber every later id when one node is inserted, converting a one-line change into a
  whole-file rewrite. Token efficiency belongs in ephemeral output; diff stability belongs
  in the committed file.
- **Queries must parse line shapes, not grep substrings.** A bare substring search over
  the projection returned 9 hits where the correct answer was 5, because it matches both
  directions and both clause variants.

### Why committed, and the cost

Committing gives three things one-sided authoring otherwise gives up: a bare clone answers
"what depends on this" with no command run; GitHub renders it, which is the only way
in-edges reach a human reviewer; and the diff shows the semantic consequence of an edge
change during review. The precedent is uniform across ecosystems — dependency lockfiles,
Rails' schema file, Terraform's lock file are all generated, committed, and **resolved on
conflict by regeneration**, which for a fully derived file is always correct.

Mark it generated in a tracked `.gitattributes` so GitHub collapses its diff by default.
**Never define a merge driver**: driver definitions live in untracked local config, so a
fresh clone, a CI runner, an agent worktree, and server-side merges all silently fall back
to the default. **Never use union merge**: it resurrects deleted entries.

The honest cost: a derived copy is a second place a fact lives, every edge change produces
two diffs, and reviewers learn to skim the second. The byte-exact check makes disagreement
*unmergeable* rather than merely unlikely, which is what makes the copy safe; if the
artifact ever grows past a few hundred KB, revisit and move to build-not-commit.

**One refusal rule, precisely scoped.** The writer refuses when a file it *reads* differs
between index and worktree, because the checks read the index and the writer writes the
worktree; combining them silently discards partially staged work. It does **not** refuse on
the state of the file it writes — otherwise resolving a merge conflict in the artifact would
be impossible. The merge procedure is: resolve source conflicts, stage them, regenerate,
stage the artifact.

### Determinism rules

Byte-identical regeneration is the property everything else rests on, and it is exactly
what comparable tools got wrong.

Write with an explicit `"\n"` newline and no BOM; sort every collection explicitly on
code-point order; **never iterate a set** (string hashes are randomised per interpreter
run) and never fix that by pinning the hash seed — run the determinism test *with*
randomisation on; never use locale collation; enumerate files from the git index, not the
filesystem, whose order is arbitrary and whose filename normalisation differs by platform;
no floats, no timestamps, no hostnames, no tool version strings in the body — a hand-bumped
schema integer instead.

**Mandatory test:** generate, generate again, compare bytes; then generate from a fresh
clone in a different directory with a different timezone, locale, and hash seed, and
compare again. The second half is what catches the locale and ordering rules.

**No incremental generation.** Measured: a full pass over this repository's 244 tracked
markdown files is 28 ms, and at 2,000 files the change-detection pass alone is ~60% of a
full rebuild — so incrementality's ceiling is a 40% saving on a 300 ms job, bought with a
cache-invalidation bug class. Revisit at roughly 7,000-10,000 in-scope files, and key any
cache on git blob ids, never mtimes, which are wrong on a fresh clone.

## The mined layer, and the three-way join

Mining is one reconciler check of roughly 120 stdlib lines. It reads commits, counts
co-occurrence, and reports pairs above a support and confidence floor. Parameters, all
measured on this repository:

| Parameter | Value | Why |
|---|---|---|
| support | ≥ 3 commits | below this, every number rests on noise |
| confidence | ≥ 0.8 for the advisory | fires on ~17% of commits, ~2 suggestions each |
| commit size cap | 40 files | tangled commits are the documented dominant noise source |
| stop-list | files the contract requires to change every session | their coupling is mandated, so it carries no information |
| same-directory pairs | suppressed | folder structure already encodes composition |
| evidence | the shared commit subjects | already-written, never-stale rationale, free |

At confidence ≥ 0.9 the advisory fires on about 3% of commits, independently reproducing
the published rate of the original co-change recommender at the same threshold. Compare the
rejected digest-pin mechanism at roughly 200 merge-blocking findings per day.

**The product is the join, not either half.** Borrowing the reflexion-model vocabulary,
which is a thirty-year-old formal primitive rather than an invention:

| State | Meaning | What to do |
|---|---|---|
| **confirmed** | declared *and* co-changed | declaration is load-bearing; leave it |
| **undeclared** | co-changed, nothing declared | **the queue of edges worth authoring** |
| **suspect** | declared, never co-changed | stale or aspirational; re-check or delete |

This inverts the migration cost, which was the design's biggest practical risk. Instead of
recalling 40-60 dependencies from memory, an agent reviews a ranked, evidence-backed
candidate list — mining proposes about 39 directed candidates at support ≥ 3 and confidence
≥ 0.8, the same order of magnitude as the hand-authoring estimate it replaces. And it is
the only place the two prose fields earn their cost, because the author is answering a
specific question about a specific pair rather than filling in a required field.

One caution on `suspect`: an absence carries no evidence, so a declared edge with no
co-change may be genuinely stale *or* may simply predate enough history. The state is
informational and never blocks.

### The accepted/rejected ledger is not optional

Every comparable system that shipped a divergence report also shipped a way to freeze the
existing set — a rules-as-tests framework ships a freezing rule with a violation store
precisely because "when rules are introduced in grown projects, there are often hundreds or
even thousands of violations"; a dependency linter ships a baseline mode. Without a ledger,
the first run's `undeclared` list is unusable and the mechanism dies in week one.

So: an append-only ledger records each mined candidate as accepted (an edge was declared)
or rejected (with a one-line reason). A rejected pair stays rejected and never re-surfaces.
This is also the concrete answer to fault tolerance — it is what makes a *decision* durable
in a system where the agent that made it is gone.

### Governance thresholds, borrowed rather than invented

The one property this design admits its prose lacks is falsifiability. The mined half can
have it, using published operational thresholds from large-scale static-analysis practice:

- An **effective false positive** is any report where the user chose not to act — not "the
  tool was wrong."
- Target under **10%** effective false positives; show results only for changed lines.
- **At or above 10% judged not-useful, the check goes on probation; above 25%, it is turned
  off.** Successful analyzers in that practice run 0-3%.
- Acceptance does not require high precision: the closest industrial impact-analysis study
  found practitioners got utility at 10-25% correctness, with one warning that "too much
  help is not good, I still want the developers to think for themselves." What is required
  is honest ranking, a hard cap of about ten suggestions, and a cheap dismiss.

The ledger's rejection rate *is* the effective-false-positive rate, which makes the
governance rule self-measuring.

## Review debt: freshness without stored pins

This replaces v1's content digests, which were rejected for churn. The mechanism is derived
from git on every run, so there is no stored state to thrash.

For every `depends-on` and `enforced-by` edge that names a `#clause`:

1. Map the target's headings to line ranges.
2. Take the changed line ranges from git history.
3. Intersect. **If the named clause's lines changed**, and the declaring file has not been
   modified in any commit at or after that one, the edge carries **review debt**.

Why this survives the objection that killed digest pins: it is **clause-scoped**. The worst
target under a file-level scheme is the roadmap's current-state file — 15 inbound
references and required by contract to change every session — and under clause scoping it
generates debt only for the dependents of the specific section that changed, which is
almost never those 15. The same reasoning disposes of typo fixes and formatting passes.

Debt **closes automatically** when the dependent is next modified, and explicitly when an
agent records a disposition in the repair item. It is never a commit blocker: it is
judgment, and blocking on judgment strands work whose fix belongs to another task.

This is also what makes the mandatory clause anchor pay for itself, and it is why an anchor
is required whenever a target has two or more headings — on a single-section file the
requirement would have no legal answer.

## Eventual consistency: the repair loop

The design assumes an agent will forget to declare an edge or to review a dependent most of
the time. That is acceptable, and it is the reason the mechanism is a loop rather than a
gate. What must not be acceptable is a *forgotten* omission — every omission becomes a
durable item that some later session picks up.

The repository already has the whole machinery: the reconciler's repair-filing mode writes
one item per finding into the agent-facing retry queue, keyed by a hash of check id plus
subject, refreshes the machine-generated part on re-run while preserving actor notes, and
garbage-collects items whose finding has cleared.

| Condition | Tier | How it clears |
|---|---|---|
| Malformed record, unknown relation or path type, dead target, dead anchor, `Update-when` where forbidden, placeholder prose, cycle, stale artifact | **block** | the agent fixes it; every finding names a literal edit or a literal command |
| A blocking finding whose fix belongs to another task or another folder | **discharged by filing** | clears once a queue item names that finding id and subject |
| Review debt on a `depends-on` / `enforced-by` edge | **repair item** | the dependent is edited, or an agent records "checked, no change needed" |
| An inline link to an in-scope node with no declared edge | **repair item**, capped and diff-scoped | an edge is declared, or the item is rejected in file |
| Edge whose rationale has never been human-reviewed | **repair item** | a review pass marks it |

The third tier is the one this design would not have had without the owner's framing, and
it is what converts "the agent forgot" from a silent hole into a work item. The second tier
is what stops the blocking tier from stranding an agent: a finding it cannot fix is
discharged by filing, not by bypassing the hook.

**Where the tiers live.** The blocking checks belong in the reconciler, which runs in
about 5 seconds. They must **not** go in the repository test suite, which is measured at
**205 seconds** — 98 of them a single test file. Putting a 40 ms check behind 205 seconds of
latency buys nothing and costs every iteration. What belongs in the test suite is **unit
tests of the CLI itself**, which is a different thing and is required. Push and merge gates
come free: CI already runs the reconciler and the tests on push and pull request.

The advisory tier has one honest limitation today: reconciler findings have no severity, so
every finding blocks. Until the filed severity-tiers task lands, advisory output rides in
the pre-commit hook as text that always exits zero — which means **an ignored advisory
leaves no trace in the repository.** Repair-item filing is what closes that gap, and it is
why the loop, not the advisory, is the load-bearing half.

## The agent's guide

The owner's request was a guide agents follow when editing markdown: run the check in both
directions and update the graph if needed. Its honest status matters — a guide is an
instruction, and instructions are wishes. It is worth writing anyway, because the loop
tolerates it being ignored.

Two mechanical facts shape it. **Git has no pre-edit hook** — the hooks directory contains
exactly one file, `pre-commit` — so nothing can intercept the moment between deciding to
edit and editing. And the three highest-traffic leaf contracts sit at exactly their
60-line budget, so an instruction cannot be added to them without displacing contract
prose. The guide therefore lives in a skill plus two lines in the root contract, and the
*guarantee* lives in the template stub and the repair loop.

What the guide says, in order: run the impact query before editing a file that has an
`## Edges` section; apply the one-question test before adding an edge; name a clause, not
just a file; write the sentence or delete the record; regenerate and verify the artifact
twice. Directory activation is a rare, multi-step judgment pass and gets the skill; routine
editing gets the two lines and the hook output.

**One mechanism does make declaration happen rather than be requested:** every template
that creates a file in an activated directory carries an `## Edges` section containing
`None.`, and the checker rejects the unresolved placeholder. This copies the repository's
own working precedent, where a required field must be exactly `none` or a list of valid
paths and the structure check blocks anything else. It converts an unenforceable
instruction into an end-state invariant — at file creation, when the author's knowledge is
highest. For *edits to existing files* nothing guarantees anything, and nothing can; that
is the undecidability above, and the repair loop is the answer.

**One budget concession is required.** Line-budget counting must exclude the `## Edges`
section, or activating the three directories already at 60/60 becomes an unresolvable
failure. This is correct — budgets exist to curate prose read on every visit, and edges are
not that — but it establishes "metadata does not count", so its record should be written
narrowly enough that the next proposal cannot cite it for anything else.

## Query surface

Verbs: `check`, `build`, `impact <path> [--clause]`, `advise --staged|--range`, `debt`,
`review --range`, each with `--json`. Exit codes mean one thing each: 0 clean or answered,
1 repository findings, 2 usage or environment refusal. A repair item is only ever filed for
1.

The output contract is part of the design, because a graph tool that presents a
complete-looking answer over an admittedly incomplete graph will make an agent skip a file
it needed:

```
CHANGING  message-queue/AGENTS.md §Routing: three independent axes (line 8)

MUST REVIEW  4 files declared an edge to this clause
  handbook/human-action-guide.md:136   depends-on
      because      "Choose kind and timing independently" is built on these three axes
      update-when  a prefix is added or removed, or its required timing field changes
  ...

MUST REVIEW  2 code targets — nothing else in the repo tracks these
  automation/reconcile/reconcile.py::delivery_class

CHECK BY HAND  3 files depend on this file but name a different clause
      their update-when names other clauses; confirm before skipping

FROZEN  31 files match by grep; do not edit
  history/** (24), memory/decisions/** (5), tasks/4_done/** (2)

UNDECLARED  2 pairs co-change in history with no declared edge — the graph is incomplete here
  templates/queue/review.md      conf 0.81, n=13   "enforce first-class queue actions", +12 more
  handbook/decision-guide.md     conf 0.56, n=9    "bind actions and reviews to exact boundaries", +8 more

coverage  activated: handbook/ (1 of 11 directories)
          nothing above is claimed about a directory that is not activated
```

Five properties earn this its place, and four are absent from a plain neighbour listing:
**clause scoping** turns noisy file-level hits into precise ones; **FROZEN** encodes the
judgment grep cannot make — 121 of this repository's 123 broken relative links live in
directories that are exempt on purpose; **code targets** appear beside documents;
**UNDECLARED** and the **coverage block print unconditionally, even when empty**, so the
tool always volunteers its own incompleteness. A per-node answer measures about 180-260
tokens, which is the unit an agent actually needs.

## The human surface, and the deferred viewer

The graph's only unverifiable part is two sentences per edge, so the human's job is prose
review, and every human-facing surface should be judged on how directly it delivers those
sentences. Two surfaces earn their keep before any UI exists, and both are nearly free: the
`## Edges` diff in a pull request, and a range digest that prints only new and changed edge
prose with old-versus-new for changes. Six sentences get read; six hundred do not.

The viewer is deferred at the owner's instruction. When it is built, the evidence says
**do not start with a force-directed graph.** Controlled studies find adjacency matrices
outperform node-link diagrams on most tasks **above roughly twenty vertices**, with path
finding the consistent exception; this repository is around 250 nodes, twelve times that
threshold. Practitioners of the closest comparable tool report the global view becoming
useless as the corpus grows and using only the local neighbourhood view. So the first
views are a **faceted node table**, a **local neighbourhood panel** implementing
search-then-expand-on-demand, and a **directory-by-directory matrix** — which is the view
that answers "which folders depend on which".

And it needs no graph library: the generator can precompute a layered layout in Python and
emit coordinates, leaving the page as static markup. Vendoring 435 KB of minified
JavaScript into a repository whose rule is "no dependencies" would be a dependency wearing
a costume, and it would be the largest file in the repository by an order of magnitude.

## Trust assumptions and non-goals

**Assumed.** Whoever authors an edge understands the relationship; the repository's records
are trustworthy; the git index is the source of truth for what exists.

**Not claimed.**

- **Prose quality is not enforced.** This repository is the evidence: all twelve mandatory
  core-fit justifications written to date read `pass — <one clause>`, none says `fail`, and
  none is falsifiable. Required prose drifts toward formula and no deterministic check can
  tell a real reason from a fluent one. The defences are structural — forbid the field
  where it would be vacuous, require a clause anchor so the claim is specific, cap edges
  per file, and put every new sentence in front of a human exactly once. **Fluent filler
  defeats all of them**, and the volume cap is the real defence, which means the design
  must choose between coverage and quality and chooses quality.
- **The graph is never complete**, and every answer says so.
- **A narrow `Update-when` can mislead** — it reads as a licence not to read. Triggers must
  be written inclusively, and the `CHECK BY HAND` section exists for dependents whose
  trigger names a different clause.
- **This does not fix the broken links in `history/`**, which are exempt on purpose.
- **No dependency, no network, no read or write outside the repository.**

## Rejected by measurement

| Rejected | Killed by |
|---|---|
| Reciprocal metadata in both files (v1) | Three leaf contracts at exactly 60/60 lines; one folder writing into another's files; conflict-hostile generated blocks; a digest loop with no fixed point |
| Content digest pins on edges (v1) | ~200 merge-blocking findings/day modelled on real history; the worst target must change every session by contract; re-pinning is indistinguishable from reviewing. Replaced by clause-scoped review debt |
| Mining git co-change **instead of** declaring edges | Mining cannot type an edge, scope it to a clause, or say why. Kept and promoted to layer 0 as a *complement*: an earlier review rejected it on a 7.4% precision figure that was measured against a mention-based reference set, and mention and co-change are 96% disjoint here, so that figure was precision against the wrong yardstick |
| A lexical "undeclared link" completeness signal | Measured 78-85% of real co-change pairs are mentioned nowhere; the block would have been mostly wrong |
| SQLite as the stored artifact | Optional CPython module; not byte-reproducible under insert-order changes even after vacuum |
| Interned node ids in the committed artifact | One inserted node renumbers all later ids — a whole-file diff |
| Committed JSON as the primary artifact | 3.5× the tokens of the text projection for identical information |
| A JS graph library in the viewer | 435-644 KB vendored into a no-dependency repository, for a view the evidence says is the least useful one |
| Force-directed graph as the first view | Matrices beat node-link above ~20 vertices on most tasks; this graph is ~250 nodes |
| Incremental artifact generation | Full rebuild is 28 ms here; change detection alone is ~60% of a rebuild at 2,000 files |
| The gate living in the test suite | 205 s versus 5 s for identical blocking power |
| `file-relative` as the default path type | 451 repo-root references versus 4 relative links; requires rename detection that misses 15% of real moves |
| Section named `## Links` | Already used by 27 files under a different free-form schema |
| YAML frontmatter | A decided, unexpired repository decision; no stdlib YAML parser; invisible on rendered GitHub |
| Link rot as the justification | Zero broken links in scope; 121 of 123 are in deliberately exempt directories |
| Declaring duplication | Requires the knowledge whose absence causes duplication; needs lexical detection instead |
| Enforcing graph completeness | Undecidable, and a false completeness claim makes agents skip files |

## Research anchors

- **Forward-only authoring is settled elsewhere.** Backstage derives typed relations from
  one authored side and states descriptor files "are not supposed to contain" the derived
  field. RFC 8288 deprecates the reverse-link form. PROV-O defines only two inverses out of
  dozens of properties, because defining both forces every consumer to handle two
  equivalent forms. OSLC's link guidance gives the positive rule this design uses: store
  the link "in the resource that is developed later", so the finished end never needs
  editing.
- **Declare the inverse name once, in the schema.** StrictDoc's grammar carries a reverse
  role per relation type while items specify only the canonical role; Sphinx-Needs
  auto-creates a computed back-field per link type; PROV-O reserves inverse names without
  defining the properties.
- **Someone built the rejected version.** `adr-tools` writes both ends atomically and has
  no checker — nothing ever re-verifies the pair. And the canonical tool that materialises
  backlink sections into markdown documents its own behaviour as "any text you might add to
  this section will be clobbered."
- **Names from Dublin Core**, whose inverse pairings exist only in prose descriptions with
  no formal assertions in the machine-readable vocabulary.
- **Relationships belong outside the documents they relate.** DITA hoists them into a
  relationship table because topics that hardcode context-specific links cannot be reused;
  XLink formalises the out-of-line collection as a linkbase.
- **The nearest peer leaves typed links unsolved.** Google Cloud's Open Knowledge Format —
  agent-maintained markdown with metadata — states a link's kind "is conveyed by the
  surrounding prose, not by the link itself", with a typed-link proposal open and
  unaccepted. It does ship an absolute `stale_after` date as a freshness mechanism, the
  same shape as this repository's existing memory review dates, and a plausible fallback if
  clause-scoped debt proves too noisy.
- **Frameworks that built reference validation died or walked it back.** The one library
  with real build-time validation is unmaintained and checked file existence only; the
  most-cited framework removed its build-time guarantee in a major version and closed the
  regression as not planned. The constraint that follows: **keep the checker small enough
  to stay alive.**
- **Wikilink syntax is not an option** — specified nowhere, supported by GitHub only inside
  wikis, with implementations disagreeing on the alias divider.
- **Co-change mining is established work, and documentation is its strongest case, not its
  weakest.** The original recommender reports a documentation rule between four PostgreSQL
  SGML files at support 11 and **confidence 1.0**, explicitly noting coupling "between items
  that are not even programs", caused by duplicated options and examples — which is exactly
  this repository's thirteen-file restatement cluster. Independent studies find declared or
  static structure captures well under half of real change propagation (recall ~0.42 for
  static structure against ~0.87 for historical co-change in one five-system study), that
  the large majority of co-change pairs have no structural counterpart, and that the two
  signals are complementary rather than competing. The documented dominant noise source is
  tangled commits, which is why the commit-size cap exists.
- **The three-way join has a name and a thirty-year literature**: reflexion models, whose
  primitives are convergence, divergence, and absence. Its documented weakness is directly
  relevant — one in-vivo study found that detecting inconsistencies "was insufficient to
  prompt their removal", which is why this design pairs the report with a ledger and repair
  items rather than assuming a list causes action.
- **A shipping commercial product already uses this exact shape**: users declare
  architectural components, the tool mines change coupling between them, and the guidance is
  to compare the mined result against declared intent because deviations may indicate real
  problems.
- **Governance thresholds come from large-scale static-analysis practice**, including the
  definition of an effective false positive as a report the user chose not to act on, a
  target below 10%, and probation at 10% with removal above 25%.
- **There is essentially no measured evidence that graphs help LLM agents navigate**, and
  what exists leans the other way: graph-based retrieval ties agentic search at file
  granularity, the vendor successor to the best-known document graph system claims
  comparable quality at a fraction of the indexing cost, and this repository's in-scope
  corpus is only about 90k tokens. The honest argument for this feature is not retrieval
  quality — it is that a small, deterministic, evidence-annotated impact list is a cheap and
  verifiable context payload.
- **A whole-corpus dump is the wrong agent interface.** The closest analogue ranks and
  truncates to a token budget rather than serialising a graph, and the emerging
  machine-readable docs convention is a curated index of links with one-line notes,
  explicitly because context windows cannot hold the corpus.

## Staged plan — each stage validates before the next

The owner's instruction is to verify the idea before investing. The stages are ordered so
the zero-annotation half proves or kills the expensive half.

**Stage 0 — mine, and let it decide whether a schema is warranted.** One reconciler check,
about 120 stdlib lines, no schema, no migration, nothing activated: co-change coupling with
support and confidence floors, commit-size cap, ritual-file stop-list, and shared commit
subjects as evidence. Plus heading-anchor validation inside the existing link check, which
catches real bugs — including the broken anchor an earlier revision of this design's own
summary shipped. Then one written experiment: for the top-ranked couplings of two hot files,
record whether each is a real dependency, and whether a hand-authored edge would have said
anything the mined pair plus its commit subjects did not. **If the mined list is already
sufficient, stop here** — the schema is unjustified and the advisory is the whole feature.

**Stage 1 — the ledger.** Accepted/rejected, append-only, with the rejection rate reported
as the effective-false-positive rate. Nothing further is worth building until a dismissal is
durable, because otherwise every run re-proposes what was already declined.

**Stage 2 — the schema, capped.** Vocabulary, parser, tests, and `handbook/` activated alone,
with a hard ceiling of 30 edges and a mandatory clause anchor. Edges are authored *from the
mined candidate list*, not from memory.

**Stage 3 — the artifact.** Generation, byte-exact check, determinism tests including the
foreign-environment run.

**Stage 4 — the join.** `impact` with the full output contract, the confirmed/undeclared/
suspect report, clause-scoped review debt, and repair-item filing. This is where the design
earns its keep or does not.

**Stage 5 — the advisory**, once finding severity tiers exist.

**Stage 6 — further directories**, one per change. Expect the first cross-directory heading
rename to block a commit in an unrelated folder; that is the feature working, and it will be
annoying once.

**Stage 7 — the viewer**, deferred: table, neighbourhood panel, and directory matrix, in that
order. Not a force-directed graph.

Reality is verified at every stage by real recorded command output, never by assertion.

### One caveat that applies to every mined number here

This repository has **four days and 107 in-scope markdown-touching commits**. The published
work in this area discards the first few hundred change records as warm-up, so every
precision and confidence figure above will move as history grows, and the direction is
unknown. Mining is also indifferent to quality: it learns established bad practice as
readily as good, and a coupling it reports may be a duplication to remove rather than a
dependency to declare. The stop-list and the ledger exist because of both facts.
