# Verification — mine markdown co-change couplings and validate heading anchors

**Verified:** 2026-07-25 by claude — plan step 9, the gating experiment, at commit e52f68e

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Steps 1 through 8 landed in commit e52f68e without recording their own transcripts, so
the sections they owe — the anchor hole before-state, the two new `link-check` findings,
and the agents-budget check — are still missing. Step 10 owes them. Everything below is
from the gating-experiment session and is pasted from the terminal, including the results
that went against the design.

One re-run warning applies to every mining command below: the sweep and the two reports
in the middle sections were run **before** any ledger verdict existed. The 29 verdicts
recorded near the end of this file now suppress 29 pairs, so re-running those commands
today prints fewer candidates. The final section shows the post-verdict report so both
states are on the record.

## mining report on this repository — default floors, before any verdict

```
$ python3 automation/mine_cochange.py report
co-change candidates (advisory, provisional)
  floors      support >= 3 commit(s), confidence >= 0.80
  commit cap  40 changed path(s); 4 tangled commit(s) skipped
  history     200 commit(s) walked, 144 in scope, 180 file(s) seen
  scope       *.md outside history/, memory/decisions/, message-queue/needs-agent/retries/, tmp/
  stop-list   memory/index.md, roadmap/current-state.md, tasks/*/*/worklog.md
  dropped     20 pair(s) naming a path no longer tracked, 0 already in the ledger
  ledger      automation/cochange-ledger.txt -- 0 verdict(s), 0 rejected, rate n/a
  ranking     confidence desc, support desc, source path asc, target path asc

 1. templates/queue/review.md (11 commit(s))
    -> also review message-queue/AGENTS.md  conf 1.00  support 11
       because  harness: require authoritative source release
                harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                 +8 more shared commit(s)
 2. templates/queue/clarification.md (8 commit(s))
    -> also review message-queue/AGENTS.md  conf 1.00  support 8
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +5 more shared commit(s)
 3. templates/queue/decision.md (8 commit(s))
    -> also review message-queue/AGENTS.md  conf 1.00  support 8
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +5 more shared commit(s)
 4. templates/queue/request.md (7 commit(s))
    -> also review automation/AGENTS.md  conf 1.00  support 7
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +4 more shared commit(s)
 5. templates/queue/request.md (7 commit(s))
    -> also review handbook/git-workflow.md  conf 1.00  support 7
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +4 more shared commit(s)
 6. templates/queue/request.md (7 commit(s))
    -> also review handbook/human-action-guide.md  conf 1.00  support 7
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +4 more shared commit(s)
 7. templates/queue/request.md (7 commit(s))
    -> also review message-queue/AGENTS.md  conf 1.00  support 7
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +4 more shared commit(s)
 8. templates/queue/retry.md (7 commit(s))
    -> also review message-queue/AGENTS.md  conf 1.00  support 7
       because  harness: bind actions and reviews to exact boundaries
                harness: structurally triage conversation sources
                harness: replay current review actions
                 +4 more shared commit(s)
 9. docs/designs/risk-tiered-agent-guardrails.md (3 commit(s))
    -> also review roadmap/desired-state.md  conf 1.00  support 3
       because  docs: derive assurance from guard evidence
                harness: fold reviewed guardrail decisions
                Design risk-tiered agent guardrails
10. tasks/3_in-review/2026-07-23-first-class-message-queue/task.md (3 commit(s))
    -> also review message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md  conf 1.00  support 3
       because  queue: retire superseded PR 7 continuation
                harness: publish PR 7 review state
                harness: hand off derived assurance review

20 candidate(s) clear the floors; 10 shown, 10 dropped by the ranking above -- not "nothing else couples".
  see them all: --limit 0
provisional: 200 commit(s) of history, and the published work this borrows from discards the first few hundred change records as warm-up.
dismiss or keep one: mine_cochange.py accept <a> <b> | reject <a> <b> --reason "..."
```

Three of the design's own published mined numbers do not reproduce at this commit:

| Claim in the design | Measured here | Command |
|---|---|---|
| "about 39 directed candidates at support ≥ 3 and confidence ≥ 0.8" | **20** | the report above |
| review-template pair "at confidence 0.81 over 13 commits" | **1.00 over 11** | candidate 1 above |
| git-workflow "mining returns 8 partners" | **4** | the partner query below |

Part of the gap is scope — this tool drops the 20 pairs naming a path no longer tracked,
suppresses same-directory pairs, and stop-lists worklogs, none of which the design's
ad-hoc queries did. The rest is two days of extra history. Either way the design's mined
figures are not reproducible from its text and should not be cited as measurements.

## floor sweep

```
$ for c in 0.5 0.8 0.9; do for s in 3 5; do n=$(python3 automation/mine_cochange.py report --confidence $c --support $s --limit 0 --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["candidates"]))'); echo "confidence=$c support=$s candidates=$n"; done; done
confidence=0.5 support=3 candidates=52
confidence=0.5 support=5 candidates=43
confidence=0.8 support=3 candidates=20
confidence=0.8 support=5 candidates=18
confidence=0.9 support=3 candidates=11
confidence=0.9 support=5 candidates=9
```

Confidence is the whole control surface here and support is nearly inert: dropping the
confidence floor from 0.9 to 0.5 multiplies the candidate set by 4.7, while raising the
support floor from 3 to 5 removes 9 to 17% of candidates at every confidence. That is a
direct consequence of the noise structure described below — the couplings come from a
dozen broad commits, so almost everything that clears confidence 0.5 already has support
5 or more. The support floor is not doing the work the design assigned to it.

