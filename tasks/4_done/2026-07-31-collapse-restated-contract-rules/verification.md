# Verification — collapse restated, circular, and unenforced contract rules

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reconciler, before the change (at `ed3a9ee`, via `git stash push -u`)

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Reconciler, after the change

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0
```

Same finding set before and after: zero blocking findings both times.

## Full test suite

```
$ python3 automation/run_tests.py
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 28.94s
```

## The generated index matches its sources

```
$ python3 automation/reconcile/reconcile.py --fix-index && git diff --stat memory/index.md
memory/index.md regenerated
```

No diff: the committed `memory/index.md` is exactly what the generator produces from the
memory files. It was never hand-edited.

The two entries the generator's new branch changed:

```
-- [Guardrails are template-first and mode-configurable](decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md) — Guardrails ship as templates …
+- [Guardrails are template-first and mode-configurable](decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md) **[amended]** — Guardrails ship as templates …
-- [The markdown edge graph ships mined co-change first, …](decisions/2026-07-25-markdown-edge-graph-architecture.md) — … commit the generated artifact, offer three per-folder freshness modes …
+- [The markdown edge graph ships mined co-change first, …](decisions/2026-07-25-markdown-edge-graph-architecture.md) **[amended]** — … commit the generated artifact, offer three per-folder freshness modes …
```

`2026-07-23-queue-resolution-preserves-review-intent.md` already printed `**[superseded]**`
(the generator keys on its successor's `Supersedes:` line); the ADR file now says so too, so
the index and the file agree.

## Contract line budgets

```
$ wc -l AGENTS.md handbook/AGENTS.md history/AGENTS.md tasks/AGENTS.md memory/AGENTS.md message-queue/AGENTS.md README.md skills/*/SKILL.md
     122 AGENTS.md                          (budget 140)
      13 handbook/AGENTS.md                 (budget 60)
      60 history/AGENTS.md                  (budget 60)
      60 tasks/AGENTS.md                    (budget 60)
      34 memory/AGENTS.md                   (budget 60)
      60 message-queue/AGENTS.md            (budget 60)
     122 README.md                          (budget 140)
      46 skills/adversarial-review/SKILL.md (budget 70)
      50 skills/ask-me-anything/SKILL.md    (budget 70)
      44 skills/memory-gardener/SKILL.md    (budget 70)
      44 skills/session-handover/SKILL.md   (budget 70)
```

`history/AGENTS.md` and `tasks/AGENTS.md` sat at exactly 60 before the change and still do:
both edits were rewrites in place, not additions. `message-queue/AGENTS.md` is at 60 and was
not touched — the canonical prefix statement is the text that was already there.

## No rule was lost — before and after, each deleted clause

Every clause below was deleted from at least one copy. BEFORE is the deleted text; AFTER is
the surviving text, quoted from `message-queue/AGENTS.md` at the line given. Both columns
are quoted contract prose, fenced so nothing here reads as a new instruction.

```
BEFORE  blocking-: a named current task, transition, or operation cannot proceed now.
AFTER   L16  blocking-<slug>.md: a named current task, transition, or operation cannot proceed.

BEFORE  future-blocking-: work may continue, but must stop at a named date, event, or
        transition.                                        <- the drifted copy
AFTER   L17-18  future-blocking-<slug>.md: work continues until an explicit UTC date,
        event, or transition; unresolved action stops there.

BEFORE  non-blocking-: this message never stops work and names the safe unattended outcome.
AFTER   L19-20  non-blocking-<slug>.md: the action never stops work and names the safe
        unattended outcome.

BEFORE  The filename prefix is canonical. Do not add a separate **Blocking:** field.
AFTER   L22  The filename is canonical; never duplicate Blocking.

BEFORE  Risk severity does not determine the prefix.
AFTER   L20  Prefix is dependency timing, not risk severity.

BEFORE  A live action may move only toward an earlier dependency:
        non-blocking -> future-blocking -> blocking.
AFTER   L22-23  Live timing may only escalate non-blocking -> future-blocking ->
        blocking, updating every link in one commit.

BEFORE  Weakening creates an authorized replacement, and no human timing changes with or
        after the first concrete response.
AFTER   L24  Weakening needs an authorized replacement; a concrete human response freezes
        timing.   (also L60: timing never changes after that response)

BEFORE  UTC dates can be checked against the repository clock. An arbitrary named event,
        transition, or operation is only an agent-attested acknowledgement ...
AFTER   L56-58  UTC dates are clock-checked; other timing is agent-attested absent a
        validating adapter

BEFORE  Every review predeclares non-queue Resolution evidence distinct from its target ...
AFTER   L55-56  Every item predeclares non-queue Resolution evidence; a review keeps it
        distinct from its target.

BEFORE  ... then a kebab-case slug
AFTER   handbook/naming-conventions.md, the "Queue items" bullet, which owns the grammar
```

Three clauses were **not** deletable because no other file carried them; they were kept in
place and only the surrounding restatement was removed:

- `skills/memory-gardener/SKILL.md` — a gardening item's future boundary "is normally the
  deletion date". Kept, reworded to sit beside the link.
- `skills/adversarial-review/SKILL.md` — a panel review's safe unattended result is
  "normally do not merge". Kept verbatim.
- `skills/session-handover/SKILL.md` — "remaining stopped is valid" as a safe unattended
  result. Kept verbatim.
- `templates/README.md` — the template-local mechanic that each queue template ships all
  three timing blocks and you keep the one matching your filename. Kept, since
  `message-queue/AGENTS.md` describes the rule, not the template's shape.

## Every restating file now reaches the owner in one hop

```
$ grep -c 'message-queue/AGENTS.md' <the thirteen edited files>
templates/queue/clarification.md:1
templates/queue/decision.md:1
templates/queue/request.md:1
templates/queue/retry.md:1
templates/queue/review.md:1
templates/README.md:1
handbook/human-action-guide.md:1
handbook/collaboration-modes.md:1
handbook/decision-guide.md:1
skills/adversarial-review/SKILL.md:1
skills/ask-me-anything/SKILL.md:2
skills/memory-gardener/SKILL.md:1
skills/session-handover/SKILL.md:2
message-queue/needs-human/reviews/README.md:1
```

```
$ grep -rn "future-blocking-: " templates/
exit=1
```
No matches: the drifted definition is gone from every template.

```
$ grep -c "future-blocking" message-queue/AGENTS.md
3
```
The owner still states it.

## Precedence terminates — followed by hand

1. Root `AGENTS.md` boot step 3 → "the closest `AGENTS.md` up the tree from a file is the
   one that applies, and leaf contracts only add local rules to this one. Precedence and
   the repair for a conflicting leaf are stated once, in
   `handbook/principles/folder-as-a-service.md`."
2. `handbook/AGENTS.md` → "Contract precedence is stated once, in the root `AGENTS.md` boot
   sequence; this folder does not restate or invert it." **No counter-claim.** The loop is
   gone.
3. `handbook/principles/folder-as-a-service.md` → "Contracts nest, closest wins … Child
   files add local context only; they never restate or contradict an ancestor — a conflict
   is a bug in the child." Terminates: it cites the AGENTS.md standard, not another repo
   file.
