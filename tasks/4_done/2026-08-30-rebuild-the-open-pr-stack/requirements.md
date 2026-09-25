# Recovery requirements

## Verbatim owner request — 2026-08-30

The following is the owner’s exact request, retained as source data.

```text
[https://github.com/QuentinMeow/agentfold/pulls](https://github.com/QuentinMeow/agentfold/pulls) I have PR's that's conflicting. use [$agent-orchestration](/Users/quentinmiao/code/dotagents/skills/agent-orchestration/SKILL.md)  to research on local changes and PRs, and reason about each changes are needed or not, and do whatever you need to create mergeable PRs (stacked PR) to include all useful changes. Discarded / temporary changes can be ignored, I only need the final correct changes. Feel free to drop existing PRs and create new ones instead. Don't block yourself. You have 8 - 12 hours to do this.
```

## Interpretation

- [user] Research both open PRs and local changes; retain useful final behavior, exclude temporary/discarded work.
- [user] Existing PRs may be replaced; the final deliverable is a mergeable stacked PR set.
- [user] Proceed without blocking questions within the offered 8–12 hour window.
- [derived] Preserve original refs, staged merge patch, and owner checkout until recovery has been verified; no main product changes will be merged as part of this request.
- [derived] Prefer a shallow stack with explicit keep/drop decisions, passing repository gates, fresh-context five-lens verification and cross-vendor refutation.
- [derived] Working baseline is origin/main 326d8ed5fa4f89eaa1402a54d8377dba5946be12; the installer initially selected stale local main, corrected before any work unit.

### Environment matrix

- Owner checkout: unfinished merge, 79 staged paths, ignored nested probe worktrees and agent adapters; inspect and preserve.
- Integration and worker worktrees: clean tracked baseline plus repository bootstrap, no copied private configuration.
- Cold clone: fresh repository and bootstrap, validates tracked inputs and runner discovery.
- Owner-environment final validation must account for the preserved dirty merge; do not present a clean worktree result as proof of that old staged state.

### Interrogation disposition

Resolved: autonomous reversible reconstruction is authorized; final PRs stay open. Deferred: no user decision currently needed. Risks: historical immutable records, review receipts, missing task scope, and cross-vendor CLI availability require evidence rather than assumptions.
