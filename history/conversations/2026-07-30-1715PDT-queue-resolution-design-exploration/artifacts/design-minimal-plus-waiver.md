# Design — Minimal change plus a first-class escape hatch

**Author:** design agent D (assigned philosophy: minimal change + first-class escape hatch)
**Date:** 2026-07-30
**Repo:** `/Users/quentinmiao/code/ai-harness`
**Status:** proposal — implementable as written

This is the conservative option, argued as strongly as it honestly goes. It is two parts:
(A) evaluate and harden the already-finished Option C branch, and (B) add the thing the
briefing proves is missing everywhere — a declared, recorded, expiring, ratcheted override
that out-competes `--no-verify` on convenience.

Everything below marked **[measured]** was run against this repo today. Everything marked
**[reasoned]** is inference from the code and is flagged with a confidence level. Nothing is
fabricated.

---

## 0. Executive position

1. Option C's *lineage walk* is correct for the scenario it targets and **it is not slow** —
   it is measurably **faster** than main on both hot paths. That concern from the briefing is
   unfounded and I have the numbers.
2. Option C's *evidence rule* opens a laundering hole that main does not have. **14 of the 21
   live `needs-agent/requests/` items on main become deletable with zero work the day it
   merges** [measured]. I demonstrated an end-to-end laundering commit sequence that main
   rejects and Option C accepts.
3. Option C's failure mode on a shallow clone is **exit 2, zero findings, all other invariant
   reporting silenced, every commit in the checkout blocked** [measured]. That is strictly
   worse than main and must be fixed before it ships.
4. Three small hardenings (H1, H2, H4 below) fix 2 and 3 for roughly 40 lines.
5. The escape hatch is the part that actually moves the needle. It converts eleven of the
   briefing's hardest rows from "permanently stuck" to "one command plus a visible nag."
6. **It fixes exactly one of the ten hardest scenarios by construction.** Everything else is
   either untouched or routed through the hatch. That is the honest headline, and Section 8
   spells out what it means.
7. My recommendation inverts the branch's own ordering: **ship the waiver first and alone;
   ship Option C second, hardened, as its own PR.** Reasoning in Section 9, Objection 3.

---

# PART A — Evaluating and hardening Option C

## A.1 What Option C actually does

Source: `automation/reconcile/reconcile.py` on branch
`task/2026-07-26-resolve-queue-items-whose-evidence-already-merged`
(+615 lines in `reconcile.py`, +1517 test lines, 14 new module-level functions).

New rule, applied **only** to `message-queue/needs-agent/requests/` (ordinary agent requests;
task pickups keep E2, retries keep E1, human endpoints and reviews are untouched):

```
ordinary_request_resolution_evidence_problem(path, text, prior_revision, revision)   # :3041
  1. parse **Resolution evidence:** with a closed grammar
     (backticked paths | [label](dest) | [label](<dest with spaces>), comma/semicolon separated)
  2. reject absolute / traversing / URI / queue-local / whitespace-bearing entries — one bad
     entry rejects the WHOLE field
  3. queue_action_creation_roots(...) walks the DAG back to the item's UNIQUE creation commit
  4. baseline := each evidence path's bytes at that creation commit (absence is a valid baseline)
  5. admit iff, for EVERY declared path, at EVERY candidate
     (deletion revision, --range head, captured index / exact base+head synthetic merge),
     the path is a readable regular file whose bytes != baseline
```

Supporting machinery, all new:

| Function | Line | What it costs |
|---|---|---|
| `bulk_revision_parent_map` | 2896 | **one** `git rev-list --parents --topo-order`, memoized per invocation |
| `git_object_snapshot` | 918 | **one** persistent `git cat-file --batch` process; per-OID cache |
| `git_commit_snapshot` | 2773 | raw commit-header parse, terminated at the blank line; per-revision cache |
| `git_tree_entries_from_object` | 2816 | raw tree parse; per-tree-OID cache |
| `linear_queue_history_boundary` | 2951 | skips runs of commits whose whole `message-queue/` subtree is unchanged |
| `complete_creation_parents` | 2934 | compares rev-list parents against raw commit parents; **mismatch ⇒ shallow ⇒ raise** |
| `matching_disappearing_lineage_paths` | 2563 | follows unambiguous renames across merge parents |

Everything runs `git --no-replace-objects` (constant `RAW_GIT`, :53) with a source-level guard
test, after four adversarial review rounds found replacement-ref forgeries in four different
subsystems.

## A.2 Does it fix the deadlock? Yes — verified, with correct discrimination

**[measured]** I built both halves of briefing scenario 1 (B1/B2) as real commit sequences in a
worktree of the branch and ran the checker on a staged deletion.

Case B1 — evidence changed after filing, before the claim edge, and never touched in the
deletion commit:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)                                    # ADMITTED
```

Same staged deletion, main's checker:

```
[queue-resolution] .../blocking-probe-laundering.md: deleted unresolved queue item:
  resolution evidence was not created or changed in the deletion commit: `docs/probe-target.md`
reconcile: 1 finding(s)                                    # REJECTED
```

Case B2 — evidence never changed anywhere in the item's lineage:

```
[queue-resolution] .../blocking-probe-never.md: deleted unresolved queue item:
  resolution evidence was not created or changed; no surviving post-creation byte
  change: `docs/probe-never.md`
