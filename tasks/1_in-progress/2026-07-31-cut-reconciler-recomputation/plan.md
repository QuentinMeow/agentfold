# Plan — Cut the reconciler's repeated recomputation

- [ ] 1. Measure the baseline on this machine before changing anything: several runs of
      `--check` and of at least two `--range` sizes, recording the spread rather than one
      number, plus a `cProfile` run at the stack tip that confirms which hot spots survive
      the object-read caching layer.
- [ ] 2. Build a differential harness that runs the pre-change and post-change reconciler
      against the same working tree and diffs the finding lists for `--check`, a mid-size
      range, and `--range root:<head>`.
- [ ] 3. Memoize the pure text answers — Markdown semantic blanking and task-record
      action-prose recognition — on their exact input text.
- [ ] 4. Replace whole-index prefix scans used as single-path lookups with a direct entry
      lookup.
- [ ] 5. Ask Git for one revision's parents at most once by routing the governed edge walk
      through the cached `git rev-list` helper.
- [ ] 6. Read the immutable handover incarnation through the `cat-file --batch` reader
      instead of spawning `git show`.
- [ ] 7. Re-profile, and only then decide whether the remaining per-edge task-structure
      recomputation still needs structural work; record what was skipped and why.
- [ ] 8. Prove parity on all three scopes, run the full suite, and record real before/after
      numbers with spreads in `verification.md`.
