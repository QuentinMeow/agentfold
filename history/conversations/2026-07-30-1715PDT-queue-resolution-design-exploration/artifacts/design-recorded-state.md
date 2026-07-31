# Design — Resolution is a recorded state, not a deletion

**Author:** design agent (philosophy: *recorded terminal state + derived liveness + mechanical compaction*)
**Repo:** `/Users/quentinmiao/code/ai-harness`
**Target:** replace `resolution_evidence_problem` / `queue_deletion_problem` adjudication with a recorded-state model
**Status:** proposal — implementable as written

---

## 0. The one-paragraph version

Today an item's existence *is* its pendingness, so resolution is deletion, so an
irreversible destructive act has to be adjudicated by a hook at the exact instant it
happens, against a one-commit-wide window. Every failure in the briefing is a corollary.
This design separates the three things that are currently fused: **(a) the item's ask**
(spec, frozen once live), **(b) the item's disposition** (an append-only `## Resolution
log` inside the same file, which is the new authoritative state), and **(c) the file's
physical existence** (compaction, a later mechanical step gated only by a lookup). The
checker stops adjudicating destruction and starts *computing derived status*: `live` =
a tracked queue item whose resolution log has no terminal verdict. Physical deletion
needs no proof of work because the proof is already a committed record; it needs only a
**tombstone** — an in-tree line naming the path, its terminal state, the resolving commit
and the sha256 of the final bytes.

Two properties do the heavy lifting and both come from choosing *content* over
*topology*:

1. **Every check becomes tree-local.** A tombstone is a file, not a commit relationship.
   That is why this design survives shallow clones (F8), rebase, squash and cherry-pick
   (F1/F2/F3), and why it can afford to be evaluated on a merge *result*.
2. **Every state transition is an append.** The merge rule is therefore
   *"each parent's resolution log must be a subsequence of the candidate's"* — one
   O(lines) string operation that is order-independent, conflict-honest, and attacks the
   stale-branch scenario (C6/C7) directly.

---

## 1. The state model

### 1.1 Two axes, not one

| Axis | Field(s) | Semantics | Mutability |
|---|---|---|---|
| **Spec** — what is being asked | `Action`, `Full context`, `Why-you-might-care`, `If-you-do-nothing`, body sections | the ask | frozen once live (unchanged from today) |
| **Delivery** — where in the pipeline | `Status:` (`open`/`in-repair`, `awaiting-artifact`/`waiting`/`folding`), timing prefix + `Blocks *` | who owes what next | monotone (unchanged from today) |
| **Disposition** — how it ended | `## Resolution log` (authoritative) + `**Resolution:**` (checked cache) | terminal or not | **append-only** |

This is Kubernetes `spec` vs `status`. Today the repo has spec and delivery but no
disposition, so disposition is encoded in a *file-system fact* (present/absent) that
cannot be appended to, cannot carry a reason, cannot be merged, and cannot be corrected.

### 1.2 The resolution log

Every queue item may carry, as its last `##` section:

```markdown
## Resolution log

- 2026-07-28 `done` by claude — anchor `commit:6d4e337...`; `check:handover-queue-projection`
- 2026-07-29 `reopened` by codex — the repair was reverted in `4a1b2c3`
- 2026-07-30 `obsolete` by codex — the projection check was replaced wholesale by v2
```

Grammar, one line per event, checked by one regex:

```
- <YYYY-MM-DD> `<verdict>` by <actor> — <detail>
```

`verdict ∈ TERMINAL ∪ {reopened}`. **Derived state = the verdict on the last line.**
`reopened` is not terminal, so a reopened item is live again. The log is never rewritten;
history is the log.

`**Resolution:** <verdict|none>` sits with the other bold-key fields near the top. It is
a **generated cache** of the log's last verdict, in the same sense that `memory/index.md`
is generated from `**Description:**` fields — the reconciler enforces equality and
`--fix-resolution` regenerates it. Two representations are justified here for the same
reason the repo already accepts filename-prefix ⟷ `Blocks *` redundancy: one is for
grep/projection/eyeballs, one is for the machine, and a check binds them.

*(Variant if the redundancy is judged unacceptable: drop the field, make projection and
`live_queue_items()` parse the log's last line. Costs one extra regex per item read;
loses greppability. The design is otherwise identical.)*

### 1.3 The terminal states

| Verdict | Meaning | Required evidence | Cost to record |
|---|---|---|---|
| `done` | the requested work was performed | ≥1 **anchor**, of which ≥1 must be a *state* anchor (§1.4) | one line + one anchor |
| `answered` | (needs-human) a concrete response exists and was folded into a durable non-queue artifact | ≥1 state anchor naming where it was folded; plus a committed concrete response | one line + one anchor |
| `superseded` | a named successor item now owns this action | `Resolution ref:` naming a live item that points back with `Supersedes:` | one line + reciprocal link |
| `duplicate` | another item (live *or* tombstoned) already carries this action | `Resolution ref:` resolving to a live path or a tombstone | one line + one link |
| `rejected` | the receiving actor declines to do it | one concrete reason sentence | **one line** |
| `withdrawn` | the filer retracts their own ask | one concrete reason sentence | **one line** |
| `obsolete` | the world changed; this is no longer relevant | one concrete reason sentence | **one line** |

Three of the seven — `rejected`, `withdrawn`, `obsolete` — require **no git archaeology,
no second file, no boundary, no ordering**. That is deliberate and it is the single most
important calibration in this design. The briefing warns that if "no longer relevant" is
expensive, agents manufacture work to satisfy the gate. It is not merely cheap here; it
is the *cheapest path in the system*, cheaper than `--no-verify`, and it is the design's
declared break-glass (see §7.6 and §10.1).

Two hard restrictions keep cheapness from eating the one irreplaceable thing:

- **`obsolete`/`withdrawn` are forbidden on a `needs-human` item that already carries a
  concrete committed response.** If the human answered, the only legal terminals are
  `answered`, `done`, or `superseded`. You may not make an answer you already have go
  away. (Check: `first_concrete_response(...) is not None` ⇒ reject those verdicts.)
- **A `needs-human` item that reaches `obsolete`/`rejected`/`withdrawn` *without* ever
  receiving a response emits a `queue-unanswered-closed` advisory** and appears in the
  next handover's `## Resolved since last handover` list. The human sees, once, every ask
  to them that was closed without their answer, with its reason. That visibility is the
  accountability substitute for a gate that the briefing proves cannot work anyway.

### 1.3a Who may record which verdict

The actor recorded on the log line is self-declared (one shared identity — the briefing
puts authentication out of scope), but *authority per verdict* is still checkable from
repository state and is worth encoding, because it is what stops the cheap states from
eating the expensive ones.

| Verdict | Who may record it | Checkable precondition |
|---|---|---|
| `done` | the actor who holds the claim | `Status` is `in-repair`/`folding` in the parent tree |
| `answered` | any agent | a concrete human response is committed |
| `superseded`, `duplicate` | any agent | `Resolution ref:` resolves |
| `rejected` | the **receiving** actor only — an agent may reject a `needs-agent` item; only a human response may reject a `needs-human` ask | for `needs-human`, requires a concrete response; otherwise use `obsolete` |
| `withdrawn` | the filer, or the owner | — |
| `obsolete` | any actor | **forbidden** once a concrete human response exists |

The line that matters: **an agent cannot `reject` a human's ask.** It may record that the
ask became `obsolete`, which is a different and visibly weaker claim, and which triggers
`queue-unanswered-closed`. Today an agent can simply delete the file.

