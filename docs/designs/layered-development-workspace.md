# Layered development workspace

**Status:** proposed architecture; the first read-only topology-inspection slice is
implemented for review, while repository creation, migration, session admission,
capability isolation, and publication remain separate decisions
**Last-updated:** 2026-07-24

## Outcome

Give a human or agent one coherent development experience across public, private,
restricted, raw, and disposable material without pretending that a Git convention or
directory name is a confidentiality boundary.

The governing invariant is:

> Every byte has one physical origin, one publication zone, and an explicit set of
> allowed sinks. A convenient logical view may compose origins, but it never changes
> their authority, retention, or publication rules.

The design optimizes daily editing for the common public-plus-private case. It does not
claim that a process running as the same operating-system user is unable to read sibling
paths. Content separation and capability separation are different claims and require
different evidence.

## Claim vocabulary

| Claim | Meaning | Evidence required |
|---|---|---|
| Storage topology | Declared roots do not overlap, declared Git repositories report separate metadata/object paths, and the publisher reports no alternates. | Strict path resolution, filesystem identity/ancestor comparisons, and read-only Git metadata inspection. Hard-link sharing, undeclared roots, mounts, configuration authority, and file bytes remain uninspected. |
| Content admission | An exact public candidate's bytes, modes, paths, metadata, and detector coverage were inspected. | Content-addressed projection, explicit clean/finding/incomplete/error/unsupported state, authority result, and receipt. |
| Capability isolation | The publishing process cannot read private objects, restricted/raw roots, private credentials, or an unrestricted output sink. | Independently trusted enforcement fixes a non-expanding capability set for the bound process tree and operation lifetime; in-runtime attestation and continuous monitoring cover mounts, descriptors, IPC, agent/control sockets, identities/connectors, credentials, subprocesses, and network/telemetry egress. |
| Publication admission | A named export was reviewed and admitted to a named public destination. | Immutable export digest, scan evidence, source/base identity, human or policy receipt, and destination identity. |
| Backup evidence | Replication/coverage/freshness facts were observed for an exact target. | Destination/snapshot identity, covered target/version, time/expiry, key and destination availability, plus a separate restore-verification state. Observation alone is not a recoverability claim. |

The first implementation slice verifies only declared storage topology. It always
reports content admission not inspected, object-file sharing and Git configuration
authority not inspected, capability isolation unverified, publication admission not
inspected, and publication via the inspector unavailable.

## Trust assumptions and non-goals

The design assumes:

- Git correctly reports repository/common/object directories;
- an installer or operator binds a trusted Git executable outside the declared
  workspace roots; the first slice does not attest that binary's supply chain;
- the local filesystem reports path identity, ancestor identity, and symlink resolution
  honestly;
- trusted policy authors are identified before their instructions are composed; and
- a later capability adapter can attest its own complete ambient capability graph
  independently of the integration source.

It does not assume:

- `.gitignore`, sparse checkout, a private branch, a local hook, Git LFS, encryption
  filters, nested repositories, or symlinks prevent reads or publication;
- a private Git remote is suitable for secrets or erasure-sensitive personal data;
- a clean detector result proves that content has no secrets or PII;
- filenames are harmless metadata;
- an editor's combined tree identifies the storage or Git destination; or
- a same-user publisher is capability-isolated merely because it is a separate clone.

Mount providers, automatic publication, destructive migration, private-repository
creation, and secret/PII classification are outside the first slice.

## Zone model

The non-Git workspace envelope contains separate physical roots. A logical status view
may present them together, but tools write to origins rather than to an ambiguous merged
mount.

| Zone | Physical/version model | Allowed sinks | Agent access and metadata | Recovery/loss contract |
|---|---|---|---|---|
| Public | Public base present in the private integration checkout; admitted projections enter a separate public publisher and public remote. Public-intended work remains physically private until admitted. | Private integration history, sealed export envelope, clean publisher, named public remote. | Ordinary development access. A public label is destination intent, not declassification; filenames become public only when admitted. | Public remote plus local clone; observed public commit/push is publication evidence, not proof that worktree/config/stashes are backed up. |
| Private/customized | Ordinary commits in the private integration repository, including same-path overrides of public files. | Private integration object store and approved private remote only. | Agents admitted to private development may read it. Presence and filenames are private by default outside that context. | Observed private commit and push/snapshot; unpushed commits are not reported as backed up. |
| Restricted | Sibling root outside every Git worktree for secrets, credentials, erasure-sensitive PII, or contractually restricted inputs. | Named restricted store/vault and redacted derived output only. Never Git or an export envelope. | Access requires a separately admitted capability whose full ambient graph and output sinks are enumerated. Same-user/cloud-agent access is not implied. | Destructive operations require exact target/version coverage, policy-valid failure-domain/immutability, current destination/key availability, freshness, matching restore verification, and source revalidation or exact human loss acceptance. |
| Raw durable local | Sibling root outside Git for large, unknown, or source-of-record inputs whose retention is appropriate but Git is not. Raw is a lifecycle state, not a lower confidentiality class. | Named processing jobs, approved durable backup, and deliberately classified derived outputs. Unknown raw input is non-exportable. | Access is task-specific. Filenames and directory shape may be sensitive and are redacted by default. | Explicit loss tolerance plus independent snapshot/replication and restore evidence. Local-only means loss is possible. |
| Temporary | Sibling scratch root outside Git and other durable zones. | Disposable outputs and classified promotion into another zone. | Normal task access; output inherits the most sensitive source classification until deliberately reduced. | No backup promise. Automatic cleanup is allowed only inside the exact temporary root. |
| Public publisher | Separate clean Git repository and object store that consumes only admitted export envelopes. | One exact public ref update on one named public remote. | Topology-separated only; content admission and capability isolation require separate evidence. | Public commit/push is publication evidence; no private history is available for recovery. |

