# Research — parallel-agent harnesses and evaluation

**Observed:** 2026-08-31; product facts can change after this date. `Verified` below means
an official page, fixed source revision, or repository/API
observation supported the statement. `Assessment` is the architecture judgment drawn from
those facts. No product was installed or fault-tested in this pass.

## Result

No evaluated product earns AgentFold's complete canonical core today. The market has mature
pieces for agent execution, shared messaging, task graphs, isolated workspaces, dashboards,
and GitHub delivery, but no candidate was shown to also preserve AgentFold's repository-owned
provenance, human/agent action ledger, immutable evidence, recovery receipts, and admission
checks. The practical architecture is a small vendor-neutral evidence/governance core with
replaceable execution and visibility adapters.

## Vibe Kanban

**Level:** a real, medium-to-large open-source developer product, not a toy; unacceptable as
a new canonical dependency because continuity has failed.

- Verified: the fixed `4deb7eca8f381f7cbc1f9d15515a9ab8f8009053` source snapshot has a
  multi-language desktop/local stack, worktree-based workspaces, parallel agent sessions,
  diff/review/preview/PR surfaces, multi-platform release automation, and an Apache-2.0
  license. See the [repository](https://github.com/BloopAI/vibe-kanban),
  [workspaces](https://vibekanban.com/docs/workspaces),
  [supported agents](https://vibekanban.com/docs/supported-coding-agents), and fixed
  [test workflow](https://github.com/BloopAI/vibe-kanban/blob/4deb7eca8f381f7cbc1f9d15515a9ab8f8009053/.github/workflows/test.yml).
- Verified: bloop announced its shutdown and removal of remote projects, issues, comments,
  and organizations; local workspaces were left available. See
  [Goodbye bloop](https://vibekanban.com/blog/shutdown). The last examined release was
  [v0.1.44](https://github.com/BloopAI/vibe-kanban/releases/tag/v0.1.44-20260424091429),
  and community succession was still being discussed in
  [discussion 3424](https://github.com/BloopAI/vibe-kanban/discussions/3424).
- Assessment: retain its workspace/review interaction as reference material or try a
  delete-and-rebuild, read-only UI experiment. Promoting it would mean adopting a large
  cross-platform fork after its commercial control plane shut down.
- Actual use effect: a developer gets the strongest local visual workflow of the candidates
  reviewed here, but AgentFold would still need its own task/action/evidence rules and would
  inherit the maintenance of the abandoned product surface.

## Beads and Gas Town

**Level:** Beads is a high-adoption, strongly engineered but young task substrate; Gas Town
is the closest open-source full-stack parallel-agent harness, also young and operationally
heavy. Neither is a low-risk core replacement yet.

- Verified: the Beads charter deliberately owns issue primitives and leaves routing,
  scheduling, retries, workflow semantics, and cross-system coordination to higher layers.
  See the fixed [project charter](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/engdocs/PROJECT_CHARTER.md).
- Verified: Beads has atomic same-database claim operations, dependencies, history, a Dolt
  embedded/server architecture, migration checks, cross-platform CI, backup commands, and
  substantial release automation. See [coordination](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/multi-agent/coordination.md),
  [Dolt modes](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/architecture/dolt.md),
  [migration discipline](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/internal/storage/schema/migrations/README.md),
  and [workflows](https://github.com/gastownhall/beads/tree/d530cddfa64b174930bddc6c5949b127a450fc13/.github/workflows).
- Verified: server-backed multi-writer use adds a Dolt service; federation documents
  clone-local claim leases; ordinary Git clone does not fetch `refs/dolt/data`; upgrades
  require a designated migrator and coordinated bootstrap. See
  [federation](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/multi-agent/federation.md),
  [sync setup](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/getting-started/sync-setup.md),
  and [upgrade runbook](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/getting-started/upgrading.md).
- Verified: fixed governance files record recent corrupting, duplicate, and edited migration
  incidents followed by tighter policy. See [CODEOWNERS](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/.github/CODEOWNERS)
  and [maintainer guidelines](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/PR_MAINTAINER_GUIDELINES.md).
- Verified: Gas Town layers Beads/Dolt with roles, worktrees, mail/handoff, daemon recovery,
  merge machinery, and observability. See its fixed
  [architecture](https://github.com/gastownhall/gastown/blob/649b832b7672bc7a2dbef26f5983aba6198b819b/docs/design/architecture.md)
  and [provider integration](https://github.com/gastownhall/gastown/blob/main/docs/agent-provider-integration.md).
- Assessment: trial Beads only as a disposable task-index/claim projection; trial Gas Town
  first when evaluating an entire scratch control plane. Do not dual-write canonical state.
- Actual use effect: Beads makes dependency queries and claims much better but does not give
  the human a complete control room; Gas Town supplies the control room and recovery roles,
  at the price of Dolt, daemons, terminal/session machinery, a specialized mental model, and
  a much larger failure surface.

## Other mature candidates

| Candidate | Verified strength | Missing or costly boundary | Best AgentFold role |
|---|---|---|---|
| GitHub Agent HQ / Agent Control Plane | Native issue-to-session-to-draft-PR flow, logs, commands, diffs, status, enterprise policy/audit; control plane announced GA while partner agents were preview ([Agents tab](https://github.blog/changelog/2026-01-26-introducing-the-agents-tab-in-your-repository/), [control plane and partner agents](https://github.blog/changelog/2026-02-26-claude-and-codex-now-available-for-copilot-business-pro-users/)) | No verified peer message bus or durable dependency graph equivalent to AgentFold's records | First visibility and GitHub-delivery trial |
| Conductor | Multiple isolated workspaces, local worktrees/cloud sandboxes, checkpoints, history, diff/check/PR workflow, multiple coding agents ([parallel agents](https://www.conductor.build/docs/concepts/parallel-agents), [workspaces](https://www.conductor.build/docs/concepts/workspaces-and-branches), [checkpoints](https://www.conductor.build/docs/reference/checkpoints)) | Closed product; API/MCP documented as beta; no verified durable peer task graph | Human workspace/control-plane adapter |
| OpenHands | Open-source multi-model runtime, Docker/VM sandbox options, append-only event persistence and conversation restore ([repository](https://github.com/OpenHands/OpenHands), [persistence](https://docs.openhands.dev/sdk/guides/convo-persistence), [sandbox](https://docs.openhands.dev/openhands/usage/sandboxes/overview)) | Self-hosting and sandbox operations; no verified worktree-to-merge-queue plus peer task system | Runtime/persistence adapter |
| Worktrunk | Focused, low-operations worktree lifecycle and agent activity primitive ([repository](https://github.com/max-sixty/worktrunk), [agent integration](https://worktrunk.dev/claude-code/)) | No task graph, peer messages, orchestrator, or durable recovery ledger | Replaceable worktree primitive |
| LangGraph / Microsoft Agent Framework | Mature graph/handoff/checkpoint/HITL building blocks ([LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [Agent Framework workflows](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/)) | No coding workspace, branch, PR, or repository-governance lifecycle without custom product work | Only if AgentFold intentionally builds a workflow service |

## Claude and Codex messaging

- Verified: Claude Agent Teams provides named lead-to-teammate and teammate-to-teammate
  messaging plus a shared task list. Teammates share a working directory, in-process
  teammates do not resume, and the feature is documented as experimental. See
  [Agent Teams](https://code.claude.com/docs/en/agent-teams) and
  [parallel agents/worktrees](https://code.claude.com/docs/en/agents).
- Verified: Claude's newer cross-session messaging transports text between separate local or
  remote sessions but does not transfer conversation history, files, permissions, a shared
  task graph, worktrees, or a PR lifecycle. See
  [cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging) and the
  [Claude Code changelog](https://code.claude.com/docs/en/changelog). On this host,
  `claude --version` returned `2.1.238`; its `--brief` help describes `SendUserMessage`, which
  is agent-to-user and is distinct from Agent Teams peer messaging.
- Verified: Codex subagents can be spawned, followed up, interrupted, and waited on; Codex
  worktree chats provide separate checkouts. The official materials reviewed did not prove
  peer-to-peer messaging or a durable shared task graph. See
  [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and
  [Codex worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees).
- Assessment: messaging improves latency and coordination but is transport, not authority.
  A message cannot prove task completion, writer revocation, review approval, or durable
  recovery; those claims still require the authoritative fact owner and evidence receipt.

## Harness testing and self-evolution

The evaluation design follows evidence from official harness guidance and failure reports:

- Isolate tasks, record multiple trials, prefer deterministic outcome checks, and calibrate
  model judges ([Anthropic agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).
- Pin compute/network/concurrency because infrastructure changes can move scores materially
  ([Anthropic infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise)).
- Remove future-answer Git refs/remotes/reflogs and QA the task/grader itself
  ([SWE-bench leakage issue](https://github.com/SWE-bench/SWE-bench/issues/465),
  [OpenAI Verified audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/),
  [OpenAI Pro audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)).
- Treat self-improving systems as candidate generators because real experiments observed fake
  test logs and objective-marker removal ([Darwin Gödel Machine](https://sakana.ai/dgm/)).
- Use independent skeptical review because agents are biased toward praising their own work
  ([Anthropic long-running harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps));
  reviewer diversity still needs calibration because model errors correlate
  ([ICML 2025](https://proceedings.mlr.press/v267/kim25e.html)).

## Promotion gate

Before any product owns a canonical fact family, a scratch-repository bake-off must prove:
atomic claims without duplicates; crash/restart around every durable write; same-file and
cross-file conflict preservation; replica outage and stale-claim recovery; schema upgrade and
backup restore; human visibility for every state; reconstruction without chat; deletion and
rebuild of the adapter; unchanged repository gates; and at least Claude and Codex execution
backends. Failure leaves the adapter disposable and Git records authoritative.

## Unverified

- No candidate was installed, load-tested, upgraded, crashed, or restored in this pass.
- Public stars, downloads, funding, and vendor customer counts were not treated as production
  reliability evidence.
- No official source reviewed here proves universal crash recovery, exactly-once execution,
  or a writer fence across every provider and machine.
- The cross-provider refuter was not run because sending candidate repository bytes to an
  external model requires separate publication authorization.