reconcile: 1 finding(s)                                    # REJECTED
```

Opposite verdicts on the two halves of scenario 1, as required. **Option C does what it says
for its target scenario.** This is not in dispute.

## A.3 Performance — the briefing's concern is unfounded [measured]

The briefing warns that `--range root:HEAD` "already exceeds a 2-minute timeout" and that "any
design adding per-edge history walking compounds there." I measured it properly.

Repo shape: 317 commits total; 127 (40%) touch `message-queue/`;
`git rev-list --parents --topo-order HEAD` costs **0.01s**.

**Hot path 1 — `--check` (the pre-commit hook path), 3 runs each:**

| Checker | Runs | Mean |
|---|---|---|
| main | 15.42 / 13.89 / 13.59 s | **14.30 s** |
| Option C branch | 8.09 / 8.46 / 8.79 s | **8.45 s** |

**41% faster.**

**Hot path 2 — `--range root:<head>` (the first-push-of-default-branch CI path).** Apples to
apples: I built a branch whose only delta from `main` is `reconcile.py` swapped for the Option
C version, so both runs replay the *same* history.

| Checker | History | Wall | Findings |
|---|---|---|---|
| main @ `38f7bb3` | 317 commits | **497.71 s** | 55 |
| Option C over identical history | 318 commits | **419.96 s** | 56 |

**16% faster**, over one more commit.

Why: `bulk_revision_parent_map` is a single `rev-list` (0.01s), and the persistent
`cat-file --batch` plus the object/tree/commit caches replace hundreds of `git show` and
`git ls-tree` **process launches** across the *whole* file, not just the new code. The lineage
walk is cheap; the caching it brought is a large net win. The branch's own claim of one
`rev-list` plus one `cat-file --batch` with a 300-commit process-budget regression test
(`test_creation_lookup_bounds_git_calls_across_300_unrelated_commits`) **checks out against the
code**: `_GIT_REVISION_PARENT_MAP`, `_GIT_OBJECT_CACHE`, `_GIT_COMMIT_SNAPSHOT_CACHE`,
`_GIT_TREE_ENTRIES_CACHE` and `_GIT_QUEUE_BOUNDARY_CACHE` are all invocation-global, so the
walk amortizes across all 21 request items rather than repeating per item.

Two caveats that keep this honest:

- **420s is still ~7 minutes.** Option C does not fix the CI budget problem; it makes it 16%
  less bad. `.github/workflows/harness.yml` sets no `timeout-minutes`, so GitHub's 6h default
  applies and the real cost today is developer patience, not a hard fail. The briefing's
  "2-minute timeout" is not in the workflow file I read.
- `linear_queue_history_boundary` only skips commits that leave the entire `message-queue/`
  subtree unchanged. **In this repo that is only 60% of commits**, so the optimisation is
  weaker here than in a typical adopted repo. It is still net positive.
- `bulk_revision_parent_map` materialises the *whole* parent graph into a Python dict. At 317
  commits that is nothing. At 1M commits it is ~100 MB and a multi-second rev-list. **[reasoned,
  high confidence]** For core-admission portability this needs the bound in H4.

**Verdict on the perf question: the branch is faster on both hot paths. Do not block it on
performance. Do keep its caching even if you reject its rule.**

## A.4 It is still a byte comparison — and it is a *weaker* one

This is the finding that matters.

The briefing establishes that appending `\n# probe\n` to the declared evidence file clears the
current check. **Option C does not change that at all.** The predicate is
`candidate_bytes != baseline_bytes`; a space satisfies it. Say that plainly: *Option C buys
zero anti-gaming.*

But it is worse than "no change," because it moves the baseline from *one commit ago* to *the
item's creation*, which means **someone else's unrelated edit now satisfies your evidence.**

**[measured] — end-to-end laundering, no work done at all:**

```
commit 1  file blocking-probe-laundering.md   Resolution evidence: `docs/probe-target.md`
commit 2  a DIFFERENT concern edits docs/probe-target.md ("unrelated typo fix")
commit 3  status-only claim: open -> in-repair
stage     git rm blocking-probe-laundering.md      <- zero work performed

Option C:  reconcile: 0 finding(s)          ADMITTED
main:      reconcile: 1 finding(s)          REJECTED
```

Under main you must at least *touch* the named file in the deletion commit. Under Option C you
need not touch anything, ever, as long as anyone else did.

**How big is that hole on today's corpus? [measured]** For every live
`needs-agent/requests/*.md`, I compared its `Filed:` date against the commit count on its
declared evidence path since that date:

```
14 of 21 live needs-agent/requests are already deletable under Option C with ZERO work

  5 churn  blocking-repair-handover-projection-code-span-copy.md   -> automation/reconcile/reconcile.py
  3 churn  future-blocking-add-the-pre-commit-mining-advisory.md    -> automation/AGENTS.md
  9 churn  future-blocking-complete-parent-before-workspace-manifest.md      -> roadmap/current-state.md
  9 churn  future-blocking-continue-first-class-message-queue-review.md      -> roadmap/current-state.md
  6 churn  future-blocking-finish-mining-task-before-transcript-backfill.md  -> roadmap/current-state.md
  9 churn  future-blocking-resolve-lineage-and-instruction-before-...        -> roadmap/current-state.md
  9 churn  future-blocking-resolve-lineage-and-provenance-before-...         -> roadmap/current-state.md
  9 churn  future-blocking-resolve-manifest-before-cross-zone-operations.md  -> roadmap/current-state.md
  9 churn  future-blocking-resolve-manifest-before-override-lineage.md       -> roadmap/current-state.md
  9 churn  future-blocking-resolve-manifest-before-recovery-evidence.md      -> roadmap/current-state.md
  6 churn  non-blocking-build-the-edge-graph-viewer-...                      -> roadmap/current-state.md
  6 churn  non-blocking-build-the-stage-2-edge-schema.md                     -> roadmap/current-state.md
  6 churn  non-blocking-build-the-stage-4-edge-join.md                       -> roadmap/current-state.md
  3 churn  non-blocking-detect-lexical-restatement-across-contracts.md       -> automation/AGENTS.md
```

Eleven live items share **one** evidence path, `roadmap/current-state.md` — a file the
end-of-session ritual in `AGENTS.md` instructs every session to update. `automation/AGENTS.md`
(2 items) and `automation/reconcile/reconcile.py` (1 item) have the same property.

This is not a corner case. **Two-thirds of the corpus this change exists to serve is
auto-satisfied by it.** Option C's design.md acknowledges the class ("a later unrelated
different-byte edit can look like the requested repair") but nobody appears to have counted it.
The count is the argument.

### H1 — the hardening that closes this

Reject at **filing** time, in `queue-schema`, never at deletion time:

> An item's `Resolution evidence` may not name a path that is already declared as
> `Resolution evidence` by another live queue item.

Pure in-memory scan over `live_queue_items()`. Zero git cost. It kills the
`roadmap/current-state.md` × 11 case outright and forces every request to name a path specific
to its own work — which is what makes the byte delta mean something.

**It must live in `queue-schema` (filing), not `queue-resolution` (deletion).** The
`Resolution evidence` field is inside the immutable action identity, so a deletion-time
rejection would be a permanent deadlock of exactly the D1/D2/D4 shape. At filing time the field
is still mutable and the cost is a rewrite.

Secondary, advisory only: a `git rev-list --count --since=<Filed> -- <path>` churn warning for
paths edited more than K times since filing. One cheap git call per distinct path, cached. I
would ship H1 and hold the churn advisory until there is a reason for it.

**Even with H1, scenario 9 (D13/D12/B5) is not fixed.** A cosmetic edit still passes. The
briefing already ruled prevention off the table; H1 narrows the hole from "anybody's edit to a
shared file" to "an edit to a file only this item names." That is a real narrowing and it is
not a fix.

## A.5 Shallow clone (F8) — the failure that must not ship [measured]

`complete_creation_parents` (:2934) compares `rev-list` parents against the raw commit object's
parents; a mismatch means the graft boundary, and it **raises `GitSnapshotError`**. There is no
`try/except` anywhere between it and `main()`; the only handler is at
`reconcile.py:8147`, which prints to stderr and `return 2`.

I built an honest deletion — the real repair genuinely landed — and cloned at `--depth 2`:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: Git snapshot error: creation history for
  `message-queue/needs-agent/requests/blocking-probe-shallow.md`
  is shallow or incomplete at 5e4372c8…