The future manifest/status control plane is private metadata; it does not live in public
Git. An absent private integration root is not equivalent to “there are no private
overrides.” It produces `private-unavailable` unless the operator explicitly selects
public-only mode.

## Recommended topology

```text
workspace-envelope/                 # not a Git repository
├── integration/                    # private Git: public base + private commits
├── restricted/                     # no Git
├── raw/                            # no Git
├── temporary/                      # no Git, disposable
└── publisher/                      # clean public Git, separate objects/no alternates
```

The names are illustrative; filesystem identities and declared roles matter, not folder
spelling.

### Private integration source and admitted sessions

The integration repository admits a public base and stores private commits, public
candidate records, and private same-path results. Its only push destination is private;
it must not have a usable public push path. Private objects remain reachable in its
history even if the current tree looks public.

The repository path is source storage, not the supported tool entrypoint. The supported
everyday entrypoint is a future envelope-level launcher that verifies the exact
integration repository/ref/HEAD, index and worktree state, private manifest and override
lineage, independently witnessed control-plane generation, expected public base, and
effective-tree digest. It marks the source path visibly `source-only`, opens a supervised
private session, and issues a short-lived lease bound to those values. Editors, search,
tests, language servers, and agents launched by the session retain native file and Git
behavior.

The supervisor distinguishes authorized session mutations from unrecognized drift. It
admits at most one mutation against a control generation. The authorization binds the
session and lease identities, a single-use mutation nonce, prior generation, exact
operation class, permitted logical write set, and the admitted process-tree generation.
An OS-enforced writer gate makes that process tree the exclusive source writer for the
mutation window; ordinary editors can retain native file I/O only inside the permitted
set. Before the gate permits its first write, the supervisor durably records the open
mutation intent and exact pre-write identities/digests. Protected refs, manifests,
witnesses, and instruction receipts are never directly writable by editor processes.

A save or permitted Git operation enters `updating`: operations that require stable
state pause while the mediator inventories the exact resulting paths and digests,
reclassifies them, and performs one compare-and-swap from generation `G` to `G+1`. The
consumed mutation receipt binds both generations, the nonce, permitted writes, actual
result digests, and CAS outcome. The session remains `updating` after local CAS; only
the matching committed witness makes `G+1` admitted and permits lease renewal. A CAS
failure or missing witness commit leaves no admitted successor. Authority conflicts or
failed reconciliation stay blocked. A ref/manifest/witness change outside that mutation
protocol, an unknown writer, a second writer, or a stale generation revokes the lease
and terminates admitted long-running tools before the session becomes unavailable.

An admitted private-reading session has no ambient public credential or unrestricted
network path. Its capability adapter either permits only exact private endpoints with
remote-side private-scoped credentials, or makes the session local-only. A public URL,
alternate Git transport, helper, inherited credential agent, or raw socket is denied.

A global publication-block claim additionally requires the integration object store to
be readable only by a separate capability principal/container/VM whose entire process
set has that same egress and credential fence. If a same-user direct process can read
the source, topology is still observable but sealed publication mode is unavailable;
that process can bypass AgentFold and no global block is claimed. The later publication
review must test non-session direct-push attempts and cover the integration source as
well as the clean publisher.

A direct process intentionally opened against the source path receives no lease,
effective-instruction receipt, layered credentials, or integrated-workspace status and
is outside the supported product claim; the source marker and status identify it as
quarantined raw state. Same-user filesystem access cannot prevent a determined bypass
and is never presented as capability isolation. Manifest loss does not rewrite the last
private worktree to its public base, while a direct Git branch switch is an explicit
unsupported source operation rather than a fallback.

Public-only in this design is non-executing, read-only inspection of declared public
state. The inspector may run its own fixed read-only control-plane Git queries against
the publisher with inherited `GIT_*` state removed and system/global configuration
disabled. It binds a canonical regular Git executable outside every declared root from
an explicit installer/policy input or fixed platform candidate list; inherited `PATH`
cannot select it, and status reports that executable authority is not attested. The
first slice runs only fixed `rev-parse` control queries, which do not invoke hooks,
filters, credential helpers, remotes, or workspace commands; it preflights local/common
configuration and rejects includes, external worktrees, non-regular metadata, or a
timeout before trusting the result. It rejects
integration/restricted/raw/temporary roots and launches no user or workspace subprocess.
Public-only has no writable source workspace and cannot run tests, hooks, build tools,
or instructions. A future authoring flow would need its own source checkout, envelope
path, authority policy, and capability review; the clean publisher is never that
checkout. The first topology inspector implements neither session admission nor
authoring.

### External no-Git roots

