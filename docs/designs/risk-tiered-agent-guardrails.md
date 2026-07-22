# Risk-tiered guardrails for obligations an agent may forget

**Status:** proposed
**Researched:** 2026-07-22
**Task:** 2026-07-22-design-critical-agent-guardrails

## Recommendation

Build a small, layered guardrail system around this rule:

> Hard, narrow invariants at irreversible boundaries; flexible, inspectable evidence
> everywhere else.

Do not turn the handbook into one universal blocking checklist. Classify each obligation
by consequence, reversibility, and detectability. Preferences stay as guidance;
repairable drift becomes a reconciler finding; judgment-heavy risks can request explicit,
content-bound review; and a deployment claiming protected disclosure boundaries runs the
relevant guards in `hard` mode at more than one independently controlled boundary.

The proposed “acknowledge button” is useful because it interrupts the normal path and
demands current dispositions. A self-authored receipt proves neither that the agent read
the evidence nor that its judgment was correct; it is a deliberate nudge plus an
auditable claim. For PII or credentials, it can complement scanners but cannot override
a confirmed critical finding.

### Human review disposition

The owner reviewed this proposal and narrowed its initial adoption:

- do not build or require a capability sandbox now;
- ship proposed guard mechanisms as templates, not automatically active policy;
- use one versioned configuration surface to select each guard's mode; and
- keep token-expensive independent-agent review manual by default rather than running it
  on every change.

Every guard supports the same four modes:

| Mode | Automatic behavior | Transition effect |
|------|--------------------|-------------------|
| `hard` | runs at its declared trigger | finding, incomplete coverage, or error blocks that transition |
| `soft` | runs at its declared trigger | reports evidence and remediation without blocking |
| `off` | does not run | records that the guard contributes no assurance |
| `manual` | runs only when explicitly invoked | produces evidence but is not an always-on gate |

The configuration controls invocation, not truth. Selecting `off` or `manual` for a
critical guard visibly lowers the assurance profile; it cannot still claim that the
boundary is enforced. A separately controlled provider rule may remain mandatory even
when repository-local automation is off. Mode changes are ordinary reviewed policy
changes, never an implicit exception written inside a detector.

Unless a later section explicitly says otherwise, words such as “block,” “reject,” and
“fail closed” describe `hard` mode or an assurance profile that requires that hard guard.
In `soft`, the same result is reported without stopping the transition; in `manual`, it
affects only an explicitly requested run; in `off`, the guard supplies no result.

## Context and current gap

Current enforcement is owned by `roadmap/current-state.md` and
`automation/AGENTS.md`. Against those sources, the missing content- and evidence-level
guardrails are:

- a data classification defining what “PII must not be committed” means;
- staged-content, new-object, or history scanning;
- separate clean, finding, incomplete, and detector-error results;
- evidence tied to the exact content reviewed;
- a remotely authoritative admission control that survives `--no-verify`;
- protected, expiring exceptions; or
- canaries proving the detector and its configuration are alive.

