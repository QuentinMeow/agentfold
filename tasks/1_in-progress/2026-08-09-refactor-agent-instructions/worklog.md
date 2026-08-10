# Worklog — Refactor repository agent instructions

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-09 — agent-instruction-audit (codex)

- Audited the personal global file and all fourteen tracked `AGENTS.md` contracts. The
  screenshot's compatibility, dependency, and temporary-implementation absolutes conflict
  with explicit repository promises; its other four visible principles are compatible.
- Compared current guidance from OpenAI, the AGENTS.md standard, GitHub, and Anthropic.
  All favor concise persistent guidance, closest-scope rules, progressive disclosure, and
  mechanical enforcement for objective constraints.
- Filed the owner's three-way decision and a pickup request. No global or repository
  instruction text changed; the task remains unclaimed until the decision is folded.

## 2026-08-09 — apply-contract-aware-defaults (codex)

- The owner chose the recommendation in chat and asked for every local change to be
  published through pull requests. The exact sentence was committed before folding.
- The response commit also refreshed the generated open-action index. An answer-only
  candidate failed the reconciler because that index became stale; the response plus the
  generated companion passed without bypassing the hook.
- Folded the answer into the contract-aware-defaults decision, claimed this task, and
  removed its completed human decision and agent pickup actions in the same transition.

## 2026-08-09 — refactor-scoped-contracts (codex)

- Added the recommended compatibility wording to the personal global Codex contract:
  obsolete internal compatibility may be removed after migration, while explicit public
  and persisted contracts remain protected without authorized breaking-change scope.
  The dependency and temporary-bridge defaults were already present in qualified form.
- Clarified the earlier audit language: only the screenshot's absolute compatibility
  deletion rule was a direct conflict. The library and temporary-implementation wording
  were tensions that became compatible once qualified by repository policy and risk.
- Reduced the root contract from 139 to 79 lines, automation from 60 to 40, and history
  from 60 to 42. The root now routes to lifecycle owners; automation keeps agent-facing
  editing invariants instead of implementation narration; history states only the active
  creation contract and immutable-record rule.
- Audited all fourteen tracked contracts. Removed ancestor-owned standard-library rules
  from both quote-service leaves and the accepted-decision routing restatement from
  `docs/designs/`; retained the queue, task, memory, skill, service-parent, docs-parent,
  and service-template contracts because their remaining rules are local to those scopes.
- The final history contract is 44 lines: two lines were added after the first count to
  preserve the exact `awaiting-artifact` projection exclusion and distinguish the one
  handover marker from the three repository schema markers.