Restricted, raw, and temporary roots are siblings rather than descendants of a
worktree. That prevents accidental Git discovery and gives backup/retention tools an
unambiguous target. It does not stop a same-user process from reading them; operating
system capabilities own that stronger claim.

### Clean publisher

The publisher is a separate clone or repository with a distinct common directory and
object store. It has no Git alternates, no shared clone object dependency, and no
private remote or credentials. A linked worktree, local clone using shared objects, or
separate branch is rejected because private objects remain reachable.

The publisher accepts a future sealed export envelope, not a branch from the integration
repository. A later envelope/admission protocol may establish content separation; the
topology alone does not. Before capability isolation exists, supported AgentFold
publication stays unavailable; this is not a claim that arbitrary same-user processes
cannot transmit bytes.

A passing topology inspection establishes only that declared roots were disjoint under
the inspected filesystem view, the declared repositories reported separate metadata and
object paths, and no publisher alternates file was observed. It does not establish that
the publisher contains no private bytes, that files are not hard-linked, that undeclared
mounts or roots are absent, that an unmarked detached Git directory names a no-Git root
as `core.worktree`, that the observations were one atomic filesystem snapshot, that
credentials are constrained, or that publication is safe.

## Alternatives considered

| Approach | Everyday ergonomics | Conflict/provenance quality | Confidentiality and leak paths | Portability/recovery | Decision |
|---|---|---|---|---|---|
| Private integration history | Native editor, Git, test, blame, merge, and same-path behavior. | Native textual three-way merge; semantic authority still needs a separate gate. | Private objects coexist with public-base objects; pushing the wrong remote leaks history. | Excellent Git recovery and macOS/Linux portability. | Selected for normal versioned work, with a sealed publisher. |
| Sibling repositories plus materialized view | Clear origins, but edit/rename routing and regeneration need custom tooling. | A manifest can expose base digests, overrides, and tombstones precisely. | Strong content separation if the view never becomes a publication source; generated copies can leak. | Portable but operationally heavy; recovery needs source/view reconciliation. | Borrow provenance/status ideas; defer writable view. |
| Resolver-native layering | Excellent for structured schemas and declared merge rules. | Best semantic conflict handling for supported formats. | Generic tools still see physical files and may bypass the resolver. | Portable per resolver; incomplete for arbitrary code and `AGENTS.md`. | Use later only for schemas that opt in. |
| Private patch stack | Delta-only and reviewable against a public base. | Explicit staleness and textual conflicts. | Patch files can contain the full private content and need private storage. | Awkward for binaries, renames, bidirectional edits, and team collaboration. | Not the primary workspace. |
| Nested repositories and symlinks | Simple navigation at first. | No same-path merge semantics; Git ownership is easy to misread. | Ignores are bypassable, gitlinks are accidental, links can expose external paths. | Fragile across tools/platforms and poor incident recovery. | Rejected as boundary; links may only be convenience under explicit provenance. |
| Union/overlay filesystem | Appears to give one tree. | Upper-layer shadowing hides lower changes; copy-up is not conflict resolution. | Mount configuration and lower-layer access remain capability-sensitive. | OverlayFS is Linux-specific; macOS requires another provider and recovery differs. | Defer as optional adapter after the logical model is proven. |

Linked worktrees, sparse checkout, private branches, Git LFS, hooks, shared clones,
bundles, and `format-patch` are also rejected as publication boundaries. Patches and
bundles may themselves disclose paths, bytes, authors, messages, and reachable objects.

## Same-path customization and updates

A future provenance manifest owns the logical tree. For every logical path it records:

- admitted public base commit and blob identity;
- explicit public-candidate commit/blob identity, if public-intended work exists;
- private effective-result commit/blob identity derived against that public candidate,
  if present;
- tombstone identity when the private layer intentionally hides a public path;
- last base identity against which the override was reviewed;
- monotonic private control-plane generation, predecessor, and independent witness
  identity;
- effective zone and allowed sinks;
- instruction-bearing status and authority source; and
- availability, scan, and backup evidence states.

Every logical binding has exactly one canonical state:

| State | Meaning | Effective-tree behavior |
|---|---|---|
| `base-only` | The admitted public base is current and no private result or public candidate exists. | Ordinary content is available. |
| `current` | The private result is bound to the current base and optional current public candidate. | Ordinary content is available. |
| `tombstone` | A current ordinary private tombstone is bound to the current base/candidate. | The ordinary path is intentionally absent. |
| `updating` | One admitted mutation is in its exclusive writer/CAS window. | Dependent and protected operations pause. |
| `stale-base` | The admitted public base changed after review. | The affected path and dependents block. |
| `stale-candidate` | The explicit public candidate changed after the private result was bound. | The affected path and dependents block. |
| `textual-conflict` | Three-way content reconciliation did not produce one result. | The affected path and dependents block. |
| `authority-review-required` | Text reconciled, but instruction authority has not been re-admitted. | Instruction use and protected operations block. |
| `authority-conflict` | An instruction replacement/tombstone conflicts with admitted authority. | Instruction use and protected operations block. |
| `private-unavailable` | Required private state, witness, binding, or lease is absent or invalid. | Layered composition and protected tools block; no public fallback occurs. |

