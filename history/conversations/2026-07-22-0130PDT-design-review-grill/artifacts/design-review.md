# Design review — grilling AgentFold (2026-07-22)

**Scope:** every file in the repo, the reconciler's actual behavior, the git history,
plus three parallel web-research passes (instruction-file best practices; agent memory
and handoff patterns; file/git-based multi-agent coordination).
**Requested by:** the repo owner, in chat ("grill the design, find conflicting ideas,
research improvements, finalize details").

**Verdict:** the design is coherent, self-aware, and in two places ahead of the field
(one-item-one-file coordination; enforced memory expiry). It has one flagship
contradiction — the repo preaches *eventual* consistency while the pre-commit gate
enforces *immediate* consistency through a single severity channel — plus a
self-healing loop with no automated trigger, a git workflow its own history deviates
from, and an enforcement table that oversells what is mechanical.

---

## Part 1 — Contradictions found

### 1.1 Eventual consistency vs. the hard pre-commit gate (flagship)

`handbook/principles/eventual-consistency.md` promises drift becomes a queued repair
"the next session picks up." But the pre-commit hook runs `reconcile.py --check`,
which exits 1 on **any** finding and blocks **every commit repo-wide**. Time-based
findings make the two models collide:

- `stale-queue` (>30 days) fires on *all five* queues, including
  `needs-human/decisions/` — where the design says an unanswered decision is fine
  (proceed on default path, politely re-surface forever). The queue table says only
  *reviews* go stale at 30 days. As implemented, one month-old unanswered decision
  makes every commit fail. The finding's own suggested fix ("re-surface it in the
  next reply") does not touch the `Filed:` date, so following it cannot clear it.
- **Mass memory expiry is scheduled**: 13 of 14 memory entries were written
  2026-07-22, so their `Review-by` dates land 2027-01-18..22. In late January the
  repo accumulates 13 simultaneous findings and no commit passes until a full
  gardening pass runs. (The fact file expires alone on 2026-10-22.)
- **The escape hatch deadlocks**: `automation/AGENTS.md` says "fix the finding or
  file the reason as a decision" — but filing the decision needs a commit, which the
  finding blocks. Only `--no-verify` gets through, which the guardrails forbid.
- **CI becomes time-dependent**: the same commit is green today and red in three
  months.

*Fix (task `2026-07-22-severity-tiers-for-reconciler-findings`):* split findings into
`block` (schema, links, budgets, structure) and `advise` (staleness, expiry); only
`block` fails `--check`; advisory findings surface through retry filing and CI
warnings.

### 1.2 The self-healing loop is an instruction, not a system

Nothing runs `--file-retries`: the hook and CI both run `--check` only. The loop
diagram's "retry item auto-filed" step has no automated trigger — the centerpiece of
systems-over-instructions is itself an instruction. Even when run manually, filing
can't complete: while an invariant is broken, pre-commit blocks committing the retry
items too. Two further defects in `file_retries()`:

- It unconditionally rewrites every finding's file, clobbering an agent's committed
  `**Status:** in-repair` claim — violating the "Append, don't clobber" guardrail.
- Rejection is unreachable: a rejected-but-unfixed finding resurrects on the next
  run with the rejection text erased. There is no waiver mechanism.

*Fix (task `2026-07-22-retry-filing-automation-and-waivers`).*

### 1.3 The two-kinds-of-writes rule vs. the repo's own history

`handbook/git-workflow.md` says coordination writes go "directly on `main`." The
actual history: every `harness:` commit of the second session sits on a
`session/…` branch merged via PR #2, and task branches merged into the *session*
branch. Related unfinalized details:

- Task-folder files straddle the split: claims are coordination (main) but
  `worklog.md`/`verification.md` describe branch work; `verification.md` lands on
  main describing code main doesn't have yet — the exact issue-state-vs-code-state
  race documented for the beads tracker (a dependent task can start against
  unmerged code).
- The claim protocol depends on an immediate push nothing requires; no rule defines
  when a claim dies. `stale-task` uses filesystem mtime, which git does not
  preserve: it can never fire in CI and fires spuriously on old local clones.
- "A task branch touches one service" doesn't cover the repo's actual work
  (handbook/automation edits).

*Fix (tasks `2026-07-22-finalize-coordination-write-rules`,
`2026-07-22-severity-tiers-for-reconciler-findings` for the mtime issue).*

### 1.4 The enforcement table oversold (fixed on main, 2026-07-22)

- "Every conversation leaves a handover.md — reconciler": the reconciler only sees
  conversation *folders that exist*; a session leaving nothing is invisible. The
  session-handover skill's pair-mode skip contradicted `history/AGENTS.md`.
- "Merges get adversarial review": a skill is prose; nothing verifies a panel ran.
- `templates/README.md` claimed the reconciler skips `templates/`, but the budget
  check applied there.

*All three fixed in the `fix/design-review-hardening` merge (README wording, skill
rewording, reconciler skip).*

### 1.5 Letter-vs-ritual wording conflicts (fixed on main, 2026-07-22)

- "Never edit or delete text the human wrote" vs. the ritual of deleting answered
  decision files → now "delete only after folding."
- `message-queue/AGENTS.md` claimed *all* agent↔agent coordination flows through the
  queue; it actually flows through `tasks/` → scope corrected.
- CONTRIBUTING's "change the template, the check, and nothing else" was
  unsatisfiable (schema changes must migrate existing items) → corrected.
- `memory/AGENTS.md` stated a +90-day default that contradicted the +180 in two
  templates → defaults now live only in templates; stagger guidance added.
- Remaining, deliberately left to tasks: "every change traceable to a task" vs.
  CONTRIBUTING's untracked small fixes (task
  `2026-07-22-de-minimis-path-for-micro-changes`); `2_blocked` defined only for
  human decisions (task `2026-07-22-finalize-coordination-write-rules`); done-task
  pruning tripping the link check via `roadmap/current-state.md` citations (noted in
  the memory-gardener skill).

