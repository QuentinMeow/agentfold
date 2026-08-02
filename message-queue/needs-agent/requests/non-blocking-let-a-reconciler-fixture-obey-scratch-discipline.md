# Give a fixture the reconciler must see a legal place to live

**Status:** open
**Filed:** 2026-08-02, by claude, from task 2026-07-25-complete-stage-0-verification-transcripts — `AGENTS.md`
**Action:** State in the scratch-discipline guardrail where a fixture the reconciler must scan may live, or make the reconciler scan one named ignored path for that purpose.
**Full context:** `AGENTS.md`
**Resolution evidence:** `AGENTS.md`
**If unanswered:** Nothing stops. A session that has to demonstrate a check keeps writing an untracked fixture at a scanned path and deleting it in the same shell line, which works and is what the Stage 0 transcripts record — but every such session rediscovers by trial that the guardrail as written forbids the only method that produces evidence.

## What you need to know

Two rules in this repository disagree, and a session cannot obey both.

The scratch-discipline guardrail in the root `AGENTS.md` says throwaway files go under
git-ignored `tmp/`, never the repository root. The reconciler's `live_markdown_files`
calls `path_is_git_ignored` and skips every ignored untracked path, and
`path_is_git_ignored` documents that skip as deliberate deference to that same guardrail.
So a Markdown fixture written to `tmp/` is never scanned at all: a clean run over it
proves nothing, and a fixture whose whole purpose is to produce a finding produces none.

Recording the Stage 0 anchor-hole transcripts ran straight into this. The plan for that
task said fixtures would live under `tmp/`, because the guardrail says so; step 1 replanned
on contact. The fixtures were written instead as untracked files under `docs/`, run, and
deleted in the same shell line so nothing could survive a failed run, and nothing was ever
committed. That is a guardrail violation by the letter of the text, chosen knowingly,
because the alternative was a transcript that demonstrated nothing.

The same session needed a control run for exactly this reason: a clean reconciler report
over a fixture is byte-for-byte what an unscanned file prints, so a before-state without a
control cannot distinguish "the checker had a hole" from "the checker never looked".

The cheapest repair is one clause on the guardrail naming what a check fixture may do.
A larger one is a named ignored path the reconciler deliberately does scan, with a test.
Do not treat this as decided — which rule gives is the question, not the answer.

## Done when

The scratch-discipline guardrail in the root `AGENTS.md` says where a fixture the
reconciler must scan may live, or the reconciler scans a named ignored path for that
purpose and a test covers it.
