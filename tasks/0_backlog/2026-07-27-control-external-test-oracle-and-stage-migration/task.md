# Control test completion outside the candidate interpreter

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Parent:** 2026-07-27-configure-test-gates-and-time-budgets
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-control-external-test-oracle-and-stage-migration.md`

## Goal

Build a provider-neutral controller that observes test completion outside every candidate
interpreter, then migrate the base-pinned test floor without weakening the protected base.
Until this task is complete, automatic final transitions and provider-hard execution remain
unavailable.

## Acceptance criteria

- [ ] An external controller, not candidate code or its interpreter, owns the test-file
      lifecycle and records whether each expected assertion stage completed.
- [ ] A base-owned assertion driver never imports or executes candidate bytes; candidate code
      runs only behind a bounded process or service broker under a different UID.
- [ ] The controller gives the driver a private completion channel and single-use nonce that
      the candidate process, environment, filesystem, and descendants never inherit.
- [ ] A test that calls `os._exit(0)` before its assertion marker cannot produce controlled
      completion, a reusable authorization receipt, or an enforcement-eligible result.
- [ ] Missing, truncated, duplicated, reordered, failed, or abruptly terminated stage evidence
      blocks; a child process return code alone is never sufficient.
- [ ] The exact base-pinned tests and support bytes run against exact candidate product bytes,
      while candidate-added or changed tests remain separately identified supplemental evidence.
- [ ] Receipt identity binds the candidate, base, test/support manifests, expected stage graph,
      controller version, execution boundary, environment, and every observed completion record.
- [ ] The final record binds candidate and tested-view digests, the base-owned driver-plan
      digest, expected case count, completed case count, and the private-channel transcript;
      candidate-produced markers alone are never completion evidence.
- [ ] Migration uses a transitional-test change that accepts the old and new regimes, then a
      later production change targeted at that merged base; one pull request cannot claim both.
- [ ] Focused canaries cover interpreter exit, process crash, timeout, output truncation, forged
      markers, deleted tests, changed helpers, stale receipts, and partial stage migration.
- [ ] The core mechanism remains useful across agent runtimes, providers, and adopted
      repositories; provider-specific launch code is a thin optional adapter.

## Links

- Parent design: task `2026-07-27-configure-test-gates-and-time-budgets`
- Test-gate contract: `handbook/testing-gates.md`
- Publisher follow-up: task `2026-07-27-publish-hard-gate-through-external-oidc-app`
