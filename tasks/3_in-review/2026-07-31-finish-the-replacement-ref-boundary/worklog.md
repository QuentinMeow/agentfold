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

## 2026-07-31 — repair the adversarially reviewed boundary (claude)

An adversarial review of the session above confirmed the vulnerability and the tests but
filed four defects. All four reproduced; all four are fixed. Real transcripts in
`verification.md`.

- The guard was leakier than the previous session claimed. It walked `ast.List` nodes and
  matched element 0 against the literal `"git"`, so six spellings were appended to
  `reconcile.py` at `4ffa8e3` and the guard stayed green on every one: a tuple argument
  list, `[_GIT_BIN, ...]` with `_GIT_BIN = "git"`, an f-string with `shell=True`,
  `[_GIT_BIN] + [...]`, `os.popen`, and `list((...))`. Rewritten to start at the spawn
  call sites; all six now fail it, each with its source text.
- Measured before designing, which changed the design. The obvious fix — reject any
  argument list that is not a literal — was wrong: three call sites in `reconcile.py` and
  three in `run_tests.py` legitimately build a command in a local variable, and one is
  `[sys.executable, ...]`, not Git at all. So the scan resolves names bound by plain
  assignment (mutated only by `append`/`extend`, which cannot touch the head) and
  resolves the program at position 0 to the set of strings it can be.
- The boundary really did stop at the reconciler. Worst of the three: on `4ffa8e3`,
  `check_core_scope.py` returned **zero findings** for a core-fit review that was stale
  by a real `automation/` change and a rewritten task input, because
  `git replace -f $REVIEWED $CURRENT` answered its `rev-parse`, `merge-base`, `diff` and
  `ls-tree` reads at once. That is the core-admission gate defeated end to end, not one
  check bypassed.
- Second worst: `run_tests.py --staged` read the staged diff bare, so pointing HEAD at a
  commit that already held the staged code but an older record left the hook seeing one
  record path and selecting **no tests at all** for a staged code change. An emptied diff
  falls back to the full suite, which is why the exploit has to forge a *narrow* diff
  rather than an empty one — worth knowing before writing that regression.
- `check_action_projection.py` was not on the review's list but is on the guard's: five of
  its six reads passed the flag at the call site and one did not, which is the fragility
  the guard exists to remove. Hardened in `git_output` and the redundant per-call flags
  dropped.
- Judgement call recorded: `git fetch` in `.github/workflows/harness.yml` stays bare. It
  moves objects over the network and decides nothing, and the workflow scan allowlists it
  by name rather than by silence.
- Python floor bit once. `ast.get_source_segment` is 3.8+, and `python3` here is 3.7.6
  while CI takes the runner default, so the guard falls back to the whole source line.
  Both forms are diagnosable, and the docstring says which is which.
- Registering `automation/check_core_scope.py` and `automation/run_tests.py` as inputs of
  `test_reconcile_queue.py` is what makes the guard re-run when either changes; the
  matching assertions in `test_run_tests.py` moved with them.
- Measured the guard's own cost rather than assuming it, because it runs in the
  pre-commit lane: the first working version took 28.7s for one test, since resolving a
  name walked the whole 6,000-line module and it asked about dozens of names. Resolving
  every name in a scope in one walk and memoizing the map on the scope node gives
  identical findings in 3.0s for all six guard tests.
- Full suite 11/11 files, reconciler 0 findings.
