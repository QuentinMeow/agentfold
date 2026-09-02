# Cross-arm replay witness proof of concept

## Result

**VERIFIED:** a 30-row real-Git matrix separates four observations about an action
X. Unique arm-local births (U) catch damage that endpoint equality (E) misses.
In this deliberately untyped matrix, matching the canonical birth state (B)
distinguishes one object-state case that generic U accepts. That does not show B
adds authority beyond a production U that validates AgentFold identity, lifecycle,
binding, deletion, and mutation semantics. The normalized governed-path birth delta
(D) adds no
demonstrated provenance protection. It blocks seven rows that B accepts because it
couples X to neighboring queue bytes or birth-parent count, yet it still accepts
independent equal creation, forged metadata, changed series order, and the
information-limit pair.

This POC therefore retains U and B only as diagnostics for the Git properties they
actually establish. It does not select between them for production; the typed
production-contract POC owns that decision. D does not survive as a production
authority candidate. None of E, U, B, or D proves replay intent or permits a queue
finding to be suppressed.

This POC changes no production code. It reads immutable Git objects with
--no-replace-objects; authors, messages, trailers, branch labels, pull-request state,
patch-id, and operator claims are never authority.

## Decision matrix

| Candidate | Exact claim when it matches | Useful protection observed | Counterexample / cost | Decision |
|---|---|---|---|---|
| E endpoint equality | O and N each contain exactly one canonically located X with equal mode, object kind, size, and bytes | Catches O-only loss, an arbitrary untrusted move, and endpoint multiplicity | Accepts delete/recreate and an inherited-then-deleted merge arm | Damage-only baseline |
| U unique arm-local origin | Each C..tip arm has exactly one birth of X; the live origin reaches the tip without deletion on an inherited path; no commit has multiple normalized occurrences | Blocks delete/recreate and inherited-then-deleted history that E accepts | Accepts different birth bytes that later converge, independent creation, transient binding damage, and the intent twins | Retain as an arm-history diagnostic |
| B matched canonical birth state | U matches and the two birth blobs have equal mode, kind, size, and SHA-256 of exact bytes | In this untyped matrix, blocks the unequal birth restored to equal endpoints | Equal bytes can be created independently; corrected typed U may reject that shape first; copied metadata and identical-object intent twins still match | Retain only as a secondary object-state diagnostic; this POC does not select it |
| D normalized governed birth delta | B matches and the sorted per-parent normalized queue/ tree deltas at both births are byte-equal, including parent multiplicity | Ignores unrelated non-queue changes and parent order | Seven extra blocks are coupling to squash grouping, queue neighbors, support tree entries, or parent shape; independent creation and reordering still match | Reject as authority; no material provenance gain over B |

B and D are stricter predicates than U; a D match never repairs a failed
B or U. “Retain” means the observation can help a person diagnose a finding. It
does not mean the reconciler may trust the observation as intent.

## Exact immutable inputs

The classifier receives only:

1. one local Git object-and-graph read view, including its object format,
   alternates, and shallow boundary;
2. full commit object IDs C, O, and N;
3. the governed prefix tuple ("queue/",);
4. the target canonical key queue/actions/action.md;
5. the two action roots queue/needs-agent/{requests,retries}/;
6. the ordered, closed prefix vocabulary future-blocking-, non-blocking-,
   pick-up-, and retry-; and
7. the exact limits max_commits=256, max_unique_blob_bytes=4,194,304,
   max_command_output_bytes=4,194,304, and max_graph_line_bytes=65,536,
   except the resource-refusal fixture's declared max_commits=3.

Before comparison, the classifier removes inherited GIT_* routing, disables global
and system Git config and optional locks, and requires a non-shallow repository. It
then requires all three inputs to be readable commits,
requires git merge-base --all O N to return exactly [C], and requires X to be
absent at C. Missing objects, a wrong or non-unique base, an invalid object ID,
or a crossed resource limit returns unavailable; it never substitutes partial
evidence.

The synthetic paths and prefixes are POC inputs, not a proposal to change AgentFold's
queue schema. In particular, the normalizer does not treat a file's Action: or
Binding: text as an identity assertion.

## Exact normalization and D

For paths directly below either action root, the normalizer repeatedly removes only
the four listed leading prefixes and maps the result to queue/actions/<basename>.
It leaves every other governed path byte-for-byte unchanged. It rejects two raw
paths that map to the same normalized path. UTF-8 paths are sorted by their encoded
bytes.

For each direct parent P of the unique birth commit H, D reads the recursive
queue/ trees at P and H. It emits one record for every changed normalized path:

~~~text
path,
before = null | {mode, kind, object, size, sha256, exact bytes as hex},
after  = null | {mode, kind, object, size, sha256, exact bytes as hex}
~~~

Blob entries carry both their exact bytes and a display digest. Governed gitlinks
carry mode, kind, and target object ID even when that target is not stored in the
superproject. No non-tree entry is silently dropped.

