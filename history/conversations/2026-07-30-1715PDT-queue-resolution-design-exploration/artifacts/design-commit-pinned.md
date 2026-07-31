# Design — Commit-pinned / digest-bound resolution receipts

**Philosophy:** stop asking *when* the work happened. Make the resolving commit **name
the object** where the work landed, and make the checker verify that the named object
exists, is reachable, really did what was claimed, and **still stands in the tree being
committed**.

**Status:** proposal, one of four independent designs
**Author:** design agent (commit-pinned lane)
**Repo:** `/Users/quentinmiao/code/ai-harness`
**Target code:** `automation/reconcile/reconcile.py` (`resolution_evidence_problem` :2722,
`queue_deletion_problem` :3577), `message-queue/AGENTS.md`, `templates/queue/*.md`,
`automation/hooks/`

---

## 0. Measurements taken before designing

All numbers measured on the repo at `38f7bb3` (317 commits, 41 live queue items,
45 historical queue deletion/rename events, 127 commits touching `message-queue/`,
git 2.23, macOS):

| Measurement | Value |
|---|---|
| `reconcile.py --check`, clean tree, no staged deletion | **8.69 s** |
| `reconcile.py --check --range root:HEAD` | **426.9 s** (284 s user + **135 s system**), 55 findings |
| One `git` spawn (`rev-list --parents -n 1`) | **10.6 ms** |
| One `git merge-base --is-ancestor` spawn | **13.0 ms** |
| 200 object queries through one `git cat-file --batch-check` process | **27 ms total** (~0.05 ms each, spawn included) |
| `git cat-file --batch-check` accepts `<rev>:<path>`, reports `missing` for absent | verified |
| `git cat-file --batch` on a commit oid returns tree/parents/author/message | verified |

Two facts drive the entire cost section:

1. **135 s of the 427 s root:HEAD run is system time.** That is `fork`/`exec`, not work.
   `git_tree_blob_entry` (:1160) spawns **one `git ls-tree` per `(revision, path)` pair**,
   and `resolution_evidence_problem` calls it twice per evidence path per deletion.
2. **A persistent `cat-file --batch-check` reader answers the same questions for ~0.05 ms
   and zero spawns.** The reconciler already runs a persistent `cat-file --batch` process
   (`git_blob_bytes` :899). The mirror process is a 20-line addition.

Therefore a design that replaces `ls-tree`-per-path lookups with batch-check digests is
*cheaper than what it replaces*. This design does that.

---

## 1. The receipt: what is recorded, and where

### 1.1 Two artifacts, not one

The receipt is split across two places because the two halves have opposite lifetimes:

| Half | Where | Written when | Lifetime |
|---|---|---|---|
| **Baseline** — what the evidence looked like *before* the ask | `**Resolution baseline:**` field **in the item**, at filing | item creation, before it goes live | frozen inside the item's immutable action identity |
| **Receipt** — what landed, and where | **git commit trailers on the deletion commit** | the resolving commit | the commit object, forever |

The baseline cannot go on the deletion commit: it must be fixed *before* the work, or an
agent can pick a baseline that makes any change look like completion. The receipt cannot
go in the item: the item is deleted by the very act it describes, and — mechanically —
adding a field to a live item trips `queue_mutation_problem` via `immutable_action_text`
(:1986), because `Resolution evidence` and every non-lifecycle field are frozen after
filing. The split is forced by the existing invariants, not chosen for taste.

### 1.2 Location evaluation for the receipt half

| Option | Survives rebase / squash / cherry-pick | Survives fresh clone | Visible in `git log` | Cheap to check | Verdict |
|---|---|---|---|---|---|
| **Field in the deleted item** | n/a — the file is gone | no (only in history) | no | yes | **Rejected.** Mechanically impossible: the field would have to be added after the claim edge, which `claimed_lifecycle_problem` (:2655) rejects as "action identity or response changed after it was claimed". |
| **Git note** (`refs/notes/*`) | yes (notes survive; `notes.rewriteRef` can copy) | **no** — `refs/notes/*` is not in the default fetch refspec | only with `--notes` | yes | **Rejected.** Silently absent in a fresh clone, and notes are *mutable* — a resolution receipt that can be rewritten violates "records are immutable". |
| **Separate tracked receipt file** (`history/resolutions/<slug>.md`) | yes (tree content) | yes | `--stat` only | **free** (already in the index cache) | **Runner-up.** Rejected for clutter (one file per resolution, forever, needing its own GC policy and its own schema), and because it can be staged in a *different* commit than the deletion, decoupling receipt from act. |
| **Free prose in the commit message** | yes | yes | yes | fragile parse | Rejected: unparseable, and indistinguishable from narrative. |
| **Git commit trailers on the deletion commit** | message is preserved by rebase, cherry-pick and squash (squash concatenates) | yes — part of the commit object | **yes**, and `git log --grep` finds them | ~free through the batch reader | **Chosen.** |

**Why trailers win.** The receipt is a statement *about an act*; a commit message is the
only place in git that is bound one-to-one to an act, is copied by every history-preserving
operation, is visible without extra flags, and costs nothing to store. Decisively, it
enables the query this whole design exists to make possible:

```
git log --grep='^Resolves: message-queue/needs-agent/requests/blocking-foo.md'
```

Today there is *nothing to point at* when you ask "what resolved this item?" — the answer
is buried in a diff of an unrelated file on a commit that also did five other things.

**The one real cost of trailers**, and its answer: `pre-commit` runs *before* the message
exists (git's `prepare_to_commit()` runs the pre-commit hook, then writes
`COMMIT_EDITMSG`). So the receipt cannot be verified by the existing hook. It is verified
by a new `automation/hooks/commit-msg`, which receives the message file as `$1`.

This is cheap because `install.py` sets `core.hooksPath automation/hooks` — a **tracked
directory**. Adding `automation/hooks/commit-msg` activates for every clone that has ever
run `install.py`, on the next `git pull`, with **no re-install**. There is no partial
migration state.

### 1.3 Exact grammar

**In the item** (new optional field, written at filing by a tool):

```
**Resolution baseline:** sha256:<64 hex>
```

or, when the evidence file does not exist yet:

