# Level-Triggered Resolution (LTR)

A design for AgentFold queue resolution. Philosophy: **replace every edge question with a
state question.** Nothing in the resolution gate is ever allowed to ask "did X change in
*this* commit"; it may only ask "is P true of *this tree*".

Status: proposal. Target: `automation/reconcile/reconcile.py`, `templates/queue/*`,
`message-queue/AGENTS.md`.

---

## 0. The claim in three sentences

An item declares its own completion condition as a closed-grammar, machine-checkable
predicate over repository state (`**Done when:**`). At deletion the reconciler evaluates
that predicate against the deletion candidate's own tree and its reachable history —
never against the deletion *edge* — so the answer is a frozen fact about an immutable
snapshot and does not depend on when, in what order, or by whom the work landed. Time and
ordering become irrelevant by construction: the B1/B2 deadlock cannot be expressed,
because no question is asked about a specific edge.

This is not a departure from the existing architecture. `generated_retry_clear`
(`reconcile.py:2851`) already does exactly this — it re-runs a named checker inside
`git_revision_candidate(revision)` and admits deletion when the finding is gone. E4
(`approved_review_merge_receipt_problem`:3269) and E5 (`task_transition_receipt_problem`:3163)
already prove resolution from history that predates the deletion commit, and both
deliberately bypass `resolution_evidence_problem`. LTR generalizes the one genuinely
level-triggered escape into the primary mechanism and lets the other four be deleted.

---

## 1. What changes in code

| Function | Change |
|---|---|
| `resolution_evidence_problem` (:2722) | **Replaced** by `predicate_problem(text, path, revision)`. The `prior_revision` parameter disappears from its signature — that removal *is* the design. |
| `queue_deletion_problem` (:3577) | Calls `predicate_problem` instead of `resolution_evidence_problem` on all four call sites. `claimed_lifecycle_problem` is left untouched. |
| `generated_retry_clear` (:2851) | Becomes the implementation of the `clear:` clause; the special case in `queue_deletion_problem` collapses into the general path. |
| `pickup_completed` (:1892) | Becomes the implementation of the `task:` clause plus one pickup-specific reciprocity assertion; the E2 special case shrinks. |
| `check_queue_schema` (:3826) | Gains filing-time predicate validation (grammar, charset, referent existence). This is where most of D1/D2/D4 dies. |
| `claim_identity` (:1955), `immutable_action_text` (:1987) | `Done when` joins the frozen key set **only when well-formed**; `Waiver` is fully mutable lifecycle state. |
| `schema_activation_commits` (:1242) | Unchanged — it already takes `version=` as a parameter, so `v2` costs zero new machinery. |
| New | `PredicateCache`: two git-backed indexes, described in §4. |

No new dependency. No daemon. `subprocess` + `git` + stdlib, as today.

---

## 2. The predicate language

### 2.1 Design rules for the grammar

1. **Closed.** A finite set of clause forms, each with a fixed arity. No free text
   anywhere in the value.
2. **Normalization-invariant.** Every token is drawn from a character class that
   `automation/markdown_semantics.py:semantic_text` passes through unchanged: no
   backticks, no `<`, no `&`, no HTML, no comment delimiters. This is a direct D22
   countermeasure and is asserted by a test (`semantic_text(line) == line` over the
   full legal alphabet). *The predicate field can never be the cause of a D22-class
   unsatisfiable gate, because there is no legal predicate whose bytes two readers
   normalize differently.*
3. **No code.** §3.
4. **Conjunction only.** No disjunction (an item would resolve on its easiest branch),
   no negation beyond the explicit `absent:` form (negating `clear:` would reward
   *breaking* an invariant). Maximum three clauses — bounds cost and keeps the line
   projectable into a handover entry.
5. **Evaluable from one tree plus bounded reachable history.** Nothing may depend on the
   working directory, the environment, the clock, or the network.

### 2.2 Grammar

```
Done when   := clause (" and " clause){0,2}
clause      := exists | absent | contains | task | landed | clear | superseded | waived

exists      := "exists:" path
absent      := "absent:" path
contains    := "contains:" path "#" slug
task        := "task:" task-id " in " status
landed      := "landed:" (path | "git:" oid)
clear       := "clear:" check-id " " path
superseded  := "superseded:" queue-path
waived      := "waived:" date

path        := [A-Za-z0-9._-]+ ("/" [A-Za-z0-9._-]+)*       ; no "..", no leading "/"
slug        := [a-z0-9][a-z0-9-]*                            ; a GitHub heading anchor
task-id     := \d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*
status      := "0_backlog"|"1_in-progress"|"2_blocked"|"3_in-review"|"4_done"
check-id    := [a-z0-9][a-z0-9-]*                            ; must be a key of CHECKS
oid         := [0-9a-f]{40}|[0-9a-f]{64}
date        := \d{4}-\d{2}-\d{2}
queue-path  := message-queue/(needs-human|needs-agent)/<leaf>/<prefix>-<slug>.md
```

Every terminal is already a vocabulary this repo constrains elsewhere
(`TASK_ID_RE`, `TASK_STATUSES`, `CHECKS`, `FULL_GIT_OID_RE`, `anchor_slugs`). The grammar
introduces no new naming concept.

### 2.3 The admitted forms, evaluated

`C` = the deletion candidate. For a staged pre-commit run `C` is the index; for a range
run it is the committed revision. `T(C)` = the tracked-path/blob snapshot of `C`, which
the reconciler already loads once per candidate (`_GIT_INDEX_ALL_PATHS_CACHE`,
`git_revision_candidate`).