Records are sorted by normalized path. The complete per-parent record lists are
sorted by their canonical JSON bytes, so swapping merge parents is invariant. Equal
lists are not deduplicated, so changing one parent to two parents changes the
witness. The comparison is exact over canonical JSON encoded with ASCII,
sorted keys, no insignificant whitespace, and no locale-dependent formatting.

This construction makes the limit visible:

- If D contains only the creation of X, it carries the same cross-arm fact as B.
- If D contains more, those neighboring changes and parent multiplicity are
  reproducible context, not proof that one birth replayed the other.
- If D expanded to the full commit, even unrelated app/ work would block. The
  full-commit-patch negative control executes that failure.
- If D expanded from the birth edge to the whole series, squash and reordering would
  make the chosen serialization policy, rather than provenance, decide the result.

## Common scenario table

Match means the named Git predicate holds. Block means it does not. Unavailable
means the bounded read could not complete. The “fixture observation” column describes
how the POC constructed the case; it is not classifier evidence.

| Scenario | E | U | B | D | Fixture observation |
|---|---|---|---|---|---|
| Normal restack | match | match | match | match | scoped action birth replays over unrelated base work |
| O-only loss | block | block | block | block | N omits X |
| Delete/recreate | match | block | block | block | equal endpoint bytes hide two births on the new arm |
| Transient mutation restored | match | match | block | block | the new arm begins with different bytes, then converges |
| Binding removal/restoration | match | match | match | match | equal births and tips hide a temporary binding loss |
| Collisions/multiplicity | block | block | block | block | two timing spellings normalize to X |
| Neutral merge arms | match | match | match | match | a merge parent that never carried X stays neutral |
| Inherited-then-deleted arm | match | block | block | block | a parent inherited and deleted the live origin before rejoining |
| Exact cherry-pick | match | match | match | match | exact scoped patch equality is observable, intent is not |
| Squash | match | match | match | block | one arm groups support bytes with the birth |
| Arbitrary rename/move | block | block | block | block | no trusted mapping connects the new basename to X |
| Retries/pickups | match | match | match | match | the closed path vocabulary maps both locations to X |
| Parent-order invariance | match | match | match | match | sorted two-parent birth deltas are equal |
| Unreadable history | unavailable | unavailable | unavailable | unavailable | a depth-one view lacks C and O |
| Resource refusal | unavailable | unavailable | unavailable | unavailable | ten arm commits exceed the fixture's exact limit of three |
| Unrelated outside same commit | match | match | match | match | D excludes app/unrelated.txt |
| Unrelated governed same commit | match | match | match | block | D couples X to queue/unrelated.txt |
| Timing-prefix move | match | match | match | match | the closed normalizer preserves X |
| Merge birth versus linear birth | match | match | match | block | D retains one versus two birth parents |
| Changed parent shape | match | match | match | block | D retains two versus three birth parents |
| Equivalent bytes created independently | match | match | match | match | no candidate can prove which act caused equal bytes |
| Forged/copyable metadata | match | match | match | match | equal author/message/trailer claims are ignored |
| Extra queue identity | match | match | match | block | D observes a second action created beside X |
| Support artifacts | match | match | match | block | D observes different queue/evidence/ bytes |
| Cross-C side origin | match | block | block | block | a merge parent carries a distinct origin from before C |
| Cross-C import, delete, recreate | match | block | block | block | U remembers the imported outside-C origin even after deletion and a later local birth |
| Governed gitlink | match | match | match | block | D observes a queue/support gitlink beside X |
| Reordering | match | match | match | match | support moves across the birth edge; birth-only D omits order |
| Intent twin: declared replay | match | match | match | match | external story says replay |
| Intent twin: declared independent | match | match | match | match | the exact same objects receive the opposite external story |

## Information-theoretic limit

The two intent-twin rows are two evaluations of the exact same object database, graph,
C, O, N, governed scope, target key, normalizer, and limits. The only difference
is an explicitly off-object fixture label: declared-replay versus
declared-independent. Both rows emit observation digest:

~~~text
sha256:8a984b819a5fba802f99f9dc34f3041df98f39f89c922b23945c6d19f5b929b8
~~~

Assume an O/N classifier is a function f(I) of those immutable inputs. The twins
have the same I, so substitution gives f(I) = f(I). Returning “replay” for one
and “independent” for the other would require an input outside the trusted object
view. Therefore no O/N-only rule—including D, full patches, patch-id, messages,
or trailers—can distinguish their intent. The POC checks both input observation
digests for equality and fails if they diverge.

The independent-bytes row is the practical counterexample: two distinct birth commits
produce equal normalized deltas without a cherry-pick. The forged-metadata row adds
the same Replay-Approved: true trailer to both independently constructed commits.
All four candidates still match.

## Raw verified totals

The canonical clean stream contains 30 scenario records plus one summary record:

~~~json
{"candidate_totals":{"B":{"block":8,"match":20,"unavailable":2},"D":{"block":15,"match":13,"unavailable":2},"E":{"block":3,"match":25,"unavailable":2},"U":{"block":7,"match":21,"unavailable":2}},"d_blocks_while_b_matches":7,"damage_control":null,"failed":0,"failure_messages":0,"information_limit_pairs":1,"passed":30,"schema":"agentfold-replay-oracle/v2","summary":"replay-oracle-poc","total":30}
~~~

