# Track layered public candidates and private override lineage

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-track-layered-override-lineage.md`; `message-queue/needs-agent/requests/future-blocking-resolve-manifest-before-override-lineage.md`

## Goal

Implement provenance records for same-path public and private customization after the
manifest/status task is complete. Preserve an explicit public candidate independently
from the private effective result, and bind layered sessions tightly enough that stale
or missing private state cannot silently expose the public base.

## Acceptance criteria

- [ ] Each logical path can bind an admitted public base, optional explicit public
      candidate, private effective result, review base, zone, and ordinary tombstone.
- [ ] An atomic two-result transaction initializes the public buffer only from admitted
      public state, reapplies the private result by three-way operation, revalidates
      every binding, and writes neither result on failure.
- [ ] Files, renames, deletions, and binaries use exactly one canonical state:
      base-only, current, ordinary tombstone, updating, stale-base, stale-candidate,
      textual-conflict, authority-review-required, authority-conflict, or
      private-unavailable, with the design's exact blocking behavior.
- [ ] Layered admission binds repository/ref/HEAD, index, worktree, manifest, lineage,
      independently witnessed generation, base, and effective digest to a short-lived
      supervised lease that invalidates on change.
- [ ] Each mutation binds a single-use nonce, exact lease/session/process generation,
      permitted operation/write set, prior generation, resulting digests, and one
      exclusive-writer compare-and-swap; a durable pre-write intent covers the first
      source write, only a successful `G` to `G+1` CAS plus the matching committed
      witness renews the lease, and protected control state is mediator-only.
- [ ] Prepare/local-CAS/commit recovery is idempotent and tested at every crash edge:
      exact prepared or committed successors replay safely, while missing envelopes,
      competing successors, result mismatches, and unwitnessed local generations stay
      quarantined and `private-unavailable`.
- [ ] Missing or mismatched private state stops protected layered operations; a
      separate explicit public-only mode remains visibly partial.
- [ ] Admitted private-reading sessions either enforce exact private-only endpoints and
      remote-scoped credentials or are local-only; ambient public push transports,
      helpers, credentials, and sockets are unavailable.
- [ ] Sealed publication mode is unavailable unless every process able to read
      integration objects is under the same enforced egress/credential fence; tests
      cover non-session direct-push attempts.
- [ ] The slice creates no exporter, public remote, capability claim, or automatic
      publication path.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- Prerequisite task: `2026-07-24-declare-layered-workspace-manifest`