Only `base-only`, `current`, and an ordinary `tombstone` are stable non-blocking
states. `updating` is a bounded transition, not evidence that either old or new state
is admitted. Every stale, conflict, authority, or unavailable state blocks the affected
operation; an instruction-stack or control-plane failure blocks every dependent
protected operation.

The effective-state rules are:

1. A current private result wins for ordinary effective content, while both the
   admitted public base and explicit public candidate remain visible in status/diff.
   Public export uses the candidate, never inferred hunks from the effective file.
2. A tombstone hides an ordinary public path only when its provenance record is
   available. An instruction-bearing tombstone is `authority-conflict`, never an
   effective deletion; changing/removing public safety policy requires its own
   protected public decision.
3. When the public base changes beneath an override, status becomes `stale-base`
   until a three-way textual and semantic review is recorded.
   Changing the explicit public candidate also invalidates its bound private result
   as `stale-candidate` until that result is reapplied and reviewed against the new
   candidate.
4. A textual merge conflict is `textual-conflict` and blocks the effective tree.
5. A clean textual merge of instruction-bearing content is still
   `authority-review-required`.
6. Missing manifest/private state, a mismatched ref/HEAD, or an invalid admission lease
   is `private-unavailable`; the lower public file is not silently exposed in layered
   mode and protected tools stop.
7. Public-only mode is an explicit non-executing, read-only inspection with visibly
   reduced guarantees. It means no private integration role was declared or composed,
   not that no override exists or that publisher metadata has no external association.
   It is not the effective integrated workspace, and all writes and user/workspace
   subprocess execution stay blocked.

Generic `AGENTS.md` is treated as a whole semantic authority document until a versioned
schema declares field-level override behavior. Position never grants authority.

Every accepted private control-plane generation is also witnessed by an independently
durable owner-controlled checkpoint. The checkpoint stores the generation,
predecessor, manifest digest, transaction nonce, and identity of an opaque encrypted
recovery envelope sufficient to reconstruct that exact private generation record
without exposing cleartext paths or content to the witness store.

Generation acceptance is an idempotent three-step transaction:

1. Persist an immutable local successor record and recovery envelope, then durably
   prepare the witness for exact tuple `<G, G+1, manifest digest, nonce, envelope>`.
2. Atomically compare-and-swap the active local generation from exact predecessor `G`
   to that prepared successor.
3. Commit the same witness preparation. Repeating any step with the same tuple is
   idempotent; another tuple for either generation is a conflict.

Recovery compares the local active generation, local staged successor, and witness
state before any lease is issued. In this matrix, current `G` already has its committed
witness:

| Local state | Successor witness state | Required disposition |
|---|---|---|
| Active `G`, no open intent or staged successor | None | `G` remains admitted. |
| Active `G`, open intent, no staged successor | None | No lease renewal. Inventory the permitted set against the intent's pre-write digests: close the intent only when nothing changed, or construct the exact staged successor and continue; an unclassifiable or uncertain result remains `private-unavailable`. |
| Active `G`, exact staged `G+1` | None | No lease renewal. Resume by preparing the exact tuple only when its envelope/result digests match and no competing witness exists; discard only with proof no admitted write reached storage. Otherwise quarantine and remain `private-unavailable`. |
| Active `G`, exact staged `G+1` | Prepared `G+1` | Replay the exact local CAS when envelope/result digests match, or abort only with proof no admitted write reached storage. |
| Active `G+1` | Prepared `G+1` | Validate the exact local/envelope digest, then idempotently commit the witness; no lease exists before that commit. |
| Active `G` | Committed `G+1` | Replay the exact encrypted recovery envelope and local CAS only when all bound result digests match. |
| Active `G+1` | Committed `G+1` | The successor is admitted and may issue or renew its bound lease. |
| Active `G+1` | Missing or different preparation/commit | Quarantine the local successor as unadmitted; never infer acceptance from local consistency. |
| Any state | Missing envelope, competing successor, digest mismatch, or uncertain write result | Remain `private-unavailable` for owner-directed recovery. |

Every transition is idempotent on the exact tuple. Thus an unavailable witness or an
internally consistent but older restored snapshot cannot issue a lease; local digests
alone cannot prove that a newer tombstone or stricter instruction never existed.

An exporter never infers “public hunks” from a same-path integration file. It constructs
an explicit public projection against an exact public base; rename is conservatively
delete-plus-create until a resolver proves lineage.

An ordinary save changes only the private effective result. Public intent starts an
explicit two-result transaction: its public buffer is initialized exclusively from the
admitted public base/candidate, never by copying the effective private file; an agent or
human expresses the intended public change there; and the transaction reapplies the
private result against that proposed candidate using a three-way operation. At commit
it revalidates every input binding and atomically records the public candidate, private
result, their shared base, and candidate-to-result binding in one private control-plane
generation. Failure writes neither result. Non-overlapping updates remain agent-managed;
overlap or ambiguous intent blocks the transaction without leaking the effective file.

## Instruction authority

The following monotonic composition rule is a proposal pending human review, not an
implemented authority change. Instruction composition would apply provenance before
filesystem position:

1. Bind each source to an authority receipt covering repository/trust domain, logical
   path and allowed scope, signer role/delegation, schema version, predecessor/control
   epoch, and exact digest; Git author fields alone are never the receipt.