EXIT=2

$ python3 automation/reconcile/reconcile.py --check --file-retries
   (same error, exit 2, retries: 0 filed)

# same shallow clone, main's checker:
[queue-resolution] …/blocking-probe-shallow.md: deleted unresolved queue item: …
reconcile: 4 findings          exit 1
```

Every consequence is bad and all of them are new:

1. **No finding is emitted.** There is nothing for a human or agent to fix, nothing for
   `--file-retries` to file, and nothing for a waiver to name.
2. **All other findings are silenced.** The shallow clone went from 4 reported findings to 0.
   The repo's entire invariant-reporting surface disappears on one unrelated error.
3. `automation/hooks/pre-commit` is `set -e`, so **every commit in that checkout is blocked**,
   permanently, with an unactionable message. This is G1/G3 amplified to the whole repository.
4. It is triggered by an **honest** deletion. The agent did the work correctly.

GitHub Actions here uses `fetch-depth: 0`, so this repo's own CI is safe. Any adopter on the
default `fetch-depth: 1`, any `git clone --depth`, and any agent working in a shallow
sandbox hits it.

### H2 — mandatory, four lines

In `queue_deletion_problem` (:4129):

```python
    if actor == "needs-agent" and leaf == "requests":
        try:
            return ordinary_request_resolution_evidence_problem(
                path, text, prior_revision, revision
            )
        except GitSnapshotError as error:
            return (
                "resolution evidence lineage could not be verified "
                f"(shallow, incomplete, or unreadable history): {error}"
            )
