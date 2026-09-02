# Production-contract provenance POC

This file is generated in full by `audit_readme.py` from the closed
`evidence.json` manifest. Do not edit observations here by hand.

## Result

The real-Git self-test passed 229/229 scenarios, 4/4 executable aliases, and 41/41 damaged-mode controls.
It imports and calls the worktree's actual `queue_action_identity` and
`queue_deletion_problem`, and `queue_mutation_problem`; it never invents
an Action-ID or lifecycle verdict.

Canonical evidence artifact: `sha256:891830d2d5445dd537bffa24d3cc43387cfd6f7c866fb5cce88621118ef99487`.
Canonical semantic stream: `sha256:4df77ffd33059f4f763e7fcc077966ddb50c024d29040f4bde0321c5741199f8`.
The raw JSONL stream is ephemeral and has no stored hash claim.
Evidence schemas v2 at commit `0b80c342feb310d73de6564aab2224a899f42486`, v3 at commit `7f4a1ffacd1cf8163f597daa186f801e9ce06a3a`, v4 at commit `cce76a037f1584ff7d37048cb4411bdf0f5aa907`, v5 at commit `d12b799a2fa27b05a5ee2af1b422131856296b41`, v6 at commit `9ab61c416be1911e44c6bce2b3d711b6f2abef15`, and v7 at commit `820ae1a788f5b24493a4277fb4d79981e0be202f` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `agentfold-production-contract-evidence/v8`.
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
values fail closed with zero transaction entries and zero Git children.

The stable executable adapter entrypoint is
`prototype.py --repo ROOT --event-kind KIND --event-payload EVENT.json`.
Exits 0, 1, and 2 mean clean, blocking, and coverage-unavailable. Importers
use `event_endpoints(event_kind, payload)` and typed-U-only
`audit_event(root, event_kind, payload, *, budget_limit=None, transaction=None)`.
A valid event calls the optional transaction seam once around
the complete Git-backed audit, so an external evaluator charges every Git
child; invalid publication calls it zero times. The caller receives neither
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
damage probes preserve output sentinels. Both output files are staged and fsynced
before namespace publication; an ordinary late second-replace failure restores
the old pair. Portable filesystems cannot atomically exchange two paths, so an
unreported process or machine crash between the two replacements remains the
explicit crash boundary; this is namespace rollback, not a durability claim.

The object database closes stdin and stdout on success, abort, an already-exited
child, and a stubborn child that requires timeout then kill. Even an unproved
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

