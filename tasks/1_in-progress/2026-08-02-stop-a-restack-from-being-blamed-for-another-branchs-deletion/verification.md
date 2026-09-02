# Verification — Stop a restack from being blamed for another branch's deletion

**Verified:** 2026-09-01 by codex

Only commands actually run and their real output are recorded here. Design reviews name
their immutable revision and remain explicitly superseded when a later correction exists.

## Superseded five-lens design review

**Reviewed revision:** `09b9e08cfbe127ebdb886a5a4438c0ba3391e1ce`

- semantic/DAG / r17-final-semantic-verifier: `block` — the design omitted the POC's old-side graph and did not project persisted proof failures to Findings.
- workflow/adapter/human / r17-production-seam-audit: `block` — normal synthetic PR checkouts, deletion, fork-conflict coverage, transport security, standalone CLI use, and the repair push were underspecified or contradictory.
- budgets/transaction/composition / r16-composition-verifier: `block` — retained results, imported authority, the pre-parse snapshot, and several measured work families had no exact pre-work limits.
- core-fit/substitution / receipt-blast: `approve` — immutable Git inputs, repository authority, no global writes, and the optional policy-free adapter satisfy core admission.
- CLI/contracts/testability / integration-receipt: `block` — standalone and duplicate argument shapes, writer checkout binding, retired-option tests, and executable live canaries were not closed.

The four-to-one panel rejected the revision. No production implementation began from it.

## Superseded separated-CLI design review

**Reviewed revision:** `28d63c0e654bbadfd932f69908512c755c848987`

- semantic/DAG/executable / a15-semantic-review: `block` — amendment 15 conflated the POC's clean persisted `none` with a missing-resolution `none`, and made movable representative paths the stable Finding subject.
- budgets/transaction/composition / a15-budget-review: `block` — a 32 MiB stdout result cannot both meet the absolute deadline and guarantee zero emitted bytes when a pipe reader stalls after accepting a prefix.

The revision was rejected before the remaining lenses. No production implementation began
from it.

## Superseded corrected-design review

**Reviewed revision:** `30c9cc0f9a71a3ae5f82cefb7928a818c383f421`

- semantic/DAG / r18-semantic-design: `block` — the graph command omitted `--ancestry-path`, reopened neutral outside ancestry, and could spend the intrinsic budget on irrelevant history.
- budgets/transaction/composition / receipt-contract: `block` — outside ancestry, arbitrary historical checker dispatch, and stalled children remained unbounded.
- workflow/adapter/human / r18-workflow-design: `block` — the trusted lane lacked a separate historical entrypoint, coverage could be laundered, required-check and evaluator binding claims were unsound, and canary/push lifecycle identities were incomplete.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded attempt-bound activation review

**Reviewed revision:** `3ba7d9f54c7ad22761a5306a0a43035f51a00a59`

- semantic/DAG / a15-semantic-review: `approve` — Strategy A remained accepted-POC
  equivalent and no negative provider state could authorize classifier success.
- workflow/provider / r19-semantic-design: `approve` — official GitHub run-attempt, jobs,
  contexts, artifact, and upload/download source supported the attempt-specific job-log plus
  raw-event/result evidence joins and the public-fork hold union.
- CLI/resource / final-cli-panel: `block` — authenticated patch bytes did not bound expanded
  blob/worktree/object-store bytes, scratch disk, or diff/apply children before materialization.
  Its executable probe produced a 6,037,250-byte Git binary patch for a 1,073,741,824-byte
  zero file, demonstrating the compression boundary.

Budget and core-fit lenses were not run. Production remained unopened.

## Superseded supervised-suite review

**Reviewed revision:** `fef7d871e1b0364a447ae51b072c1d7caf4bd068`

- semantic/DAG / a15-semantic-review: `approve` — the five activation execution forms and
  supervisor remained outside classifier authority and fail closed.
- workflow/provider / r19-semantic-design: `block` — Git emits regular↔symlink changes as a
  same-path delete/create pair, which none of the four parser forms admitted.
