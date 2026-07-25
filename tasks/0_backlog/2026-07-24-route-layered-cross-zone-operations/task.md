# Route layered cross-zone operations through explicit plans

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-route-layered-cross-zone-operations.md`; `message-queue/needs-agent/requests/future-blocking-resolve-manifest-before-cross-zone-operations.md`

## Goal

Add a dry-run planner for create/import, copy, move, rename, link, promotion, and
cleanup across declared layered-workspace zones after manifest/status exists. Make
classification inheritance and loss/export gates visible without giving the first
implementation authority to delete durable data or publish content.

## Acceptance criteria

- [ ] Every plan names source and destination roles, operation, resulting
      classification, required evidence, rollback point, and blocked/ready state.
- [ ] Unknown imports remain unclassified; cross-zone copy is export plus import; and
      cross-zone move keeps the source until exact destination and recovery evidence
      passes.
- [ ] Links retain target classification and cross-zone links cannot make content
      publishable; unresolved, escaping, looping, or broken targets fail closed.
- [ ] Temporary cleanup is bounded to one identity-verified temporary root and never
      derives a recursive target from an unresolved variable, glob, or symlink.
- [ ] Every recursive cleanup freezes the operation's mount topology, enumerates and
      rejects descendant/alternate mount or filesystem identities, and uses an
      identity-bound descriptor-relative target even when the zone is disposable.
- [ ] Durable deletion plans use an identity-checked atomic quarantine transition and
      descriptor-relative deletion so a concurrent path replacement cannot become the
      target.
- [ ] The deletion adapter drains or revokes every writer/descriptor/mapping/mount,
      revalidates after that OS-enforced fence, and operates on an immutable snapshot;
      inability to attest the fence remains blocked.
- [ ] Repeated failures use one canonical key over exact operation, source/destination
      roles and stable identities, stable workspace/manifest identity, candidate digest,
      policy revision, canonical finding-set digest, decision consequence, and required
      authority; retry receipts attach to that same decision subject.
- [ ] The adapter atomically compare-creates the deterministic queue key, the reconciler
      rejects duplicate live keys, and a changed decision input or answered action uses
      a distinct linked successor.
- [ ] The first implementation emits and tests plans only; no durable deletion,
      protected-zone declassification, export, or public push is executed.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- Prerequisite task: `2026-07-24-declare-layered-workspace-manifest`
