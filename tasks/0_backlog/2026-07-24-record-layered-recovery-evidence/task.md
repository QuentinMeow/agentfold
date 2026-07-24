# Record layered backup and restore evidence without overclaiming

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Parent:** 2026-07-24-layered-development-workspace
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-record-layered-recovery-evidence.md`; `message-queue/needs-agent/requests/future-blocking-resolve-manifest-before-recovery-evidence.md`

## Goal

Define and implement repository-portable evidence records for backup, restore, and
loss decisions across every layered-workspace zone. Keep version evidence, replication,
coverage, availability, freshness, and restore verification independent so a configured
job or observed commit cannot authorize unsafe deletion.

## Acceptance criteria

- [ ] One canonical template records exact target/version, coverage, destination or
      snapshot identity, policy-required and independently observed actual failure
      domain/immutability, observation time, expiry, destination/key availability, and
      restore state.
- [ ] Status never treats a local commit, configured remote/job, or unobserved push as
      independent backup evidence.
- [ ] Worktree, refs/objects, index, untracked files, stashes, configuration, and each
      external root can report separate coverage without a synthetic green aggregate.
- [ ] Restore evidence binds a quarantine test to the exact target/version and reports
      untested, failed, stale, unavailable, or verified explicitly.
- [ ] A read-only loss evaluator always requires mount/target identity safety, an
      attested exclusive writer fence, immutable snapshot/quarantine, and post-fence
      source revalidation; only recovery evidence may be replaced by an exact
      target/operation/nonce/expiry-bound human loss-acceptance receipt.
- [ ] Default evidence and failures redact sensitive paths and content; the slice does
      not delete, restore over, replicate, or upload user data.

## Links

- Parent design: `docs/designs/layered-development-workspace.md`
- Prerequisite task: `2026-07-24-declare-layered-workspace-manifest`
- Related guard-mode task: `2026-07-22-universal-guard-mode-configuration`
