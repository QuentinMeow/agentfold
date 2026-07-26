# Plan — accelerate the local development feedback loop

- [x] 1. File and claim one task for the performance work, with one integration branch
      and one pull request.
- [x] 2. Add a conservative staged-path test lane that selects only known-safe service
      scopes and falls back to the full suite for every uncertain path or Git state.
- [x] 3. Preserve the existing full isolated runner as the default and add deterministic
      lane, file-selection, reason, and timing output.
- [x] 4. Wire pre-commit to the staged-path lane and document the fast versus full
      verification boundaries without claiming a staged-snapshot guarantee.
- [x] 5. Add focused regression coverage for narrow selection, dependency unions,
      fallback cases, and unchanged full-suite behavior.
- [x] 6. Measure before and after runtime for the reconciler, narrow hook path, and full
      suite; take only adjacent low-risk optimizations supported by the evidence.
- [x] 7. Run independent correctness and blast-radius review over one immutable revision,
      then repair every accepted finding.
- [x] 8. Record exact verification output, publish the task branch, and open one draft
      pull request with a complete file map.
