# Design notes — Report the structurally visible readability rules as advisory findings

**Status:** decided

## Problem

`memory/decisions/2026-08-02-readability-enforcement-disposition.md` decided the
enforcement level (advisory) but not where the three rule families run. Three families are
machine-visible:

1. required sections present and in template order — for a queue item and for a
   pull-request body;
2. every choice ends with a concrete `*Example consequence:*`;
3. a pull-request `## TL;DR` carries three to six numbered items.

Two constraints shape the answer. The reconciler walks repository files and never sees a
pull-request body; `automation/check_action_projection.py` is the only tracked program
that ever reads one, and it also runs against issue bodies and conversation comments,
which are not pull requests and have no schema of their own. Separately, several live
queue items were written under an earlier field spelling, and this repository treats a
written record as immutable — `check_queue_schema` and `check_human_attention` already
judge such an item by the schema it was written under.

## Options considered

### Option A — one checker

Put all three families in the reconciler, and have it read a pull-request body from an
environment variable or a file when one is supplied.

That gives one severity model, one output format and one flag (`--fail-on-advisory`) for
everything. It costs the reconciler its defining property: it is a function of repository
files, so a run is reproducible from a commit alone. A body arriving by environment
variable would make two runs of the same commit disagree, and the check ids that
`--file-retries` turns into repair items would then name a subject that no longer exists.

*Example consequence:* a maintenance run of `--file-retries` on `main` files a
`blocking-*` repair item naming a pull-request body that was edited an hour earlier, and
no agent can ever clear it because the subject is not in the repository.

### Option B — split by what each program can see

The reconciler owns the queue-item rules, because queue items are repository files it
already walks. The boundary gate owns the pull-request-body rules, because it is the only
thing that ever holds a body. Each reports advisory findings in its own output.

The cost is two implementations of "advisory": the reconciler already has a severity tier,
and the gate needs a second output stream that its exit code ignores.

*Example consequence:* an agent that files a queue item with its sections in the wrong
order sees the finding in the pre-commit hook, seconds after writing it; an agent that
writes a four-section pull-request body sees it in the CI log for that pull request, and
neither run has to know anything about the other surface.

## Chosen

**Option B.**

### The reconciler half

One new check id, `explanation-shape`, registered in `CHECKS` and in `ADVISORY_CHECKS`.
The id is permanent — retry filenames embed it
(`memory/lessons/automation/deterministic-finding-keys.md`) — and one id covers both queue
families because `CHECKS` is one function per id and both families read the same parse of
the same file. It reports:

- a required section missing from a queue item, named;
- the first required section that sits out of the order its template declares;
- a `### ` choice with no concrete `*Example consequence:*` line under it, named.

**Required sections are derived, never restated.** The check reads
`templates/queue/<singular leaf>.md` at run time and takes that file's level-2 headings,
in order, as the requirement. `decisions` → `decision.md`, `retries` → `retry.md`, and so
on. A typed leaf an adopter adds has no template, so it gets no heading rule — which is
what `automation/AGENTS.md` already says about new typed leaves inheriting the actor's
generic schema.

**Only items the current templates govern are checked.** A live human item written in the
pre-rename spelling (`Why-you-might-care` / `If-you-do-nothing`) keeps the schema it was
written under, exactly as `check_human_attention` already decides with
`human_attention_format_applies`. Ten of the thirteen live `needs-human` items and one of
the forty-one live `needs-agent` requests are in that earlier generation; checking them
against today's templates would ask for an edit the immutability rule forbids.

**The agent side needs a date as well as a field, and this is the subtle part.** On the
human side the predicate already existed and is reused. On the agent side there was none,
and the first version of this — "the item carries a legacy projection field" — was a hole
rather than a carve-out. The single live legacy request is precisely the file an agent
copies as a model, so a brand-new request that inherited its `Why-you-might-care:` line
switched the rule off for itself; and for an agent request nothing else has ever read its
sections, because `check_queue_schema` scopes every section rule behind
`if actor != "needs-human": continue`. A review probe demonstrated it: a request dated
today, missing `## What you need to know`, carrying that one line, produced zero findings.

The carve-out now needs the legacy field **and** a `Filed` date before
`EXPLANATION_SHAPE_ACTIVATION`, the day the rule landed. Two alternatives lost. Keying on
the creation commit is what `handover_creation_commit` and `staged_side_creation_commit`
do, and it is the more principled signal, but both need a `--range` or a merge parent and
return nothing in a plain `--check` — which is the pre-commit path, where this check does
most of its work — so the rule would have gone silently inert exactly where it matters.
Dropping the agent carve-out entirely would report the one genuine legacy request forever,
against a file whose only repair is rewriting a record. `Filed` is agent-written and so
could be backdated; that is accepted, because a false date in a record is a far larger
violation than a missing heading, and the realistic failure here is imitation rather than
malice. An item whose `Filed` date cannot be read is checked, not excused.

### The boundary-gate half

`automation/check_action_projection.py` gains `--pull-request-body-shape`, an opt-in flag
that the pull-request-description step of `.github/workflows/harness.yml` passes and no
other step does. Under it the gate reads `templates/pull-request.md`, takes its level-2
headings as the required sections and their order, and reports missing sections,
out-of-order sections, and a `## TL;DR` outside three to six numbered items.

The flag exists because the same program checks issue bodies and conversation comments.
Those are not pull requests, they have no section schema, and reporting `missing section
## Verification` on a drive-by comment would be noise that trains readers to ignore the
line.

