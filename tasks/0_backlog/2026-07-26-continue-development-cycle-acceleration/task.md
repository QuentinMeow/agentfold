# Keep small-change feedback under one minute and continue bottleneck work

**Claimed-by:** unclaimed
**Filed:** 2026-07-26, by codex, from the owner's continuation request in chat
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-continue-development-cycle-acceleration.md`

## Goal

Make the repository's development loop proportionate to change risk: a small change should
receive useful local feedback in at most 60 seconds, while the complete isolated suite remains
an eventual correctness gate in CI and at deliberate publication or merge boundaries. Once
that policy is working for harness changes—not only the example services—inspect the repository
structure, roadmap, queues, and task graph with independent agents, debate priorities, and
implement the highest-value safe development-speed improvements in one dedicated pull request.

Do not mix the separate queue-resolution correctness repair into the development-speed pull
request. Continue that work on its existing task branch and subject it to its own final review;
its fifth-panel findings and test evidence are recorded in task
`2026-07-26-resolve-queue-items-whose-evidence-already-merged`.

## Starting state

- Draft pull request 16, task `2026-07-26-accelerate-development-feedback`, adds a
  conservative staged service lane. Recorded probes select quote CLI coverage in 1.06–1.27
  seconds. Unknown, automation, task, history, and other cross-cutting paths still fall back to
  the complete suite.
- The same task measured the clean reconciler at 5.28–5.43 seconds and the complete suite at
  214.62–221.17 seconds. On the queue-repair branch, the queue test file alone varied from
  91.73 to 311.67 seconds and complete runs remained roughly three minutes. The suite is green
  in the recorded final runs, not generally broken; its wall time and variance are the problem.
- A failed repair fixture on the speed branch consumed 223.59 seconds before reporting a
  metadata-free test-environment mistake. This is the concrete failure mode the inner loop
  must prevent: a targeted harness mistake should not require a full-suite wait to diagnose.
- The local queue-resolution task branch is unpushed at `b4b75c3`. Four earlier review rounds
  were repaired, but a fifth independent panel blocked
  it on five issues: bypassable raw-Git source enforcement; whole-history materialization;
  noncanonical queue-local evidence paths; optional Markdown-link-title compatibility; and a
  text/bytes error path that raises `AttributeError`. It is not ready to publish.

## Required test policy

- During implementation, run only the smallest discriminating affected checks, with an
  aggregate local feedback budget of 60 seconds per small change. If the safe selected set
  exceeds the budget, run a deterministic smoke/focused subset locally and defer the rest.
- Keep the complete isolated suite authoritative, but run it once after a coherent repair is
  stable and in required CI for every pull request. Do not rerun it after documentation-only
  records or every checkpoint commit. A full run is also appropriate before changing a draft
  to ready, merging, or releasing.
- Make deferred coverage visible and merge-blocking through required remote checks. A fast
  local result must say what it selected and what remains deferred; it must never be described
  as full correctness evidence.
- Prefer explicit, fail-closed source-to-test ownership for automation modules over broad path
  guesses. Measure parallelism or sharding before adopting it because Git-heavy isolated tests
  may contend for filesystem and process resources.
- Until an automation-aware fast lane lands, accumulate a coherent harness repair with focused
  tests and pay the full pre-commit cost once. Do not create many small commits that each trigger
  the complete suite.

## Acceptance criteria

- [ ] A representative small service change and a representative small automation change each
      receive deterministic local feedback in no more than 60 seconds, with the selected tests,
      reason, elapsed time, and deferred coverage reported.
- [ ] Unknown or unsafe change shapes fail closed either to the complete suite or to an explicit
      “full suite deferred to required CI” outcome that cannot be mistaken for merge admission.
- [ ] The complete isolated suite remains discoverable and runs in required pull-request CI;
      publication records include one final full-suite result and the remote run URL.
- [ ] Test timing is broken down by file or shard, the dominant cost and variance are measured,
      and any parallelism, caching, or selection change is justified by before/after evidence.
- [ ] The fifth-panel findings on the queue-resolution branch are repaired with focused
      regressions under the local budget, followed by one complete-suite run and a fresh
      three-agent revision-bound adversarial review before that separate branch is published.
- [ ] Independent investigators inspect repository structure, roadmap, live queues, task graph,
      current pull requests, and development-cycle bottlenecks after the feedback policy is
      stable; independent designers compare priorities before the main agent decides the order.
- [ ] Implement only bounded, high-value improvements that fit the remaining session and survive
      focused verification plus independent review; preserve larger ideas as separately filed
      tasks rather than forcing them into the pull request.
- [ ] Publish one dedicated development-speed pull request with an evidence-based summary. Begin
      closeout after roughly eight hours and leave a handover listing completed work, unresolved
      attention items, and the next prioritized actions.

## Links

- Existing speed task and draft pull request: `2026-07-26-accelerate-development-feedback`
- Queue correctness task: `2026-07-26-resolve-queue-items-whose-evidence-already-merged`
- Known admission-event race: `2026-07-25-fix-pull-request-admission-event-race`
- Full runner: `automation/run_tests.py`
- Reconciler: `automation/reconcile/reconcile.py`
- Current roadmap: `roadmap/current-state.md`
- Desired state: `roadmap/desired-state.md`
