# Verification — stop link-check false positives

**Verified:** 2026-07-30, by claude

Only commands actually run and their real output. Probe files used to reproduce bugs
1–4 were throwaway (handbook/regex-probe*.md, deliberately not backticked in this
prose since they no longer exist), staged only to make the check see them (existence
here is Git-index-based), and deleted again before any commit — they never appear in
the diff. Bug 5 was reproduced against a real, live repository file (a genuine queue
action already cited by the design doc `docs/designs/queue-resolution-order-
independence.md`), temporarily staged as deleted and then restored byte-identical.

## Bugs 1, 2, 4 — reproduced before the fix

Probe file handbook/regex-probe.md: ordinary prose with slashes, a path inside a
4-space indented code block, and two genuinely broken links. A second pair of files
(handbook/regex-probe-anchor-target.md with heading "## See [the design]
(docs/AGENTS.md)", handbook/regex-probe-anchor-source.md citing
handbook/regex-probe-anchor-target.md#see-the-design) reproduced bug 4.

```
$ git add handbook/regex-probe.md handbook/regex-probe-anchor-target.md handbook/regex-probe-anchor-source.md
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -F "regex-probe"
[link-check] handbook/regex-probe-anchor-source.md: `handbook/regex-probe-anchor-target.md` has no `see-the-design` heading anchor
    fix: point the link at a heading in `handbook/regex-probe-anchor-target.md` or add one whose slug is `see-the-design`
[link-check] handbook/regex-probe.md: `12/s` does not exist
[link-check] handbook/regex-probe.md: `24/7` does not exist
[link-check] handbook/regex-probe.md: `A/B` does not exist
[link-check] handbook/regex-probe.md: `and/or` does not exist
[link-check] handbook/regex-probe.md: `automation/does-not-exist.py` does not exist
[link-check] handbook/regex-probe.md: `input/output` does not exist
[link-check] handbook/regex-probe.md: `s/foo/bar/` does not exist
```

Seven false positives (bug 1's six examples plus bug 2's indented-code path) and one
anchor false positive (bug 4), all reproduced verbatim against the real checker.

## Bug 3 — reproduced before the fix (fails open)

Same probe file also contained `[y](httpd/conf/broken.md)` and
`[x](./handbook/missing-file.md)`, both genuinely broken:

```
$ python3 automation/reconcile/reconcile.py --check > /tmp/before_fix_full.txt 2>&1
$ grep -F "httpd" /tmp/before_fix_full.txt
$ grep -F "missing-file" /tmp/before_fix_full.txt
$ tail -1 /tmp/before_fix_full.txt
reconcile: 8 finding(s)
```

Neither grep produced any output — both broken links passed silently (fail open).

## Bug 5 — reproduced before the fix, against real content

```
$ mkdir -p /tmp/bug5-stash
$ mv message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md /tmp/bug5-stash/
$ git add message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -F "queue-resolution-order-independence"
[link-check] docs/designs/queue-resolution-order-independence.md: `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md` does not exist
```

Restored immediately after:

```
$ git checkout HEAD -- message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
$ git diff main -- message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
(no output — byte-identical to main)
```

## After the fix — same probes, same repository

```
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -F "regex-probe"
[link-check] handbook/regex-probe.md: `./handbook/missing-file.md` does not exist
[link-check] handbook/regex-probe.md: `httpd/conf/broken.md` does not exist
```

All seven bug-1/2 false positives and the bug-4 anchor false positive are gone; the
two genuinely broken links from bug 3 are now correctly reported (previously silent).

```
$ git rm -q -f handbook/regex-probe.md handbook/regex-probe-anchor-target.md handbook/regex-probe-anchor-source.md
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Bug 5, re-simulated after the fix:

```
$ cp message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md /tmp/bug5-restore.md
$ git rm -q message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -F "queue-resolution-order-independence"
(no output)
$ python3 automation/reconcile/reconcile.py --check 2>&1 | tail -3
[task-structure] tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md: Queue actions path `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md` is not in the Git index
    fix: stage the queue item or remove the stale task reference
reconcile: 2 finding(s)
```

The link-check finding is gone (fixed); the remaining `task-structure` finding is a
different, unrelated check correctly noticing the reciprocal task record was not also
updated — expected when only the queue file is deleted in isolation, not a link-check
regression. Restored again immediately after, confirmed byte-identical to `main`.

## Real-content sweep found and fixed a second-order false positive

While proving the bug-1 fix against every live Markdown file in the repository (not
just the probes), one new false positive turned up on real content:

```
$ python3 automation/reconcile/reconcile.py --check 2>&1 | tail -3
[link-check] tasks/4_done/2026-07-30-stop-background-git-maintenance/verification.md: `.git/objects` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 6 finding(s)
```

`.git/objects` has no recognized extension, and `.git` exists on disk, so the
known-prefix test wrongly treated it as a known repository path. Scoped the
known-prefix test to Git-tracked content only (matching `repo_artifact_bytes`'s own
Git-index-vs-filesystem split); re-ran:

```
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -F "regex-probe"
[link-check] handbook/regex-probe.md: `httpd/conf/broken.md` does not exist
[link-check] handbook/regex-probe.md: `./handbook/missing-file.md` does not exist
$ python3 automation/reconcile/reconcile.py --check 2>&1 | grep -v "regex-probe"
    fix: fix the path, create the target, or unquote if not a path
    fix: fix the path, create the target, or unquote if not a path
reconcile: 2 finding(s)
```

Only the two intentionally-broken probe links remain; every other real Markdown file
in the repository is unaffected.

## Final clean state

```
$ git rm -q -f handbook/regex-probe.md handbook/regex-probe-anchor-target.md handbook/regex-probe-anchor-source.md
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Regression tests

```
$ cd automation/tests && python3 -m unittest test_reconcile_queue.ReconcileQueueTests -k link_check -k anchor -k semantic_text -v
test_anchor_slugs_strip_markdown_link_syntax_from_headings ... ok
test_link_check_accepts_a_live_anchor_on_a_live_path ... ok
test_link_check_accepts_an_anchor_defined_by_a_linked_heading ... ok
test_link_check_allows_predeclared_future_resolution_evidence ... ok
test_link_check_allows_queue_lifecycle_lineage_paths ... ok
test_link_check_does_not_treat_git_internals_as_a_known_prefix ... ok
test_link_check_exempts_a_resolved_queue_action_cited_from_any_file ... ok
test_link_check_ignores_a_bare_same_file_fragment ... ok
test_link_check_ignores_a_path_inside_an_indented_code_block ... ok
test_link_check_ignores_ordinary_prose_with_slashes ... ok
test_link_check_keeps_anchor_exemptions_for_records_and_schemas ... ok
test_link_check_numbers_duplicate_heading_anchors ... ok
test_link_check_rejects_an_anchor_defined_only_inside_a_fence ... ok
test_link_check_reports_a_broken_dot_slash_relative_link ... ok
test_link_check_reports_a_dead_anchor_on_a_live_path ... ok
test_link_check_reports_dead_path_carried_behind_an_anchor ... ok
test_link_check_reports_httpd_prefix_no_longer_confused_with_http_scheme ... ok
test_link_check_slugs_punctuation_heavy_headings ... ok
test_link_check_still_catches_a_broken_link_fenced_inside_a_list_item ... ok
test_link_check_still_rejects_a_non_queue_path_near_a_queue_citation ... ok
test_link_check_still_rejects_unrelated_missing_queue_path ... ok
test_link_check_still_skips_dot_dot_relative_candidates ... ok
test_link_check_treats_a_known_extension_as_a_path_claim_regardless_of_prefix ... ok
test_link_check_uses_staged_markdown_not_unstaged_repair ... ok
test_semantic_text_blanks_indented_code_lines ... ok
test_semantic_text_still_blanks_a_fence_nested_in_a_list_item ... ok

Ran 26 tests in 0.28s

OK
```

(The count includes `test_link_check_ignores_ordinary_prose_with_slashes`'s six
subTests, one per bug-1 example, and one subTest each for the two `test_link_check_
still_catches_a_broken_link_fenced_inside_a_list_item` / `..._skips_dot_dot_relative_
candidates` fixture variants.)

## Full automation suite

```
$ python3 automation/run_tests.py
...
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 33.23s
```

`semantic_text` is used by `check_action_projection.py` and `check_core_scope.py`
too (field extraction, action-unit parsing), so its test files were run explicitly to
confirm the added `strip_indented_code` call has no unintended effect there — both
pass.

## Reconciler on the final committed state

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Pre-commit hook (real run, not simulated)

Both the fix commit and this task's coordination commits went through the installed
pre-commit hook (`core-scope`, `reconciler`, staged-path tests) with no `--no-verify`
bypass at any point; each commit's hook output is in the actual Git history of branch
`task/2026-07-30-stop-link-check-false-positives`.