2. Reject instruction-shaped external or raw content as untrusted data.
3. Apply public hard-safety constraints monotonically; a private layer cannot weaken
   them.
4. Permit a narrower trusted source to specialize only keys declared overridable by
   the owning schema.
5. Block any other trusted conflict and show redacted identities for both sources.
6. Bind admission to the exact public base, private override, effective result, logical
   applicability scope, and current control-plane generation.

A claimed Git author is metadata, not sufficient provenance. A clean Git merge is
evidence about text, not authorization.

For free-form `AGENTS.md`, same-path replacement or tombstone blocks until an
owner/maintainer receipt binds the public document, private candidate, effective result,
and exact logical path/scope. Every admission also binds the complete ordered
root-to-leaf ancestor stack: each ancestor's path, scope, authority receipt, exact
digest, and control generation. A new or changed descendant requires a protected
compatibility receipt explicitly confirming that it neither contradicts nor weakens
every admitted ancestor—public or private—in that stack. Public hard-safety remains
the non-waivable floor, while a private parent's stricter admitted rule cannot be
weakened by a descendant. Free-form prose is never semantically merged or declared
compatible automatically.

Copying identical bytes to a broader path never expands the receipt's scope. A changed
ancestor invalidates every descendant stack receipt that names its old digest. After
admission, the effective instruction stack is the ordered root-to-leaf list of admitted
logical instruction documents under normal directory containment. Any unavailable,
stale, or conflicting member blocks the stack. Position determines applicability only
after path-and-scope provenance and whole-stack compatibility admission.

Public-only mode only reports the admitted public instruction stack; it does not execute
instructions or subprocesses. A future executable public-only mode would require an
independently available authority-bound compatibility policy plus a capability boundary
that cannot reach private/restricted/raw state.

## Provenance-aware status view

The eventual status command presents one row per logical path:

| Field | Example state |
|---|---|
| Logical path | a service-relative config path or a stable redacted token |
| Layer identities | public base A, explicit public candidate B, private effective result C |
| Per-layer origins/zones | physical origin and allowed publication zone for A, B, and C |
| Per-layer Git state/destination | clean/modified/staged/untracked plus private/public/none |
| Candidate/result binding | exactly one canonical state: base-only, current B→C, tombstone, updating, stale-base, stale-candidate, textual-conflict, authority-review-required, authority-conflict, or private-unavailable |
| Backup state | target/version, coverage, durability, destination availability, freshness, restore verification |
| Scan state | clean, finding, incomplete, error, unsupported, not inspected |
| Instruction provenance | source identity, authority class, base binding, conflict state |

Default output identifies roots only by semantic role; it does not derive identifiers
from paths or filenames. `--show-paths` is an explicit local display choice, never an
export permission. Tool output, prompts, logs, exceptions, caches, and queue evidence
inherit the highest sensitivity of their inputs.

The first inspector reports only topology. It must label Git configuration authority,
scan, backup, and instruction provenance as not inspected rather than filling them from
configuration.

## Operations and failure behavior

| Operation | Normal path | Cross-zone or failure behavior | Human attention |
|---|---|---|---|
| Create/import | Create directly in a declared zone. | An unknown origin is `unclassified`; no Git add, link, or export occurs. | Required only for unclassified imports or protected-zone changes. |
| Read/search/tool output | Read only after the session enumerates the model/provider, subprocess, prompt, telemetry, cache, crash-log, clipboard, network, and other output sinks admitted for that root. | Output inherits the most sensitive input; excerpts and filenames are redacted outside that context. Restricted/raw access is unavailable to a runtime whose sinks are broader than the owning policy. | Required when a new capability/root or sink is needed. |
| Copy | Same-zone copy retains provenance. | Cross-zone copy is an export plus import; destination classification never declassifies source automatically. | Required for private/restricted/raw to public. |
| Move/rename | Atomic within one origin when supported. | Cross-zone move is copy, verify, then an identity-checked atomic quarantine transition; rollback keeps the source until destination/recovery evidence passes, and later deletion is descriptor-relative to the quarantined inode/snapshot. | Required when loss is not already authorized by current evidence/policy. |
| Link | Same-zone convenience only, with target provenance visible. | A link across zones retains target classification and cannot make content publishable; loops/broken targets are errors. | Required before introducing a new cross-zone link policy. |
| Stage | Stage ordinary work in the private integration repository. A separate public-candidate operation updates an explicit projection against the exact base and reapplies the private result. | Mixed integration staging remains private and is never itself an export. The publisher index is written only from a verified envelope; dirty/untracked publisher state blocks. Restricted/raw/temp paths are rejected. | None for classified private work; one candidate-level review only when public intent is ambiguous or final export is requested. |
| Stash | Private integration stash is private Git data. | It is neither backup nor public-export evidence; publisher stashes may contain only admitted public content. | None unless a destructive cleanup would remove the only copy. |
| Commit | Integration commits may contain effective private work and push privately; the manifest separately binds any exact public-candidate tree. | Commit labels do not declassify objects. Publisher commits are reconstructed only from a sealed envelope with one expected public parent and separately admitted metadata. | Public admission occurs at export, not every private commit. |
| Push | Integration pushes only to an approved private remote. Publisher requests one exact old-to-new ref transaction under a remote fencing token. | Missing/ambiguous destination, failed compare-and-swap, unexpected object closure, private reachability, scanner error, stale receipt/epoch, or capability uncertainty blocks. Advertised-ref inventories are observations, not proof about hidden server state. | Required for the eventual public export receipt. |
| CI | Requirement: private CI may consume the integration repository only under private policy; public CI starts from an already admitted clean publisher/public remote. | Public CI is never the first confidentiality boundary because content has already been transmitted. It must not fetch private history or mount restricted/raw roots. Detector unsupported/error is not clean. | Required when changing protected CI/capability policy. |
| Cleanup | Exact temporary-root cleanup may be automatic only under the non-waivable target-safety fence. | No recursive target is derived from an unresolved variable/symlink. The adapter freezes the operation's mount topology and rejects every descendant or alternate mount identity. Durable/protected deletion additionally fences writers and atomically quarantines the identity-checked target before descriptor-relative deletion. | Required to accept durable/protected loss when recovery evidence is absent or stale; never permitted to waive targeting/mount/writer safety. |
| Backup | Observe commit/push/snapshot identities. | Configured remotes/jobs without an observed result remain unknown. | Required only to accept loss or change protected retention policy. |
| Restore | Restore to a quarantine location, verify identity/classification, then admit. | A restore cannot silently replace newer overrides or tombstones. | Required for provenance conflicts or destructive replacement. |
| Incident recovery | Advance the remote publication epoch, revoke single-envelope credentials, stop/drain publishers, preserve redacted evidence, inventory reachable objects/sinks, contain access, and rebuild from a clean base. | The remote adapter rejects stale epochs/nonces atomically with its ref transaction; recovery does not claim revocation until in-flight publishers are drained or fenced. Rewriting/deleting a file is not proof of remote erasure. Inventory includes refs, tags, notes, reflogs, clones, CI artifacts/logs, caches, mirrors, and backups. | Always required for confirmed public disclosure or authority compromise. |

