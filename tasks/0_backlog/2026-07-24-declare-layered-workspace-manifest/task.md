# Declare the layered workspace manifest and bounded status view

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-declare-layered-workspace-manifest.md`; `message-queue/needs-agent/requests/future-blocking-complete-parent-before-workspace-manifest.md`

## Goal

Define a versioned, repository-portable manifest template for declared layered-workspace
roles and build a read-only status command over it. The command must extend the topology
inspector without converting configured intent into content, capability, scan, backup,
or publication evidence.

## Acceptance criteria

- [ ] A canonical template owns the versioned manifest schema; active private state is
      supplied explicitly and is not committed to public Git by the tool.
- [ ] The schema can declare integration, publisher, restricted, raw, and temporary
      roots, monotonic control-plane generation/witness, availability, and policy
      references without embedding credentials.
- [ ] Generation updates use an idempotent prepare/local-CAS/commit witness protocol
      with an opaque recovery envelope; a complete state matrix and crash tests cover
      intent-before-write, write-before-staging, staging-before-prepare,
      prepare-before-CAS, CAS-before-commit, commit-before-local-replay, and
      mismatched/competing/rolled-back/unwitnessed states.
- [ ] Status reports each declared logical role and per-layer base/candidate/effective
      identity, origin, publication intent, Git destination/state, binding state, and
      explicit not-inspected/unavailable evidence states.
- [ ] Binding status uses exactly the design's canonical state enum and blocking
      semantics; stale-base and stale-candidate remain distinct.
- [ ] Missing private state fails closed as `private-unavailable`; only an explicit
      non-executing read-only public-only invocation reports
      `private-integration-role: not-declared`.
- [ ] Default output is role-redacted, and tests prove paths, filenames, and private
      manifest values do not enter ordinary logs or errors.
- [ ] The implementation remains read-only: it creates no repository, mount, remote,
      credential, or public export.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- First slice: `automation/inspect_workspace_boundaries.py`
