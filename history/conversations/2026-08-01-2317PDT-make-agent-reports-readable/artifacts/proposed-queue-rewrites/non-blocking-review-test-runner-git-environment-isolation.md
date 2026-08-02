# Should the change that stops the test suite from writing into your own working copy stand?

**Action:** After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.
**Why this matters:** Every test this repository launches from a commit hook depends on this: without it, a test that creates its own scratch repository can end up writing into the working copy you are sitting in.
**If you do nothing:** Nothing stops; the change stands as the repository-wide rule for how tests run, and its task finishes without your judgment on record.

## What you need to know

**Today:** the change is already merged and in force. Every test launched by a commit hook runs under it right now, and nothing waits on your answer.

**What this would change:** your verdict goes on the record — that this is the right boundary for every test the repository runs, rather than something that merely happens to be in place.

**What this does not decide:** it makes no promise about a test that deliberately reaches for the real repository by its full path. Those still touch it, and are meant to.

The problem it solves: when version control launches a hook, it hands the child process settings pointing back at the current repository. A test that then creates a temporary repository of its own can silently inherit those and write into your actual checkout instead of its own sandbox. The change strips them out and starts each test in a fresh, disposable copy placed where ordinary discovery cannot reach back. The task's verification notes include a live probe confirming a secondary linked working copy was left untouched. The changed code is [the test runner](../../../automation/run_tests.py).

## Your choices

The choices differ in what happens to a boundary that is already merged and running: it is confirmed, repaired first, or removed.

### Approve
This becomes the accepted rule for how every test runs. The cost is a permanent layer of indirection: tests no longer run in the obvious place, so anyone debugging one has to know the copy exists before the paths make sense.
*Example consequence:* a test fails and the path in the error is a temporary directory nobody recognises, and the first minute of debugging goes on working out why.

### Request changes
The idea is right but something specific is wrong — a compatibility case that breaks, or a way the isolation still leaks. Name it; an agent repairs it and brings the change back. The cost is that the repair lands on top of code already in use.
*Example consequence:* you point out a tool that needs one of the stripped settings, it gets passed through deliberately, and the boundary gets one documented exception.

### Reject
The approach is wrong and the change comes back out. The cost is that the original problem returns immediately and has to be solved another way.
*Example consequence:* tests run in your working copy again, and the next test that creates a scratch repository can write into it without anyone noticing.

## What I recommend

**Recommendation:** Approve — the failure it prevents is silent and lands in your own working copy, which is the worst combination, and it is already running without incident.
**Strongest case against this:** isolation like this is exactly the kind of machinery that quietly breaks a tool nobody tested with, and the breakage shows up as a confusing failure rather than a clear one. If you have hit unexplained test weirdness since it merged, that is worth naming now.
**Confidence:** low — I am reading a file a previous session wrote rather than the change itself; I confirmed it is merged, its task still parked in review, and its verification notes contain a real linked-working-copy probe, but I re-ran nothing.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-24, by codex, from task `2026-07-24-isolate-test-git-environment`
**Full context:** `roadmap/current-state.md`
**Resolution evidence:** `roadmap/current-state.md`
**Review target:** git:25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e
**Review revision:** git:25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-22