- CLI/resource / am22-cli-review: `block` — it reproduced the file-type pair and found that
  patch bytes were accidentally double-charged into the 4 MiB metadata category, making the
  16 MiB patch boundary unreachable. Its supervisor deadline arithmetic was coherent.

Budget and core-fit lenses were not run. Production remained unopened.

## Superseded file-type and single-charge review

**Reviewed revision:** `38ce7a911af196b9ea88b5252f05abca89f31f87`

- semantic/DAG / a15-semantic-review: `block` — the authority digest bound path and payload
  but not Git mode, so a regular authority file could become a same-payload symlink and make
  a latent `os.path.islink()` branch return a false `clean` without a digest change.
- workflow/provider / r19-semantic-design: `block` — provider joins and the new file-type
  pair were coherent, but a schema-valid LF pathname made literal Git emit quoted headers
  outside the parser's admitted grammar.
- CLI/resource / am22-cli-review: `block` — it independently reproduced the quoted-path
  mismatch and proved working-copy and loose-object `+1` fixtures unreachable because their
  limits equal the mathematical maxima of earlier source bounds.

All reviewers confirmed that amendment 24's safe-path regular/symlink fixtures emitted the
required consecutive delete/create pair and applied to the exact intended tree. Budget and
core-fit lenses were not run. Production remained unopened.

## Superseded mode-bound execution review

**Reviewed revision:** `3f3a9554708f7b7f8fb6eac6eb7ee2503f046e48`

- semantic/DAG / a15-semantic-review: `block` — Python could execute a timestamp-valid
  untracked `.pyc` containing different equal-length code while the authenticated regular
  source, mode, size, timestamp, and v2 digest all passed.
- workflow/provider / r19-semantic-design: `block` — provider/receipt sequencing passed,
  but v2 row framing retained v1 numeric maxima and undercounted maximum authority and
  adapter transcripts by 1,920 and 320 bytes respectively.
- CLI/resource / am22-cli-review: `block` — it confirmed the framing defect, proved
  `:(literal)foo` was interpreted as Git pathspec magic and produced an empty patch, and
  showed that an opened descriptor cannot detect a later pathname replacement as amendment
  25 required.

The provider lane, amendment-25 quoted-path domain, safe-path file-type pairs, and
four-independent/two-derived scratch model passed their assigned attacks. Budget and
core-fit lenses were not run. Production remained unopened.

## Superseded authenticated-source review

**Reviewed revision:** `79a4fe9f3e45feac2214509fc2dea17254295859`

- semantic/DAG / a26-design-consistency: `block` — the direct script necessarily executed
  before its own v2 check, and the host-pinned interpreter/standard-library profile had no
  exact identity, so authenticated source did not identify all executed semantics.
- workflow/provider / r19-semantic-design: `approve` — v2 receipt flow, native approval,
  literal pathspecs, attempt joins, and dormant/canary/receipt/activation ordering remained
  coherent.
- CLI/resource / am22-cli-review: `block` — adapter framing and payload aggregate retained
  impossible independent `+1` fixtures; the direct script lacked an external trust root;
  and removing `__file__` did not prevent known-path filesystem observation after open.

Literal magic-path Git probes, revised v2 arithmetic, safe unquoted-path classes, and the
four-independent/two-derived scratch ledger passed. Budget and core-fit lenses were not run.
Production remained unopened.

## Superseded external-root review

**Reviewed revision:** `cf2dd89520caec1bb855eb8f7c53516705affaf6`

- semantic/DAG / a26-design-consistency: `block` — strict result/receipt schemas could not
  carry launcher/runtime/execution identities, the local installer self-vouched, and the
  launcher claimed to attest native mappings that existed only after exec.
- workflow/provider / r19-semantic-design: `block` — the first canary required the receipt it
  was meant to create, local launch lacked a host root, and exact artifact/receipt fields for
  the new identities were absent.
