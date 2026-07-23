# Queue resolution is proven by Git evidence, not a terminal label

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** agent (delegated two-way-door implementation of the owner's queue-first requirement; independently adversarially reviewed)
**Description:** Queue actions resolve through committed claims and boundary-specific Git evidence; external asks are checked projections
**Review-by:** 2027-02-10

## Context

The queue became the canonical surface for every pending human action and durable
cross-session agent action, but a terminal-looking `folding` or `in-repair` value still
let an agent delete an item without proving that its response or work was preserved.
The original failure also remained possible at the provider boundary: a PR could invent
new review questions without queue links.

## Decision

Queue resolution is a versioned Git lifecycle:

- a human response is committed while `waiting`, and the later claim commit changes
  only `Status` to `folding`;
- an agent claim likewise changes only `open` to `in-repair`;
- ordinary actions predeclare non-queue `Resolution evidence` files, all of which change
  in the deletion commit;
- approved reviews revalidate the bound artifact, while non-approved reviews may delete
  only with a live same-boundary successor;
- task pickups prove the atomic backlog-to-claimed task move; generated retries prove
  exact generator identity and absence of their named finding; and
- once activated, deletion-history enforcement cannot be disabled by removing its
  repository marker.

External channels use a provider-neutral projection gate. Every declared review entry
contains one live `needs-human` queue link and no second unlinked ask. A task-scoped
projection includes every human action declared by that task; a channel with no human
ask makes that fact explicit. Provider adapters only pass repository state, external
Markdown, and an explicitly allowed immutable link prefix to the canonical local gates.

This proves repository transitions, not human identity. A committer can transcribe or
fabricate text; authenticated authorship remains an optional provider-control layer.

## Alternatives considered

- Trust terminal status labels — minimal ceremony, but reproduces deletion without
  completion evidence.
- Keep resolved queue files forever — preserves delivery bytes but leaves completed
  actions indistinguishable from pending work.
- Require signed human responses in core — stronger identity, but provider-specific and
  incompatible with chat transcription and repository substitution.
- Classify arbitrary PR prose with an AI model — broad, but nondeterministic and too
  restrictive for future agents; explicit action sections provide a stable boundary.

## Consequences

Resolution takes at least one committed claim and an evidence-producing commit, with
narrow checked exceptions. The ceremony is proportional to actions that must survive
sessions, not to every implementation step. Provider-independent Git checks catch
forgetful agents; stronger authentication can be layered on without changing the queue
schema.
