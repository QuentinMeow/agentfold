# Design notes — protect AgentFold core portability

**Status:** decided

## Problem

The rejected change solved a real personal operating problem, and part of its diagnostic
was usable by more than one agent. That was mistaken for proof that it belonged in
AgentFold. Agent independence is only one admission test: core also has to be generally
useful to AgentFold's lifecycle, independent of one external provider, and safe to adopt
in an unrelated product repository.

The existing contracts stated portability but no mechanical gate asked “why here?”
Reviewers therefore tested correctness and safety inside the proposed solution without
first challenging its repository boundary.

## Root cause

1. “Make this permanent for future Codex sessions” was interpreted as “version it in
   the current repository.” The correct persistence boundary was personal configuration
   under the user's Codex home, or a separate personal plugin/config repository.
2. A GitHub authentication classifier was described as portable because multiple agents
   could run it. It remained provider- and use-case-specific, so portability did not
   make it an AgentFold lifecycle primitive.
3. The portable-looking diagnostic and the Codex installer were bundled as one skill.
   Root instructions and roadmap claims then promoted an optional personal adapter into
   core policy.

## Options considered

### Option A — strengthen prose only

State the boundary in contracts. This is necessary orientation but repeats the failure
mode: an agent can forget it or rationalize around it.

### Option B — reject vendor names

Scan core for names such as agents and providers. This catches yesterday's incident but
is stale, evadable, and blocks legitimate research or thin deployment adapters.

### Option C — check in a general adapter framework

Create a paved home for every agent/provider integration. This would encourage the
specific integrations the owner wants kept out and add constraints before a general
interface is proven useful.

### Option D — require a core-fit receipt and independent challenge

Use a narrow Git boundary check to trigger structured architectural questions for core
paths. Deterministic checks validate the receipt and reject obvious user-global state
access; an independent reviewer challenges the semantic claim before review. Chosen:
it forces deliberation without pretending syntax can prove architectural relevance.

## Chosen boundary

AgentFold core must survive three substitutions: another agent runtime, another external
provider, and adoption into an unrelated product repository. Tracked executables do not
configure user-global state. A thin adapter is acceptable only when it forwards to a
canonical repository behavior, adds no policy, is optional, and writes inside the clone.

Personal configuration, provider operations, and product workflows stay in local config,
a private overlay, a separate plugin/repository, or `services/` as appropriate. The
personal GitHub authentication safeguard remains outside AgentFold.

## Core fit

**Agent substitution:** pass — the task receipt and check are plain files, Python, and Git
**Provider substitution:** pass — provider CI only invokes the canonical local check
**Repository substitution:** pass — every adopted AgentFold repository needs a core-scope boundary
**User-global writes:** none
**Why AgentFold core:** this protects the framework's own extension boundary rather than implementing the triggering personal integration
**Thin adapter:** canonical=automation/check_core_scope.py; optional=yes; policy=none; writes=repo-only

## Failure behavior

The local hook checks staged bytes, including its task evidence; pull-request CI checks
the full base-to-head tree. A core change without a task, `core` scope declaration,
complete substitution evidence, or an independent approve majority fails with a routing
message. Obvious home-directory access in changed core executables and canonical skill
instructions fails directly. Research, product code, and unregistered product CI stay
unaffected; thin provider adapters are listed in `automation/core-scope-paths.txt`.
The existing small-fix branch convention remains available outside core; its dedicated
backlog task must design any safe core exception rather than this gate guessing one.