The exact reviewer DAG is clean and record-bound by `sha256:e325bb06c373dcff66b443f887ea975d5c6a408ba2d658fdceae10ee0dcf22de`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.
R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `sha256:1a558b67902392847d2ae99c8139c937b49197b16e38ec8f12f64ac478ee1035`.
The hidden-G attacker is clean at exit 0 and record-bound by `sha256:c851684f1e49bd6f2b62dafbab19245c87afd940293b05baebfcc8dfb3554700`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.
R6-02 is explicitly dispositioned clean and record-bound by `sha256:3f93f91e1f059b1c83ba39a509dca223de64159ac2b0c0d1a80f8f82b0292d0d` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.
All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.
The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `sha256:0a42c57841f769d0aaec23e6ab7dc4c49913f16b32a03ad5c2763ecefe3a5e08`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.
The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at 4, freezes later counters, and is record-bound by `sha256:8e413604004e8854c45dba14af04af05a03ee1ff09c2ef5ba7a3bb1af3ead707`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.
Ten runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, certificate serialization, origin-arm nodes/parent edges, and canonical birth-witness bytes. Every +1 refusal exits 2 with zero partial results; graph reads peak at 256 bytes per chunk and publish nothing on refusal. P22 separately observes exactly 129 imported production parent queries and 135 Git processes.
Unreadable Git objects use the stable typed reason `missing-or-malformed-commit:b5fcd8d0260da07b741462af3e3e2b49b546d600`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.
Before any projection or digest, all 273 raw rows must match the static recursive key/list/type grammar catalog `sha256:d9162ac4be0fb42ec45eb89f0c6078d0b0f9f2cdf24a604855d3e5680ccc971f`; an unknown top-level or nested field exits 1.
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
| `docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py` | 254087 | `sha256:8144a30dc8e5186ba7674a33b9cea4c92229eb9e07210ba4b7bdf9acb89872f2` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py` | 542217 | `sha256:d60dab01cbaec52d267a1dbf1d4d3a4916d21847261a4386e7fbf3c7804fa32a` |
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
| `P1-direct-linear-valid` | `46109f507dba3eeb6191db457fc7848c415e8979` | `2819957948197a593fb1d0dc966e747c44db9ee5` | `029be55decf7d7f65826f86684cc8605d5d47b18` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:19de19f09f3402ca1f502b6498aeb46fbf4bc78246debf20bb7aea7853a2722d` |
| `P10-direct-invalid-parent` | `2ef716a2345dffac470956041b5245e20fbc8f98` | `1ac818d6b6ce87da87358e55015671ecf823dbb5` | `8f7e8c69c7ec6e4af250366114c90ecc24ce811d` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:83ce3acdfcf36a77730dd606b7222054f699125e1db1530f7104e92fafddf195` |
| `P11-direct-three-parent-valid` | `78ad042cef55f824658b367d8599c5523b4e601d` | `b5726dd5f1e717518fae85cf820fc7b134db83fc` | `ad16f6d1f31e155a41a236d51a7a396e54dd5ea3` | 0 | `no-finding` | `valid` | `direct` | 3/0/1/0 | `PASS` | `sha256:cd42739e043ee292ebadc0f244af11462f3b7c0ab99a0722e2db1d3efa44aee1` |
| `P12-merge-supplier-valid` | `3a01d100e676a9a20f8dc545fed19be3419fb759` | `bc433c8ed8cda37d3813042f730b2f23d8e8d778` | `8dc6dbc10535cb058ee49c63a979d75966b7f248` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:da372dac178ed29d3bdab3a9d44fe3c80f9400ecd7fe20823c6c18abcb53e7e0` |
| `P13-merge-supplier-invalid` | `c9de2e4ee2e285093b2b1ae42b597989f5e2c267` | `898789857318c82970d920a105ee1a124474e155` | `9424f0b01381a9388d58b77c06efec9a59f0249f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:8517251c72375bc046d570e053470daa21ede14f3a890a02415228a9d4334f5a` |
| `P14-supplier-reintroduced` | `f340f1d750e747d6cf6a74dfac05146fd208f964` | `bf8487fe5085a4dc4b483f512c51ecd10cf7c253` | `14d300ed67dece9c599e5c0d096b708cc38bafa6` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:3518c69f53ed44ddc3fcbc6e9b8bd5493657ed1b112c51bc4ec285540861f3cf` |
| `P15-competing-suppliers` | `80b72ef13352057aa74028971730fbfb266b56f9` | `20a4f077a613c17b6e3f36d87f807bed9395d541` | `fe575f3eecc1f2b034bcbeb17a0021fce16bb82f` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/1/1/0 | `PASS` | `sha256:e469fac88f61df4b481f205af7bcf4d931e65e0f21bf077bddac969eaa6574ec` |
| `P16-PCX-08-invalid-supplier-claimed-carrier` | `b76e3dd3be1c4896d95f0ade31b63eada3ec7002` | `b756376fce02251f8036c1b1560d8c6c96dd0699` | `b23ca400da3968f74afc3b950ff4d4eb27307196` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:983913a8e2eeab74af0def4c6867e7abb5bfe2a4f395190037fd70c1b052c56e` |
| `P17-post-event-reintroduction` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:8bc0c311630d9e5e48acf8998ae0588c1b6347362c35f28a1999cc52ac39e165` |
| `P18a-missing-tip` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `907f5d5221680a4ff7eccd647bcf26bcd5e9c4d5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:633516b93709c0b78da587b899446c74a169399935899acf5fbcd3ebcfaecdfa` |
| `P18b-noncommit-tip` | `None` | `90db16de6c0119c0c924c80d206b1e80bc3d2331` | `22be33aff3fad75ef91ab1e1cae2f2f8da2987d3` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:944a72a6c511fd953626f5d79892efa123efc5795b83a0f433191e1683cc2fc9` |
| `P18c-unrelated-tip` | `None` | `22628ae24f01e250d30bb4cf9c2a7832f217677e` | `e46c2df2b7bdeeedf09b55b74a3745ea6d7f5139` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:c7c1f4109a347761d4089ad0f4484fe6206632ed8a8644644720ccfcaa5ca4a9` |
| `P18d-shallow-required-region` | `None` | `e68bb90fcc341adde9f4372caff5ecc6f9b1e340` | `4303d2f9587973759de42362a6c20b4b48170ab5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:452dc1025e7b8c27712206001eacd5ee9662cef92fc79c8386e198bb9cd76ce9` |
| `P18e-missing-queue-blob` | `a668e725d1233ee7d5930c077268d222dd27c277` | `8d7223893ec84e193595fe975a53d36f893502cb` | `ec9f29e0560c60e66700496cee9ce14858aebb4d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:6b03f428851aa440e7ebc445770abb6912c16dc3c0acf3883108d5a384159f75` |
| `P18f-missing-queue-tree` | `80ee9796305f288404f4aab5960193d8555c5e5a` | `61e6b7c9b52f0ea9ecb35c5bb8da8211aa7232d5` | `4f08ffcf2930d3d3a121b453b4b16a5b5f0bfa73` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:b6db223595703f21ac1f380c1a39e3f6e78d7a9475ba287ff85725f83188f981` |
| `P18g-multiple-merge-bases` | `None` | `c9a1e28be75d020fa3222bfb2a5b04649329083e` | `8e067847820ccf0c7ed10b39c330162e1b10d880` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:816ea160b21bd6c653f192da184769b5aff29bd70334e933d509e4f0e7abc782` |
| `P19-production-identities` | `5a986a543953cc623f320ced017dc315be4ac80e` | `7aed085d4fb3393205d57ad66e8d2834a0263bf7` | `7ceda0b76130db3d02ecd3c1d271b467980cf25e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/6/0 | `PASS` | `sha256:0fd43eb2bf74c42b7e6a122240dad192d846f3ed3700fa87c5d405f7260aac2a` |
| `P2-direct-linear-invalid` | `70b791b1e8a9bd24f58737e93a443451f8f0ca11` | `ab15090d6bc10c375e03aa38f1ca6aa87d672a98` | `b00411d0cb294fe228cef9fa6744869d212bff1b` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:13e4c21915cd0432df7b1c30455d5a99d72b1bedc99504fc78dba7478bb48bf8` |
| `P20-lifecycle-types` | `4c9f5ab102d33b44f949f0490fa2ab6b1afef7d5` | `f01ebed3277db3c00a38c601d11a5423a35fc922` | `9de85b85f0f28f3594f681543732bdd2b76bee5a` | 0 | `no-finding` | `valid` | `direct` | 4/0/9/0 | `PASS` | `sha256:5e6104983bbcfe8117e8844d160866b91a785a3c4fd0b0b35210d63ab81daa44` |
| `P21-PCX-17c-squash-erasure` | `34448e62dde0da7a459c9f068a1929a11404bc60` | `67154541398ed536f17c169d282b151571b9031e` | `cdd5e979ba9eeb3e6caf97b05a182981178203bf` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:12c1d53459b10842a60fb296cced251171aa49d7e9730ae25866e609dcb5a709` |
| `P22-PCX-18-one-pass-many-actions` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 1 | `blocking-finding` | `invalid` | `direct` | 16/0/16/0 | `PASS` | `sha256:2ac49920a8aaff399284b401a49db81a8fe06bcbcf24dfc3026f0e25ed97f80e` |
| `P3-genuine-old-loss` | `94db247b706f734bca553f86045fba8b98158a6c` | `5fa1eba2f8984af57952e6c083a0c455fc65d54c` | `5dffe2d077e79208c3e05ec0bfdd5de39600292e` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:fa17788daa5ba1c83093d7413028d766a33cde25dcd9545071fb0605b534d6ca` |
| `P4-pre-C-identical-origins` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:df6076aae0c4abba70a4aefe8b4a3ced94da5e1b188c8fd591e7136bf78f3a7e` |
| `P5-duplicate-at-C` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:bf15ea8e714a7840be079933b4fa534141d6cbce249e0392c481b44c8822dc40` |
| `P6a-old-delete-recreate` | `8039e1a89ee29be7b3a79d4fda7aa15a8653058f` | `900438d3fe4393f0ea2f87aa4d8dfc1e188f5919` | `6781a4eaee80c8ebde47bef04c33dcb47e91bc98` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/1/0 | `PASS` | `sha256:e7476ca9ddd39efd1f8ddc6dff60ef091d6535ef0d448b9bbff348ab9429b19b` |
| `P6b-candidate-delete-recreate` | `b5161adf1ba6eeb99b2181aa264598f707d19a95` | `bfb4c66d18c551b23a8580132543db2357ddb4f7` | `ca9f44b0f38c99dc7c70093046ead1b19f464389` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:c17440be9a06b30a5a7d182cc9b103c17b4e974bdd2751b170561cfc5efdbcf4` |
| `P7-immutable-payload-change` | `43f673bf99a741dc37c6631d39bd5e9c037f7368` | `523cb1cb6e17b0e00b3bc3235618cfc0834d233f` | `03ae818dc35342d03432e7e25ca292808528ff3d` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:486ff8310b7917927de71b8cf36c9a45258f2b810f9a8eb934115ee6c52404d4` |
| `P8-path-timing-move` | `1c34d6196d22c53ce54eac5b2cbed46be8432134` | `f9bdb1fd1af9e2d3b5b405594d2ef37ab55ac025` | `cef78e9bb54e4b4318172d0a2b6881da3a4b8971` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:a0ac22359f018b2e38ed57c7a86b1a1a3badf8d7cd633d026bc617dc9cd0e4d8` |
| `P9-direct-two-parent-valid` | `074b437bb8582cabd4372ea380454368e8d81ab3` | `2380b58d4a6b687769359903f12100d69a543b2d` | `faa886162cc54c7c6544e33793a6e7f4342a90a0` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:85d5d6234a3dfcf59fbee9f44f56230d2ff9c281c1632ac0c935939b793130bb` |
| `PCX-01-neutral-parent` | `ee5d0eb6e70a978d7da73147f1faef9615f8624e` | `c4b177d1b0039326cd6592c90f7ce62e729ed3a8` | `acc6673079b122e2ae443cc91c4012c83344430d` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:ddcbcf13e9de835ea6efd32f91ae3f1a7e141e68178595d4f6a6a7e1587c87b0` |
| `PCX-02-neutral-plus-invalid-carrier` | `b02a161fd6cd727aa2eb6bdf5ec43f5c5587e04d` | `78c77a131414cb7f196137896f9fd0080bb6552e` | `cf599de5003f9d108a979cb21f6d36c5c3785dee` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:3db4d2da6dff62957ec7abc2d44cc9e3bd0de86b5b6b2956371fc33ec37bcba2` |
| `PCX-03-foreign-exact-identity` | `35f271b5d18393dac59002bb0c0c794d3589659b` | `36313b4892aaa243fc2d01fd05ebc8e7ac0145e3` | `f7fb0303c3061d22daf61cdeb03cd67496639432` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:1a9c93a73da55382401e057fb81b58e9ae883b4dd3d24f862f4bff1f71e13f6b` |
| `PCX-04-several-absent-one-supplier` | `32c7576c4c4aca96bdad8162078e9b2a28d6ae33` | `c4cf7124f59fc3edbec373d87507aba76143cfd6` | `cb06b9b4e0a3ae842774d0f888ebb5f1bca53881` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:983e99a6645f2c7911efb9a8c83363d3ba19ad38a7c1b0fde25d8c0799cd9f79` |
| `PCX-05-competing-later-supplier` | `d297f8d7d5f3557c94f944194e6da99c1c092c81` | `39f138bf6fdf1db76fe12a652664dbdd3fcb33e6` | `5cc308cff656d4866cfd255d968e65ee17b58271` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:bedb7e1c5b70d6ae015327ca762451aaca8a0e59b5a169d3b2ed4026855e0024` |
| `PCX-06-nested-supplier-over-direct` | `4fef7d2a64023363e13a455eddeac016838f651a` | `db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0` | `2513214e5beaae7f3a289d4fae4018a00971c21c` | 0 | `no-finding` | `valid` | `supplier` | 2/2/1/4 | `PASS` | `sha256:d8a2552d80880c0076952e03a25b00cc9f450bc794d5c82af430748b9cd05c80` |
| `PCX-07-overqualified-propagation` | `e9920c69e87c8fadecea9dd6bfce80039a60619b` | `4eb27ecce806ae96e902a1c1cb1098fb7e8d7ba7` | `ea08bb6dd2a18266bfd6f436011c1cc610c4c8dd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:361cf870fe1cca1c45c3f6cbbc3c2d21a8b68d94958a402c00ff967df17b2648` |
| `PCX-09-recreated-claimed-bytes` | `41008171d1f9c6afd397a17c3e5567e040d881e2` | `9e38900a6d2f2e3b48457b5fe92fb55cf68ef1ed` | `626d32b7150a4185dddc568c91f3f096abd5f4e5` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:112b4d39bab8020eb1791323987f86ae72152a005547191ad69a9011eea5f3ca` |
| `PCX-10-transient-multiplicity` | `04b5c0356d29ee676d98d58fc639efaaa47278ea` | `cb082de1d3492e0b6e85918c5b1a4d2d600a110c` | `6dc48150188c026a1300d5fa19b065b1ad6a01aa` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:d3b15fba5f28d41bf2f709f180bf671d4d90b830846b4b52cd462b6bd182bc3d` |
| `PCX-11-different-payload-same-path` | `9f7f5b9e5ce030055a6151bed80dfb6db1a94206` | `d45b35ca53a81320262faaeb7136fd081e8c1fef` | `78876b74b5d5c2cbdd3085a992a484c82280c769` | 1 | `blocking-finding` | `invalid` | `mixed` | 2/1/1/1 | `PASS` | `sha256:f0f2a23e1c912092ac153a62c24b26ac3b02dc9cdc866bf529e62cbcd42163ee` |
| `PCX-12-timing-rename-supplier` | `c81cd1ddc4c58f7e6d5b9bd7f0a626f972651c79` | `e89ed03c9f3c8d338d6b4f03dfee7d6994ce400e` | `97ae732aab6ceb15bba65fdc775f3b4d5115a3a2` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:8b35f84315ddbe5acbfbe92c846a244f92ca5967c80b5c372efb080a67a83973` |
| `PCX-13-conflicting-human-response` | `58e15401aaba3e6f056f7dbaf6789c10d35ae553` | `1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047` | `14707f668aecd10bb531aa6fa0ec57700d26844b` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/3/1/1 | `PASS` | `sha256:0fa302dd23258cb6fdd9ba836357c6b2ab1783be4ec38ca51ccd1a1ddb72949d` |
| `PCX-14-valid-human-supplier` | `920e716ffd62703b03e21acd40423d34d60f165d` | `15ab9f04625ca7c4d6a8847bebaaa2b3169b5b69` | `36eaf058713764ea31d22a9cc74f800aaefbed1d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:96f92e248bc4bb5138dff35ef1beb984fff2760647ca638098d8c1bfae53c89f` |
| `PCX-15-generated-retry-supplier` | `03cab3c249ed96db646bda0085596770b15f5801` | `44457ccb883890f47979a0504d52f5da066af287` | `338762e488c1ce489527bb173d9f8e2262c5f4c8` | 0 | `no-finding` | `valid` | `supplier` | 1/1/7/1 | `PASS` | `sha256:cb6f84953c858c323ac3ae871fa11898b45004e496aab1a4f5728c7fe6eacfd3` |
| `PCX-16-task-pickup-supplier` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:936b41936cccad3c5a13b5f0e7f5493f2df68dc9d55f9ae0685f392a4b6c689e` |
| `PCX-17-complete-cherry-pick` | `33db81167dcecdaa77e3c6e97ea6305b99d13346` | `8385f0c8c1094932a794ebb94b32b4d872806cd2` | `855eaa3b813900caaa0e523baa198491cb4bc47b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:b01e39fb87274d607564cccd519a3d524abfb5407bbbe7a46dd3604bb66f8fb5` |
| `PCX-17-deletion-only-cherry-pick` | `56008eecc6492c2c091a516834d675e283cc40bd` | `35b9163866f1c9cf6ab2435eeba3abfc0b9fd1fa` | `5da95440d2c9065d8b6f4506d2108a3f97bed539` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:126c1846d489f8b558855d1bc99bf5f75197e28e6e8243e2098e2e94acc45e5f` |
| `PCX-19-missing-claim-blob-recovery` | `759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c` | `90aed2b3f8214a269d6421e6f4fe63ad3a61b091` | `dd34454f3204840ae81e2f273772c00488e681ea` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:e9e12381f6d09f1e5fb1711e0487b9297b60d07b5b8a1c5f8c8cc2a535787c73` |
| `PCX-20a-budget-below-limit` | `c957293f54b1b960b7b7f351087c77ac874eb253` | `ad76497bc5fa23076fff741b5d419a2ccd714637` | `ce775146b901f12bc2c05d22f06343da4d2c66d0` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:2b551b5030673dfd739ee53fe14021ab6e63c045baa1b5dc3d2603a23591a329` |
| `PCX-20b-budget-overflow` | `a018c90c3dbe1374339730ede5c7b76e21fee985` | `fb2043655802898f2561cc21431580a2609aef9c` | `06abdb0e773f19b6acc2ecf85d17e6c1770e7295` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:34b0c3958a5702f59e0f5139df337832eb4cb08c0681bde6d42e9c616c1d5d38` |
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/2/0 | `PASS` | `sha256:13327654600c6bec16211160960f514418fc9dab13839477b1f5e81a7493ff1a` |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` | `9d96a7eecc2b34704ef588142e4b48111849f3a9` | `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 1/1/2/0 | `PASS` | `sha256:77ab0503f79f57dd3d18e883c8b0c106922a30cb6e7638c2a34ac9d2ab9e44f5` |
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` | `7e0284f9a2354f44218502da59ca365cff918285` | `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | 0 | `no-finding` | `valid` | `direct` | 2/0/4/0 | `PASS` | `sha256:71bcacd7b3293d84b47f47b1f6cc61dd480e805399f0088fa3fc11bfc959c11e` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` | `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` | `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:3dec6494170b1a386836df93f56ddcd06adb2089eb66b78a298fe97e5de299a6` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` | `75d9c282afe629e2fee58b878ffe93481926e719` | `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:6b99e008e964030aa45e8d04054352c0a8bd7017b49dc3e7774cef6a62706801` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` | `d784ca71704ac0bd18e1a70b45c18d1994353eb9` | `6677edfd8778a755904939d01b070af66f32bcaa` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/4/0 | `PASS` | `sha256:d5e081fe7d5550eaf9b32bf8950f31e4323d9cdc9cad3afd1846bf155b8d0195` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:47f9bdd9ac187028875bff51f687abe8cad37975deb9fab29957352645944ec3` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` | `5218487e636b8519c69f49d146acd9b7f8b25948` | `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:3d9e8e438c5c63213f0247b3c471efd21e6fc3d09de9cad9838ce8cde55e6861` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` | `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` | `464115d4c500dda036c5592c6c8f21fe9a959e15` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:beb36c07fbc633d342e4003603030e10813e7b8692764a4ac7530574dc4f80f1` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` | `69bbf3a1bec29fcf92121c581925bb092d1535ab` | `24126e616db515f5ee1d08d4f2da297b50e02f3a` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:9d4a84b64df14f7c1b5035a0def3c376688a8b5ceef7375f84c6beac711d5032` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` | `2c3f7acfeeb385de256074091a38c9953ce7f1f9` | `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:db83055f244cce5d2b1a9ae49a3509d77c552aa448b5e76757b48b579b56dd0f` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` | `cc3bf0c5664ca51a1c1df82759aaa607efd30550` | `344c8d4e0333b14fb5b21550528242614812a55b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:6d9d381533bd2bf804b5bcf1f1eb2110bd2f0be2e884bef22e7e4eff7caa26e6` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` | `2c37567f76cece330ee8c4997c96aa2bcd1764e0` | `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:0846fc05b0b91868d16e5a0eddc5287c855396eb88292f966ec753d2f5e68a1d` |
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` | `a3edb26d4a2069954d0459dd9ea503cc27833f61` | `edee50f1fe44db9136335db0de7e27ad442f4eca` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:2338e3898823dd9988933a74f62cc00c3669d85f2b85df4e3d8c64062c49bc9a` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` | `b5ea69a78713ea41e8229125a90fa2718088c6f9` | `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | 0 | `no-finding` | `none` | `none` | 0/0/6/0 | `PASS` | `sha256:7aab601a5efbed150984f852cb7736352a3e7ffc0fe481fa9f283b8d55bba6ca` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` | `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` | `962821fb4d4faabe72c3b8e86823a5367aa3294f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:49a79483e84ea7a89cd256f683304983b5cdc9f91df3371a4c23e379ad0f01f1` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` | `e7a884697094e9be1c876b78fc33d9e259d92149` | `8fd2e814f38bf145bd7c84d9e22a355056d40649` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:56992f5b10d81c704b239e2e5700662137acd3c87c6ce312b4191b79a832d015` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:18acda731a97141f40af6e4115ea5eaa4c1336cde4f38d56db0514138206f94a` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` | `60538a926a9acd01f898ba0371ad5249c912f7fc` | `1031e6315881cdc99376df52bcddc86a4427e920` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:b5056d19928cfcfaaa8c52c5c57620ae43d90d4f05aef3c5477ea3e1eac13c05` |
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` | `37d577cc2c265e8e7082bfd86dd156172db98c5c` | `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:7ba7bb5d7e7b8e000a3920310fe875ae91b46dc16265cecd3565e3a706db2909` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` | `d39ee31be16db2789928827c2e132a31e22b828f` | `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:e8b18f9036fe0c962ac3ce843dee0df0801855a090ce8185aaf2a14dfc5cb7a0` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` | `68f01125491f31f259d6cc636bc2f818c9529571` | `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:538fc603a3feec2777e8b89f28743a6689ec86b08c2115849ff9cf294f8c2683` |
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/3/0 | `PASS` | `sha256:6cb0f5acb3a9f8d013bb69ab9659639a9b4a2a4de2d1f6af6d08ac91e7c46667` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:0eea4130410e0abd7a1f701b7a2de860a7f78dbd664922a81527b77950885112` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` | `ceeb45bc58cb8e6726517130e20fff034db993f3` | `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:40d89a889151f7c172902bae5aa48489272351b92426ce033e16c5418f1e11c7` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` | `521e76aa7253b7dc1214c2bbdca5c788a601e21d` | `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/8/0 | `PASS` | `sha256:fcd3277c50ea718d30b73f6fbe37336b87f62020626e79ab03f879477b46bbd3` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` | `74442946b6639f57e7167838a13cc286f39d3519` | `ca8939b406b7b2323fd08b044625639f5e80cb6b` | 0 | `no-finding` | `none` | `none` | 0/0/8/0 | `PASS` | `sha256:17353efb5504ff22a3ce1ab9e0344c8f83cb9ac83b75a202a49c1dba3964b6a8` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` | `dafb69000967fde6234bce7999767113def81c5c` | `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:98c00dcd4a5c2c0fee4d1ac4d588a40acc75ed80266fb5fe84b3bc5efb2cc68c` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` | `03f6cd5ee859d98e6110b2554606ba655ea9b66c` | `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | 0 | `no-finding` | `none` | `none` | 0/0/5/0 | `PASS` | `sha256:ff42d0c815ccc53912a3be69cc56bb70411923db830d2f43d4fca13e9fde568d` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` | `6f1dba05d9dca3e3776da3c7005a83807190ae74` | `0662f0827db1ad2e39f59626dd8d87f316b73421` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:ed655c24b07ff2d6489cccfc84aae0c3a359e116794a9e5b2f596c104ed39471` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` | `6d9c8b1bfed15a512d68db494efb71a2d0577f33` | `0b0243e67b4d4635716eb2113f81419da982ba3c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:7047838953278577da593c0049e88fb92b7ec5b0197f2e9dfaab558a47d75c36` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` | `a6ff10d32896ec2d87dad1696b24e07cc73ead65` | `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:09fc9a4b834f9e695184e34c48e1071ea89bf18150670b64d023ed5f73bcd5f6` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:0f30de25a5f3e680aa4491d3eaf98edc35cf7eaf5659ddd7b364489e6ade74fa` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` | `b6e124010b1f74882864bdc3dc1fbd289fd5305c` | `e9e33f66742ae613b738497753ffb4957610b85e` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:0a10908036b1ee60065b565bd242f9401906a3f5430d74b1c33e2eb48d78621d` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` | `a09f2f2ed771008847609d177c72e0b1f62d8084` | `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:1f23961a939f9a451a871ff6b68e2714e44fa369bad4741aeb035ade1715d6e1` |
| `R15-old-continuous-preserved` | `9972c0979b118b85b5c9d80a811679b41840910b` | `6e29170cbd7791baf6f74923a50387a9359979e1` | `316e8cd76611658ad9587c73e54cbfb6f3c9f379` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:ff80a288fcd46197e946c4928c10025380a75a8d0588417deee0a220c5f26520` |
| `R15-old-hidden-bytes-restore` | `600ae7430233c349c25bbe4ab0f9f8fb55e7c92e` | `023e0594e4a6d2f3403635decbac7a9d90ec06f0` | `20096f8d2a62bfe7e6990d90b91135ef249879c6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:5092392c3ce52068c2de5952779140dd8d69281d8c878ee14ef1eb386211ed08` |
| `R15-old-human-binding-restore` | `ed9337d8d288a493c724a71081e4db71972e2e08` | `1d8e4411979ce8ea8dc5697180f8d17be74f1be6` | `fce1db3bfd0846d5af6dcc96b362a52baec376bc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:369fe0458f490c46eb0d1724b7fb549b8c61961885df74fe4738f6d384033a6e` |
| `R15-old-invalid-delete-recreate` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:0f6c99737cf14e16cd720ecb43e69a664ef7b264522b07c8f751169dfaa769e0` |
| `R15-old-valid-delete-recreate` | `d949c6358b9809dbc4c19c55ccc30fab511c7413` | `5f6066d0642c29fbb3414c54445b8ac08d5c99ff` | `de690fe09e6d88d499db4b3ebccdb7dbfb8b5617` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:2701297e2d02d33bb0de6487b0867541feed7a3d20871520109804f4de9e4189` |
| `R16-earlier-landed-evidence-reversal` | `e731036f833027f6e32ae9d17deec1f1b3114412` | `f8186fb2af1ae0e23196a4ac0095582433643daa` | `aee42abb66d8ba55343efe6f741c32987563844e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:cd3bc9e63a2ac96d13aabf3431dcbf4ac75da09d93554dbd50114e02989835f2` |
| `R16-pickup-evolution-0-backlog` | `41945ab0488983f425986ec3f815e50e974be318` | `ddee8c3c0a47baed150ff41c81fe3dd3578991e0` | `50ddfeceda267269a756eff178f2e6f2dcde7af7` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:f6fe98a1f9e128aa905b3949dec19e5c56c06ba34ee0cd2d0406ff05f9c7940d` |
| `R16-pickup-evolution-2-blocked` | `e7e14e5b5790e4682f7609b3ca494fc9fd1e9218` | `97de8555908750bc8bfe4f195811124e6639b33e` | `48a4d96e210ac69ff036bff2bd154d6e496e6a05` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:cc4fa80a5018611b1724d0fedda1d6013b97dd15d0c0eebcca6c8d9a62485e4a` |
| `R16-pickup-evolution-3-in-review` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `66aae1f38225afbdde6a9af1c261223a7505c461` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:ce91aa00956f45c83bfeff4a458980b43eca8784bda0b0fba8de3d8983b02c01` |
| `R16-pickup-evolution-3-in-review-drop-artifact` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `04e4cdf6f4c210ea0a27c59ed86f1d01627024c2` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:33cc6273f00587099fc0a7121eb5484ecfff82df0a8a5a0768bf131364261ac8` |
| `R16-pickup-evolution-4-done` | `28b720891ddfd4c7291ada824d3d2196cf4a560b` | `da9ebd1326c500e7d2c008fdb80f43be5cf13ff9` | `a8a309c333926cb8144f022c4356736917e5907f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:43e891b1b6d97d9d13d84735b6c00ad1052f3192d6be8608aead3a0c83a67da4` |
| `R16-support-adoption-drift` | `a831384530c69ef834d1d997c25ffb996cfa4bbc` | `be001bade214359024c192e8b06d79229261a4c7` | `ce12604ff0140d20fdda463a6140634b62f35bed` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:85a1d440adff9586b69f921c15e6bb0b05aed7f03624fd8cb004c0bbfe9c3e76` |
| `R16-support-forward` | `8617eee2ba78f3977a9e7e0329159f725633daac` | `4690d1f06ca2513358bd47fc88e8dfdee3a15d71` | `9e15331efb2e68a1762d26fed1df245232a40f2d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:018a1758e57bb2f651ec826ce44c5b3702b539f186bda98d0052eaa1bd71abfd` |
| `R16-support-invalid-source` | `b5e005e8c934907d6548515f752cba73b79797da` | `8cc15771a0e42ecaa2b04166fdd57589976cb454` | `2c6d7881177ab459839ec9bf195c035cb8faeddf` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:92ae68617299cdd37929c813f0751c42ae80df32cdabd7d6e27351e727225815` |
| `R16-support-nested-drop` | `168496fb2f34612a9276eab0151b2b83bf1edd88` | `13967af6be58e3cbea6ee31c6f54f6c39b246626` | `95622f34bd3618ecc561897fe977861d26c1a4c8` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:8441d4d5057ce12e5bee71b77c9ce33ad251de17936450ebe9e80973fa373da4` |
| `R16-support-permutation-diamond` | `f3d302490bc5c12be93f9392e00071fef0822ffa` | `b82141d042aba0552175891be684c7dd7eccc579` | `04baf28178f9b9b80761050e875ca2f993b4792a` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:313aa050645dcd203db33f843fe912e15d74a017cf5509e45768180d2b61a111` |
| `R16-support-reverse-drop` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:71491a1d2c81850c87da0f7a455cf73dbfa4b52ec802fae650086361ff02fffa` |
| `R16-support-reverse-preserved` | `f3b2fb92a748ae2b38142cc01b1542b5302dcdfb` | `1f62604717746cdf35f2f13b4efe8789e9a73118` | `e38824daf72c0fbb9c049b6662fea36ad262f8cd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:517ec37abff6ee3c7c7e98f96f273d29f8c866aad954365e3d36427723fefad6` |
| `R16-support-source-evolution` | `ffc5faa56114e44e8497228192ca4daacd278179` | `91474815e967e29084c0d18638907fe068dfd87e` | `2614fbbda55f0fd12af32872df6361a290c8b12b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:46b92535c8d12b4bbaab442d61db2e9db87e1310127c0928bb745a9fa0710757` |
| `R17-carry-absent-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:d96cba8e1d99b320d00b8d1e5f71c70401afa7a9a1b2485b3ec1dc0316fb8e13` |
| `R17-carry-compatible` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `ba001beceb64bc88110a724ad6da2ee3498c8c90` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:a257b5e716870c0dbdaabb2def18f20c3c72bc11770ed6c7c584265db4fc806b` |
| `R17-carry-compatible-reversed` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `b4684c533ad9bfcb5918dfff653a30eda3e53d66` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:1631785cd53758a165cac49923f8982b83e56be9c7c320733cae2d85cf65ff60` |
| `R17-carry-incompatible` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:0ec3d9aff1f5131f60470e863d0dc914d6976423d297e54e5370353bffa9cca5` |
| `R17-carry-outside-duplicate` | `f793332edc8b2cbee979959d560c177365267cb6` | `723fbd86c6180058e653f7b8241401c172a7dd1a` | `0449217881a784a7c4bb1ef1e6b8ed1a5fb781f5` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:028901ed4ff8d5bf955016dbd16cabfc831500546fbc6859fd53a3b92a9602e7` |
| `R17-carry-outside-single` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:a3c051da3ebdf5e9c2ced2b7031c5e1841162dab68fafd99227211174dce5c68` |
| `R17-dynamic-support-traversal-exact` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:724d94b479b33477e26f3401ebb49226d0ef7c6e536cf98df33c582f296cee68` |
| `R17-dynamic-support-traversal-plus-one-refused` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:9e44f502ce49f05825661c6fd26e2c6e95b8cc6055cf9de5940f13b94a1251a8` |
| `R17-flat-tree-peak-exact` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8ca44a7260e4cfe2bd12d505631ff3eb18784fc321578a199a41c0cf5b01f71e` |
| `R17-flat-tree-peak-plus-one-refused` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:e7b1bb1c6dcb1a7b0bdc65a0dbea2e7bb38a58aad06220dd06d7a0274cafd9e6` |
| `R17-graph-line-peak-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:41a97013aa150c56caac29653d5dd9698bdd0b8451de7ecbc836624f3165bca0` |
| `R17-graph-line-peak-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:9b71446d65d66526334722308b20fdaadd7d85caa774820c6bd3c90fddd4ebcc` |
| `R17-graph-output-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:b540e8690d9d5b1240a45b23e3dc6efe8ae577af58a25c6507b2ddd6a84c2f22` |
| `R17-graph-output-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:6dc04abc301ba6cf54a77866705031c93d58a32c8e0cc0b27d07dd857ac69a28` |
| `R17-graph-parent-tokens-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:15327dd6ee43c73000301fe1340344330c57c4b0bc8e798cfdf60e281788df40` |
| `R17-graph-parent-tokens-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:30c58b0253bfad4a9ae1c3c9314a25b8ecb64206f7034b2697bc912664395f4d` |
| `R17-object-payload-peak-exact` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:da6ba0ce09eae061f94738f49e6cc3cb84e348e468fa5ad25b59093e2da405d1` |
| `R17-object-payload-peak-plus-one-refused` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:ca14b2cc2c8a804e85ee1af1b4089a42980126b5de3a8e59b65ecf18902bc6d8` |
| `R17-outside-C-neutral-parent-valid-restack` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:e325bb06c373dcff66b443f887ea975d5c6a408ba2d658fdceae10ee0dcf22de` |
| `R17-persisted-outside-duplicate` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `481c03e8e4afa0b3dfe37df8a244bc53823811f4` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:0b5736d9b34842065c185ea8f3c6adaf9d878f3e68229a528c178d8247e30dfe` |
| `R17-persisted-outside-duplicate-reversed` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `d74cfd74fc6648eb13bb52ad192ee13b4146155e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:d059e0f53909d5c4857b5e08a352e944deabcf4e28e93f72d38fa4f8d4544ebb` |
| `R17-persisted-outside-single` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:2c778a568599e028ca786285c5f6bbdee2b46258e873f1aeb648c2d708ff0985` |
| `R17-persisted-outside-single-reversed` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `4a231bb4516e6185d7ade17f5e5cb8aaafcc0613` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:8cb1504320ec05dcd9e316688e62c51195b6997029f4950951a462a8c393d901` |
| `R17-persisted-unauthorized-absent-arm` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `c1e4c835d0ece38b56490f0beffef88494aef8a2` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:c21aa3a8f002915c482547824d7a042d700d23d5dd521fb6940b72fefd7d3d12` |
| `R17-persisted-unauthorized-absent-arm-reversed` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `6a55c69bf40bfcd9abe33bababdae51ad111eeca` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:b46d669c1faf080f79619692dfe7ee5f2398be1b11543baef3ead4757813c8f5` |
| `R17-persisted-valid-absent-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:602dc2f47493331b671afe1b90d1c5d6fd66cd430799b8fcac202ffa830923b9` |
| `R17-persisted-valid-absent-arm-reversed` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `12f08cf66b77738190f29720044039af1fcc10ec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:a630ee2a676a292a3bc56fdb457e80145d90d64aa2504cc4fc2e2dac57559fcb` |
| `R17-precharge-P22-budget` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:8e413604004e8854c45dba14af04af05a03ee1ff09c2ef5ba7a3bb1af3ead707` |
| `R17-support-serialized-exact` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3a1c80bdf79e4a74a3f660c2ffb4d843c92281b723539f9aecbede2ad56d37e2` |
| `R17-support-serialized-plus-one-refused` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:7e665cdd4c8bdbdc5deec80fbfe7e1bf472dd59d31d37e6dd7de1cdcaab23452` |
| `R17-unreadable-outside-C-ancestor-stays-unopened` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:c851684f1e49bd6f2b62dafbab19245c87afd940293b05baebfcc8dfb3554700` |
| `R17-unreadable-outside-C-boundary` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:39e77f5fe3eb29606d65cda0a8d72b2051974e8e09e44eb18a20e1eafcf3c246` |
| `R17-wide-outside-C-boundary-budget` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:0a42c57841f769d0aaec23e6ab7dc4c49913f16b32a03ad5c2763ecefe3a5e08` |
| `R18-B-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:b0e2ddfe02123526ab284d38b3680d7b3b2cf35b6c3bf55fbd59b8a3fcc5d256` |
| `R18-B-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:d7983a7ea36b32764e055f1020e59e4d3a188d4c89fa0207627f1a3d5ce525ab` |
| `R18-B-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:4a69ea5ede6d9db4f78085e1b0fdaa766b161bb269b69d01deecb872c8cae8f8` |
| `R18-B-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:31554872fc89467dbb95d18415c6559a39d5628459a14a8a9e9e1b975150ab53` |
| `R18-B-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:e88d716291ff6f462c48287ad4085e744d74d3660cefd1e848fbed8968d9cd31` |
| `R18-B-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:91d1df81c9210adf8279729c2def6b6e356ca764d1a802279a91c29b166b3d05` |
| `R18-B-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:cbdc1d583891b9972b71b97c2b386dcd1ce7ae08904763cc079ecae902391a0e` |
| `R18-B-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 1 | `blocking-finding` | `ambiguous` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:af693df6a2d5b29de2f8f37cf13e818613567f5c7bed6f60d38519afb52a4fd4` |
| `R18-B-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:73f05a5be0f618a2756b91a2bb32b5a687f4d94a376d161937cb75fdbac72088` |
| `R18-U-O-only-post-C-loss` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9c12ccfb1f02f0d3d7571d00ffdb12c66d82130b` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:b40d51c6f169e1c35bb1a9588185afb47d718a1be83162e6407beecfa2085c3d` |
| `R18-U-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:0bfd50f33422fc26c38bbafcedf2f642d7fcd744911986856e3bb3aab595a164` |
| `R18-U-claim-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `90e1f0632af49864eb90bb43dfd9d653226f7e29` | `0170b8f74746a2842e91e3d24db2b40794892a6d` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:89228816ec6ab6e4d5b40875b9c529fa174bffaff13dde6b3432a92facf1c600` |
| `R18-U-delete-recreate-N` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:9211af9e02d9d213b1b98298e65f1e0d8bee347927c0630855448b32daff8e40` |
| `R18-U-delete-recreate-O` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `32e5e784fb97324e37f759d14a5dac600588b780` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:fda89d80d78e3b6098cad2a0247da04bd0e076e75641984d7cf88b0de3115ff1` |
| `R18-U-endpoint-regression` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `fe39fc5d19b39d80c00132f6bb67671afd026024` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:a3f9739b4114b67ea14a3daab312996adc909fc0d90bff5f7e1dece7623c4a4f` |
| `R18-U-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:1599c73fdeafaf56eda162da45c461fdeea7cbe359d92b59cca9e9bff03a6573` |
| `R18-U-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:6ec2327ada9ebcf97a8d415b6f539043cd78c1e65dc4879549c53f1c8163ffa3` |
| `R18-U-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:71594bdfe99772aef5601543c0d415758604ea572e2740f7c0c1f39a05bfb0cf` |
| `R18-U-human-response-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `2574705b088135eb07beb5b710a919626a134e9f` | `8570f09b40724dcdbe220428a2808fd418d9955b` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:1e07af878796bdbac2bb0e1aa654d91c3c4ff7a09fb62da441cb7b7ce90f5513` |
| `R18-U-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:0cb38a99efdfcc69c33166f37104a651255bc0731f119f22a3917d64acc478a8` |
| `R18-U-inherited-then-deleted-merge-arm` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `073d6e1d080608961f59d7a9168d96b24fd2e3a5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:c8b29cb79c2c26b02ef8c06e022395cca680a670d4fd99f6d6f770d0ace0292a` |
| `R18-U-multiplicity` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9d0e0b8d05a8ea5f0da83647bec14f62b5edfb67` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:182de1612667db226ff09b9033633020d31f754c4e01163d4349f989025da3c6` |
| `R18-U-neutral-pre-origin-merge` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `57533e22234a2f70d70777040816fd6c436ee9a6` | `b50449c74ca178d7aa31ffe996afadb3563c8ef4` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:4a0e6e7b14d4cf191deccc47b3121eb841029534ab7df079871960071b703049` |
| `R18-U-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:75a6aab12a668424b28bd2c93fb91454ea6fb6321ef8645d16467e59c6504510` |
| `R18-U-outside-collision` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `71cedcd8dde74240d0cdd5a0d0e0e43e4819e80e` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:d4538541553e09725a6e0f3ad1ef5e749f0db71b3f8d4355d9f953880042c88d` |
| `R18-U-parent-order` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `68f00ece3d08a437207e31fea0decedc88ca3a22` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:11c14b6688b6107e97798edb1225f3cba4c344b5260944300137a319ab56a0fa` |
| `R18-U-parent-order-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `f96e171c8daff5cdc0ec7af626eb222af3c4f2bb` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:6c6b7512f09fb31bb0dfa429fc4548ba588e7842af47e3000a1c0361fbfb81b5` |
| `R18-U-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:05c6ec27a52dba8d0f1d750962f7d443c27b3b77c2cd861c34967c49d941be89` |
| `R18-U-review-binding-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `b4203751e312d0423e9b046c2363e2f638ecdeb2` | `9ee8ac72a1862689c5199828a56b8a83a26a8a26` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/5/0 | `PASS` | `sha256:81df6027f6e1e8e4dcc8f4ac246bbb8141fedb4468ccda628943305f7590adf0` |
| `R18-U-review-compatible-merge` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `85e0328be42a0ecc304640ea8be0bae4272633f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:e2095b04f2a8a58053d427d785626a0cd05519ab7791cd6b4377317438ad3037` |
| `R18-U-review-compatible-merge-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `d7dc0b370d32259f32a188728ba05b599651a4f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:e35981ac39f98cf9251c16c42f96deaa99df3ddeae1c1eccfb841605e3e6eb83` |
| `R18-U-review-compatible-source-high` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `85e0328be42a0ecc304640ea8be0bae4272633f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:4fa83370400a9a7521a8008470968d013c5721d78cbc24a8d430a38569d71819` |
| `R18-U-review-compatible-source-high-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `d7dc0b370d32259f32a188728ba05b599651a4f2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:1f9819cc486339feb3cb36a38ca957f8d5490a8366f3edcd03fa6c74dd11d6a1` |
| `R18-U-review-compatible-source-low` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `4f95dd0b5c539e966be5556fc9bdf9f0a3e6f28f` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:9fc119da3ba91428a861abce36abf2b849aef45bc4a29f84b625bb7e1da80837` |
| `R18-U-review-compatible-source-low-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `eb0fa8a1f62aaf79a97d3e15c3a1eba9a0a1c0c8` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:94a200b7cfb512895aa9bdcc5bfa05d7dfebce95559b84efb08321fecb36d84c` |
| `R18-U-review-duplicate-parent-header` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `25abcada854ffc68d1f6194a349bb5af6bffadf8` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:984083634e0507dc9eb5ea3faad057b318f066bf2b09baed9c079461a162ca28` |
| `R18-U-review-incompatible-carrier` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `064c8ecc54d3eda1a5749b93e4fc8c85f093aa4a` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:28a280abbd27cad8c3f212472648a502d285df2854b55bb0f0674a7bf7765780` |
| `R18-U-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:dbf2ace53011d8fef8459c38df1387d676d57861836ac128f287c401bab22890` |
| `R18-U-review-three-carrying-parents` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `efd5d8b85cb409e8b7615e15d6eda9df0e0db231` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/6/0 | `PASS` | `sha256:00e14fb4e98fdc09efe0d69797a0c16c0e6c6645d37e2697d635de948ff593d0` |
| `R18-U-review-two-valid-sources` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `9344d392b5a97fdad0886c3624e1089daf360f13` | `4693117002177ee117d6f88392b31c99fd3845a5` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/6/0 | `PASS` | `sha256:2b6bf3da35f547070cbe8742d5b542a206bfb23194391282254c453ad86c621d` |
| `R18-U-schema-invalid-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `ae5b882d624ac753ab179bca502e1d470f7cdf23` | `87ffc4416aee8aee8c2adca7eff692b471c5de4a` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:ab26885ec5f786fb4591a8e5486e06d7d5ee59eb38c391a8e8423297f5f4b2ca` |
| `R18-U-second-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `baa0995a63d5d5f4fa418cdf7f79b274c9e90272` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:3f6bf25f1921b804f4d59f7de36cccd7a133e8e954985193b8ae1c4d30834d8d` |
| `R18-U-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:dddc6eae891bac82f3eac5cd3acf9adae362aad75d1f4556989097a6f13b36de` |
| `R18-U-transient-protected-mutation` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4a58c18ccdc13f072d74f6b134ad76b98f28463c` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:60f8029df8a162a5a3aec9c5d106d04d88679b85b8aba8f0cbfd22ef7811a409` |
| `R18-U-unreadable-object` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `a04f20486b2958f99aa41dcf8590989d70bdbc9d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:f8e8d927ec26757eaed5ba45ad2eed7570b336af386cdba97d25ac9d92d4506c` |
| `R18-origin-arm-nodes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:70b5886c396372a4ef4700d06b96c9315046753741595cd324886de221442b61` |
| `R18-origin-arm-nodes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:9f7a079d5a61eee1d3f0145699ebe04ee3bbf6b9156dbfe93fd09b8a6fee8740` |
| `R18-origin-parent-edges-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:0ad8ea2768332e91ae64686482b9d50618c1c12fe4df89835d0612f709cd92a6` |
| `R18-origin-parent-edges-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:c874f39e693c876f1228f6b10774333e976a7249d645e047ad9d9ce6b93230c5` |
| `R18-origin-witness-bytes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:9e091e3bff759dd0d32f7fd982ab03eb1a4c6505e93cc1f7eaab1ed03a2bad9a` |
| `R18-origin-witness-bytes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:43468a258bd768e133248e6f2e7c1b1be52ce8fc20d814f99543cbb7342898b8` |
| `R19-WF-local-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:464925f64531a451ed821e66229e8c98ecca09144c0a5bb072de0a262a3da1ff` |
| `R19-WF-local-missing-old` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:02d7bfaa93b425372d27765107e35e37caf353adc0ab8b30d8ac3f2bf9f85c3f` |
| `R19-WF-local-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:0d3a6304c773f66495fb7c7a403bf1a483b19ab8ddc33aa020ff3acd1ccd7956` |
| `R19-WF-pre-push-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:1673d47fb35423b226ec048da259f2a5f98c290ab0fec602b42710f97b32d42c` |
| `R19-WF-pre-push-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:8129e31d3f67f6b7c6f5ab4b96c86bc9646a2b174061b5b31b1c1e49226f91a3` |
| `R19-WF-pull-request-synchronize-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:ff4a014583149969b6b6ad89e4afb34665e03c6b504533f0ccdb2238d4da64f4` |
| `R19-WF-pull-request-synchronize-head-mismatch` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:296cd1fea87d38abb3fbaf6c4e5c3aad9ad277f9e4f640b8717fd442d09bf15c` |
| `R19-WF-pull-request-synchronize-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:448b7a5e678b1e128d4b59c6d58fba696d0e607ebb106bbd5b022ad362ceb22e` |
| `R19-WF-push-blocking-attack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:810c5fc7313e5941ba84b599da620b05f085062a6b21fd0dc79a6b1f4722ca63` |
| `R19-WF-push-normal-restack` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:543235667adba7b84370ad326957940242a8be4ca6db8d47bca212752d06914f` |
| `R19-WF-push-zero-before` | `None` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:2eb96d72103b1c787936bf2ef9d8051a5087e992d1ccd9b5592a2edd29611812` |
| `R3-01-two-invalid-causal-sources` | `73373ac5106e43d8643b5b616268d77a5ca1d264` | `8f89d0fc4c063c0bbabb284434f74bcf244fb5d3` | `8ed846d60715d845a5e19ab6b299ce853a592614` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:7080f7122e859ac8372a6578618530a339e9f0a89947069e81c38fdd7185dbf9` |
| `R3-02-invalid-valid-causal-competition` | `16722b83a642e40f2157c752a07adffddfaa709d` | `35e767d91f32b96f8f8308b431b5c6a0b35be23f` | `ff42531aadc6ffa000560bc56d995993ffa8e62c` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/2/1/1 | `PASS` | `sha256:e3543be449a9eafe68624012ba1d29cf32a162f92b7909c3819701a9fe21bb60` |
| `R3-03-valid-supplier-plus-invalid-parent-at-N-blocks` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:1a558b67902392847d2ae99c8139c937b49197b16e38ec8f12f64ac478ee1035` |
| `R4-01-same-root-valid-diamond` | `4e831314d34c2897a072cca5b58303d8fd0e7ddd` | `2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e` | `a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:ac7b1a08f05e9aa13c79a590a16185931f1c6b5e1a475b3a0c20c66d735c304a` |
| `R4-02-distinct-valid-root-diamond` | `10965dc1169826888c7d66e2389f9f90787c0064` | `286e35141edc20fad35f8b0d4aeb4930c403d038` | `37a75ca4c96e8966c19fa18afe6b6f9b1e4c10d7` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:924cb12e3b55980de53373cd1c5fa6321d6366337bfb7e7d7acb66b401f8dd6c` |
| `R4-03-equal-root-plus-invalid-diamond` | `90e37b9adc7b3b428f2963282519639354bd2b56` | `de44aaea6c73d11ca46c2255f39f9b9a3d10d36e` | `3c9778ae10bc7a945bb59ad802db12bd6803ea64` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/1 | `PASS` | `sha256:bf507c7e75a9a1ae9a20db2c1207ff74057816959ebada5da12ea20c938f18de` |
| `R5-01-invalid-redelete-after-supplier-reintroduction` | `1e5dad973b3278ca8c12f3dd74f72250eaaf9f09` | `c63664276a141f3f60f61c9d404de201e6f8cf16` | `d40a531fd9a0dacb986f9259ac6f94ec0d248faa` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:58cb8855daf74eee8675d36964b83c0a639c4fe281e6ff6b3ea89414d5dd3705` |
| `R5-02-valid-redelete-after-supplier-reintroduction` | `79b338b3ef54382a0ec95e87a7ba962b1ec7c20a` | `9c8b1418effb6889d14466e278a7987b7e7cfbc3` | `fb0bff9778f436aed2a46f887eafb84e1c74ea5f` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:d7fb2cc76d77087c5095500e838050ffe2ddfb587650e8a0e97d207a4a9e8194` |
| `R6-01-valid-plus-invalid-all-absent` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:94b32a566761416dfd7d47d2db133fcc62f73c110a2361a02420f24d983c210c` |
| `R6-02-valid-plus-ambiguous-all-absent` | `f61617485ff0160e37de559fe752c56ff3bcb5f7` | `10a37a2bc559519d6d84f70850b0a78445c3d5ec` | `4ab46009954bb98c5f22629274722667dc21ca37` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3f93f91e1f059b1c83ba39a509dca223de64159ac2b0c0d1a80f8f82b0292d0d` |
| `R6-03-two-invalid-all-absent` | `f5141f92b29541282cf1ec520470e8c604aeaa6b` | `eb354df4fb54776834a9dff53f51f496a2bb338f` | `8f769727f1c641bd2587115f2fbcda5fdda816d1` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:4a2c54b471f0a55e5e6858399537558daa89e28d8638b3cafc3e8f1f180345c9` |
| `R6-04-same-valid-root-all-absent-wrappers` | `c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59` | `c3b9fb54026383a350146fb2f25243c9e8c7cb01` | `7bf74330f432155c3c39eedbfc81fa72bface489` | 0 | `no-finding` | `valid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:50d2ebd3babc7d5b542bad2ace0c016de81a282f9af28fd312b59a251b774777` |
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` | `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` | `cb29049ff107a9a11a4ec7babbdee21819518dd6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:9b88b08361eef215035dadf61a8f93cad8fe260873fd43fa5fa561a8047225f4` |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` | `b3879039d6d7168e89b3046e6e60e056460907c1` | `2c2289035cfc91c73564f6a97b326ebca02be132` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:3da9b50b86096a9e14f1ead08255de2a57c39b66ee8d2921db607a5fcae78c79` |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` | `e3c594800cfe94f4f23c58060ae4ab31f50c078c` | `dc70864ec5e13a399d4966356b9803075681a0e6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:7d926d7e98bdb607f136398b4f75083bf57912c577424d4533ce71453ebb8190` |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` | `a3f97a3b22945e663eb10180bde5de3b7bf790fa` | `b2dbe65f89982fb586b0fb5349454d80c7c53310` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:210ef882d39550bcbafedd8bf4341c9939c2e1d6ba7eeccf71e94c031c9ddb6d` |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:d936eb1adae81f7614a4c5da184d8da7b1637d1f206798243ea9e46eb4bcb538` |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` | `27927fe11bdeee043660e700c81e8cb3853c56bf` | `1fb9fc40da2d44e839830611cc20d0aee23c560e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/0 | `PASS` | `sha256:00a0fc736d57f66a6449feb58e4c2f73fdbf98d94f89803f5dc4674ea8ccea1f` |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` | `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` | `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:0234e297c74b8562f71f194427ac641ed3c03925e98febdce6cff8ae8b040663` |
| `R9-direct-review-revision-pending-fill` | `00ce8c4f203a14c87a9955fece2645744ab2222a` | `6da769be2398ce26c45d3dba7845e0d6bcdc07fc` | `f5e8ec93ded434c47e27f345c1e38da95297f7be` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:5b21c541339d7767d1c302fecea26278f8cda724de1bd24bec981c6b6db89189` |
| `R9-direct-review-target-pending-fill` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:f759a1beaf9f8df2efcbe67f45a128c94f036e47ae320f98714e9769a3b48866` |
| `R9-supplier-review-revision-pending-fill` | `eef4459d2337688dab6f6681415a6f5c57cca6b8` | `9bec712c0e2453a881aa8fd36ff89d8887e07942` | `26d16dfc1e390a11c674ccbcf8281d212a19544b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:16ba8165b00ea22f715d264611fafdca8297b026020795c6753ca5e05927b021` |
| `R9-supplier-review-target-pending-fill` | `8cc94bd588fa82e6bf7fa0258a7f4a3b96453d75` | `648b5b5515d697600fab0a9aa087a1f63bddad3d` | `64affcee2fe535a4f21aa80e72df2131349dda62` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:ebd4814e8f569969158f00e344a77e8e13edfb19e4ddf18e315e39a998cad79c` |
| `W0-fast-forward-return` | `b614e3dd70da804a078bde5088d38ac9de511846` | `b614e3dd70da804a078bde5088d38ac9de511846` | `2fce4585d497e94f48f6807dd3cd9fd7b432b264` | 0 | `no-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:cc3a6b465ebebe508dbd2ef343fc371680adcacd056c5e1e56e708e41b692538` |
| `W1-pre-PR-push-exact-endpoints` | `2fb10d8c39b965cafdeb5e496e351ab258f75960` | `365339838cdfc9d6579ac21478fec9b776742c27` | `1cc139111382dea68cae0208e17354f6f75c5bad` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:c959d74b453c1e44695a29079915ce975110b2411106cd7b848de4dac6f9108b` |
| `W2-base-advance-retarget-invariant` | `1e1e59bc5493dd584372acb3da94233d867bbed0` | `a6363187edd2b2ae4cac6d24e0bc6d4d9adfb836` | `1c48ddcef1c77fdc65609d2a077ef3cb40396393` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:f16e22f20b03f282771e6e05fa72222a84c315d1e70751e4232856515e4fb6a4` |
| `W3-multiple-PR-API-zero-calls` | `7f7a2d473d3bb95a7879b5ff2c26195a4b730e1e` | `b32b24f6a4b08d17c073bfdc2355521efbcbcf58` | `56238e170cdc0358979e2cbefc7af6cbf89b279b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8d08c17f4254446c95deaa0a7098aac7ea1f1246ea57076c6b47b5ae74feeefe` |
| `W4-stale-rerun-exact-inputs` | `b5c4bd355d0c9fb9279be13d67268628652addc1` | `842d19ca481aa76dfcdcf096af4c550e826d9569` | `6046485394ff351e5cbecdd5c5503c44a821af8c` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8b0a7c25940e3fb05e5d0018777cc3b65ff477d419bb2413673976fbf394c253` |
| `W5-missing-O-coverage-unavailable` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `4923d6cd62a6ccd426bd569cc06323a11f775bc4` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:ec4dc65a87a0dc4e06e079c68b0a62bba6087bf8fb2400b2dae5cb2374b0df12` |
| `W6-created-deleted-zero-endpoints` | `fb590466fe387afa4f25743982c78e281f34f36e` | `2df4b3d62821abe8ea3f482b931ed91d256d24a9` | `1f3aa42d8428e4dd3b8b98220355e0bf883c318d` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:6a0790bdbe68a94819a0bc14acc3dd90493e53d69b51323e1642db2fcbcc9472` |
| `W7-PR-synchronize-top-level-endpoints` | `99342d9672d3f50559eccba1fc16eb8710b7b476` | `55bd0ff6ffe71dcae7a1afbfa440b021bf972dec` | `5a612247b54e551764fbf258e44893a0f5c40dde` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:5537bfdfd3f9086ed2a881a92089c189278bda29d8e4b1783affbba089a51b79` |

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
| `event-adapter-cli-entrypoint` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `three-exit-adapter-contract` | `metadata-only-workflow-fixture` | `OBSERVED_RED` | `sha256:5e5fa8b0f2a196a0f6923572ad09ed7dafc01e2bc7f5e0081832c7ed53ef115f` |
| `first-parent-carry-proof` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c6b273cd04dcb4b4d17e60a3c3913f929ff3342d72b92ccfacd964f07d8f74e` |
| `identity-multiplicity-collapsed-to-set` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7e6e7b7646ca1bcd1821ef3fd920528858c6a8e435eb04b5ff975ff4ebd20ccc` |
| `ignore-absent-C-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:f9a91f587c7790cdfdcd77cd3f389ea8fe9a54a4a27ce0f51af4d4809e75e3a4` |
| `ignore-invalid-N-root` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:017dfcee6a829874ad3c86a4868e42d8d4108579c771a8d838ab1f5c2e9c0fb9` |
| `ignore-outside-C-carrier` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3b56c222946112d1313e27f2259fa322b9f6715328bcbc5a67038eccb63181a8` |
| `ignore-persisted-absent-C-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:b5a60b9898d9fabd6d22870af82214ea6692dc94c68f297735bc18d994a3e4ff` |
| `ignore-persisted-outside-C-collision` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:db79757d9c07fd27faa50b16aad799d190bc584e23a910badd7c2aed36f19100` |
| `leak-object-database-pipes` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `closed-descriptors` | `leaked-descriptors` | `OBSERVED_RED` | `sha256:46e60fa95102a0f119b17330d2ecd8ae610593d0d62e54f6a7cf3b43689f39e0` |
| `literal-review-pending-treated-concrete` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:13d112385cf15c651e998e536dc1094018aa7eed5bcb3a8e7462bcbbbda7a5eb` |
| `locale-git-error-stream-equality` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `unreadable` | `unreadable` | `OBSERVED_RED` | `sha256:5c034618ea0b830c69aa5591031431f90a390b243a064353150941fb215c4cf9` |
| `missing-all-parent-direct-validation` | `d7dc739a275601572c26fadc522a2ae4b71d3b12` | `ff1d9fce8cf6d941f7e0210a9cc6b3380df94741` | `bd005f27951b3bae6225e8cc736936db93667388` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a71ef07baa481ad097d61471eb45665ceb58881ef0384a019692ee0ce15b4493` |
| `missing-post-event-continuity` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:84f5b3d73899c5a20ffd97d5252f388df00d154afd64a4aa9c5f049befdb76a1` |
| `omit-old-tip-human-binding` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ef4a25a4aabc01d7d532866e6426b0e835bb764ddba91dee3bb799907a9d4ecf` |
| `omit-supplier-carrier-human-binding` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7ddbab84dee6c41351e232629529ef9126fe57025c9ef664213926ed748ccdd4` |
| `omit-unanswered-published-review-binding` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:58344243b4503b74ca823588324cfb10c725a5cc25ad5dca23f7469369210de8` |
| `posthoc-budget-accounting` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:8f07fb9440d3812e5416aebd5e7ca45c0a2b72ad79b7aaf5e887d282c7766c64` |
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
| `stream-malformed-truncated-final-line` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `unreadable` | `partial-graph` | `OBSERVED_RED` | `sha256:7f15bfc0408ce7d02754a9c860f5db3523d0c686f1f59e52160243feca438a57` |
| `supplier-authority-borrowing` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` | `41865c9def0f066b1d121b9882872ecf33bfe729` | `8579708e09425d6c4e09b9260991148f8ef3ed6b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bd0477934aca03ca18ec5300fa3db3dc5bbf310cffa7086a8776de47f5d55e74` |
| `unmetered-cone-work` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ea953cb9245f335c1cd2072547c6b5dd1dfe9e20a81dca51eca277d874d4e03a` |
| `unmetered-dynamic-support` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bbcb82db16c13abaf88b2d0a0afc2aa345235c7926a1add086de0f8090fecc4e` |
| `unmetered-object-payload` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a4ff94c668bdd9f7a2198acfc060c16e161a4f9946f348cbe50c67d058d5675d` |
| `unmetered-support-construction` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:33adcbb8dc7c85beb53db6beeed2f4fa65a3aa7b9250cd8bf893678e78507f3e` |
| `unmetered-tree-paths` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:23e8841c4f18d00df03a75b99c583f4926abcdfff4c72a7f959185b030dbe329` |

## Measured cost and object recovery

P22 measured 133 graph commits and 16 disappeared actions with exactly 1 POC graph enumeration, 0 POC-owned per-action history walks, 10973 snapshot requests, 10970 snapshot-cache hits, and 135 actual Git processes.
The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.
PCX-20a passes at its exact measured maximum 5645 with limit 5645; PCX-20b exits 2 with zero partial results when measured maximum 6102 exceeds limit 6101 by one.
R17-precharge-P22-budget charges before work and aborts on `measured work budget exceeded: object_reads=134>133` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.
The 64-parent boundary case stops at parent token 8 against limit 7 after 2870 of 2952 raw bytes; the graph child is reaped and no graph is published.
The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, 2,920 serialized certificate bytes, five origin-arm nodes, three origin parent edges, and 1,042 canonical birth-witness bytes.

PCX-19 is replay-bound by `sha256:e9e12381f6d09f1e5fb1711e0487b9297b60d07b5b8a1c5f8c8cc2a535787c73`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.

## Reproducible audit

Use two fresh, empty scratch roots:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r19-v8-seed1 > /tmp/production-contract-r19-v8-seed1.jsonl
PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --reverse-construction --fixtures-dir /tmp/production-contract-r19-v8-seed777 > /tmp/production-contract-r19-v8-seed777.jsonl
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r19-v8-seed1.jsonl --compare /tmp/production-contract-r19-v8-seed777.jsonl
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r19-v8-seed1.jsonl --damage-test
python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r19-v8-seed1.jsonl --generate
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N --origin-strategy U
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
- PCX-21/22 remain production-integration gates, not isolated-POC completion claims.

## Tests not represented by this artifact

This artifact does not claim deployment, a real remote push, production
adapter wiring, server enforcement, or unsupported review-successor coverage.
