# Desired state

**Last-updated:** 2026-09-04

Where this repository is going, as goal entries copied from the goal template in
`templates/` (`templates/README.md` maps it). Position is priority and `G<n>` is identity:
an id is never reused, and confirmed goals are listed before agent-proposed ones.

## G9 — Several coding agents develop this repository in parallel, see each other's tasks, resume after an interruption, and stop later pull requests from re-resolving the same refactor conflict

**Asked:** 2026-08-31, by the owner, from chat
**Confirmed:** 2026-08-31 by owner

```text
/Users/quentinmiao/Documents/Codex/2026-08-30/ba/outputs/multi-agent-git-implementation-prompt.md check this,  as well as understand the current repo structure[$agent-orchestration](/Users/quentinmiao/code/dotagents/skills/agent-orchestration/SKILL.md)  use strongest agent teams to implement this, and also reason about the human workflow for collaborating with agents. Make sure you design for each common development cycle and create common usage scenario upfront, and let subagents verify they work in the end. You can work for as long as you want, even more than 10 hours are fine. Do whatever you need to unblock yourself. I'm able to answer questions for the first 6 hours. Go full auto after 6 hours. Make sure you reason about the plan and have detailed plans for verifying the results (let subagents search for harness testing and self evolved AI agents).

If you find current repo has problems, fix current repo first. Do the most correct way, finishing implementation is not a hard requirement, I want to do things right instead of done.

In the end, I want all progress in the form of PRs. You don't need backward compatibility, I only need the most correct final version in PRs.
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
here's the handoff from another agent. use highest agent teams (you can spin up 5 - 10 subagents at the same time) to review this design. You need to pick up the work and decide what design to revise, push back, and redesign as needed. Another thing I want to highlight is, we also need to persist the user's idea for ALL TASKS. We MUST DIFFERENTIATE USER'S REQUIREMENT and agent's self-added requirements, and we need a place to document the desired features /end goals for each repo, the full picture, so that we don't miss the goal half way due to AI generated fake goals. At the start of every non-trivial task, agent must compare the end goal, current state and how does the new requirement fits (and let human decide if there's any conflicts, anything doesn't seem intuitive, instead of hacking around and make compromise). Implement this human requirements / agent supplied requirements documentation efficiently (search online for any solid open source light weight implementation and learn from them), then continue working on the task showed below (make sure you find the work correctly from the worktree / branches):
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
**Confirmed:** 2026-09-04 by owner

```text
A stranger's agent can work here on first clone. Boot from `AGENTS.md`, pass the
reconciler, complete a task end-to-end with no human explanation.
```

Done means an agent that has never seen this repository completes a task from a fresh
clone with no human explanation. *(Largely true — needs outside validation.)*
The owner confirmed this goal on 2026-09-04 in chat, in these words about G1, G2, G7, and G8 together: "这些都同意，都算是goal。"

## G2 — Every schema mechanically enforced

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** 2026-09-04 by owner

```text
Every schema mechanically enforced. Each file format in `templates/` has a
matching reconciler check; drift between a template and its check is itself a
finding.
```

Done means no file format exists without a check that refuses drift from it. *(Checks
exist for queue, tasks, memory, handover; template↔check drift detection does not exist
yet.)*
The owner confirmed this goal on 2026-09-04 in chat, in these words about G1, G2, G7, and G8 together: "这些都同意，都算是goal。"

## G5 — Layered public/private workspace as a packaged module

**Asked:** 2026-07-24, by agent codex, from `docs/designs/layered-development-workspace.md`
**Confirmed:** 2026-09-04 by owner

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
The owner confirmed this goal on 2026-09-04 with a reason in his own words: "G5 需要保留的，比如看我的 ~/code/job-finder-toolkit/." The repository meant is `~/code/jobs-finder-toolkit`, a public toolkit whose real data lives in a git-ignored `private/` overlay that is its own repository, guarded by a leak word list and an export script; this goal turns that hand-kept pattern into a checked module.

## G7 — The harness survives its own design review

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
**Confirmed:** 2026-09-04 by owner

```text
The harness survives its own design review. Finding severity tiers so advisory
drift never blocks commits; automated retry filing with waivers; coordination
write rules that match practice; a de-minimis path for micro-changes; mechanical
provenance checks; optional ritual hooks for agent adapters; a core-admission gate
that rejects personal or provider-specific scope.
```

Done means every finding of the July design review is fixed or explicitly deferred. *(The
core-admission gate is implemented; six design-review tasks remain in `tasks/0_backlog/`.)*
The owner confirmed this goal on 2026-09-04 in chat, in these words about G1, G2, G7, and G8 together: "这些都同意，都算是goal。"

## G8 — Critical obligations survive agent forgetfulness and detector failure

**Asked:** 2026-07-22, by agent codex, from `docs/designs/risk-tiered-agent-guardrails.md`
**Confirmed:** 2026-09-04 by owner

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
The owner confirmed this goal on 2026-09-04 in chat, in these words about G1, G2, G7, and G8 together: "这些都同意，都算是goal。"

## G4 — Per-skill eval canaries, manual and optional

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** 2026-09-04 by owner

```text
G4改成手动/可选，不强制。
```

Originally proposed as: "Per-skill eval canaries. 3–6 scripted scenarios per skill with expected behaviors; behavioral skill edits must pass them before merge." The owner confirmed it on 2026-09-04 with one change: the scenarios are run by hand and are optional, never a merge condition. Done means every skill ships scripted scenarios an agent or a human can run when a skill's behaviour changes. *(Not started.)*

## G6 — A queue/task viewer

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** 2026-09-04 by owner

```text
G6 先推迟，我希望最终有网页kanban 来看总体的任务进度。
```

Originally proposed as: "A queue/task viewer. Read-only board rendered from the folders (the folders stay the source of truth)." The owner confirmed it on 2026-09-04 and deferred it: eventually a web kanban shows overall task progress. Done means a read-only web board renders the task and queue folders without becoming a second source of truth. *(Deferred by the owner on 2026-09-04; not started.)*

## G3 — One-command adoption

**Asked:** 2026-07-22, by agent claude, from `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
**Confirmed:** 2026-09-04 by owner

```text
G3未来是需要的，但是我感觉还没准备好，未来一定要，但是现在先不做。
```

Originally proposed as: "One-command adoption. An `npx`/`pipx`-style installer that drops the harness folders into an existing repo, asks three questions (name, mode, first service), and wires the hooks — the claude-code-templates playbook." The owner confirmed it on 2026-09-04 as a goal for later, not now. Done means an existing repository adopts the harness with one command and three answers. *(Deferred by the owner on 2026-09-04; not started.)*