| Clause | How the checker evaluates it | Cost | Moved by a no-op edit? |
|---|---|---|---|
| `exists:P` | `P in T(C)` and its mode is `100644`/`100755`. | 0 spawns, O(1) | **Yes** — `touch P`. Weakest form. |
| `absent:P` | `P not in T(C)`. | 0 spawns, O(1) | No — requires a deletion, which is loud in every diff and usually gated by another check. |
| `contains:P#S` | Read `P`'s blob through the existing persistent `git cat-file --batch`; `S in anchor_slugs(markdown_headings(semantic_text(blob)))`. Reuses `reconcile.py:7091-7113` verbatim. | 0 spawns, ~1 ms | No — a whitespace edit adds no heading. You must author a named section. |
| `task:I in S` | Exactly one `tasks/*/I/task.md` in `T(C)`, and it is under `S`. Reuses `task_incarnations_in_tree`. | 0 spawns, O(1) | No — the move trips `task-structure`/`task-admission`, which independently require the status folder's artifacts. |
| `landed:P` | A commit reachable from `C` that touches `P` and postdates the item's own creation commit (derived, not declared — `staged_side_creation_commit`:2386 already computes this shape). Also requires `P in T(C)`. | 0 amortized (§4) | **Yes** — the deletion commit may touch `P` itself. Legacy/amnesty form only. |
| `landed:git:O` | `git merge-base --is-ancestor O C`, through the existing `_GIT_ANCESTRY_CACHE`. | ~10 ms, cached | **No, and not by any edit at all.** You must actually merge `O`. Content-addressed; this is the briefing's "bind evidence to a SHA" arriving inside the grammar. |
| `clear:K P` | `with git_revision_candidate(C): not any(f.check == K and str(f.subject) == P for f in CHECKS[K]())`. Literally `generated_retry_clear` with the identity supplied by the clause instead of by `Check:`/`Subject:`. | 1 spawn (tree capture) + the named check's own runtime; memoized on `(K, C)` | **No.** No cosmetic edit makes a named invariant hold. Strongest form. |
| `superseded:Q` | `Q in T(C)`, `Q` is a live queue item of the same actor folder and same timing prefix, and `Q`'s `Supersedes:` names this item. | 0 spawns, O(1) | n/a — a repair form, §6. |
| `waived:D` | `TODAY <= D` **and** a `**Waiver:**` line is present and well-formed. | 0 spawns | n/a — the escape hatch, §6. |

### 2.4 Anti-gaming ranking, and the composition rule

Ordered by how much real work satisfying the clause requires:

```
clear:  >  task:  >  landed:git:  >  contains:  >  absent:  >  landed:path  >  exists:
```

The briefing's central finding — that today's check is cleared by appending `\n# probe\n`
to the declared file — kills only the two right-hand forms. Everything from `contains:`
leftward requires an act that is close to the work itself.

**Composition rule, recommended in the template:** the canonical strong predicate for
"produce a durable record" is

```
**Done when:** exists:memory/decisions/2026-08-01-foo.md and clear:memory-schema memory/decisions/2026-08-01-foo.md
```

`touch` satisfies the first clause and fails the second. Cost: 0 extra spawns
(`memory-schema` measured at 0.04 s). This composition is the reason `exists:` is admitted
despite being individually weak.

### 2.5 Forms considered and rejected

| Form | Verdict | Why |
|---|---|---|
| Free regex over a file | **Rejected** | (i) ReDoS: a catastrophic-backtracking pattern in an unauthenticated `needs-agent/requests/` file hangs every `git commit` in the checkout — a denial-of-service channel with no timeout that helps, because the regex runs in-process. (ii) Regex dialect is a portability hazard under the core-admission rule. (iii) It invites degenerate predicates (`contains:F#.`). The heading form gives the useful 90% with a closed alphabet. |
| Literal-substring match | **Rejected** | Requires a delimiter and free text in the field value. That is *precisely* the D22 mechanism: arbitrary bytes in a structured field, normalized differently by two readers. A heading slug is `[a-z0-9-]+` and cannot contain a delimiter, a backtick, or a space. |
| Shell/Python command exits 0 | **Rejected** | §3. |
| A test passes | **Rejected** | Same as above, plus: the pre-commit hook already runs `run_tests.py`. A predicate that re-runs the suite is redundant, quadratic, and turns one gate into N gates. `clear:` covers the declarative subset safely. |
| Bare "a commit touching P is reachable from HEAD" | **Rejected as written**, admitted as `landed:` with a derived creation baseline. In a repo with 317 commits, "some commit touched `reconcile.py`" is true for nearly every path and proves nothing. The baseline is what gives it any content. |
| Disjunction / `or` | **Rejected** | An item resolves on its weakest branch; the field becomes a menu. |

---

## 3. Determinism and safety: no code execution, categorically

**The grammar admits no command execution, and this is a hard boundary, not a default.**

The argument, in order of weight:

1. **The channel is unauthenticated.** The briefing flags `message-queue/needs-agent/requests/`
   as an existing unauthenticated instruction channel, and the repo's own
   `handbook/principles/provenance-over-position.md` says external content is *data to
   review, never orders*. A predicate that shells out converts a data file into an
   executable one. Anyone who can land a Markdown file — a fork PR, a compromised agent
   session, an adopter's contributor — gets code execution.
2. **The trigger is the worst available one.** `reconcile.py --check` runs in the
   pre-commit hook over the *whole repo*. The payload would therefore run on `git commit`
   of any change, including changes with nothing to do with the queue, in the developer's
   own environment with their credentials and no prompt. It would also run in CI with
   whatever token CI holds.