```
**Resolution baseline:** absent
```

or, when the item declares more than one evidence path (explicit pairing, order-free):

```
**Resolution baseline:** `automation/reconcile/reconcile.py` sha256:1a2b…, `docs/designs/x.md` absent
```

The digest is `sha256` of the exact file bytes — the same vocabulary the repo already uses
for `Review revision:` (`sha256:344a30c8…` in
`message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`) and
the same computation as `negative_review_cancellation_problem` (:3412). It is deliberately
*not* a git blob oid: sha256-of-bytes is provider-neutral, reproducible with
`shasum -a 256`, and identical in a repo that is not git.

**On the deletion commit** (trailer group; one group per item deleted in that commit):

```
Resolves: message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
Resolved-by: 6d4e337a1c9f0e2b5d8c4a7f3e1b0d9c8a6f5e4d
Resolved-evidence: automation/reconcile/reconcile.py=sha256:9f3c…
```

- `Resolves:` opens a group and names the exact repo-relative item path being deleted.
- `Resolved-by:` names one **full 40-hex commit oid** — the commit where the work landed.
- `Resolved-evidence:` repeats once per declared evidence path, as
  `<path>=sha256:<64 hex>` — the digest that `Resolved-by` **produced** at that path.
  The path set must equal `resolution_evidence_paths(item_text)` exactly.

Optional, for the honest-anomaly cases (each is *recorded and counted*, never silently
inferred):

```
Resolved-by-prior: yes        # the work commit predates the item's filing (see §3, B1)
Resolves-corrective: <full oid of an earlier deletion commit>   # forward repair, see §6
```

**Parsing rule (deliberate deviation from strict git trailer convention): scan the whole
message, not only the last paragraph.** Precedent exists — `reconcile.py` :4538 already
scans whole messages for `task:` tokens. Whole-message parsing is what makes a squash
merge (which concatenates several messages) preserve every group instead of only the last
one. This is a direct hardening against F2.

**In `Resolved-by`'s own message** (optional but checked when present — see §3):

```
Resolves: message-queue/needs-agent/requests/blocking-foo.md
```

A work commit that names the item it is doing the work for produces a **Tier A (bound)**
receipt. A work commit that does not produces a **Tier B (pinned)** receipt. The tier is
*derived by the checker*, never declared by the agent, so it cannot be lied about.

---

## 2. What the checker verifies

Replaces `resolution_evidence_problem(text, prior_revision, revision)` with
`resolution_receipt_problem(path, text, prior_revision, revision, message)`.
Every call site that reaches the ordinary evidence path (`queue_deletion_problem` :3671
and :3692, `review_cleanup_boundary_problem` :3464/:3472/:3478,
`negative_review_cancellation_problem` :3359) routes through the new function. The
existing escapes E1 `generated_retry_clear`, E2 `pickup_completed`, E3 successor pairs,
E4 `approved_review_merge_receipt_problem`, E5 `task_transition_receipt_problem` are
**untouched** — they are already commit-pinned in spirit and this design is their
generalization, not their replacement.

Let `P` = a declared evidence path, `C` = `Resolved-by`, `D` = the deletion candidate
(a commit oid, or `None` meaning the staged index), `B` = the baseline digest for `P`.

### V0 — Receipt present and shaped

Parse the message into groups. Exactly one group must have `Resolves: <path>` equal to
the deleted item path (or, for a rename-out-of-queue deletion, the source path).
`Resolved-by` must match `^[0-9a-f]{40}$`. The `Resolved-evidence` path set must equal
`resolution_evidence_paths(text)`.

*Plumbing:* pure Python on a string. **0 spawns.**
*Failure:* `"deletion commit carries no resolution receipt for <path>"`.

### V1 — Baseline resolved

If the item carries `**Resolution baseline:**`, use it (**0 spawns**). Otherwise (legacy
item, §5) derive it: find the item's creation commit
`git log --diff-filter=A --format=%H -- <item path> | tail -1` (**1 spawn, memoized**),
then read `<creation>:<P>` through the batch-check reader and sha256 its bytes
(**0 spawns**). If the creation commit is unreachable (shallow clone), **fail open** with
a recorded advisory — see §6/F8.

### V2 — The named commit exists

Query `C` through the persistent `cat-file --batch-check` reader. Result must be
`<oid> commit <size>`.
*Plumbing:* **0 spawns.**
*If missing:* do **not** fail. Enter the **degraded path** (§2.9).

### V3 — The named commit is reachable from the deletion candidate

`C` must be an ancestor of `D` (committed case) or of at least one staged parent
(`staged_parent_oids()`, staged case).
*Plumbing:* `git merge-base --is-ancestor C D` — **1 spawn (13 ms)**, already memoized by
`_GIT_ANCESTRY_CACHE`; **0 spawns** once the commit-graph preload (§4) lands.
*Failure:* `"receipt names <C>, which is not reachable from the deletion"`. This is the
check that makes a cherry-picked deletion without its work commit fail, correctly.

### V4 — The named commit is not the deletion itself

`C != D`. Staged case: trivially satisfied, the deletion commit does not exist yet.
Additionally, `C` must not be a commit whose *only* change is queue state:
`git diff-tree --name-only C` must contain at least one path outside `message-queue/`.
*Plumbing:* one `diff-tree` — **1 spawn**, memoized by oid; or **0** by reading `C`'s tree
vs its parent's tree entry for `message-queue` through batch-check.
*Failure:* `"receipt names a queue-only commit; evidence must live outside the queue"`.
This mechanically extends the existing "evidence must be outside the queue" invariant from
*paths* to *commits*.

### V5 — The named commit really modified the evidence, and produced the declared digest

For each declared `P`:
- `blob(C:P)` must exist, and `sha256(bytes(C:P))` must equal the `Resolved-evidence`
  digest for `P`.
