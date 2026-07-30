# Plan — parallel test shards

- [x] 1. Enumerate test methods per file without importing them, so discovery costs no
      subprocess: `ast` walk for `class ...(unittest.TestCase)` and its `test_*` methods.
      A unit test covers a file whose methods are inherited from a base class.
- [x] 2. Add `--jobs N` with `N=1` reproducing today's serial behaviour byte-for-byte,
      and a default taken from the physical core count.
- [x] 3. Schedule work as a pool over test methods, longest file first, so the long pole
      starts earliest and no worker idles at the tail.
- [x] 4. Quarantine `automation/tests/test_run_tests.py` to a serial tail and report that
      it ran serially, with the reason, rather than leaving it implicit.
- [x] 5. Aggregate failures so a sharded run names the same failing tests a serial run
      does, and interleaved worker output never corrupts a traceback.
- [x] 6. Verify equality of the run test set: sharded and serial runs cover the same
      method names, checked mechanically rather than by eye.
- [x] 7. Repeat the sharded run to expose concurrency-induced flakiness, and record the
      repetition count.
- [x] 8. Record wall time at several worker counts, all variants interleaved inside one
      measurement session, since separate runs on this machine are not comparable.