This matters because an instruction can fall out of context, a test can be wrong, and a
correctly running detector can still miss contextual PII. Microsoft Presidio explicitly
warns that automated detection cannot find all sensitive information and recommends
additional protections ([Presidio](https://microsoft.github.io/presidio/)). Git itself
documents that local pre-commit hooks are bypassable, while a server-side pre-receive
hook can reject an entire push ([Git hooks](https://git-scm.com/docs/githooks)).

## Scope and non-goals

This design covers obligations that affect repository content, Git history, PR/merge
admission, and the agent's filesystem-facing workflow. PII is the representative hard
case because disclosure is not repaired merely by a later commit.

This design does not:

- claim that any scanner proves the absence of all PII;
- require one agent vendor, model, hosted Git provider, or policy engine;
- prescribe how an agent must investigate or implement ordinary work;
- make every handbook preference a gate;
- defend against a malicious repository administrator who controls policy, checks,
  branch protection, and audit history;
- make CI the first privacy boundary—content on a PR branch has already reached the
  remote system; or
- include a filesystem/network capability sandbox in the initial implementation.

## How this design was made

The investigation used a breadth-first architecture pass before choosing a combination:

1. State obligations and failure consequences.
2. Classify detectability, reversibility, and disclosure boundaries.
3. Enumerate mechanism families without ranking them.
4. Place each mechanism at every plausible lifecycle point.
5. Record bypasses, detector failure, false positives, and controlling authority.
6. Compare complete layer combinations, not favorite tools in isolation.
7. Deepen the highest-risk case—PII—and adversarially test the recommendation.

This is a lightweight version of the scenario-and-trade-off shape in SEI's
[Architecture Tradeoff Analysis Method](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/).
It also matches GitHub Spec Kit's separation of specification, plan, tasks, and
cross-artifact analysis ([Spec Kit](https://github.github.com/spec-kit/reference/agentic-sdd.html)).

## Agent-oriented design principles

### Enforce consequences, not a favorite workflow

State the end condition—such as “no prohibited sensitive data becomes reachable from a
protected ref”—and let the agent choose its investigation and remediation path. Exact
tool-call grading punishes valid alternatives; deterministic final-state graders are
preferable when the outcome is mechanically observable
([Anthropic agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

### Separate must-be-true from must-be-considered

A machine-checkable safety property needs a gate. A qualitative concern may instead
need evidence that the exact artifact was inspected. Calling both “checks” hides the
difference between proof, a fallible signal, and an attestation.

### Separate policy, detection, evidence, and enforcement

Policy says what is prohibited and how uncertainty is handled. Detectors produce
signals and coverage. Evidence binds those results and dispositions to content.
Enforcement decides whether a transition may proceed. Keeping these roles separate
makes detectors replaceable without changing the invariant. OPA uses the same broad
policy-decision/enforcement separation, although adopting OPA is unnecessary here
([OPA documentation](https://www.openpolicyagent.org/docs)).

### Make failure actionable and safe to display

A rejection should identify the invariant, category, an opaque locator, coverage,
remediation choices, and exception route. It may show a path only after the path itself
passes the sensitive-data check; otherwise it shows a redacted label and leaves the
ID-to-path mapping in an access-controlled local report. It should not echo the matched
PII or secret into a terminal, CI log, agent transcript, or review comment. SWE-agent's agent-computer
interface work shows the value of immediate, precise tool feedback
([SWE-agent ACI](https://swe-agent.com/0.7/background/aci/)).

### Bind evidence to exact bytes and policy

“Reviewed: yes” is replayable. A useful receipt binds to a defined subject envelope:
tree or blob IDs, parents, identities, message content excluding receipt fields, the
relevant policy slice, detector version, finding IDs, disposition, actor, and expiry.
This avoids circularly hashing a receipt inside its own commit and covers metadata that
a tree-only digest misses. A finding-level disposition carries forward only when its
path, blob, rule, relevant policy slice, and detector-declared context dependency digest
are identical. A contextual detector declares whether it depends on a directory, linked
records, or the whole candidate tree; an absent dependency manifest disables reuse.
Unrelated edits outside that set regenerate the run manifest without demanding new
judgment. This follows the same artifact-binding idea used by SLSA verification
([SLSA verification summary](https://slsa.dev/spec/v1.2/verification_summary)).

A self-authored receipt remains an untrusted claim even when perfectly bound. Evidence
that authorizes a critical exception additionally binds repository identity, destination
sink, ref, and assurance profile and needs an authenticated external principal: for
example, a protected provider approval/check record or a signature whose key is
unavailable to the producing agent.

### Treat the verifier as attack surface

A critical check distinguishes pass, finding, incomplete coverage, runtime error, and
not applicable. It returns incomplete coverage on zero scanned inputs when inputs were
expected. Scanner,
workflow, fixtures, policy, allowlists, and waiver changes receive stronger ownership
than ordinary code. The design tests both positive and negative cases and never turns a
crash into “clean.”

In `hard` mode, failure closed applies at the protected transition, not to every kind of
work. Keep a pinned, minimal offline detector as the portable baseline; optional
semantic/provider detectors may degrade only according to declared policy. During an
outage, agents can inspect and repair locally, but a hard-mode commit/push/merge
transition remains blocked. An operational break-glass is distinct from a content
false-positive waiver: it is short-lived, scope- and revision-bound, authenticated by a
separate owner, and cannot silently change an error into clean. If neither
last-known-good verification nor an authorized break-glass exists, a hard confidentiality
boundary intentionally wins over availability. `soft` reports the outage and continues;
`manual` reports it only when invoked; `off` makes no detector-health claim.

### Use independent layers with different failure modes

Running the same buggy script twice is availability redundancy, not detection diversity.
Useful layers differ: structured patterns and checksums, contextual classification,
direct artifact inspection, a separately controlled remote gate, and sampled
human/independent-agent review. OWASP likewise treats an LLM guardrail as one layer,
not a replacement for input validation, least privilege, and approval on high-risk
actions
([OWASP prompt-injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)).

### Put authority at the last safe choke point

Local hooks optimize feedback. They are not the authority because they may be absent or
bypassed. For accepted Git history, authority belongs at pre-receive/push protection
when available; protected required checks govern merge. GitHub rulesets can require a
status check from an expected app
([GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)).

There is no universal choke point for every disclosure sink. Git commits, LFS uploads,
provider API calls, CI logs/artifacts, package/release publication, and mirrors each need
an adapter or a capability boundary before their own egress. An agent with unrestricted
network credentials can bypass repository scripts, so a no-transmission profile also
requires an external capability boundary and credentials scoped to guarded wrappers.
That stronger profile remains future work because the reviewed initial design explicitly
defers sandboxing.

### Make escape hatches narrower than the rule

A legitimate exception is finding-specific, content-bound, attributable, reasoned,
expiring, and visible. The producing agent cannot self-approve a confirmed critical
finding. GitHub's delegated push-protection bypass follows this requester/approver split
([GitHub bypass requests](https://docs.github.com/en/code-security/concepts/secret-security/bypass-requests)).

### Add friction only when the evidence changes

A static acknowledgement becomes wallpaper. Security-warning research observes rapid
habituation to repeated warnings
([warning habituation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7751389/)).
Trigger deliberation from risk or a finding, require per-finding dispositions, and
invalidate a disposition when its path, blob, finding, policy, or declared contextual
dependencies change.

### Keep harness assumptions removable

Every non-security scaffold should name the model weakness or failure history it
compensates for and have an eval that can show whether it remains load-bearing.
Anthropic's long-running harness work recommends removing components one at a time as
models improve, while constraining deliverables more than implementation details
([harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps)).
Security boundaries remain even when models improve because they also defend tool bugs,
prompt injection, configuration mistakes, and compromised actors.

## Obligation taxonomy

The same mechanism should not govern taste and disclosure.

| Tier | Meaning | Typical available treatment | Examples |
|------|---------|-----------------------------|----------|
| Preference | Failure is cheap and subjective | concise contract guidance; no receipt | naming taste, prose style |
| Repairable invariant | Wrong state is detectable and reversible | reconciler advisory, optionally hard near a transition; retry queue | stale handover, broken link |
| Deliberation required | Consequence is meaningful but judgment is necessary | risk-triggered inspection plus content-bound receipt; optional manual independent review | migration trade-off, ambiguous public contact data |
| Critical boundary | Disclosure or action is expensive or irreversible | hard-capable independent detectors and remote controls, plus separate approval for exceptions; weaker modes must advertise weaker assurance | prohibited PII, active credentials, destructive release |

Classification is driven by consequence, reversibility, detectability, and where the
last safe boundary sits—not by words such as MUST in prose.

## Breadth-first choice space

### Mechanism families

| Mechanism | What it contributes | Characteristic failure |
|-----------|---------------------|------------------------|
| Contract or task prompt | cheap orientation and provenance | forgotten, compacted, or overridden by untrusted content |
| Template/checklist | forces named questions into an artifact | boilerplate and stale answers |
| Dynamic acknowledgement | interrupts the normal path and requests current dispositions | forgeable self-claims, rubber-stamping, and warning fatigue |
| Deterministic check | repeatable proof for narrow syntax/structure/patterns | blind spots, bad configuration, crashes |
| Semantic scanner | contextual PII/content signal | false positives/negatives, locale and model gaps |
| Sandbox/quarantine | limits what an agent may read, write, or transmit | policy can over-constrain work; not portable to every agent |
| Local Git hook | immediate staged-content feedback | uninstalled or bypassed with `--no-verify` |
| Remote admission | rejects incoming objects before refs update | needs server/provider control; remote still processes the push |
| Required CI/merge check | clean-environment replay and merge authority | too late to prevent transmission to the remote branch |
| Independent review | semantic challenge and common-sense coverage | correlated model blind spots and review fatigue |
| Reconciler/history scan | convergence and new-detector backfill | detects confidentiality loss after the fact |
| Waiver/break-glass | makes legitimate exceptions possible | broad, permanent, or self-approved bypasses |

### Enforcement times and honest guarantees

| Time | Best use | Guarantee ceiling |
|------|----------|-------------------|
| Before agent input | classify, minimize, redact, or quarantine raw data | can prevent model exposure if access and egress are also controlled |
| While editing | workspace/output scan and rapid correction | educational feedback; incomplete and agent-controlled |
| Pre-commit | exact staged-tree scan and acknowledgement interlock | prevents ordinary local commits only |
| Pre-push | scan every outbound commit and object | prevents ordinary pushes only; still client-controlled |
| Pre-receive / push protection | quarantine and reject new objects centrally | prevents accepted remote history; remote necessarily receives/processes the attempted push |
| Guarded provider/LFS/artifact API | scan or deny each non-Git egress sink | prevents only calls routed through the guarded capability |
| PR CI | diverse rescans, policy tests, ownership, evidence validation | prevents merge, not remote disclosure |
| Merge queue | retest the prospective merged result | prevents stale-base merge gaps when configured correctly |
| Scheduled/history | catch new signatures, bypasses, and legacy leaks | detection and response, not prevention |

### Candidate architectures

| Approach | Strength | Fatal weakness |
|----------|----------|----------------|
| Instructions and checklists only | portable, flexible, almost free | critical compliance depends on memory and honesty |
| One universal pre-commit gate | simple mental model and fast feedback | bypassable; false positives and detector errors can deadlock all work |
| One “smart” PII scanner | catches context patterns regex misses | remains a fallible oracle and a sensitive-data processor |
| Independent reviewer agent | useful semantic critique | shared blind spots; no deterministic boundary; ongoing cost |
| Capability sandbox alone (deferred) | prevents broad classes of reads/exfiltration | not selected now; cannot classify every permitted artifact or protect later Git use |
| Risk-tiered layered evidence gates | matches friction and authority to consequence; replaceable detectors | more design work; strongest guarantees need hosting/infrastructure support |

The last approach is recommended. The others remain useful layers or deployment modes,
but none should be advertised as a complete PII guarantee by itself.

### Deployment assurance profiles

The installed controls determine the claim; a policy file cannot declare itself secure.
An installer records capabilities, and a protected canary verifies them against provider
configuration. The reconciler and CI reject a stronger label when its required controls
cannot be observed.

| Profile | Required observed controls | Honest claim |
|---------|----------------------------|--------------|
| Feedback only | local staged scan | catches ordinary mistakes before ordinary commits; bypassable |
| Merge protected | independent required CI from a trusted source, with covered guards in `hard` mode | prohibited findings cannot merge; they may already exist remotely |
| Repository admission | server pre-receive or equivalent push protection over declared Git surfaces, with covered guards in `hard` mode | rejected objects do not become reachable refs; the host still processed the attempted push |
| Controlled egress (future) | admission controls plus an external filesystem/network capability boundary and guarded credentials for every declared sink | prohibited data cannot leave the approved boundary through covered capabilities |

If a repository lacks remote admission, a critical guard configured `hard` may still
block ordinary local commits and merges, but the harness must display “merge protected,”
never “PII cannot reach the remote.” If a declared hard capability goes unavailable,
the profile degrades visibly and its stronger transitions stop until recovery or
authenticated break-glass. Soft, manual, and off deployments never inherit this claim.

## Recommended architecture

### Three planes

1. **Policy plane** — versioned data classification, obligation tier, covered surfaces,
   required enforcement points, detector configuration, owners, and exception rules.
2. **Evidence plane** — coverage manifests, redacted findings, untrusted self-review
   claims, authenticated approvals, detector-health results, and narrow waivers.
3. **Enforcement plane** — small adapters at workspace scan, commit, push, remote
   admission, CI/merge, and scheduled audit. Each consumes policy and evidence; none
   invents policy in its own shell script.

This can remain Python-stdlib-first inside the existing automation service. Optional
provider or semantic-scanner adapters add coverage without becoming a core dependency.
Templates are the adoption boundary: installing AgentFold makes choices visible but
does not silently enable every guard. A possible future layout is illustrative, not a
required schema:

```text
templates/guardrails/
├── config.json                # every guard id -> hard | soft | off | manual
├── policy.json                # classifications and tier-to-control mapping
└── evidence/                  # receipt, finding, waiver, and run-manifest schemas

automation/guardrails/
├── AGENTS.md
├── config.json                 # adopted repository choices copied from the template
├── policy.json
├── run.py                      # one manual/automatic entry point that reads mode
├── checks/                     # small replaceable detectors
├── adapters/                   # staged, pre-push, CI, provider integration
├── fixtures/
│   ├── pass/                   # must not trigger
│   ├── finding/                # must trigger
│   └── error/                  # detector failure must not become clean
└── waivers/                    # one protected, expiring exception per file

tmp/guardrails/                 # ignored local reports; never raw matched literals
```

The root reconciler can validate the policy/evidence schemas and expiry without owning
the detectors themselves. The runner reports disabled and manual-only guards explicitly
so absence of execution cannot be confused with a clean result.

### Transition model

```mermaid
flowchart LR
    W["Agent workspace"] --> S["Candidate staged tree"]
    S --> M{"Configured mode"}
    M -- "off" --> C0["Continue; no guard assurance"]
    M -- "manual, not invoked" --> C0
    M -- "hard / soft / manual invoked" --> L{"Run local policy check"}
    L -- "Clean" --> C1["Continue with recorded evidence"]
    L -- "Judgment required" --> J{"Manual content review invoked?"}
    J -- "Yes" --> K["Content-bound review receipt"]
    J -- "No" --> X{"Mode hard?"}
    K --> C1
    L -- "Finding / incomplete / error" --> X
    X -- "Yes" --> R["Redacted report and remediation"]
    R --> W
    X -- "No" --> N["Report weaker evidence; do not block"]
    N --> C0
    C0 --> C["Local commit"]
    C1 --> C
    C --> E{"Declared assurance controls healthy?"}
    E -- "No, required hard control" --> D["Degraded: repair locally or authenticated break-glass"]
    D --> W
    E -- "No hard control required" --> I
    E -- "Healthy merge-only profile" --> I
    E -- "Healthy admission profile" --> P["Remote object admission"]
    P -- "Reject" --> R
    P -- "Accept" --> I["Required CI and merge-result checks"]
    I -- "Reject" --> R
    I -- "Accept" --> G["Protected history"]
    G --> H["Scheduled full-history rescan"]
```

In `hard` mode, critical findings do not take the self-receipt path. They are removed,
sanitized, or sent through a separately approved waiver. A scanner crash, timeout,
unreadable file, or unexplained skip is incomplete coverage—not clean—but only `hard`
turns that outcome into a transition block. Soft and invoked-manual runs preserve the
result as evidence and continue; off and uninvoked-manual paths make no inspection
claim. The merge-only edge is an explicitly weaker deployment: content reaches the
remote before CI, and the UI must say so rather than presenting that path as repository
admission protection. A future sandbox/ingress design may add controls before the
workspace; it is intentionally not part of this reviewed initial transition.

### Content-bound acknowledgement

For the deliberation tier, a local guard configured `hard` may intentionally fail once
and generate a challenge. A soft or explicitly invoked manual run can generate the same
challenge without stopping the transition. The agent inspects the staged diff and
redacted report, records a disposition
for every finding ID, and asks the acknowledgement command to bind the receipt to:

- the defined candidate envelope: repository identity, destination sink/ref/profile,
  staged tree, parents, identities, and commit message with receipt fields removed;
- the relevant policy slice and detector version;
- surfaces, redacted path locators, bytes, and file types examined;
- explicit skipped, unreadable, timeout, and not-applicable counts;
- stable finding IDs and dispositions, without matched literals;
- claimed attester identity, rationale, timestamp, and expiry.

A Git commit trailer is a reasonable portable carrier for a self-authored deliberation
claim because the envelope can exclude the trailer and avoid a circular digest. CI can
reject structurally stale claims, but it cannot prove the agent read anything. An
unchanged finding-level disposition carries forward when its path, blob, rule, relevant
policy slice, and declared context dependencies match; the new run manifest records that
reuse so genuinely unrelated changes do not create warning fatigue. A contextual
detector that cannot enumerate dependencies binds to the whole candidate tree.

A critical authorization uses a different carrier: a protected provider approval/check
record or a cryptographic signature verified against a trusted identity whose credential
is unavailable to the producing agent. A plain approver name in a file is not authority.
A committed evidence file is only an audit container unless it carries that verifiable
external assertion.

## PII and credentials worked design

### Define the actual invariant first

“No PII in Git” is underspecified: ordinary commit objects contain author and committer
names and email addresses
([git-commit-tree](https://git-scm.com/docs/git-commit-tree.html)), and names or email
addresses may be intentionally public. NIST treats PII impact as contextual and
risk-based ([NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final)).

The policy should distinguish:

- permitted repository metadata, preferably pseudonymous or noreply where appropriate;
- prohibited real customer, employee, patient, or private operational data;
- credentials and cryptographic material, which have different detection and incident
  response from general PII;
- controlled public, synthetic, or fixture data with narrow provenance; and
- combinations of fields that become identifying only together.

Recommended invariants:

- Prohibited sensitive data does not become reachable from a protected Git ref.
- Prohibited sensitive data is not transmitted outside its approved processing boundary.
- Guardrail output never reproduces a matched sensitive literal.
- Incomplete coverage or detector failure is never reported as clean.

The second invariant is stronger than Git hosting can provide: a rejected remote push
was still transmitted to and processed by the host. Environments that prohibit that
transmission need local pre-push enforcement plus filesystem/network isolation. The
portable repository can describe and test the policy but cannot create that external
boundary by itself.

### Covered surfaces

Scanning only added text in the final diff is insufficient. The policy inventory should
consider tracked blobs, every new commit in a push, content added and deleted in an
intermediate commit, commit/tag messages, author identities, filenames, symlinks,
submodules, archives, images/OCR, binary metadata, generated logs, Git LFS objects, PR
text, CI logs/artifacts, releases, packages, and mirrors. Each run emits what it covered
and what it skipped.

Each declared surface maps to its own last safe sink:

| Surface | Required pre-egress control for a no-transmission claim |
|---------|---------------------------------------------------------|
| Git blobs and commit/tag metadata | staged/commit-message scan plus pre-push or server admission over every new object |
| Git LFS | guarded LFS transfer or LFS-server admission; a pointer-only Git scan is insufficient |
| PR/issue/review text | provider API wrapper that scans arguments before submission |
| CI logs and artifacts | redacting log boundary and guarded artifact uploader before host upload |
| Releases and packages | protected publication workflow that scans payload and metadata before upload |
| Mirrors | replication job that accepts only already-admitted object IDs and rescans metadata |

The agent receives only credentials for guarded capabilities in the controlled-egress
profile. If it can call the provider or network directly, these are detective controls,
not a non-transmission boundary.

### Ingress and direct inspection

The initial implementation begins with repository content already available to the
agent; it does not promise sandboxed ingress. A future controlled-egress deployment may
place unknown external data outside tracked Git in an access-controlled quarantine and
minimize, redact, tokenize, or reject it before a cloud agent sees it. The agent may
inspect sanitized input, tool output, generated files, and the exact staged diff to
catch contextual PII that patterns miss.

Direct agent inspection is secondary evidence. If showing raw data to the model would
itself violate policy, the harness must route review to an approved local model or human;
it must not print the raw value into a prompt merely to ask whether the value is PII.

### Local feedback

When a local guard is configured to run, use cheap structured patterns, checksums,
organization-specific tokens, high-entropy signals, and file-type/coverage checks over
the staged candidate. On a finding, emit only
category, an opaque locator, and a path only when the path is independently clean. A
sensitive filename is replaced with a redacted label and resolved only inside the
access-controlled local inspection path. Low-entropy PII should not be hashed without a
key because dictionary guessing can recover it; durable fingerprints need a protected
keyed construction or must avoid value-derived IDs.

Ambiguous contextual findings may take the content-bound review route. In `hard` mode,
active credentials and high-confidence prohibited identifiers block the configured
transition. In `soft` or an invoked `manual` run they are reported without blocking and
the deployment cannot claim that boundary as protected; in `off` they are not inspected
by this guard. If a credential may have escaped the approved boundary, revoke or rotate
it before cleaning history.

### Remote authority

When the Git server is controlled and repository-admission protection is selected, run
the covered guards in `hard` mode over all newly reachable objects in pre-receive
quarantine and reject atomically. On GitHub, enable push protection and delegated bypass
for supported secrets when that profile is desired, recognizing that secret scanning is
not general PII scanning
([GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)).

For a merge-protected profile, required CI then replays the hard policy in a clean
environment, preferably with at least one different detector or configuration,
validates self-receipt freshness and external waiver authority, checks detector
canaries, and scans the prospective merge result.
Rules protect the scanner, workflow, policy, fixtures, and waiver paths themselves.
Without remote admission, document the weaker promise honestly: “cannot merge,” not
“cannot reach the remote.”

### Exceptions and recovery

A critical exception is requested by the producing agent and approved by a distinct
principal. It contains no sensitive literal and cannot suppress an entire directory.
Its signed subject includes the finding/category, repository identity, destination sink,
ref, assurance profile, covered content and context digests, reason, and expiry, so
approval for an internal ref cannot be replayed to a public package. The gate verifies a
protected provider approval record or a signature against a trusted key whose credential
is outside the agent's capability set. An `approver:` string written by the agent is not
approval.

Scheduled full-history scans catch new signatures and expired waivers. A later leak is
an incident, not a normal retry: contain access, revoke credentials, inventory every
exposure surface, remove or rewrite history where justified, coordinate clones/forks and
host caches, delete affected logs/artifacts, then add the miss as a regression fixture.
GitHub notes that history rewriting does not clean other clones or every cached surface
([removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).

## Detector assurance

Every detector or policy change runs:

- positive fixtures that must be findings;
- negative and synthetic fixtures that must remain usable;
- adversarial encodings, split values, Unicode, archives, images, large files, and
  content introduced then deleted within one push;
- crash, timeout, missing-model, unreadable-file, and zero-input cases; and
- a coverage assertion listing counts and skips.

Real misses become regression fixtures. Capability evals—how much a new semantic scanner
can catch—remain separate from regression gates that should stay near 100% pass. Review
samples of diffs and detector output periodically because a green grader can encode the
wrong behavior.

## Preserving room for smarter agents

The durable constraints in this design sit at trust and data boundaries. Everything
inside those boundaries remains open:

- policy declares outcomes and evidence, not a fixed sequence of tool calls;
- scanners and provider integrations are adapters, not framework dependencies;
- one universal mode surface makes every guard removable or manually invocable without
  changing its implementation;
- receipts trigger only on risk or findings, not every commit;
- independent-agent review is manual by default and reserved for unresolved
  high-consequence judgment;
- each non-security scaffold carries a hypothesis and eval so it can be ablated; and
- a stronger future agent may satisfy the invariant with better evidence without asking
  permission to use a better internal method.

This is deliberately less paved than an end-to-end agent workflow. The harness decides
what may cross a boundary, not how intelligence must work on the safe side of it.

## Decision and rejected directions

Choose the risk-tiered layered design as a template-first, mode-configurable system.
Keep the existing reconciler for repository-state invariants, offer replaceable
obligation checks without enabling them all by default, use local hooks only for guards
configured to run there, and add remote authority when the deployment supports it. Do
not include a capability sandbox in the initial implementation.

Reject these as sole solutions:

- more prose—the failure is forgetting;
- a universal blocking reconciler—advisory drift and confidentiality do not share a
  severity or recovery model;
- a generic acknowledgement—the agent can learn to click through it;
- one PII model—its own vendor says detection is incomplete;
- an always-on guard bundle—costly review becomes wallpaper and adopters lose control;
- CI-only scanning—remote disclosure has already occurred; and
- a mandatory multi-agent workflow—valuable for high-risk review, unnecessary ceremony
  for routine work, and still subject to correlated blind spots.

## Implementation sequence

1. Define the universal guard configuration template and exact `hard`, `soft`,
   `off`, and `manual` runner semantics.
2. Define the data/obligation policy, sink inventory, and honest assurance profiles
   before choosing a scanner.
3. Add a manually invocable stdlib coverage/result protocol and synthetic
   pass/finding/error canaries.
4. Offer fast staged-tree feedback with redacted diagnostics; adopters choose its mode
   instead of receiving an always-on hook.
5. Add risk-triggered, content-bound self-receipts for deliberation-tier findings,
   including dependency-aware carry-forward for unchanged finding subjects. Keep
   independent-agent review `manual` in the starter template.
6. Add authenticated external approval for critical and operational exceptions; protect
   policy/check/fixture/waiver changes and validate authority where enabled.
7. Offer pre-push, pre-receive/provider, LFS, provider-API, log/artifact, publication,
   and mirror adapter templates as required by each deployment profile; never claim
   coverage for an unguarded or disabled sink.
8. Verify active deployment capabilities with canaries, then add optional scheduled
   history scans and an incident/outage exercise.
9. Measure false negatives, false-positive burden, bypass rate, detector errors,
   remediation success after feedback, and whether agents game receipts.
10. Periodically ablate non-security scaffolding against held-out agent evals.

Each step can land independently. No step should weaken the existing repository when a
later, provider-specific layer is unavailable. Sandboxing requires a separate future
design and is not a prerequisite for this sequence.

## Research sources

Primary and authoritative sources used in the breadth pass:

- [OpenAI harness engineering](https://openai.com/index/harness-engineering/) — short
  root map, structured design docs, plans, and mechanical documentation checks.
- [GitHub Spec Kit](https://github.github.com/spec-kit/reference/agentic-sdd.html) —
  specification, research, plans, tasks, and consistency/convergence analysis.
- [Software Engineering at Google: Design Docs](https://abseil.io/resources/swe-book/html/ch10.html)
  — goals, trade-offs, alternatives, and design review.
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  — simple composable patterns, parallel workers, evaluators, and environmental feedback.
- [Anthropic: Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
  — clear tool boundaries, held-out evals, and avoiding strategy overfitting.
- [Governance Decay](https://arxiv.org/abs/2606.22528) — experimental evidence that
  lossy context compaction can remove governance constraints.
- [Git hooks](https://git-scm.com/docs/githooks) and
  [receive-pack quarantine](https://git-scm.com/docs/git-receive-pack) — local bypass
  and remote rejection semantics.
- [GitHub secret-scanning scope](https://docs.github.com/en/code-security/reference/secret-security/secret-scanning-scope)
  — documented skips, timeouts, pattern, and push-protection limits.
- [Microsoft Presidio](https://microsoft.github.io/presidio/) — multi-method PII
  detection and its explicit non-guarantee.
- [Yelp detect-secrets design](https://github.com/Yelp/detect-secrets/blob/master/docs/design.md)
  — heuristic scanning, baselines, audits, and human interpretation.
- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final) — contextual PII
  identification and impact-based protection.
- [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) — security practices
  integrated across the software lifecycle.
- [OWASP AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
  — least privilege, input/output validation, separation of decision and execution,
  and adversarial testing.
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
  — protected required checks, expected sources, and merge controls.
- [GitHub push-protection bypass](https://docs.github.com/en/code-security/concepts/secret-security/bypass-requests)
  — audited, delegated exception handling.