### 1.3b The highest-volume path: reconciler-generated retries

`--file-retries` files repair items for findings and garbage-collects them when the named
finding clears. That is by far the highest-volume resolution path in the repo, and it must
not become ceremonial. Under this design the reconciler, resolving its own generated
items, appends `done` with a `check:<id>` anchor **and may compact in the same run**,
bypassing the 14-day window. The exception is principled rather than convenient: the
reconciler *is* the generator, the anchor is machine-verified against the exact candidate
tree at that instant (this is E1 `generated_retry_clear`, which the briefing calls "a
genuine level-triggered predicate [that] already works"), and the tombstone is still
written. Nothing is unrecorded; only the delay is waived.

### 1.4 Anchors — level-triggered predicates replacing "the evidence file changed"

`Resolution anchor:` takes one or more `;`-separated expressions from a closed grammar.
**State anchors** assert a predicate over the candidate tree. **Landing anchors** assert
that an event is present in admitted history.

| Kind | Expression | Evaluated by | Detects a revert? |
|---|---|---|---|
| state | `digest:<repo-path>@sha256:<64hex>` | one blob read + hash | ✅ |
| state | `contains:<repo-path>#<heading-slug>` | one blob read + heading scan | ✅ |
| state | `absent:<repo-path>` | one index lookup | ✅ |
| state | `check:<check-id>` | re-run that check against the candidate tree, no finding for this subject (generalises E1 `generated_retry_clear`) | ✅ |
| state | `task:<task-id>@<status-folder>` | one path lookup (generalises E2/E5) | ✅ |
| landing | `commit:<full-oid>` | `git merge-base --is-ancestor` (generalises the whole B1/B2 class) | ❌ |
| landing | `merge:<full-oid>` | two-parent merge already in the adapter-supplied admitted base (generalises E4) | ❌ |
| attested | `transition:<name> attested-by:<actor>` | not verifiable; **labelled as attestation everywhere it is shown** | ❌ |

Design rules:

- **`done` requires at least one state anchor**, except for a merge-boundary review where
  the landing *is* the thing being asserted. This is what makes the audit sweep (§5.3)
  able to notice a reverted repair.
- Anchors are written **at resolution time**, by an actor who can see reality. They are
  not predeclared. This is what kills D1/D2/D4 (§7.3).
- Anchors may name paths that do not exist (`absent:`), so `check_links` must strip
  `Resolution anchor:` and `Resolution ref:` lines under `message-queue/` exactly as it
  already strips `Resolution evidence:` (`reconcile.py:7143`).
- Anti-gaming: `\n# probe\n` appended to a file satisfies today's check. It satisfies
  **none** of `digest:` (exact bytes), `contains:` (a named heading), `check:` (a real
  finding must clear), `task:@status` (a real lifecycle move), or `absent:`. That is the
  briefing's own anti-gaming criterion, met.
- Anchor evaluation is **memoised and bounded** so it cannot become the new compounding
  term in a full-history replay — see §5.5, which is load-bearing, not an optimisation.
- The old `Resolution evidence:` field survives as an **advisory expectation** — the
  machine-shaped half of `## Done when`. It is not load-bearing and is correctable while
  live (§7.3).

### 1.5 What "cheap" means, concretely

| Action | Commits | Files touched | Git calls added to the gate |
|---|---|---|---|
| mark `obsolete` | 1 | 1 | 0 |
| mark `done` with `contains:` | 1 | 1 | 1 blob read |
| mark `done` with `commit:` | 1 | 1 | 1 `merge-base --is-ancestor` |
| reopen a wrongly-terminal item | 1 | 1 | 0 |
| compact 12 eligible items | 1 | 13 (12 deletions + 1 manifest) | 12 blob reads already paid |

---

## 2. Where the state lives

**Decision: in the item file itself.** Rejected alternatives and why:

| Option | Verdict | Reason |
|---|---|---|
| Git notes | **rejected** | not fetched by default, not merged, absent in a fresh clone. Violates the fresh-clone constraint outright. |
| Commit trailers | **rejected as primary** | topological: destroyed by squash/rebase/cherry-pick (F1/F2/F3), and deriving state requires a history walk — the exact cost this design exists to remove. Retained only as an optional corroborator in commit messages. |
| One sibling ledger file (`message-queue/ledger.md`) | **rejected** | every resolution writes the same file. This violates `handbook/git-workflow.md`'s "**one item, one file** — concurrent agents create files, never edit shared ones," and turns every parallel resolution into a merge conflict on unrelated lines. |
| A `resolved/` directory (move the file) | **rejected** | see below |
| **In the item file** | **chosen** | see below |

### 2.1 Why not `resolved/`

1. **A move is a rename, and rename semantics on a stale-branch merge are the failure
   mode we are trying to fix.** Concretely: main moves `A → resolved/A`; a stale branch
   still has `A` live and edits it (escalates its timing). Git's rename detection applies
   the branch's edit to `resolved/A`. A *live edit silently lands on a resolved item* at
   a path where no liveness check looks. In-place, the same merge produces one file
   holding both the branch's timing edit and main's resolution log entry, and the
   monotonicity and log-subsequence checks both see it.
2. **The path is the routing identity.** `message-queue/AGENTS.md` defines three axes —
   actor folder, typed leaf, filename prefix — and states that extra nesting is invalid.
   `valid_queue_item_path`, `governed_queue_path`, `queue_document_path`,
   `split_live_queue_entries`, `HANDOVER_HUMAN_LINK_RE` and `queue_item_owned_by_task`
   all key on a 4-part path. A `resolved/` subtree either destroys those axes or clones
   the whole tree shape, and touches every path predicate in a 7,700-line file.
3. **It buys only cosmetics.** `live_queue_items()` would still have to read `resolved/`
   to enforce anything about it.

### 2.2 The four evaluation criteria

**Merge behaviour on a stale branch (scenario 4 — the hardest case).**

The invariant is: *for every parent P of the candidate C, P's resolution-log line
sequence must be a subsequence of C's*, for every queue path present in both. Cost:
O(lines), pure string work, no git beyond the blob reads the code already performs on
each edge.

- Main appends `done`; stale branch untouched → git takes main's file → C's log ⊇ both
  parents' → **pass**.
- Main appends `done`; stale branch escalates timing → 3-way merge keeps both hunks →
  **pass**, correctly (a terminal item with escalated timing is harmless).
- Stale branch reverts main's resolution (branch's shorter log wins some hunk) → main's
  log is **not** a subsequence of C's → **finding on the merge result**. Today the
  analogous revert of a review state is caught only by
  `queue_parent_state_regression_problem`, and only for `Status`; the log rule is
  strictly broader and covers reasons, anchors and actors too.
- Stale branch *deletes* a live item with no tombstone → §3.3 accounting → **finding on
  the merge result**. Today: clean merge, no finding on either head. **New detection.**