- CLI/resource / am22-cli-review: `block` — launcher/runtime policy JSON types were open,
  result v1 contradicted new digest fields, and a staged local launcher could be replaced
  before its first instruction.

The sealed mount/pivot/descriptor sequence, literal Git pathspecs, v2 arithmetic, and derived
adapter totals passed their assigned controls. Budget and core-fit lenses were not run.
Production remained unopened.

## Superseded closed-execution review

**Reviewed revision:** `c58b038c0e47e10ae0f2c495b1b2100ff3937fb3`

- semantic/authority / a26-design-consistency: `block` — activated production re-fetched a
  retention-bounded launcher artifact forever while atomic activation removed the legacy
  path it claimed would remain available after expiry.
- workflow/provider / r19-semantic-design: `block` — the provider artifact object did not
  prove which rerun attempt produced it, and independently confirmed the post-activation
  expiry gap. Result v2, canary/receipt v3, publication v2, first-canary sequencing, and the
  local/core trust distinction otherwise joined coherently.
- CLI/resource / am22-cli-review: `block` — ordinary release CPython could not encode its
  empty ABI flags; the valid launcher policy could not reach its promised 64 KiB boundary;
  a same-fd verifier allowed in-place inode mutation before exec; and the exact argument
  vector omitted `argv[0]`. It found no further contradiction in the four stored/two
  derived counters, literal pathspecs, or sealed-root budget composition.

All three reviews were read-only and named the same immutable SHA. Budget and core-fit
lenses were not run, and production remained unopened.

The empty ABI observation was reproduced under the fixed interpreter flags:

```text
$ python3 -I -S -B -X utf8 -c 'import sys,sysconfig; print(repr(sys.abiflags), repr(sysconfig.get_config_var("ABIFLAGS")))'
'' ''
```

Independent canonical-JSON probes measured the amendment-28 maximum at 519 bytes including
LF and the amendment-29 complete-argv/sealing-capability maximum at 578 bytes including LF.
The revised 1,024-byte raw ceiling therefore is not represented as a valid-schema boundary.

## Superseded durable-launcher review

**Reviewed revision:** `305fbadf783e0bb2827843cc57de1790215fd9bd`

- semantic/authority / a26-design-consistency: `approve` — first-instruction trust, sealed
  memfd execution, durable Git payload identity, V4 schema joins, fail-closed lifecycle, and
  unchanged POC classifications were coherent. It independently reproduced the 578-byte
  launcher-policy maximum.
- workflow/provider / r19-semantic-design: `block` — the first post-activation restack can
  have an O older than Gate 2 and therefore no launcher if source selection uses O; a future
  dormant Gate 2 also overwrites fixed active launcher/manifest/receipt locations before
  its Gate 3 switch. The build-attempt job/log/API join itself was feasible.
- CLI/resource / am22-cli-review: `block` — it independently reproduced the pre-Gate-2 O
  ambiguity, found `launcher_source` required in a nonexistent per-scenario bundle, and
  found the new build-job log scan without its own byte/token/deadline grammar. Empty ABI,
  memfd/exec feasibility, Git patch forms, policy maxima, and scratch arithmetic passed.

All three reviews were read-only and named the same immutable SHA. Budget and core-fit
lenses were not run. Production remained unopened.

The revised outer launcher-publication marker arithmetic was executed directly:

```text
$ python3 - <<'PY'
p=b'AGENTFOLD_REF_UPDATE_LAUNCHER_PUBLICATION_V2 '
print(len(p), (4*65536+2)//3, len(p)+(4*65536+2)//3+1)
PY
45 87382 87428
```

## Superseded immutable-slot review

**Reviewed revision:** `6e5978cdf17207b62365abf75e37488e6cef1481`

- semantic/authority / a26-design-consistency: `block` — the retained O/N/evaluator policy
  equality contradicted pre-Gate-2 migration; one mixed fd could not enforce T/candidate
  roles; live workflow bytes were not protected by the active adapter policy; launcher
  publication lacked fields required by its equality join; and receipt landing used the
  rejected records-only trust class.
