# Production-contract provenance POC

This file is generated in full by `audit_readme.py` from the closed
`evidence.json` manifest. Do not edit observations here by hand.

## Result

The real-Git self-test passed 229/229 scenarios, 4/4 executable aliases, and 41/41 damaged-mode controls.
It imports and calls the worktree's actual `queue_action_identity` and
`queue_deletion_problem`, and `queue_mutation_problem`; it never invents
an Action-ID or lifecycle verdict.

Canonical evidence artifact: `sha256:40db59e4e039ced600aca22c574bd21749c7c714d7ae5b4f1bef58fd8b8a3d31`.
Canonical semantic stream: `sha256:7c31d6ff191505c0b3ab2d62f41785f8df7baedacfbca412b646c3c600f41a28`.
The raw JSONL stream is ephemeral and has no stored hash claim.
Evidence schemas v2 at commit `0b80c342feb310d73de6564aab2224a899f42486`, v3 at commit `7f4a1ffacd1cf8163f597daa186f801e9ce06a3a`, v4 at commit `cce76a037f1584ff7d37048cb4411bdf0f5aa907`, v5 at commit `d12b799a2fa27b05a5ee2af1b422131856296b41`, v6 at commit `9ab61c416be1911e44c6bce2b3d711b6f2abef15`, v7 at commit `820ae1a788f5b24493a4277fb4d79981e0be202f`, v8 at commit `c3793ec53c9b6aebe03b6e1b1cfa7badf3d4828a`, v9 at commit `8abc908840191185e222a29132e72630ebf73a21`, v10 at commit `5872446ad4ed1e9940f96b6e28b8f7042fccf6d1`, and v11 at commit `1e1b81adae4cba13d29fac221a3de6ea78612ce7` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `agentfold-production-contract-evidence/v12`.
The execution-bound runtime landed in commits `c32f470977735a63feaf377ca9290353d1520e0e` and `850d02587f7f812b7dde9667a39da80b4ce48764`; the latter binds literal refusal at the 68th parent token.

## Contract exercised

The classifier accepts exactly two immutable inputs, old tip `O` and new tip
`N`, and derives the unique merge base `C`. It enumerates the full C-rooted
`C..N` ancestry-path frontier once. Immediate outside-`C` parents remain
identity-discovery boundaries, never event children. A boundary parent with no matching identity is
neutral and its ancestors remain unopened; any matching identity there is a
collision. Production identities map to exact
path lists, so multiplicity cannot collapse to membership. O-side and C-descendant
carrying paths require one continuously valid `C`-rooted occurrence. Every
linear carry edge calls production mutation authority and its frozen-byte
complement; a carrying merge chooses one source and checks every other parent
as a binding/frozen-compatible carrier.

Direct mode requires every carrying parent-to-child deletion edge to pass
production deletion authority independently. Supplier mode requires one earlier
real deletion root, continuous absence to absent parents, live carrying parents,
and merge adoption. Carrying-to-merge edges remain propagation-only.

A supplier root carries a domain-separated `queue-supplier-support/v1` certificate
binding the real authority edge, raw non-action tree delta, every concrete path
referenced by the authoritative action, typed lifecycle obligations, and a
canonical digest. Adoption exact-copies the closest absent source's current
support projection. Earlier source-lineage evolution is allowed; adoption drift,
dropped evidence, conflicting projections, incomplete leaf coverage, or a failed
typed obligation blocks. Pickup accepts one uniquely claimed resolving task with
no pickup backlink; retry reruns its checker. Unsupported successor/reask and
boundary-review support dependencies fail closed.

Concrete human response/review binding is anchored at `O` and unified across
every real authority or propagation parent. Only outer-trimmed plain `pending`
is the Review target/revision pending sentinel. Final absence remains continuous
to the fixed `N` frontier; reintroduction and every invalid, ambiguous, or
additional causal root reaching `N` aggregate complete evidence and block.

Workflow transport is non-authoritative metadata around exact `O,N`: push uses
immutable event `before`/`after` and never `github.sha`; PR synchronize uses
top-level `before`/`after`, requires `after == pull_request.head.sha`, and makes
no API lookup. Created/deleted zero endpoints and an unavailable old `O` are
explicit coverage-unavailable results; the latter exits 2 with no fallback.

All four transports reject identical O/N before the transaction factory or
any Git child. A budget is likewise admitted before execution only when it is
`None` or an exact positive integer; zero, negative, Boolean, float, and string
values fail closed with zero transaction entries and zero Git children. Non-mapping
payloads and non-string event kinds have the same stable pre-execution refusal.

The stable executable adapter entrypoint is
`prototype.py --repo ROOT --event-kind KIND --event-payload EVENT.json`.
Exits 0, 1, and 2 mean clean, blocking, and coverage-unavailable. Importers
use `event_endpoints(event_kind, payload)` and typed-U-only
`audit_event(root, event_kind, payload, *, git_runner, budget_limit=None, transaction=None)`.
The required keyword-only `git_runner` has no default, `None`, ambient, or
process-global fallback. There is no advertised ordinary O/N CLI and no
selectable non-U production route.
Each valid audit creates a private `RepositorySession` that owns its resolved
root, metrics, observer, children, descriptors, object database and caches,
carry-proof cache, and uniquely named reconciler module. The reconciler's
repository roots, mutable caches, persistent readers, active transition state,
and date are session-local; retry rendering is pinned to `2026-09-02`.
Its closed module-local subprocess facade exposes only Git `run`/`Popen` and
routes every imported child through the injected runner. It never patches or
delegates to the process-global `subprocess.Popen`.
A valid event calls the optional transaction seam once around the complete
Git-backed audit and its resource cleanup. Its context may yield a `GitSpawnObserver`;
production calls `before_spawn(exact_command)` before creating every Git
child and `after_spawn(exact_command, pid)` afterward. Thus an external
evaluator precharges every attempt while `git_processes` counts only children
actually created and delivered to `after_spawn`. Factory/entry failures create
no attempts; launch or callback throwables retain exact attempt/actual/before/after
counts. Callback throwables clean up
the child before returning unreadable or re-raising cancellation, and attach a
stable cleanup-failure note if cancellation cleanup cannot be proven. Session
cleanup finishes while the transaction remains active; `__exit__` is called once
after cleanup, cannot suppress the audit result, and final metrics are taken after
exit. Non-cancellation factory/enter/exit failures are typed unreadable, while
cancellation is deferred until independent cleanup and the permitted exit call finish.
Deterministic cancellation at the first line after reconciler load, after the
session ContextVar changes, after the runner result is published, after its local
binding, after pipe attachment,
after transaction entry, and before transaction exit leaves no private module,
child, or descriptor behind. The caller context manager is entered and exited
directly; no Python wrapper adds a delegate-entry or delegate-exit gap.
Concurrent and nested sessions, including duplicate prototype imports sharing one
immutable runner, remain isolated for the same or different repository roots; all
private module names are removed on cleanup and ambient Popen identity is unchanged.
The caller receives neither
the operation nor its result, so O/N, Strategy U, and classification remain
owned by the audit. Local, pre-push, push, and PR
synchronize each run a real non-fast-forward clean restack and genuine blocking
attack. Endpoint extraction never consults provider state, an API, a current
ref, or `github.sha`, and makes no claim about provider authority or intent.

The ten former candidate-base endpoint/adapter scenarios are retired because
that endpoint no longer exists in the classifier API. Fixture-internal commits
remain landmarks only and cannot steer attribution.

## Absent-at-C strategy comparison

Strategy U is selected for this POC. When an identity is absent at C but live
once at O and N, it independently proves exactly one all-parents-absent legal
birth on each arm, followed by uninterrupted production-valid carriage. An
all-parents-absent candidate is legal only when its historical queue header
passes the production path/actor/leaf, delivery, field, lifecycle, context,
and exact identity-round-trip projection; repository-global reciprocity and
current-template presentation remain separate admission gates. Agent actions,
including generated retries and task pickups, must be born `open`; human
decisions and clarifications must be born `waiting` and unanswered; reviews
must be born unanswered in `awaiting-artifact` or `waiting`, never `folding`.
An outside-C carrier collides; a second birth, multiplicity, post-birth absence,
delete/recreate, invalid or frozen mutation, binding regression, incompatible
merge carrier, unreadable object, or endpoint non-regression failure blocks.
Absent merge parents that do not descend from the birth are neutral.

At a carrying merge, U gathers every production-valid source edge, selects
the lexically smallest `(parent, child, path)` deterministically, and validates
every remaining edge as a compatible carrier. Real-Git controls vary source
OID order and parent order, cover three carrying parents and two explicit valid
sources, reject a truly incompatible carrier, and observe the old reject-all
mutant red. Parent-header multiplicity is deduplicated by logical parent OID
before classification: a manually encoded, `git fsck`-accepted commit with
three raw headers and two logical parents produces exactly one source and one
compatible carrier. Every accepted edge is checked by production mutation semantics.

Strategy B layers a canonical birth-state witness on U. Its witness contains
only the production identity transcript, actor, leaf, production delivery
class, frozen skeleton, and initial lifecycle/review-binding projection. It
contains no queue path, commit, timestamp, mutable retry diagnosis, or operational
counter. Both strategies clean exact cherry-pick, independently identical birth,
generated retry, task pickup, and rename/timing-move fixtures.

U's typed birth gate rejects an agent action born `in-repair` and a human
decision born with a concrete answer under both strategies. B therefore adds
no protection for those former claim-at-birth examples. B does, however, block
a fully legal pair: one review is born `awaiting-artifact` and reaches `waiting`
through the exact production publication transition, while the other is born
`waiting` with the same binding and endpoint state. Every production mutation
check accepts that edge: `True`; every endpoint non-regression check is also clean: `True`. U stays clean and B blocks only on `origin-birth-witness-mismatch`, so B is redundant for illegal births and false-blocking for a legal restack; U is selected.
Both strategies claim only equivalent valid live incarnations. Neither claims
human intent, replay/cherry-pick provenance, or a relationship between independently
identical legal births. Equal B witnesses would still not prove that one birth
came from the other. Endpoint-only equality exists only in the
`endpoint-only-origin-equality` observed-red damaged mutant; it is not a normal
strategy branch.

## Evidence publication and process cleanup

`python3 -I -S audit_readme.py --generate` requires its own isolated/no-site
startup and runs the prototype the same way with an allowlisted environment
and fresh temporary fixture root. Git is selected only from fixed system
prefixes, smoke-tested after the scrub, and its resolved path and executable
digest are bound in evidence; caller PATH and Python/Git startup variables are
not inherited. Caller-supplied JSONL and optional comparison input must match
that replay byte-for-byte before either output file is touched. Raw records are
compact sorted-key JSON, one LF per row, with a final LF and no CR; duplicate
keys, unsorted rows, CRLF, and missing final LF are rejected. The auditor
recomputes aliases, permutations, and summary invariants from scenario/control
rows. Nonexistent-OID and contradictory-result forgeries remain red even when
the same forged file is both `--stream` and `--compare`; all six pre-generation
damage probes preserve output sentinels. Both output files and their old backups
are staged and fsynced before a canonical same-directory recovery journal is
published and directory-fsynced. A directory-inode lock serializes publishers;
a concurrent publisher refuses before staging. Cancellation immediately after
the directory fd is published or immediately before close releases the lock, and
a following publisher reacquires it. An ordinary late failure restores
the old pair. If that recovery also persistently fails, the journal and verified
regular-file backups remain, every invocation refuses or restores the old pair
before generating, and a later successful invocation recovers deterministically.
Forged traversal names, malformed digests, symlink journals/backups, and symlink
targets are never accepted as recovery authority. One bounded descriptor reader
uses required `O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC`, compares lstat/pre-fstat/post-fstat
type, device, inode, size, mtime_ns, and ctime_ns, and reads no more than limit+1
bytes. Artifacts/backups use a 16777216-byte cap; journals use
the separate 8192-byte cap. Exact-limit files pass; plus-one, FIFO, device,
directory, symlink, lstat/open replacement, growth, shrinkage, and same-inode/same-size
mutation refuse. Bytes become visible only after the one raw descriptor close succeeds.
Recovery stages verified backup bytes to a distinct restore file, preserves the sole
backup until the restored target validates, and validates both newly published targets
against intended bytes before deleting the journal.
Portable filesystems still
cannot atomically exchange two paths: a process or machine crash may expose a
temporary mixed namespace, but the fsynced journal keeps it non-authoritative and
recoverable on the next invocation. This does not claim atomic pair visibility or
survival of storage loss/corruption beyond the filesystem's fsync guarantees. The
lock pins and serializes one directory inode, but pathname operations are not yet
dirfd-relative; hostile replacement of the parent directory during publication is
explicitly outside this POC's claim.