- Stale branch resurrects a path that main compacted → C's tree contains both the
  tombstone for that path *and* a live file at it → **finding** ("compacted path is live
  again"). This is exactly a Kafka tombstone-vs-record collision, and it is another new
  detection.

**Two agents resolving concurrently.** Both append to the same section of the same file
⇒ a textual conflict in the same hunk. Loud, at the right place, with both intents
visible. Compare today: both `rm` the file ⇒ **clean merge**, one intent silently lost.

**Fresh clone.** Everything is tree content. Nothing needs reflog, notes, or depth.

**"Append, don't clobber."** The log is the literal implementation of that contract:
`resolution_log_append_problem(before, after)` is a prefix/subsequence check. It is the
first place in the repo where the contract is *mechanised* rather than instructed.

---

## 3. Compaction

### 3.1 Eligibility (all clock- or tree-local, no history walk)

An item is compaction-eligible when:

1. its last log verdict is terminal, and
2. `TODAY - <date of that line> ≥ COMPACT_AFTER_DAYS` (default **14**), and
3. its terminal record is **published** — the commit that introduced it is an ancestor of
   the adapter-supplied admitted base (reusing the existing admitted-base machinery from
   `approved_review_merge_receipt_problem`). One `merge-base --is-ancestor` per item.
   Without a trusted base (plain local hook), this degrades to "the record is committed
   on the current branch's upstream" and compaction is advisory-only locally.

Condition 3 is what stops file-and-erase inside one branch: you cannot create an item,
mark it `obsolete`, and compact it away in the same unpublished sequence.

### 3.2 The act

`python3 automation/reconcile/reconcile.py --compact` — mechanical, idempotent, and
**re-verifies every anchor level-triggered against the current tree before removing
anything.** If an anchor no longer holds, it does *not* compact; it appends a `reopened`
line with the reason `anchor no longer holds: <expr>` and files a retry. That is
scenario B9/F6 handled by construction rather than by exception.

For each item it removes, it appends one line to `message-queue/compacted/<YYYY-MM-DD>-<runid>.jsonl`:

```json
{"path":"message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md",
 "state":"done","resolved":"2026-07-28","by":"claude",
 "sha256":"<64hex of the file's final bytes>",
 "commit":"<oid that committed the terminal record>",
 "anchors":["merge:9f4d364..."]}
```

One file **per run**, so parallel compaction runs never conflict. JSON per line, so no
delimiter can be poisoned by item content (a direct application of the D22 lesson, §7.5).

*Implementation detail that is easy to miss and would brick the repo if missed:*
`check_queue_location` (`:3806`) requires every live queue path to sit under exactly one
actor folder and one typed leaf, and `queue_document_path` (`:1053`) whitelists only the
root contracts and typed-leaf `README.md` files. `message-queue/compacted/*.jsonl` matches
neither, so it must be added to `queue_document_path`'s whitelist (or given its own
predicate) in the **same commit** that creates the directory. `governed_queue_path`
(`:1068`) must likewise not treat a tombstone file as action state, or compaction would be
reported as an unresolved deletion of itself.

Who runs it: any agent. Natural home is `skills/memory-gardener/` — the repo already has
a "forgetting pass" ritual that re-verifies, compacts and prunes, and this is exactly
that shape. The session-handover skill gains one line: *if `--compact --dry-run` lists
anything, run it.*

### 3.3 The deletion-accounting check (what replaces `queue_deletion_problem`)

On each governed edge, for each parent `P` and candidate `C`:

```python
for path in queue_paths(P) - queue_paths(C):
    tomb = tombstones(C).get(path)            # one tree-dir read per candidate, cached
    if tomb is None:
        yield finding("queue item removed with no compaction tombstone")
    elif tomb["sha256"] != sha256(bytes_at(P, path)):
        yield finding("tombstone does not match the removed bytes")
    elif last_log_verdict(text_at(P, path)) not in TERMINAL:
        yield finding("compacted an item whose record is not terminal")
```

`bytes_at(P, path)` is already fetched today by `queue_deletion_events`
(`reconcile.py:1646`). So the accounting adds **zero git calls** relative to today, and
removes: two blob reads per declared evidence path, the `claimed_lifecycle_problem`
history stack walk, `deletion_and_later_candidates`, and the review-cleanup boundary
replay. See §5.4.

### 3.4 If compaction never runs

Nothing breaks. `live_queue_items()` filters terminal items out, so `queue-name`,
`queue-location`, `queue-schema`, `stale-queue`, `queue-boundary`,
`queue-task-reciprocity` and the handover projection all ignore them automatically. The
only cost is one small-file read per terminal item per reconciler run.