- workflow/provider / r19-semantic-design: `block` — selector `adapter_policy` formed a
  digest self-reference through its own activation patch, independently confirmed the
  pre-Gate-2 policy contradiction, and restored receipt landing to a tested core-data PR.
  Provider attempt/job/log/artifact APIs and additive slot ordering otherwise remained
  feasible.
- CLI/resource / am22-cli-review: `block` — the slot had no exact manifest locators or
  complete source-extraction budget, the fd-5 role table was undefined, and the 87,428-byte
  LF cap contradicted a required 87,429-byte maximum CRLF line. It reproduced all Git
  command forms and the positive selector/tree/batch/token arithmetic.

All three reviews were read-only and named the same immutable SHA. Budget and core-fit were
not run. Production remained unopened.

The amendment-31 T-only and deployment totals were recomputed directly:

```text
$ python3 - <<'PY'
authority_framing=30+2+32*30+8192
authority_payload=4194304
deployment_payload=8192+1024+2097152+65536+65536+authority_payload+27262976+16777216
print(authority_framing, authority_framing+authority_payload)
print(deployment_payload, deployment_payload+54*(79+79+1))
PY
9184 4203488
50471936 50480522
```

The complete tested-commit/split-FD launcher policy was independently encoded at 642 bytes
including LF; substituted maximum-width arguments occupy 351 bytes including NULs.
The pointer-only active-selector V2 canonical vector was independently encoded at 184 bytes
including LF.

## Superseded T-only split-object review

**Reviewed revision:** `33b52f95e166ed74067f5d9427e9a24c5bf65d27`

- semantic/authority / a26-design-consistency: `block` — initial and upgrade canaries could
  not satisfy a target projection that Gate 3 had not yet installed in A, and the reduced
  control ODB charged authority blobs but not its mandatory T commit/tree objects.
- workflow/provider / r19-semantic-design: `block` — code executing from A could skip its
  own projection check and forge success because no production verifier existed outside A;
  it independently found the uncharged T graph and a breaking switch that could strand an
  old edge permanently. Unsupported historical data can also occur in an intermediate
  commit, so universal pre-graph refusal was false.
- CLI/resource / am22-cli-review: `block` — the reduced ODB omitted T graph storage; the one-
  GiB scope could not contain the admitted evaluator plus two Git children; active projection
  omitted `--literal-pathspecs`; role registries were not literal schemas; and result-v2
  still carried the obsolete three-source policy limits.

All three reviews were read-only and named the same immutable SHA. Budget and core-fit were
not run, and production remained unopened.

The amendment-32 sealed-bundle and launcher values were recomputed directly:

```text
$ python3 - <<'PY'
import json
argv=['--authority-manifest-fd=3','--runtime-manifest-fd=4',
      '--authority-bundle-fd=5','--candidate-git-dir-fd=6',
      '--old=<full-oid>','--new=<full-oid>']
actual=sum(len(x)+1 for x in ['agentfold-ref-update-launcher',*argv])
actual += 2*(64-len('<full-oid>'))
print(30+2+32*30+8192+4194304, actual)
PY
4203488 271
```

Removing the 29-byte canonical tested-commit array member and replacing the control-Git
spelling by the one-byte-longer bundle spelling changes the launcher-policy maximum from
642 to 614 bytes including LF. The two phase projections contain at most nine rows, so their
tree transcript cap is `9*78 + 4,096 = 4,798` bytes.

The amendment-22 scratch arithmetic was executed directly:

```text
$ python3 -c 'raw=134217728; rows=256; n=raw+14*rows; loose=n+(n>>12)+(n>>14)+(n>>25)+13*rows+4095*rows; cats=[301989888,loose,16777216,2097152,4194304,2097152]; print(loose); print(sum(cats))'
135313924
462469636
```

The amendment-25 source-derived maxima were recomputed directly:

```text
$ python3 -c 'b=134217728;a=134217728;m=33554432; q=lambda n:n+(n>>12)+(n>>14)+(n>>25)+27+4095; working=b+a+m; loose=4*q(m)+252*q(0); print(f"working={working}"); print(f"loose={loose}"); print(f"sum={working+loose+16777216+2097152+4194304+2097152}")'
working=301989888
loose=135313924
sum=462469636
```

The amendment-26 v2 maxima were recomputed directly:

```text
$ python3 -c 'authority_framing=3*(30+2+32*30+8192); authority_payload=12582912; adapter_framing=39+32+2+16*30+4096; adapter_payload=27262976; print(f"authority_framing={authority_framing}"); print(f"authority_total={authority_framing+authority_payload}"); print(f"adapter_framing={adapter_framing}"); print(f"adapter_total={adapter_framing+adapter_payload}")'
authority_framing=27552
authority_total=12610464
adapter_framing=4649
adapter_total=27267625
```

## Superseded bounded-materialization review

**Reviewed revision:** `a8f52f86e356c8f35aff9d62eebd268b6342c6a0`

- semantic/DAG / a15-semantic-review: `approve` — size/parser/quota failures remained
  infrastructure-unavailable and could not alter Strategy A or hide candidate tree bytes.
- workflow/provider / r19-semantic-design: `block` — the exact Git command emits no `index`
  line for a pure mode change, while the parser required one despite admitting that row.
- CLI/resource / am22-cli-review: `block` — it independently reproduced the pure-mode
  contradiction, proved the current test runner has no promised timeout/output cap, and
  showed aggregate +1 is unreachable independently when the aggregate is the sum of category
  limits.

Budget and core-fit lenses were not run. Production remained unopened.

## Superseded preserved-status design review

**Reviewed revision:** `92a5f3e61fd3e03009813bf6e49a842e422bf25f`

- semantic/DAG/executable / a15-semantic-review: `block` — every-O row coverage contradicted the accepted empty-row fast-forward transaction and ordinary ownership.
- budgets/transaction/composition / a15-budget-review: `approve` — retained memory, graph/policy arithmetic, child cleanup, accepted-delivery handling, and separate ordinary composition were closed for the stated boundary.
- workflow/provider/human / r19-semantic-design: `block` — canaries were not bound to activated adapter bytes, and the required local authority-bearing capture wrapper had no executable contract or implementation gate.
- core-fit / final-corefit-panel: `approve` — the observer remained provider/agent/repository neutral, repository-local, optional-adapter, and free of user-global or third-party core coupling.
- CLI/contracts/testability / final-cli-panel: `block` — object type was unknowable before an object read, fast-forward rows conflicted, and identity/evidence hash inputs were not byte-framed.

The three-to-two panel rejected the revision. No production implementation began from it.

## Superseded canary-bound design review

**Reviewed revision:** `2f43c7d024b046600ded34c2e0b93430ae29d0ba`

- semantic/DAG/executable / a15-semantic-review: `approve` — two-stage endpoint preflight, empty-row fast-forward, divergent POC mapping, exact identity framing, and removal of the open public evidence digest were semantically closed.
- workflow/provider/human / r19-semantic-design: `block` — the digest omitted full workflow execution semantics and the activation candidate could replace an unauthenticated, unpinned canary receipt.
- CLI/contracts/testability / final-cli-panel: `block` — the nested wrapper could not contain separately grouped grandchildren or its true memory peak, adapter framing was not exact, fast-forward counter membership conflicted, and activation omitted live public contracts.

The revision was rejected after two independent blocks; the remaining lenses were not run.
No production implementation began from it.

## Superseded closed-receipt design review

**Reviewed revision:** `7a6eec531026e5c59af4a7a2affd0f07952483d7`

- semantic/DAG/executable / a15-semantic-review: `approve` — classifier and tagged receipt states remained separate and POC-equivalent; exact activation did not authorize an authority change.
- workflow/provider/human / r19-semantic-design: `block` — pending schema confused run status with nullable job conclusion and full-tree equality contradicted permitted lifecycle record updates.
- CLI/contracts/testability / final-cli-panel: `block` — scalar/count/reason limits, artifact name, activation manifest/patch bytes, and record-tree comparison were not executable.