Every production `PIPE` pair is published into a construction registry before
Python regains control, converted to one raw parent-fd ownership token before
Popen, and exposed through a non-owning Python view. Immediately before
the sole raw close call, cleanup tombstones the numeric descriptor and changes OPEN
to durable UNKNOWN; only a normal return upgrades it to CLOSED. Every throwable is
therefore ambiguous and fail-closed; cleanup never retries an UNKNOWN token, so later fd
reuse cannot be closed by a stale object. The object database closes stdin and
stdout on success, abort, an already-exited child, and a stubborn child that
requires timeout then kill. Public process replacements and mutations of the
non-owning view are never granted a close callback; cleanup uses its immutable
closefd-false backing reference only after the raw token is consumed. A raw closer
that closes first and then throws is propagated as UNKNOWN, never claimed as
verified cleanup; cancellation is never swallowed. An
unclosable descriptor likewise fails closed with no action. Even an unproved
post-kill reap closes both descriptors and returns unreadable without recording
a false reap. Repeated close or abort is idempotent, and published metrics are
snapshotted only after final cleanup. The observed-red leak mutant leaves both
descriptors open after the child has already exited.

| Fixture | U | B | Witness match |
|---|---|---|---|
| Normal base advance + replayed addition | `no-finding` | `no-finding` | `True` |
| Independently identical birth | `no-finding` | `no-finding` | `True` |
| Agent action born claimed (illegal) | `blocking-finding` | `blocking-finding` | `None` |
| Human decision born answered (illegal) | `blocking-finding` | `blocking-finding` | `None` |
| Legal review publication equivalence | `no-finding` | `blocking-finding` | `False` |

## Bound r17 review outcomes

The exact reviewer DAG is clean and record-bound by `sha256:a5d35690a2d9df83a63bceb6a248d1898e417ae564f4eddaa62a3873e57d3edd`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.
R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `sha256:57ea9f8bed74a5a06115778d3aff6fd65af2d2a58cff4d59eab59bfece423afa`.
The hidden-G attacker is clean at exit 0 and record-bound by `sha256:ae2db8a0006342fcb66fb03f71bf835550c4e7147118cef98ca05a4692ab2231`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.
R6-02 is explicitly dispositioned clean and record-bound by `sha256:01adac5c954eb3d6b58d9ae1a9ded269e293351b9971b6493e794ae5d8cee333` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.
All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.
The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `sha256:05489d56a44f65a444e22722694af14140c139841df146c964b841e7cacfafc4`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.
The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at 4, freezes later counters, and is record-bound by `sha256:d7102979bd1f64c2d1e5d873b692b73d200f2e4cae24fafa37318c0ed689ced7`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.
Ten runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, certificate serialization, origin-arm nodes/parent edges, and canonical birth-witness bytes. Every +1 refusal exits 2 with zero partial results; graph reads peak at 256 bytes per chunk and publish nothing on refusal. P22 separately observes exactly 129 imported production parent queries, 135 Git spawn attempts, and 135 actual Git children.
Unreadable Git objects use the stable typed reason `missing-or-malformed-commit:b5fcd8d0260da07b741462af3e3e2b49b546d600`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.
Before any projection or digest, all 273 raw rows must match the static recursive key/list/type grammar catalog `sha256:cc668580b07563929d4fcb1a133fc23b839d89d9f65e59f8a85344b1d61a7219`; an unknown top-level or nested field exits 1.
The parent-order pair has identical verdicts and the same role multiset:
`['compatible-carrier', 'source']`. The four persisted parent-order pairs and the origin-birth parent-order pair are also equal by semantic signature.

Reviewer-supplied reference OIDs (bound as review input, not regenerated fixture IDs):

| Role | OID |
|---|---|
| `C` | `030fe92b832b1bd2790182cab030b9dfd46ec6dc` |
| `F` | `233e9c9821300b9a1579c261a37b3829d0459250` |
| `K` | `920d63682562575383ac5adbaf33c5855d24a554` |
| `N` | `3a60d2c225bbcdf0619135111af9bc0a1120dbce` |
| `O` | `07418610247abbde975bd54ac937acf75ca02500` |
| `P` | `bda691d6bc1759421cc55925e8c350edea7d42be` |
| `deletion` | `d45b8657259492bbc12f6c32a2e81a7944357ce4` |

Boundary-attacker reference OIDs (bound review input):

| Role | OID |
|---|---|
| `C` | `52c16e3ace5b2fb945b2e8fc42b7485536ea1a47` |
| `D` | `595acd03b0c0f5cee214599587247d1115b2fc40` |
| `F` | `4afa966344cb99e6a72a10997b10572072e7cccb` |
| `G` | `b838a677f5753a45bff2d33f6e94b3a80cc92905` |
| `G_blob` | `88ce173dddc1914b0e7ccd52f5b89fb4742a713d` |
| `K` | `245d7de3ef54645d32fbcf8bbda7d69f426ce6d2` |
| `N` | `61d97651036a8cc9da10662ca7560bce14ce9ce5` |
| `O` | `5ff93e594d8689fe44774a9728a882c846e1833e` |
| `P` | `6564e680097653cebcc008a0bfee8587c644057f` |

Persisted outside-C collision reference OIDs (bound review input):

| Role | OID |
|---|---|
| `A` | `426b485efa3b5f85a678600795a20b1e91c6049f` |
| `C` | `843634959ac1156ef81ee7ccbf1f703261bbde1f` |
| `F` | `e10a4eb3208c44000e7363c2894e2a77b74828fa` |
| `N` | `af48cf172570a08d65c12dc467b2226dfbe8981a` |
| `O` | `c0ec07829f6aa4e1207a680a0354deb8a8f0c162` |
| `P` | `60f5448337b6f9a114c0231b86242474dd34873b` |

Persisted absent-arm reference OIDs (bound review input):

| Role | OID |
|---|---|
| `A` | `90de0b5af2ad8baec036ddaed2842eda86c2c556` |
| `C` | `0ddb561a40c84c0590d9abe8a3036521b239de25` |
| `D` | `161d7ed2d7bc121ce5331fed2e1ecb0dd650041e` |
| `K` | `f03d61cc931d7c860e7fd6f166c60d09596b48e5` |
| `N` | `76cf3354a913effec09cac7b183684159dfd0b84` |
| `O` | `17ef4a3d8c518778d62c635864670319efd03754` |
| `P` | `1847cdbe8298d5895ad566c03abc870064ca711b` |

Wide-boundary budget reference OIDs (bound review input):

| Role | OID |
|---|---|
| `C` | `b066accf737c901fd1ee314fcf310afb70c8fe87` |
| `N` | `412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0` |
| `O` | `ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3` |
| `P` | `b79ff7a4036270fed4a70d82ad226817ae94e662` |

## Input byte identities

| Path | Bytes | SHA-256 |
|---|---:|---|
| `docs/AGENTS.md` | 675 | `sha256:5342de9cada318428ea9b091e2434ad4d1e19e173a87295fe978651dc1a04b14` |
| `docs/designs/AGENTS.md` | 709 | `sha256:0e8c04dea40750971f0a567e84dd33ae5529960629abee9323234046105649e8` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py` | 350203 | `sha256:c30913829d962280269faf2a2aca85338304f5e3c95899064828f7bf60ec693d` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py` | 658680 | `sha256:123637aebc88f18e04ea41958bfdbc0edb03d7557d746c378769a794ab6a3b71` |
| `automation/check_action_projection.py` | 123062 | `sha256:bd9f73b79b3fac94f36d8248b4ce23c6fa7826da45d562a85bd9b1e14255e0c1` |
| `automation/markdown_semantics.py` | 33735 | `sha256:a5f58a99e739af4e3e61109caa880cb68dc739d93c727b74b8e2456220641c63` |
| `automation/reconcile/reconcile.py` | 499357 | `sha256:0436489bf3bb9a52ff80e6e36962393413d626d034b029e938876f4ddd84c0b7` |

## Seven fixture SHA bindings

| Claim | Scenario | JSON pointer | SHA-256 |
|---|---|---|---|
| `r8-divergent-old-target` | `R8-review-binding-divergent` | /details/old_binding/1 | `sha256:2ab16346393dd555c10887e02261d9fa80124206e31437260fb5d50cc7185bd3` |
| `r8-divergent-candidate-target` | `R8-review-binding-divergent` | /details/candidate_binding/1 | `sha256:5ac4dea8ba9a26fa2e56de8e4ffb2d7fe0cf688e57fb6eeeb0091f9a399115bc` |
| `r8-identical-target` | `R8-review-binding-identical` | /details/old_binding/1 | `sha256:371e751cdca327cb53062048f641bba3263084738230bdd8b24ae6cc4aecb484` |
| `r8-terminal-reviewed-revision` | `R8-review-binding-terminal-conflict` | /details/old_binding/1 | `sha256:2159f135c15139aa0fdbd35362a3dd949c47c2627bee2aae17edf746e6ba5b75` |
| `r9-direct-filled-revision` | `R9-direct-review-revision-pending-fill` | /details/candidate_value | `sha256:7b0d8084905c6e81c7f74bf50eb38a2c22eac406092088111603b64855fc1575` |
| `r9-supplier-filled-revision` | `R9-supplier-review-revision-pending-fill` | /details/candidate_value | `sha256:5706f8e796fc78b6bf7465c994523dec4fe9240309bbdb51c0bda69dfe0e5b70` |
| `r10-malformed-bound-revision` | `R10-supplier-review-revision-generic-placeholder-rejected` | /details/candidate_value | `sha256:62b8e9ca2b243a2fc6baf048001d518d73455c3829217d3703fede4cd2f524b9` |

## Scenario evidence inventory

Each record digest binds its complete canonical scenario JSON, including
all nested OIDs, verdicts, reasons, paths, counters, certificates, and
carry proofs, and workflow input contracts. It is not an OID-pool membership check.

