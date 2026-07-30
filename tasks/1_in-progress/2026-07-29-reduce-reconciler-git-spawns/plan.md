# Plan — spawn fewer Git processes in the reconciler and its fixtures

- [x] 1. Census the spawns exactly, by patching `subprocess.Popen.__init__` in-process so
      both fixture and reconciler spawns are counted without adding a wrapper process.
- [x] 2. Lever 1: build the per-test repository skeleton once with a real
      `git init --template=<empty>` and copy it per test, with a guard test that rebuilds
      it using real Git and compares byte for byte.
- [x] 3. Lever 2: route blob reads through the existing reusable `git cat-file --batch`
      reader instead of one `git show` per artifact.
- [x] 4. Lever 2: cache facts that are keyed by a full object ID, scoped per repository,
      never caching failures.
- [x] 5. Prove behaviour is unchanged with an equivalence harness over regular, exec,
      empty, CRLF and unicode files, symlinks, directories, absent and odd paths.
- [x] 6. Attribute the win by interleaving base, Lever 1 only, and both levers inside a
      single lock hold.
- [ ] 7. Convert the two remaining `git show <commit>:<path>` sites, which need the
      universal-newline translation that `text=True` performs.
