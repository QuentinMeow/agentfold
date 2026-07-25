# Markdown edge graph — direction and decisions (v3)

**Status:** awaiting your answers on eight decisions
**Full design (you do not need to read it):** `docs/designs/markdown-edge-graph.md`

Self-contained. What we're building, the best practices I'd adopt and why they beat the
alternatives, one conclusion I got wrong and reversed, and the decisions left. Nothing
implemented.

---

## 1. The architecture, and what changed since v2

Your redirect is adopted wholesale: one-directional edges in the files, both directions in a
CLI-generated graph, recommended actions on change, gates at commit/push/merge, and explicit
tolerance for agents forgetting because a retry loop converges. One rule now covers all seven
relations — **the file that would become wrong declares the edge**.

**What's new in v3: a mined layer that ships before the schema.** I had "mine git history for
files that change together" measured, rejected it, then re-measured and reversed. Details in
§4, because the reversal changes your most important decision.

Four layers:

| Layer | What | Annotation cost |
|---|---|---|
| **0. Mined** | co-change coupling from git history, with support/confidence floors | **zero** |
| **1. Declared** | `## Edges` sections — the *residue* mining can't express | per edge |
| **2. Derived** | one committed text projection holding both directions | zero |
| **3. Consumers** | queries, a structural blocking gate, and a repair loop | zero |

## 2. What a file looks like

```markdown
## Edges

- **depends-on** `handbook/git-workflow.md#conflict-avoidance-by-construction-not-by-care` (repo-path)
  **Because:** this checker assumes concurrent agents never edit files another task owns.
  **Update-when:** that section changes which lane may write contracts, or drops the
  one-item-one-file rule.
```

A file with nothing to declare writes `## Edges` then `None.` — one line. Forcing a
*decision* rather than a *sentence* is deliberate; requiring a justification for "no edges"
would manufacture 17 vacuous sentences in `handbook/` alone.

**Seven relations, forward only.** You never write the reverse; the CLI knows the label.

| You write | CLI shows the other end as | In "must review"? |
|---|---|---|
| `depends-on` | required by | yes |
| `enforced-by` | enforces | yes |
| `restates` | restated by | yes |
| `supersedes` / `decided-by` / `generated-from` | superseded by / decides / generates | informational |
| `references` | referenced by | **never** — graph only |

## 3. Six best practices I'd adopt, and why each beats the alternative

**1. Mine git co-change first; declare only the residue.** *Better because* it answers "what
else must I review" on day one at zero annotation cost, for every file, and cannot go stale.
It also inverts the migration: instead of recalling 40–60 dependencies from memory, an agent
reviews a ranked, evidence-backed list — and mining proposes about the same number of
candidates. The commit subjects two files share ("enforce first-class queue actions") are
already-written rationale that nobody has to maintain.

**2. Derive the reverse direction; never author it.** *Better because* the alternative is
measured unsatisfiable here — three leaf contracts sit at exactly 60/60 permitted lines, so
writing backlinks in produces a budget failure fixable only by deleting contract prose.
Backstage forbids it, RFC 8288 deprecated it, PROV-O defines only 2 inverses out of dozens.
The one tool that writes both ends has no checker.

**3. A line-oriented text projection as the artifact, not JSON or SQLite.** *Measured:* at
250 nodes/400 edges the text form is **56 KB / ~16k tokens** against pretty JSON's **198 KB /
~57k** for identical information. **SQLite is disqualified on two grounds:** Python documents
`sqlite3` as an *optional* module ("if it is missing from your copy of CPython, look for
documentation from your distributor"), and it isn't byte-reproducible — same rows in a
different insert order produced different bytes even after a full vacuum.

**4. Keep prose out of the whole-graph file; serve it per query.** *Measured:* adding
`Because`/`Update-when` to every edge takes the artifact 56 KB → 132 KB. A single node's
neighbourhood is ~180–260 tokens, which is the unit to serve.

**5. Clause-scoped freshness derived from git, not stored hashes.** *Better because* the
stored-hash version modelled at ~200 merge-blocking findings/day, with the worst target being
`roadmap/current-state.md`, which your contract requires to change every session. Clause
scoping fixes it at the root: intersect the target's heading line-ranges with git's changed
lines, and raise debt only for dependents of the section that actually changed.

**6. Table and matrix before a graph, for the future viewer.** *Controlled evidence:*
adjacency matrices beat node-link diagrams on most tasks **above ~20 vertices**; this graph is
~250. Users of the closest comparable tool report the global graph view becoming useless as
the corpus grows. And it needs **no JS library** — precompute layout in Python, emit static
markup, avoid vendoring 435–644 KB of minified JavaScript into a no-dependency repo.

## 4. The conclusion I got wrong, and reversed

**Last message I told you git co-change mining measured 7.4% precision and was rejected. That
was wrong, and the error was in the yardstick, not the technique.**

That measurement scored co-change against a reference set of *files that textually cite the
target*. I then measured the two signals against each other, symmetrically:

| Measured, identical scope both sides | `templates/` in | out |
|---|---|---|
| mention-derived edges | 184 | 154 |
| co-change-derived edges | 84 | 40 |
| overlap | **13** | **9** |
| Jaccard | **0.051** | **0.049** |
| co-change pairs mentioned nowhere in prose | **85%** | **78%** |

The two sets are ~95% disjoint. Scoring co-change against a mention-based reference set was
guaranteed to return near-zero *whether or not mining works*.

**The decisive single case**, verified by hand: `templates/queue/review.md` restates in its
opening lines the exact `blocking-` / `future-blocking-` / `non-blocking-` prefix semantics
that `message-queue/AGENTS.md` owns — and **never names that file, zero occurrences.** It
co-changes with it at confidence 0.81 over 13 commits. A real, load-bearing dependency that
no link checker, no grep, and no graph built from declared links can see. Git has it for free.

And mining reproduces this design's own motivating claim: for `handbook/git-workflow.md`, 8
partners at support ≥3 — `automation/AGENTS.md` (0.88), `handbook/human-action-guide.md`
(0.81), four queue templates, `message-queue/AGENTS.md` — which is the dependency set the
design was written to make visible.

**Two things this does not mean.** Mining cannot type an edge, scope it to a clause, or say
why — every semantic distinction in the vocabulary is invisible to it. And it learns
established bad practice as readily as good: a reported coupling may be duplication to
*remove* rather than a dependency to *declare*. So mining is the complement, not the
replacement. The honest caveat: this repo has **4 days and 107 in-scope commits**, and the
literature discards the first few hundred change records as warm-up, so every number here
will move.

**One consequence worth flagging:** v2 specified an `UNDECLARED` block listing inline links
with no declared edge. At 78–85% disjointness that block would have been mostly wrong.
Co-change replaces it as the completeness signal.

## 5. Honest cost

Migration set is **43 durable files**, not 250 — 108 of 153 in-scope files are `tasks/` and
`message-queue/` ephemera whose relationships an existing check already enforces. Expect
**40–60 edges, ~150 lines**, now authored *from a ranked list* rather than from memory. The
mined check is ~120 lines and runs in 0.23 s; a full markdown pass is 28 ms.

Advisory load, measured by walking history forward: at confidence ≥0.9 it fires on **3% of
commits**; at ≥0.8, **17% of commits with ~2 suggestions each**. (The 3% figure independently
reproduces the published rate of the original co-change recommender at the same threshold.)

**The one cost I can't design away:** `Update-when` requires predicting what a future agent
will change in a file you don't own, for a payoff someone else collects. Expect some triggers
to be technically true and practically useless.

---

## 6. Decisions — your call

Your earlier answers stand (repo-root default, derive-not-author, both prose fields,
`enforced-by` may target code, reconciler-not-tests, duplication detector as its own task).
N4 reverses your earlier D4.

### ☐ N1. Ship the mined layer first, and let it decide whether the schema is warranted?

Per §4. One reconciler check, ~120 lines, no schema, no migration, nothing activated — plus
heading-anchor validation. Then a written experiment: for two hot files, record whether each
top-ranked coupling is real, and whether a hand-authored edge would say anything the mined
pair plus its shared commit subjects did not.

- **Recommended:** yes. If the mined list is already sufficient, stop there and the advisory
  is the whole feature. This is the cheapest possible test of the idea, and it now tests the
  *right* thing — v2's version of this decision tested a mention-based index that I've since
  measured to be the wrong signal.
- **Or:** build the schema directly.

### ☐ N2. Adopt the three-way join as the product?

`confirmed` (declared and co-changed) / `undeclared` (co-changed, nothing declared — the
queue of edges worth authoring) / `suspect` (declared, never co-changed — stale or
aspirational). This is the reflexion model, a thirty-year-old primitive, not an invention.

- **Recommended:** yes — the delta between declared intent and mined reality is more
  informative than either alone, and it's what a shipping commercial product does.
- **Or:** report the two separately and let the reader join them.

### ☐ N3. The accepted/rejected ledger — in or out?

An append-only record of each mined candidate as accepted (edge declared) or rejected (with a
one-line reason), so a dismissal is durable and never re-surfaces.

- **Recommended:** in, and treated as non-optional. Every comparable system that shipped a
  divergence report also shipped a way to freeze the existing set, because otherwise the
  first run's list is unusable. It's also the concrete answer to your fault-tolerance
  question: the ledger is what makes a decision survive the agent that made it. Bonus: the
  rejection rate *is* the false-positive rate, so the check measures its own usefulness.
- **Or:** out, and accept re-proposals every run.

### ☐ N4. Reinstate `references`? (reverses your earlier D4)

With one-way edges the reason I dropped it is gone — impact filters by relation, so it's
inert there, costs two lines, and populates the map you want to render.

- **Recommended:** reinstate as **graph-only** — never in "must review", `Update-when`
  forbidden.
- **Or:** keep it dropped.

### ☐ N5. Freshness: clause-scoped git debt?

- **Recommended:** clause-scoped review debt (§3.5) — derived each run, closes automatically
  when the dependent is next edited.
- **Or:** an absolute re-review date per edge, the mechanism this repo already runs on memory
  entries. Can't detect a target changing, but can't thrash.
- **Or:** nothing mechanical; `Update-when` stays advisory prose.

### ☐ N6. Commit the generated graph file, or generate on demand?

The reviews disagreed, so this is genuinely yours.

- **Recommended: commit it** (one text projection). A bare clone answers "what depends on
  this" with no command run; GitHub renders it, which is the only way in-edges reach a human
  reviewer. Lockfiles, Rails' schema file, and Terraform's lock all do this, resolving
  conflicts by regeneration. Marked generated so GitHub collapses the diff.
- **Or: generate on demand** (git-ignored). No conflicts; costs a command, and a stale
  ignored copy can silently answer for a different commit.
- *A conflict-deadlock concern was raised and resolved:* the writer refuses only when a file
  it **reads** differs between index and worktree, not the file it writes.

### ☐ N7. Cap edges per file, or chase coverage?

Prose degrades to formula — all twelve mandatory `Core fit` justifications in this repo read
`pass — <one clause>`, zero say `fail`, none is falsifiable. **Fluent filler defeats every
deterministic check.** The only real defence is volume low enough that a human reads each one.

- **Recommended:** cap at ~7 edges per file, 30 for the first directory. Accept a permanently
  incomplete graph that says so in every answer.
- **Or:** chase coverage, and accept that some of the prose is decoration.

### ☐ N8. Retry closure and the third gate state?

- Review debt closes **automatically** when the dependent is next edited, or **explicitly**
  when an agent records "checked, nothing needed."
- Blocking findings get a third state: **discharged by filing** — clears once a queue item
  names the finding, so an agent is never stranded by a finding whose fix belongs to another
  task. Without it the blocking tier becomes a hook-bypass factory.
- **Recommended:** both. **Or:** blockers must always be fixed in place.

---

## 7. If you answer nothing

Nothing happens; no code exists and no pre-existing file changed. The recommended answers are
what a follow-up session would proceed with, after the boundary named in the queue items
linked from your reply.

## 8. Errors I found and corrected, for the record

- **Rejecting co-change mining on a 7.4% precision figure.** Measured against the wrong
  reference set; reversed in §4. This is the one that would have cost you the most.
- **An asymmetric overlap measurement** that excluded `templates/` from one side only,
  overstating disjointness as 0.041/86% rather than the symmetric 0.049–0.051/78–85%.
- **A broken anchor** in the v1 summary (`#conflict-avoidance`; the real slug is
  `conflict-avoidance-by-construction-not-by-care`) — a good argument for anchor checking.
- **A false claim** that the indent rule made documentation examples inert "without relying on
  fence detection." My examples sit at indent 0–2 and are inert only *because* they're fenced.
