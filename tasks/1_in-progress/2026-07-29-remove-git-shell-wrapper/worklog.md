# Worklog — isolate child Git configuration by environment

## 2026-07-29 — implementation and measurement (claude)

- Traced the cost: 13,261 Git subprocess calls per full suite, 92-93% of wall time inside
  them, and each one paying an extra `fork`+`exec` for the `/bin/sh` shim.
- Replaced the shim with environment-based isolation. Verified with live canaries in the
  caller's `~/.gitconfig`, `XDG` config, a global `core.hooksPath`, and a `!`-shell alias
  that none are visible to children before or after.
- Measured a controlled before/after under one lock: 457.15s to 276.17s (−39.6%), with
  `sys` CPU falling 84.87s. Per call, interleaved: 25.39ms to 12.53ms (2.03x).
- Left one residual open, recorded as plan step 7: nine call sites build child
  environments by dropping every `GIT_*` variable, which also drops
  `GIT_CONFIG_NOSYSTEM`, so grandchild Git can read system configuration. The old shim
  re-imposed it. Direct test children are unaffected.