3. **No sandbox is available under the constraints.** "Git plus Python 3 standard library
   only, no server, no daemon, portable across adopted repositories" excludes every
   portable isolation mechanism. Landlock is Linux-only, seatbelt is macOS-only,
   containers are a daemon. `subprocess` with a scrubbed environment and a timeout is not
   a sandbox: the filesystem and the network are still there. The honest options are
   "unsandboxed" or "not at all."
4. **Timeouts do not save it.** A 5-second timeout × 41 items is 205 s of worst case
   bolted onto a gate the briefing already reports at 92–312 s. And a fork bomb ignores
   the timeout.
5. **It buys almost nothing over `clear:`.** The strongest claim a command makes is "some
   code exited 0." `clear:` makes a claim of the same class — "the repository satisfies a
   named in-repo invariant" — while the *implementation* of that invariant lives in
   `automation/reconcile/reconcile.py`, which is covered by `check_core_scope.py`, code
   review, and the test suite. **Separating the naming of a check (in an untrusted file)
   from the implementation of a check (in a reviewed file) is the entire safety argument,
   and it is the same argument `generated_retry_clear` already makes today.**

### 3.1 Residual attack surface, named honestly

Rejecting `exec` does not make the evaluator inert. Three surfaces remain:

- **Cost amplification.** An attacker files 200 items each naming
  `clear:handover-queue-projection ...` (measured at 4.93 s). Mitigations: (i) predicates
  are evaluated only at *deletion* edges, and filing items creates no deletion edges;
  (ii) **at most one `clear:` clause per item**, enforced at filing time; (iii) a memo
  keyed `(check-id, candidate)` so N items naming the same check at the same candidate
  cost one run; (iv) a per-invocation wall-clock budget for predicate evaluation, on
  exhaustion of which every remaining predicate **fails closed** with a distinguishable
  "predicate budget exhausted" message. A DoS therefore yields a blocked commit, never a
  laundered deletion.
- **Re-entrancy.** `clear:queue-resolution` is rejected outright (the existing code
  already refuses this exact case). Generalized: a `clear:` clause may not name a check
  currently on the evaluation stack; a cycle fails closed.
- **Path traversal / symlink games.** Structurally impossible: `..`, leading `/`, and
  non-`[A-Za-z0-9._/-]` bytes are rejected by the grammar, and every read goes through
  the *tracked-path tree snapshot* (mode must be `100644`/`100755`), never through the
  filesystem. You cannot "exist" unless git tracks you. This follows the established
  `readable_queue_item` pattern.

---

## 4. Fail-closed semantics

The single most important structural point: **a predicate is examined at two different
times, and the two fail in opposite directions.** That asymmetry is what fixes D1/D2/D4.

### 4.1 Filing time — `check_queue_schema`, over every live item, on every commit

A malformed predicate is a **finding on the live item**, which blocks the commit that
*introduces* it. A bad predicate therefore never becomes live, and is corrected while the
field is still free to edit.

Validated at filing time, with 0 git spawns:

| Rule | Catches |
|---|---|
| Grammar and charset | typos, delimiters, code spans, HTML |
| No path under `message-queue/` | preserves "evidence must be outside the queue" (D2) |
| No `..`, no leading `/` | traversal |
| No clause naming the item's own `Review target` | preserves "review target must differ from evidence" |
| `task:` referent must exist somewhere under `tasks/` | the D5 class: a declared dependency that never existed |
| `clear:` check-id must be a key of `CHECKS`, must be on `DETERMINISTIC_CHECKS`, must not be `queue-resolution` | dead references, clock dependence, recursion |
| `landed:P`, `absent:P`, `contains:P#S` referent path must exist **now** | you cannot "land a change to" or "remove" something that does not exist |
| `exists:P` — parent directory must exist and be a governed zone | `memry/decisions/...` typos |
| At most one `clear:` clause; at most three clauses | cost |
| Exactly one `Done when:` field (`field_counts` already enforces this shape) | ambiguity |

### 4.2 Deletion time — `check_queue_resolution`

| Situation | Behavior |
|---|---|
| Predicate TRUE at `C` | deletion admitted (subject to `claimed_lifecycle_problem`, unchanged) |
| Predicate FALSE at `C` | deletion refused, message names the failing clause |
| Predicate **unparseable** | treated as **ABSENT**, falls back to the legacy path — see §6.3, this is a deliberate anti-brick decision, not leniency |
| Input unavailable — shallow clone, missing object, git error | **refused**, with a distinguishable message naming the missing capability ("`landed:` needs history this clone does not have; `git fetch --unshallow`"), so the operator knows the fix is not a content change |
| Named check raises | **refused**; the exception is reported as a distinct `queue-resolution` finding, not swallowed |
| Predicate budget exhausted | **refused** |
| Was TRUE, is now FALSE | **cannot happen for the deleted item.** Predicates are evaluated at the deletion candidate's own snapshot, which is immutable. A later revert of the evidence does not retroactively redden the old deletion. |

### 4.3 The one non-determinism, disclosed

`clear:` is the only clause whose truth depends on code *outside* the evaluated tree: it
runs today's checker against yesterday's snapshot. If someone tightens `memory-schema`
next month, an old deletion that was valid becomes invalid under `--range root:HEAD`
replay.

Three things must be said:

1. **This flaw already exists**, verbatim, in `generated_retry_clear`. LTR widens an
   existing exposure; it does not create a new class.