Normal within-zone edits do not prompt. Human interaction is reserved for:

- unclassified import;
- private/restricted/raw-to-public export;
- a scanner error/incomplete/unsupported result that cannot be repaired without
  judgment or separate authority;
- trusted instruction conflict or protected-policy change;
- destructive action on unbacked durable/restricted data; and
- incident containment or an assurance claim the current adapter cannot prove.

A scanner failure first blocks the applicable transition and routes agent repair/retry.
It interrupts a human only when judgment or separate authority is actually required.
Repeated failures and bulk imports use one canonical unanswered-action key over the
exact operation, stable workspace/manifest identity, source role and stable source
identity, destination role and stable destination identity, candidate digest, policy
revision, canonical finding-set digest, decision consequence, and required authority.
The identities are manifest-issued opaque identifiers, never path-derived labels; roles
alone cannot coalesce two decision subjects. An exact operation-plan digest may bind the
same fields but cannot omit them. Invocation or retry-receipt identity is not part of
that key. The adapter derives one deterministic queue filename/key from a canonical
serialization, performs an atomic compare-create, and attaches immutable retry receipts
to the existing unanswered action. The reconciler rejects duplicate live canonical
keys.

A changed operation input, candidate, policy revision, finding set, consequence, or
authority requirement creates a different action rather than mutating the old decision
question. A response freezes its action; later evidence uses an explicitly linked
successor. The unattended state remains blocked, so identical concurrent retries do
not create prompt storms or parallel decisions.

## Export and publication protocol

A future exporter creates a content-addressed envelope containing only:

- admitted file bytes and modes;
- logical public paths;
- exact public base commit (also the expected old OID), destination ref, and candidate
  tree identity;
- source identities and the publication epoch, nonce, and expiry;
- explicit deletions;
- scan binary digest, invocation, version, ruleset/config/database/model identities,
  exclusions, exact input manifest/object identities, coverage/result, and scanner
  output-sink policy;
- instruction-admission result;
- envelope digest; and
- exact public remote URL, authenticated server/adapter key, immutable destination
  repository identity, credential audience, admitted transport/redirect identity,
  expected new commit metadata, and the one requested old-to-new ref update.

The envelope contains no integration Git objects, private pathnames, absolute paths,
credentials, raw packs/bundles/patch mail, or unrestricted symlinks. The clean publisher
verifies the digest, applies the explicit projection to an expected public base, scans
again, and reconstructs a candidate commit with separately admitted author/message
metadata and exactly one expected public parent. It starts with only the admitted public
base closure and generated candidate objects, no extra refs, tags, notes, stashes, or
reflogs. Before any push it enumerates every newly reachable commit, tree, blob, and tag
object in the exact `candidate ^base` closure and proves each object was admitted or
generated from the envelope.

The destination independently hashes and inventories every object received before
finalization. Its received object set must equal the reserved object manifest exactly,
including unreachable objects; extra, missing, substituted, or unparseable objects
produce a retained/unknown disclosure outcome and can never update the ref.
It then combines the received set with the exact admitted base closure and independently
hashes and traverses the complete candidate closure, including every pre-existing base
object. A missing, corrupt, substituted, wrong-parent, or untraversable base/candidate
object blocks the ref update even when the newly received set is exact.

