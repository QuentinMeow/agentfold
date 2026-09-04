# Desired state

**Last-updated:** 2026-09-04

Where this repository is going, as goal entries copied from the goal template in
`templates/` (`templates/README.md` maps it). Position is priority and `G<n>` is identity:
an id is never reused, and confirmed goals are listed before agent-proposed ones.

## G9 — Several coding agents develop this repository in parallel, see each other's tasks, resume after an interruption, and stop later pull requests from re-resolving the same refactor conflict

**Asked:** 2026-08-31, by the owner, from chat
**Confirmed:** 2026-08-31 by owner

```text
use strongest agent teams to implement this, and also reason about the human workflow for collaborating with agents. Make sure you design for each common development cycle and create common usage scenario upfront, and let subagents verify they work in the end.
请在我的实际开发环境中落地一套可用的工作流。多个编码 agent 要能并行开发、查询彼此任务、中断后接续，并减少后续 PR 重复解决同一次重构冲突。请完成配置与验证，不要停在概念、选型报告或架构图。
```

Done means the workflow is configured and verified in this repository, with a short
operations manual and the five disposable acceptance experiments from the owner's request
document (copied whole into the `requirements.md` of task
`2026-08-03-plan-multi-worktree-safety-remediation`) recorded with real evidence. *(The
development cycles are designed in task `2026-08-03-plan-multi-worktree-safety-remediation`
(pull request #94); none of the five acceptance experiments has run; no operations manual
exists yet; the restack false-accusation defect is under repair in task
`2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`.)*

## G10 — Every task keeps the owner's words, labels what the agent added, and states its fit to a confirmed goal

**Asked:** 2026-09-04, by the owner, from chat
**Confirmed:** 2026-09-04 by owner

```text
we also need to persist the user's idea for ALL TASKS. We MUST DIFFERENTIATE USER'S REQUIREMENT and agent's self-added requirements, and we need a place to document the desired features /end goals for each repo, the full picture, so that we don't miss the goal half way due to AI generated fake goals. At the start of every non-trivial task, agent must compare the end goal, current state and how does the new requirement fits (and let human decide if there's any conflicts, anything doesn't seem intuitive, instead of hacking around and make compromise). Implement this human requirements / agent supplied requirements documentation efficiently
```

Done means every task folder holds the owner's words verbatim in `requirements.md`, every
acceptance criterion says `[user <date>]` or `[derived]`, this file carries provenance and
a confirmation state per goal, and a `core` or `service:` task states its fit before work,
each refused by the reconciler when missing. *(In progress in task
`2026-09-04-keep-owner-words-and-goal-fit-in-every-task`: the templates, the four
reconciler checks, and this file's rewrite; the eight July goals below await the owner's
confirmation.)*

## G1 — A stranger's agent can work here on first clone

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
A stranger's agent can work here on first clone. Boot from `AGENTS.md`, pass the
reconciler, complete a task end-to-end with no human explanation.
```

Done means an agent that has never seen this repository completes a task from a fresh
clone with no human explanation. *(Largely true — needs outside validation.)*

## G2 — Every schema mechanically enforced

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
Every schema mechanically enforced. Each file format in `templates/` has a
matching reconciler check; drift between a template and its check is itself a
finding.
```

Done means no file format exists without a check that refuses drift from it. *(Checks
exist for queue, tasks, memory, handover; template↔check drift detection does not exist
yet.)*

## G3 — One-command adoption

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
One-command adoption. An `npx`/`pipx`-style installer that drops the harness
folders into an existing repo, asks three questions (name, mode, first service), and
wires the hooks — the claude-code-templates playbook.
```

Done means an existing repository adopts the harness with one command and three answers.
*(Not started.)*

## G4 — Per-skill eval canaries

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
Per-skill eval canaries. 3–6 scripted scenarios per skill with expected
behaviors; behavioral skill edits must pass them before merge.
```

Done means every skill ships scripted scenarios and a behavioural edit that fails one
cannot merge. *(Not started.)*

## G5 — Layered public/private workspace as a packaged module

**Asked:** 2026-07-24, by agent codex, from `docs/designs/layered-development-workspace.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
Layered public/private workspace as a packaged module. The topology and
provenance model from `docs/designs/layered-development-workspace.md` shipped as
repository-local tooling: explicit zone manifest/status, same-path override lineage,
sealed public export, capability adapters, and observed backup/scan evidence.
Mounts remain optional adapters rather than the boundary.
```

Done means the layered workspace design runs as repository-local tooling with observed
evidence for each of its claims. *(Design proposed; the first read-only topology inspector
is implemented, and later stages are specified but await coordination filing.)*

## G6 — A queue/task viewer

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
A queue/task viewer. Read-only board rendered from the folders (the folders stay
the source of truth).
```

Done means a read-only board renders the queue and task folders without becoming a second
source of truth. *(Not started.)*

## G7 — The harness survives its own design review

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
The harness survives its own design review. Finding severity tiers so advisory
drift never blocks commits; automated retry filing with waivers; coordination
write rules that match practice; a de-minimis path for micro-changes; mechanical
provenance checks; optional ritual hooks for agent adapters; a core-admission gate
that rejects personal or provider-specific scope.
```

Done means every finding of the July design review is fixed or explicitly deferred. *(The
core-admission gate is implemented; six design-review tasks remain in `tasks/0_backlog/`.)*

## G8 — Critical obligations survive agent forgetfulness and detector failure

**Asked:** 2026-07-22, by agent codex, from `docs/designs/risk-tiered-agent-guardrails.md`
**Confirmed:** no — agent-proposed, clarification `message-queue/needs-human/clarifications/non-blocking-confirm-the-eight-july-goals.md`

```text
Critical obligations survive agent forgetfulness and detector failure. A
consequence-based policy separates preferences, repairable invariants, required
deliberation, and critical boundaries; PII/secret controls layer redacted local
feedback, content-bound evidence, detector canaries, protected exceptions, and
remote authority where available. Every guard is selected through one `hard`,
`soft`, `off`, or `manual` configuration surface; starter mechanisms are
templates, costly agent review is manual by default, and assurance is derived per
obligation and scope from observed coverage, health, and enforcement rather than
configured labels. Sandboxing and controlled egress are excluded unless a separate
design receives explicit human approval.
```

Done means the guard design is implemented under its one configuration surface with
assurance derived from observed evidence. *(Human-reviewed design in
`docs/designs/risk-tiered-agent-guardrails.md`; implementation task
`2026-07-22-universal-guard-mode-configuration` filed but not started.)*