```

Converts a repo-wide unfixable exit-2 brick into one ordinary finding: reported, retry-filable,
waivable, and non-contaminating. **Option C must not merge without this.**

### H4 — bound the walk

Add `CREATION_WALK_LIMIT = 5000`; when `queue_action_creation_roots` traverses more revisions
than that, raise. With H2 that becomes a finding, and with the waiver it is clearable. Protects
adopted repos with deep history, satisfies core-admission portability, ~6 lines.

### H5 — keep the caching regardless

The persistent `cat-file --batch` and the object/tree/commit caches are a measured 41% / 16%
win on the two hot paths and are independently valuable. If Option C's *rule* is rejected, land
its *plumbing* anyway.

## A.6 Rebase, squash, cherry-pick, stale-branch merge

**Rebase (F1)** — **[reasoned, medium confidence]** `queue_action_creation_roots` follows
exact-path predecessors keyed on `queue_action_identity(path, text)`, which is content-derived,
not commit-derived. A rebase preserves path and content, so the walk relocates the creation root
on the rewritten history and the rule still holds. Not empirically verified.

**Squash (F2)** — Option C's own design.md states the rule "rejects unchanged evidence,
**same-commit filing and evidence**, changes made before filing…". So if a squash collapses
filing and the repair into one commit, the creation snapshot already contains the repaired
bytes, the delta is zero, and **the item becomes permanently undeletable**. That is a new
permanent-deadlock class. `handbook/git-workflow.md` forbids squash merges here, so this repo
is safe; adopters squash by default. Needs the hatch.

**Cherry-pick (F3)** — **[reasoned, medium confidence]** A cherry-picked lineage can yield zero
roots (identity never appears on the walked parents) or two (both the original and the picked
incarnation), and `len(roots) != 1` returns
`queue action creation lineage is not unique: found N creation roots` — an item that can never
be deleted. Fails closed, which is the right polarity, and it is a deadlock, which needs the
hatch.

**Stale-branch merge (scenario 4, C6/C7)** — Option C changes **nothing** about detection. A
78-commit-behind branch still merges cleanly, still resurrects a pickup for a `4_done` task,
still reverts 7 review states, still produces no finding on either head. Nothing in Option C
evaluates a merged result. What Option C *does* change: the resurrected item may now present
two creation roots across the merge (there is a test for exactly this,
`test_ordinary_request_rejects_duplicate_creation_roots_across_merge`), so the *cleanup* after
a bad merge becomes impossible without the hatch. **Net: the corruption stays silent and the
repair gets harder.**

**Revert of a deletion (F5)** — **[reasoned, medium confidence]** genuine improvement. Reverting
a deletion restores the same identity, so the walk finds the same creation root, and the
evidence still differs from baseline ⇒ the re-deletion is admitted. Under main it was
permanently stuck. If the revert *also* reverted the evidence to its creation bytes, the design
explicitly rejects it forever ("any reversion to the baseline") — needs the hatch.

## A.7 What Option C does NOT fix, stated plainly

From the briefing's hardest list, Option C touches **one** row (B1/B2) and leaves these
completely untouched:

- **D22** — no new "is this rule satisfiable for all legal content?" analysis. It *adds* a new
  closed grammar for `Resolution evidence` over a field that is inside the immutable action
  identity, i.e. it adds a new way for legal item content to be permanently unsatisfiable.
- **D5** — queue topology (`Depends on:`, `Supersedes:`, `Successor action:`) still unvalidated.
- **C6/C7, C8** — nothing evaluates a merged result. Ever.
- **H-P1** — projection still shape-checked, never state-checked.
- **E7/B13** — three live items naming `transition:merge` whose ranges are already ancestors of
  main are still pending; three tasks still stranded in `3_in-review`.
- **G1/G3** — Option C *is* a new check on a core path, and per the briefing "any solution that
  adds a check must ship its own escape path or it adds a new way to brick the repo." Option C
  ships no escape path. Without Part B it is a net increase in brick surface (see A.5).
- **D13/D12/B5** — byte evidence still proves a byte changed, nothing more, and A.4 shows it
  proves less than before.
- **C10/C11/B17** — `live_queue_items()` still yields untracked working-tree files.
- **D1/D2/D4** — worse: a stricter grammar over an immutable field.
- **D10, G12** — untouched.

## A.8 Process observation worth recording

The branch went through **four independent adversarial review rounds and was blocked in all
four** (verification.md). Every round found a genuinely new attack class, and each repair
widened the fix's blast radius:

1. synthetic-merge candidate not checked for restoration to creation bytes; commit parsing
   crossed the raw header boundary; per-commit process launches
2. replacement refs could desynchronise the parent graph from the object snapshots
3. replacement refs could forge candidate-parent discovery into an apparent synthetic merge
4. replacement refs could hide staged queue/handover/task changes, forge review-target type and
   ancestry, hide new handovers, and substitute creation snapshots — the repair expanded from
   one function to *every audited Git read in the file*, enforced by a source-level command guard

Four rounds is unusual and it is data. Section 9 uses it.

---

# PART B — The escape hatch

## B.0 The problem it solves

The briefing is unambiguous:

- there is **no** waiver, allowlist, expiry, or break-glass mechanism anywhere;
- `--no-verify` is one flag away and agents have already used it on **four** `exp/*` branches;
- repair itself deadlocks: G1 (the finding blocks the commit that would fix it) and G3 (the
  repair task is pinned by the thing it repairs) are **both live right now**;
- prevention is off the table, so the only viable strategy is to **out-compete the silent
  bypass on convenience** while making its use visible and trending to zero.

There is also existing sanction for this inside the repo. `tasks/0_backlog/2026-07-22-retry-filing-automation-and-waivers/task.md`
already says, in the owner-directed voice:

> Add a `**Waived-until:** <date> — <reason>` field the reconciler respects, making rejection a
> real terminal state.

So this is not a new idea in this repo — it is a backlogged, owner-directed idea that never
shipped. What follows is that idea made break-glass-capable, which the backlog version is not
(see B.2).

## B.1 Location and format

### File: `WAIVERS.md`, at the repository root.

```markdown
# Reconciler waivers

**Waiver schema:** v1
**Live waivers:** 1

Each `## waiver` block suppresses exactly one reconciler finding — everywhere except the merge
boundary — until it expires. Create one with:

    python3 automation/reconcile/reconcile.py --waive-current "<why>"

Using this is legitimate and recorded. Letting one expire unresolved is not: an expired waiver
blocks the next merge and lowers the waiver budget for 30 days.

Machine-checked: Check, Subject, Finding identity, Expires, Filed, Human review, Authorized-by
shape. Attested only (nobody verifies these): Why, Retire-when, and whether a human really
authorized anything.

## waiver 1

**Check:** queue-resolution
**Subject:** `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
**Finding identity:** sha256:2f1c…64hex…
**Why:** The requested repair merged in 6d4e337 before the claim edge; the declared evidence
cannot change again, so no honest commit can delete this item.
**Authorized-by:** agent:claude
**Attestation:** self
**Expires:** 2026-08-13
**Filed:** 2026-07-30
**Retire-when:** The lineage-baseline rule lands on main and admits this deletion, or the item
is retired and refiled with a corrected evidence path.
**Human review:** `message-queue/needs-human/reviews/future-blocking-ratify-waiver-queue-resolution-blocking-repair-handover-projection.md`

## retired

<!-- append-only. One line per waiver ever removed. Never edit or delete a line here. -->
- 2026-07-28 · link-check · sha256:11ab… · resolved (not expired) · task 2026-07-26-…
```

### Why the repository root, and not anywhere else

This is the single most load-bearing choice in Part B and every alternative fails for a
concrete, verifiable reason.

**Not `automation/waivers.md`.** `automation/` is a `CORE_PREFIXES` entry in
`automation/check_core_scope.py:30`. Any staged change under it makes
`check_core_scope.py --staged` demand a `task/<task-id>` branch, a matching task folder, and a
complete `design.md` core-fit receipt — enforced by the same pre-commit hook, one stage before
the reconciler. **A break-glass that requires you to first create a task folder is not a
break-glass.** This rules out the obvious-looking home, and I verified it in the source rather
than assuming it.

**Not `message-queue/`.** Three independent reasons. (a) Every file there is governed by
`queue-name`, `queue-location`, `queue-schema`, `queue-resolution`, `stale-queue` — the very
checks a waiver may need to suppress. That is G1/G3 recursion by construction. (b) The repo's
own invariant table says "Evidence must be outside the queue"; a waiver is evidence about a
finding. (c) A queue item's existence *is* a pending action; a waiver is a recorded disposition,
not an action. Note this is exactly why the backlog's `**Waived-until:**`-on-a-retry-item design
cannot be the break-glass: retries only exist after `--file-retries` runs, and nothing runs it.

**Not `memory/decisions/`.** ADRs are immutable by hard invariant — "a reversal is a new file
linking the old one." A waiver must be *deleted* when retired. An append-only waiver store
cannot ratchet down; the count would only ever grow.

**Not a dotfile, YAML, or JSON.** The repo's entire coordination grammar is `**Field:**`
Markdown parsed by the existing `text_fields()` (`reconcile.py:229`). Reusing it means a new
parser is ~15 lines, and the file stays readable by the human who has to ratify it. A JSON
waiver file would be the only machine-only artifact in the repo.

**Root, not `docs/`.** The live waiver count is the health metric of the entire scheme. It has
to be visible to anyone who opens the repository, sitting next to `README.md` and `AGENTS.md`.
A waiver file you have to go looking for is how waiver counts drift.

**Verified non-core:** `is_core_path("WAIVERS.md")` is `False` —
`ROOT_INSTRUCTION_TOKENS = {agent, agents, assistant, assistants, instruction, instructions,
prompt, prompts}` does not contain `waivers`, and `WAIVERS.md` is not in `CORE_EXACT`. Editing
it needs no task branch, no design.md, no review. That is the property that makes it a hatch.

**One required companion change:** `check_links` (`reconcile.py:~6280`) validates backticked
paths, and a waiver's `Subject` is very often a path that has just been deleted. Add `WAIVERS.md`
to the same exemption list that already carries
`message-queue/needs-agent/retries/` ("repair items cite broken/deleted subjects by design").
Two lines, identical rationale, existing precedent.

## B.2 What a waiver must state

| Field | Machine-checked? | Check |
|---|---|---|
| `Check` | **yes** | must be a key of `CHECKS` (`reconcile.py:7261`) |
| `Subject` | **yes** | recomputed into the identity below; a waiver cannot drift off its target |
| `Finding identity` | **yes** | `== "sha256:" + finding_identity(Check, Subject)` — the **existing** function at `:7285`, already used to name retry files. Zero new identity scheme. |
| `Expires` | **yes** | ISO date; `Expires - Filed <= 21 days`; **unique across all live waiver blocks** |
| `Filed` | **yes** | ISO date, `<= TODAY` |
| `Human review` | **yes** | path exists in the candidate, is under `message-queue/needs-human/reviews/`, and its `Resolution evidence` is `` `WAIVERS.md` `` |
| `Authorized-by` | **shape only** | `agent:<slug>` \| `human:<slug>` \| `external:<opaque>` |
| `Attestation` | **conditionally** | `self`, or `queue-answer <path>@<full blob oid>` (see B.3 tier 2) |
| `Why` | **no — attested** | free text |
| `Retire-when` | **no — attested** | free text |

`Subject` and `Check` reconstructing `Finding identity` is the whole trick: it means a waiver
is bound to one exact finding, cannot be written speculatively against a finding you have not
seen, and cannot be silently re-aimed by editing one field.

**Non-waivable checks.** A hard-coded set, because waiving them is actively dangerous:

```python
NON_WAIVABLE = {"queue-location", "waiver-hygiene"}
```

`queue-location` is what surfaces C10/C11/B17 — an untracked working-tree queue item. Its
finding is the *only* signal that a human's answer may be about to be destroyed. Waiving it
makes the worst scenario in the briefing more likely, not less. `waiver-hygiene` is excluded so
the mechanism cannot exempt itself.

## B.3 Who may author one — and the identity problem, honestly

**In this repo an agent can author anything the human can.** There is no key, no signature, no
out-of-band channel inside core. The repo's own ADR already concedes the ceiling — "This proves
repository transitions, not human identity" — and a prior adversarial panel already ruled a
self-authored acknowledgement forgeable. I will not pretend to have solved this. What I do
instead is stop the mechanism from *implying* it has.

**Tier 1 — `Authorized-by: agent:<name>`, `Attestation: self`.**
An agent authorising itself. Fully permitted, no ceremony, no attestation theatre. This is the
tier that competes with `--no-verify`, and it must stay a one-liner or the whole design fails.
Its cost is entirely social and structural: it consumes a slot, files a human review item,
appears in every handover, appears in the chat reply, and prints a banner on every commit.

**Tier 2 — `Authorized-by: human:<name>`, `Attestation: queue-answer <path>@<blob oid>`.**
Machine-checked that a blob with that OID exists, that `<path>`'s bytes at some commit reachable
from HEAD hash to it, and that the file carries a non-empty `**Your answer:**` or
`**Your review:**` line. **This is not proof of human identity.** It is proof that a
human-answer-shaped artifact was committed while the item was `waiting` — which is exactly the
standard the repo already applies to every human response everywhere else. It buys consistency,
not new confidence: it raises forging cost from "type one line" to "fabricate a committed
human-response lifecycle that survives the existing write-once checks." That is not nothing and
it is not identity.

**Tier 3 — `Authorized-by: external:<opaque>`.** An adapter-supplied receipt (a protected
required check, a native review). Real assurance, **not portable**, therefore out of core per
the core-admission rule. Optional, adapter-provided.

**The design must state its own ceiling in the file itself**, and the seeded `WAIVERS.md` above
does: *"Attested only (nobody verifies these): … whether a human really authorized anything."*
A mechanism that looks stricter than it is, is worse than a lenient one, because it substitutes
for review — the briefing says this explicitly, and it applies to my design as much as to
anyone's.

## B.4 Where a waiver applies — the split gate

This is what stops the hatch from becoming a new brick.

| Invocation | Live waiver | Expired waiver | Ratchet enforced |
|---|---|---|---|
| `--check` (pre-commit hook, every commit) | **suppresses** | **suppresses** | no |
| `--check --range …` (push CI) | **suppresses** | **suppresses** | no |
| `--check --at-transition merge` (PR CI) | **suppresses** | **does not** | **yes** |

Implemented as one condition on the existing `ACTIVE_TRANSITIONS` global.

Three consequences, each deliberate:

1. **Adding a waiver is always locally unblocking and never locally blocking.** A malformed,
   expired, over-budget, or orphaned waiver never *creates* a finding at the commit gate; at
   worst it fails to remove one, and the original finding stands. The mechanism is
   monotonically finding-reducing at the commit gate. This is the property that prevents the
   hatch from reproducing G1/G3.
2. **Expiry can never brick a checkout.** At worst an expired waiver reddens the next PR — the
   one place a human is already looking. G12's calendar bomb is contained from "every commit in
   every clone" to "the next merge."
3. **The waiver survives push CI**, which is the reason an agent picks it over `--no-verify`
   (B.7).

## B.5 Expiry, and what happens at expiry (G12)

- `Expires` is a required ISO date, at most **21 days** after `Filed`.
- **`Expires` must be unique among live waivers.** A new waiver whose expiry date collides with
  an existing live one is inert until the date is changed. This is the anti-calendar-bomb rule
  and it costs one `set` comparison. G12 is designed out rather than survived.
- At expiry the waiver **does not vanish and does not lock the repo**. It stops suppressing at
  the merge boundary only. Local commits and push CI still pass.
- The companion review item carries `**Blocks at:** <the expiry date>`, so the **existing**
  `check_stale_queue` (`reconcile.py:4323`) reports it on the day, through machinery that
  already exists and is already tested.
- **Renewal is allowed exactly once**, mechanically: `Filed` may be advanced at most once per
  waiver, tracked by a `**Renewed:** <date>` field whose presence blocks a second renewal at the
  merge boundary. One renewal is honest (work is in flight); two is a permanent waiver wearing
  a costume.

## B.6 The ratchet

Three rules, all enforced **only** at the merge boundary:

**R1 — Hard cap.** `live_waivers <= WAIVER_CAP` (constant `3` in `reconcile.py`). There is no
fourth slot. To take a fourth waiver you must first retire one.

**R2 — One per merge.** `live(head) <= live(merge_base) + 1`. At most one new waiver crosses
any single merge. A "waive everything" laundering run cannot land in one PR — it needs N
separate reviewed merges, each with its own chat notification.

**R3 — Expiry costs budget.** The `## retired` ledger is append-only and each line records
whether the waiver `expired` or was `resolved`. Every ledger entry marked `expired` within the
last 30 days reduces the effective cap by one. **Letting a waiver lapse shrinks your future
budget.** This is the clause that makes the count trend down rather than oscillate at the cap:
the only cost-free way to free a slot is to actually fix the finding.

**What enforces "may only shrink":** the merge-boundary CI job, plus the fact that
`WAIVER_CAP` lives in `automation/reconcile/reconcile.py`, which is a core path — raising it
requires a `task/<id>` branch, a `design.md` core-fit receipt, and independent review, all
enforced by `check_core_scope.py` one hook stage earlier. The dishonest path (raise the cap) is
strictly more expensive than the honest path (retire a waiver). That asymmetry is the entire
enforcement story.

**It is not prevention.** An agent with `--no-verify` can edit the constant and push. Prevention
is off the table per the briefing. What R1–R3 buy is that every step of the dishonest path is a
diff in a reviewed file, and the honest path is cheaper.

## B.7 Surfacing to the human — riding the existing push channel

`--waive-current` writes **two** files in one command:

1. the `## waiver` block in `WAIVERS.md`;
2. `message-queue/needs-human/reviews/future-blocking-ratify-waiver-<check>-<slug>.md`, from
   the **existing** `templates/queue/review.md`, with
   - `**Blocks at:** <the waiver's Expires date>`
   - `**Review target:** <the waived subject>`
   - `` **Resolution evidence:** `WAIVERS.md` `` — which by construction differs when the waiver
     block is deleted, so the review item resolves cleanly through the *existing* evidence rule
     with no special case. This is precisely why the machine-readable waivers must live in one
     file whose bytes change on every retirement.

From there, **zero new delivery machinery**:

- `check_handover_queue_projection` already forces every session's handover to project every
  live `needs-human/` item into "Needs your attention," with the exact `Action` text, a
  resolving relative link, and the copied Why-you-might-care / If-you-do-nothing fields.
- `AGENTS.md` boot rule 4 already forces the final chat reply to repeat that section verbatim,
  with a clickable link and enough context to act from the reply alone.
- `check_stale_queue` already reports it on the expiry date.

**The escape hatch rides the channel the repo already enforces.** No new projection, no new
schema, no new notification path. This is the strongest single argument for the design and it
is only available because the repo already built that channel.

Plus a banner, printed on every reconciler run in every checkout:

```
reconcile: 0 finding(s)   ⚠ 2 WAIVED (expire 2026-08-06, 2026-08-13) — see WAIVERS.md
```

Every agent, every commit, sees the count. The nag is the pressure.

**One residual risk, stated:** the generated review item is subject to `queue-schema`. If
`--waive-current` generates a malformed item, that is a *new* finding, and the agent is briefly
worse off than with `--no-verify`. Mitigations: the item is tool-generated from the template
(malformation is a tool bug with a test, not an agent slip), and if the review item is missing
or invalid the waiver goes **inert** — the original finding returns, no new finding is created.
The only way to get a new finding is a malformed-but-parseable item, which is a narrow band.

## B.8 Why an agent under time pressure picks this over `--no-verify`

Four reasons. Three are structural facts about the existing system; one is exhortation and I
label it as such.

1. **`--no-verify` does not get you through CI.** It is local-only. The agent's actual goal is a
   pushed branch and an open PR. `--no-verify` defers the wall by minutes; the waiver is the
   only bypass that also survives push CI (B.4). **This is the decisive reason and it costs me
   nothing to build** — it is already true of the system.
2. **`--no-verify` skips all three hook stages**, including `check_core_scope.py` and
   `run_tests.py --staged`. The agent loses its own safety net and finds the real test failure
   later, in CI, with a bigger diff. A waiver suppresses exactly one named finding and nothing
   else.
3. **One command, zero mechanical typing.** `--waive-current "<why>"` reads the findings the
   checker just produced, picks them up by their existing identity, and writes both files with
   correct dates, identity hashes, and cross-links. `--no-verify` then requires the agent to
   remember an unenforced handover note.
4. *(weakest, and I concede it)* `--no-verify` is contract-forbidden; the waiver is permitted.
   Giving agents a legitimate door removes the rationalisation pressure. But an agent already
   willing to `--no-verify` on an `exp/*` branch is not optimising for the contract. Reasons 1
   and 2 are the ones that actually bind.

## B.9 Implementation

| Change | Lines | Risk |
|---|---|---|
| `WAIVERS.md` seeded empty | ~35 | none |
| `parse_waivers()` — `text_fields()` over `## waiver` blocks | ~45 | low |
| `apply_waivers(findings)` — filter + `NON_WAIVABLE` + banner | ~40 | low, one call site |
| `check_waiver_hygiene()` — new `CHECKS` entry, merge boundary only | ~60 | low, gated behind `ACTIVE_TRANSITIONS` |
| `--waive-current` — write both files | ~50 | low |
| `check_links` exemption for `WAIVERS.md` | 2 | none |
| `AGENTS.md` guardrail line, `automation/AGENTS.md` row, `handbook/git-workflow.md` | ~6 | none |
| tests | ~400 | — |

**Two call sites in `reconcile()`:**

```python
findings = [f for check in CHECKS.values() for f in check()]
findings, waived = apply_waivers(findings)          # <- new line
...
print(f"reconcile: {len(findings)} finding(s)" + waiver_banner(waived))
```

and `CHECKS["waiver-hygiene"] = check_waiver_hygiene`.

Total ~640 lines including tests, against Option C's 615 + 1517. Materially lower blast radius:
one filter at one call site plus one gated check, versus a new Git DAG walker threaded through
every admission read in the file.

**Migration:** none required. Zero waivers on day one; the file is inert until used. The
existing 41 live items and the entire resolved-item history are unaffected. This is the only
part of any of these designs with a trivially safe migration story.

---

# PART C — The combined design against every named scenario

Combined design = Option C **plus H1, H2, H4, H5** plus the waiver.

Legend: **EASY** = works, no ceremony. **AWKWARD** = works, costs a waiver or several commits.
**BLOCKED** = no path; the design does not address it. **SILENT-CORRUPTION** = the bad state
happens and nothing reports it.

| # | Scenario | What happens under this design | Verdict | Hatch? | Notes |
|---|---|---|---|---|---|
| 1 | **B1/B2** evidence merged before claim; two halves must differ | Option C admits the merged-evidence case and rejects the never-changed case — **[measured]** both. H1 stops 11 items sharing `roadmap/current-state.md` from auto-satisfying | **EASY** | no | The one row genuinely fixed by mechanism |
| 2 | **D22** item content makes its own gate unsatisfiable | Option C *adds* a closed grammar over an immutable field, so it creates new instances of this shape rather than curing it. Waiver clears each in one command | **AWKWARD** | **yes** | Net new risk from Option C, absorbed by the hatch |
| 3 | **D5** live item declares a reciprocal dependency that never existed | Nothing detects it. No finding exists, so there is nothing to waive | **BLOCKED** | n/a | Wholly unaddressed |
| 4 | **C6/C7** stale branch, clean merge, divergent queue | Merge still silent, still reverts review states, still resurrects a `4_done` pickup. Option C makes the *cleanup* harder (two creation roots ⇒ undeletable) | **SILENT-CORRUPTION** + AWKWARD cleanup | **yes** | Worst row. Design makes the aftermath harder, not the event detectable |
| 5 | **C8** rule and first violation meet only in the merge | Still nothing evaluates the merged result; main goes red after merge. The waiver lets main be un-redded in one command while the real fix lands — today that state is a repo-wide brick with no legal exit | **AWKWARD** | **yes** | Real liveness gain, zero detection gain |
| 6 | **H-P1** answered item re-asked forever | Projection still shape-checked, never state-checked. **Worse:** every waiver adds one more entry to the same unvalidated projection | **BLOCKED** | n/a | Marginally worsened |
| 7 | **E7/B13** boundary crossed outside the repo while `waiting` | Three live `transition:merge` items whose ranges are already ancestors of main. A human attests the crossing, waiver clears the finding, the three stranded `3_in-review` tasks move | **EASY via hatch** | **yes** | The canonical *legitimate* waiver: an out-of-band fact the repo cannot observe |
| 8 | **G1/G3** repair blocked by the finding it repairs; repair task pinned | Waive, commit the repair, delete the waiver in the same PR — the retirement is itself the evidence | **EASY via hatch** | **yes** | The waiver's reason for existing. Also required by Option C, which is itself a new check |
| 9 | **D13/D12/B5** byte evidence proves nothing about work or actor | Unfixed. **[measured]** Option C makes it *easier* — an unrelated actor's edit suffices. H1 narrows it to per-item paths; a space still satisfies it | **SILENT-CORRUPTION** (accepted) | no | The design must not claim to fix this |
| 10 | **C10/C11/B17** queue state only in an uncommitted working tree | Untouched. And `queue-location` is in `NON_WAIVABLE` **on purpose** — the finding is the only warning that a human's answer may be destroyed | **BLOCKED** | **deliberately excluded** | The one place the hatch would be actively harmful |
| 11 | **D1/D2/D4** wrong / queue-pointing / typo'd evidence path, field immutable | Option C's stricter grammar creates more of these. H1 fires at *filing* time while the field is still mutable, so it costs a rewrite not a deadlock. Existing instances: waiver, one command, instead of a 2–4 commit retire-and-refile | **AWKWARD** | **yes** | H1's placement in `queue-schema` rather than `queue-resolution` is the load-bearing choice |
| 12 | **D10** `operation:` where `task:` was meant, pins a task forever | Waive the `task-structure` finding on the pinned task so it can reach `4_done` while the item is refiled correctly | **AWKWARD** | **yes** | Ugly — waiving a *symptom* on a different subject than the cause |
| 13 | **F1 rebase** | **[reasoned, medium]** identity is content-derived, so the walk relocates the creation root; rule holds | **EASY** | no | Not empirically verified |
| 13b | **F2 squash** | Option C explicitly rejects same-commit filing-and-evidence ⇒ permanently undeletable. This repo forbids squash merges; adopters squash by default | **BLOCKED → AWKWARD** | **yes** | New permanent-deadlock class from Option C |
| 14 | **F3 cherry-pick** | **[reasoned, medium]** zero or two creation roots ⇒ `lineage is not unique` ⇒ undeletable. Fails closed, which is right, and deadlocks, which needs the hatch | **AWKWARD** | **yes** | |
| 15 | **F5** revert of a deletion resurrects an unre-deletable item | **[reasoned, medium]** genuine Option C improvement: same identity, same creation root, evidence still differs ⇒ re-deletion admitted. If the revert also restored the evidence bytes, rejected forever ⇒ waiver | **EASY** (common) / AWKWARD (evidence reverted) | partial | One of only two rows Option C improves |
| 16 | **F8 shallow clone** | **[measured]** *without H2*: exit 2, zero findings, all other reporting silenced, every commit in the checkout blocked, on an **honest** deletion. *With H2*: one ordinary finding — reported, retry-filable, waivable. The waiver itself needs no git, so it works on a shallow clone | **BLOCKED without H2** → **AWKWARD with H2** | **yes** | H2 is non-negotiable |
| 17 | **G12** batch-filed items expiring on one calendar date lock the repo | For **queue items**: untouched — `stale-queue` still fires on the date; the waiver clears it. For **waivers**: designed out — `Expires` must be unique across live waivers, and expiry binds at the merge boundary only, never at the commit gate | **EASY via hatch** / designed out | **yes** | The one row where I improved on the pattern rather than routing around it |

### Tally

- Rows fixed by mechanism, no hatch: **3** (1, 13, 15-common) — and only **row 1 is one of the
  briefing's ten hardest**.
- Rows that lean on the escape hatch: **11 of 17** (2, 4-cleanup, 5, 7, 8, 11, 12, 13b, 14, 16, 17).
- Rows still BLOCKED or SILENT-CORRUPTION after the design: **5** (3, 4-event, 6, 9, 10).
- Rows where Option C makes things *worse* absent a hardening: **4** (2, 9, 13b, 16).

**That eleven is the finding, and I am not going to dress it up.** This design's mechanism fixes
one of the ten hardest scenarios. Its hatch converts eleven more from "permanently stuck" into
"a human types one command and gets nagged in chat until it is really fixed." That is a large,
real improvement in **liveness** and a **zero** improvement in **detection**. Five rows remain
untouched, and on two of them (4 and 9) the repository can be silently wrong with nothing
reporting it.

If you were hoping the escape hatch would be a rarely-used safety valve, the table says
otherwise: **under this design the hatch is a routine part of the workflow**, load-bearing on
two-thirds of the hard cases. A design whose primary mechanism is "a human decides, on the
record, with an expiry" is a legitimate design — but it should be chosen knowingly, not
discovered later.

---

# PART D — The three strongest objections to my own design

## Objection 1 — "You have built a legalized `--no-verify`, and the ratchet will not hold."

**Largely conceded.** `WAIVER_CAP` is a constant in a writable file. The merge-boundary CI job
is a YAML file an agent with write access can edit. R1–R3 are enforced by exactly the trust
boundary that already failed on four `exp/*` branches. Nothing here is tamper-*proof*.

The narrow counter is real but small: a waiver is **tamper-evident** where `--no-verify` is
**tamper-silent**. It is a diff in a root file, plus a queue item that the *already-enforced*
handover projection forces into the human's chat reply, plus a banner on every commit. The
measurable claim is not "waivers will be rare" — it is "the count will be visible."

Which leads to the honest framing: **this design's primary output is a measurement; its
secondary output is unblocking.** If the count sits at 3 for two months, that is not the
mechanism failing quietly, that is the mechanism reporting that the underlying model is wrong.
**If you would not act on a rising waiver count, do not build this** — an honest lenient check
(extend E6's free deletion to more leaves) would be cheaper and no worse.

## Objection 2 — "Eleven of seventeen rows lean on the hatch. The hatch *is* the design, and the hatch is just 'a human decides.' You replaced an automated invariant with a manual one and called it engineering."

**Partially conceded, and it is the objection I respect most.**

The defence rests entirely on the briefing's own conclusion: prevention is off the table, and
"a strict-looking mechanism that creates false confidence is WORSE than a lenient one, because
it substitutes for review." Granting that, the question is not automated-versus-manual. It is:
*does the manual path have a record, an expiry, and a trend?*

Today it has none of the three. The manual path today is `--no-verify` plus an unenforced
prose instruction to mention it in the handover. It has already been used four times, and I
could not tell you from the repo whether those four were justified.

So the claim I am willing to defend is narrow: this converts an **undocumented, unbounded,
invisible** manual path into a **documented, expiring, counted, chat-surfaced** one, for ~640
lines and no migration. That is worth doing. It is **not** worth calling a fix, and Section C's
tally is written so nobody can read it as one.

What I will not defend: the idea that eleven hatch-dependent rows is *fine*. It is a symptom.
See Objection 3.

## Objection 3 — "Option C is 615 lines of new Git-DAG machinery to fix ONE scenario, and your own probes show it opens a 67% laundering hole and bricks shallow clones. Ship the waiver and drop Option C."

**This is the objection I cannot fully answer, and I now think it is substantially right.**

The decisive fact: **the waiver alone resolves the live stuck item today.** Waive
`queue-resolution` on `blocking-repair-handover-projection-code-span-copy.md`, delete the item,
retire the waiver — one commit, three files, no new Git machinery, no new attack surface, no
shallow-clone regression. The task that has been pinned at `1_in-progress` moves. If the goal is
"unstick the live deadlock this week," Option C is entirely unnecessary.

Option C only earns its place if the "evidence landed earlier" pattern will recur often enough
that per-instance waivers become the norm rather than the exception. The measurement cuts both
ways: 14 of 21 live requests declare shared, churny evidence paths, which suggests the pattern
**is** common — and simultaneously proves that Option C's version of the fix is far too loose
to be the right answer to it.

**Revised recommendation, inverting the branch's own plan step 10:**

1. **Ship the waiver first and alone.** ~640 lines, one call site, no migration, immediate G1/G3
   relief, and it is the escape path that Option C is required to ship anyway ("any solution
   that adds a check must ship its own escape path").
2. **Use it to unstick the live item and the three stranded `3_in-review` tasks (row 7).**
3. **Land H5 (the caching) on its own** — a measured 41%/16% speedup with no behaviour change.
4. **Ship Option C second, as its own PR, with H1 + H2 + H4** — after the waiver has been live
   long enough to *count* how often the "already merged" pattern actually fires. If the count
   is low, Option C's 615 lines never needed to exist.

That ordering is uncomfortable because Option C is the finished thing and the waiver is not
written yet. It is still the right ordering, and the four blocked review rounds are the reason.

## The strongest argument that a deeper redesign is worth the extra cost

I will make it properly rather than gesturing at it.

**The four blocked adversarial rounds are the evidence.** Each round found a *new* class of
attack, and each repair widened the blast radius:

| Round | Attack class | Repair scope after |
|---|---|---|
| 1 | synthetic-merge candidate restored to creation bytes; header-boundary parsing; per-commit process launches | one function |
| 2 | replacement refs desynchronise the parent graph from object snapshots | the shared object reader |
| 3 | replacement refs forge candidate-parent discovery into an apparent synthetic merge | range-candidate validation |
| 4 | replacement refs hide staged queue/handover/task diffs, forge review-target type and ancestry, hide new handovers, substitute creation snapshots | **every audited Git read in the file**, enforced by a source-level command guard |

That progression is the signature of a mechanism fighting its substrate. Byte comparison against
a historical baseline has an **unbounded** attack surface, because the history is locally
rewritable in a dozen ways (`refs/replace`, grafts, shallow boundaries, rebases, cherry-picks,
synthetic merges, force-pushes) and each one is a separate thing to remember. Round 5 exists;
nobody has found it yet.

A **level-triggered** predicate over *current* repo state (briefing idea 1) has no baseline
moment to attack. `git log` plus the working tree is the oracle; there is no "bytes at commit X"
for a replacement ref to lie about. Making "resolved" a **derived status** and deletion a
**compaction** step (idea 3) means the hook only ever computes and never adjudicates an
irreversible act — and an honest "no longer relevant" becomes a first-class terminal state
instead of a waiver.

Score it against my own table. A level-triggered design plausibly collapses rows **2, 5, 8, 11,
12, 13b, 14, 16** — eight rows that I route through the hatch — into "no deadlock exists, so no
override is needed," because order-independence is the whole point of the pattern. That would
take the hatch from eleven rows to three, which is what a *safety valve* looks like as opposed
to a *workflow*.

**The measured cost of the current path:** 615 + 1517 lines, four blocked review rounds, a hole
that auto-satisfies 67% of the live corpus, a new permanent-deadlock class on squash, and a
shallow-clone brick that silences all reporting — to fix one scenario, with a mechanism that
provably buys zero anti-gaming.

**The decision rule I would actually write down:** ship the waiver now, because it is cheap and
correct regardless of what comes next. Then look at the waiver count after 60 days. **If more
than two waivers are live at once for more than a few weeks, the redesign is cheaper than the
waivers, and this design has done its most valuable job — telling you that.**

---

# PART E — When this is the wrong choice

1. **If the human will not read or act on the waiver count.** The entire enforcement story is
   visibility plus an asymmetric cost. Without a reader, the hatch is `--no-verify` with extra
   steps, and an honestly lenient check would be cheaper and no less safe.
2. **If AgentFold is about to be adopted by third parties.** Shallow clones, squash merges, deep
   histories and rebase-heavy workflows are all normal outside this repo, and every one of them
   lands on the hatch. The hatch works because a nag reaches one owner in chat. That does not
   scale to adopters who cannot be nagged.
3. **If more than ~2 waivers stay live for more than a few weeks.** That is the ratchet failing,
   and it means the underlying model — one-shot byte evidence bound to a deletion edge — is
   wrong. At that point pay for idea 1 or idea 3.
4. **If the goal is detection rather than liveness.** This design improves liveness a lot and
   detection not at all. Rows 3, 4, 6, 9 and 10 stay broken. If silent divergence across a
   stale-branch merge is the thing that worries you most, none of this helps and you should
   spend the budget on evaluating merged results instead.

---

## Appendix — reproduction commands for every measurement

```bash
# perf, --check
for i in 1 2 3; do /usr/bin/time -p python3 automation/reconcile/reconcile.py --check; done
# main mean 14.30s; Option C branch mean 8.45s

# perf, root:HEAD, apples-to-apples (only reconcile.py differs)
git worktree add --detach /tmp/afold-perf main
git show task/2026-07-26-…:automation/reconcile/reconcile.py > /tmp/afold-perf/automation/reconcile/reconcile.py
# commit, then:
python3 automation/reconcile/reconcile.py --range root:<full-oid>
# main  317 commits: 497.71s, 55 findings
# OptC  318 commits: 419.96s, 56 findings

# laundering probe (Section A.4)
#  commit 1: file request with Resolution evidence -> docs/probe-target.md
#  commit 2: unrelated edit to docs/probe-target.md
#  commit 3: status-only open -> in-repair
#  stage:    git rm the request, do no work
# Option C: reconcile: 0 finding(s)     main: reconcile: 1 finding(s)

# corpus scan (Section A.4)
for f in message-queue/needs-agent/requests/*.md; do
  ev=$(grep -m1 '^\*\*Resolution evidence:\*\*' "$f" | sed 's/.*\*\* *//; s/`//g')
  d=$(grep -m1 '^\*\*Filed:\*\*' "$f" | sed 's/.*Filed:\*\* //;s/,.*//')
  echo "$(git rev-list --count HEAD --since=$d -- $ev) $f -> $ev"
done
# 14 of 21 have >0 post-filing churn

# shallow clone (Section A.5)
git clone --depth 2 --no-local file:///<worktree> /tmp/afold-shallow -b <branch>
cd /tmp/afold-shallow && git rm <request>.md && python3 automation/reconcile/reconcile.py --check
# Option C: "Git snapshot error: creation history … is shallow or incomplete", EXIT=2, 0 findings
# main:     4 findings, exit 1
```