2. It is **observable on main today**, by a different mechanism: my `--range root:HEAD`
   run produced exactly one finding —
   `message-queue/needs-human/clarifications/workspace-platform-priority.md: deleted
   unresolved queue item: missing non-queue Resolution evidence` — an old, historically
   legitimate deletion now red because the rule that governs it postdates it. Full-history
   replay against current code is *already* retroactive.
3. Mitigations, in order: `DETERMINISTIC_CHECKS` excludes the three clock-dependent checks
   (`stale-queue`, `memory-expiry`, `roadmap-fresh`) so no predicate can flip with the
   calendar; the repo's existing stable-check-id rule
   (`memory/lessons/automation/deterministic-finding-keys.md`) constrains drift; and a
   documented rule that tightening a check requires a `--range root:HEAD` run before
   merge. If that is not enough, the escape hatch (§6.3) is the release valve.

**I do not claim `clear:` is replay-stable. It is not. Everything else in the grammar is.**

---

## 5. Cost

### 5.1 Measured baselines (this repo, 317 commits, 41 live items, Apple silicon, warm cache)

| Measurement | Value |
|---|---|
| Full `--check`, staged, clean tree | **8.57 s** |
| ...of which `queue-resolution` | **0.57 s** |
| ...of which `handover-queue-projection` | **4.93 s** (the actual slowest check today) |
| `queue-resolution` alone, `--range root:HEAD` | **58.7 s** |
| 41 × `git log -1 --format=%H HEAD -- <path>` | 1.21 s (29.5 ms each) |
| **One** `git log --format=%H --name-only HEAD` over all commits, all paths | **0.298 s** |
| `git rev-list HEAD` (317 commits) | 0.034 s |

The briefing's 92–312 s corresponds to the `--range root:HEAD` path on slower hardware;
58.7 s here is the same shape.

### 5.2 The structural point about `--check` cost

**The number of predicate evaluations equals the number of DELETION EDGES, not the number
of live items.** Forty-one live items contribute *zero* predicate evaluations to a run
that deletes nothing. Today's `resolution_evidence_problem` has the identical property.

Steady-state pre-commit, per run:

- Removed: 2 × `git_artifact_bytes_at` per evidence path per deletion edge.
- Added: one grammar parse per live item in `check_queue_schema` — pure Python, ~0.1 ms ×
  41 = **~4 ms**.
- Net: **indistinguishable from today (±5 ms).**

A normal resolving commit deletes 1–2 items:

| Predicate used | Added wall clock |
|---|---|
| `exists:` / `absent:` / `contains:` / `task:` / `superseded:` / `waived:` | **< 5 ms** |
| `landed:path` | **~0.33 s** (one index build, amortized across all items in the run) |
| `landed:git:` | **~10 ms** |
| `clear:K` | 0.03 s + K's runtime — **0.04 s for `memory-schema`, up to 4.93 s for `handover-queue-projection`** |

So the strongest predicate is genuinely slower, up to ~5 s, paid only by the commit that
deletes the item. The two other strong forms (`task:`, `contains:`) cost nothing. That
trade is stated plainly in the template so an author chooses knowingly.

### 5.3 Caching, and the `--range root:HEAD` path

The briefing's hard constraint is that `--range root:HEAD` must not get worse. Two-level
cache, both measured:

- **L1, once per invocation:** one `git log --format=%H --name-only <range-head>` builds
  `path → [commits touching it]` for the entire reachable history. **0.298 s, one spawn.**
  Replaces the naive 41 × `git log -- path` (1.21 s, 41 spawns) — a 4× improvement over
  the obvious implementation, and it scales with history size, not item count.
- **L2, per distinct deletion candidate, memoized:** `reachable(C) = set(git rev-list C)`
  at **0.034 s each**. This repo has 35 merges and a bounded number of deletion-bearing
  candidates; ≤ 41 distinct candidates ⇒ **≤ 1.4 s total.**
- `landed:P at C` is then `bool(L1[P] & L2[C] & after_creation(C))` — a set intersection,
  no spawn.

Expected root:HEAD delta: the per-edge two-sided blob comparison that
`resolution_evidence_problem` performs today is removed, and L1+L2 (≈ 1.7 s) is added
once. **I expect a net improvement, but I have not implemented it, so I claim only: the
added cost is bounded above by ~1.7 s on this corpus and grows with history length, not
quadratically.** For a 10 k-commit adopted repository, L1 is ~10 s and L2 is ~0.3 s per
candidate; at that scale L1 should be persisted to `.git/` as a derived cache keyed by the
head OID. That is the named crossover point.

Everything except `landed:` and `clear:` is **history-free** — pure tree lookups. An
adopter who bans those two clauses gets a resolution gate with **zero** history-walking
cost, which is strictly better than today's design can offer.

---

## 6. Schema and migration

### 6.1 Exact schema changes

**New field, all five templates in `templates/queue/`:**

```
**Done when:** <one predicate line; see message-queue/AGENTS.md>
```

Placed immediately after `**Resolution evidence:**` in `request.md`, `retry.md`,
`decision.md`, `clarification.md`, `review.md`. In `request.md` and `retry.md` it becomes
the machine-readable head of the existing `## Done when` prose section — the prose stays
and explains, the field decides. This is not a new concept for authors: every live request
already writes `## Done when`, and several already state a mechanically checkable
condition ("The manifest task is in `4_done`" → `task:2026-07-24-declare-layered-workspace-manifest in 4_done`).

**New optional field, escape hatch only:**

```
**Waiver:** <reason> — authorized by <needs-human/decisions/... path>
```

**Changed:** `**Resolution evidence:**` becomes *legacy-and-optional*. It is not deleted:
records are immutable, ~41 live items carry it, and history is full of it.