| Scenario | C | O | N | Exit | Classification | Evidence | Mode | A/P/U/S | Validation | Record SHA-256 |
|---|---|---|---|---:|---|---|---|---:|---|---|
| `P1-direct-linear-valid` | `46109f507dba3eeb6191db457fc7848c415e8979` | `2819957948197a593fb1d0dc966e747c44db9ee5` | `029be55decf7d7f65826f86684cc8605d5d47b18` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:0e95869599c309db1671274d95c7c2fac5c446c3b793a03edce91b2af6f1c234` |
| `P10-direct-invalid-parent` | `2ef716a2345dffac470956041b5245e20fbc8f98` | `1ac818d6b6ce87da87358e55015671ecf823dbb5` | `8f7e8c69c7ec6e4af250366114c90ecc24ce811d` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:61532acaf77afe5c95a0f4f1ddc6f47aa267764d1fb739284bca8bdaddade767` |
| `P11-direct-three-parent-valid` | `78ad042cef55f824658b367d8599c5523b4e601d` | `b5726dd5f1e717518fae85cf820fc7b134db83fc` | `ad16f6d1f31e155a41a236d51a7a396e54dd5ea3` | 0 | `no-finding` | `valid` | `direct` | 3/0/1/0 | `PASS` | `sha256:9fa79f9b3dc1b2ecf5d06d679a6a77c1bdab82ab5c0214835fb96ef02af4b7a9` |
| `P12-merge-supplier-valid` | `3a01d100e676a9a20f8dc545fed19be3419fb759` | `bc433c8ed8cda37d3813042f730b2f23d8e8d778` | `8dc6dbc10535cb058ee49c63a979d75966b7f248` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b8a9e4aa9c643a60aa1ec019e0750bfcfe5ea57bff0b9319e5f36751ae2f059b` |
| `P13-merge-supplier-invalid` | `c9de2e4ee2e285093b2b1ae42b597989f5e2c267` | `898789857318c82970d920a105ee1a124474e155` | `9424f0b01381a9388d58b77c06efec9a59f0249f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:412ae92c69b666ecfa22b93223ca38c8a90d791b65dfd35cc42deac0fca9184a` |
| `P14-supplier-reintroduced` | `f340f1d750e747d6cf6a74dfac05146fd208f964` | `bf8487fe5085a4dc4b483f512c51ecd10cf7c253` | `14d300ed67dece9c599e5c0d096b708cc38bafa6` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:9096573beb5fe4d020a6a36f6a471ec621194f5dab7515a896b0abaa94641cbc` |
| `P15-competing-suppliers` | `80b72ef13352057aa74028971730fbfb266b56f9` | `20a4f077a613c17b6e3f36d87f807bed9395d541` | `fe575f3eecc1f2b034bcbeb17a0021fce16bb82f` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/1/1/0 | `PASS` | `sha256:386a2f2499f09a29d3c13fb2290e957b86ea5f27dcd9ee2f2cc62491a5b3766e` |
| `P16-PCX-08-invalid-supplier-claimed-carrier` | `b76e3dd3be1c4896d95f0ade31b63eada3ec7002` | `b756376fce02251f8036c1b1560d8c6c96dd0699` | `b23ca400da3968f74afc3b950ff4d4eb27307196` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:9281beaf40bedd0ef96a99820908243e93a0187ed3ce96722f1c4d31ffc58e4a` |
| `P17-post-event-reintroduction` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:ad8a20ac87a919643fafb8a224b32217d72beaaaacbcce034e2e9b82b3e85df7` |
| `P18a-missing-tip` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `907f5d5221680a4ff7eccd647bcf26bcd5e9c4d5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:3631460ce61a7aa34c9301c7d9038726ef36616512e81a9e695a7c0315a8ee05` |
| `P18b-noncommit-tip` | `None` | `90db16de6c0119c0c924c80d206b1e80bc3d2331` | `22be33aff3fad75ef91ab1e1cae2f2f8da2987d3` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:9a333c04e49520a32541a9aa71f8fc9b1aae5686c190e2ffecf61abb8537d515` |
| `P18c-unrelated-tip` | `None` | `22628ae24f01e250d30bb4cf9c2a7832f217677e` | `e46c2df2b7bdeeedf09b55b74a3745ea6d7f5139` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:81d636c8d90f03c61ea41f07c020886edaaaab12ed4038d7ad0bda0be2aa78d3` |
| `P18d-shallow-required-region` | `None` | `e68bb90fcc341adde9f4372caff5ecc6f9b1e340` | `4303d2f9587973759de42362a6c20b4b48170ab5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:4ee7ed9733ba16bd278bff3519610adc7eb6a2af45b5708cabd98670601a094e` |
| `P18e-missing-queue-blob` | `a668e725d1233ee7d5930c077268d222dd27c277` | `8d7223893ec84e193595fe975a53d36f893502cb` | `ec9f29e0560c60e66700496cee9ce14858aebb4d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:de0e7dd75ab2ca00cd7584b23f2b43ecacbc6ec07072feebcb3a963baf09388e` |
| `P18f-missing-queue-tree` | `80ee9796305f288404f4aab5960193d8555c5e5a` | `61e6b7c9b52f0ea9ecb35c5bb8da8211aa7232d5` | `4f08ffcf2930d3d3a121b453b4b16a5b5f0bfa73` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:28850d295cae32a3ebdca800d871be16cf58522282d4634e94e859e8c3a6a257` |
| `P18g-multiple-merge-bases` | `None` | `c9a1e28be75d020fa3222bfb2a5b04649329083e` | `8e067847820ccf0c7ed10b39c330162e1b10d880` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:816f007d7000a900f9094a6bd22bd091b8e3ece1e25c128c9f3aa5e6915c67b4` |
| `P19-production-identities` | `5a986a543953cc623f320ced017dc315be4ac80e` | `7aed085d4fb3393205d57ad66e8d2834a0263bf7` | `7ceda0b76130db3d02ecd3c1d271b467980cf25e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/6/0 | `PASS` | `sha256:6700fadf0128afa8d75d58afc42499af1d02b332e5d855302a15ade24ee9568b` |
| `P2-direct-linear-invalid` | `70b791b1e8a9bd24f58737e93a443451f8f0ca11` | `ab15090d6bc10c375e03aa38f1ca6aa87d672a98` | `b00411d0cb294fe228cef9fa6744869d212bff1b` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:e9c11997ca7da7b156f784d4886283bbefce4d233b9ee16ba3476591db4d12bf` |
| `P20-lifecycle-types` | `4c9f5ab102d33b44f949f0490fa2ab6b1afef7d5` | `f01ebed3277db3c00a38c601d11a5423a35fc922` | `9de85b85f0f28f3594f681543732bdd2b76bee5a` | 0 | `no-finding` | `valid` | `direct` | 4/0/9/0 | `PASS` | `sha256:de854d12094caf357528033e8aafd8d004a4c6a14ce2372c8fffa693cace14ed` |
| `P21-PCX-17c-squash-erasure` | `34448e62dde0da7a459c9f068a1929a11404bc60` | `67154541398ed536f17c169d282b151571b9031e` | `cdd5e979ba9eeb3e6caf97b05a182981178203bf` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:ad110040627a7092438adeb2a827df23cc4884bfd6f556fc2aa5ba440765548e` |
| `P22-PCX-18-one-pass-many-actions` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 1 | `blocking-finding` | `invalid` | `direct` | 16/0/16/0 | `PASS` | `sha256:50dbd8ba9dfbaa17a55defbbc610a660be0a719c2b450ed92083af893988c0a6` |
| `P3-genuine-old-loss` | `94db247b706f734bca553f86045fba8b98158a6c` | `5fa1eba2f8984af57952e6c083a0c455fc65d54c` | `5dffe2d077e79208c3e05ec0bfdd5de39600292e` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:87e5c51c9562fa544a5f297a90b22546c34142c98106acdcb415fed9fb383806` |
| `P4-pre-C-identical-origins` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:ab9bfdf0cdef6123bfd675b604724fd8964f2464944b35f0f77b2b37f280662f` |
| `P5-duplicate-at-C` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:3afc93eb785426b5c635b168222e1dfafe2b7ad9cb16a4a62ff9bbb75c58d359` |
| `P6a-old-delete-recreate` | `8039e1a89ee29be7b3a79d4fda7aa15a8653058f` | `900438d3fe4393f0ea2f87aa4d8dfc1e188f5919` | `6781a4eaee80c8ebde47bef04c33dcb47e91bc98` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/1/0 | `PASS` | `sha256:c5b60d65ede448d1e860998d97430fe358d36a7061e43e07a88f406ea4d3ee31` |
| `P6b-candidate-delete-recreate` | `b5161adf1ba6eeb99b2181aa264598f707d19a95` | `bfb4c66d18c551b23a8580132543db2357ddb4f7` | `ca9f44b0f38c99dc7c70093046ead1b19f464389` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:4522262d361e2e62167d8f8b89a0147db277e5683e259e918ea5311286d70050` |
| `P7-immutable-payload-change` | `43f673bf99a741dc37c6631d39bd5e9c037f7368` | `523cb1cb6e17b0e00b3bc3235618cfc0834d233f` | `03ae818dc35342d03432e7e25ca292808528ff3d` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:44c9f8a1fc5430c53ce9242c2ea065647a6e0cdab881b918baa644e00419c682` |
| `P8-path-timing-move` | `1c34d6196d22c53ce54eac5b2cbed46be8432134` | `f9bdb1fd1af9e2d3b5b405594d2ef37ab55ac025` | `cef78e9bb54e4b4318172d0a2b6881da3a4b8971` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:341fb33539b2d6f8a03ae9a778dc15f5c136737bf6fc264b2b5b9fbe5e26deb6` |
| `P9-direct-two-parent-valid` | `074b437bb8582cabd4372ea380454368e8d81ab3` | `2380b58d4a6b687769359903f12100d69a543b2d` | `faa886162cc54c7c6544e33793a6e7f4342a90a0` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:0b5659372a1d31943bd06666915918493ec403e527930071e1574f76939ceffd` |
| `PCX-01-neutral-parent` | `ee5d0eb6e70a978d7da73147f1faef9615f8624e` | `c4b177d1b0039326cd6592c90f7ce62e729ed3a8` | `acc6673079b122e2ae443cc91c4012c83344430d` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:e6a9318a066cbc10cfc23e0ac5dc20861b38b35a6d97048c4d15419d8ce8426e` |
| `PCX-02-neutral-plus-invalid-carrier` | `b02a161fd6cd727aa2eb6bdf5ec43f5c5587e04d` | `78c77a131414cb7f196137896f9fd0080bb6552e` | `cf599de5003f9d108a979cb21f6d36c5c3785dee` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:1dfbbcfb51d793cdc7131e55c6e16ec6c78d1f0c853296fe9770ba939a18bcc5` |
| `PCX-03-foreign-exact-identity` | `35f271b5d18393dac59002bb0c0c794d3589659b` | `36313b4892aaa243fc2d01fd05ebc8e7ac0145e3` | `f7fb0303c3061d22daf61cdeb03cd67496639432` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:7ee12f003d1f79390d0ad8f58293cd5a2fb2afcd691acec261a9b1449893bc01` |
| `PCX-04-several-absent-one-supplier` | `32c7576c4c4aca96bdad8162078e9b2a28d6ae33` | `c4cf7124f59fc3edbec373d87507aba76143cfd6` | `cb06b9b4e0a3ae842774d0f888ebb5f1bca53881` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d2bf3e7f2fecb977c850b2946ba7eebc79ba4de365c34bfbce0d7990059bf871` |
| `PCX-05-competing-later-supplier` | `d297f8d7d5f3557c94f944194e6da99c1c092c81` | `39f138bf6fdf1db76fe12a652664dbdd3fcb33e6` | `5cc308cff656d4866cfd255d968e65ee17b58271` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:9ca1cefa930e63dcdb2cd0e8a95883fc4c1055d2f8a2c7a5cab36a129975ae0b` |
| `PCX-06-nested-supplier-over-direct` | `4fef7d2a64023363e13a455eddeac016838f651a` | `db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0` | `2513214e5beaae7f3a289d4fae4018a00971c21c` | 0 | `no-finding` | `valid` | `supplier` | 2/2/1/4 | `PASS` | `sha256:10ecfb6b9704e876461e23785360c7407e606e1b8423dbad2c25b9ecf759740a` |
| `PCX-07-overqualified-propagation` | `e9920c69e87c8fadecea9dd6bfce80039a60619b` | `4eb27ecce806ae96e902a1c1cb1098fb7e8d7ba7` | `ea08bb6dd2a18266bfd6f436011c1cc610c4c8dd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b375702dd08b4611391ad50909c50aa5407ef79bf487c5fc46f93a52ca588f9f` |
| `PCX-09-recreated-claimed-bytes` | `41008171d1f9c6afd397a17c3e5567e040d881e2` | `9e38900a6d2f2e3b48457b5fe92fb55cf68ef1ed` | `626d32b7150a4185dddc568c91f3f096abd5f4e5` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:f04663264e5f5c25f23720c8c781fe05e27d66a2d6306cf949be4cebe671e7b7` |
| `PCX-10-transient-multiplicity` | `04b5c0356d29ee676d98d58fc639efaaa47278ea` | `cb082de1d3492e0b6e85918c5b1a4d2d600a110c` | `6dc48150188c026a1300d5fa19b065b1ad6a01aa` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:40ab27cbfabcde7a580d16c6336a25aab0eb749073dec8e4ae2f41e7dde58cb2` |
| `PCX-11-different-payload-same-path` | `9f7f5b9e5ce030055a6151bed80dfb6db1a94206` | `d45b35ca53a81320262faaeb7136fd081e8c1fef` | `78876b74b5d5c2cbdd3085a992a484c82280c769` | 1 | `blocking-finding` | `invalid` | `mixed` | 2/1/1/1 | `PASS` | `sha256:6dc0c86fd2bd7975389e9150a4eec11beb7c66f4a158aea62ec916c276e01351` |
| `PCX-12-timing-rename-supplier` | `c81cd1ddc4c58f7e6d5b9bd7f0a626f972651c79` | `e89ed03c9f3c8d338d6b4f03dfee7d6994ce400e` | `97ae732aab6ceb15bba65fdc775f3b4d5115a3a2` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:f8f851385ae6b3f12cfea993a6079fe761296fe9bf799359610a34b4000d3149` |
| `PCX-13-conflicting-human-response` | `58e15401aaba3e6f056f7dbaf6789c10d35ae553` | `1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047` | `14707f668aecd10bb531aa6fa0ec57700d26844b` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/3/1/1 | `PASS` | `sha256:2bceeddee39e357685285810f2361b7a4b4431f36880c1278e714b18e02837df` |
| `PCX-14-valid-human-supplier` | `920e716ffd62703b03e21acd40423d34d60f165d` | `15ab9f04625ca7c4d6a8847bebaaa2b3169b5b69` | `36eaf058713764ea31d22a9cc74f800aaefbed1d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:5c8c2b9a01df10f8d6fc9bbab3e08ecbf52a696c11946dfab38b43fc84872ddf` |
| `PCX-15-generated-retry-supplier` | `03cab3c249ed96db646bda0085596770b15f5801` | `44457ccb883890f47979a0504d52f5da066af287` | `338762e488c1ce489527bb173d9f8e2262c5f4c8` | 0 | `no-finding` | `valid` | `supplier` | 1/1/7/1 | `PASS` | `sha256:2ad389d7ff619962d558c4eca8e9f15a5c856bf2f2c934d3fb9915b285e03bc8` |
| `PCX-16-task-pickup-supplier` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:a77da844d11832cd4ad529aa7ed02ebddee75716cdafd12f23061cf15ad2d3f4` |
| `PCX-17-complete-cherry-pick` | `33db81167dcecdaa77e3c6e97ea6305b99d13346` | `8385f0c8c1094932a794ebb94b32b4d872806cd2` | `855eaa3b813900caaa0e523baa198491cb4bc47b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3d14d7eae584563d182adc04df0b68f3126c34fd0b691cede3657317ed8f2758` |
| `PCX-17-deletion-only-cherry-pick` | `56008eecc6492c2c091a516834d675e283cc40bd` | `35b9163866f1c9cf6ab2435eeba3abfc0b9fd1fa` | `5da95440d2c9065d8b6f4506d2108a3f97bed539` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:1dd83f820d14a8f888b02abd64090940d12f751478fe041acbd9b2d72d326f5f` |
| `PCX-19-missing-claim-blob-recovery` | `759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c` | `90aed2b3f8214a269d6421e6f4fe63ad3a61b091` | `dd34454f3204840ae81e2f273772c00488e681ea` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:95812f65a03b9717a9455f1dcaefdeb68fa4b4d738cc8e4bf0d37a027f10eddd` |
| `PCX-20a-budget-below-limit` | `c957293f54b1b960b7b7f351087c77ac874eb253` | `ad76497bc5fa23076fff741b5d419a2ccd714637` | `ce775146b901f12bc2c05d22f06343da4d2c66d0` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:0b4323fd8978f6ce0e0bc08f5d6d59569ed29670a8c9fe03a931bc70e1d5c6e8` |
| `PCX-20b-budget-overflow` | `a018c90c3dbe1374339730ede5c7b76e21fee985` | `fb2043655802898f2561cc21431580a2609aef9c` | `06abdb0e773f19b6acc2ecf85d17e6c1770e7295` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:639a985a01ee06c906cfb5d71893b687713d101e0aecb048b916f0aa9634baee` |
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/2/0 | `PASS` | `sha256:2fe2dafb8643dd10db56af3a509e6203e228477912698b2b261e2bef36f0e40f` |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` | `9d96a7eecc2b34704ef588142e4b48111849f3a9` | `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 1/1/2/0 | `PASS` | `sha256:acfd2b95e3495f0afb3e65941ecb272150089bbe9f42d8217da5e3cb391797ba` |
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` | `7e0284f9a2354f44218502da59ca365cff918285` | `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | 0 | `no-finding` | `valid` | `direct` | 2/0/4/0 | `PASS` | `sha256:96e2c42c5818ea03d75b047467f6f1c0c10495b2603339057f30a057cfb4254e` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` | `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` | `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:0836ab1564db09bfe6f7c8be7335bce0038edffd90d23b5ac5d1733e5b299723` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` | `75d9c282afe629e2fee58b878ffe93481926e719` | `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:42ca982f82de2918fc35fd1f63c4bd3cdcfac474caf0d301c595c00b06062987` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` | `d784ca71704ac0bd18e1a70b45c18d1994353eb9` | `6677edfd8778a755904939d01b070af66f32bcaa` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/4/0 | `PASS` | `sha256:51d97f164add50c20112e5ff114b1d31efcf4d1cb99fa7e75922355fdc60e88a` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:b2a9bfa2b5e6f283e5c7ac028dbec46dae1a200fdf6b2651cf98915e98829a1d` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` | `5218487e636b8519c69f49d146acd9b7f8b25948` | `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:7b889acd01773c07a985e7d1aa880d6f83ca1f7293bc3f9318c92c4063b574f9` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` | `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` | `464115d4c500dda036c5592c6c8f21fe9a959e15` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:ec730ce593da08e7715f55babe6134d420e1a6489302900bf50060944cc8d651` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` | `69bbf3a1bec29fcf92121c581925bb092d1535ab` | `24126e616db515f5ee1d08d4f2da297b50e02f3a` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:ff78ee43c6e48b9c2a5215bb41730a04964c010a499949f64b97a721e9fd83b8` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` | `2c3f7acfeeb385de256074091a38c9953ce7f1f9` | `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:d16fc322b2437d61f2d68f390005bfbd1d93f9396581158af946f7fcd6d91d3a` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` | `cc3bf0c5664ca51a1c1df82759aaa607efd30550` | `344c8d4e0333b14fb5b21550528242614812a55b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:b05308730b3518766d04c5aada82bd89dee4bdf55c56037823751241eec2cc78` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` | `2c37567f76cece330ee8c4997c96aa2bcd1764e0` | `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:383548142dfb944f1188e74548003120dd2c9548da583b66fa54a27627ba8e34` |
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` | `a3edb26d4a2069954d0459dd9ea503cc27833f61` | `edee50f1fe44db9136335db0de7e27ad442f4eca` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:912f4f179c3d6dcf3fe5f10ebcf7d58f0f2caddb0f2c32b3724d45dbefaaaf80` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` | `b5ea69a78713ea41e8229125a90fa2718088c6f9` | `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | 0 | `no-finding` | `none` | `none` | 0/0/6/0 | `PASS` | `sha256:185f1a1e5faf3944f8eebe634fe65061ed5e5371e58f5d891e7f89ce84908b2b` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` | `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` | `962821fb4d4faabe72c3b8e86823a5367aa3294f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:9f6dec16b85f309fd0d2169179357e167c7a07f82d296cc5cecbf7cfd67caf51` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` | `e7a884697094e9be1c876b78fc33d9e259d92149` | `8fd2e814f38bf145bd7c84d9e22a355056d40649` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:773cca13267cf27634b051a2f319eb4ec24f93504c6225d241344650caf6b974` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:02a9930b9d3e259ba22bf81f0c7ac6e58b4bf05186edd013fee107d8cb1b033a` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` | `60538a926a9acd01f898ba0371ad5249c912f7fc` | `1031e6315881cdc99376df52bcddc86a4427e920` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:448ab658bc59b9651a5f661e0294f9be95e62264337cbaec9a072c4b8e8a1286` |
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` | `37d577cc2c265e8e7082bfd86dd156172db98c5c` | `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:284da6743cbda70933c06125414cac0315af2c32d6791201ffe6e34a7c6c57ab` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` | `d39ee31be16db2789928827c2e132a31e22b828f` | `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:f1c15588bd8f0a7213ebbe71add98705cd8bcd5f88f22e70c2ee07841358dc20` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` | `68f01125491f31f259d6cc636bc2f818c9529571` | `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:ac5f94023666eaf5f6b88fa7793c042e16797f6027a4c2a3e234c50d8f2292c9` |
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/3/0 | `PASS` | `sha256:4a593f2ddbf2fd4d29c90f3fd1f1d480e6afc99da8d2f45effbac3d84cadc7e4` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:eb6491c3b9aae3655788a806403d4f3c1bdc797d1dbbc40315b5a7544b4522f5` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` | `ceeb45bc58cb8e6726517130e20fff034db993f3` | `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:3a9febcb52c013e024b73b5348a0ab99f2c103edf7aeb84808eb003b7afb73cf` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` | `521e76aa7253b7dc1214c2bbdca5c788a601e21d` | `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/8/0 | `PASS` | `sha256:e8d2890febb03f56200f3c98ae0fbc4cbe5c558f4bb7b66362abec03951f2690` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` | `74442946b6639f57e7167838a13cc286f39d3519` | `ca8939b406b7b2323fd08b044625639f5e80cb6b` | 0 | `no-finding` | `none` | `none` | 0/0/8/0 | `PASS` | `sha256:b059d424136efce14fbf96240d9274e3f983ee1c43b70319bf45919cda5c833d` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` | `dafb69000967fde6234bce7999767113def81c5c` | `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:4df52a2aa9b644d5edddb0fd7b549cc5a721ee4d204a5082604a5236e057d996` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` | `03f6cd5ee859d98e6110b2554606ba655ea9b66c` | `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | 0 | `no-finding` | `none` | `none` | 0/0/5/0 | `PASS` | `sha256:6843da58b7928d10bdf522d8051a31fe0fe76e8d2b49c97ba21fdce832bb33a5` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` | `6f1dba05d9dca3e3776da3c7005a83807190ae74` | `0662f0827db1ad2e39f59626dd8d87f316b73421` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:e0f96bde117c0690cc069362ce2a03d44c459606128e7b32687a3671d990a41d` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` | `6d9c8b1bfed15a512d68db494efb71a2d0577f33` | `0b0243e67b4d4635716eb2113f81419da982ba3c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:50d1963d2c6ccf5c7b2d322f626362fa7dbf6eb93f95fbb0a96f45671dfd6b50` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` | `a6ff10d32896ec2d87dad1696b24e07cc73ead65` | `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:fbe10e4fa1261a94cf6957be22c9f104b54b219d1f009ba10e6b5252db3e6cd7` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:0d06dd2d740958cf8705d311795eb0ff0caaead8b32b82855e9120e24484e8ef` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` | `b6e124010b1f74882864bdc3dc1fbd289fd5305c` | `e9e33f66742ae613b738497753ffb4957610b85e` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:46d2edca63646a4cc841d6b24e9a4e69dd59ab462de458984abdc30fcc40a3e2` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` | `a09f2f2ed771008847609d177c72e0b1f62d8084` | `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:d366add9ee96713bdf618b8c61baaf0ea357e6ad9e48ad4a4cf1fa16aea4f216` |
| `R15-old-continuous-preserved` | `9972c0979b118b85b5c9d80a811679b41840910b` | `6e29170cbd7791baf6f74923a50387a9359979e1` | `316e8cd76611658ad9587c73e54cbfb6f3c9f379` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:d3e8855bb582c8ded66a96cd72ab24fbbe39374d663571d1a33e67e9b9d65280` |
| `R15-old-hidden-bytes-restore` | `600ae7430233c349c25bbe4ab0f9f8fb55e7c92e` | `023e0594e4a6d2f3403635decbac7a9d90ec06f0` | `20096f8d2a62bfe7e6990d90b91135ef249879c6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:84c30fc005ea6c743acc575cb4385673ec40b114745279477f19f57db0f2d544` |
| `R15-old-human-binding-restore` | `ed9337d8d288a493c724a71081e4db71972e2e08` | `1d8e4411979ce8ea8dc5697180f8d17be74f1be6` | `fce1db3bfd0846d5af6dcc96b362a52baec376bc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:9380132a7343dc4a6b57f5892f08918e5962efb1efa2ed078c0d8a88477a2ba1` |
| `R15-old-invalid-delete-recreate` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:1631dc67bae2f409e3f48c1a2fb59b00521a0905454661d921acffb0f01623af` |
| `R15-old-valid-delete-recreate` | `d949c6358b9809dbc4c19c55ccc30fab511c7413` | `5f6066d0642c29fbb3414c54445b8ac08d5c99ff` | `de690fe09e6d88d499db4b3ebccdb7dbfb8b5617` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:08362695ac40715ae45b2e737a74a633e9cb64735781513e3a834fa96cf4f8da` |
| `R16-earlier-landed-evidence-reversal` | `e731036f833027f6e32ae9d17deec1f1b3114412` | `f8186fb2af1ae0e23196a4ac0095582433643daa` | `aee42abb66d8ba55343efe6f741c32987563844e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b9e50e5b33a97011cd9f2d4badd264c76751700d928daceec0b91b8f93a29cd9` |
| `R16-pickup-evolution-0-backlog` | `41945ab0488983f425986ec3f815e50e974be318` | `ddee8c3c0a47baed150ff41c81fe3dd3578991e0` | `50ddfeceda267269a756eff178f2e6f2dcde7af7` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:174a9e5a094b4d45c2a310e83ffa860a6e514111867a65b61246c10464d8c805` |
| `R16-pickup-evolution-2-blocked` | `e7e14e5b5790e4682f7609b3ca494fc9fd1e9218` | `97de8555908750bc8bfe4f195811124e6639b33e` | `48a4d96e210ac69ff036bff2bd154d6e496e6a05` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:571c39472582593d73375348bec8099c3230c771e203b0d478244105f21f7cfb` |
| `R16-pickup-evolution-3-in-review` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `66aae1f38225afbdde6a9af1c261223a7505c461` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:3b83f394de1412f403c743cee89140390a4dee945c15f0efe739051e79033f67` |
| `R16-pickup-evolution-3-in-review-drop-artifact` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `04e4cdf6f4c210ea0a27c59ed86f1d01627024c2` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:a3fb361a52f193721c069b0fea548782d82080dac102c22620d04b6b52a2f275` |
| `R16-pickup-evolution-4-done` | `28b720891ddfd4c7291ada824d3d2196cf4a560b` | `da9ebd1326c500e7d2c008fdb80f43be5cf13ff9` | `a8a309c333926cb8144f022c4356736917e5907f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:51f3951c59b254f3f21923623a1302ba370e078a2787f087dd3ea8f8322fbbca` |
| `R16-support-adoption-drift` | `a831384530c69ef834d1d997c25ffb996cfa4bbc` | `be001bade214359024c192e8b06d79229261a4c7` | `ce12604ff0140d20fdda463a6140634b62f35bed` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:f873d7ccda02a3e92331a601d17557ab09e940f52b95dde5ce28bcd48ae7c886` |
| `R16-support-forward` | `8617eee2ba78f3977a9e7e0329159f725633daac` | `4690d1f06ca2513358bd47fc88e8dfdee3a15d71` | `9e15331efb2e68a1762d26fed1df245232a40f2d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:463e6a5f70a1029e61d1922b74d22989c126cf5c7c8763f27b90aeceff995353` |
| `R16-support-invalid-source` | `b5e005e8c934907d6548515f752cba73b79797da` | `8cc15771a0e42ecaa2b04166fdd57589976cb454` | `2c6d7881177ab459839ec9bf195c035cb8faeddf` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:6c97f7ceb0b1bdfc3d2fb9ad69a5c44e949f779c52cfd1a81edbc2ec3f7b9f0a` |
| `R16-support-nested-drop` | `168496fb2f34612a9276eab0151b2b83bf1edd88` | `13967af6be58e3cbea6ee31c6f54f6c39b246626` | `95622f34bd3618ecc561897fe977861d26c1a4c8` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:1d2645112897ac89b2742e617d16662fef24d959318cdbc534708669d53cec2a` |
| `R16-support-permutation-diamond` | `f3d302490bc5c12be93f9392e00071fef0822ffa` | `b82141d042aba0552175891be684c7dd7eccc579` | `04baf28178f9b9b80761050e875ca2f993b4792a` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:c392e5fb81903d974069d590e23cfdebf036774845b345646e4a2208f4ab0207` |
| `R16-support-reverse-drop` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:1025d411c43141268e31fa3ead42546f9b14260a8dc543b77354feee6bc96ad8` |
| `R16-support-reverse-preserved` | `f3b2fb92a748ae2b38142cc01b1542b5302dcdfb` | `1f62604717746cdf35f2f13b4efe8789e9a73118` | `e38824daf72c0fbb9c049b6662fea36ad262f8cd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d63c19f8a9efc73ffbaaa049a6d66642e5b568dfc7566f6d9c9316120b9cb7f6` |
| `R16-support-source-evolution` | `ffc5faa56114e44e8497228192ca4daacd278179` | `91474815e967e29084c0d18638907fe068dfd87e` | `2614fbbda55f0fd12af32872df6361a290c8b12b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:581f2d32cb797ed45bc931563193daa8363ec18d32ef5d7b96efa874b87be683` |
| `R17-carry-absent-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:e6b5c3f6669814fbc5313bb8287102f67d9aca69178b7a3e093383f401250344` |
| `R17-carry-compatible` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `ba001beceb64bc88110a724ad6da2ee3498c8c90` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:27c363e6fcf11ecef59cb03195d7daa1909afd9538547bdb9836fdaca83cbd66` |
| `R17-carry-compatible-reversed` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `b4684c533ad9bfcb5918dfff653a30eda3e53d66` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:88de8ee74d4f01850e380c49625a43e67309aba95583920237ede7c425e02da0` |
| `R17-carry-incompatible` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:d57371615258d8d322c9ccb6741b4a4cc07febf4c46976808da0714e6ddbb504` |
| `R17-carry-outside-duplicate` | `f793332edc8b2cbee979959d560c177365267cb6` | `723fbd86c6180058e653f7b8241401c172a7dd1a` | `0449217881a784a7c4bb1ef1e6b8ed1a5fb781f5` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:56219d9e3eb3df828985f4cfa1ba9f3afebba1918abdfe26f6a512fe2d8149e9` |
| `R17-carry-outside-single` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:e360df7c6458651423cc33c90c8297c0973f368854e2b6faccd8914c112fa43a` |
| `R17-dynamic-support-traversal-exact` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:aca58d400bf944490e6ae091dc68b3a2b64194f7bd649462675eaba786a03fa7` |
| `R17-dynamic-support-traversal-plus-one-refused` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:a2f7f57ff0babb5ba3a8d8b045d34af3e4a6975e36817b8d01dde86b06328faf` |
| `R17-flat-tree-peak-exact` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:7eda6ba7214d5004e135ed611807897565d4a8e2aeda1f22393a72e4edc7e0fe` |
| `R17-flat-tree-peak-plus-one-refused` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:50077a7304edb32a4328077e99e98b0cd62a2d1815ac0732ffeb28241a78a973` |
| `R17-graph-line-peak-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:1d6541c04c9c84b4ae5c69c04bda57ce66b813a6e2bf772031a56d878d34d233` |
| `R17-graph-line-peak-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:2993072fe05784c7b244be2adcd1b78fefe28752ebb8cad3ffd128b0a5554c7d` |
| `R17-graph-output-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:df429465b093c4032426e6868954070169f48b41be9955ac81ac86d66687f055` |
| `R17-graph-output-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:95e9711f62c97b7915084d2e83cc134d046c087b2bbfdf3cf9f07004a8eedf74` |
| `R17-graph-parent-tokens-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:c495bdcf6f32afee3b634ff34baf07c4a0bf287edc75dc839d103e57c26de9d1` |
| `R17-graph-parent-tokens-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:79fbec6f64487b721c1ca476627c17bc4fef87ba7c3a3190595c4edb70eb42fc` |
| `R17-object-payload-peak-exact` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:37635e14c588f7e8f2ec6f7503887c00fd4f8de48c24ad9ccbe6888e6e7b09f9` |
| `R17-object-payload-peak-plus-one-refused` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:922884038226c0f900d373755ce2bea348abe795ea8109404de0eff2ae90b2f5` |
| `R17-outside-C-neutral-parent-valid-restack` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:a5d35690a2d9df83a63bceb6a248d1898e417ae564f4eddaa62a3873e57d3edd` |
| `R17-persisted-outside-duplicate` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `481c03e8e4afa0b3dfe37df8a244bc53823811f4` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:83455828257cecad00d0a9aea15db66567ccfbd60414d39d1e164d3b39d12c9a` |
| `R17-persisted-outside-duplicate-reversed` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `d74cfd74fc6648eb13bb52ad192ee13b4146155e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:30a906c4707391d5b8bf19595c84859f751c1bdbe5c81d6bffcb4524dfd2715a` |
| `R17-persisted-outside-single` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:e454b979f8d60faa166d0332624060e8655587bad654a323e4bc115d667e4ea7` |
| `R17-persisted-outside-single-reversed` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `4a231bb4516e6185d7ade17f5e5cb8aaafcc0613` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:1e7aad8a1128eebda04f2143b33c363ea0606b32675d598e43e1ccd0892f51aa` |
| `R17-persisted-unauthorized-absent-arm` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `c1e4c835d0ece38b56490f0beffef88494aef8a2` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:e5fa5b4748c339e00380d4937938704f4ef40a03360a15737051a6f41dd0d88d` |
| `R17-persisted-unauthorized-absent-arm-reversed` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `6a55c69bf40bfcd9abe33bababdae51ad111eeca` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:d7085b413347f0df05aceb64d432d4c6df3210d5ca6e4ded564290aee27e5dd0` |
| `R17-persisted-valid-absent-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:1aa6ad56a3eb57b113203a635e18110dd96dfc487d7defcb36d9252ea9e19156` |
| `R17-persisted-valid-absent-arm-reversed` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `12f08cf66b77738190f29720044039af1fcc10ec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:2b0b5273a398e3a7ed309a0644a4da4a4ab47cf312007511602c070a55f425a3` |
| `R17-precharge-P22-budget` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:d7102979bd1f64c2d1e5d873b692b73d200f2e4cae24fafa37318c0ed689ced7` |
| `R17-support-serialized-exact` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8048028d3b98a4c6d92d0e96df8b4f31b0eb9d6451c4104d1d32ee5c011bfe93` |
| `R17-support-serialized-plus-one-refused` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:f3668b2bf229a1b80cf3ad9159b609548335f2601190961f0f5d17ce57aeb2fa` |
| `R17-unreadable-outside-C-ancestor-stays-unopened` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:ae2db8a0006342fcb66fb03f71bf835550c4e7147118cef98ca05a4692ab2231` |
| `R17-unreadable-outside-C-boundary` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:fd9d35b74c7a25aae4d44284bf10956f2292da3f1a34308f0313820dbb1dda77` |
| `R17-wide-outside-C-boundary-budget` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:05489d56a44f65a444e22722694af14140c139841df146c964b841e7cacfafc4` |
| `R18-B-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:4c3bdf612e30a5bf1c9d7e8c994f0c0857772bfefcc3fbed61e9976d7a59c063` |
| `R18-B-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:2a13122431e4ebcf2d31c0f90ee5f27a3b35952b72cc62d984057ee14bef8c7d` |
| `R18-B-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:50f45d0a7c210bd38495619c7a2b85e4158ef464302f7b8b61959b3f57f0a0ba` |
| `R18-B-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:8e815833ab0f45de51101c3dc5954a251b58710de19ca7528ab42d81965118e4` |
| `R18-B-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:220f457d3377e4e4777b8352b31c0b3bc88bf645f6298dd5212b4b1c3c2cc7dd` |
| `R18-B-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:62fac7a3c4ecee5aafd3ae57856e50cb2625c7f257b7165bf64e0332fc25c98e` |
| `R18-B-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:1ab2e95379c7c8d0388ccc82bd4f0ce60e2944bb36b80503eb248bfd39f21fe0` |
| `R18-B-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 1 | `blocking-finding` | `ambiguous` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:3b0b5cf6335c1b230c380d81be68c918a9e599b0d6c9fec994e9e69425b06292` |
| `R18-B-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:ac9656791e33f925c33c37a5fdb35ff21c906798926e714b7a497a8424d309d2` |
| `R18-U-O-only-post-C-loss` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9c12ccfb1f02f0d3d7571d00ffdb12c66d82130b` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:6f909f2b6001e9480e28cc09212dd7aed7f005eb9aeba27e5e06f224e16033bb` |
| `R18-U-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:8b5b564ad0e87860dfd8e78b31cf7e28c138a0bfd1f1575d9ff9895b46c4b2d5` |
| `R18-U-claim-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `90e1f0632af49864eb90bb43dfd9d653226f7e29` | `0170b8f74746a2842e91e3d24db2b40794892a6d` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:4a4acbe751042b67471175844a07ea25dd486f125c9a41a9e20c6b0fa965ec0c` |
| `R18-U-delete-recreate-N` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:91734662f7f73d6a5679fd805d90ce496dd82aa0d6f54946c17f60bbb57aab5a` |
| `R18-U-delete-recreate-O` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `32e5e784fb97324e37f759d14a5dac600588b780` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:db8e3a61ba7d6cebd0c82245e696632ede3746496588f0d1697b53872dfba9ae` |
| `R18-U-endpoint-regression` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `fe39fc5d19b39d80c00132f6bb67671afd026024` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:2b0b1e1116f6d77f7e7340966b308a7df5b2815befef72d650054edbfcf24bf3` |
| `R18-U-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:a69d3555072790a3d9337cfe4cb3e464b11c70a98d1bed9c4b2c0648a83dddaf` |
| `R18-U-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:b99c023f99c7735433eae2159aa587a6c1406018e3e8b3f25c1adae127976656` |
| `R18-U-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:2088e9c803ffc30d06e3148b9b581d15f0ad7431fc2be0ee49e47796a143cddd` |
| `R18-U-human-response-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `2574705b088135eb07beb5b710a919626a134e9f` | `8570f09b40724dcdbe220428a2808fd418d9955b` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:ddc52e1373c78942425fb9604272fcc1132992d25bd2d5be953c852ce688b919` |
| `R18-U-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:ef3fe096f1a9a41f2bdaaf7ab4d0cc1dc75fba178d110b2905c6865ff5d47b60` |
| `R18-U-inherited-then-deleted-merge-arm` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `073d6e1d080608961f59d7a9168d96b24fd2e3a5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:a0fa3acd586b10a821ceb71be0b64feadf621d5c2a77c953955be02e7258f75b` |
| `R18-U-multiplicity` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9d0e0b8d05a8ea5f0da83647bec14f62b5edfb67` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:7f5fb4dbda2df6df65fe6350cfef3d3e36ef08ebbfc66835dbf665a1f03cc1a4` |
| `R18-U-neutral-pre-origin-merge` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `57533e22234a2f70d70777040816fd6c436ee9a6` | `b50449c74ca178d7aa31ffe996afadb3563c8ef4` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:c9ce7dadc7ae4643dfa3a54d00cf767334172ca19666c91567580e4d0af9806e` |
| `R18-U-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:92a249d49dbde0e49f26a6165ca856c983101ce7cfef0e23161db5c3a99dd8f7` |
| `R18-U-outside-collision` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `71cedcd8dde74240d0cdd5a0d0e0e43e4819e80e` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:2755303fa610a79446129ca5a314108200a1db876b9b6471a9bd54493fce0d56` |
| `R18-U-parent-order` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `68f00ece3d08a437207e31fea0decedc88ca3a22` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:5d76657166abcfe3cde588b43d6818dbdd15e62d86437d322fbaedc8469b6c83` |
| `R18-U-parent-order-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `f96e171c8daff5cdc0ec7af626eb222af3c4f2bb` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:570f5e73906c29aaa132cb02ef36dba8963aa6c8189a0fb23e43fc3bba2407ad` |
| `R18-U-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:b0219963f625e3fb6d8ed7f3f939353b55bab970bfef1b61f2bc26c8a201dade` |
| `R18-U-review-binding-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `b4203751e312d0423e9b046c2363e2f638ecdeb2` | `9ee8ac72a1862689c5199828a56b8a83a26a8a26` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/5/0 | `PASS` | `sha256:403541d965a4da290a31f1661453395a75557b6ad2c093319c5bfe0e32f31a30` |
| `R18-U-review-compatible-merge` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `85e0328be42a0ecc304640ea8be0bae4272633f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:f08ebf0b3dd0aef5a64f2abdb6e16da6f8f9410eb9aa740b1f13028deb1e60da` |
| `R18-U-review-compatible-merge-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `d7dc0b370d32259f32a188728ba05b599651a4f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:1bd286c8a7b54882318893282cddcf2e760ea7ce933113c24d2298794724d8c6` |
| `R18-U-review-compatible-source-high` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `85e0328be42a0ecc304640ea8be0bae4272633f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:08972c29c494c2d9a808b6cd7d42b6fd3198256e334d610fac953e6dce958f74` |
| `R18-U-review-compatible-source-high-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `d7dc0b370d32259f32a188728ba05b599651a4f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:98aae892f378e8ffd57e2d32993cc3d28ea967be9e7cdd4d9d10622bfdced411` |
| `R18-U-review-compatible-source-low` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `4f95dd0b5c539e966be5556fc9bdf9f0a3e6f28f` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:8bb5eae70792a0ab1828c1d3088d533c6ab7ccedf47ad0230a2703e960610cb7` |
| `R18-U-review-compatible-source-low-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `eb0fa8a1f62aaf79a97d3e15c3a1eba9a0a1c0c8` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:67d9eedb7bd18eb501f44be9ffa928995d3a5735d542b6ad44047089145362ba` |
| `R18-U-review-duplicate-parent-header` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `25abcada854ffc68d1f6194a349bb5af6bffadf8` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:01b931be2d2a0e879b8cfba94ea7121aa4e33c236ed3bb3ec38e886882cac737` |
| `R18-U-review-incompatible-carrier` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `064c8ecc54d3eda1a5749b93e4fc8c85f093aa4a` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:1c12bc53500fcb7151cadee2c26071a545843a2be67e4ad908f7cf695b45321f` |
| `R18-U-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:4e45f5076cf749a2e3bb99ff27090494956ce7f8412d2cf63b3c2319773d71b4` |
| `R18-U-review-three-carrying-parents` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `efd5d8b85cb409e8b7615e15d6eda9df0e0db231` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/6/0 | `PASS` | `sha256:afba7d77b17b2bbd79ef675396e5dc0390d535cb683f51886cf6fba702ab27b9` |
| `R18-U-review-two-valid-sources` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `4693117002177ee117d6f88392b31c99fd3845a5` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/6/0 | `PASS` | `sha256:b5c7d960b5e37054e1f9f2aea51b2ace7c3e043a7bb87d012dac05322c207ca4` |
| `R18-U-schema-invalid-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `ae5b882d624ac753ab179bca502e1d470f7cdf23` | `87ffc4416aee8aee8c2adca7eff692b471c5de4a` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:dea556eed32cc2555025f8c2da38fa44cc19aecd6ddf8e72cc8e4c470c4b9548` |
| `R18-U-second-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `baa0995a63d5d5f4fa418cdf7f79b274c9e90272` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:8aa1f81317f1ca9690951ebb44a26dbc317d0d3b765cbd6a6de6912fc77aa5a0` |
| `R18-U-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:ff664d000d2589bb57afba4da42ed40169fd75d2e57071e0969c3b86a6bb92cc` |
| `R18-U-transient-protected-mutation` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4a58c18ccdc13f072d74f6b134ad76b98f28463c` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:763adfc6636e58c297e82ab3f4c58d48ca7e5b0e7efea92b2dc64ab59e192f57` |
| `R18-U-unreadable-object` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `a04f20486b2958f99aa41dcf8590989d70bdbc9d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:6ca5af87fc0c978e53b4379e005a7a7ecb4a0d1d4747a9d10698244f50cf5d25` |
| `R18-origin-arm-nodes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:b247add13ca0ad1aa2310aa265d11b6c531ff35d8464c75d2d36416e1383444a` |
| `R18-origin-arm-nodes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:d7ee79235394eb3c464bab591fd31e7e8a0d9ef57b0e94bda6a57cd9e7c41343` |
| `R18-origin-parent-edges-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:def2a19ed399d93663e56fd16d1487f3d2445367de5fdd745a43914344ee2d52` |
| `R18-origin-parent-edges-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:5e09ee5be10179c041843f87e20e2540f1e6253b6b9b793d22589f48780cd89d` |
| `R18-origin-witness-bytes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:aca29de1bee3fd4b0884dca75f5e302e8b3519c0d0eb6a2e12f94e0c886ebf42` |
| `R18-origin-witness-bytes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:a1e4636e672204a1c346bd53c30dfb34081687b663f60acebc400af130906828` |
| `R19-WF-local-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:5a0342ed932e13b788c12214a413f9f78567abb4d4d81ed34b59612f985f14e7` |
| `R19-WF-local-missing-old` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:52bb5948f95d5aacef4cc6ccc22bbd17e4fe779d1f11d5d8a6267e9c3dfde143` |
| `R19-WF-local-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:dd13300b0a921e63b28e1c7994bf3ac1b265e1bc86ef0f7920c72c4317ecae08` |
| `R19-WF-pre-push-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:fdf5690b21ca98579e5f9a35eb650ddc99bbfd61c0a3b7c2b5f35ae584698158` |
| `R19-WF-pre-push-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:a4ac390924b2ec61f3b4ce13f7108446312e19095e117d7400ac9d8c481f12e9` |
| `R19-WF-pull-request-synchronize-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:8a92a3e65ab79b4a0122dc4955f5416c89107356266df11b9925b6b9b46f89e9` |
| `R19-WF-pull-request-synchronize-head-mismatch` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:b7f82e49f3e02a88562f4ecbfbd66f7608797dd8845631a6771e6b9b9b3156df` |
| `R19-WF-pull-request-synchronize-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:a73c55a7c9e314c5fc799240b50d6e314733e163e7b915be16bf128a81f5da40` |
| `R19-WF-push-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:37b0127e2dfaa41d1cd4cc442f8a4411eafe6d08b32fa857914987eaad3478a9` |
| `R19-WF-push-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:af51fdf7af40361bca2e451d9e048ef839122df68d335de4eae628b65e7aec4f` |
| `R19-WF-push-zero-before` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:f6958589ad6fc29fa93333a57d56d3fe171485c0ad509926ceaf51791e150fe7` |
| `R3-01-two-invalid-causal-sources` | `73373ac5106e43d8643b5b616268d77a5ca1d264` | `8f89d0fc4c063c0bbabb284434f74bcf244fb5d3` | `8ed846d60715d845a5e19ab6b299ce853a592614` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:d92753499771022530fa40350db0dd797149b35a2c7fae3359f42a58c4a22949` |
| `R3-02-invalid-valid-causal-competition` | `16722b83a642e40f2157c752a07adffddfaa709d` | `35e767d91f32b96f8f8308b431b5c6a0b35be23f` | `ff42531aadc6ffa000560bc56d995993ffa8e62c` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/2/1/1 | `PASS` | `sha256:b3ac0f2d9963cc1a2a94d7586d5fe038074c8f467ffa5068caa56d1f93238f89` |
| `R3-03-valid-supplier-plus-invalid-parent-at-N-blocks` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:57ea9f8bed74a5a06115778d3aff6fd65af2d2a58cff4d59eab59bfece423afa` |
| `R4-01-same-root-valid-diamond` | `4e831314d34c2897a072cca5b58303d8fd0e7ddd` | `2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e` | `a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:7661192c0703c77014f8471941e2b7da36ce3aeb8a733bff4e15da561d931a6a` |
| `R4-02-distinct-valid-root-diamond` | `10965dc1169826888c7d66e2389f9f90787c0064` | `286e35141edc20fad35f8b0d4aeb4930c403d038` | `37a75ca4c96e8966c19fa18afe6b6f9b1e4c10d7` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:be8fbcd3c5c0c2ebb97f44519d88b1c6b9cd40362a197a334a21f88772ef6e61` |
| `R4-03-equal-root-plus-invalid-diamond` | `90e37b9adc7b3b428f2963282519639354bd2b56` | `de44aaea6c73d11ca46c2255f39f9b9a3d10d36e` | `3c9778ae10bc7a945bb59ad802db12bd6803ea64` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/1 | `PASS` | `sha256:fcfa43d8633dac14ebdfb53f67e309a84eedee5302b91bc970608fa23ff8d4d8` |
| `R5-01-invalid-redelete-after-supplier-reintroduction` | `1e5dad973b3278ca8c12f3dd74f72250eaaf9f09` | `c63664276a141f3f60f61c9d404de201e6f8cf16` | `d40a531fd9a0dacb986f9259ac6f94ec0d248faa` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:6638975c1b9f270b1a6d5bde07ef81b7afc177b882b7f577fd279ccba6af5189` |
| `R5-02-valid-redelete-after-supplier-reintroduction` | `79b338b3ef54382a0ec95e87a7ba962b1ec7c20a` | `9c8b1418effb6889d14466e278a7987b7e7cfbc3` | `fb0bff9778f436aed2a46f887eafb84e1c74ea5f` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:92ab0460a0d4642b43b92a8885d77c5736b6bcb6986691f25c24fa141a100296` |
| `R6-01-valid-plus-invalid-all-absent` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:6a2a06a3e72cbaf6c7ecc30bb44d12af1d3724b1938b246ceb6b8de432552204` |
| `R6-02-valid-plus-ambiguous-all-absent` | `f61617485ff0160e37de559fe752c56ff3bcb5f7` | `10a37a2bc559519d6d84f70850b0a78445c3d5ec` | `4ab46009954bb98c5f22629274722667dc21ca37` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:01adac5c954eb3d6b58d9ae1a9ded269e293351b9971b6493e794ae5d8cee333` |
| `R6-03-two-invalid-all-absent` | `f5141f92b29541282cf1ec520470e8c604aeaa6b` | `eb354df4fb54776834a9dff53f51f496a2bb338f` | `8f769727f1c641bd2587115f2fbcda5fdda816d1` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:9e148ff4c1fe85725709324be1e051b79b81e74f3b714addadb97b8b619f6d99` |
| `R6-04-same-valid-root-all-absent-wrappers` | `c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59` | `c3b9fb54026383a350146fb2f25243c9e8c7cb01` | `7bf74330f432155c3c39eedbfc81fa72bface489` | 0 | `no-finding` | `valid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:865839edb58db67693a540ae9a8cecbb6047baab7de9fcbbf8f286535e86b9fa` |
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` | `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` | `cb29049ff107a9a11a4ec7babbdee21819518dd6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:be1e23284b4a1e8eaa21b62eefdb314f5dc18a119bcec1df8e7e2ebf008c8566` |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` | `b3879039d6d7168e89b3046e6e60e056460907c1` | `2c2289035cfc91c73564f6a97b326ebca02be132` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:d3de3e017e5618f1e317d976bac398e73fea75adb6ec5739830fc8948c2f057f` |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` | `e3c594800cfe94f4f23c58060ae4ab31f50c078c` | `dc70864ec5e13a399d4966356b9803075681a0e6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:d56edcb0c61d134fa35e1d6033c77a05bd524e19b700b0c1309e136ab24a6ac6` |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` | `a3f97a3b22945e663eb10180bde5de3b7bf790fa` | `b2dbe65f89982fb586b0fb5349454d80c7c53310` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:9740e17f372cb9828378ccf5a3b75c240cfa7e686ef27c3ce8e56fb5b40c3c4e` |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:57d7fda2fe4a51c4b082208dc50116fa223b9b791e275cbe45e8c3aaa11a20f2` |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` | `27927fe11bdeee043660e700c81e8cb3853c56bf` | `1fb9fc40da2d44e839830611cc20d0aee23c560e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/0 | `PASS` | `sha256:f905471905a2a52149b414ca142014aa47456a2f06ee3238f3d2dcfdc9d5df4a` |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` | `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` | `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:07aa8479fde9df9c38c81b84426add5874431c0a187399afdfb8ea4463650421` |
| `R9-direct-review-revision-pending-fill` | `00ce8c4f203a14c87a9955fece2645744ab2222a` | `6da769be2398ce26c45d3dba7845e0d6bcdc07fc` | `f5e8ec93ded434c47e27f345c1e38da95297f7be` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:1a4dcbbd186552bd36a5a52233cb6bd8600a07cd15f84478ec4a67d578f18a00` |
| `R9-direct-review-target-pending-fill` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:8749640fe2702262eb52391225a0fcdde2e22e48a08ce5cd89282bd925e98038` |
| `R9-supplier-review-revision-pending-fill` | `eef4459d2337688dab6f6681415a6f5c57cca6b8` | `9bec712c0e2453a881aa8fd36ff89d8887e07942` | `26d16dfc1e390a11c674ccbcf8281d212a19544b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:47f73a58d01a25da642937fefc982ca13f9df82af7d9f1087b9c508737674c1d` |
| `R9-supplier-review-target-pending-fill` | `8cc94bd588fa82e6bf7fa0258a7f4a3b96453d75` | `648b5b5515d697600fab0a9aa087a1f63bddad3d` | `64affcee2fe535a4f21aa80e72df2131349dda62` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:3c9f1ad641265cc1303a9176491f2872318a7e57317e571adbe9eb0033d79d88` |
| `W0-fast-forward-return` | `b614e3dd70da804a078bde5088d38ac9de511846` | `b614e3dd70da804a078bde5088d38ac9de511846` | `2fce4585d497e94f48f6807dd3cd9fd7b432b264` | 0 | `no-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:2b339b90787855dd6e5ca520d18a201cdb952390d0770738dc55354502779291` |
| `W1-pre-PR-push-exact-endpoints` | `2fb10d8c39b965cafdeb5e496e351ab258f75960` | `365339838cdfc9d6579ac21478fec9b776742c27` | `1cc139111382dea68cae0208e17354f6f75c5bad` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:eeb8febd3f4f96a9ea45e014da41df7019611d881da624139100e2ef50b9391f` |
| `W2-base-advance-retarget-invariant` | `1e1e59bc5493dd584372acb3da94233d867bbed0` | `a6363187edd2b2ae4cac6d24e0bc6d4d9adfb836` | `1c48ddcef1c77fdc65609d2a077ef3cb40396393` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:0a654b277ae1d9225a42e1971fba51183cd58d35ec68f944ca3c47e7a2bca2e7` |
| `W3-multiple-PR-API-zero-calls` | `7f7a2d473d3bb95a7879b5ff2c26195a4b730e1e` | `b32b24f6a4b08d17c073bfdc2355521efbcbcf58` | `56238e170cdc0358979e2cbefc7af6cbf89b279b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:b7b981b36a5d3df2e560bb98f6fe2da0a40d0954c35e2c1f08094f6020b4842a` |
| `W4-stale-rerun-exact-inputs` | `b5c4bd355d0c9fb9279be13d67268628652addc1` | `842d19ca481aa76dfcdcf096af4c550e826d9569` | `6046485394ff351e5cbecdd5c5503c44a821af8c` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3483a91a27c7326dcffeb4ef03c00167eb45cafbcf929acdb420526b9a9a7734` |
| `W5-missing-O-coverage-unavailable` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `4923d6cd62a6ccd426bd569cc06323a11f775bc4` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:7b5d104c46e982bfc3a4f3f26c920872ba3614a2d6bd6e5d6b146d2917771a11` |
| `W6-created-deleted-zero-endpoints` | `fb590466fe387afa4f25743982c78e281f34f36e` | `2df4b3d62821abe8ea3f482b931ed91d256d24a9` | `1f3aa42d8428e4dd3b8b98220355e0bf883c318d` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:ccd04bbff7014612b4827489416dd00670b1a2fd9be79463b21ff8e21e4b375c` |
| `W7-PR-synchronize-top-level-endpoints` | `99342d9672d3f50559eccba1fc16eb8710b7b476` | `55bd0ff6ffe71dcae7a1afbfa440b021bf972dec` | `5a612247b54e551764fbf258e44893a0f5c40dde` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:657eea8129ca15b347362bfda30bbbcd7f713651c217472f6edbcd4e48bcb611` |

A/P/U/S means authority, propagation, persisted mutation, and supplier-support checks.

## Executable S aliases

| Alias | Maps to | Classification | Evidence | Mode | Authority | Invalid authority | Propagation | Status | Record SHA-256 |
|---|---|---|---|---|---:|---:|---:|---|---|
| `S1` | `P1-direct-linear-valid` | `no-finding` | `valid` | `direct` | 1 | 0 | 0 | `PASS` | `sha256:fef7c69b2733ef9300eb8a94c5402f06644504c1630441cd8bc5f6ae421c57e0` |
| `S12` | `P12-merge-supplier-valid` | `no-finding` | `valid` | `supplier` | 1 | 0 | 1 | `PASS` | `sha256:adb7c8e1467d16f5adb49e5287cc1393850094f70ea67894484b9ad98e6ac8f9` |
| `S2` | `P2-direct-linear-invalid` | `blocking-finding` | `invalid` | `direct` | 1 | 1 | 0 | `PASS` | `sha256:88ba94fa4ccea046af31fca874581f9a7cffa7f52de5f67e6a8d799ef6e05268` |
| `S3` | `P3-genuine-old-loss` | `blocking-finding` | `none` | `none` | 0 | 0 | 0 | `PASS` | `sha256:55e72e86cc683168757a7da62a39580e628f3a5af4662244e3715d24e458c397` |

## Damaged-mode controls

| Control | C | O | N | Baseline | Damaged | Status | Record SHA-256 |
|---|---|---|---|---|---|---|---|
| `broad-review-pending-normalization` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:292e6c32afeb9ca638d3bad9cd4a9596302eee6456662ce51f51bf84a31df86d` |
| `buffered-graph-output` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:4076adca6645e7afdbbc0cd09df9cfdf73c8396d8a6f9475346170a5608ad5d0` |
| `endpoint-only-origin-equality` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4a58c18ccdc13f072d74f6b134ad76b98f28463c` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:c4e33f3dab8b3dc1ad85cf9cb33ceea7717c5017d1ca85ce2cedb4aa6f3caa4e` |
| `event-adapter-cli-entrypoint` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `three-exit-adapter-contract` | `ambient-or-shared-session-boundary` | `OBSERVED_RED` | `sha256:ef198b3e836b4d68df5067c20c8756cddee8129f92eb69efb26dec8f18dbf0da` |
| `first-parent-carry-proof` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c6b273cd04dcb4b4d17e60a3c3913f929ff3342d72b92ccfacd964f07d8f74e` |
| `identity-multiplicity-collapsed-to-set` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7e6e7b7646ca1bcd1821ef3fd920528858c6a8e435eb04b5ff975ff4ebd20ccc` |
| `ignore-absent-C-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:f9a91f587c7790cdfdcd77cd3f389ea8fe9a54a4a27ce0f51af4d4809e75e3a4` |
| `ignore-invalid-N-root` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:017dfcee6a829874ad3c86a4868e42d8d4108579c771a8d838ab1f5c2e9c0fb9` |
| `ignore-outside-C-carrier` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3b56c222946112d1313e27f2259fa322b9f6715328bcbc5a67038eccb63181a8` |
| `ignore-persisted-absent-C-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:b5a60b9898d9fabd6d22870af82214ea6692dc94c68f297735bc18d994a3e4ff` |
| `ignore-persisted-outside-C-collision` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:db79757d9c07fd27faa50b16aad799d190bc584e23a910badd7c2aed36f19100` |
| `leak-object-database-pipes` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `closed-descriptors` | `leaked-descriptors` | `OBSERVED_RED` | `sha256:20044b448140a57d50da0e36f3ef823d819205a28644808f55a0492749cebe65` |
| `literal-review-pending-treated-concrete` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:13d112385cf15c651e998e536dc1094018aa7eed5bcb3a8e7462bcbbbda7a5eb` |
| `locale-git-error-stream-equality` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `unreadable` | `unreadable` | `OBSERVED_RED` | `sha256:5c034618ea0b830c69aa5591031431f90a390b243a064353150941fb215c4cf9` |
| `missing-all-parent-direct-validation` | `d7dc739a275601572c26fadc522a2ae4b71d3b12` | `ff1d9fce8cf6d941f7e0210a9cc6b3380df94741` | `bd005f27951b3bae6225e8cc736936db93667388` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a71ef07baa481ad097d61471eb45665ceb58881ef0384a019692ee0ce15b4493` |
| `missing-post-event-continuity` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:84f5b3d73899c5a20ffd97d5252f388df00d154afd64a4aa9c5f049befdb76a1` |
| `omit-old-tip-human-binding` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ef4a25a4aabc01d7d532866e6426b0e835bb764ddba91dee3bb799907a9d4ecf` |
| `omit-supplier-carrier-human-binding` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7ddbab84dee6c41351e232629529ef9126fe57025c9ef664213926ed748ccdd4` |
| `omit-unanswered-published-review-binding` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:58344243b4503b74ca823588324cfb10c725a5cc25ad5dca23f7469369210de8` |
| `posthoc-budget-accounting` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:38af161b12f5105311c479dd96968cbe19104c1c1dfa32045f1494e38bd95c36` |
| `reject-all-origin-invalid-carriers` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `85e0328be42a0ecc304640ea8be0bae4272633f2` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:9a03a2d7025afc2b87426de2c0c5ad98fe841415e5dbf8d646ad85afb70ad6d0` |
| `reopen-outside-C-boundary-ancestry` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | `no-finding` | `unreadable` | `OBSERVED_RED` | `sha256:157181b097f4d2be8cab789883086861525fd654134a838a42f564e262280b66` |
| `reopen-pre-C-genealogy` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:a009eb9b4b50291d7cd9be8722192ad2e66090801ed093a14cf27e9469b3bb8a` |
| `restore-universal-ancestor-carry-scan` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:af433f685f3710f1c9a8c5488bf5581df374b7c6aad0a536cf9c5ea5a500d04b` |
| `skip-carry-compatibility` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:227154600e109348a3d6c0b1514e54872effddc9be1f7ba0ebc66880909d3abb` |
| `skip-old-side-continuity` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3a19d4f3b7d4ca1f109fd58c85b6365eb5dbf9e21bce3aa3e1a72dad161fa73b` |
| `skip-origin-birth-uniqueness` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `baa0995a63d5d5f4fa418cdf7f79b274c9e90272` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:46780c4c26bec93c6a347d55679fcb32a5ae31d34428a7c9ad83237a52550e4e` |
| `skip-origin-endpoint-non-regression` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `fe39fc5d19b39d80c00132f6bb67671afd026024` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:f6e7a02312c7093efc66413539e01068febd09b540962072208eed4f52c6efae` |
| `skip-origin-post-birth-absence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `073d6e1d080608961f59d7a9168d96b24fd2e3a5` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:954f795b2f02f50085ce51ab93ac853cdc41dc4b1f1e5d419febc64a33ebfc54` |
| `skip-persisted-candidate-continuity` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:be25c6d46778bb2ae7c7c41984f17f94a41335ee62bb08a48d93186be9bb87c4` |
| `skip-persisted-frozen-skeleton` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c4193947ee5457b221c3f7e0e7d097120e8494f9b663f5ac88cc3954bce035d` |
| `skip-preserved-state-validation` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:24c70098bf6f1ac8767098bddbd3a29314b6564ca96b3a8e10349b51bbdc5bf6` |
| `skip-supplier-support-certificate` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:d1b258a1c702f816d164f26803f921934c2eb2c94f103ac281f1e9a16401c1f3` |
| `sole-valid-ignores-invalid-root` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:abe626b443dd6abfc3904501eb9a699340e2377c88e2e62540220fce7a8e0260` |
| `stream-malformed-truncated-final-line` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `unreadable` | `partial-graph` | `OBSERVED_RED` | `sha256:aba7670b099f934d10428ca9fe8e7753c3ae65888527b5275e4f0f1fb3b2517d` |
| `supplier-authority-borrowing` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` | `41865c9def0f066b1d121b9882872ecf33bfe729` | `8579708e09425d6c4e09b9260991148f8ef3ed6b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bd0477934aca03ca18ec5300fa3db3dc5bbf310cffa7086a8776de47f5d55e74` |
| `unmetered-cone-work` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ea953cb9245f335c1cd2072547c6b5dd1dfe9e20a81dca51eca277d874d4e03a` |
| `unmetered-dynamic-support` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bbcb82db16c13abaf88b2d0a0afc2aa345235c7926a1add086de0f8090fecc4e` |
| `unmetered-object-payload` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a4ff94c668bdd9f7a2198acfc060c16e161a4f9946f348cbe50c67d058d5675d` |
| `unmetered-support-construction` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:33adcbb8dc7c85beb53db6beeed2f4fa65a3aa7b9250cd8bf893678e78507f3e` |
| `unmetered-tree-paths` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:23e8841c4f18d00df03a75b99c583f4926abcdfff4c72a7f959185b030dbe329` |

## Measured cost and object recovery

P22 measured 133 graph commits and 16 disappeared actions with exactly 1 POC graph enumeration, 0 POC-owned per-action history walks, 10973 snapshot requests, 10970 snapshot-cache hits, 135 precharged Git spawn attempts, and 135 actual Git processes.
The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.
PCX-20a passes at its exact measured maximum 5645 with limit 5645; PCX-20b exits 2 with zero partial results when measured maximum 6102 exceeds limit 6101 by one.
R17-precharge-P22-budget charges before work and aborts on `measured work budget exceeded: object_reads=134>133` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.
The 64-parent boundary case stops at parent token 8 against limit 7 after 2870 of 2952 raw bytes; the graph child is reaped and no graph is published.
The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, 2,920 serialized certificate bytes, five origin-arm nodes, three origin parent edges, and 1,042 canonical birth-witness bytes.

PCX-19 is replay-bound by `sha256:95812f65a03b9717a9455f1dcaefdeb68fa4b4d738cc8e4bf0d37a027f10eddd`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.

## Reproducible audit

Use two fresh, empty scratch roots:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r25-v12-seed1 > /tmp/production-contract-r25-v12-seed1.jsonl
PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --reverse-construction --fixtures-dir /tmp/production-contract-r25-v12-seed777 > /tmp/production-contract-r25-v12-seed777.jsonl
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r25-v12-seed1.jsonl --compare /tmp/production-contract-r25-v12-seed777.jsonl
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r25-v12-seed1.jsonl --damage-test
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r25-v12-seed1.jsonl --compare /tmp/production-contract-r25-v12-seed777.jsonl --generate
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --event-kind push --event-payload /path/to/event.json
python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py
python3 automation/run_tests.py
python3 automation/reconcile/reconcile.py --check
```