**Unbounded growth?** Bounded in practice and harmless in principle. Current corpus: 48
files. Observed resolution rate implies a few hundred per year at ~2–4 KB each — order
1 MB/year of tree, which git deltas to far less. At 400 terminal items the added read
cost is ≈0.1 s. The reconciler emits a **non-blocking** `queue-compaction` advisory once
terminal items exceed 100. Deliberately non-blocking: a hygiene backlog must never brick
the repo (that is scenario G1/G3's whole lesson).

### 3.5 Archaeology: "what happened to item X"

1. File still present → read it. The log *is* the answer. **No archaeology.**
2. Compacted → `grep -r <slug> message-queue/compacted/` gives state, date, actor,
   anchors, resolving commit and content hash, **from the current tree**.
   `git show <commit>:<path>` retrieves the exact bytes; the recorded sha256 verifies
   them.
3. `reconcile.py --explain <slug>` does 1–2 automatically.

Compare today: `git log --diff-filter=D --follow -- <path>` to find the deletion, then
read a commit message that may say anything. This design is Fossil's reconstructible
ticket table: the tombstone is a durable in-tree index; the bytes are reconstructible
from git and *verifiable by hash*.

---

## 4. The projection problem (scenario 6, H-P1)

### 4.1 Why the bug exists

`live_human_queue_paths()` (`reconcile.py:5959`) returns every readable item under
`needs-human/`, and `check_handover_queue_projection` requires
`set(projected_human) == live_human` (`:6971`). There is no state to consult, because
under "resolution IS deletion" the only state is presence. So an item that has been
`folding`/`approved` since 2026-07-24 is re-asked in 19+ handovers.

### 4.2 Two independent fixes, both enabled by explicit state

**(a) Terminal items are not live.**

```python
def live_queue_items():
    ...  # unchanged enumeration
    # then, for each candidate item:
    if terminal_verdict(text) is not None:
        continue
```

Every downstream check inherits this for free.

**(b) Route by *derived next actor*, not by folder.** `needs-human/` says who acts next
*at filing time*. Once the human has answered, `Status: folding` means **the human is
done and an agent owes the fold**. Projecting it under "Needs your attention" is a bug
independent of terminality.

```python
def derived_actor(path, text):
    if terminal_verdict(text) is not None:      return None
    actor = Path(path).parts[1]
    if actor == "needs-human" and status(text) == "folding" \
            and first_concrete_response(human_response_fields(text)):
        return "needs-agent"                    # fold owed
    return actor
```

`live_human_queue_paths()` = items whose `derived_actor == "needs-human"`. This fixes
H-P1's *observed* case immediately, before any item reaches terminal.

Guard so nothing falls silent: a new **`queue-fold`** finding — a `folding` item with a
concrete committed response older than `FOLD_DEADLINE_DAYS` (default 7) — which auto-files
a blocking retry via the existing `--file-retries` path. The obligation moves; it does not
evaporate.

### 4.3 Immutable already-written handovers

Nothing retroactively invalidates. `check_handover_queue_projection` re-checks historical
handovers by re-running itself inside `git_revision_candidate(revision)` at the handover's
**creation commit** (`:6564`). At that tree, the item's log had no terminal line and
`Status` was whatever it was then, so the old projection still validates. The property is
not luck: it holds precisely because terminal state is *recorded in the tree at a commit*,
so "was it live then?" is answerable at that tree. The 60 existing conversation folders
need no edit, and `history/AGENTS.md`'s freeze on pre-existing handovers is untouched.

### 4.4 Schema version bump

The set of items a new handover must project changes, and a v1 handover written *after*
activation would demand projecting terminal items. Per `history/AGENTS.md` ("a newly
rejecting grammar needs a new version instead of retroactive validation"), this needs:

- `history/AGENTS.md`: `**Queue projection schema:** v2` (v1 records keep v1 semantics).
- `templates/handover.md`: `**Queue projection:** v2`, and one new optional section:

```markdown
## Resolved since last handover

<One line per needs-human item that reached a terminal verdict since the previous
handover: `[<Action>](<queue path>)` — `<verdict>`: <reason or anchor>. `None.` when
there were none. This section is a receipt, never an ask.>
```

That section is what makes a cheap `obsolete` *visible* rather than silent, and it is
where `queue-unanswered-closed` surfaces. It is checked for shape only — **no check may
require copying resolution prose byte-for-byte** (§7.5).

---

## 5. What the pre-commit hook still checks

### 5.1 Retained (all tree-local or single-blob)

1. **Log well-formedness** — line grammar, closed verdict vocabulary, `Resolution:` cache
   equals the log's last verdict, required companions present per verdict (§1.3).
2. **Append-only / no regression** — for each parent, its log is a subsequence of the
   candidate's; existing `queue_parent_state_regression_problem` extended to cover
   `Resolution:`. Pure string work.
3. **Anchors hold now** — level-triggered, evaluated only for items whose log *changed on
   this edge* (incremental) and fully in `--audit` (§5.3).
4. **Deletion accounting** — §3.3. One tombstone-dir read per candidate.
5. **Action identity frozen while live** — unchanged (`queue_action_identity`).
6. **Timing monotone while live; frozen on response** — unchanged.
7. **Claim before terminal** — the item's `Status` must already be `in-repair`/`folding`
   **in the parent tree** of the edge that appends the terminal line. This is the
   existing "active-repair proof", but read from *content in the parent* rather than
   found by walking a claim-edge stack — which is why it survives rebase and cherry-pick
   (§9, F1/F3).
8. **Schema anti-downgrade** — `Queue resolution schema: v2` sticky, same machinery as v1;
   plus a missing `message-queue/compacted/` directory after activation is itself a
   finding.

### 5.2 Removed

`resolution_evidence_problem` (the two-blob diff, `:2722`); the deletion-path invocation
of `claimed_lifecycle_problem`'s multi-parent stack walk (`:2655`); `pickup_completed`'s
task-snapshot walking (`:1892`, becomes `task:<id>@1_in-progress`);
`review_cleanup_boundary_problem`'s `deletion_and_later_candidates` replay (`:3417`,
becomes `merge:<oid>` + one ancestry probe); `generated_retry_clear` (`:2851`, becomes the
`check:` anchor — E1 generalised rather than special-cased). **E1–E6 stop being escapes
and become five anchor kinds.** The strictness gradient stops tracking timing prefix
(today: a `blocking-` request whose work merged is permanently stuck while a non-blocking
approved review deletes for free) and starts tracking *kind of claim*: asserting work
happened costs an anchor; asserting irrelevance costs a reason.

### 5.3 The audit sweep — and why it is not "deferral"

`reconcile.py --audit` re-derives every live claim: re-evaluates every terminal item's
anchors against current HEAD, reports anchors that no longer hold, reports per-actor
`obsolete`/`withdrawn` rates for the last 30 days, and lists compaction-eligible items.
Runs on the default branch in CI and on demand. Cost on today's corpus: well under 1 s.

ADR `2026-07-30-commit-gate-skips-only-on-proof.md` forbids skipping a check because a
later boundary will run it. This design does not skip anything. The hook checks
**everything decidable from the candidate**, including every anchor that changed on the
edge. The audit answers a different question the hook *cannot* ask — "does a claim made
in an earlier commit still hold?" — which is not a fact about the commit being made. Both
layers are proof-about-the-present. There is no deferral.

### 5.4 Cost — measured, not asserted

All numbers measured on this repo today — 317 commits, 48 queue files, CPython 3.7.6,
macOS 26.5.2, x86_64, 8 physical cores, warm page cache — from a harness that imports
`reconcile.py` and times each `CHECKS` entry individually (left at
`tmp/time_checks.py`, git-ignored, so the before/after comparison is reproducible).
Absolute values will differ on other machines and interpreters; the *ratios* and the
*rank ordering* are the load-bearing part.

| Mode | Total | `queue-resolution` | Rank | Dominant terms |
|---|---|---|---|---|
| `--check`, staged, clean tree | **7.89 s** | **0.40 s** | 4 / 19 | `handover-queue-projection` 4.95 s, `link-check` 1.25 s |
| `--range` over 20 commits | **77.63 s** | **4.11 s** | 4 / 19 | `task-action-origin` 31.08 s, `task-admission` 21.56 s, `handover-queue-projection` 18.18 s |
| `--range root:HEAD` | **525.08 s** | **103.87 s** | **3 / 19** | `task-action-origin` 199.66 s, `task-admission` 113.43 s, `handover-queue-projection` 104.63 s |
| `python3 -m unittest automation.tests.test_reconcile_queue` | **150.03 s** | — | — | 302 tests, 12,946 lines, 54 % of the repo's test LOC |

**A third datum worth stating plainly: `--range root:HEAD` on `main` today reports 55
findings** — 1 `queue-resolution`, 38 `task-admission`, 16 `handover-queue-projection` —
in 8 m 45 s. The repo's own full-history admission path is red and has been for some time,
and the one `queue-resolution` finding is *unfixable by the rules that produced it* (§6.4).
That is not an argument against the current design so much as evidence for the briefing's
central claim: a strict-looking mechanism that is too expensive to run, and that the
repository's own history does not satisfy, provides *false confidence* rather than
assurance. Any replacement has to be cheap enough that the full-corpus sweep actually runs,
**and repairable forward when it finds something**.

**A correction and a confirmation of the briefing.** The briefing states "the queue check
is already the slowest thing in the repo: 92–312 seconds for the queue file alone." Two
distinct things are true and it is worth separating them, because they point at different
work:

- *Correction:* at commit time the `queue-resolution` **check** costs **0.40 s** — 5 % of a
  7.89 s reconciler run. The 92–312 s figure matches the **test file**
  `automation/tests/test_reconcile_queue.py`, measured here at **150.03 s** standalone. At
  the pre-commit boundary the gate's cost is overwhelmingly the suite, not the check.
- *Confirmation:* over `--range root:HEAD`, `queue-resolution` costs **103.87 s** — right
  inside the briefing's band, and the joint-slowest check in the repo. The briefing's
  warning about compounding is correct; it just lands on the CI first-push path rather
  than on the commit path.

That 103.87 s is *specifically the deletion adjudication compounding per edge*. Root-range
replay pays, for every governed edge and every deletion on it: two blob reads for
`resolution_evidence_problem`; a predecessor BFS in `claimed_lifecycle_problem` with
`queue_lineage_snapshots`; `deletion_and_later_candidates` walking every descendant for
review cleanup; task snapshots for `pickup_completed`; and — worst of all —
`generated_retry_clear`, which re-runs an **entire reconciler check** inside
`git_revision_candidate` for each retry deletion. Every one of these is removed or bounded
by this design.

Projected costs:

| Mode | Today | Projected | Why |
|---|---|---|---|
| staged, clean tree | 0.40 s | ~0.45 s | +1 tombstone-dir read, +N field reads |
| staged, 1 queue deletion | 0.40 s + 2 blob reads + a predecessor BFS | ~0.45 s | tombstone set already loaded; parent bytes already fetched ⇒ **0 new git calls, 2 fewer blob reads, 1 fewer history walk** |
| `--range` 20 commits | 4.11 s | ~1.5–2.5 s | removes per-deletion blob diffing and per-edge lineage snapshots |
| `--range root:HEAD` | **103.87 s** (of a 525.08 s run) | **~10–20 s** | removes all five compounding terms above; per-edge work becomes a set difference plus a cached tombstone lookup |

The `root:HEAD` projection is the design's strongest quantitative claim and also its most
uncertain; §11 makes measuring it a merge precondition.

### 5.5 Bounding anchor evaluation so it cannot become the new compounding term

The one way this design could reintroduce the 103.87 s problem is by evaluating anchors on
every replayed edge — especially `check:` anchors, which re-run a whole check inside a
historical candidate. Two rules prevent it:

1. **Memoise.** Each distinct `(anchor expression, candidate tree oid)` is evaluated at
   most once per reconciler run. Same anchor, same tree ⇒ same answer. This collapses
   replay from O(edges × items) to O(distinct anchors).
2. **Do not re-prove immutable history.** `check:` anchors are evaluated against the
   *current* candidate and in `--audit`, never during historical edge replay. The
   historical question ("did the finding clear at that tree?") is settled by an immutable
   record; the live question ("does it still hold?") is the one worth asking, and `--audit`
   asks it. This is not deferral in the sense ADR `2026-07-30` forbids: nothing is
   postponed to a future boundary — the current-tree evaluation happens now, and the
   skipped work is a re-derivation of a record that cannot have changed.

With both rules, `queue-resolution` over `root:HEAD` becomes O(edges) cheap set operations
plus O(items) blob reads plus O(landing anchors) `merge-base` probes.

---

## 6. Schema and migration

### 6.1 Field changes (all five templates in `templates/queue/`)

Added, optional while live and required once terminal:

```
**Resolution:** <none | done | answered | superseded | duplicate | rejected | withdrawn | obsolete>
**Resolution anchor:** <anchor expr>[; <anchor expr>...]      # done / answered
**Resolution ref:** `<queue path>`                            # superseded / duplicate
```

plus the `## Resolution log` section (authoritative; `Resolution:` is its cache).
`Resolution reason` lives in the log line's `— <detail>` tail; no separate field.

Changed:

- `Resolution evidence:` → advisory expectation, **mutable while live** before a claim and
  before any concrete response.

### 6.2 Exact code deltas

```python
RESOLUTION_FIELDS = {"Resolution", "Resolution anchor", "Resolution ref"}
LIFECYCLE_MUTABLE_FIELDS = {
    "Status", "Blocks now", "Blocks at", "Until then", "If unanswered",
} | RESOLUTION_FIELDS | {"Resolution evidence"}          # :1974
```

This is **required**, not cosmetic: `immutable_action_text` (`:1987`) treats every
non-listed bold-key line as part of frozen action identity, so appending
`**Resolution:**` to a live item would otherwise trip `queue_mutation_problem` with
"action identity changed while the queue item remained live." Adding `Resolution
evidence` here is what makes D1/D2/D4 correctable; the write-once protection for human
items is unaffected because `human_response_fields` (`:2046`) already covers it and
`claim_identity` (`:1955`) still freezes it across the claim edge.

`RESOLUTION_LOG_RE` for the log section; `resolution_log_lines(text)`;
`terminal_verdict(text)`; `resolution_log_subsequence_problem(before, after)`;
`anchor_problem(expr, revision)`; `compaction_tombstones(revision)`;
`derived_actor(path, text)`. New checks: `queue-compaction` (advisory),
`queue-fold`, `queue-unanswered-closed` (advisory). `check_links` (`:7143`) gains
`Resolution anchor|Resolution ref` to its message-queue strip regex.

### 6.3 Migrating ~41 live items

**Zero migration.** Absent `Resolution:` and absent `## Resolution log` ⇒ live. Every
existing item is valid unchanged. New states are purely additive.

### 6.4 Migrating historical resolved items

**Nothing to do.** They are already deleted; git archives them. `message-queue/compacted/`
starts empty with a `README.md`. Deletion accounting applies only to edges at or after the
v2 activation commit, using the existing `queue_resolution_activation_commits` /
`governed_by_activation_join` machinery — the same pattern v1 already uses.

`--backfill-tombstones` mines `git log --diff-filter=D -- message-queue/` and writes
historical tombstone lines with `{"state":"legacy-v1"}`. It is optional for the design's
correctness — but it turns out to be the repair path for a real, currently permanent
failure, which is worth spelling out.

**A permanently-red historical deletion, and why forward annotation fixes it.** The single
`queue-resolution` finding over `--range root:HEAD` on `main` today is:

```
[queue-resolution] message-queue/needs-human/clarifications/workspace-platform-priority.md:
  deleted unresolved queue item: missing non-queue **Resolution evidence:** file path
  fix: commit the required claim/response evidence before deleting it
```

A *human clarification* was deleted with no resolution evidence at all. The prescribed fix
is impossible: the evidence would have to exist on a deletion edge that is already
committed, and pushed history is never rewritten. The finding is unresolvable by
construction and will stay red on the full-history path forever.

Under this design the same situation is repairable **forward**: append a tombstone line to
`message-queue/compacted/` recording that path, its verdict (`legacy-v1`), and what is
known about it, in the current tree. Accounting is satisfied by content, not by an
unrewritable edge. This is the same ethos the repo already applies to ADRs — *records are
immutable; a reversal is a new file that links the old one* — extended to queue history,
and it is only possible because state is a record rather than a topology.

### 6.5 Coexistence and the activation edge

`message-queue/AGENTS.md`: `**Queue resolution schema:** v2`. At activation the v1
deletion adjudication is **replaced**, not layered — leaving both paths live would keep
the gameable one available. Pre-activation history stays governed by v1 exactly as today.
Removing the v2 marker after activation is a finding, mirroring v1's anti-downgrade rule.

The activation commit is **pure addition** (marker, `compacted/README.md`, templates,
code) and deletes no queue item, so no accounting question arises on the edge itself.

**Proof-of-value, on the very next commit.** `message-queue/needs-agent/requests/
blocking-repair-handover-projection-code-span-copy.md` is permanently unresolvable today
(its repair merged in `6d4e337` before deletion was attempted; the evidence bytes are
identical on both sides of any deletion edge). Under v2 it resolves with one appended
line:

```markdown
## Resolution log

- 2026-07-30 `done` by claude — anchor `commit:6d4e337...`; `check:handover-queue-projection`
```

One commit. No window. No ordering. That single line is the design's whole claim in
miniature.

---

## 7. Repair — the main claim

### 7.1 A wrongly-terminal item / a terminal state set by mistake

Append one line:

```
- 2026-07-31 `reopened` by codex — marked done in error; the fix landed on a branch that was never merged
```

Derived state returns to live. **One commit, one file, no evidence, no boundary, no
ordering.** Nothing is erased — the mistaken verdict and its correction are both in the
log, both attributed, both dated.

Compare today: if the item was deleted, you `git checkout <sha>^ -- <path>` to restore it,
and then it can **never be deleted again** (F5), because the evidence diff on any future
deletion edge is unsatisfiable. The cheap repair today creates a permanent brick.

Abuse guard: reopens are loud. `--audit` reports every reopen in the last 30 days;
frequent reopen/re-resolve churn on one item is visible as a pattern, which it is not
today.

### 7.2 An item resurrected because the work was reverted (B9/F6)

Handled by construction. Anchors are level-triggered, so `--compact` and `--audit`
re-evaluate them against current HEAD. A revert makes `digest:`, `contains:`, `check:`
and `task:@status` anchors fail; the item is auto-reopened with the reason
`anchor no longer holds: <expr>` and a retry is filed.

**Honest limit, stated plainly:** `commit:` and `merge:` are *landing* anchors and a
revert does not un-ancestor a commit. They therefore do **not** detect reverts. This is
precisely why §1.4 requires at least one *state* anchor for `done` outside merge-boundary
reviews. Under today's model a revert leaves a deleted file and nothing anywhere ever
notices.

### 7.3 A wrong, queue-pointing, or typo'd evidence path (D1/D2/D4)

Two independent fixes:

1. `Resolution evidence:` is demoted to advisory and made mutable while live (§6.2), so a
   typo is corrected with **one edit**.
2. The load-bearing anchor is written **at resolution time**, by an actor looking at what
   actually happened. A predeclared path can be wrong before anyone knows the answer; an
   anchor cannot be pre-typo'd because it does not exist until resolution.

Today: the field is inside frozen identity, so it can never be corrected in place;
retire-and-refile costs 2–4 commits, or the item is a permanent brick.

### 7.4 D10 — `operation:` where `task:` was meant, pinning a task at `1_in-progress`

Primary answer: the item reaches `obsolete` or `superseded` in one line, and a correct
replacement is filed. The task unpins in the same commit.

Optional secondary (offered, not required): a **retarget correction** — change the
boundary token when (i) the timing class is unchanged or escalated, (ii) no concrete
human response exists, and (iii) a `retargeted` log line records the old value. This
*strengthens* auditability (today a retarget is either impossible or an unlogged rewrite)
while removing the brick. It does not weaken the timing lattice, which still only
escalates.

### 7.5 D22 — content that makes its own gate unsatisfiable

The live case: an inline code span in a human `Why-you-might-care` field that the handover
projection cannot copy. Editing the item = "live action was rewritten"; deleting it =
"not committed as folding with a concrete response". Both doors closed; every session's
handover ritual blocked.

Under this design **both doors open**: appending a `Resolution log` line is not a rewrite
of action identity (§6.2 puts the resolution fields in `LIFECYCLE_MUTABLE_FIELDS`, exactly
where `Status` already sits), and it needs no response. The projection then excludes the
item because it is terminal. The poisoned fields are never touched.

**Applying D22's meta-lesson to this design.** Is there legal item content that makes *my*
gate unsatisfiable? Audit:

| Surface | Can content poison it? |
|---|---|
| Log line grammar | No — the resolver writes it; nothing is compared to pre-existing content |
| Verdict vocabulary | No — closed set |
| Reason prose | No — free text, never compared to anything, never required to be copied |
| Anchors | No — written by the resolver, from a closed grammar |
| Deletion accounting | No — compares paths and hashes, not prose |
| Tombstone serialisation | Closed by choosing **JSON per line** over a delimited format, so no filename or field value can break the record |

And one **hard design rule**, written into `message-queue/AGENTS.md`:

> No check may ever require resolution prose to be copied byte-for-byte into another
> artifact.

That rule is D22's root cause stated as a prohibition. It is the reason the
`## Resolved since last handover` section (§4.4) is shape-checked only.

### 7.6 G1/G3 — repair blocked by the thing it repairs

Every escape in this design is a **pure append to a single file**. It requires no other
file to change, no history to be walked, no boundary to be crossed, no other actor.
Therefore any red state caused by a queue item is clearable by editing that item, in the
same commit, by the agent that is blocked. Corollary design rule: *no future queue check
may require a second file to change in order to clear it.*

This also means the design ships its **own break-glass, and it is cheaper than
`--no-verify`** — which is the only strategy the briefing says can work (steal #4). There
is no separate override mechanism to build: `Resolution: obsolete` with a reason *is* the
declared, recorded, attributed, dated, counted, projected override. `--no-verify` is
silent and leaves less trace; this is louder and faster. That is the whole competitive
argument.

---

## 8. Interaction with the existing invariants

| Guarantee | Verdict | Mechanism |
|---|---|---|
| Deletion needs an act, not a label | **PRESERVED + STRENGTHENED** | §8.1 — the crux |
| Active-repair proof (committed status-only claim edge) | **PRESERVED** | claim must be present in the parent tree of the terminal edge (§5.1.7); read from content, so it survives rebase/cherry-pick |
| Claim receipts are not transferable | **PRESERVED** | the record lives inside the item whose action identity is frozen; a new identical item has neither a log nor a tombstone |
| Human responses are write-once | **PRESERVED + STRENGTHENED** | the file survives instead of being destroyed; plus `obsolete`/`withdrawn` are *forbidden* once a concrete response exists (§1.3) |
| Committed lifecycle claims never regress across merge parents | **PRESERVED + EXTENDED** | log-subsequence rule covers verdicts, reasons, anchors and actors, not just `Status` |
| Action identity frozen once live | **PRESERVED** | resolution fields join `LIFECYCLE_MUTABLE_FIELDS`, where `Status` already lives; body and `Action` unchanged |
| Timing may only escalate; freezes on response | **PRESERVED** | untouched; optional retarget correction is monotone and logged |
| Evidence must be outside the queue | **PRESERVED** | anchors must name non-queue paths. `superseded`/`duplicate` deliberately point *into* the queue, but they are not claims that work happened, and are rendered as such in every projection |
| Review target must differ from resolution evidence | **PRESERVED, and the ambiguity shrinks** | for `withdrawn`/`rejected` no anchor is required at all, so "withdrawing by rewriting the reviewed bytes" has no motive |
| The gate cannot be turned off | **PRESERVED** | v2 marker anti-downgrade (same machinery); plus a missing `compacted/` directory after activation is itself a finding |

### 8.1 The crux: "a naive reading says you replaced an act with a label"

The objection is the right one to press, and the answer has four parts.

**(1) The invariant protects the item's *content*, not the file's *existence*.** Read its
stated threat: *"an agent writing `Status: in-repair` and `rm`-ing inconvenient items."*
The harm is that the human's answer, the action text and the delivery state cease to exist
as live state. A label under this design cannot cause that harm, because a label destroys
nothing. After `Resolution: obsolete`, the action text, the human's answer, the timing,
the filer, the disposition and its reason are all still in the tree — greppable,
diffable, and projected once into the human's next handover. The label changes *derived
visibility*. The destruction is a separate, later, independently gated act.

**(2) The act still exists; it moved to where acts are cheap and reversible.** Deletion
now requires a tombstone naming the path, its terminal state, the resolving commit and the
sha256 of the exact removed bytes. That is *more* of an act than today's, which is a `rm`
plus a blob diff. An agent who `rm`s a queue file without a tombstone is blocked — on the
candidate, with no window and no ordering luck, **including on a merge result**, which
today's check cannot catch at all (C6/C7, C8).

**(3) Today's "act" is already a label in a costume.** The briefing's own empirically
verified finding: appending `\n# probe\n` to the declared evidence file and staging it
cleared the finding entirely. The current gate buys *"the deletion commit also touched the
named file"*, never *"the work happened."* This design does not trade an act for a label.
It trades a **forgeable act** for a **durable record plus a real act at compaction**, and
it makes the honest path the cheapest path so the forgeable one has no advantage left.

**(4) Monotonicity is preserved where it matters.** Nothing is ever erased; states are
appended; each parent's log must be a subsequence of the merged log. `obsolete` is not
"make this go away" — it is "record that this is no longer relevant, and let it be seen
before it is compacted." Compaction eligibility requires the record to be published in
admitted history, so file-and-erase inside one branch is impossible.

**The honest residue.** A dishonest agent *can* write `Resolution: obsolete` with a
plausible reason on an inconvenient blocking item and unblock itself in one commit. That
is true and intentional. What is claimed is not prevention — the briefing rules prevention
out, given a bypassable hook, one shared identity, and the checker living in the same
writable tree. What is claimed is that the dishonest act becomes **tamper-evident,
attributed, dated, reasoned, counted and projected**, where today the equivalent act is
`--no-verify && rm && git commit`, which is cheaper *and* leaves less trace.

---

## 9. Scenario verdict table

| # | Scenario | What happens under this design | Verdict | Notes |
|---|---|---|---|---|
| 1 | **B1/B2** — evidence merged before the claim edge vs. evidence never changed | Item A: `done` + `commit:6d4e337` (an ancestor) ⇒ passes. Item B: every state anchor fails (`digest:` mismatch, `contains:` absent, `check:` still firing) ⇒ `done` rejected; the honest terminal is `obsolete`/`withdrawn` with a reason | **EASY** | Opposite verdicts, as required. The one-commit window is gone by construction, not by exception |
| 2 | **D22** — item content makes its own gate unsatisfiable | Log append is not an identity rewrite and needs no response; projection then excludes the terminal item. Poisoned fields never touched | **EASY** | Plus a hard rule (§7.5) forbidding any check from requiring resolution prose to be copied — the meta-lesson, mechanised |
| 3 | **D5** — live item declares a reciprocal dependency that never existed | `superseded`/`duplicate` gain a validated `Resolution ref:` (must resolve to a live path or a tombstone). `Depends on:`/`Successor action:` on *live* items remain unvalidated | **AWKWARD** | Genuine improvement, not a fix. Queue topology validation is orthogonal work this design neither solves nor blocks |
| 4 | **C6/C7** — stale 78-commit branch carrying a divergent queue | *Deletes a live item*: no tombstone ⇒ finding on the merge result (today: nothing). *Reverts review states*: parent's log is not a subsequence of the merge's ⇒ finding (broader than today's `Status`-only rule). *Resurrects a pickup for a `4_done` task*: tombstone + live file at the same path ⇒ finding (**new detection**). *Untouched item*: 3-way merge keeps both hunks ⇒ correct | **EASY** | The strongest result in the table. Requires the merge *result* to be checked at all — see #5 |
| 5 | **C8** — a rule and its first violation meeting only in the merge commit | Not fixed. This design *reduces the surface*: because every new check is tree-local (set difference + dir read + string subsequence), checking the merge result becomes affordable, and the collision checks above are exactly the kind that only a merge-result evaluation can catch | **AWKWARD** | Honest: state modelling cannot make an unevaluated commit evaluate itself. Attached recommendation: run `--check --range base...merge-result` in the merge queue |
| 6 | **H-P1** — the answered item re-asked in 19+ handovers | Fixed twice: terminal items are not live; and `folding` + concrete response routes to the agent as a fold obligation, not to the human. New `queue-fold` finding keeps the obligation from evaporating | **EASY** | Committed handovers are untouched: historical re-checks run at the creation tree, where nothing was terminal |
| 7 | **E7/B13** — boundary crossed outside the repo while the item is `waiting` | Each of the three items reaches `obsolete` in one line ("the merge boundary was crossed outside this repository; this review can no longer gate it"), emits `queue-unanswered-closed`, appears once in `## Resolved since last handover`, and the three tasks leave `3_in-review` | **EASY** | The right answer is *honest recording*, not a fake `done`. This is the Saga-compensation steal working exactly as intended |
| 8 | **G1/G3** — repair requires a commit the finding blocks | Every escape is a pure single-file append; the blocked agent can always clear it in its own commit. The design ships its own break-glass, cheaper than `--no-verify` | **EASY** | Plus a standing rule: no future queue check may require a second file to change in order to clear it |
| 9 | **D13/D12/B5** — evidence proves a byte changed, never that work happened, never who did it | Anchors are strictly harder to satisfy trivially: `check:` needs a real finding cleared, `contains:` a named heading, `task:@status` a real lifecycle move, `digest:` exact bytes. A cosmetic edit satisfies none. *Who did it* is unchanged | **AWKWARD** | Half-solved and honest about it. Identity requires signing, which the briefing puts out of scope |
| 10 | **C10/C11/B17** — queue state only in an uncommitted working tree | Inherited, not fixed by state modelling. Companion fix specified: terminal/deletion accounting considers only *tracked* paths, and untracked queue files get their own `queue-uncommitted` finding naming them ("stage it or remove it") instead of silently blocking every commit in that checkout | **AWKWARD** | Explicitly a companion fix, not a consequence. It is small, orthogonal, and lives in the same function (`live_queue_items`, `:740`) |
| — | **D1/D2/D4** — wrong / queue-pointing / typo'd evidence path, immutable today | Field demoted to advisory and made mutable while live; the load-bearing anchor is written at resolution time and cannot be pre-typo'd | **EASY** | 2–4 commits or a permanent brick → one edit |
| — | **D10** — `operation:` where `task:` was meant pins a task forever | `obsolete` + refile in one commit; optional logged retarget correction as a secondary path | **EASY** | The optional retarget rule strengthens auditability rather than weakening timing |
| — | **F1/F2/F3** — rebase / squash / cherry-pick destroy the status-only claim edge | Terminal records and tombstones are *content*, so all three preserve them. The claim requirement is read from the **parent tree**, not found by walking a claim edge, so it survives rebase and cherry-pick. A squash that collapses claim + resolution into one commit still fails | **AWKWARD** | Improved, not solved. `handbook/git-workflow.md` already forbids squash-merging task branches, so the residual is policy-supported |
| — | **F5** — reverting a deletion resurrects an item that can never be re-deleted | Reverting a compaction restores the file *and* removes the tombstone line; the item is live again with its terminal record intact; re-compaction is one mechanical command needing no proof | **EASY** | The single clearest win. Today this is a permanent brick |
| — | **F8** — shallow clone makes lineage unverifiable, so every deletion fails closed | Records and tombstones are tree content ⇒ fully readable at depth 1. Only `commit:`/`merge:` anchors need ancestry; at insufficient depth they yield an **advisory** "could not verify anchor at this depth", not a block | **EASY** (flagged) | Judgment call, stated as such: this fails *open on a verification* while the record itself is present and the admitted-boundary check still runs. The alternative (fail closed) reproduces today's brick in every shallow CI job |
| — | **G12** — batch-filed items expiring on the same calendar date lock the repo | Ten items, ten one-line log appends, one commit, no evidence, no ordering. Terminal items also leave `check_stale_queue`'s scope automatically because `live_queue_items()` excludes them | **EASY** | The "cheap honest path" requirement paying off at batch scale |
| — | **NEW, measured this session** — a historical deletion that is red forever: `needs-human/clarifications/workspace-platform-priority.md` was deleted with no `Resolution evidence:` at all, and the prescribed fix requires evidence on an already-pushed edge | Repaired **forward** with a `legacy-v1` tombstone line in the current tree; accounting is satisfied by content, not by an unrewritable edge (§6.4) | **EASY** | Today this finding is unresolvable by construction. Same ethos as the repo's immutable-ADR rule, extended to queue history |

**Silent-corruption audit.** No row is SILENT-CORRUPTION. The two candidates and why they
are not:

- *A merge that keeps both a terminal record and a stale branch's live edit.* Result: a
  terminal item with, say, escalated timing. Harmless — terminal items are excluded from
  every liveness check, and the log records both events.
- *A tombstone whose sha256 does not match the removed bytes.* Detected on the accounting
  edge (§3.3), because the parent's bytes are fetched there anyway.

The residual risk is not corruption but **dishonesty**: a false `obsolete`. It is loud,
attributed, counted and surfaced — see §8.1's honest residue and §10.1.

---

## 10. The three strongest objections to this design

### 10.1 "You made unblocking free. Every agent under time pressure will write `obsolete`."

**Largely conceded — this is the design's real price.** One line and any blocking item is
gone. Three answers, in decreasing strength:

1. **The comparison is not "free vs. prevented."** The briefing's phase-1 verdict is that
   prevention is off the table: a bypassable hook, one shared identity, and a checker in
   the same writable tree. The real comparison is *free-and-recorded* versus
   *free-via-`--no-verify`-and-unrecorded* — and agents have already used `--no-verify`
   on four `exp/*` branches. A design that loses the convenience race loses entirely.
2. **Abuse becomes a number.** `--audit` prints `obsolete`/`withdrawn` counts per actor per
   30 days; `queue-unanswered-closed` names every human ask closed without an answer; the
   handover's `## Resolved since last handover` puts each one in front of the owner once.
   None of these exist today, because today the item is simply *gone*.
3. **The irreplaceable thing is protected absolutely.** `obsolete`/`withdrawn` are
   forbidden once a concrete human response exists. You may abandon an *ask*; you may not
   make an *answer* disappear.

What I will not claim: that this stops a determined dishonest agent. It does not. It makes
dishonesty legible.

### 10.2 "You added a second source of truth. The file and the tombstone can disagree."

**Partially conceded.** Two places now describe an item's fate. Answers:

- The tombstone carries the sha256 of the final bytes and the resolving commit oid, so
  disagreement is *detectable*, not silent, and it is detected on the only edge where it
  can be introduced (§3.3).
- The states are mutually exclusive by check: a path is either present-with-record or
  absent-with-tombstone. Both, or neither, is a finding. That makes it one source of truth
  with a verifiable index — the Fossil pattern — not two competing sources.
- Honest residual cost: one more directory, one more contract paragraph, and a real risk
  that `message-queue/compacted/` becomes a junk drawer nobody reads. Mitigated by
  `--explain <slug>`, not eliminated.

### 10.3 "Terminal items rot in the folders and the queue stops being a queue."

**Conceded as a real ergonomic cost.** A human opening `needs-human/reviews/` will see
resolved files for up to two weeks. Answers and their limits:

- Compaction is mechanical, cannot fail (the proof is already recorded), and defaults to
  14 days. It slots into the existing memory-gardener forgetting pass and gains one line
  in the session-handover ritual.
- Every terminal item carries `**Resolution:** <verdict>` in its first few lines, and no
  projection ever shows it.
- **But** if compaction is neglected the folder does get noisy, and the obvious fix —
  moving terminal items to `resolved/` — is the one I rejected in §2.1 for merge-safety
  and path-identity reasons. I am trading browsing ergonomics for merge correctness, and
  that trade is deliberate but genuinely a trade.

A fourth, smaller objection worth naming: **this is more schema to learn.** Three new
fields and one section, against the removal of an evidence-window rule, five special-case
escapes, and (in the templates and `message-queue/AGENTS.md`) several paragraphs of
lifecycle prose that exist only to explain those escapes. Net contract surface should
shrink; net *conceptual* surface certainly does, because "resolution is a recorded state"
is one sentence and "resolution is deletion, adjudicated by a one-commit evidence window
with six named exceptions" is not.

---

## 11. Implementation plan

| Step | Files | Notes |
|---|---|---|
| 1 | `templates/queue/*.md` (5), `templates/handover.md` | add fields, `## Resolution log`, `## Resolved since last handover` |
| 2 | `message-queue/AGENTS.md` | `Queue resolution schema: v2`; the state table; the "no check may require copying resolution prose" rule; the "no check may require a second file to clear" rule |
| 3 | `message-queue/compacted/README.md` | tombstone format (JSON lines), append-only, one file per run |
| 4 | `reconcile.py` — state | `RESOLUTION_FIELDS`, `LIFECYCLE_MUTABLE_FIELDS` (`:1974`), `terminal_verdict`, `resolution_log_lines`, `resolution_log_subsequence_problem`, `derived_actor` |
| 5 | `reconcile.py` — anchors | `anchor_problem(expr, revision)`; reuse `git_revision_candidate` for `check:` anchors; **memoise by `(expr, tree oid)` and exclude `check:` from historical replay (§5.5)** |
| 6 | `reconcile.py` — liveness | `live_queue_items` (`:740`) skips terminal; `live_human_queue_paths` (`:5959`) uses `derived_actor`; `queue-uncommitted` companion finding |
| 7 | `reconcile.py` — accounting | replace `queue_deletion_problem` (`:3577`) and delete `resolution_evidence_problem` (`:2722`); `compaction_tombstones`; tombstone/live collision check |
| 8 | `reconcile.py` — new checks | `queue-fold`, `queue-compaction` (advisory), `queue-unanswered-closed` (advisory); `--compact`, `--audit`, `--explain`, `--fix-resolution` |
| 9 | `check_links` (`:7143`) | strip `Resolution anchor|Resolution ref` |
| 10 | `history/AGENTS.md`, `templates/handover.md` | `Queue projection schema: v2` |
| 11 | ADR | new decision file superseding `2026-07-23-queue-resolution-preserves-review-intent.md`; the old ones are never rewritten |
| 12 | Tests | `automation/tests/test_reconcile_queue.py` — expect large net deletion; replace escape-specific tests with table-driven anchor-grammar and log-subsequence tests |
| 13 | Demo commit | resolve `blocking-repair-handover-projection-code-span-copy.md` and the three `transition:merge` items stranded since 2026-07-23 |

**Measurement obligation before merge.** §5.4's baselines are measured; its post-design
figures are projections. Re-run the per-check timing harness in all four modes and record
real numbers in `verification.md`. The acceptance bar:

| Mode | Measured baseline (`queue-resolution`) | Must not exceed |
|---|---|---|
| `--check` staged, clean tree | 0.40 s | 0.60 s |
| `--check` staged, 1 queue deletion | 0.40 s + a predecessor BFS | 0.60 s |
| `--range` 20 commits | 4.11 s | 4.11 s |
| `--range root:HEAD` | **103.87 s** (whole run 525.08 s) | **30 s** — if this is not met, §5.5's bounding rules are wrong and the design does not merge |

The last row is the one that decides whether this design is worth its schema cost.

Also record, before and after: the count of `queue-resolution` findings over
`--range root:HEAD` (**1 today**) and the size of `automation/tests/test_reconcile_queue.py`
(**12,946 lines / 302 tests / 150.03 s today**). A design that adds contract surface must
be able to show the test corpus shrinking.
