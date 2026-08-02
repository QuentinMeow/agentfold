# Verification — rewrite the human-facing guidance

## The rule inventory, and the audit against it

`rule-inventory.md` in this folder lists every normative statement in the two pre-rewrite
files: 163 rows, 126 from `handbook/human-action-guide.md` (178 lines at the time) and 37
from the "Lifecycle and content" section of `message-queue/AGENTS.md`.

An independent agent then audited the rewrite against that inventory, row by row, with
instructions to treat a half-preserved rule as changed rather than kept. Its verdicts:

| Verdict | Count | Meaning |
|---|---|---|
| `KEPT` | 151 | stated in the rewritten file itself |
| `MOVED` | 9 | now stated in a file the rewrite points to for that topic, verified present there |
| `LOST` | 1 | found nowhere |
| `CHANGED` | 2 | present, but its meaning differs |

The four non-`KEPT` outcomes are each accounted for below. Nothing was dropped silently.

### The one `LOST` rule was false

Row 152, `message-queue/AGENTS.md:56`: *"a review … binds a stable local file"*.

It was deleted deliberately. A merge review binds a Git range, and `templates/queue/review.md`
also permits an HTTPS artifact, so the flat claim contradicted both the template and
`handbook/human-action-guide.md`. The correct, narrower rules — a task-lifecycle review binds
a stable local artifact, a merge review binds the candidate Git range — survive as rows 107
and 109, both `KEPT`, and `message-queue/AGENTS.md` now points at the guide that states them
rather than restating a wrong summary.

### Both `CHANGED` rules were corrections

Row 69: the guide claimed *"this guide adds no timing rule of its own"* and then stated four.
It now says which timing rules it does state and where the rest live.

Row 125: *"Legacy `not-approved` is equivalent"*, positioned beside `rejected`/`abandoned`,
which implied it ends pursuit. `automation/reconcile/reconcile.py` registers it as
`# legacy alias for changes-requested` and puts it in `REVIEW_SUCCESSOR_OUTCOMES`, so it
carries the opposite obligation — a repair action plus a re-review. The rewrite states that.

```
$ grep -n "not-approved" automation/reconcile/reconcile.py
189:    "not-approved",  # legacy alias for changes-requested
191:REVIEW_SUCCESSOR_OUTCOMES = {"changes-requested", "not-approved"}
5252:                                "abandoned (legacy not-approved means "
```

### The `MOVED` rules point at files that really say it

Rows 19–22 to `templates/queue/review.md` (target and revision grammar, when `pending` is
allowed); row 127 to `templates/README.md` (copy-and-fill); rows 139–140 to
`handbook/decision-guide.md` (folding a counter-question); rows 157–158 from
`message-queue/AGENTS.md` to `handbook/human-action-guide.md` (what each non-approved outcome
owes). The auditor quoted the sentence it found at each destination rather than assuming.

### One rule was added, and it is an addition

The audit found a constraint in the rewrite that is in neither pre-rewrite file: *"Two options
is the minimum. Four is the maximum: past that, readers defer rather than choose."* It appears
in `handbook/decision-guide.md` and in `skills/explain-to-human/scenarios/queue-item.md`. It
comes from the research behind the explanation skill, not from the old text, and it is
recorded here rather than presented as preserved.

A smaller expansion: *"never copy a hash, a revision, or any offered vocabulary"* became
*"never copy a hash, a revision, a field name, or any vocabulary you offered them"*.

## Line budgets

`message-queue/AGENTS.md` is a leaf contract with a 60-line budget.

```
$ wc -l message-queue/AGENTS.md handbook/human-action-guide.md handbook/decision-guide.md
      60 message-queue/AGENTS.md
     316 handbook/human-action-guide.md
      74 handbook/decision-guide.md
```

The guide is longer than the 178 lines it replaced. The added length is headings, examples,
and tables; the depth divider means a reader writing an ordinary decision stops around line
225.

## Repository invariants and tests

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)

$ python3 automation/run_tests.py
tests: 12/12 files passed
test elapsed: 37.74s
```

## Not verified

No test asserts anything about these documents' content — they are prose contracts, and the
reconciler checks only their line budgets and their links. The rule inventory and the audit
are the evidence that the rewrite preserved meaning, and both were produced by reading, not
by execution. A rule that both the inventory and the audit missed would not be caught here.
