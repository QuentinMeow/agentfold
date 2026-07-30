# Read each repository view once per action-projection run instead of once per path

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-batch-action-projection-git-reads.md`

## Goal

`automation/check_action_projection.py` asks Git about one path at a time.
`candidate_record` runs `ls-files --stage` per path, `candidate_paths` runs `ls-files`
per prefix, and `tracked_regular_file` runs `cat-file -s` per object, so a run that
inspects fifty queue paths pays fifty index reads for an index that cannot change
underneath it. Measured over its own test module, 1,288 of 1,496 Git spawns come from
this one helper, and the module is the second most expensive file in the suite at
16.15s. The same views read once per run serve every path, which cuts the cost of the
gate itself and of every test that exercises it.

## Acceptance criteria

- [ ] WHEN one check run inspects many paths, THE SYSTEM SHALL read the index or the
      candidate tree once per repository view rather than once per path.
- [ ] THE SYSTEM SHALL return the same verdict as the per-path reads for every existing
      case, including a path recorded at more than one merge stage and a path that names
      a directory rather than a file.
- [ ] THE SYSTEM SHALL NOT let one run's snapshot answer another run, so a repository
      mutated between runs is re-read.
- [ ] A test SHALL fail if a snapshot is reused across runs.

## Links

- `docs/designs/fast-local-test-feedback.md`
- Task `2026-07-30-write-fixture-git-objects-in-process`, which reduced fixture-side
  spawns in the sibling test module