**Marker:** `**Queue resolution schema:** v2` in `message-queue/AGENTS.md`. The activation
machinery is already parameterized — `schema_activation_commits(head, path, field,
version="v1")` at `:1242` takes the version as an argument — so v2 is a one-line call
change plus the anti-downgrade rule the v1 marker already has.

### 6.2 Migration: nobody edits anything

Three rules, in priority order.

**Rule 1 — legacy reinterpretation (this is the whole migration).** Once v2 is active, for
an item that carries `Resolution evidence: P` and no `Done when:`, the gate is
**`landed:P`** instead of `resolution_evidence_problem`. The field's *meaning* ("this file
will change") is preserved exactly; only the *window* widens from one commit to "since the
item was filed."

No file is edited. All ~41 live items migrate for free. Verified against the live stuck
item:

```
message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
  created at b4c1ec5 (2026-07-25), Resolution evidence: automation/reconcile/reconcile.py
  6 commits touching that path are reachable from HEAD since b4c1ec5, including
  6d4e337 "fix: render code spans on both sides of the handover copy check" — the repair
  ⇒ landed: TRUE ⇒ resolvable.
```

**Rule 2 — additive tightening is free and monotone.** A well-formed `Done when:` may be
added to a live item that is still in its initial status (`open`/`waiting`/`awaiting-artifact`),
absent → present, once. When the item also carries `Resolution evidence`, the added
predicate is evaluated **in conjunction with** the legacy `landed:` clause, never instead
of it. Adding a predicate can therefore only ever *tighten*. Present → different is a
rewrite and requires §6.4.

**Rule 3 — new items must declare.** Once v2 is active, an item whose creation commit is a
descendant of the activation must carry a well-formed `Done when:` (`staged_side_creation_commit`
already derives creation). Pre-existing items are grandfathered permanently. This mirrors
`handover_action_entry_version_for` (:5735) exactly, which already grandfathers handovers
by creation-time grammar — the repo has this pattern and I reuse its shape rather than
inventing one.

**`landed:` is an amnesty, priced as an amnesty, closed to new entrants.** New items may
not use `landed:path` (they may use `landed:git:`, which is strong). This confines the
form's weakness to a grandfathered corpus that shrinks monotonically.

I must be blunt about that weakness. Of the 6 commits satisfying the live stuck item's
`landed:automation/reconcile/reconcile.py`, four are unrelated work (`perf: spawn fewer
Git processes`, `reconcile: report a backticked absolute path`). **For a hot path like
`reconcile.py`, `landed:` is close to vacuous.** It is not *weaker* than today's rule
against a determined actor — both are satisfied by touching the file — but it is weaker
against accident. That is the price of a zero-edit migration, and it is a price I am
choosing to pay for exactly one grandfathered generation.

### 6.3 Anti-brick rule: a malformed predicate is ABSENT, not a violation

Critical. If `Done when` were frozen identity text *and* a malformed value were a
violation, then the commit that fixes a malformed predicate would be blocked by the
malformed predicate. G1/G3, reproduced by my own design.

Therefore: **`Done when` participates in `claim_identity` / `immutable_action_text` only
when it parses.** A malformed value is uninterpretable text, and freezing noise is not an
invariant. So editing a malformed predicate into a well-formed one is a legal mutation, the
item falls back to the legacy path in the meantime, and the fix lands in the very next
commit.

Likewise **`Waiver` is fully mutable lifecycle state**, in `LIFECYCLE_MUTABLE_FIELDS`
alongside `Status`. If it were frozen, the escape hatch would itself be unreachable on a
live item.

Both of these had to be got right or the design would be a new way to brick the repo. I
believe I have found both; I do not claim there is no third.

---

## 7. Repair

Three distinct problems.

### 7.1 A wrong predicate

Prevention first: §4.1 catches grammar, charset, traversal, queue-pointing targets,
nonexistent parent directories, unknown task ids, unknown/banned/nondeterministic check
ids — **at the commit that files the item, while the field is still free.** That is the
D1/D2/D4 fix, and it is the difference between "the field is immutable so it can never be
corrected" and "the field cannot be wrong in those ways in the first place."

### 7.2 A semantically wrong or unsatisfiable predicate — the `superseded:` path

Tightening is free (§6.2 Rule 2). Loosening requires a successor, using the mechanism the
repo already has for changes-requested reviews:

- File a same-timing, same-actor successor naming this item in `Supersedes:`.
- The original becomes deletable by `superseded:<successor path>`.
- Guards: same timing prefix (no downgrade), same actor folder, original in a claimed
  status, successor carries a well-formed predicate.

**Cost: one coordination commit** (create successor + delete original together), against
the 2–4 the briefing measures for retire-and-refile. The correction is a normal, cheap,
*recorded* act rather than an impossibility.

### 7.3 Break-glass — the waiver, and why it beats `--no-verify`

The briefing is explicit: any solution that adds a check must ship its own escape path.
Mine is:

```
**Done when:** waived:2026-08-29
**Waiver:** the declared predicate is unsatisfiable because the reviewed task was
abandoned — authorized by message-queue/needs-human/decisions/blocking-waiver-nnn.md
```

Semantics and teeth:

- Evaluates TRUE while `TODAY <= expiry`. Expiry must be **≤ 30 days** from `Filed`;
  a malformed or over-long date is a *filing-time* finding, so a bad waiver never goes live.
- **A waiver may only be added by a commit that also creates the authorizing
  `needs-human/decisions/` item.** Using the escape hatch *files an ask to the human*, in
  the channel the human already reads, in the same commit. That is the visibility property.