- `blob(C:P)` must differ from `blob(C^n:P)` for **every** parent `n` of `C` (for a merge
  commit `C`, the evidence must differ from both sides — a merge that merely carries
  someone else's change is not itself the work).
*Plumbing:* `C`'s parent list comes free from the `cat-file --batch` read of the commit
object; each `<rev>:<path>` is one batch-check query. **0 spawns.**
*Failure:* `"receipt names <C>, which did not change <P>"` /
`"<P> at <C> is not the declared digest"`.

### V6 — The effect survives in the tree being committed (the level-triggered core)

For each declared `P`, read the candidate digest:
- staged case: `git_index_path_entry(P)` — already loaded by the single `git ls-files -s`
  the reconciler performs. **0 spawns.**
- committed case: `<D>:<P>` through batch-check. **0 spawns.**

Then require **both**:

- **(a) the evidence moved off its baseline:** `sha256(P @ D) != B`
  (or, if `B` is `absent`: `P` exists at `D`).
- **(b) the named commit's change was not undone:** `sha256(P @ D) != sha256(P @ C^1)`.

(a) is the check that dissolves the entire defect. It compares the candidate tree against
a digest fixed at filing time — an **unbounded window**, order-independent, with no
history walk at all. "The work landed three merges ago" is not merely tolerated; it is
*indistinguishable* from "the work landed in this commit," which is the correct answer.

(b) is what "commit-pinned" adds on top: it catches the case where the evidence has moved
since filing but the specific change you are claiming credit for was reverted.

### V7 — Ordering

`C` must **not** be an ancestor of the item's creation commit — i.e. the work must not
have already been in history when the ask was written.
*Plumbing:* one ancestry query, **0 spawns** after the graph preload.
*Failure:* `"receipt names <C>, which predates the item's filing"` — **unless** the group
carries `Resolved-by-prior: yes`, in which case the check passes and the reconciler counts
it as a declared anomaly (see §3 and the honest treatment of B1).

V7 is what stops a **twin-item** attack: filing a second identical item and resolving it
by pointing at the *same* old commit that resolved the first. Without V7 the receipt would
be transferable; with it, a receipt is only usable by items filed before the work.

### V8 — Tier derivation (recorded, not gating by default)

Read `C`'s message through the batch reader (**0 spawns** — the commit object read in V2
already contains it). If it carries `Resolves: <this item path>`, the receipt is **Tier A**.
Otherwise **Tier B**. The tier is reported by `--audit` and may be *required* per policy
(§3), but is never required for pre-v2 items and never required to be self-declared.

### 2.9 The degraded path (V2 failed: `C` is not an object in this repository)

This is not an error. It is what a rebase, a squash of the work commit, a shallow clone,
or a `filter-repo` leaves behind. Verification continues with content only:

- **D1.** The `Resolved-evidence` digest must correspond to a **real blob present in the
  repository** — sha256 is not a git oid, so this is checked by walking
  `git log --format=%H -- P` (**1 spawn**, memoized per path) and batch-checking `<oid>:P`
  for each until a match is found. A fabricated digest fails; a digest that genuinely
  existed at that path at some point in history passes.
- **D2.** V6(a) still applies in full — the candidate digest must differ from the baseline.
- V3, V4, V5, V7 and the tier are skipped and the receipt is recorded as **degraded**.

A degraded receipt **passes**. This is a deliberate, load-bearing choice, argued in §3 and
conceded in Objection 2: failing closed here would turn every rebase and every shallow
clone into a repo-wide brick, which is exactly the class of failure the briefing warns
against (F8, G1/G3).

---

## 3. Anti-laundering — the honest analysis

**The briefing's finding:** appending `\n# probe\n` to the declared evidence file and
staging it clears `resolution_evidence_problem` entirely. The invariant buys "the deletion
commit also touched the named file," never "the work happened."

**Does naming a commit fix that? No. Be clear about this.**

A launderer under this design does:

1. `echo '' >> automation/reconcile/reconcile.py && git commit -m "chore: touch"` → commit `X`.
2. Next commit: delete the item with `Resolves: …` / `Resolved-by: X` /
   `Resolved-evidence: automation/reconcile/reconcile.py=sha256:<the new digest>`.

Every check passes. V5 (X modified P) passes. V6 (digest moved off baseline, not reverted)
passes. V7 (X postdates filing) passes. It is even **Tier A** if they write
`Resolves: <item>` in X's message — which is one extra line.

**So the mechanism relocates the problem. What does the relocation actually buy?**

| Before | After |
|---|---|
| The laundering is a staged byte inside a commit that also does real things. Invisible. | The laundering is a **named commit** the deletion **points at**, in a **greppable index**. |
| Nothing records what was claimed to resolve the item. | `git log --grep='^Resolves: <path>'` returns the deletion; `git show <Resolved-by>` returns the exact diff the agent claimed as the work. |
| Cost to launder: **1 staged byte, 0 extra commits, 0 attributable statements.** | Cost to launder: **1 extra commit, permanently in history, authored and timestamped, whose one-line whitespace diff is the agent's own testimony.** |
| Cost to be honest when the work already merged: **impossible** (permanently stuck item). | Cost to be honest when the work already merged: **3 trailer lines, generated by a tool.** |

The last row is the design's actual thesis. The briefing already ruled prevention off the
table ("with a bypassable hook, one shared identity, and the checker living in the same
writable tree, you cannot prevent laundering"). The achievable goals are **tamper-evidence,
order-independence, and cheap honest paths**. This delivers all three and I claim nothing
more. In particular I do **not** claim the receipt makes forgery harder in a security
sense; I claim it makes forgery *nameable*, and honesty *possible where it currently is
not*.

### 3.1 The one attack the pin genuinely kills: repurposing

Without V4/V5/V7 an agent could point at *any* commit that ever touched `P` — someone
else's honest work, unrelated to the ask — and delete the item for free. V5 (C changed P
and produced this exact digest), V4 (C is not queue-only), V7 (C postdates the filing) and
V6(a) (the current tree still differs from the filing baseline) together mean the named
commit must be a real, post-filing, non-trivially-located change to the declared artifact
that still stands. That is not proof of work, but it is the difference between *pointing
at a fact* and *pointing at any fact*.

### 3.2 Requiring a back-trailer on the work commit (Tier A) — cost/benefit

**What it would buy:** the work commit must have been authored knowing the item existed.
It kills "grab a stranger's commit" completely: you cannot retroactively add a trailer to
a pushed commit without rewriting history, which this repo forbids.

