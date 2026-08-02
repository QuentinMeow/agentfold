# Design notes — Finish the replacement-ref boundary the reconciler is halfway through building

**Status:** decided

## Problem

`main` passes `--no-replace-objects` to 39 Git invocations but leaves 22 list-literal
invocations bare, including the persistent `git cat-file --batch` reader every cached
object read now funnels through. A complete implementation exists on the unmerged
task/2026-07-26-resolve-queue-items-whose-evidence-already-merged branch, but that
branch is 77 commits behind and its headline rule was rejected on the record in
`docs/designs/queue-resolution-order-independence.md`, so it can only be ported by
understanding.

Two structures `main` has grown since that branch change where the flag belongs:

- the persistent `git cat-file --batch` reader and its process-lifetime object caches,
  which did not exist on the 07-26 branch;
- `git_merge_base_result` and `git_ancestry_probe`, which the perf commit `d9762aa`
  extracted from many call sites and gave a `replace_objects` keyword. Three callers
  (`git_review_revision_problems` and two reads inside `newly_added_handovers`) pass
  `replace_objects=True` — faithfully preserving what those call sites did bare before
  the refactor, which is exactly the gap this task closes.

## Options considered

### Option A — Keep `replace_objects` and flip the three callers to the default
The escape hatch survives as a keyword. Nothing in the source-level guard, which reads
list literals, would notice a fourth caller opting back in.

### Option B — Delete the `replace_objects` parameter
The two helpers always harden, so the keyword stops being a way to opt back in and
every remaining Git read in the reconciler is spelled as an argument list at a spawn.

### Option C — Copy the 07-26 branch's guard allowlist verbatim
Its allowlist names `("git", "rev-parse", "--git-path", "MERGE_HEAD")`, but `main` now
resolves the repository path through a `name` variable, and `main` grew index queries
the 07-26 branch did not have. A verbatim copy would have rejected legitimate index
reads.

## Chosen

Option B, with the allowlist rebuilt from `main`'s own bare invocations rather than
copied. The seven allowed prefixes read the index (`ls-files --stage`), the worktree
(`diff-files`, `ls-files --others`), a ref name (`rev-parse --verify --quiet HEAD`), a
repository location (`rev-parse --git-path`), or hash stdin (`hash-object -t tree
--stdin`) — none reads an object's contents, so a replacement entry has nothing to
substitute.

Only the boundary was ported. The creation-baseline rule,
`ordinary_request_resolution_evidence_problem`, its
`test_replace_ref_cannot_change_ordinary_request_resolution_verdict` regression, and the
evidence-lineage tests stay on the rejected branch.

The regressions needed one adaptation the 07-26 branch did not: object answers are now
cached for the whole process and the blob reader is reused across invocations, so two
reads inside one test would replay the first answer and the exploit would look impossible.
`forget_git_object_reads` drops that scope between reads, which is what the next
reconciler process against the same repository would do anyway.

## Second session — the reviewed scope was too narrow, twice

An adversarial review of the first session found the boundary unfinished and the guard
leaky. Both findings reproduced; `verification.md` carries the transcripts.

### The guard walked list literals, so most spellings were invisible

Scanning `ast.List` nodes and comparing element 0 against the literal `"git"` misses
every other way to write the same call. Six spellings were appended to the reconciler
and the guard stayed green on all six: a tuple argument list, a name bound to `"git"`,
an f-string with `shell=True`, `[_GIT_BIN] + [...]`, `os.popen`, and
`list((...))`. The same scan rejected `[*ORDINARY_HEADERS, "note"]` — an ordinary list
with no Git anywhere near it — because its starred rule applied to every list in the
file rather than to argument lists.

Options considered for the replacement:

- **Widen the literal scan to tuples.** Closes exactly one of the six. Rejected: the
  concatenation, the `list(...)` call, the shell string, and `os.popen` all remain, and
  the false positive stays.
- **Forbid every non-literal argument list.** Rejected on measurement: three call sites
  in `reconcile.py` and three in `run_tests.py` legitimately build a command in a local
  variable, and one of those is `[sys.executable, ...]`, not Git at all.
- **Chosen: invert the scan to start at the call sites.** Every `subprocess` and `os`
  spawn in a guarded module must present an argument list the scan can fold to constant
  tokens — a list or tuple display, directly, through a conditional, or through a local
  name bound only by plain assignment and mutated only by `append`/`extend`, which
  cannot change the program at the head. The program at position 0 is resolved to the
  set of strings it can be, so `RAW_GIT` splats fold, `_GIT_BIN = "git"` resolves, and
  `sys.executable` or `shutil.which("sysctl") or "/usr/sbin/sysctl"` is recognised as
  not-Git. Anything it cannot read is reported rather than skipped, so the gaps fail
  closed. The starred rule now exists only as ordinary folding inside an argument list,
  which is what makes the `[*ORDINARY_HEADERS, "note"]` false positive impossible, and
  every finding carries `ast.get_source_segment` text — the source line on Python 3.7,
  which has no such function.

What the scan still cannot see is written into the test's own docstring rather than
claimed away: it reads four files, it reads source rather than the run, and it says
nothing about `PATH`, `GIT_*`, or a library that never spawns anything.

### The boundary stopped at the reconciler

`check_core_scope.py` — the core-admission gate in the same pre-commit hook — ran every
Git read bare. A blob passed its "is this a commit" test and its full-object-id equality
test, and a stale core-fit review with real later core changes reported zero findings.
`run_tests.py` read the staged diff bare, so a replacement for HEAD swapped it for a
record-only diff and the hook selected no tests at all for a staged code change.
`check_action_projection.py` hardened five of its six reads at the call site instead of
in its `git_output` helper, and the merge and push adapters in `.github/workflows/harness.yml`
read `cat-file -e` and `merge-base` bare while the blocks below them did not.

All four now name one `RAW_GIT` constant and read through it, all four are inside the
guard, and the workflow — which the AST guard cannot see, because it is shell — gets its
own scan that allows `git fetch` alone to run without the flag.

Registering the two new inputs the guard reads (`automation/check_core_scope.py` and
`automation/run_tests.py`) in `INPUT_TEST_OWNERS` is what keeps a change to either of
them re-running the guard.

## Core fit

**Agent substitution:** pass — the change is inside four stdlib Python checkers any
runtime invokes as a subprocess, plus the shell steps of the provider workflow; no
agent-specific interface, prompt, or file format is involved.
**Provider substitution:** pass — the workflow steps hardened here are GitHub adapters,
but what they gained is a plain `git` flag every provider's runner honours; no provider
API, payload field, or product behaviour is involved.
**Repository substitution:** pass — every adopted repository runs these gates over its
own Git history, and any of them can carry a `refs/replace/*` entry; the guard reads only
the repository's own checked-in source.
**User-global writes:** none
**Why AgentFold core:** these four gates are the referees every adopter runs, and this is
the integrity of their own reads — not local config, not product code, and not separable
into an overlay, because the guard has to live beside the source it scans.
**Thin adapter:** none