The auditor requires a fresh internal replay and raw byte equality before generation, rejects
duplicate keys/IDs, enforces a static recursive raw key/list/type grammar
before projection, compares a fresh
manifest byte-for-byte, and regenerates this README in full. Its damage
matrix covers invented/duplicate/missing rows, same-region OID swaps, tuple
relabels, false verdicts/counters, contradictory transcripts/digests,
unknown raw fields/cost rows, locale error drift, post-hoc or unmetered runtime work,
noncanonical ordering, BOM, CRLF, and missing newline.

## Nonclaims and integration gates

- This executable comparison is not production-ready and does not authorize production integration.
- This POC changes no production reconciler, restack adapter, workflow input, schema, task, queue, memory, or history record.
- A post-push check can only be advisory; prevention requires a pre-push or server-side production gate.
- Strategy U accepts only typed legal live-incarnation births and does not prove squash, replay, or cherry-pick provenance; a squash that creates claimed or answered state at birth is illegal, and deletion-only resolution provenance remains unsupported and blocks.
- No candidate-base or provider base field participates in attribution.
- Fork/pre-PR transport without a trusted old O is coverage-unavailable; no reflog guess is permitted.
- Local pre-push uses remote old/local new; an offline wrapper must capture O before rewriting.
- Certificates intentionally overbind non-action authority delta and referenced paths until production exposes a validator-owned support receipt.
- Review successor/reask and boundary-review supplier leaves fail closed rather than simulate semantics.
- The one-pass claim excludes imported production parent queries; production integration must cache/eliminate them.
- Uncatchable process termination and native failure inside a resource-creating syscall are outside this Python POC; Python-level `KeyboardInterrupt`/`SystemExit` after resource return is covered by pre-bytecode ownership publication.
- Hostile replacement of the artifact parent directory inode during publication is excluded until every pathname operation is dirfd-relative.
- PCX-21/22 remain production-integration gates, not isolated-POC completion claims.

## Tests not represented by this artifact

This artifact does not claim deployment, a real remote push, production
adapter wiring, server enforcement, or unsupported review-successor coverage.
