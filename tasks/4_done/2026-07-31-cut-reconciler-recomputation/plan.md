# Plan — Cut the reconciler's repeated recomputation

- [x] 1. Measure the baseline on this machine before changing anything: several runs of
      `--check` and of at least two `--range` sizes, recording the spread rather than one
      number, plus a `cProfile` run at the stack tip that confirms which hot spots survive
      the object-read caching layer.
- [x] 2. Build a differential harness that runs the pre-change and post-change reconciler
      against the same working tree and diffs the finding lists for `--check`, a mid-size
      range, and `--range root:<head>`.
- [x] 3. Memoize the pure text answers — Markdown semantic blanking and task-record
      action-prose recognition — on their exact input text.
- [x] 4. Replace whole-index prefix scans used as single-path lookups with a direct entry
      lookup.
- [x] 5. Ask Git for one revision's parents at most once by routing the governed edge walk
      through the cached `git rev-list` helper.
- [x] 6. Read the immutable handover incarnation through the `cat-file --batch` reader
      instead of spawning `git show`.
- [x] 7. Re-profile, and only then decide whether the remaining per-edge task-structure
      recomputation still needs structural work; record what was skipped and why.
      Answer: no. Memoising the text views cut it 2.8x on its own, and the remainder is not
      soundly cacheable (`design.md`, Option A). Derived the live queue path sets once per
      candidate instead — the larger remaining cost on the pre-commit path. Every skip and
      its reason is recorded in `verification.md`.
- [x] 8. Prove parity on all three scopes, run the full suite, and record real before/after
      numbers with spreads in `verification.md`.