**What it costs — and this is why it cannot be mandatory:**

- **Scenario B1 (the live defect).** The stuck item's repair merged in `6d4e337`, whose
  message does not name the item. Requiring Tier A re-blocks the exact item this redesign
  exists to unblock. Fatal on its own.
- **Work that legitimately precedes filing.** An agent fixes something; a later session
  files an item asking for it (or a human asks for something already done). Requiring a
  back-trailer means the honest answer — "already done, here it is" — is unrepresentable.
- **Work by another actor.** Agent B does the work on a task branch; agent A folds the
  queue item. B's commit will not name A's item.
- **Merge-carried work.** The work is a range on a branch; no single commit is "the" one.
- **It buys nothing against a determined launderer**, who simply writes the trailer.

**Decision: Tier A is derived and reported, never required by default.** Two knobs are
offered but off in core:

- `receipt.require-tier-a-for-blocking` — require Tier A for `blocking-*` items *filed
  after the v2 activation commit only*. Legacy and non-blocking items are unaffected.
  This is the only place where the strictness gradient can be made to track risk without
  re-bricking the migration corpus.
- `Resolved-by-prior: yes` — the declared escape when V7 fails legitimately. It is a
  *statement*, counted by `--audit`, not a suppression. A repo that sees this trailer
  trending upward knows exactly which resolutions to review.

---

## 4. Cost

### 4.1 Per item, per `--check`

| Work | Today | This design (v2 item) | This design (legacy item) |
|---|---|---|---|
| Read evidence at prior revision | 1 `ls-tree` spawn per path (11 ms) | — (baseline is a literal) | 1 spawn for creation commit (memoized) |
| Read evidence at candidate | 1 `ls-tree` spawn per path, or index-cached | 1 batch-check query (~0.05 ms) | same |
| Verify named commit + parents | — | 1 batch read of the commit object (0 spawns) | same |
| `blob(C:P)`, `blob(C^n:P)` | — | 2–3 batch-check queries (0 spawns) | same |
| Reachability + ordering | — | 2 ancestry queries → **1–2 spawns**, or **0** with the graph preload | same |
| **Total spawns per deleted item** | **1–2 (11–22 ms)** | **0–2 (0–26 ms), 0 with preload** | **1–3, 0–1 with memo** |

**Live-item count is irrelevant to the receipt check.** The 41 live items are never
receipt-checked; only *deletions* are. The only per-live-item work added is a pure-string
regex validating the `Resolution baseline:` shape in `check_queue_schema` — 41 × ~0 µs.

**Pre-commit, the path agents actually feel.** A typical coordination commit deletes 1–2
items. Added cost: **0–26 ms on a measured 8.69 s baseline (≤0.3 %)**, and it *removes*
2–4 `ls-tree` spawns the current check pays. Net: **at worst a wash, at best faster.**

### 4.2 `--range root:HEAD` — the path that already takes 426.9 s

Measured today: **426.9 s, of which 135 s is system time** (i.e. spawn overhead), 55
findings. The design must not compound there. It does not, for three reasons:

1. **The receipt requirement is not retroactive.** Deletions whose commit is an ancestor
   of the v2 activation commit are checked under **v1 rules, unchanged** (§5). This is the
   repo's own stated rule for grammar changes: *"Entry schema versions preserve
   creation-time grammar; a newly rejecting grammar needs a new version instead of
   retroactive validation"* (`automation/CLAUDE.md`). All 45 current historical deletions
   are pre-v2 and cost exactly what they cost today.
2. **Post-v2 deletions add 0 spawns each** once the graph preload (C2) is in place; V6 at
   the newest candidate is one batch-check query.
3. **The whole run gets faster,** because C1 (below) is a prerequisite of this design and
   is the single largest available speedup to the existing queue check.

### 4.3 Caching (all three are part of this design, not optional)

**C1 — persistent `git cat-file --batch-check` reader.** Mirror of the existing
`_GIT_CAT_FILE_PROCESS` (:907). Converts `git_tree_blob_entry(revision, path)` from *one
`ls-tree` spawn per pair* to *one pipe round-trip*. Measured: 0.05 ms vs 10.6 ms — a
**200×** reduction on the hottest operation in the reconciler. This alone should reclaim
most of the 135 s of system time in the root:HEAD run, and it is worth landing
independently of the rest of this design.

**C2 — in-process commit graph.** One `git rev-list --parents <heads>` (1 spawn; 317
commits here, ~50 ms at 10 k commits) builds a parent map; ancestry becomes an in-process
BFS with memoized answers. Replaces every `merge-base --is-ancestor` in the receipt path
and, incidentally, `deletion_and_later_candidates` (:2932) and
`approved_review_merge_receipt_problem`'s `git_is_ancestor` loop (:3325).