Ranking does not reorder as the floors move; the tool sorts by confidence, then support,
then paths, so a lower floor only appends. What changes is which pairs sit in the default
`--limit 10` window: at confidence 0.8 the visible window is eight queue-template pairs
plus two unrelated ones, and at 0.5 the same eight still lead.

## the two hot files, chosen on measured revision counts

```
$ python3 -c "
import sys; sys.path.insert(0, 'automation')
import mine_cochange as m
from collections import Counter
log = m.git('log','--root','-z','--name-status','--format=%x00%H%x00%s')
touched = Counter()
for subject, paths in m.walk_commits(log):
    if len(paths) > 40: continue
    files = sorted({p for p in paths if m.in_scope(p, m.SCOPE_EXCLUDES) and not m.stopped(p, m.STOP_LIST)})
    for f in files: touched[f] += 1
live = {n for n in m.git('ls-files','-z').split(chr(0)) if n}
for name, n in touched.most_common(15):
    print('%3d  %s%s' % (n, name, '' if name in live else '   [untracked now]'))
"
 19  automation/AGENTS.md
 17  tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md   [untracked now]
 14  tasks/3_in-review/2026-07-24-isolate-test-git-environment/verification.md
 14  handbook/git-workflow.md
 14  message-queue/AGENTS.md
 13  tasks/3_in-review/2026-07-24-isolate-test-git-environment/task.md
 12  message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md
 12  handbook/human-action-guide.md
 11  templates/queue/review.md
 10  message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md
  9  tasks/AGENTS.md
  8  tasks/3_in-review/2026-07-24-isolate-test-git-environment/design.md
  8  templates/queue/clarification.md
  8  templates/queue/decision.md
  7  roadmap/desired-state.md
```

The counter is the tool's own `touched` denominator, reproduced by importing its scope
predicates, so these are the exact revision counts its confidences are computed against.

Chosen: **automation/AGENTS.md (19)** and **message-queue/AGENTS.md (14)**.

- The task brief proposed `handbook/git-workflow.md` and `message-queue/AGENTS.md`. The
  measurement overrules the first half: `automation/AGENTS.md` has 19 in-scope revisions
  against git-workflow's 14, so it, not git-workflow, is the hottest durable contract.
  The design's "16 in-scope revisions" for git-workflow is also not what the tool
  measures at this commit.
- Four record files rank above or level with git-workflow — a task design at 17, a task
  verification at 14, a task record at 13, two human review items at 12 and 10. They are
  excluded as hot-file candidates because their coupling is an artifact of when they were
  written, which is the exclusion the design already states for record folders and which
  this tool's `--excludes` does not yet implement for `tasks/`.
- `message-queue/AGENTS.md` keeps its place on the tie at 14, because it is the target of
  the single case the design calls decisive. Picking the design's strongest example on
  purpose makes an unfavourable verdict harder to dismiss as a bad sample.

## every candidate coupling of the two hot files at confidence ≥ 0.5

The JSON was captured to a session scratch file outside the repository; `$C05S3` below
stands for that path exactly as it was run, and a reader may substitute any scratch path.
Re-running the capture today yields 23 candidates rather than 52, because the ledger
verdicts recorded further down now suppress 29 pairs.

```
$ C05S3=<session scratch dir>/c05s3.json
$ python3 automation/mine_cochange.py report --confidence 0.5 --support 3 --limit 0 --json > $C05S3
$ python3 -c "
import json
d=json.load(open('$C05S3'))
hot={'automation/AGENTS.md','message-queue/AGENTS.md'}
rows=[c for c in d['candidates'] if c['source'] in hot or c['target'] in hot]
print('total candidates', len(d['candidates']), '| touching the two hot files', len(rows))
for c in rows:
    role = 'OUT' if c['source'] in hot else 'IN '
    print('%s conf %.2f n=%2d  %s -> %s   (source revs %d)' % (role, c['confidence'], c['support'], c['source'], c['target'], c['source_commits']))
"
total candidates 52 | touching the two hot files 27
IN  conf 1.00 n=11  templates/queue/review.md -> message-queue/AGENTS.md   (source revs 11)
IN  conf 1.00 n= 8  templates/queue/clarification.md -> message-queue/AGENTS.md   (source revs 8)
IN  conf 1.00 n= 8  templates/queue/decision.md -> message-queue/AGENTS.md   (source revs 8)
IN  conf 1.00 n= 7  templates/queue/request.md -> automation/AGENTS.md   (source revs 7)
IN  conf 1.00 n= 7  templates/queue/request.md -> message-queue/AGENTS.md   (source revs 7)
IN  conf 1.00 n= 7  templates/queue/retry.md -> message-queue/AGENTS.md   (source revs 7)
IN  conf 0.86 n=12  handbook/git-workflow.md -> automation/AGENTS.md   (source revs 14)
IN  conf 0.86 n= 6  templates/queue/retry.md -> automation/AGENTS.md   (source revs 7)
IN  conf 0.83 n=10  handbook/human-action-guide.md -> message-queue/AGENTS.md   (source revs 12)
IN  conf 0.82 n= 9  templates/queue/review.md -> automation/AGENTS.md   (source revs 11)
OUT conf 0.79 n=11  message-queue/AGENTS.md -> templates/queue/review.md   (source revs 14)
IN  conf 0.75 n= 9  handbook/human-action-guide.md -> automation/AGENTS.md   (source revs 12)
IN  conf 0.75 n= 6  templates/queue/clarification.md -> automation/AGENTS.md   (source revs 8)
IN  conf 0.75 n= 6  templates/queue/decision.md -> automation/AGENTS.md   (source revs 8)
IN  conf 0.75 n= 3  templates/handover.md -> message-queue/AGENTS.md   (source revs 4)
OUT conf 0.71 n=10  message-queue/AGENTS.md -> handbook/human-action-guide.md   (source revs 14)
IN  conf 0.67 n= 6  tasks/AGENTS.md -> automation/AGENTS.md   (source revs 9)
IN  conf 0.67 n= 4  CONTRIBUTING.md -> automation/AGENTS.md   (source revs 6)
IN  conf 0.64 n= 9  handbook/git-workflow.md -> message-queue/AGENTS.md   (source revs 14)
OUT conf 0.64 n= 9  message-queue/AGENTS.md -> automation/AGENTS.md   (source revs 14)
OUT conf 0.64 n= 9  message-queue/AGENTS.md -> handbook/git-workflow.md   (source revs 14)
OUT conf 0.63 n=12  automation/AGENTS.md -> handbook/git-workflow.md   (source revs 19)
IN  conf 0.60 n= 3  templates/task/verification.md -> automation/AGENTS.md   (source revs 5)
OUT conf 0.57 n= 8  message-queue/AGENTS.md -> templates/queue/clarification.md   (source revs 14)
OUT conf 0.57 n= 8  message-queue/AGENTS.md -> templates/queue/decision.md   (source revs 14)
OUT conf 0.50 n= 7  message-queue/AGENTS.md -> templates/queue/request.md   (source revs 14)
OUT conf 0.50 n= 7  message-queue/AGENTS.md -> templates/queue/retry.md   (source revs 14)
```

