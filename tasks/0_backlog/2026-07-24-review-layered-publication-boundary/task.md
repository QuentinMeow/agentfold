# Review the layered publication and capability boundary

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-review-layered-publication-boundary.md`; `message-queue/needs-agent/requests/future-blocking-resolve-lineage-and-instruction-before-publication-review.md`

## Goal

Validate the sealed-envelope and capability-isolated publisher reference architecture
as a separate one-way-door design. Produce an exact threat model and human review
artifact; do not build an exporter, introduce public credentials, or push any content
as part of this task.

## Acceptance criteria

- [ ] The threat model binds the exact public base/old OID, candidate tree and commit,
      one refspec, destination URL, authenticated server/adapter key, immutable
      repository identity, credential audience, transport/redirect identity, epoch,
      nonce, expiry, scanner coverage, authority receipt, operation-scoped capability
      receipt, reserved object manifest, and complete candidate Git object closure.
- [ ] The publisher design rejects extra refs, tags, notes, stashes, reflogs,
      alternates, configured refspecs, mirror/follow-tags behavior, stale epochs, and
      unexpected advertised-remote ref changes, while reporting hidden server state as
      unknown absent destination attestation.
- [ ] Capability evidence enumerates principal, mounts, object stores, credentials,
      model/provider, subprocess, network, telemetry, prompt, cache, crash-log, and
      other output sinks plus inherited descriptors, IPC/ptrace, agent/container
      sockets, metadata identities, and connectors on macOS and Linux, under trusted
      operation-lifetime enforcement that cannot expand.
- [ ] Adversarial tests are specified for private-object reachability, detector
      error/unsupported states, dirty publisher state, retry after incident revocation,
      exact server-side ref/epoch compare-and-swap, ambient Git configuration and
      out-of-band payloads, private-session direct-push attempts, pre-upload reservation,
      wrong destination/redirect/audience, extra unreachable received objects, corrupt
      or incomplete pre-existing base closure, lost/retained/unknown outcomes, receipt
      replay across process trees, and hidden retention advertised refs cannot prove.
- [ ] An exact-revision human review approves or rejects the architecture before any
      exporter, capability adapter, credential, template, or publication mode is built.
- [ ] If approved, implementation is split into independently reversible tasks; if
      unanswered or rejected, publication remains blocked.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- Prerequisite tasks: `2026-07-24-track-layered-override-lineage`,
  `2026-07-24-review-layered-instruction-admission`
