# Handover — fold reviewed guardrail decisions

**Session:** 2026-07-22 15:35–16:26 PDT, codex
**Task:** 2026-07-22-protect-core-portability (also folded 2026-07-22-design-critical-agent-guardrails)
**Mode:** async

## What happened

- Folded both human review responses: the provenance wording is approved unchanged;
  guardrails are template-first and universally `hard`/`soft`/`off`/`manual`, with no
  sandbox now and costly independent-agent review manual by default.
- Added the accepted guard-mode ADR and implementation backlog task, made the design
  mode-aware throughout, and removed both resolved queue projections.
- Kept deterministic core-portability checks automatic while making semantic review an
  explicitly invoked, full-commit-bound receipt with honest skipped/verified output.
- Updated draft PRs #4 and #6 with focused reviewer checklists; both stacked branches
  are pushed, clean, and green on GitHub Actions.

## How it works now

Pre-commit and PR CI always validate objective core scope, substitution evidence, and
repository-local state; they say that independent review was not invoked. A human may
run a panel and select `--require-review`, which validates a receipt tied to the full
reviewed commit plus task/design/plan inputs. Later bound edits stale it, while
records-only follow-up and byte-identical task-status moves do not. The universal
four-mode runner remains designed and backlogged, not implemented.

## Decisions made for you

- [Guardrails are template-first and mode-configurable](../../../memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md).
- [Core portability keeps deterministic admission and manually selected semantic review](../../../memory/decisions/2026-07-22-core-portability-review-is-manually-selected.md).

## Needs your attention

None.

## Dead ends

- A global mode disclaimer was insufficient because later design sections still stated
  unconditional blocking; the taxonomy, failure behavior, assurance profiles, and
  transition graph were all made mode-aware.
- An unbound historical verdict was too easy to recycle. Early fixes also over-rejected
  shared identity words and invalidated normal status moves; content binding, claimed
  full-label identities, and blob-based task-input comparison replaced them.

## Next steps

Review and merge draft PR #4 before its stacked draft PR #6. Implement
`2026-07-22-universal-guard-mode-configuration` only when ready to turn the approved
template and four-mode semantics into repository automation.

## Deep links

- Task folder: [`tasks/3_in-review/2026-07-22-protect-core-portability/`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/) · Worklog: [`worklog.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/worklog.md) · Verification: [`verification.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/verification.md)
- Pull requests: https://github.com/QuentinMeow/agentfold/pull/4 and https://github.com/QuentinMeow/agentfold/pull/6 · Commits: PR #4 `76d224d..19ba6b0`; PR #6 `d8efe3a..0cd64d8`
