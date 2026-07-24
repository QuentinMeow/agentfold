# Review layered instruction admission before enforcement

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-review-layered-instruction-admission.md`; `message-queue/needs-agent/requests/future-blocking-resolve-lineage-and-provenance-before-instruction-admission.md`

## Goal

Turn the proposed layered instruction-authority rules into one exact, reviewable
artifact after override lineage exists. Reuse the repository's provenance work rather
than creating a second maintainer registry, and do not enforce a new authority policy
until a revision-bound human review approves it.

## Acceptance criteria

- [ ] The proposal binds repository/trust domain, exact path/scope, signer
      role/delegation, schema, predecessor/epoch, and public/private/effective digests
      to explicit receipts; Git author metadata is never sufficient.
- [ ] Free-form `AGENTS.md` is whole-document authority, ordered root-to-leaf only after
      admission, and unavailable/conflicting members block the effective stack.
- [ ] Each free-form admission binds the complete ordered ancestor stack with exact
      path/scope/authority/digest/generation; a new or changed child needs a protected
      compatibility receipt against every admitted public or private ancestor, with no
      automatic semantic merge.
- [ ] Public hard-safety remains monotonic; a private replacement or instruction
      tombstone is an authority conflict until specifically admitted.
- [ ] Public-only remains non-executing read-only inspection; any proposed executable
      mode requires separately reviewed authority-bound compatibility and capability
      isolation.
- [ ] The proposal consumes the canonical provenance mechanism from task
      `2026-07-22-provenance-checks-for-instruction-files` without duplicating schemas
      or authority lists.
- [ ] Before enforcement code is added, an exact-revision human review is filed and
      approved; absent approval, the safe result is no layered instruction enforcement.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- Prerequisite task: `2026-07-24-track-layered-override-lineage`
- Prerequisite authority task: `2026-07-22-provenance-checks-for-instruction-files`
