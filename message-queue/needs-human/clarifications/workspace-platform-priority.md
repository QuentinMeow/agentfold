# Which operating systems must the layered workspace design prioritize?

**Status:** folding
**Blocking:** no — proceeding on the answered platform priority below
**Assumption:** macOS and Linux define the baseline; Windows is included only when it adds little complexity and does not distort that design
**Matters-by:** publication of the layered development workspace design
**Filed:** 2026-07-24, by codex, from the owner's answer in this session

## Context

The workspace composition mechanism may use Git history, generated views, symlinks, or
operating-system mounts. Cross-platform parity would rule out some otherwise strong
macOS/Linux options, so the supported platform boundary must be explicit before the
design compares them.

**Your answer:** Prioritize macOS and Linux. Ignore Windows when supporting it requires
substantial effort; include it when doing so is simple and does not affect the macOS or
Linux design.
