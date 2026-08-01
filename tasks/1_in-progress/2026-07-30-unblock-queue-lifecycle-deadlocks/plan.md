# Plan — give claimed agent queue items and generated retries a legal way out

- [x] 1. Reproduce all three closed exits of the claim-before-evidence deadlock on a
      generated retry, and settle the suspected ordinary-agent-request sub-case, recording
      the real reconciler messages
- [x] 2. Reproduce the retry garbage-collection escape for both `stale-task` and
      `queue-resolution`, the surviving `blocking-*` retry reaching `transition:merge`
      under an unrelated `--task-id`, and the rejection text lost by delete-then-refile
- [x] 3. Stop a committed agent claim from freezing `Resolution evidence`: move the field
      out of `claim_identity`'s agent key set and make it agent-mutable in
      `immutable_action_text`, leaving every human-side rule untouched
- [x] 4. Register `stale-task` in `CHECKS` and make the runner deduplicate checks by
      function identity, so each finding is still reported exactly once
- [x] 5. Name the retry garbage-collection predicate and tie it to what
      `queue_deletion_problem` will certify, so the two cannot drift apart again
- [x] 6. Emit `**Resolution evidence:**` from `retry_text`, add it from
      `refresh_retry_text` only when absent, and restore a deleted retry's committed text
      when `--file-retries` refiles a still-live finding
- [x] 7. Add regression tests: each closed exit, the live evidence establishment, the
      surviving receipt-transferability invariant, the `stale-task` clearance and single
      report, an every-emitted-id-is-registered guard, and the preserved rejection text
- [x] 8. Full suite green and `--check` 0 findings, both recorded in `verification.md`
      with real output; write `design.md` with the `## Core fit` receipt and the worklog
