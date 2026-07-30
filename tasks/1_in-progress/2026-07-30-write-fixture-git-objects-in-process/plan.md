# Plan — in-process fixture Git objects

- [ ] 1. Write a loose-object writer: blob, tree and commit, zlib-compressed under the
      two-character prefix, with tree entries sorted the way Git sorts them.
- [ ] 2. Prove equivalence by byte-comparing every written object against the object real
      `git add` and `git commit` produce for identical content.
- [ ] 3. Pin the author and committer identity and the timestamp so fixture object
      identifiers are reproducible run to run.
- [ ] 4. Move the long-pole file's fixture helper onto the writer, leaving real Git where
      index semantics or a non-default object format are actually under test.
- [ ] 5. Census spawns before and after, per test file.
- [ ] 6. Time both variants interleaved inside one session, since separate runs on this
      machine are not comparable.