The revision was rejected after two independent blocks; the remaining lenses were not run.
No production implementation began from it.

## Superseded direct-evaluator design review

**Reviewed revision:** `c9608fcc191072fbe1bcea27313384eba8e47b9b`

- semantic/DAG/executable / a15-semantic-review: `approve` — direct in-process parity, endpoint/fast-forward/divergent behavior, two-arm proofs, identity framing, counters, and policy binding remained POC-equivalent.
- workflow/provider/human / r19-semantic-design: `block` — the receipt could not represent required no-observation/pending scenarios and did not close numeric fixture/fork topology identity.
- CLI/contracts/testability / final-cli-panel: `block` — batch descriptors were undercounted, receipt JSON/schema was open, and path-level activation permission allowed unrelated invariant/test edits.

The revision was rejected after two independent blocks; the remaining lenses were not run.
No production implementation began from it.

## Superseded observer-only design review

**Reviewed revision:** `a79425b7de1234b390ed0c495b6ed774a6b32c51`

- semantic/DAG/scope / r19-semantic-design: `approve` — publisher authority was fully withdrawn; Linux-gated historical paths, direct/synthetic candidates, handover incarnations, and ordinary roles remained POC-equivalent.
- budgets/transaction/composition / r17-production-seam-audit: `block` — the blanket remote-helper prohibition contradicted the trusted adapter's required bounded anonymous HTTPS fetch/upload-pack transport.
- workflow/adapter/human: `not run` — the assigned reviewer exhausted its execution quota before returning a verdict.

The panel stopped after one concrete block. The two remaining lenses were not run, and no
production implementation began from this revision.

## Superseded final observer-only design review

**Reviewed revision:** `b6966a34252184f6245d346ecf6904fa1cffcfc6`

- semantic/DAG/executable / final-semantic-panel: `approve` — exact two-arm semantics, role-specific ordinary projections, Linux continuity gate, and bounded read-only adapter transport matched the accepted POC.
- budgets/transaction/composition / final-budget-panel: `approve` — arithmetic, pre-exec containment, transaction ordering, arenas, cleanup, and zero partial output/writers were closed for the stated scope.
- workflow/provider/human / final-workflow-panel: `approve` — common cycles and provider observation states remained honest; publication stayed external and the optional adapter remained separately gated.
- core-fit / final-corefit-panel: `approve` — observer authority was agent/provider/repository substitutable, made no user-global writes, and kept the GitHub adapter optional and policy-free.
- CLI/contracts/testability / final-cli-panel: `block` — Linux-gating ordinary range broke macOS integration, core/workflow retirement could not land independently, duplicate/output/exit contracts were open, and new authority modules escaped the Git-spawn guard.

The four-to-one panel rejected the revision. No production implementation began from it.

## Superseded sealed-publisher design review

**Reviewed revision:** `56b73d57cd1564c510d6a331793b6b9f5aa4beed`

- semantic/DAG + object view / r19-semantic-design: `block` — native macOS ordinary range availability contradicted the mandatory historical-child memory gate; sealed object semantics otherwise preserved O/N roles.
- budgets/transaction/composition / r17-production-seam-audit: `block` — publication had no pack/network/disk/process/resource profile, failed temp repositories accumulated without a numeric cleanup contract, and macOS ordinary range remained contradictory.
- workflow/adapter/human / r20-workflow-design: `block` — recursive alternates escaped the validated source ODB, macOS had no executable prepublication Linux path, failure/auth cleanup was open, and redirects remained enabled.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded executable-enumeration design review

**Reviewed revision:** `6643bdc0c68282420b9778badfd425d68810a900`

