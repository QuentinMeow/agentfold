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
The two helpers always harden. Every remaining way to read an object through a
replacement is a literal Git argument list, which is precisely what the source-level
guard scans, so the guard covers the whole surface rather than most of it.

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

The guard is one step stricter than the 07-26 original: a starred first element is
skipped only when it is `*RAW_GIT`, and the test asserts `RAW_GIT` itself equals
`("git", "--no-replace-objects")`, so the splat cannot become a way around the scan.

Only the boundary was ported. The creation-baseline rule,
`ordinary_request_resolution_evidence_problem`, its
`test_replace_ref_cannot_change_ordinary_request_resolution_verdict` regression, and the
evidence-lineage tests stay on the rejected branch.

The regressions needed one adaptation the 07-26 branch did not: object answers are now
cached for the whole process and the blob reader is reused across invocations, so two
reads inside one test would replay the first answer and the exploit would look impossible.
`forget_git_object_reads` drops that scope between reads, which is what the next
reconciler process against the same repository would do anyway.

## Core fit

**Agent substitution:** pass — the change is inside a stdlib Python checker any runtime
invokes as a subprocess; no agent-specific interface, prompt, or file format is involved.
**Provider substitution:** not-applicable — nothing here talks to a provider; the boundary
is between the reconciler and the local Git object store.
**Repository substitution:** pass — every adopted repository runs this reconciler over its
own Git history, and any of them can carry a `refs/replace/*` entry; the guard test reads
only the reconciler's own source.
**User-global writes:** none
**Why AgentFold core:** the reconciler is the referee every adopter runs, and this is the
integrity of its own reads — not local config, not product code, and not separable into an
overlay, because the guard has to live beside the source it scans.
**Thin adapter:** none
