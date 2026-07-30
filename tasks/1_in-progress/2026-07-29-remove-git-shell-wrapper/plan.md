# Plan — isolate child Git configuration by environment

- [x] 1. Read `install_isolated_git_wrapper`, `isolated_test_environment`, and every test
      covering them; establish which properties the shim actually provides.
- [x] 2. Replace the shim with `HOME`, `XDG_CONFIG_HOME`, and `GIT_CONFIG_NOSYSTEM` set on
      `child_environment`; keep `GIT_CONFIG_GLOBAL` for Git 2.32 and newer.
- [x] 3. Keep the fail-closed `shutil.which("git")` guard so a missing Git still fails.
- [x] 4. Prove nothing depends on the caller's `HOME`, and that the core-scope gate's
      global-state markers keep it that way.
- [x] 5. Replace the test that asserted the old mechanism with one asserting the new one,
      plus a canary test that proves its negative assertions are not vacuous.
- [x] 6. Measure a controlled before/after of the full suite and of the per-call cost.
- [ ] 7. Close the residual: nine test call sites drop every `GIT_*` variable and so drop
      `GIT_CONFIG_NOSYSTEM`, letting grandchild Git read system configuration.