- semantic/DAG + command parity / r19-semantic-design: `approve` — direct N and synthetic H prefix enumeration, unchanged live and prior incarnations, continuity DAG, merge-base/shallow grammars, and raw/retained roles were executable and POC-equivalent.
- budgets/transaction/composition / r17-production-seam-audit: `block` — continuity and policy children could allocate across unbounded history before first output because only ordinary children had an address-space ceiling.
- workflow/adapter/human / r20-workflow-design: `block` — `remote.origin.vcs` could select an arbitrary remote helper after the named remote's URL passed validation; receive-pack transport configuration was likewise open.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded attempt/activation-contract review

**Reviewed revision:** `7e41dc7a1a1a916060770fde03bbe821ada2ce64`

- semantic/DAG / a15-semantic-review: `approve` — the two-arm graph, old-side continuity,
  new-side authority, unique N frontier, fast-forward empty rows, identity digest, and
  accepted-POC equivalence remained coherent.
- workflow/provider / r19-semantic-design: `block` — completed rows did not bind each
  scenario's run attempt, job, raw event, and result artifacts; the public-fork hold excluded
  GitHub's native `action_required` forms.
- CLI/resource / final-cli-panel: `block` — the exec-status pipe had neither a cumulative
  frame grammar nor +1 behavior, and the 16 MiB patch bound could not fit the mandatory
  4 MiB aggregate adapter transcript.

The panel stopped after two independent blocks. Budget and core-fit lenses were not run,
and no production implementation began from this revision. Official GitHub REST material
was then re-read: workflow runs expose separate status/conclusion and `run_attempt`, the API
has an attempt-specific run endpoint and public-fork approve endpoint, and provider status
filters include `action_required`/`waiting`/`pending`/`requested`.

The amendment-21 arithmetic was executed directly:

```text
$ python3 -c 'import base64; n=65536; print(26*1024*1024, 26*1024*1024+4329, len(base64.urlsafe_b64encode(b"x"*n).rstrip(b"=")))'
27262976 27267305 87382
```

## Superseded candidate-complete ordinary design review

**Reviewed revision:** `aa872dfb6b27b864b2e9b12f9a542c834c86efb7`

- semantic/DAG / r19-semantic-design: `block` — the literal candidate-tree `ls-tree` command used unsupported glob pathspec magic and exited 128 on Git 2.55.0; a plain wildcard returned no rows.
- budgets/transaction/composition / r17-production-seam-audit: `block` — candidate-tree path bytes could not reach the same cap as framed raw bytes; continuity graph, merge-base, and shallow/chunk limits retained unreachable exact boundaries; and successful batch readers could remain alive into ordinary work.

The panel stopped after two independent blocks. The three remaining lenses were not run,
and no production implementation began from this revision.

## Superseded pre-output-memory and literal-transport design review

**Reviewed revision:** `8ef4cf2b5bf7c99376edb9232315905cb5201e19`

- semantic/DAG + hostile-config / r19-semantic-design: `block` — literal URL bypassed remote fields but the original local config still executed credential helpers and applied HTTP transport policy.
- budgets/transaction/composition / r17-production-seam-audit: `block` — macOS could not install the promised 512 MiB address-space ceiling, byte-level OOM controls were invalid for page-granular limits, and original local Git config remained visible.
- workflow/adapter/human / r20-workflow-design: `block` — hostile local credential helpers ran before askpass and inherited TLS/proxy environment could redirect or weaken the validated HTTPS transport.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded split-transaction design review

**Reviewed revision:** `927a48825962d0b3923751f0e3ce152f3806b697`

- semantic/DAG / r18-semantic-design: `approve` — policy ordering, fast-forward ownership, two-arm divergence, boundary, persisted, and mixed-root fixtures matched the accepted POC.
- budgets/transaction/composition / receipt-contract: `block` — the 12 MiB hash-input cap omitted non-empty domain/path/length framing and made its exact maximum unsatisfiable.
- workflow/adapter/human / r18-workflow-design: `block` — production fork credentials, conflicted lane availability, ordinary B, closed same-repository pushes, and fast-forward human workflow were incorrect or incomplete.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded bounded-ordinary design review