Candidate bytes remain private only before the first admitted transmission byte. Every
scanner and its rules/model loader, logs, telemetry, caches, crash handling, and network
paths must therefore satisfy the candidate's private sink policy; a clean result from
an unadmitted scanner is itself invalid evidence.

The publisher runs a fixed, digest-bound Git binary with a sanitized environment,
fixed `PATH`, and a sealed configuration. Hooks, includes, URL rewrites, credential
agents, push options, replace/graft state, external remote helpers, filters, and
unapproved protocols are disabled or exact allowlisted inputs. LFS pointers/objects,
gitlinks, symlinks, filters, and every other out-of-band payload are rejected unless
their bytes, transport, and destination are separately admitted and scanned.

It requests one explicit full refspec with `--no-tags` and an exact server-side
compare-and-swap over `<destination-ref, expected-old-OID, expected-new-OID>`. Mirror,
follow-tags, configured default refspecs, and extra ref updates are rejected. Pre/post
local and advertised-remote inventories must be consistent with the requested
transaction, but the receipt reports remote reflogs, hidden refs, quarantine packs,
hooks, mirrors, and retention as unknown unless a destination-side attestation covers
them.

Before accepting content, the client authenticates the exact server/adapter key,
immutable repository identity, credential audience, and transport endpoint; redirects
are disabled unless the exact redirect identity is separately admitted. The destination
adapter then durably reserves a single-use nonce/current epoch and exact
`<server-key, repository-id, audience, transport, ref, old, new, object-manifest>`
transaction. Only that authenticated reservation may authorize a revocable
per-envelope credential to transmit admitted objects into an isolated slot. Finalization
revalidates those identities, atomically consumes the reservation, verifies the complete
candidate closure, and updates the ref. The destination keeps a nonce-keyed durable
outcome bound to the same identities and distinguishing committed, aborted-and-erased,
aborted-but-retained, and unknown.

Once transmission begins, status is `publication-in-flight`, never private. A missing,
lost, negative, or unknown destination outcome becomes `potentially-disclosed` and
starts incident handling even if the ref did not change; a rejected push is not proof
that hooks, quarantine, mirrors, or retention saw no bytes. A plain Git endpoint that
cannot reserve before upload and attest the durable outcome cannot satisfy automatic
publication. Incident handling advances the remote epoch, revokes credentials, and
drains or proves every in-flight publisher fenced before claiming old authority is
unusable.

Publication remains blocked until:

1. publisher common/object directories are distinct and have no alternates;
2. the publisher consumes only the admitted envelope;
3. scanner failures and unsupported inputs fail closed;
4. destination URL, authenticated server/adapter key, immutable repository identity,
   credential audience, transport/redirect identity, server-side compare-and-swap,
   fencing epoch, one-ref update, exact received set, and complete candidate closure
   over both received and pre-existing base objects are exact;
5. no extra local refs, tags, notes, stashes, or reflogs are present; remote hidden
   state is explicitly unknown absent destination attestation;
6. instruction authority checks pass;
7. a human or approved policy binds the candidate digest, epoch, nonce, expiry,
   authenticated destination identities, credential audience, transport/redirect
   identity, old/new OIDs, and refspec; and
8. independently trusted enforcement prevents the bound process tree's capability set
   from expanding for the operation lifetime; continuous in-runtime evidence denies
   unadmitted mounts, inherited file descriptors, IPC/ptrace, credential-agent and
   container/host-control sockets, cloud metadata identities, tool connectors, private
   credentials, and unrestricted network/output channels, failing closed on unknown or
   changing ambient capability. Its receipt binds the envelope digest, nonce, epoch,
   enforcement-instance identity, exact process-tree generation, and live status; the
   destination revalidates that receipt at finalization so evidence from another
   process cannot be replayed.

A same-user local publisher can satisfy the first seven as content controls but not the
eighth.

## Backup, restore, and incident states

Backup is a set of independent evidence dimensions, not a boolean or monotonic ladder:

- policy-required durability/failure-domain/immutability and independently observed
  destination identity, actual failure domain, and enforced immutability;
- coverage: worktree, refs/objects, index, untracked files, stashes, configuration,
  and each external root;
- observed destination/snapshot identity and time;
- freshness/expiry, current destination and key availability; and
- restore: untested, failed, or verified for the exact target/version at a named time.

A local commit is version evidence, not backup evidence unless an approved independent
destination observed the required objects. A Git remote or bundle does not cover every
worktree file, index, stash, configuration value, or external root. An unavailable
backup system reports error and does not preserve an expired green state.

Every recursive deletion, including disposable temporary cleanup, first satisfies
non-waivable target-safety controls: freeze the operation's mount topology (a mount
namespace on Linux or an equivalent trusted mount-change fence on macOS), enumerate
mount identities beneath and through the target, reject any descendant/alternate mount
or filesystem boundary, open and revalidate the exact target identity, and operate
descriptor-relatively without following a replacement path. A temporary cleanup needs
no backup evidence, but it never bypasses these controls.

Durable or protected deletion additionally requires an OS-enforced exclusive writer
fence over the complete target tree. All write-capable descriptors, mappings, process
trees, and alternate mounts are drained or revoked; the adapter then revalidates the
source version and creates an immutable snapshot or identity-checked atomic quarantine
transition. Deletion operates descriptor-relative to that fenced snapshot/quarantine,
so concurrent path replacement or post-validation mutation cannot become unrecorded
loss. An adapter unable to attest the mount and writer fences keeps deletion blocked.

