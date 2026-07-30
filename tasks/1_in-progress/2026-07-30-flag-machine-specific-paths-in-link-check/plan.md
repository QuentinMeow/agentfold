# Plan — machine-specific paths in the link check

- [ ] 1. Decide the absolute case before either resolution is attempted, since an
      absolute path can never name a repository artifact.
- [ ] 2. Word the finding so it names unquoting as the fix, because prose about a real
      binary is legitimate and only the backticks are wrong.
- [ ] 3. Cover it with a test whose verdict does not depend on which paths exist on the
      machine running it.
- [ ] 4. Survey the existing records for absolute paths already in backticks and report
      the count before changing behaviour.