**Reviewed revision:** `d075666935d1e9cabf28cc40321584137f0b1828`

- semantic/DAG / r18-semantic-design: `block` — one untyped ordinary map could not preserve distinct queue, task-message, symmetric-diff, root, activation, handover, and synthetic-candidate revision projections.
- budgets/transaction/composition / receipt-contract: `block` — several graph limits were unreachable, activation/root work remained open, and ordinary result/output/helper work was not transactional or bounded.
- workflow/adapter/human / r18-workflow-design: `block` — approval-pending fork runs and follow-tags/multiple-pushurl publication effects were missing.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded role-specific ordinary design review

**Reviewed revision:** `6ea2d284a882daebae6f043ba4762bbd80b3b6ea`

- semantic/DAG / r18-semantic-design: `block` — path-history admission omitted unchanged live handovers, so a pre-range v1 mutation followed by an unrelated candidate delta could become falsely clean.
- budgets/transaction/composition / receipt-contract: `block` — side-marker bytes were undercounted; two byte boundaries were unreachable; path and child caps contradicted each other; the retained snapshot had no aggregate budget; and tracked pre-push hooks could compose an exact publication.
- workflow/adapter/human / r18-workflow-design: `approve` — source-distinct trust, no-observation states, anonymous fork transport, attempts, canary cleanup, and configuration-closed leases were coherent.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded observable-provider design review

**Reviewed revision:** `10e2d6a1cf2e7983301cdb10dd9ba1dbd976de81`

- semantic/DAG / r18-semantic-design: `approve` — graph, policy, fast-forward, creation, root competition, and persisted/disappeared fixtures remained POC-equivalent.
- budgets/transaction/composition / receipt-contract: `block` — derived-counter +1 promises were unreachable and creation `root:N` used an unbounded buffered ordinary history traversal.
- workflow/adapter/human / r18-workflow-design: `block` — same-repository SHA-like suppression, provider-visible trust aliasing, and creation trust labeling remained incorrect.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded per-event-lane design review

**Reviewed revision:** `22e1c00ce0fcec05da9ea6842db9d31128e2571a`

- semantic/DAG / r18-semantic-design: `approve` — two-arm, persisted/disappeared, fast-forward, policy mismatch, ordinary independence, and mixed-root results matched the accepted POC.
- budgets/transaction/composition / receipt-contract: `block` — total hash +1 was unreachable, framing was not byte-canonical, creation lost root-range protection, and provider absence states were open.
- workflow/adapter/human / r18-workflow-design: `block` — candidate-controlled push runs were called trusted, provider absence was mapped to impossible conclusions, and update/deletion refspecs were incomplete.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded edge-scoped design review

**Reviewed revision:** `db720d3321ee25f09c82def46d77fd418735e904`

- semantic/DAG / r18-semantic-design: `approve` — fresh fixtures matched the accepted POC and its complete 167/167 scenario, 34/34 damage-control, and 4/4 alias suite.
- budgets/transaction/composition / receipt-contract: `block` — integrated candidate code and the pinned trusted evaluator did not bind one authority-policy version.
- workflow/adapter/human / r18-workflow-design: `block` — default-branch workflow authority, a closed PR matrix, fixture installation, cleanup authentication, bounded run discovery, and the concrete manual lifecycle remained incomplete.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded policy-bound design review

**Reviewed revision:** `0a488cc38bf772982d06a6519f828c6cc9bbd43f`

- semantic/DAG / r18-semantic-design: `block` — fast-forward policy verification, clean return, and ordinary ownership had contradictory ordering.
- budgets/transaction/composition / receipt-contract: `block` — policy mismatch starved ordinary checks and the policy bootstrap lacked logical-source budgets and parity counters.
- workflow/adapter/human / r18-workflow-design: `block` — base/head repository identities, closed and SHA-like fork events, retention limits, fork fixture relationships, run attempts, and atomic first publication were incomplete.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.
