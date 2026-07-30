# Design notes — isolate child Git configuration by environment

**Status:** decided

## Problem

The runner needs child Git processes that cannot read the caller's Git configuration. It
achieved that by writing a `#!/bin/sh` wrapper named `git` onto the child `PATH`:

```sh
#!/bin/sh
HOME=<iso> XDG_CONFIG_HOME=<iso> GIT_CONFIG_NOSYSTEM=1 exec <real git> "$@"
```

Correct, but it costs an extra process on every Git call, and the suite makes 13,261 of
them with 92-93% of its wall time inside Git subprocesses.

## Options considered

### Option A — Keep the shell wrapper

No work, keeps a single well-understood interposition point. Its consequence is the current
cost: an extra `fork`+`exec` per Git call, measured at 12.87ms (2.03x) per call and 34-42%
of the gate.

### Option B — Set the same variables on the child environment

`HOME`, `XDG_CONFIG_HOME`, and `GIT_CONFIG_NOSYSTEM` are all inherited, so the isolation
the wrapper provided can be expressed without a process. Chosen.

The subtlety that justifies the original wrapper: `GIT_CONFIG_GLOBAL` was introduced in Git
2.32, so on Git 2.23 it is a no-op and the wrapper's `HOME` was doing the real work. Any
replacement must isolate through `HOME` **and** `XDG_CONFIG_HOME`, because Git reads
`$XDG_CONFIG_HOME/git/config`.

### Option C — Keep a wrapper but make it cheaper

There is no cheaper wrapper: any interposed executable is a process. Rejected.

## Chosen

Option B. `install_isolated_git_configuration` sets the variables on `child_environment`,
keeps `GIT_CONFIG_GLOBAL` for newer Git, and keeps the fail-closed `shutil.which("git")`
guard so plain `git` still resolves — to the real binary.

### Known residual

Nine call sites in the tests build child environments as
`{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}`, which also drops
`GIT_CONFIG_NOSYSTEM`. The shim used to re-impose it, so *grandchild* Git processes can now
read system configuration. It is bounded — every `~/`-relative entry in that system config
dereferences against the isolated `HOME`, `!`-shell aliases only run when invoked, and the
direct test children still carry `GIT_CONFIG_NOSYSTEM=1` — but it is a real narrowing and
plan step 7 closes it, one line per site.

## Core fit

**Agent substitution:** pass — the runner's isolation boundary is a repository mechanism with no agent-runtime dependency
**Provider substitution:** pass — the change is local to the test runner and needs no provider participation
**Repository substitution:** pass — any adopted repository running hook-launched tests needs child Git isolated from the caller without paying a process per call
**User-global writes:** none
**Why AgentFold core:** the isolation boundary between hook-launched repository tests and the invoking checkout is part of the harness contract, and its cost is paid by every adopter on every commit
**Thin adapter:** none
