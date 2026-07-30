# Plan — input-ownership test selection

- [x] 1. Establish, by experiment rather than assumption, which repository paths the suite
      can read: corrupt and then delete every record tree in the projection and confirm
      the suite still passes.
- [x] 2. Replay the existing `--staged` lane over real repository history and record its
      hit rate.
- [x] 3. Add an explicit ownership table mapping path prefixes to owning test files,
      extending the existing staged machinery rather than replacing it.
- [x] 4. Make the default fail-closed: an unregistered top-level entry, or a removal or
      rename of a non-record path, selects the full suite.
- [x] 5. Add a guard test that fails if a test starts reading a record path, and prove the
      guard actually fails by introducing such a test.
- [x] 6. Replay the new selection over the last 60 non-merge commits and record the result.
- [ ] 7. Decide whether the heavy record-free probe should run in CI rather than opt-in.