- **Ratchet:** `message-queue/AGENTS.md` carries `**Waiver budget:** N`, which may only
  decrease. Any commit raising it is a finding. Outstanding waivers > N is a finding.
  Zero spawns.
- Expiry findings are filed under `stale-queue` (which already owns dates), scoped to the
  waived item.

**Why it out-competes `--no-verify`:** `--no-verify` requires remembering a flag; it
bypasses *everything* including tests and the core-scope gate; it leaves no record, so the
next session hits the same wall cold; and **CI still rejects the push**, so the work is
wasted. A waiver is one line in a file already open, keeps every other check running, is
visible in the diff, and passes CI. Additionally the pre-commit hook prints **the exact
waiver line to paste** when a predicate fails — which makes the sanctioned escape a
copy-paste and the unsanctioned one a lost push.

---

## 8. Interaction with the existing invariants

| Guarantee | Verdict | How |
|---|---|---|
| Deletion needs an act, not a label | **Strengthened** | `claimed_lifecycle_problem` kept verbatim. The *act* is now the predicate's subject: `clear:`, `task:`, `contains:` demand acts a label cannot fake. `Status: in-repair` + `rm` fails both gates. |
| Active-repair proof (committed status-only claim edge) | **Preserved, deliberately untouched** | I do **not** level-trigger the claim. A claim genuinely *is* a transition, so edge-shape is correct there. LTR replaces the *evidence* question only. Not everything should be level-triggered, and saying so is part of the philosophy, not a hedge against it. |
| Claim receipts are not transferable | **Slightly strengthened** | Unchanged mechanically; `Done when` joins `claim_identity`, so a twin with a different predicate is a different identity. |
| Human responses are write-once | **Preserved** | `Done when` is not a response field; nothing in the design touches `Your answer`/`Your review`. |
| Committed lifecycle claims never regress across merge parents | **Preserved** | `queue_parent_state_regression_problem` untouched. |
| Action identity frozen once live | **Preserved, with a named monotone ratchet** | `Done when` frozen when well-formed. Absent → present is a conjunctive tightening (can only make resolution harder). Present → other requires `superseded:`. |
| Timing may only escalate; freezes on response | **Preserved** | `Done when` is orthogonal to timing; no clause reads or writes a timing field. |
| Evidence must be outside the queue | **Preserved** | The grammar rejects `message-queue/` paths in every referent clause. `superseded:` is the sole queue-pointing form and is a repair primitive with its own guards. |
| Review target must differ from resolution evidence | **Preserved** | Filing-time rule extended: no clause may name the item's own `Review target` path. |
| The gate cannot be turned off | **Weakened, deliberately and visibly** | The waiver is a per-item off switch. Compensations: ≤ 30-day expiry, a monotone budget, a mandatory same-commit human authorization, full diff visibility. The briefing's position is that an *invisible* off switch (`--no-verify`) already exists and is one flag away; replacing it with a visible one is a net gain in evidence at a real cost in strictness. The v2 marker inherits the existing anti-downgrade rule. |

---

## 9. Scenario verdicts

Honest ratings. EASY = the design handles it cleanly. AWKWARD = partial, or handled at a
cost worth naming. BLOCKED = the design does not help. SILENT-CORRUPTION = the design
fails and hides it.