Loss authorization is separate from target safety. It requires either (a) exact
target/version coverage, independently verified actual failure-domain/immutability
evidence satisfying policy, current destination/key availability, policy-valid
freshness, and matching restore verification, or (b) a human receipt accepting the
exact immutable target, quarantine/deletion operation, nonce, and expiry. The receipt
is atomically consumed by that transition but can waive only recovery/loss evidence;
it can never waive target identity, mount isolation, writer fencing, post-fence
revalidation, immutable quarantine, or descriptor-relative deletion. Merely observing
a commit, push, bundle, or snapshot satisfies neither authorization path.

Restore preserves the original until the restored content, provenance, and authority
are verified. A missing private repository or manifest blocks composition. Incident
evidence uses digests and redacted tokens so the recovery record does not repeat leaked
content or sensitive filenames.

## Platform baseline

macOS and Linux are the supported baseline. Textual canonical paths are not identities:
case-insensitive and Unicode-normalizing filesystems may expose multiple resolved
spellings for one entry. Root and Git-metadata comparisons therefore use filesystem
identity for each path and its ancestors after strict symlink resolution; an identity
error or concurrent disappearance fails closed. The logical model, CLI, identity-aware
boundary checks, Git object-store checks, and redaction are portable between the
baseline systems. Linux OverlayFS or a future macOS filesystem provider may be adapters,
never the source of truth.

Windows support is deferred where symlink privileges, path rules, or provider-specific
mount behavior would complicate the baseline. Public-only and topology inspection may
be extended when tests show equivalent semantics.

## First reversible slice

The `inspect_workspace_boundaries.py` command is a manually invoked, read-only topology
inspector. It:

- requires an integration root unless public-only mode is explicit;
- requires a declared publisher Git worktree but reports publisher cleanliness,
  refs/stashes/remotes, and content not inspected;
- resolves symlinks and rejects identity-equal or nested roots, including case and
  Unicode-normalization aliases where the filesystem treats them as one entry;
- verifies each declared Git root is the reported non-bare worktree top level;
- verifies distinct Git common and object directories;
- rejects publisher object alternates;
- treats only a missing directory entry as absence when checking alternates and direct
  repository markers; permission or I/O uncertainty fails closed;
- rejects restricted/raw/temporary roots beneath direct Git markers or a repository
  discoverable from that path, while reporting detached unmarked worktree association
  not inspected;
- binds a canonical regular Git executable outside declared roots from installer/policy
  input or fixed platform candidates, never inherited `PATH`, while reporting its
  authority not attested;
- removes inherited Git-prefixed state, uses a minimal execution environment, disables
  system/global Git configuration, and runs only fixed read-only `rev-parse` queries;
- rejects local Git includes, configured external worktrees, non-regular config
  metadata, and query timeouts before they can become an unbounded dependency;
- reports omitted zones as not declared;
- redacts physical paths with role-only opaque labels by default and JSON-escapes an
  explicit `--show-paths` display; and
- reports storage topology only, with publisher cleanliness, content admission/
  object-file sharing, detached Git-worktree association, Git executable authority,
  and Git configuration authority not attested/inspected, point-in-time/non-atomic
  observation, capability isolation unverified, publication admission not inspected,
  publication via the inspector unavailable, and scan/backup/instruction provenance
  not inspected.

It does not create or migrate directories, inspect content, scan for PII/secrets,
generate a manifest, mount a view, produce an export, or push.

## Verification and staged delivery

The design is delivered in independently reversible stages:

1. topology inspector and tests;
2. versioned private workspace manifest and status model;
3. override/tombstone lineage;
4. provenance-aware instruction admission;
5. cross-zone operation semantics; and
6. backup/restore evidence.

Each stage must narrow its claims to observed evidence. A later implementation may
replace the proposed hybrid only if it preserves the invariant, status semantics, and
human-interruption budget.

The export envelope, capability-isolated publisher, controlled egress, and automatic
publication are reference architecture only. They require a separately bound human
review before an implementation task, adapter, template, or mode is admitted.

## Research anchors

- Git worktrees share a common repository and most refs:
  https://git-scm.com/docs/git-worktree
- Shared clones use alternates and can become corrupt when the source prunes objects:
  https://git-scm.com/docs/git-clone
- Git repository alternates extend object reachability:
  https://git-scm.com/docs/gitrepository-layout
- Sparse checkout changes the working tree, not the repository's history:
  https://git-scm.com/docs/sparse-checkout
- Fetch and push destinations can differ:
  https://git-scm.com/docs/git-config
- Bundles contain reachable Git objects, not complete worktree/config/backups:
  https://git-scm.com/docs/git-bundle
- Git ignores specify intentionally untracked paths; they are not access controls:
  https://git-scm.com/docs/gitignore
- OverlayFS uses upper/lower shadowing and copy-up:
  https://docs.kernel.org/filesystems/overlayfs.html
- Bind mounts expose host paths selected by the runtime:
  https://docs.docker.com/engine/storage/bind-mounts/
- macOS App Sandbox capabilities are separately declared:
  https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox
