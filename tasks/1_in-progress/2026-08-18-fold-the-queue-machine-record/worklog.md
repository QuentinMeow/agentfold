# Worklog — fold the machine record on new human queue items

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-18 — fold-the-queue-machine-record (claude)

- Filed the task in `0_backlog` with its canonical pickup request, then claimed it in one
  coordination commit — `Claimed-by` set, the folder moved to `1_in-progress`, `plan.md`
  and this worklog added, and the pickup request deleted — and branched
  `task/2026-08-18-fold-the-queue-machine-record` from `main` at `fc8c0af`.
- Baseline re-measured before touching anything: `automation/run_tests.py` 15/15 files,
  exit 0; `reconcile.py --check` 0 blocking findings. `automation/tests/test_reconcile_queue.py`
  carried one uncommitted repair from a concurrent session (`getattr(ast, "Str", None)`,
  for Python 3.12+ removing `ast.Str`); it was adopted unchanged, never re-spelled.
- Implemented the sanctioned fold, the region-based `record-swallow` predicate,
  `fold-shape`, `queue-frozen-skeleton`, the narrowed raw-HTML rule with its
  `parsed ⊆ rendered` companions, `--fix-queue-fold`, the advisory `queue-render`, and
  the `.gitattributes` whitespace opt-out. Real output in `verification.md`.
- Surprise worth not repeating: the specification's tracked-file count (618) was measured
  at an older commit. The real denominator at `fc8c0af` is 623, and the live-item count is
  64 rather than 66. Every number in `verification.md` was re-derived here rather than
  copied from the specification.
- Second surprise: `record-swallow` does not fire on the attack where a fold swallows the
  answer line, because that attack destroys the very landmark the region's lower half is
  defined by. `fold-shape` refuses it. Recorded in `design.md` rather than papered over.
- Third surprise, and the one worth remembering: the hard break lands *inside* the parsed
  value. `FIELD_RE` captured `'pending  '` and `'______  '`, and `PLACEHOLDER_RE` stops
  recognising an unfilled slot with two spaces after it. Most readers happened to strip
  first, so it was safe by luck. Fixed at the source — trailing whitespace is
  presentation, never value — and measured inert on 620 of 623 tracked files.
- Second commit closes five gate holes a weak-model authoring run found: the 700-word
  budget (a coin flip at ~12 words of headroom, now 800 with the count and the cut in the
  finding), a human `Blocks at:` accepting a bare calendar date, `Answer by` allowed to
  equal `Filed`, `operation:` rejecting version dots, and an unfollowable `Review
  revision` message. The sixth, a warning in `message-queue/needs-human/reviews/README.md`
  that the existing files predate the current format, was **not done**: this session was
  told to treat every file under `message-queue/` as frozen. It needs its own commit.

## 2026-08-18 — repair the defects review found (claude)

- Two kill shots closed. `queue-frozen-skeleton` dropped whole mutable field lines, so the
  red team's payload only had to move to the end of one; it now drops a line only when its
  value is byte-identical to the parsed value and carries no raw-HTML token, making
  (skeleton, mutable values) a total partition of the file's bytes. `--fix-queue-fold`
  folded the human's answer line away irreversibly; it never harvests that line now and
  refuses to write any result it cannot leave clean.
- Byte-identical to the shipped skeleton on all 9191 historical queue blobs, so "0 new
  refusals" is proven rather than sampled. Every named lifecycle edge re-tested.
- `record_visible_lines` now blanks indented code exactly as `semantic_text` does. That one
  view disagreement was a blocking false positive *and* an emitter that promoted a code
  sample to a real machine field; fixing it at the root closed both.
- The shape rule reads nested and ordered markers and non-first table cells; a collapsed
  record region and a value wrapped onto a second line are reported rather than passing in
  silence. Still 0 unscoped across all 628 tracked files.
- The 800-word budget is reverted to 700. Measured afterwards, the raise made freshly
  authored items 9.3 % longer with the quality difference inside noise — the opposite of
  the volume complaint. The finding now carries the count, the ceiling and the cut.
- Five claims in `verification.md` are corrected rather than defended, the largest being
  that `main` at `fc8c0af` is 14/15 on Python 3.14.6: the `ast.Str` guard rides on this
  branch, and the specification was right to call it owed.
- `7aaf11f` is squashed into `20c8e8f`, so no commit on the branch is one the reconciler
  refuses on checkout. Replaying the real hook against each commit's staged diff is
  stricter and found two more; one is fixed, and one — the first commit creating its task
  directly in `1_in-progress` — cannot be, because the documented repair needs a pickup
  request under the frozen `message-queue/`. It is a ship blocker and is written down as
  one.
- Not done, again: the one-line warning in `message-queue/needs-human/reviews/README.md`.
  Same reason. It still needs its own commit from a session allowed to write there.