| # | Scenario | What happens under LTR | Verdict | Notes |
|---|---|---|---|---|
| 1 | **B1/B2** — evidence merged 3 merges ago vs. evidence never changed; must reach OPPOSITE verdicts | B1: `landed:P` TRUE at the candidate ⇒ deletable. B2: no commit touching P since filing ⇒ FALSE ⇒ blocked. Verified on the live main item: 6 qualifying commits since `b4c1ec5`, including the actual repair `6d4e337`. | **EASY** | The headline case; the design exists for it. The deadlock is not *excepted*, it is inexpressible. |
| 2 | **D22** — item content makes its own gate unsatisfiable | The predicate field cannot be a D22 vector: closed alphabet, normalization-invariant, asserted by test. Does **not** fix the existing live D22 (which lives in `Why-you-might-care` and the handover projection, untouched here). Semantically-unsatisfiable predicates remain possible, with two exits (`superseded:`, waiver). | **AWKWARD** | Prevents a new instance structurally; ships exits; does not repair the old one. |
| 3 | **D5** — reciprocal dependency that never existed; topology unvalidated | `Done when` is validated topology from day one (task ids must exist, check ids must be in `CHECKS`, paths constrained). Eight of the ~34 live requests are dependency-shaped (`future-blocking-resolve-*`/`complete-*`/`finish-*`) and map directly to `task:<id> in 4_done`, gaining validation for the first time. `Depends on:`/`Supersedes:` remain stripped from link-check. | **AWKWARD (partial win)** | Fixes the new field and the dependency-shaped third of the corpus; does not retrofit the old fields, and should not pretend to. |
| 4 | **C6/C7** — 78-commits-behind branch resurrects a pickup for a `4_done` task, deletes a live item, reverts 7 review states, clean merge, no finding | Resurrected pickup: its predicate `task:I in 1_in-progress` is FALSE at the merged tree ⇒ stuck-and-visible rather than silently re-deletable. Deleted live item: **the predicate is evaluable at the merged tree**, which an edge question is not — but `candidate_paths_match_other_parent` (:2510) still excuses the deletion, and I do not remove that excusal. Reverted review states: `queue_parent_state_regression_problem`, unchanged. | **AWKWARD** | One sub-case improved, one made re-checkable in principle, one untouched. **LTR does not solve C6/C7.** |
| 5 | **C8** — rule and first violation meet only in the merge commit | This is where the philosophy is genuinely the right tool: an edge question is *structurally meaningless* at a merge result ("did the evidence change in the merge?"), while a level predicate is a pure function of a tree and is exactly as evaluable there as anywhere. And because non-`clear:` clauses cost < 1 ms, **a full-corpus sweep of all 41 live items at the merge boundary becomes affordable (~40 ms)** — which the edge-triggered design could never offer. | **AWKWARD** | The design *enables* the fix and makes it cheap; it does not *install* the merge-result sweep. Rated AWKWARD, not EASY, on that distinction. |
| 6 | **H-P1** — answered item re-asked in 19+ handovers; projection shape-checked, never state-checked | "Should this still be projected?" becomes "is its predicate TRUE?" — a < 1 ms tree question. `check_handover_queue_projection` can require that a new handover not project an item whose predicate is satisfied. The item stays live (deletion has its own boundary rules) but stops being projected as an open ask — which is precisely what H-P1 asks for. | **EASY** | A real, cheap win, possible *only* because the predicate is a state question. |
| 7 | **E7/B13** — boundary crossed outside the repo; three `transition:merge` items whose ranges are already ancestors of main | The grammar supplies the right primitive: `landed:git:<oid>` ≡ `is_ancestor(oid, C)`, which is exactly what "already an ancestor of main" means, un-fakeable by any edit. Fixing the three live items additionally requires relaxing `approved_review_merge_receipt_problem` from "an exact two-parent merge carrying the receipt" to "reviewed head is an ancestor of the previously-admitted base, and the tail touches only queue paths" — dropping brittle topology, keeping the content guard (`git_range_review_tail_problem` already computes the second half). | **AWKWARD, fixable** | The primitive is free; the actual repair is a named, small, separate code change. |
| 8 | **G1/G3** — repair needs a commit the finding blocks; enforcement global, repair local | The design adds two brick vectors and closes both **by construction**: a malformed `Done when` is treated as ABSENT (so fixing it is a legal edit), and `Waiver` is fully mutable (so the escape hatch is reachable on a live item). The waiver then covers the semantically-unsatisfiable residue. | **AWKWARD** | Two vectors found and closed; I do not claim there is no third. This is the row most likely to be wrong. |
| 9a | **D13/D12 — "proves a byte changed, never that work happened"** | `clear:`, `task:`, `contains:` are satisfied only by a state the repo independently validates. `\n# probe\n` clears nothing. | **AWKWARD** | Real but partial: `exists:` and `landed:path` remain byte-level, and `landed:path` is the entire grandfathered corpus for one generation. |
| 9b | **B5 — "never who did it"** | **Not addressed, and deliberately not.** Every predicate is about repository state, never about actors. A claim by agent A with work by agent B is indistinguishable and stays so. | **BLOCKED, by design** | LTR is an *authorization* mechanism about state, not an *authentication* mechanism about actors. Conflating the two is how the current gate ended up strict-looking and empty. |
| 10 | **C10/C11/B17** — queue state only in an uncommitted working tree | `live_queue_items` still yields untracked files, so a malformed predicate on an untracked item still blocks that checkout — **one more field that can do this than today.** Predicates are evaluated against the index/tree, so an untracked item's predicate reads a tree it is not in. | **AWKWARD (neutral to slightly worse)** | Cheap mitigation available (validate predicates only on tracked items) but it is not part of the core claim, and the human-answer-destruction risk is untouched. |
| D1/D2/D4 | wrong / queue-pointing / typo'd evidence path, immutable, 2–4 commits to refile | Caught at **filing time** while the field is free (charset, traversal, queue-pointing, missing parent directory, unknown task/check id). Semantic wrongness corrected by `superseded:` in **one** commit. | **EASY** | Strongest secondary win in the design. |
| D10 | `blocking-` item names `operation:` where `task:` was meant; pins a task at `1_in-progress` forever | The typo is in `Blocks now:`, untouched. But the *pin* exists because the item cannot be resolved — and under LTR it resolves as soon as its predicate is true. **LTR removes the pin's cause without correcting the typo.** | **EASY (indirect)** | |
| F1 | rebase destroys the status-only claim edge | I explicitly did **not** level-trigger the claim, so this is unchanged and still broken. A level-triggered claim ("some reachable commit holds this item at claimed status with identical identity") would fix it, because rebase preserves content and only changes topology. Offered as an optional companion, not part of the core. | **AWKWARD (fix proposed, not shipped)** | |
| F2 | squash destroys the claim edge | A squash of create → claim → delete leaves **no byte of the claimed state anywhere in history**. No design over git objects can recover information that was destroyed. The answer is a policy ("do not squash-merge queue transitions"), not a check. | **BLOCKED — unrecoverable in principle** | I would rather say this than pretend. |
| F3 | cherry-pick destroys the claim edge | Same as F1: content survives, topology changes; the level-triggered claim companion fixes it. | **AWKWARD (fix proposed)** | |
| F5 | reverting a deletion resurrects an item that can never be re-deleted | The predicate is re-evaluated at the *new* deletion candidate. The work is still landed ⇒ still TRUE ⇒ immediately re-deletable. The claim edge is found by walking back to the original `open → in-repair`. **Both gates pass.** | **EASY** | The cleanest structural win: level-triggering makes deletion **idempotent**, where edge-triggering makes it once-only. This is the philosophy's best single argument. |
| F8 | shallow clone makes lineage unverifiable, every deletion fails closed | `exists:`, `absent:`, `contains:`, `task:` are **depth-independent** — they read only the candidate tree, which a depth-1 clone has in full. `landed:` and `clear:`-via-history fail closed with a "needs unshallow" message. `claimed_lifecycle_problem` still needs lineage and still fails closed. | **AWKWARD (materially improved)** | Moves the failure from "both halves fail" to "one half fails," and names exactly which clause forms are shallow-safe so an adopter can choose them. |
| G12 | batch-filed items expiring on the same calendar date lock the repo | `Done when` has **no clock dependency at all** — that is why `DETERMINISTIC_CHECKS` excludes the three clock-dependent checks. The predicate can never expire. **But my waiver reintroduces a date**, so batch-waiving reproduces G12's shape. Recovery is cheap (the `Waiver` line is freely mutable; extending is one edit) versus a `Blocks at:` date, which is a timing change with escalation rules. | **AWKWARD** | Predicate immune; escape hatch recreates the shape with a cheap exit. |