The seven rows where D blocks after B matches are squash, unrelated governed
change, merge birth versus linear birth, changed parent shape, extra queue identity,
support artifacts, and a governed gitlink. The fixtures know those seven constructions preserve X, but
that knowledge is off-object. Git supplies no fact that turns those blocks into
provenance protection. Conversely, D accepts independent equal birth, copied
metadata, and changed ordering. The observed result is therefore extra false blocks
and complexity, not a demonstrable authority improvement.

## Replayable commands

Run the complete matrix from the repository root:

~~~sh
python3 -m py_compile \
  docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --self-test
~~~

Captured stderr:

~~~text
replay-oracle self-test: 29/29 scenario rows passed
~~~

Preserve every fixture in a new or empty directory:

~~~sh
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --self-test --fixtures-dir /tmp/new-empty-replay-oracle-fixtures
~~~

The command refuses a file or non-empty directory and never deletes it.

### Two-root, two-environment, reverse-order comparison

~~~sh
root_a="$(mktemp -d /tmp/replay-oracle-root-a.XXXXXX)"
root_b="$(mktemp -d /tmp/replay-oracle-root-b.XXXXXX)"
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONDONTWRITEBYTECODE=1 \
  python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --self-test --fixtures-dir "$root_a" --construction-order forward \
  > /tmp/replay-oracle-env-a.jsonl
PYTHONHASHSEED=777 LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=America/Los_Angeles \
  PYTHONDONTWRITEBYTECODE=1 \
  python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --self-test --fixtures-dir "$root_b" --construction-order reverse \
  > /tmp/replay-oracle-env-b.jsonl
cmp /tmp/replay-oracle-env-a.jsonl /tmp/replay-oracle-env-b.jsonl
sha256sum /tmp/replay-oracle-env-a.jsonl /tmp/replay-oracle-env-b.jsonl
wc -l -c /tmp/replay-oracle-env-a.jsonl /tmp/replay-oracle-env-b.jsonl
~~~

Captured result:

~~~text
485004f589df60f6065922f4c8d9faf195ca3e64d16752648d7da2647cce6483  /tmp/replay-oracle-env-a.jsonl
485004f589df60f6065922f4c8d9faf195ca3e64d16752648d7da2647cce6483  /tmp/replay-oracle-env-b.jsonl
      31   29705 /tmp/replay-oracle-env-a.jsonl
      31   29705 /tmp/replay-oracle-env-b.jsonl
~~~

cmp exited 0. This jointly varies absolute root, construction order, hash seed,
locale, and timezone. Scenario-local timestamps, forced Git locale/timezone, UTF-8
byte ordering, sorted collections, and canonical JSON make those variables absent
from the output.

### Named observed-red controls

Each command runs the same fixtures through one intentionally damaged rule. Exit 1
is expected:

~~~sh
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --negative-control endpoint-only
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --negative-control ignore-arm-history
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --negative-control trust-metadata
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --negative-control full-commit-patch
~~~

Captured results:

| Damaged rule | Exit | Red rows | Named evidence |
|---|---:|---:|---|
| Endpoint-only substitution | 1 | 12 | cross-C-import-delete-recreate changed from U=block to U=match |
| Ignored arm history | 1 | 12 | cross-C-import-delete-recreate changed from U=block to U=match |
| Trusted metadata | 1 | 1 | forged-copyable-metadata became unsafe-suppression |
| Full-commit patch equality | 1 | 4 | unrelated-outside-same-commit changed from D=match to D=block |

These are observed-red tests of the POC assertions. They are not production test
discovery evidence.

## Limits and non-establishment

- U follows the POC's path-based action key. It does not validate AgentFold's real
  action schema, typed legal birth state, binding rules, evidence lifecycle, or
  resolution authority. In particular, B's one extra block here is not evidence
  that it adds protection after corrected typed U.
- The arbitrary-move row blocks because no trusted object-only alias connects the
  two names. Adding a user-supplied alias would move the unresolved trust question
  into that input.
- The timing/retry normalizer is closed and collision-rejecting, but the experiment
  does not prove that its vocabulary matches production queue transitions.
- The byte budget is implemented and the commit-budget refusal is exercised. This
  run does not benchmark long histories or establish a production resource envelope.
- The shallow-object row proves fail-closed behavior for one missing-history shape,
  not every promisor, alternates, SHA-256, or object-corruption failure.
- The experiment does not establish a supplier-edge witness, queue deletion
  legitimacy, provider behavior, restack workflow capture, or integration with the
  reconciler.
- This mission fixes X absent at C and live at O/N. It intentionally does not rerun
  the parent task's different C-present inherited-deletion topology; that is outside
  this cross-arm birth-witness question.
- The fixture's intent labels explain construction only. They never become evidence
  or alter a candidate result.

The safe production posture remains: use these facts only to explain what Git shows.
If an authoritative real-edge proof is unavailable, the oracle reports
unavailable or a diagnostic mismatch and leaves the existing protection in place.
