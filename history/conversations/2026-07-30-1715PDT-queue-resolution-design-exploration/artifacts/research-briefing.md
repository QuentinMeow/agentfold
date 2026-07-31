# Shared briefing — AgentFold queue resolution redesign

You are one of several independent design agents. This file is the shared ground truth
from a completed research phase. Read it fully before designing. REPO: `/Users/quentinmiao/code/ai-harness`

## The system

AgentFold is an "agent-native repository": multiple AI agents plus one human owner (Quentin)
coordinate through files in git instead of live chat. `message-queue/` is the canonical action
bus. Every pending human action and durable cross-session agent action is exactly one Markdown
file, routed on three axes:

- actor folder: `needs-human/` vs `needs-agent/` (who acts next)
- leaf folder: `decisions/`, `clarifications/`, `reviews/`, `requests/`, `retries/`
- filename prefix: `blocking-`, `future-blocking-`, `non-blocking-` (when unresolved work stops)

**An item's entire existence is the presence of that file. Resolution IS deletion.**
A Python reconciler (`automation/reconcile/reconcile.py`, ~7700 lines) runs in a pre-commit
hook and in CI, and refuses commits that violate queue invariants.

## The defect

`resolution_evidence_problem` (reconcile.py:2722) gates deletion. Each item predeclares a
`**Resolution evidence:**` file path. To delete the item, that file's bytes must DIFFER between
`prior_revision` (the deletion edge's immediate parent) and the deletion candidate.

**The window is exactly one commit wide.** Work that landed earlier is byte-identical on both
sides, so it reads as "unchanged" and the item can never be deleted honestly. `after is None`
(evidence file deleted) also counts as unchanged.

Live proof on main today: `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
is permanently unresolvable. Its repair merged in commit `6d4e337` before deletion was attempted.

## CRITICAL FINDING — the current check is already trivially gameable

Empirically verified in phase 1: appending `\n# probe\n` to the declared evidence file and
staging it CLEARED the finding entirely. The invariant buys *"the deletion commit also touched
the named file"*, never *"the work happened."*

Consequences you must internalize:
- Tightening the window buys nothing real. It only taxes honest actors.
- The repo's own ADR concedes the ceiling: "This proves repository transitions, not human identity."
- A prior adversarial panel already ruled a self-authored acknowledgement "forgeable."

## CRITICAL FINDING — the design ALREADY contains the missing pattern

Two existing escapes prove resolution from history that PREDATES the deletion commit, and
both deliberately skip `resolution_evidence_problem` entirely:

- **E4 `approved_review_merge_receipt_problem`** (:3269) — proof is a two-parent merge already
  present in admitted target history.
- **E5 `task_transition_receipt_problem`** (:3163) — proof is a task-lifecycle transition
  already crossed in committed history.

Only the *ordinary* path insists the proof live on the deletion edge itself. Any design that
generalizes E4/E5 is consistent with the existing architecture, not a departure from it.

## Other escapes that exist today

- **E1 `generated_retry_clear`** (:2851) — a reconciler-filed retry deletes when the named check,
  re-run against the deletion candidate's exact tree, no longer reports that finding. This is a
  genuine level-triggered predicate and it already works.
- **E2 `pickup_completed`** (:1892) — the atomic backlog->in-progress task move IS the evidence.
- **E3 changes-requested reviews** (:3622) — the successor item pair IS the evidence.
- **E6 non-blocking approved reviews** (:3670) — **delete for free**, no evidence, no boundary.
  The strictness gradient does not track risk: a `blocking-` agent request whose work merged is
  permanently stuck, while a non-blocking approved review deletes with no proof at all.

## Enforcement reality

- Local pre-commit hook (`automation/hooks/pre-commit`) runs `reconcile.py --check` over the
  WHOLE repo. One bad item anywhere blocks EVERY commit in that checkout.
- CI runs it on push and pull_request over committed ranges.
- `--no-verify` bypasses the local hook completely. The contract forbids it; agents have used it
  anyway on four `exp/*` branches.
- **There is no waiver, allowlist, expiry, or break-glass mechanism anywhere.** None.
- A clone that never ran `install.py` has NO local gate at all.
- `--range root:HEAD` replays every deletion edge in all history; it already exceeds a 2-minute
  timeout on this repo. It is the CI path for the first push of the default branch. Any design
  adding per-edge history walking compounds there.
- The queue check is already the slowest thing in the repo: 92-312 seconds for the queue file alone.

## Invariants any solution must preserve

| Guarantee | What it prevents |
|---|---|
| Deletion needs an act, not a label | An agent writing `Status: in-repair` and `rm`-ing inconvenient items |
| Active-repair proof (committed status-only claim edge) | Deleting an item nobody picked up |
| Claim receipts are not transferable | A new identical item borrowing an older twin's claim |
| Human responses are write-once | An agent "improving" the owner's answer |
| Committed lifecycle claims never regress across merge parents | A merge silently reverting `folding` to `waiting` |
| Action identity frozen once live | Rewriting `Action:` into something already done, then deleting |
| Timing may only escalate; freezes on response | Downgrading `blocking-` to stop it gating a merge |
| Evidence must be outside the queue | An item "resolving" by pointing at another queue file |
| Review target must differ from resolution evidence | "Withdrawing" by rewriting the reviewed bytes |
| The gate cannot be turned off | Deleting the schema marker to make findings vanish |

## The 10 hardest scenarios — your design MUST be tested against these

1. **B1/B2 — evidence already merged before the claim edge.** [LIVE ON MAIN] An item whose
   evidence changed three merges ago and one whose evidence never changed at all must reach
   OPPOSITE verdicts.
2. **D22 — item content makes its own gate unsatisfiable.** [OBSERVED] An inline code span in a
   human field blocked EVERY session's handover ritual. Editing the item = "live action was
   rewritten"; deleting = "not committed as folding with a concrete response". Both doors closed.
   Any new invariant must be checked for whether some legal item content makes it unsatisfiable.
3. **D5 — a live item declares a reciprocal dependency that never existed.** [FOUND LIVE, 0 findings]
   `Depends on:`/`Supersedes:`/`Successor action:`/`Resolution evidence` are all stripped from
   link-check. Queue topology is effectively unvalidated.
4. **C6/C7 — a stale long-lived branch carrying a whole divergent queue.** [VERIFIED LIVE] A branch
   78 commits behind resurrects a pickup for a `4_done` task, deletes a live item, and reverts 7
   review states — as a CLEAN merge, no conflict, no finding on either head.
5. **C8 — a rule and its first violation meeting only in the merge commit.** [OBSERVED] Five green
   PRs merged; main immediately red. Sequencing does not help. Nothing ever evaluates the merged result.
6. **H-P1 — the answered item re-asked forever.** [OBSERVED] An item `folding`/`approved` since
   2026-07-24 is still projected as an open ask in 19+ handovers, because projection is
   shape-checked and never state-checked.
7. **E7/B13 — boundary crossed outside the repo while the item is still `waiting`.** [OBSERVED]
   Three live items name `transition:merge`; their ranges are already ancestors of main; all still
   pending. Git evidence cannot un-cross a gate. Three tasks stranded in `3_in-review`.
8. **G1/G3 — repair requires a commit that the finding blocks; the repair task is pinned by the
   thing it repairs.** [BOTH LIVE] Enforcement is global, repair is local. Any solution that adds
   a check must ship its own escape path or it adds a new way to brick the repo.
9. **D13/D12/B5 — evidence proves a byte changed, never that work happened, never who did it.**
   A cosmetic edit, a claim by agent A with work by agent B, and genuine completion are
   indistinguishable.
10. **C10/C11/B17 — queue state existing only in an uncommitted working tree.** [OBSERVED 3 WAYS]
    `live_queue_items` counts untracked files, so such an item blocks that checkout while being
    invisible to git, CI, and every other agent. Most likely scenario to destroy a human's answer.

Additional high-value cases: D1/D2/D4 (wrong, queue-pointing, or typo'd evidence path — the field
is immutable so it can never be corrected in place; retire-and-refile costs 2-4 commits);
D10 (a `blocking-` item naming `operation:` where `task:` was meant pins a task at `1_in-progress`
forever); F1/F2/F3 (rebase/squash/cherry-pick destroying the status-only claim edge);
F5 (reverting a deletion resurrects an item that can never be re-deleted); F8 (shallow clone makes
lineage unverifiable, so every deletion fails closed); G12 (batch-filed items expiring on the same
calendar date lock the repo).

## Prior-art conclusions from phase 1 research

The honest verdict: **prevention is off the table.** With a bypassable hook, one shared identity,
and the checker living in the same writable tree, you cannot prevent laundering. The achievable
goal is **tamper-evidence + order-independence + cheap honest paths**. A strict-looking mechanism
that creates false confidence is WORSE than a lenient one, because it substitutes for review.

Five ideas judged most worth stealing:

1. **Level-triggered resolution** (Kubernetes spec/status, Argo CD desired-vs-live): replace
   "the evidence changed in this commit" with "this predicate over current repo state is true now."
   Removes the deadlock by construction rather than by exception. `git log` + the working tree is a
   complete oracle; no server needed. Makes resolution answerable in any order by any actor.
2. **Bind evidence to a content digest or commit SHA, not a path plus a moment** (in-toto
   `subject.digest`, git-bug content-derived IDs, git notes). "The work landed three commits ago"
   stops being a problem the moment the claim names that commit.
3. **Make "resolved" a derived status; make deletion a compaction step** (event sourcing, Fossil
   reconstructible tickets, Kafka tombstones, Saga compensation). The hook then only ever computes,
   never adjudicates an irreversible act. An honest "no longer relevant" becomes a first-class
   terminal state.
4. **A declared, recorded, expiring, ratcheted override** — deliberately cheaper than `--no-verify`.
   A silent bypass already exists and is one flag away, so the only viable strategy is to
   out-compete it on convenience while making its use visible and trending toward zero.
   (Break-glass reason+approver+expiry+audit; Snyk `.snyk` expires; Gatekeeper dryrun->warn->deny;
   ratchet baselines that may only shrink.)
5. **Split the gate: cheap checks at commit, completion claims deferred to a coarser boundary,
   plus a full-corpus audit sweep that re-derives every claim** (PostgreSQL DEFERRABLE, Gatekeeper
   audit controller alongside admission). In a repo with a skippable hook, the periodic sweep is
   the REAL enforcement; the hook is an early warning.

Runner-up: **finalizer-style named blockers** on each item ("who still needs this open"), converting
one unanswerable global question into several locally-answerable ones, plus a documented loud
last-resort repair.

Anti-gaming guidance: prefer predicates whose value cannot be moved by a trivial edit.
"The evidence file changed" is satisfiable by adding a space. "Command T exits 0", "path P is
reachable from main in a commit whose trailer names item X", "file F contains a section matching S"
are not — you must actually do something, and that something is close to the work itself.

## Non-negotiable design constraints

- No server, no daemon, no database. Git plus Python 3 standard library only.
- Must work in a fresh clone with no reflog, and degrade sanely on a shallow clone.
- Must not make the already-slow gate materially slower; `--range root:HEAD` already times out.
- Portable across agent runtimes, external providers, and unrelated adopted repositories
  ("core admission" rule). Personal setup and single-provider workflows stay out of core.
- A decided ADR is never rewritten; a reversal is a new file linking the old one.
- Records are immutable; committed handovers cannot be edited.
- Migration matters: there are ~41 live queue items today and history full of resolved ones.
  A design that cannot migrate the existing corpus is not viable.