**No SILENT-CORRUPTION row.** Every failure mode above is either a blocked commit, a
visible finding, or an explicit "does not help." That is the property I would defend
hardest: the design fails loudly or not at all. If a reviewer finds a path where an
unsatisfied predicate admits a deletion quietly, that is a design-invalidating bug, not a
tuning issue.

---

## 10. The three strongest objections to my own design

### Objection 1 — "You replaced a gate that proves nothing with a gate that proves nothing, and charged six clause forms for it."

**Partially conceded.** `exists:` and `landed:path` prove roughly what today's rule proves,
and `landed:path` — the entire grandfathered corpus — is *weaker against accident*, because
an unrelated commit to a hot path satisfies it. I demonstrated this against the live item:
four of its six qualifying commits are unrelated work.

Contested for the rest. `clear:`, `task:`, `contains:`, and `landed:git:` are qualitatively
different: no cosmetic edit moves them, and `landed:git:` cannot be moved by *any* edit —
only by an actual merge.

The complexity charge has more bite, and I answer it with a **ship condition rather than a
defense**: LTR is worth shipping **only if it lets four existing escapes be deleted.**
E1 (`generated_retry_clear`) becomes `clear:`. E2 (`pickup_completed`) becomes `task:`.
E4/E5's bespoke receipt walks become `landed:git:` plus the tail guard. E6's free-for-all
non-blocking-approved delete becomes an ordinary predicate. If the implementation adds a
seventh mechanism beside six existing ones instead of absorbing them, **it should not
ship** — the repo's real problem is that its strictness gradient does not track risk, and
one more gradient makes that worse, not better.

### Objection 2 — "Level-triggering destroys the audit trail. An edge at least says *something happened at a moment*; a level predicate says only that the world has a shape, and the same shape is produced by your work and by someone else's last month."

**Fact conceded, framing contested.** Yes: `landed:P` after a merge is satisfied by
anybody's commit, and shared-credit laundering gets *easier*, not harder.

Three answers. (a) The audit trail is git, not the check; the check was never the record.
(b) The briefing's own phase-1 finding is that the edge check's "moment" is satisfiable by
appending a newline — it therefore recorded a moment of *nothing*, which is worse than
recording a state, because it manufactures false confidence and substitutes for review.
(c) For the strong clauses the shape **is** the deliverable: "the ADR exists and passes
`memory-schema`" is the point, and asking who typed it is the authentication question I
explicitly refuse to fake.

Residual cost I accept: prefer `contains:P#S` (a named section you must author) over
`landed:P` wherever the choice exists, and say so in the template.

### Objection 3 — "The waiver is the whole design. Everything else is decoration, because the moment anything is hard, agents will waive."

**This is the strongest objection and I largely concede it.** The briefing records agents
already using `--no-verify` on four `exp/*` branches. A waiver deliberately engineered to
be *cheaper* than `--no-verify` will be used more often than `--no-verify` was. If usage
does not trend down, I have built a rubber stamp with extra ceremony — and the briefing's
own warning applies to me: a strict-looking mechanism that creates false confidence is
worse than a lenient one.

I cannot guarantee the trend. What I can do is make it **countable** (a monotone-decreasing
budget line), **attributable** (each waiver files a human decision item in the same
commit), and **expiring** (≤ 30 days). And I can commit to a falsifiable test rather than a
hope:

> **If the outstanding-waiver count is not strictly decreasing 60 days after activation,
> the design has failed. The correct response is to remove the waiver mechanism and accept
> `--no-verify` as the honest escape — not to tighten the waiver.**

That is the design's load-bearing bet, and it is a bet about agent behavior, not about
git.

---

## 11. When this is the wrong choice

- **If the real requirement is attribution** — who did the work, not what state obtains —
  LTR is the wrong family entirely. It is deliberately actor-blind, and no amount of
  predicate design changes that. Pick the content-digest/attestation family instead.
- **If four existing escapes cannot be deleted** as part of the change (Objection 1's ship
  condition), the net effect is more surface, not less.
- **If a replay-stable historical record matters more than order-independence**, the
  event-sourcing design (briefing idea 3) dominates: my `clear:` clause is explicitly not
  replay-stable, and "resolved is derived, deletion is compaction" gives a record that
  never needs re-adjudication.
- **If the corpus is dominated by items whose completion is genuinely unstructured**
  (prose judgments, external outcomes with no repository shadow), the closed grammar will
  force `exists:`-shaped predicates everywhere and degenerate into today's gate with more
  syntax.
- **If the adopting repository cannot afford `git rev-list` at all** (very large history,
  no derived-cache persistence), ban `landed:` and `clear:` and accept a tree-only gate —
  which is still coherent, and is a property the current design cannot offer.