Breadth of the whole candidate set, and the partner query the design's claim rests on:

```
$ python3 -c "
import json
d=json.load(open('$C05S3'))
c=d['candidates']
print('candidates at conf>=0.5 support>=3:', len(c))
gw=[x for x in c if x['source']=='handbook/git-workflow.md']
print('handbook/git-workflow.md as source:', len(gw), 'partner(s)')
for x in gw: print('   conf %.2f n=%d -> %s' % (x['confidence'], x['support'], x['target']))
files=set()
for x in c: files.add(x['source']); files.add(x['target'])
print('distinct files in the candidate set:', len(files))
"
candidates at conf>=0.5 support>=3: 52
handbook/git-workflow.md as source: 4 partner(s)
   conf 0.86 n=12 -> automation/AGENTS.md
   conf 0.64 n=9 -> message-queue/AGENTS.md
   conf 0.64 n=9 -> templates/queue/review.md
   conf 0.50 n=7 -> templates/queue/request.md
distinct files in the candidate set: 17

$ git ls-files '*.md' | wc -l
     249
$ git ls-files '*.md' | grep -v -E '^(history/|memory/decisions/|message-queue/needs-agent/retries/|tmp/)' | wc -l
     172
```

Coverage, against the design's claim that mining is "available on day one for every
file": 17 of 172 in-scope tracked markdown files (9.9%) appear in any candidate at
confidence ≥ 0.5. Mining is available for every file; it *says something* about a tenth
of them.

## the shared commit subjects are the same twelve subjects for all 27 candidates

The full evidence list for every one of the 27 was dumped with the same loop over
`subjects`. Compressed: eleven of the twelve recurring subjects are

```
harness: require authoritative source release
harness: bind actions and reviews to exact boundaries
harness: structurally triage conversation sources
harness: replay current review actions
harness: bind provider assignments to queue identities
harness: preserve actor direction across review surfaces
harness: bind handover actions to queue entries
harness: preserve queue actions across revisions
harness: close queue lifecycle bypasses
harness: harden queue snapshot boundaries
harness: close queue enforcement gaps
```

and every one of the 27 candidates draws its evidence from that pool. "harness: bind
actions and reviews to exact boundaries" is the leading evidence line for the pair that
copies a prefix rule, for the pair that summarises a reconciler check, and for the pair
that restates provider admission — three different relationships, one indistinguishable
sentence. This is the measurement that matters most for the second verdict.

## why: one task's commit style manufactured the whole clique

```
$ for s in "harness: bind actions and reviews to exact boundaries" "harness: close queue lifecycle bypasses" "harness: harden queue snapshot boundaries" "harness: structurally triage conversation sources" "harness: replay current review actions" "harness: bind provider assignments to queue identities" "harness: preserve actor direction across review surfaces" "harness: require authoritative source release" "harness: preserve queue actions across revisions" "harness: close queue enforcement gaps" "harness: bind handover actions to queue entries" "harness: close projection and history bypasses"; do h=$(git log --format='%H' --grep="$s" -F | head -1); total=$(git show --name-only --format='' $h | grep -c .); md=$(git show --name-only --format='' $h | grep -c '\.md$'); echo "$(git log -1 --format='%h' $h)  total=$total  md=$md  $s"; done
52f5b04  total=17  md=11  harness: bind actions and reviews to exact boundaries
3dc7b5c  total=22  md=16  harness: close queue lifecycle bypasses
aca7014  total=15  md=12  harness: harden queue snapshot boundaries
1b40239  total=20  md=13  harness: structurally triage conversation sources
484c005  total=20  md=12  harness: replay current review actions
2066441  total=16  md=12  harness: bind provider assignments to queue identities
bfe03f9  total=19  md=12  harness: preserve actor direction across review surfaces
7024964  total=21  md=11  harness: require authoritative source release
91e0ad2  total=18  md=12  harness: preserve queue actions across revisions
7f7679a  total=8   md=5   harness: close queue enforcement gaps
0daeefe  total=14  md=10  harness: bind handover actions to queue entries
573d9d5  total=15  md=9   harness: close projection and history bypasses
```

Every one of these is a commit of the 2026-07-23-first-class-message-queue task, and each
touches 5 to 16 markdown contracts — well under the 40-path cap, so none is skipped as
tangled. A 12-file commit creates 66 directed pairs on its own. Twelve such commits over
substantially the same file set is what produces 27 candidates over 11 files.