**The workflow probes for the flag rather than passing it unconditionally.** A
`pull_request_target` run resolves the workflow file and the checked-out gate separately,
and a pull request's `base.sha` demonstrably lags the base branch tip — two open pull
requests reported a `base.sha` one commit behind `origin/main`, and one stayed behind
across a `synchronize` seven minutes after the newer commit landed. So a workflow that
hard-codes `--pull-request-body-shape` can meet a gate that predates the flag, and argparse
answers that with `error: unrecognized arguments` and **exit 2** — the one status this
repository reserves for a check that could not run at all. An advisory readability line
would then be failing pull requests that have nothing wrong with them, which is precisely
the outcome the decision behind this task forbids. So the step asks the gate what it
accepts:

```sh
SHAPE=()
python3 automation/check_action_projection.py --help \
  | grep -q -- --pull-request-body-shape && SHAPE=(--pull-request-body-shape)
```

A capability probe is the right shape rather than a version pin because the two artifacts
have no shared version to pin to: the workflow and the gate arrive from whatever commits
the provider chose, and neither can name the other's. A probe asks the only question that
matters — does the program in front of me accept this argument — and answers it from the
program itself, so it stays correct under every ordering, including a rollback. The cost is
that a genuine typo in the flag name degrades to silence instead of failing loudly; the
tests hold the spelling on both sides so the typo cannot survive a suite run.

**Reported the same way, gated differently.** Each line prints
`[explanation-shape] <label>: <message>  (advisory)`, matching the reconciler's marker
byte for byte, and a separate `explanation-shape: N advisory finding(s)` count line keeps
them out of the `action-projection: N finding(s)` total. The gate does **not** get a
`--fail-on-advisory` twin. That flag exists in the reconciler for maintenance runs of a
repository the reconciler can read on demand; the gate only ever runs at a provider
boundary, where its exit code is the merge gate, so a flag that could turn a readability
opinion into a merge refusal would have no caller and one bad use.

**Two facts are in the gate's source rather than derived.** `templates/pull-request.md`
states them only inside HTML comments, and `templates/README.md` requires that nothing a
check reads is hidden in a comment — so `semantic_text` blanks them before any parser
here sees them. They are that `## Notes` is deleted when it would be empty, and that the
summary carries three to six items.

This is the weakest part of the split, and the rejected alternative is close. The
section-order table in `skills/explain-to-human/scenarios/pull-request.md` carries both
facts in machine-readable columns (`Present` and `Rough budget`) and would have removed
the two constants entirely. It lost because that table is prose that may be reworded at
any time, and because it would make a provider gate depend on a skill file. The cost of
the choice taken is that the schema and the gate can disagree; a test pins both constants
against the schema, so a disagreement is a test failure rather than a silently wrong
report.

**Both pins are bidirectional, which the first version of one was not.** The range pin
already broke in both directions. The optional-section pin only asserted that `Notes` was
in the tuple, so a review probe could append a second section to the schema carrying the
same "Delete this section, heading included" comment and watch every test stay green while
the gate began demanding that section of a conforming body. The test now derives the set of
sections the schema marks deletable and asserts set equality with the tuple, so a schema
that gains or loses a deletable section fails the suite instead of the next pull request.

### Known limits

Three shapes the rules do not see, recorded so nobody re-discovers them as bugs:

- A `##` heading nested inside a `<details>` fold counts as present. `<details>` opens an
  HTML block that ends at the blank line the schema requires after `</summary>`, so the
  content below it is ordinary Markdown to every parser here. A body that hides
  `## Verification` inside another section's fold passes.
- A duplicated `## TL;DR` is deduplicated rather than reported. Order is compared over a
  de-duplicated list so that a missing section is reported once as missing instead of twice
  as disorder; repetition is the price.
- A bulleted `## TL;DR` counts as zero numbered items and is reported as such. This is the
  intended reading — the schema asks for numbered items and a bulleted list has none — and
  the finding says `a bulleted list counts as none` when the count is zero, so the message
  cannot be mistaken for a miscount.

### What this deliberately does not do

Nothing semantic. A `*Example consequence:*` line reading `none` is caught by the existing
placeholder test and nothing else judges whether a consequence is real. Whether an
explanation is clear stays a reviewer's job, as the decision says.

The existing blocking rule in `check_queue_schema` — at least two choices and at least two
example consequences per human item — is untouched. The new rule is strictly finer: it
names the individual choice that is missing one, which the aggregate count cannot do when
an item has four choices and two consequences.

## Core fit

**Agent substitution:** pass — the check is a Python function over repository files and a
provider body string. No agent runtime, prompt, or product surface appears in it; another
agent runtime running `reconcile.py --check` or the boundary gate gets the same findings
from the same bytes.
**Provider substitution:** pass — the pull-request rules read a body supplied on stdin, in
a file, or in an environment variable, and are opted into by a flag. GitHub appears only in
`.github/workflows/harness.yml`, which is already a registered thin adapter; another
provider passes the same flag with its own body.
**Repository substitution:** pass — any repository that adopts `templates/queue/` and
`templates/pull-request.md` gets the rules for its own templates, because the requirement
is derived from whichever template files that repository carries. An adopter that deletes
a queue template loses only that leaf's rule, and one that adds a typed leaf gets no rule
for it until it adds a template.
**User-global writes:** none
**Why AgentFold core:** the standard being checked (`skills/explain-to-human/`) is core,
the templates it checks against are core, and the decision that created this work is an
ADR in core. The rule is about the shape of the harness's own coordination files, not
about any product service, personal setup, or single provider.
**Thin adapter:** canonical=automation/check_action_projection.py; optional=yes; policy=none; writes=repo-only

The one adapter edit is `.github/workflows/harness.yml`, which gains a single
`--pull-request-body-shape` argument on the step that already passes a pull-request body to
that canonical gate. It carries no policy of its own and writes nothing.