### 1.6 No trust model (principle added on main, 2026-07-22)

`needs-agent/requests/` is an instruction channel future sessions *execute*; in an
open repo that is an unauthenticated command-injection path (the "Rules File
Backdoor" class; memory-poisoning literature). Added
`handbook/principles/provenance-over-position.md` + guardrail + queue rule +
CONTRIBUTING review requirement. Mechanical enforcement is task
`2026-07-22-provenance-checks-for-instruction-files`.

---

## Part 2 — Research findings mapped to this design

**Validated:**

- *One-item-one-file*: beads (24k stars) keeps issues in shared JSONL; its author
  documents constant merge conflicts, agents resolving them destructively, and a
  ~500-issue ceiling (Yegge, "Beads Best Practices",
  https://steve-yegge.medium.com/beads-best-practices-2db636b9760c; HN
  https://news.ycombinator.com/item?id=46467414). The ecosystem is retrofitting real
  databases under high-write coordination state; low-write markdown survives.
  AgentFold's only shared mutable file is the generated, regenerable index — the
  correct exception.
- *Enforced expiry is ahead of the field*: Kinde/Tweag preach "stale memory is worse
  than none" but stop at exhortation; mem0's eviction taxonomy
  (https://mem0.ai/blog/memory-eviction-and-forgetting-in-ai-agents) and a 435-paper
  survey (https://arxiv.org/abs/2606.30306 — forgetting/governance is the neglected
  frontier) land on review-dates + active supersession.
- *Reconciler-as-referee* matches where serious setups converged: single-committer /
  verify-the-merged-result loops (https://ctx.rs/blog/merge-queue-for-agents/),
  GitHub Squad coordinating agents entirely through versioned repo files
  (https://github.blog/ai-and-ml/github-copilot/how-squad-runs-coordinated-ai-agents-inside-your-repository/).
- *Decision-guide answerability*: escalation above ~20% makes humans rubber-stamp
  (https://zylos.ai/research/2026-04-03-agent-to-human-handoff-patterns/); AWS's
  agentic lens endorses queue-with-safe-default as the production sweet spot.

**Challenged:**

- *Ceremony overhead is measured*: Spec Kit produced ~4,800 lines of markdown for
  689 lines of code, 4× wall-clock (Eberhardt,
  https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html).
  AgentFold's own history — three one-line-rule changes, each with full task-folder
  ceremony — is the exhibit. Hence the de-minimis task.
- *Rituals sit where compliance decays*: adherence drops ~5.6% per step within a
  session (https://arxiv.org/abs/2605.10039) — the end-of-session ritual lives at the
  point of lowest adherence; skills silently fail to trigger in 56% of cases without
  always-loaded pointers (https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals).
  Compaction erases constraints (violations 0% → 30% post-compaction,
  https://arxiv.org/abs/2606.22528). Hence the adapter-hooks task.
- *Contract content doctrine*: context files generally don't raise task success and
  add ~20% cost, except minimal/operational/non-guessable content
  (ETH Zurich, https://arxiv.org/abs/2602.11988); repo *overviews* are the least
  useful section; rule-following collapses around N≈80 instructions
  (https://arxiv.org/html/2607.19257). Count rules, not lines, when budgeting.
- *Handover template gap*: the most-cited high-value handoff field is the
  failed-attempts list — exactly what compaction loses
  (https://mer.vin/2026/04/managing-handoffs-in-multi-agent-coding-sessions-fresh-context-without-losing-continuity/).
  Fixed: `templates/handover.md` now has a Dead ends section.
- *Claims need leases*: kanban-md's auto-expiring claims
  (https://github.com/antopolskiy/kanban-md) are the cleanest published answer to
  stale claims; folded into the coordination-write-rules task.
- *23% of repos have stale references in AI config files*
  (https://arxiv.org/abs/2606.09090) — the link check + expiry are the right
  defenses; keep them.

---

## Part 3 — Disposition

**Fixed directly (merge `fix/design-review-hardening`, reviewable via
`message-queue/needs-human/reviews/design-review-direct-fixes.md`):** provenance
principle + guardrail + queue rule + CONTRIBUTING review gate; README enforcement
honesty; delete-after-folding wording; queue scope claim; schema-migration wording;
Review-by single-sourcing + stagger; Dead ends handover section; pair-mode handover
alignment; gardener prune note; templates budget exemption.

**Filed as backlog tasks (in recommended order):**

1. `2026-07-22-severity-tiers-for-reconciler-findings`
2. `2026-07-22-retry-filing-automation-and-waivers`
3. `2026-07-22-finalize-coordination-write-rules`
4. `2026-07-22-de-minimis-path-for-micro-changes`
5. `2026-07-22-provenance-checks-for-instruction-files`
6. `2026-07-22-agent-adapter-ritual-hooks`

**Left alone deliberately:** local-time conversation timestamps (won't sort across
timezones — acknowledged trade-off in the ADR, not worth churn); task-id references
being socially enforced (ADR acknowledges it); per-commit full test runs (fine at
this scale).