```
$ for h in 52f5b04 3dc7b5c aca7014; do echo "=== $h $(git log -1 --format='%s' $h) ==="; git show --name-only --format='' $h | grep '\.md$'; done
=== 52f5b04 harness: bind actions and reviews to exact boundaries ===
automation/AGENTS.md
handbook/git-workflow.md
handbook/human-action-guide.md
message-queue/AGENTS.md
tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md
tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md
templates/queue/clarification.md
templates/queue/decision.md
templates/queue/request.md
templates/queue/retry.md
templates/queue/review.md
=== 3dc7b5c harness: close queue lifecycle bypasses ===
AGENTS.md
automation/AGENTS.md
handbook/git-workflow.md
handbook/human-action-guide.md
memory/decisions/2026-07-23-queue-resolution-is-git-evidence.md
memory/index.md
message-queue/AGENTS.md
roadmap/current-state.md
tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md
tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md
tasks/AGENTS.md
templates/queue/clarification.md
templates/queue/decision.md
templates/queue/request.md
templates/queue/retry.md
templates/queue/review.md
=== aca7014 harness: harden queue snapshot boundaries ===
automation/AGENTS.md
handbook/git-workflow.md
handbook/human-action-guide.md
history/AGENTS.md
message-queue/AGENTS.md
message-queue/needs-agent/retries/README.md
tasks/AGENTS.md
templates/queue/clarification.md
templates/queue/decision.md
templates/queue/request.md
templates/queue/retry.md
templates/queue/review.md
```

The 40-path commit cap does not catch this. A cap that did — 12 or so paths — would also
discard the commits carrying the real restatement propagation, so lowering it is not the
fix. What the shape means is stated in the verdict.

## the decisive case, verified rather than assumed