**C3 — on-disk verdict memo.** `$GIT_DIR/agentfold/receipt-verdicts.json`, keyed by
`(check_version, deletion_commit_oid)`. V0–V5 and V7 are functions of **immutable inputs
only** (a commit oid and its ancestors), so a verdict once computed is a permanent fact.
V6-at-newest-candidate is head-dependent and recomputed every run at 1 batch-check query
per (item, path). Stored under `$GIT_DIR`, so it is repository-local (satisfying *"tracked
executables use repository-local state only"*), never appears in the worktree, needs no
`.gitignore` entry, and is silently skipped if unwritable. Invalidated wholesale by
bumping `check_version`.

With C1+C2+C3, `--range root:HEAD` on a warm memo should be **dominated by C1's savings,
not by anything this design adds.**

---

## 5. Schema and migration

### 5.1 Changes

| File | Change |
|---|---|
| `message-queue/AGENTS.md` | `**Queue resolution schema:** v1` → `v2`; one lifecycle line: *"A deletion commit carries the item's resolution receipt (`Resolves:`/`Resolved-by:`/`Resolved-evidence:`); items filed under v2 record `Resolution baseline` at filing."* |
| `templates/queue/{decision,clarification,request,retry,review}.md` | add `**Resolution baseline:** <sha256:… of the Resolution evidence file at filing, or `absent`; stamp it with `reconcile.py --stamp-baseline`>` immediately after `**Resolution evidence:**` |
| `handbook/git-workflow.md` | the receipt trailer block in the "Rolling back" / coordination-commit rules; the forward-repair recipe (§6) |
| `automation/hooks/commit-msg` | **new**: `python3 "$ROOT/automation/reconcile/reconcile.py" --check-receipts --message-file "$1"` |
| `automation/hooks/pre-commit` | unchanged (still runs the full `--check`; receipt verification defers) |
| `reconcile.py` | `resolution_receipt_problem`, `--check-receipts`, `--message-file`, `--stamp-baseline`, `--receipt`, `--audit`; C1/C2/C3 |
| `reconcile.py` `claim_identity` (:1955) / `immutable_action_text` (:1986) | add `Resolution baseline` to the frozen key set for both actors |

### 5.2 How the 41 live items migrate: **they are not edited**

This is the critical constraint and it is forced, not chosen. Adding
`**Resolution baseline:**` to a live item changes `immutable_action_text`, which changes
`queue_action_identity`, which makes `queue_mutation_problem` report
*"live queue action was rewritten"* — the exact D22 trap. **A migration that edits live
items is a migration that bricks the repo.**

Instead: **legacy items derive their baseline** from the digest of the evidence path at the
item's creation commit (V1, 1 memoized spawn). Semantically identical, mechanically free
of mutation findings, and it works for all 41 items today.

### 5.3 Coexistence and the activation edge

The repo already has this machinery (`schema_activation_commits` :1242,
`queue_resolution_activation_commits` :1284, `governed_by_activation_join` :1453). The v2
edge reuses it verbatim:

- `queue_resolution_enabled()` accepts `v1` **or** `v2`. Removing the marker entirely
  remains the anti-downgrade failure it is today (:3713). **Downgrading `v2` → `v1` is
  also a removal**, and must be reported identically — otherwise the gate can be turned
  off, violating the last invariant.
- A deletion edge is receipt-governed iff its commit is a descendant of a **v2** activation
  commit. Everything earlier keeps v1 semantics forever. Old and new coexist permanently;
  there is no cutover moment.
- An item is **baseline-required** iff its creation commit is a descendant of a v2
  activation commit. The 41 current items are all pre-v2 → derived, never required.
- Staged mode: `candidate_activation_heads` (:1298) already handles "the marker is being
  activated in this very commit," including the merge case. No new logic.

### 5.4 The one genuinely new activation edge, stated plainly

The `commit-msg` hook activates by `git pull`, not by `install.py`. Between a developer's
`git pull` and their next commit there is no window. **But**: a clone that never ran
`install.py` has no hook at all — identical to today's situation with `pre-commit`, which
the briefing already records as accepted. And `git rebase`/`git cherry-pick` replay does
not run `commit-msg`, so replayed deletions are checked only by CI. Both are fail-open
windows and both are closed by the `--range` CI path before anything reaches a shared
branch.

---

## 6. Repair

Every failure mode has a repair that touches a commit message or adds a commit — **never a
live item's frozen fields, never pushed history.**

| Failure | Repair |
|---|---|
| **Wrong SHA named, not yet pushed** | `git commit --amend` the message. The `commit-msg` hook re-runs and re-verifies. Zero repo state touched. |
| **Wrong SHA named, already pushed** | **Corrective receipt**: land a new commit whose message carries `Resolves: <item path>` / `Resolved-by: <correct oid>` / `Resolved-evidence: …` / `Resolves-corrective: <oid of the bad deletion commit>`. The checker suppresses the earlier edge's finding when a later commit in the checked range carries a valid corrective group for the same item path. This is the design's mandatory escape hatch (the briefing's G1/G3 requirement: *"any solution that adds a check must ship its own escape path"*). It never rewrites history and it clears the finding permanently. |
| **SHA later rebased away** | Automatic: V2 fails → §2.9 degraded path → digest checks only → **passes**. No action required. |
| **SHA on a branch that never merges** | V3 fails (not reachable). Correct verdict — the work is not in the repo. Repair: merge the work, or land a corrective receipt naming a reachable commit. |
| **Work reverted after the item was deleted (B9/F6)** | V6(b) fails at the newest candidate → finding. This is *semantically right*: the ask is open again. Repair: re-file the item (a new item with a fresh baseline). **The finding is suppressed once the item path is live again at the newest candidate**, so re-filing clears it permanently — there is no immortal red edge. |
| **Evidence file legitimately deleted after resolution** | V6(a) treats `absent`-at-candidate as "moved off the baseline" only when the baseline was `absent`; otherwise a deleted evidence file fails V6. Same repair as above: re-file, or land a corrective receipt naming the commit that deleted it *and* declaring `Resolved-evidence: <path>=absent`. |
| **Malformed / missing trailer** | Blocked at `commit-msg`, before the commit exists. Fix the message and retry. **Strictly cheaper than today's repair**, which requires editing an immutable item field or a 2–4-commit retire-and-refile. |
| **Shallow clone, legacy item, creation commit unreachable (F8)** | V1 **fails open** with a recorded advisory. Today the equivalent read fails closed. |
| **A reconciler-filed retry about a receipt** | `generated_retry_clear` (E1) is untouched: a generated retry deletes when its named finding no longer reports. No recursion — receipts never gate generated retries. |

---

## 7. Interaction with existing invariants

| Guarantee | Verdict | Why |
|---|---|---|
| Deletion needs an act, not a label | **STRENGTHEN** | The act must now be a *named, inspectable* act carried on a second independent artifact (the commit object). `git show <Resolved-by>` is the review surface that does not exist today. |
| Active-repair proof (committed status-only claim edge) | **PRESERVE** | `claimed_lifecycle_problem` (:2655) is untouched. The receipt is additive. |
| Claim receipts are not transferable | **STRENGTHEN** | V7 forbids a receipt naming work that predates the item's filing, so a newly filed twin cannot borrow the older item's resolving commit. The frozen `Resolution baseline` gives each item its own, filing-time reference point. |
| Human responses are write-once | **PRESERVE** | The receipt lives outside the item; no human field is read or written by any new check. |
| Committed lifecycle claims never regress across merge parents | **PRESERVE** | Untouched. |
| Action identity frozen once live | **STRENGTHEN** | `Resolution baseline` joins `immutable_action_text` and `claim_identity`, so an agent cannot move its own goalposts by re-baselining after filing — the attempt is an existing "live queue action was rewritten" finding. |
| Timing may only escalate; freezes on response | **PRESERVE** | Untouched. |
| Evidence must be outside the queue | **STRENGTHEN** | `resolution_evidence_paths` is unchanged, **and** V4 extends the rule from paths to commits: a queue-only commit cannot be `Resolved-by`. |
| Review target must differ from resolution evidence | **PRESERVE** | Untouched (`negative_review_cancellation_problem` :3367 still owns it). |
| The gate cannot be turned off | **PRESERVE, with one deliberate weakening** | The v2 marker inherits the anti-downgrade check, including v2→v1. **Weakening:** receipt verification *defers* when no commit message is available (pre-commit, rebase replay). All other deletion legality — status, claim edge, boundary, successor — still runs at pre-commit exactly as today. The deferral is the price of putting the receipt where rebase and cherry-pick preserve it, and CI's `--range` closes it. |

---

## 8. Verdict table — every hard scenario

| # | Scenario | What happens under this design | Verdict | Notes |
|---|---|---|---|---|
| **1** | **B1/B2** — evidence merged 3 merges ago vs never changed; must reach opposite verdicts | **B1:** baseline (derived from creation commit) ≠ current digest → V6(a) true; receipt names `6d4e337`, reachable, modified `reconcile.py`, produced the digest, postdates filing → **PASS**. **B2:** current digest == baseline → V6(a) false → **BLOCKED**, correctly. | **EASY** | *The headline result.* The live stuck item on main resolves with three trailer lines and no synthetic edit. Opposite verdicts fall out of one digest comparison, with no history walk. |
| **2** | **D22** — item content makes its own gate unsatisfiable | The **live instance** clears: the blocking item's evidence (`automation/reconcile/reconcile.py`) has changed since filing, so it becomes deletable, the item disappears, and every session's handover projection unblocks. The **class** is narrowed but not closed: the new surface (a machine-stamped digest and a kebab-case path in a trailer) admits no human free text, and `--stamp-baseline` refuses to stamp a directory, a symlink, or a queue path — so an unsatisfiable item is rejected *at filing* rather than discovered at deletion. | **EASY** (instance) / **AWKWARD** (class) | I cannot prove no legal content is unsatisfiable; I can prove the *new* fields contain nothing an author chooses. Honest limit. |
| **3** | **D5** — live item declares a reciprocal dependency that never existed | Unchanged: `Depends on:` / `Supersedes:` / `Successor action:` remain unvalidated. But the design adds **no new unvalidated topology** — `Resolves:` is checked to equal the deleted path, and `Resolved-evidence:` is checked to equal the declared evidence set. | **AWKWARD** (unchanged) | Out of scope; noted so it is not mistaken for a fix. |
| **4** | **C6/C7** — stale 78-commit-behind branch carrying a divergent queue, merging cleanly | The branch's deletion commit carries a receipt that is **valid against its own stale parent** (its `Resolved-by` is reachable, modified the evidence, and the digest still differs from the baseline at the merged head). Replaying the edge after the merge still passes. **The design does not stop this.** What it adds: the deletion is now attributable and greppable on main — `git log --grep='^Resolves: <path>'` names the stale commit, its author, and the diff it claimed. A silent loss becomes a discoverable one. | **SILENT-CORRUPTION** (unchanged; new forensics) | The honest answer. The receipt is a claim about the *work*, and the stale branch's claim about the work is true; what is false is its claim about the *queue*, which no evidence mechanism can adjudicate. Fixing C6/C7 needs merge-result queue reconciliation, which is a different design. |
| **5** | **C8** — a rule and its first violation meeting only in the merge commit | **Partially closed, for one axis.** V6 is re-evaluated at the **newest admitted candidate** (`deletion_and_later_candidates`, :2932), not only at the deletion commit. A merge that reverts an evidence change retroactively invalidates the deletion that claimed it, and the finding surfaces on the merged result. Everything outside the evidence axis is unchanged. | **AWKWARD** (partial fix) | This is the one place the design evaluates a merged tree that nothing evaluates today. |
| **6** | **H-P1** — answered item re-asked in 19+ handovers | The item is stuck live on its *boundary receipt* (future-blocking review awaiting a merge), not on evidence, so it stays live and stays projected. Unchanged. Items stuck on **evidence** instead do clear, removing them from the projection permanently. | **AWKWARD** (unchanged) | Projection is shape-checked, not state-checked; that is a projection bug, not a resolution bug. |
| **7** | **E7/B13** — boundary crossed outside the repo while `waiting`; 3 items, ranges already ancestors of main, 3 tasks stranded in `3_in-review` | Still blocked on the missing **human response** — no evidence mechanism can answer for the human. **But the moment the human answers, cleanup is trivial**: the merges are already ancestors, V3 passes, and the digest survival check needs no fresh edit. Today those three would additionally need a synthetic evidence change on the deletion edge. | **BLOCKED on the human → EASY after** | The design removes the *second* blocker, not the first. |
| **8** | **G1/G3** — repair requires a commit the finding blocks; the repair task pinned by what it repairs | The design ships three escapes by construction: (a) receipt verification **defers** when no message is available, so it can never brick a checkout the way an evidence finding does; (b) the **degraded path** never fails closed on missing objects; (c) the **corrective receipt** repairs any pushed bad receipt forward, with no history rewrite. The only new block is a malformed trailer, repaired by editing a message before the commit exists. | **EASY** | The new check's worst case costs one message edit. Compare today's worst case: an immutable field you cannot correct. |
| **9** | **D13/D12/B5** — evidence proves a byte changed, never that work happened or who did it | Ceiling unchanged: a cosmetic commit still passes (§3). Forensics improved materially: the receipt names a commit, so `git show` gives the diff and git gives the **author**. B5 (claim by A, work by B) becomes *visible* — the claim edge's committer and `Resolved-by`'s author are both recorded and comparable — without being blocked. | **AWKWARD** (improved, same ceiling) | I claim tamper-evidence, not proof of work. Stated in the ADR text. |
| **10** | **C10/C11/B17** — queue state existing only in an uncommitted working tree | Unchanged: `live_queue_items()` still counts untracked files. One small new footgun: an untracked item with a hand-typed malformed baseline blocks that checkout — mitigated by making baseline malformation an **advisory for untracked items** and by `--stamp-baseline` being the sanctioned writer. | **AWKWARD** (unchanged) | Orthogonal scoping bug in `live_queue_items`. |
| **D1** | Wrong-but-existing evidence path | Unchanged for live items (field is immutable). For **new** items, `--stamp-baseline` cannot detect "wrong but plausible." | **AWKWARD** | Concede. |
| **D2** | Evidence path pointing into the queue | `--stamp-baseline` **refuses** a `message-queue/` path at filing (mirroring `resolution_evidence_paths`, :2714), so the item cannot be born broken. Existing broken items unchanged. | **AWKWARD → EASY for new items** | Detection moves from deletion time to filing time. |
| **D4** | Typo'd evidence path | `--stamp-baseline` writes `absent` and **warns** that the path does not exist, at filing. The agent fixes it while the item is still pre-live (legal). Existing typo'd items still need retire-and-refile. | **AWKWARD → EASY for new items** | Same shift. |
| **D10** | `blocking-` item naming `operation:` where `task:` was meant, pinning a task at `1_in-progress` | Boundary-token semantics, orthogonal. Unchanged. | **AWKWARD** (unchanged) | |
| **F1** | Rebase destroys the status-only claim edge | Claim edge unchanged by this design → unchanged failure. The **receipt** survives: the message is carried by rebase, and a dangling `Resolved-by` enters the degraded path and passes. | **AWKWARD** (claim axis unchanged) / **EASY** (receipt axis) | The receipt is strictly more rebase-tolerant than the claim edge it sits beside. |
| **F2** | Squash destroys the claim edge | Same split. Squash concatenates messages, and **whole-message parsing** (§1.3) means every group survives a squash instead of only the last paragraph's. | **AWKWARD** / **EASY** | The whole-message parse exists specifically for this. |
| **F3** | Cherry-pick | Message copied → receipt present. If the work commit was not also cherry-picked, **V3 correctly fails**: you moved a resolution without its work. Repair: bring the commit, or land a corrective receipt. | **AWKWARD** (correct but noisy) | This is the one case where the pin produces a *new* block, and I think the block is right. |
| **F5** | Reverting a deletion resurrects an item that can never be re-deleted | **Fixed.** Re-deletion needs only a receipt whose digest still differs from the baseline — which it does, because the work still stands. The same `Resolved-by` can be reused. Resolution becomes **idempotent and repeatable**. | **EASY** | Direct consequence of digest-vs-baseline replacing the one-commit byte window. |
| **F8** | Shallow clone makes lineage unverifiable; today every deletion fails closed | **Fixed for v2 items:** the baseline is a literal in the item and the candidate digest is the tree being committed — **depth-independent, zero history reads**. `Resolved-by` unresolvable → degraded path → passes. Legacy items need the creation commit; if unreachable, V1 **fails open** with an advisory. | **EASY** (v2) / **AWKWARD** (legacy) | A strict improvement over failing closed. Recording the baseline *in the item* is what buys this. |
| **G12** | Batch-filed items expiring on the same calendar date lock the repo | `stale-queue` date semantics, orthogonal. Unchanged. Mild indirect relief: items that are resolvable actually get resolved, so fewer pile up to expire together. | **AWKWARD** (unchanged) | |

**Summary:** 6 EASY, 2 EASY-for-new / AWKWARD-for-legacy, 1 BLOCKED-on-human-then-EASY,
9 AWKWARD (of which 6 are unchanged orthogonal issues and 3 are partial improvements),
**1 SILENT-CORRUPTION (C6/C7, unchanged)**.

---

## 9. Three strongest objections to this design

### Objection 1 — "The receipt only relocates the forgery. Naming a whitespace commit still launders, and now honesty costs two commits instead of one."

**Conceded on prevention; contested on the rest.**

I concede completely that a launderer can commit a space, name that commit, and pass every
check — including Tier A, at the cost of one extra line. This design **does not prevent
laundering** and I will not let it be described as if it does; the briefing is explicit
that a strict-*looking* mechanism creating false confidence is worse than a lenient one.

What I contest is the second clause. Honesty does **not** cost two commits — it costs
**three trailer lines emitted by `reconcile.py --receipt <item>`**, and it applies to work
that already merged, which today costs *infinity* (the item is permanently unresolvable).
Laundering is what now costs an extra commit, and that commit is a permanent, authored,
timestamped, greppable statement whose entire diff is a whitespace change. The asymmetry
runs the right way for the first time: the honest path gets cheaper, the dishonest path
gets more expensive **and attributable**.

And the design produces an artifact that does not exist today: the answer to "what
resolved this?" is a commit oid you can `git show`, not an archaeological dig through a
deletion diff. That is the whole of what tamper-evidence means in a repo with a bypassable
hook and one shared identity.

### Objection 2 — "You made commit SHAs load-bearing in a repository whose own workflow rewrites them, then defanged the check so it survives that. The pin is decorative."

**Substantially conceded.** The honest statement of this design is: **the digest is the
invariant; the commit pin is provenance.** Under §2.9, an agent that writes
`Resolved-by: 0000…0` gets digest-only checking — so an adversary can opt out of the pin
at will, and the mechanism degrades to "the evidence differs from its filing baseline."

Three defences, in decreasing strength:

1. **Degrading is strictly better than the alternative.** Failing closed on an
   unresolvable SHA converts every rebase, every squash, and every shallow clone into a
   repo-wide brick — precisely the failure class (F8, G1/G3) the briefing names as
   disqualifying. A check that bricks on legitimate git operations will be bypassed with
   `--no-verify`, which the briefing records as already happening on four `exp/*` branches.
2. **Opting out buys the adversary nothing.** A determined launderer's easier path is a
   *fully valid* Tier B receipt naming a real whitespace commit. Closing the dangling-SHA
   hole would tax only honest history rewriting.
3. **When the pin resolves — which is the overwhelming case, since this repo forbids
   squash-merging task branches and rewriting pushed history — it verifies four facts the
   digest alone cannot**: reachability from the deletion, that the commit is not the
   deletion itself, that it is not queue-only, and that it postdates the filing. That last
   one (V7) is what makes claim receipts non-transferable across twin items, a listed
   invariant that a pure digest comparison would *weaken*.

I offer `receipt.strict-pin` as an opt-in for a repository that never rewrites history and
would rather brick than degrade. It is off in core, because core must work in adopted
repositories whose workflows I do not control.

### Objection 3 — "You added a second git hook and a schema version bump to a system that already bricks itself on activation edges. The migration is the risk, not the mechanism."

**Partly conceded — this is the highest-variance part of the design.** Four structural
mitigations, then the residual risk stated plainly:

1. **The hook needs no installation step.** `install.py` sets
   `core.hooksPath automation/hooks`, a *tracked directory*. `automation/hooks/commit-msg`
   activates on `git pull` for every clone that ever ran `install.py`. There is no
   half-migrated population.
2. **No live item is edited.** Legacy baselines are *derived*, never written. An edit-based
   migration would trip `queue_mutation_problem` on all 41 items simultaneously — the exact
   D22 trap — and would be unrecoverable. Derivation is forced by the existing invariants,
   which is the best kind of migration constraint.
3. **The requirement is not retroactive.** Deletions before the v2 activation commit are
   checked under v1 rules forever, following the repo's own stated rule for grammar changes.
   The 45 historical deletions replayed by `--range root:HEAD` cannot newly fail. (That run
   already reports 55 findings; this design must not and does not add to them.)
4. **Every new failure is repairable without touching repo state or history**: amend the
   message pre-push, land a corrective receipt post-push.

**Residual risk I do not have an answer for:** a clone that never ran `install.py` has no
receipt gate at all, and `git rebase`/`git cherry-pick` replay does not fire `commit-msg`,
so replayed deletions reach a branch unverified. Both windows are closed only by CI's
`--range` path — which means, exactly as the briefing predicted for idea 5, **the periodic
full-range sweep is the real enforcement and the hook is an early warning**. If that CI
path is not run on every push to a shared branch, this design's local guarantees are
advisory. I would rather say that out loud than let the `commit-msg` hook imply a gate it
does not deliver.

---

## 10. Worked example — the live stuck item, verified end to end

`message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
is the item the briefing calls permanently unresolvable. Every value below was computed
against the repo at `38f7bb3`, not estimated:

| Quantity | Value |
|---|---|
| Item creation commit | `b4c1ec5e9184824404db58b4ba45aa3bbd2bdad6` |
| **Baseline** — `sha256(automation/reconcile/reconcile.py @ b4c1ec5)` | `6a351d8cf4b22a91c9a3e8e63d0964c4fed7bb55e3803c06eb282842bd2a24fe` |
| Work commit `C` | `6d4e337c3c3b3b795f4de6486198791023be7e83` — *"fix: render code spans on both sides of the handover copy check"* |
| `sha256(reconcile.py @ C^)` | `6a351d8c…` — **identical to the baseline**: the evidence was untouched from filing until `C` |
| `sha256(reconcile.py @ C)` | `b2e78f67015ca8298a3c6f92d50e736b65064813a4fe639c86cba5dd80f60d5f` |
| `sha256(reconcile.py @ HEAD)` | `a5d690aae0afec3e707ac27fbe2941804b5fcac99faf768e5bb7e88f1b4c4474` |
| `C` touches outside `message-queue/`? | yes — 3 files, 127 insertions |
| `C` reachable from HEAD? | yes |
| `C` predates the item's filing? | no |

Check-by-check: **V2** `C` exists. **V3** ancestor of HEAD. **V4** not the deletion, not
queue-only. **V5** `b2e78f67… ≠ 6a351d8c…` — `C` really changed the declared evidence, and
produced exactly the declared digest. **V6(a)** `a5d690aa… ≠ 6a351d8c…` — the evidence has
moved off its filing baseline. **V6(b)** `a5d690aa… ≠ 6a351d8c…` — `C`'s change was never
reverted. **V7** `C` postdates `b4c1ec5`. **All pass.**

The resolving commit needs exactly this in its message:

```
Resolves: message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
Resolved-by: 6d4e337c3c3b3b795f4de6486198791023be7e83
Resolved-evidence: automation/reconcile/reconcile.py=sha256:b2e78f67015ca8298a3c6f92d50e736b65064813a4fe639c86cba5dd80f60d5f
```

No synthetic edit, no touched byte, no ceremony beyond three generated lines — and the
item that has been blocking **every session's handover ritual** since 2026-07-25 goes away.
Under the current rule the same item requires appending a space to `reconcile.py`, which is
the laundering the briefing proved works.

Note the contrast the design turns on: `sha256(reconcile.py @ C^)` equals the baseline
exactly. The one-commit window is *blind* to this — it can only ask whether the file
changed on the deletion edge, and the answer is no. The baseline comparison sees the same
history and answers correctly, from two digests and no history walk at all.

---

## 11. Implementation order (smallest shippable increments)

1. **C1 — persistent `cat-file --batch-check` reader** and rewrite `git_tree_blob_entry`
   on top of it. Independently valuable; removes most of the 135 s of system time in
   `--range root:HEAD`. Ship and measure before anything else.
2. **`--stamp-baseline`, `--receipt`, `--audit`** as read-only/tooling commands, plus the
   template field. No enforcement. Agents start producing baselines and receipts.
3. **`resolution_receipt_problem`** behind the v2 marker, `--check-receipts`,
   `--message-file`, and `automation/hooks/commit-msg`. Legacy items derive; pre-v2
   deletions keep v1 rules.
4. **C2 (commit graph) and C3 (verdict memo)** once the check exists and its cost is
   measurable rather than estimated.
5. **ADR** in `memory/decisions/` superseding
   `2026-07-23-queue-resolution-preserves-review-intent.md`, stating the ceiling in the
   same words as §3: this proves that a named change landed and survives, not that the
   work was done or who did it.
