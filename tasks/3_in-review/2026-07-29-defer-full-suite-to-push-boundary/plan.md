# Plan — give the commit gate a routine lane and let the push boundary own completeness

- [x] 1. Verify the premise in the workflow itself: the full suite runs on every push of
      every branch with no branch or path filter.
- [x] 2. Add the routine lane and point the pre-commit hook at it, leaving the bare runner
      invocation unchanged as the full lane.
- [x] 3. Report deferred coverage honestly, naming every file not run and where its
      coverage happens, before any test starts.
- [x] 4. Ship an optional pre-push full-suite hook, inert unless enabled by repository-local
      configuration.
- [x] 5. Add a test that fails if the workflow stops running the full suite on every push,
      and prove it is not vacuous.
- [ ] 6. Depends on input-ownership selection: until that lands, the routine lane selects
      nothing for an `automation/` change.
- [ ] 7. Update `README.md` and `CONTRIBUTING.md`, which still describe the hook as running
      the full suite.