```
$ grep -c "message-queue/AGENTS.md" templates/queue/review.md
0
$ grep -n "message-queue" templates/queue/review.md; echo "exit=$?"
exit=1
$ grep -n "blocking-\|future-blocking-\|non-blocking-" templates/queue/review.md
3:- blocking-: a named current task, transition, or operation cannot proceed now.
4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
5:- non-blocking-: this message never stops work and names the safe unattended outcome.
53:blocking-*:
56:future-blocking-*:
62:non-blocking-*:
$ grep -rn "future-blocking-" message-queue/AGENTS.md | head -20
message-queue/AGENTS.md:14:| Filename prefix | `blocking-`, `future-blocking-`, `non-blocking-` | when unresolved work stops |
message-queue/AGENTS.md:17:- `future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or
```

Confirmed: the string `message-queue` does not occur anywhere in the template, and the
prefix rule it restates is owned five lines into `message-queue/AGENTS.md`.

What the design's write-up does not mention is that the restatement is fivefold:

```
$ grep -n "future-blocking-: " templates/queue/*.md
templates/queue/decision.md:4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
templates/queue/clarification.md:4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
templates/queue/request.md:4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
templates/queue/review.md:4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
templates/queue/retry.md:4:- future-blocking-: work may continue, but must stop at a named date, event, or transition.
```

All five queue templates carry the identical six-line comment and none of them names its
owner. The report found all five, in the top eight of the default view.

## textual mention, both directions, all 27 candidates

```
$ python3 -c "
import json, os
os.chdir('/Users/quentinmiao/code/ai-harness')
d=json.load(open('$C05S3'))
hot={'automation/AGENTS.md','message-queue/AGENTS.md'}
for c in d['candidates']:
    if not (c['source'] in hot or c['target'] in hot): continue
    a,b=c['source'],c['target']
    n_ab=open(a, encoding='utf-8').read().count(b)
    n_ba=open(b, encoding='utf-8').read().count(a)
    print('%-40s -> %-40s  src-mentions-tgt=%d  tgt-mentions-src=%d' % (a,b,n_ab,n_ba))
"
```

Result, compressed: **25 of the 27 pairs have zero occurrences of the partner path in
either file.** The only exceptions are the two directions of the same pair —
`handbook/human-action-guide.md` and `message-queue/AGENTS.md` mention each other once
each. This reproduces the design's disjointness claim and is stronger than its 78-85%
figure on this subset (93%). It is the clearest single result in favour of Stage 0.

## which section of each hot file actually changed, per revision

```
$ python3 - <<'PY'
import re, subprocess
def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, cwd='.').stdout
for target in ('message-queue/AGENTS.md', 'automation/AGENTS.md'):
    print('=' * 78); print(target)
    for line in sh('git','log','--format=%h %s','--',target).strip().splitlines():
        sha, subject = line.split(' ', 1)
        blob = sh('git','show','%s:%s' % (sha, target))
        heads = [(i+1, l) for i, l in enumerate(blob.splitlines()) if l.startswith('#')]
        if not heads:
            print('  %s  (file absent/empty at this rev)  %s' % (sha, subject)); continue
        diff = sh('git','show','--format=','--unified=0',sha,'--',target)
        touched = []
        for m in re.finditer(r'^@@ -\S+ \+(\d+)(?:,(\d+))? @@', diff, re.M):
            start = int(m.group(1)); count = int(m.group(2) or 1)
            for ln in range(start, start + max(count,1)):
                sec = None
                for hl, ht in heads:
                    if hl <= ln: sec = ht
                if sec: touched.append(sec)
        names = []
        for s in touched:
            if s not in names: names.append(s)
        print('  %s  %-52s sections=%d/%d' % (sha, subject[:52], len(names), len(heads)))
        for n in names: print('        %s' % n)
PY
```

Two results, both load-bearing for Stage 4.

`automation/AGENTS.md` — the hottest markdown file in the repository, 19 in-scope
revisions — reports `sections=1/1` on **every one of its 22 revisions**, because the file
has exactly one heading. A clause anchor on it is not merely unhelpful, it has no legal
value: the design requires an anchor only when a target has two or more headings, and
this target never will while it stays a single-section 60-line table. Twelve of the 29
candidates judged below (41%) point at it.

`message-queue/AGENTS.md` — 4 headings, 14 in-scope revisions in the walk, 17 revisions
total:

| Section | Revisions that touched it (of the 14 in-scope) |
|---|---|
| `## Lifecycle and content` | **13** |
| `## Routing: three independent axes` (owns the prefix rule) | 3 |
| the file's own H1 preamble | 4 |
| `## Standard endpoints` | 1 |

So clause scoping is real here and worth roughly 4.7× on this file: an edge anchored at
the routing clause fires on 3 revisions rather than 14. That is the design's clause-
scoping argument, confirmed. It is also the only one of Stage 4's claims that survived.

## whether the restating templates changed alongside the prefix clause

```
$ for h in 7024964 aca7014 3f4f1df; do echo "=== $h $(git log -1 --format='%s' $h)"; git show --name-only --format='' $h | grep -E 'templates/queue/|message-queue/AGENTS.md|templates/handover.md'; done
=== 7024964 harness: require authoritative source release
message-queue/AGENTS.md
templates/queue/review.md
=== aca7014 harness: harden queue snapshot boundaries
message-queue/AGENTS.md
templates/queue/clarification.md
templates/queue/decision.md
templates/queue/request.md
templates/queue/retry.md
templates/queue/review.md
=== 3f4f1df harness: enforce first-class queue actions
message-queue/AGENTS.md
templates/handover.md
templates/queue/clarification.md
templates/queue/decision.md
templates/queue/request.md
templates/queue/retry.md
templates/queue/review.md

$ for h in 7024964 aca7014 3f4f1df; do echo "--- $h"; git show --format='' -U1 $h -- message-queue/AGENTS.md | grep -E '^[+-].*(blocking-|prefix)' || echo "  (no prefix lines changed)"; done
--- 7024964
  (no prefix lines changed)
--- aca7014
-- `future-blocking-<slug>.md`: work continues until an explicit date, event, or
+- `future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or
+++ 3f4f1df
+| Filename prefix | `blocking-`, `future-blocking-`, `non-blocking-` | when unresolved work stops |
+- `blocking-<slug>.md`: a named current task, transition, or operation cannot proceed.
+- `future-blocking-<slug>.md`: work continues until an explicit date, event, or
+- `non-blocking-<slug>.md`: the action never stops work and names the safe unattended
```

Only **2 of the 14** in-scope revisions changed the prefix definitions themselves, and in
both of those every restating template was edited in the same commit. Under the
`each-run` freshness mode, review debt closes when the dependent is next modified — so
across the entire history of the repository's strongest declared-edge candidate, derived
clause-scoped debt would have filed **zero** items.

## the drift that mechanism would have missed anyway

```
$ git show --format='' aca7014 -- automation/AGENTS.md
-  starts with a reached `YYYY-MM-DD`; event boundaries require an actor to reclassify.
+  starts with a reached UTC `YYYY-MM-DD`; event boundaries require actor reclassification.
$ git show --format='' aca7014 -- templates/queue/decision.md
-**Blocks at:** <YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
+**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
$ grep -n "UTC date" message-queue/AGENTS.md
17:- `future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or
57:  UTC dates are clock-checked; other timing is agent-attested absent a validating
$ grep -n "UTC" templates/queue/review.md
57:**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
```

Commit aca7014 propagated "UTC" into the owning contract, into the check summary, and
into all five templates' `Blocks at` field lines — and left all five templates' prose
comments reading "a named date". That drift is live at this commit and is exactly the
failure the typed edge exists to prevent. It survived because the debt-closing rule asks
whether the dependent was *touched*, not whether it was *updated*, and the dependent was
touched in the same commit for a neighbouring reason.

This is the experiment's sharpest negative result, and it was produced by reading the
diff, not by any mechanism in the design.

## ledger verdicts

Recorded through the tool's own verbs; the ledger file was never hand-edited. The
population is the 27 hot-file candidates above plus the two candidates in the default
report's top ten that are not hot-file candidates (its items 9 and 10), because that top
ten is what an agent actually sees.

```
$ python3 automation/mine_cochange.py reject \
    tasks/3_in-review/2026-07-23-first-class-message-queue/task.md \
    message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md \
    --reason "already declared bidirectionally in a stronger checked form -- the task Queue actions field names the item and the item Blocks at names task:<id>, and the reconciler enforces the pair; the design forbids restating an enforced typed field as a generic edge"
recorded reject: tasks/3_in-review/2026-07-23-first-class-message-queue/task.md -> message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md (2026-07-25) -- already declared bidirectionally in a stronger checked form -- the task Queue actions field names the item and the item Blocks at names task:<id>, and the reconciler enforces the pair; the design forbids restating an enforced typed field as a generic edge
ledger: 1 verdict(s), 1 rejected, rate 100.0% (off)
```

The evidence behind that single rejection:

```
$ grep -n "Queue actions" tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
8:**Queue actions:** `message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md`; `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
$ grep -n "Blocks at" message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md
10:**Blocks at:** transition:complete task:2026-07-23-first-class-message-queue
$ grep -c "Queue actions" automation/reconcile/reconcile.py
5
```

The remaining 28 were accepted in one loop; each line is one invocation of the accept
verb with a one-line reason. Real output, first line of each:

```
$ while IFS='|' read -r a b reason; do [ -z "$a" ] && continue; python3 automation/mine_cochange.py accept "$a" "$b" --reason "$reason" | head -1; done <<'ROWS'
... 28 pipe-delimited rows, one per candidate ...
ROWS
recorded accept: templates/queue/review.md -> message-queue/AGENTS.md (2026-07-25) -- restates the blocking-/future-blocking-/non-blocking- prefix rule this contract owns, with zero occurrences of that path anywhere in the template
recorded accept: templates/queue/clarification.md -> message-queue/AGENTS.md (2026-07-25) -- carries the identical six-line prefix comment as review.md with no link to its owner
recorded accept: templates/queue/decision.md -> message-queue/AGENTS.md (2026-07-25) -- carries the identical six-line prefix comment as review.md with no link to its owner
recorded accept: templates/queue/request.md -> message-queue/AGENTS.md (2026-07-25) -- carries the identical six-line prefix comment plus the open/in-repair status vocabulary this contract owns
recorded accept: templates/queue/retry.md -> message-queue/AGENTS.md (2026-07-25) -- carries the identical six-line prefix comment plus the open/in-repair status vocabulary this contract owns
recorded accept: message-queue/AGENTS.md -> templates/queue/review.md (2026-07-25) -- the load-bearing direction: commit aca7014 changed explicit date to explicit UTC date here and the template prose comment still says a named date
recorded accept: message-queue/AGENTS.md -> templates/queue/clarification.md (2026-07-25) -- owner-to-restatement direction; the same UTC drift is present in this template
recorded accept: message-queue/AGENTS.md -> templates/queue/decision.md (2026-07-25) -- owner-to-restatement direction; the same UTC drift is present in this template
recorded accept: message-queue/AGENTS.md -> templates/queue/request.md (2026-07-25) -- owner-to-restatement direction; lifecycle rules here govern the template's status and Request kind fields
recorded accept: message-queue/AGENTS.md -> templates/queue/retry.md (2026-07-25) -- owner-to-restatement direction; lifecycle rules here govern the template's open-to-in-repair claim
recorded accept: templates/queue/review.md -> automation/AGENTS.md (2026-07-25) -- the queue checks summarised there are what make this template's fields enforceable; aca7014 propagated the same UTC change to both
recorded accept: templates/queue/clarification.md -> automation/AGENTS.md (2026-07-25) -- same enforcement summary; a template field change requires the queue check and its one-line description to move
recorded accept: templates/queue/decision.md -> automation/AGENTS.md (2026-07-25) -- verified content coupling: aca7014 changed Blocks at to UTC here and the stale-queue description there in the same commit
recorded accept: templates/queue/request.md -> automation/AGENTS.md (2026-07-25) -- the pickup and open/in-repair checks summarised there validate this template's fields
recorded accept: templates/queue/retry.md -> automation/AGENTS.md (2026-07-25) -- retry filing and garbage collection are described there and produce files from this template
recorded accept: handbook/git-workflow.md -> automation/AGENTS.md (2026-07-25) -- the PR and admission adapter bullets there restate this file's provider and merge rules almost verbatim
recorded accept: automation/AGENTS.md -> handbook/git-workflow.md (2026-07-25) -- reverse direction of the same restatement; the enforcement summary and the prose rule must not diverge
recorded accept: handbook/git-workflow.md -> message-queue/AGENTS.md (2026-07-25) -- the merging and review section restates the future-blocking timing and escalation semantics this contract owns
recorded accept: message-queue/AGENTS.md -> handbook/git-workflow.md (2026-07-25) -- reverse direction; changing queue timing invalidates the merge-review paragraph there
recorded accept: handbook/human-action-guide.md -> message-queue/AGENTS.md (2026-07-25) -- the guide already links this contract for the prefix choice; the only mutually mentioned pair in the whole candidate set
recorded accept: message-queue/AGENTS.md -> handbook/human-action-guide.md (2026-07-25) -- this contract already links the guide for human fields, so the coupling is declared in prose already
recorded accept: handbook/human-action-guide.md -> automation/AGENTS.md (2026-07-25) -- the projection and external-assignment rules the guide states are exactly what the action-projection adapter enforces
recorded accept: message-queue/AGENTS.md -> automation/AGENTS.md (2026-07-25) -- the queue-checks bullet there is the enforcement summary of these lifecycle rules
recorded accept: tasks/AGENTS.md -> automation/AGENTS.md (2026-07-25) -- both restate the core-scope receipt and the --require-review semantics in near-identical wording
recorded accept: CONTRIBUTING.md -> automation/AGENTS.md (2026-07-25) -- restates the same core-scope receipt and --require-review rule for a human audience
recorded accept: templates/task/verification.md -> automation/AGENTS.md (2026-07-25) -- the review-verdicts block restates when --require-review makes a core-fit verdict mandatory
recorded accept: templates/handover.md -> message-queue/AGENTS.md (2026-07-25) -- the handover projection restates the prefix ordering and the never-originate-an-ask rule this contract owns
recorded accept: docs/designs/risk-tiered-agent-guardrails.md -> roadmap/desired-state.md (2026-07-25) -- the roadmap carries a one-paragraph summary of this design and links it; all three shared commits moved both
```

Two accepts deserve their evidence recorded, because both looked like ritual noise until
they were read. The guardrail design's pair is real — the roadmap carries a summary of
the design and links it:

```
$ grep -n "guardrail\|risk-tier" roadmap/desired-state.md
44:   *(Human-reviewed design in `docs/designs/risk-tiered-agent-guardrails.md`;
$ git show --format='' 19ba6b0 -- roadmap/desired-state.md | head -12
@@ -30,5 +30,9 @@ In priority order. Each line is specific enough to spawn tasks against.
-   remote authority where available. *(Design proposed in
-   `docs/designs/risk-tiered-agent-guardrails.md`; implementation not started.)*
+   remote authority where available. Every guard is selected through one `hard`,
+   `soft`, `off`, or `manual` configuration surface; starter mechanisms are
+   templates, costly agent review is manual by default, and sandboxing is deferred.
+   *(Human-reviewed design in `docs/designs/risk-tiered-agent-guardrails.md`;
+   implementation task `2026-07-22-universal-guard-mode-configuration` filed but not
+   started.)*
```

And the template-to-check-summary group is real content coupling, not a policy artifact:

```
$ git show --format='' aca7014 -- automation/AGENTS.md templates/queue/decision.md
-  starts with a reached `YYYY-MM-DD`; event boundaries require an actor to reclassify.
+  starts with a reached UTC `YYYY-MM-DD`; event boundaries require actor reclassification.
-**Blocks at:** <YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
+**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
```

## rejection rate against the governance bands

```
$ python3 automation/mine_cochange.py status
ledger      automation/cochange-ledger.txt
verdicts    29 (28 accepted, 1 rejected)
eff. FP     3.4% -- any report the user chose not to act on
governance  on-target: on target -- under the 10% effective-false-positive threshold
$ echo "exit=$?"
exit=0
```

The same single rejection reads as two different governance verdicts depending on the
population, and both are honest:

| Population | Judged | Rejected | Eff. FP | Band |
|---|---|---|---|---|
| the 27 hot-file candidates at confidence ≥ 0.5 | 27 | 0 | **0.0%** | on target |
| the default report's top ten — what an agent sees | 10 | 1 | **10.0%** | **probation** |
| the whole ledger | 29 | 1 | **3.4%** | on target |

The governance rule is stated against a rate without naming its denominator, and at these
volumes one verdict moves the answer across a band boundary. That is a defect in the
threshold as written, not in the measurement.

## a decided pair does not re-surface, and is not re-decided

```
$ python3 automation/mine_cochange.py accept templates/queue/review.md message-queue/AGENTS.md --reason "duplicate attempt"
[cochange] templates/queue/review.md -> message-queue/AGENTS.md already recorded as accept on 2026-07-25; the ledger is append-only and never re-decided
$ echo "exit=$?"
exit=2

$ python3 automation/mine_cochange.py report --confidence 0.5 --support 3 --limit 0 | head -9
co-change candidates (advisory, provisional)
  floors      support >= 3 commit(s), confidence >= 0.50
  commit cap  40 changed path(s); 4 tangled commit(s) skipped
  history     200 commit(s) walked, 144 in scope, 180 file(s) seen
  scope       *.md outside history/, memory/decisions/, message-queue/needs-agent/retries/, tmp/
  stop-list   memory/index.md, roadmap/current-state.md, tasks/*/*/worklog.md
  dropped     20 pair(s) naming a path no longer tracked, 29 already in the ledger
  ledger      automation/cochange-ledger.txt -- 29 verdict(s), 1 rejected, rate 3.4%
  ranking     confidence desc, support desc, source path asc, target path asc
