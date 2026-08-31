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

## 2026-08-18 — land the branch and file what it owes (claude)

- The ship blocker is closed. The first commit was split into a `0_backlog` filing carrying
  the canonical `task-pickup` request and a claim coordination commit that resolves it, and
  the rest of the branch was replayed on top through the real pre-commit hook — no
  `--no-verify` anywhere. `--check --range fc8c0af...HEAD` is now 0 blocking. The
  pre-repair history is kept locally on `backup/pre-ceremony-a2ab98d`, so the shas the
  earlier records name can still be read.
- Two content changes were forced by the split and are written down rather than hidden. One
  line of `design.md` had to be reworded — `check_core_scope.is_placeholder` reads any
  value containing `<` as unfilled, and the `Provider substitution` reason named the fold
  by its tag — and the worklog's opening bullet, which said no pickup request existed, is
  now false of the repaired history and was rewritten to describe it.
- The two coordination commits are 14/15 on Python 3.14.6. They change no code, so they
  inherit `main`'s pre-existing `ast.Str` failure; the guard rides on the first code
  commit. Recorded in `verification.md` rather than smoothed over.
- The word budget goes back to 800, reversing this branch's own revert. A held-out gate
  measured the same candidate prose at Tier-C pass^2 0.750 under 800 against 0.375 under
  700, with 7 of 10 items breaching 700 and a natural mean of 724.7 words. The training-set
  ratchet that justified the revert was real and is kept beside it on the constant; it
  measures how long authors write, not whether the threshold refuses good work.
- The real repair was never the number. `--word-count` prints words before the answer line
  against the budget for any file, committed or not, and exits 1 if anything is over — so
  the format's one hard threshold is checkable before the commit instead of only by being
  refused. It writes nothing and is deliberately not a check.
- Two failure classes the same run surfaced are closed: a new human item with no clickable
  source link in its prose is now an advisory (birth-time only, because adding the link to
  a committed item would change action identity and be refused), and the no-task-paths rule
  is documented once for the whole item rather than for `Full context` alone.
- Filed what the work owes: two owner decisions — the ten legacy files, and the five values
  cut mid-sentence — and one agent request. The third is not the original identity finding:
  that one is closed for queue items and handovers, and what remains is that
  `memory/decisions/` has no integrity gate at all. Measured, four payload shapes, all 0
  blocking, and recorded in `verification.md`.
- `message-queue/needs-human/reviews/README.md` finally carries its warning, after three
  rounds of being the one thing nobody was allowed to write.
- Two ADRs: the fold and record-region decision, and an amendment retiring two false
  premises under the 2026-07-22 bold-key frontmatter record, which stays `decided`.
- Not done, and deliberately: the task stays in `1_in-progress`. Nothing is pushed and no
  pull request is opened, so moving it to `3_in-review` would claim a review that has not
  been asked for. The PR body is drafted and waiting.

## 2026-08-18 — correct the ship-gate blockers (claude)

- A ship gate on the branch tip found four published falsehoods. Three are fixed; the
  fourth cannot be, and that is the finding of this session.
- The word budget's justification cited `pass^2` figures and a McNemar p-value from a
  harness that is not in this repository. The comment now carries the reasoning and names
  the task record holding the figures, so nothing in shipped source rests on evidence a
  reader cannot reach.
- `roadmap/current-state.md` still described the pre-branch tree. Re-measured at HEAD: 17
  live `needs-human/` items, 15 waiting, 10 with bookkeeping above the answer line and 7
  below, of which the 2 this task filed are the only folded items anywhere. The record
  said fifteen live, none folded, zero production exercise.
- The previous handover's "(10 commits, nothing pushed)" was 12 when written.
  `handover-queue-projection` freezes a committed handover and its own repair text says to
  record the correction in a new one, so that is where it went, phrased as a command
  rather than a number so it cannot go stale again.
- **Repaired by rebuilding the filing commit.**
  `non-blocking-choose-what-happens-to-the-ten-older-question-files.md` said "Ten of the
  fifteen questions waiting for you" in its title, its `Why this matters` and its `Today`
  line, and labelled an excerpt "the worst file" that measurement ranks fourth of ten.
  Editing the live item is refused by `queue-resolution`, and amending its filing commit is
  refused too, because at hook time HEAD still holds the old item and the check sees a live
  rewrite. Rebuilding the filing commit from its parent is legal — the item is then born
  correct and there is no prior version to rewrite — and that is what landed, the following
  commits being replayed onto it. The two handovers that project the item were rebuilt the
  same way, since a committed handover is immutable and its projection had to be born
  correct as well. This was a history rewrite of an unpushed branch, authorized before it
  was performed.
- Re-derived rather than trusted: the ten legacy files measure 106 field lines, 7,385
  painted characters and 252 phone lines at 40 columns, reproducing the committed record
  exactly; the worst single file is
  `non-blocking-review-layered-development-workspace.md` at 1,013 characters and 33 lines,
  not the one the item excerpts.

## 2026-08-31 — verified recovery publication

The useful implementation and complete original commit history are retained and repaired in [PR90](https://github.com/QuentinMeow/agentfold/pull/90). The conflicting original PR88 is closed. The recovery task `2026-08-30-rebuild-the-open-pr-stack` records the current implementation checks; [its verification](../2026-08-30-rebuild-the-open-pr-stack/verification.md) preserves actual output. The test-file count in the original acceptance criterion now names all 16 current files; current main added a file after the original 15-file result, whose historical output remains preserved. Existing human questions and the original claimant remain unchanged. No product merge to main was performed.
