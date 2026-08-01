# Worklog — Finish the replacement-ref boundary the reconciler is halfway through building

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — claim-the-replacement-ref-boundary (claude)

- Claimed the task, moved it to `1_in-progress`, and deleted its pickup request with the
  reciprocal `Queue actions` link in the same coordination commit.
- Reproduced first: wrote the six `test_replace_ref_cannot_*` regressions and the
  source-level guard, then ran them against the unmodified reconciler. All six exploits
  worked and the guard listed 22 bare invocations — real transcript in `verification.md`.
- Surprise worth not repeating: the regressions are invisible without dropping the
  process-lifetime object caches between the two reads. `git_blob_bytes`,
  `git_object_kind`, `git_merge_base_result` and `git_ancestry_probe` all cache by full
  object ID for the life of the process, so the second read replays the first answer and
  a replacement entry installed in between looks harmless. The tests call
  `forget_git_object_reads`, which re-scopes those caches exactly the way the next
  reconciler process against the same repository would.
- Hardened 22 invocation sites behind a new `RAW_GIT` constant, including the persistent
  `git cat-file --batch` reader every cached object read funnels through and the
  `git cat-file -t` type probe.
- Dead end avoided: `git_merge_base_result` and `git_ancestry_probe` carried a
  `replace_objects` keyword that three callers set to `True`. Blame shows the perf commit
  `d9762aa` introduced it only to preserve what those call sites did bare before the
  refactor — it was never a decision. Deleting the keyword is what makes the source-level
  guard total, because a keyword argument is invisible to a scan over argument lists.
- Shape note: the 07-26 branch covered "forging a review object" and "forging ancestry" in
  one method and spent its sixth `test_replace_ref_cannot_*` name on the rejected rule.
  Here they are two methods, so the six names match the six exploits the acceptance
  criteria list, with none of them the rejected one.
- Did not port, as the task required: the creation-baseline rule,
  `ordinary_request_resolution_evidence_problem`, its
  `test_replace_ref_cannot_change_ordinary_request_resolution_verdict` regression, and the
  evidence-lineage tests.
- One pre-existing test changed expectation, not behavior:
  `test_main_caches_repeated_git_snapshot_reads` matched the HEAD-tree spawn by its bare
  prefix and now matches the hardened one; it still asserts exactly one spawn.
- Full suite 11/11 files, reconciler 0 findings.