```

52 candidates before the verdicts, 29 suppressed, 23 left. The default view shrank from
20 candidates to 8:

```
$ python3 automation/mine_cochange.py report | tail -4

8 candidate(s) clear the floors; 8 shown, 0 dropped by the ranking above -- not "nothing else couples".
provisional: 200 commit(s) of history, and the published work this borrows from discards the first few hundred change records as warm-up.
dismiss or keep one: mine_cochange.py accept <a> <b> | reject <a> <b> --reason "..."
```

**What an accept means in this ledger, and what it does not.** The design's ledger section
defines accept as "an edge was declared". No typed schema exists yet, so none of these 28
accepts can mean that. Every one of them means exactly: *judged a real dependency by reading
the two files and their shared diffs, to be declared if and when Stage 2 ships.* The ledger
is a judgment record, not a declaration record, and a later reader must not read an accept
line as evidence that an edge exists anywhere.

The operational consequence: 28 accepts now sit in the ledger with no declared edge behind
them, and the report will never propose them again. If Stage 2 is ever built, the authoring
queue for these eleven files is the ledger's accept lines, not a fresh report.

## stated limitation: this is 200 commits, not a warmed-up history

Every number above rests on 200 commits, 144 of them in scope, spanning five days. The
published co-change work this technique borrows from discards the first few hundred change
records as warm-up precisely because early history is unrepresentative, so this repository
has produced no post-warm-up data at all.

Direction of expected movement, and why:

- **The effective-false-positive rate is expected to rise.** Every accept above rests on
  restatement between contracts of one subsystem that one task rewrote twelve times. As
  unrelated work accumulates, pairs will start clearing the floors on shared session
  ritual and on incidental same-commit edits rather than on shared content — the two
  ritual-shaped candidates already in the default top ten are the leading edge of that.
  Supports also only grow, so a pair that co-changed three times and then diverges keeps
  its support forever while its confidence decays slowly.
- **Confidence is expected to fall for the hot contracts, and the ranking to churn.** These
  confidences are P(target | source) over 4 to 19 revisions; every future revision of
  `automation/AGENTS.md` that does not touch its partner moves a 0.86 down measurably.
  Three of the design's own mined figures already moved materially in two days, which is
  the empirical case for treating none of these numbers as stable.
- **Coverage is expected to improve.** 17 of 172 in-scope files today. That is the one number
  expected to move in the mechanism's favour.

## reconciler

The checker reads staged bytes, so the work is staged first. The first staged run found
three real findings in an earlier draft of this file, all from the same check — the
detector reads a heading ending in a question mark and two bullets phrased with "should"
as asks addressed to a human:

```
$ git add -A
$ python3 automation/reconcile/reconcile.py --check
[task-action-origin] tasks/1_in-progress/2026-07-25-mine-markdown-cochange-couplings/verification.md: task artifact introduced an unqueued human action: ## did the restating templates change alongside the prefix clause?
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/1_in-progress/2026-07-25-mine-markdown-cochange-couplings/verification.md: task artifact introduced an unqueued human action: - **Confidence should fall for the hot contracts and the ranking should churn.** These confidences are P(target | source) over 4 to 19 revisions; every future revision of `automation/AGENTS.md` that does not touch its partner moves a 0.86 down measurably. Three of the design's own mined figures already moved materially in two days, which is the empirical case for treating none of these numbers as stable.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/1_in-progress/2026-07-25-mine-markdown-cochange-couplings/verification.md: task artifact introduced an unqueued human action: - **Coverage should improve.** 17 of 172 in-scope files today. That is the one number expected to move in the mechanism's favour.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 3 finding(s)
$ echo "exit=$?"
exit=1
```

Four phrasings were rewritten to state findings rather than address the reader, and the
check then passed:

```
$ git add -A
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
$ echo "exit=$?"
exit=0
```

## unit tests — the ledger's own test forbids the ledger from being used

```
$ python3 automation/run_tests.py
...................F........
======================================================================
FAIL: test_shipped_ledger_documents_its_format_and_holds_no_verdicts (__main__.MineCochangeTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/var/folders/9g/.../view/automation/tests/test_mine_cochange.py", line 416, in test_shipped_ledger_documents_its_format_and_holds_no_verdicts
    self.assertEqual(([], []), MINE.load_ledger(shipped))
AssertionError: Tuples differ: ([], []) != ([('reject', 'tasks/3_in-review/2026-07-23-[5688 chars], [])

First differing element 0:
[]
[('reject', 'tasks/3_in-review/2026-07-23-[5683 chars]th')]

Diff is 6709 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 28 tests in 8.704s

FAILED (failures=1)
[...]
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
FAIL automation/tests/test_mine_cochange.py
tests: 10/11 files passed
$ echo "exit=$?"
exit=1
```

The failing assertion, at `automation/tests/test_mine_cochange.py` line 416:

```
    def test_shipped_ledger_documents_its_format_and_holds_no_verdicts(self):
        shipped = MODULE_PATH.parent / "cochange-ledger.txt"
        self.assertEqual(([], []), MINE.load_ledger(shipped))
```

That assertion can only hold while the ledger has never been used. The accept and reject
verbs write to the tracked ledger and expose no path override, so the mechanism's first
real verdict fails the suite. The pre-commit hook runs the suite, so the first real verdict
also makes the repository uncommittable:

```
$ git commit -m "docs: record the co-change gating experiment verdict

task: 2026-07-25-mine-markdown-cochange-couplings"
pre-commit: core scope
pre-commit: reconciler
pre-commit: repository tests
[...]
FAIL automation/tests/test_mine_cochange.py
tests: 10/11 files passed
$ git log --oneline -1
e52f68e feat: validate heading anchors and mine co-change couplings
```

Core scope and the reconciler both passed inside the hook; only the test step failed, and
nothing was committed. The finding stands on its own: **an assertion that a mechanism's
durable store is empty is an assertion that the mechanism is never used**, and the ledger
could not be used at all while it held.

The repair, authorized after escalation, changes that one assertion to the invariant that
survives use — the shipped ledger parses with zero malformed lines, and every verdict it
holds is well-formed: verdict in the closed set, ISO date, no tabs in any field, source
distinct from target, and a reason present on every rejection. The method is renamed to
match. No other test was touched and `automation/mine_cochange.py` behaviour is unchanged.

```
$ python3 automation/tests/test_mine_cochange.py
............................
----------------------------------------------------------------------
Ran 28 tests in 6.202s

OK
```

The full suite after the repair is recorded at the end of this file, from the commit hook.

## the anchor tests exist; the plan named the wrong file

An earlier draft of this file reported automation/tests/test_reconcile_links.py missing and
inferred the anchor validation was untested. That inference was wrong, and the correction is
recorded rather than quietly dropped: the tests were appended to the existing queue test
file instead of getting their own, so plan step 4 names a file that was never created.

```
$ grep -n "def test_link_check" automation/tests/test_reconcile_queue.py
12103:    def test_link_check_reports_dead_path_carried_behind_an_anchor(self):
12115:    def test_link_check_accepts_a_live_anchor_on_a_live_path(self):
12122:    def test_link_check_reports_a_dead_anchor_on_a_live_path(self):
12136:    def test_link_check_rejects_an_anchor_defined_only_inside_a_fence(self):
12149:    def test_link_check_numbers_duplicate_heading_anchors(self):
12170:    def test_link_check_slugs_punctuation_heavy_headings(self):
12196:    def test_link_check_keeps_anchor_exemptions_for_records_and_schemas(self):
12208:    def test_link_check_ignores_a_bare_same_file_fragment(self):
```

Eight tests, covering every branch plan step 4 asked for. `plan.md` step 4 is corrected to
name `automation/tests/test_reconcile_queue.py`; the plan's stated reason for wanting a
separate file — keeping new tests out of the 98-second file — did not survive
implementation, and that is now recorded in the step rather than left as a promise.

## the suite and the hook after the repair

The commit that carries this file ran the whole gate. Tail of the hook, trimmed to the
meaningful part:

```
$ git commit -m "docs: record the co-change gating experiment verdict ..."
pre-commit: core scope
pre-commit: reconciler
pre-commit: repository tests
[...]
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
pre-commit: OK
```

11 of 11 files pass with 29 real verdicts in the ledger, which is the state the earlier
assertion made impossible. No `--no-verify` was used at any point; the first commit attempt
was refused and is recorded above rather than bypassed.
