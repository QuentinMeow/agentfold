# Worklog — stop completed review verdicts from looking like human asks

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-04 — reproduction and claim (codex planner)

- Reproduced the contradiction on `main`: the exact receipt line required by
  `check_core_scope.py --require-review` is returned as one actionable unit by
  `task_action_unit_counts()` and then refused by `task-action-origin`.
- Stopped the stale-base publication instead of weakening or bypassing either gate.
- Filed GitHub issue #80 as a projection, claimed this prerequisite as its own core task,
  and assigned implementation to a Sol high worker under the planner's review.
- Independent design and test-inventory agents agreed on the narrow boundary: neutralize
  only the exact structural verdict token and continue scanning reviewer and finding text.

## 2026-08-04 — implement receipt-aware classification (codex sol-high implementer)

- Moved the canonical core-fit verdict grammar into the shared Markdown semantics module;
  the core-scope validator and task human-action detector now consume the same named
  reviewer, verdict, and finding groups.
- Limited the classification exception to `verification.md` and to the matched structural
  `approve` or `block` token. Reviewer identities and finding tails still pass through the
  ordinary detector; malformed lines and identical prose in other task artifacts receive
  no special treatment.
- Added unit coverage for valid approve/block receipts, hostile reviewer/finding prose,
  questions, TODOs, and malformed near-misses, plus a staged task-admission regression.
- Focused and full repository suites passed. Independent revision-bound review,
  publication, issue closure, and resuming the parent stale-base repair remain for the
  coordinating session as requested.

## 2026-08-04 — repair blocked path and receipt-region scope (codex sol-high implementer)

- The adversarial panel reviewed exact revision `85a044e67c725cf03d918432514c76ba1655c984`
  and returned 0 approve, 3 block. All three reviewers found the same admission gap:
  basename-only path matching and whole-file line normalization could hide approval-like
  prose in nested or case-variant files and outside the formal receipt region.
- Replaced the line-only sharing boundary with one formal parser for the real Review
  verdicts section, its one valid full-commit field, and only verdicts after that field.
  The detector separately requires the exact lowercase task-root verification path.
- Added regressions for nested and case-variant paths, lines outside or before the bound
  region, duplicate or missing sections and fields, malformed lines, and hostile findings.
- Re-ran the full repository suite to capture its terminal result honestly: all 15 test
  files passed in 68.19 seconds. The blocked panel is evidence about the prior revision,
  not an invocation of the repaired revision's independent core-fit review.

## 2026-08-04 — repair heading-aware receipt boundaries (codex sol-high implementer)

- The second adversarial panel reviewed exact revision
  `12a1f320a9916dd2223a6fe81fd5464ddc611aae` and returned 2 approve, 1 block. The
  blocker was valid: the H2 extractor crossed ATX H1 and CommonMark setext H1/H2
  boundaries, so a later approval-like line could inherit the receipt exception.
- Kept the exact Review verdicts H2 opening grammar and made the shared extractor end at
  the next real ATX H1/H2 or setext H1/H2. A setext heading's content line is excluded;
  H3 detail remains inside the review section.
- Added action-detector and core-scope regressions for ATX H1, ATX H2, both setext
  underline forms, a revision-like setext heading, and an H3 canary.
- Focused tests, all three owning modules, and the full repository suite passed; the full
  lane ended with all 15 test files passing in 68.07 seconds.

## 2026-08-04 — authorization boundary (codex planner)

- Three candidate implementations stayed unpublished after adversarial review found
  basename, section-boundary, and CommonMark-container gaps. Exact evidence remains on the
  task branch through commit `3de329d8b34bb9bb8afcd325b75b1c47612e7997`.
- Replanned to a closed contiguous receipt grammar that needs no general Markdown outline
  parser. The workspace safety reviewer requires fresh owner authorization before that
  security-sensitive parser and template change.
- Filed the authorization question in
  `message-queue/needs-human/decisions/non-blocking-authorize-the-closed-review-receipt-parser.md`
  and paused without bypassing the review or task-action gates.

## 2026-08-04 — owner authorization folded (codex planner)

- The owner selected Option A and authorized the closed contiguous review-receipt parser
  and template design. The answer was transcribed while the canonical item was waiting,
  then claimed in a separate folding commit.
- Recorded the durable decision in
  `memory/decisions/2026-08-04-review-receipt-parser-authorization.md` and released the
  completed human action from this task.
- The authorization does not approve a pull request or replace independent review; the
  implementation still owes focused and full verification plus a fresh adversarial panel.

## 2026-08-04 — implement the authorized closed receipt grammar (codex sol-high implementer)

- Replaced general Markdown section and heading-boundary inference with the authorized
  literal receipt state machine: one exact top-level heading, one exact full-commit field
  as its first content, then only exact one-line core-fit verdicts until the first nonblank
  non-verdict.
- Kept the task action exception at the exact lowercase task-root verification path and
  limited neutralization to each structural `approve` or `block` token; hostile reviewer
  identities and findings remain visible to the ordinary action detector.
- Tightened the canonical template and line grammar, while allowing historical panel
  revision fields outside the sole formal block. An adjacent duplicate formal field and
  duplicate exact headings fail closed.
- Added regressions for every prior panel reproduction, including nested/case paths,
  malformed or misplaced structures, strict spelling, H1/H2/H3 and setext content,
  blockquote/list containers, lazy blockquote plus thematic breaks, link references plus
  thematic breaks, hostile findings, and the first-nonreceipt terminator.
- Focused tests, all 15 repository test files, the reconciler, and the staged core-scope
  gate passed. Independent review, publication, and issue closure remain with the
  coordinating session.

## 2026-08-04 — repair raw contiguity and reviewer authority (codex sol-high implementer)

- The third panel reviewed exact revision
  `25b75c3cdd7fcb17626a79135c1b4b787fe41f0c` and returned 1 approve, 2 block.
  Both blockers were accepted: semantic blanking could bridge nonblank raw comments,
  HTML, or code; and action projection neutralized punctuation-only or self reviewers
  that the core gate could not accept as independent evidence.
- Made raw source lines own contiguity while requiring each heading, revision, and
  verdict line to be byte-equivalent in the structural semantic view. Any nonblank raw
  nonreceipt now closes the block, including content that the semantic view blanks.
- Moved normalized identity and independence checks into the shared Markdown semantics
  module. Action projection now resolves the exact sibling task file from the selected
  index or candidate revision and fails closed unless it has one concrete claimant and a
  distinct reviewer with non-punctuation identity tokens.
- Added action and core regressions for comments, raw HTML, fenced and indented code
  before the first verdict and between verdicts, plus valid independent, self,
  punctuation-only, missing, duplicate, placeholder, candidate-revision, and hostile
  reviewer/finding cases.
- Focused and owning-module tests, all 15 repository test files, range core-scope,
  staged pre-commit tests, the reconciler, and diff checks passed. Publication and a
  fresh independent review remain with the coordinating session.

## 2026-08-04 — repair whitespace and rendered identity normalization (codex sol-high implementer)

- The fourth panel reviewed exact revision
  `e073358dec0a4f7c119597f94c61ed6adb02f0de` and returned 0 approve, 3 block.
  The accepted blockers were Python's overbroad whitespace predicate, incomplete
  LF/CRLF line-ending handling, and source-shaped reviewer identities that did not
  match what a human sees or reject the repository's full placeholder vocabulary.
- Replaced `.strip()` blank tests with an explicit ASCII Markdown predicate that accepts
  only spaces or tabs plus an optional LF, CR, or CRLF ending. NBSP, form-feed,
  vertical-tab, NEL, Unicode separators, default-ignorables, comments, HTML, and code
  all terminate the receipt; a valid CRLF receipt remains accepted.
- Made both claimant and reviewer identities pass through rendered-human HTML, removal
  of default-ignorable characters, NFKC/casefold, and tokenization. Self-review through
  zero-width characters or inline HTML now compares equal, markup-only identities are
  empty, and the repository's complete placeholder vocabulary is rejected on either side.
- Preserved normal independent reviewers, candidate-revision task lookup, and hostile
  reviewer/finding scanning. Focused and owning tests, all 15 repository test files,
  pre-commit, range core-scope, the reconciler, and diff checks passed.

## 2026-08-04 — repair Markdown identity aliases and decorated findings (codex sol-high implementer)

- The fifth panel reviewed exact revision
  `788bd4cb709c4ea4f20099013eb9ea598a39c289` and returned 0 approve, 3 block.
  The accepted blockers were Markdown aliases that could disguise a self reviewer or
  mint apparent voters, rendered placeholders that could enter the voter set, and
  decorated finding text that could hide a human action after verdict neutralization.
- Added one shared inline-Markdown identity renderer for link labels, full/collapsed/
  shortcut reference labels, emphasis, inline code, visible HTML text, entities, and
  default-ignorables. Link destinations and reference destinations never contribute to
  identity; visually equivalent identities now compare equal.
- Kept the formal receipt grammar deliberately small and fail closed: reviewer and
  finding components must be literal plain text. Any Markdown or HTML decoration ends
  the formal block, so its verdict token remains visible to ordinary action detection.
  The template and task design record this compatibility cost.
- Added regressions for every requested alias, rendered placeholder, duplicate-voter
  alias, a normal plain receipt, and decorated approval-shaped findings including a
  reference-link split. Focused and owning-module tests, all 15 repository test files,
  pre-commit, range core-scope, the reconciler, and diff checks passed.

## 2026-08-04 — replace partial rendering with a source whitelist (codex sol-high implementer)

- The next panel reviewed exact revision
  `5c31f508b1166573b8f1b04c5f7410d033c0bace` and returned 0 approve with two
  completed block verdicts. A security reviewer independently reproduced the remaining
  finding bypass before its review tool errored. The accepted blockers were Markdown
  image identities and destination-based vote stuffing, backslash-escaped identities,
  and image-alt finding text that stayed human-visible after verdict neutralization.
- Removed the partial inline renderer from the receipt-authority boundary. Formal
  claimant, reviewer, and finding source now accepts only Unicode letters, marks, and
  numbers; ASCII space; and the documented finite punctuation set. Tabs, non-ASCII
  separators, controls, default-ignorables, and all Markdown/HTML introducers fail closed.
- Applied the same source validation to the exact claimant field before NFKC, casefolding,
  placeholder rejection, or tokenization. A decorated claimant or reviewer therefore has
  no identity, while the canonical `codex planner / sol-high implementer` claimant and
  ordinary Unicode reviewer names remain valid.
- Added unit and end-to-end regressions for images, destinations, escapes, every prior
  decorated form, formatted placeholders and findings, invalid claimant whitespace,
  allowed punctuation and Unicode letters, duplicate image-voter aliases, and a normal
  receipt. Focused and owning-module tests, all 15 repository test files, pre-commit,
  range core-scope, the reconciler, and diff checks passed.

## 2026-08-04 — bind claimant identity to raw source and fold Unicode marks (codex sol-high implementer)

- The next panel reviewed exact revision
  `2ba968faf027df5874de8847948568102513a497` and returned 0 approve, 3 block.
  The three accepted blockers were a claimant helper that derived identity after semantic
  rewriting, combining marks that could mint apparent reviewer identities, and combining
  marks that could split human-action keywords. The earlier security tool error on
  `5c31f50` remains reproduction evidence only and is not a vote in this panel.
- Claimant extraction now locates one literal top-level field in raw `task.md`, validates
  its unchanged suffix against the source whitelist, and only then confirms that the raw
  line is structurally visible. Comments, markup, entities, links, images, code, escapes,
  default-ignorables, hidden fields, malformed suffixes, and duplicates yield no identity.
- Identity and action detection now apply NFKD and remove every Unicode category-M mark
  before casefolding or tokenization. Composed/decomposed spellings compare equally;
  accent-only distinctions conservatively collide; marked placeholders and action words
  collapse to their ordinary forms.
- Added unit, core-gate, and action-projection regressions for every requested raw claimant
  form, multiple combining-mark positions, alias vote stuffing, marked approve/block
  words, marked placeholders, legitimate Unicode, and composed/decomposed equivalence.
  Focused, owning, full, staged pre-commit, exact-range core-scope, exact-range reconciler,
  and diff checks passed.

## 2026-08-04 — close ASCII authority and identity-alias gaps (codex sol-high implementer)

- The sixth panel reviewed exact revision
  `97c35ede09d045f63a45be13ba6452cd3aa13764` and returned 0 approve, 3 block. The
  accepted blockers were punctuation-decorated placeholders, raw claimant lines that
  CommonMark could treat as lazy paragraph continuation, and Cyrillic or mixed-script
  authority text that could create a voter or hide an action word.
- Restricted claimant, reviewer, and formal finding components to a finite ASCII source
  alphabet. The em dash remains only the receipt delimiter; Unicode explanation stays
  outside the formal receipt, where ordinary action detection still folds marks.
- Made claimant extraction require file start or an immediately preceding ASCII-blank
  line and reject an immediate raw Setext underline. Placeholder comparison now removes
  allowed punctuation before checking the repository's placeholder vocabulary.
- A follow-up design debate found that ASCII punctuation and token boundaries could still
  disguise self-review or duplicate voters. One conservative key now sorts the case-folded
  ASCII alphanumeric multiset, so punctuation, spacing, word order, and anagrams collide
  fail-closed. Formal receipts therefore use distinct stable role labels rather than
  personal or display names.
- Added unit, core-gate, and action-projection regressions for all reported placeholder,
  lazy-continuation, Setext, homoglyph, malformed-finding, punctuation-boundary,
  word-order, and duplicate-vote cases. Focused, owning, full, staged, exact-range
  core-scope, exact-range reconciler, and diff checks passed at implementation commit
  `0326174c33d6ca35c266854235c4c7239d3f2a2d`.

## 2026-08-04 — close placeholder, punctuation, and open-container gaps (codex sol-high implementer)

- The seventh panel reviewed exact revision
  `7cd22e79fc6d4ec3e3c151f0093a6ef4c251c344` and returned 0 approve, 3 block. The
  accepted blockers were reordered/anagram placeholder spellings, a colon mismatch
  between claimant and reviewer grammar, and claimants exposed structurally after a blank
  line while still nested inside an open hidden HTML container.
- Placeholder rejection now uses the exact sorted ASCII-alphanumeric multiset key used for
  claimant comparison and duplicate-vote replacement. `yet none` and `D B T` therefore
  cannot become voters.
- Claimants and reviewers now share an explicit ASCII identity predicate that excludes
  colon; findings use a separate predicate that retains colon. A canonical-looking
  embedded-colon reviewer cannot enter either gate.
- Claimant extraction still requires its literal line body at the same logical index in
  both structural and rendered-human views. A shared HTML-prefix state check now also
  rejects claimants and receipt headings under any still-open visible, hidden, non-prose,
  nested, or custom container. Closed containers and fenced, indented, or inline-code
  examples remain compatible, including CRLF input.
- A finite-model preflight found the same open-container issue around the receipt heading.
  It initially proposed global duplicate-revision counting, then retracted that proposal
  after testing the immutable verification history and accepted decision boundary. The
  parser retains scoped semantics: an immediate duplicate in the contiguous prologue
  fails, while exact historical fields after a terminator remain ordinary history.
- Focused, owning, full, staged pre-commit, exact-range core-scope, exact-range reconciler,
  and diff checks passed at implementation commit
  `d27c44174db0f1bb8d13b632be3c6f307d568707`. The final finite-model audit reported no
  remaining blocker in the owner-authorized receipt scope.

## 2026-08-04 — close pending-HTML, visibility, and scan-complexity gaps (codex sol-high implementer)

- The eighth panel reviewed exact revision
  `aa0a111d73da9807c8473848ed2dbf2f5c9828b5` and returned 0 approve, 3 block. The
  accepted blockers were incomplete multiline HTML markers that left only parser-pending
  input, receipt lines checked against structural but not rendered-human text, and prefix
  reparsing inside duplicate-heading discovery.
- Raw HTML prefix state now records `<`-prefixed pending parser input before `close()` and
  treats parser failures as open authority state. This covers incomplete start, end,
  comment, processing, CDATA, declaration, quote, and custom-tag forms with LF or CRLF,
  including a marker completed only after the claimant or receipt.
- Malformed HTML can no longer crash the rendered-human view. That view falls back to
  code-masked source so action words stay detectable, while claimant and receipt prefix
  checks still reject formal authority.
- Receipt extraction now builds source, structural, and rendered line arrays once. The
  heading, revision, and verdict lines must be character-identical at the same logical
  position in all three views. Duplicate heading candidates fail after one linear scan;
  a 1,000-heading regression records zero prefix-parser calls, and a unique candidate
  records one.
- Compatibility regressions preserve ordinary comparisons, closed markup, void tags,
  fenced/indented/inline-code examples, LF/CRLF receipts, and scoped historical revision
  fields. Focused, owning, full, staged pre-commit, exact-range core-scope, exact-range
  reconciler, and diff checks passed at implementation commit
  `5b738fb1157fbdb53c2b3be9d9813d93d3eedd89`.
- The final finite-model audit found no remaining blocker, independently exercised the
  malformed-prefix matrix, and parsed the actual 49.6 KB verification history plus a final
  receipt as one section, one revision, and one verdict with one prefix check.

## 2026-08-04 — make verdict mapping linear and scope revision duplicates (codex sol-high implementer)

- The ninth panel reviewed exact revision
  `9e9dfa2218a71135c8e6ae3e638c26d92d42f5cf` and returned 1 approve, 2 block. The
  accepted blockers were one full semantic-prefix scan per verdict token and a second
  revision field invalidating an already collected receipt instead of terminating it.
- Verdict neutralization now builds semantic line-start offsets once and walks the ordered
  matches with a monotone cursor. A deterministic 16,000-verdict CRLF regression makes
  `count` or `rfind` prefix scans raise immediately and proves every structural token is
  blanked while every finding and logical line remains.
- An actual before/after benchmark on complete neutralization measured 4,000 verdicts at
  1.090s before and 0.657s after, then 8,000 at 2.975s before and 1.357s after. These are
  observations from one run, not performance thresholds.
- A duplicate revision before the first valid verdict still fails closed. The first valid
  verdict ends that prologue; a revision immediately afterward is the first non-verdict
  terminator, preserves earlier evidence, and leaves later canonical verdict lines under
  ordinary action detection. Parser, core-gate, and action-projection regressions cover
  both sides plus the existing historical-field cases.
- The first full-suite attempt exposed a nested test helper that made the repository's AST
  sharder fall back to whole-file execution. Replacing it with a configured mock restored
  explicit discovery; both sharding meta-tests and the successful full rerun passed.
- Focused, owning, full, staged pre-commit, exact-range core-scope, exact-range reconciler,
  and diff checks passed at implementation commit
  `189fd7ee27faef510a461678eb27fc854f77eb84`. The independent finite-model preflight found
  no remaining blocker in the ninth-panel scope.

## 2026-08-04 — close composite-claimant self-review aliases (codex sol-high implementer)

- The tenth panel reviewed exact revision
  `7e3c8d2b9ea082b9289509fe64132eaaa545b272` and returned 1 approve, 2 block. The accepted
  blockers were treating an actual composite claimant only as one combined key and using
  equality alone, which let a component or an extended prefix/suffix spelling appear
  independent.
- A shared `claimant_identity_keys` helper now validates the unchanged raw identity and
  splits literal `/`, `+`, `;`, `,`, and standalone case-insensitive ASCII `and`. ASCII
  spaces are trimmed per component; any empty, invalid, punctuation-only, or placeholder
  component invalidates all claimant authority.
- The whole claimant key is the separator-free sorted multiset union of every component
  key before component deduplication, so separator spellings agree and repeated components
  retain multiplicity. Whole-placeholder forms such as `D/B/T`, `D and B and T`, and
  `N/A`, plus adjacent separators and `C++`, fail closed.
- Independence now rejects reviewer equality, either-direction multiset containment, and
  a multiset symmetric difference of at most two against the whole claimant and every
  component. The finite-model preflight added the one-substitution cases `author`/`auth0r`
  and `codex planner`/`codex plannez`; intended stable labels including `correctness
  reviewer` remain independent.
- Core majority calculation and action neutralization call the same helper. Reviewer vote
  replacement remains keyed only by exact reviewer identity, and a compatibility regression
  proves distinct containment-related reviewer roles do not merge.
- Focused 12-test, owning 315-test, full 15-file, staged 13-file, exact-range core-scope,
  exact-range reconciler, and diff checks passed at implementation commit
  `984af3602d171ee3b66cfbf0bdcc646330911e6f`. The final finite-model audit reported no
  blocker; identity labels remain deliberately conservative text, not authenticated
  principals.

## 2026-08-04 — checkpoint one-time claimant derivation (codex sol-high implementer)

- The eleventh panel reviewed exact revision
  `ea4bb732e2e4c1d0d4c2a3733298d40652fb9215` and returned 2 approve, 1 block. The accepted
  performance finding was that both core admission and action neutralization rebuilt and
  resorted the full composite claimant for every verdict.
- A new key-level independence helper accepts precomputed reviewer and claimant keys. The
  public identity helper remains compatible and delegates after deriving each side once.
  Action neutralization now derives claimant keys once per document; core validation does
  so once per task and reuses the already computed reviewer key for exact vote dedup.
- Composite component dedup now also uses a set while preserving ordered output and whole
  repeated-component multiplicity.
- Deterministic focused tests use a 256-character claimant and 256 verdicts. They prove
  claimant derivation is called exactly once and reviewer key derivation exactly 256 times
  in both action neutralization and core validation; existing composite/self/independent
  semantics remain unchanged. The focused slice passed 5/5 in 0.221s.
- The implementation was committed as
  `1abfc8d2d2e9f1baf184398f0591cb7e8632eef9`. Its staged hook passed core scope,
  reconciliation, and 13/13 registered repository test files in 79.74s.
- At the owner's wrap-up request, no additional manual full suite was started. Remaining
  work is the deferred owning/full/exact-range verification and final durable eleventh-panel
  record before a new independent revision-bound panel.

## 2026-08-05 — complete deferred claimant-precompute verification (codex terra verifier)

- Resumed from exact checkpoint `d39aedcf3b5c84e3b4ba411d0802f90c54f0ef2d`
  without changing the implementation or adding a review receipt.
- Re-ran the deterministic 5-test performance slice, all three owning modules, and the
  full repository suite. They passed 5/5 in 0.370s, 317 tests with one skip in 37.062s,
  and 15/15 files in 123.93s respectively.
- The exact task range passed the core-scope gate with 8 core paths. The first sandboxed
  reconciler attempt exposed a recovered index stat-cache difference and then failed to
  acquire the linked worktree index lock; the coordinating root session refreshed the
  shared index with escalated access and the exact-range retry reported zero findings.
- The exact-range diff check passed and the checkpoint branch was clean and tracking its
  remote. Plan step 20 is complete. Independent exact-revision review, publication,
  merge, issue closure, and the stale-base repair remain pending in steps 21 and 22.

## 2026-08-05 — repair the twelfth-panel blockers (codex sol-high implementer)

- The twelfth panel reviewed exact revision
  `1f79e4802b5d492d7388022eab453795155e3651` and returned 0 approve, 3 block. The
  accepted blockers were unbounded claimant-component comparisons, start-anchored
  reviewer or finding commands hidden by a formal receipt prefix, and action identity
  keys that collapsed accented names into ASCII spellings.
- Composite claimants now fail closed above 16 components. One shared helper derives the
  claimant once, normalizes each distinct reviewer source once, memoizes independence by
  reviewer key, and supplies the same accepted matches to core admission and action
  classification. Maximum-shape 16-component, 256-verdict tests record one independence
  comparison in both consumers; a 17-component claimant is rejected.
- Task-action classification blanks accepted receipt lines from its ordinary prose view
  and scans exact reviewer and finding components as standalone units. The compatibility
  neutralizer retains its equal-width verdict-token behavior. Regressions cover hostile
  reviewer and finding commands, pending approval, a do-not-merge directive, benign
  receipt text, task origin, and malformed/self receipts.
- Detection normalization still folds marks so combining characters cannot split an
  action keyword. Action identity and Counter normalization now use NFKC/casefold while
  preserving marks, so composed/decomposed `José` compare equal and ASCII `Jose` remains
  distinct. Projection, task-origin Counter, and handover bindings cover that boundary.
- The focused eight-test repair set passed in 2.708s, all four owning modules passed 777
  tests with one skip in 241.185s, and the full 15-file repository suite passed in
  141.90s. A new exact-revision approving panel, publication, and merge remain pending.

## 2026-08-05 — independently rerun the repaired tree (codex sol-high verifier)

- Took over the repair after the implementation session became unresponsive. The staged
  diff matched the three accepted blockers and needed no further code change.
- The focused eight-test slice passed in 4.928s, all four owning modules passed 777 tests
  with one skip in 260.371s, and the isolated full suite passed all 15 files in 146.75s.
- The interrupted implementation process completed commit `9fd8c258` while verification
  was running. The same tree was tested throughout; the takeover session did not amend
  that commit. This follow-up records independent evidence only. Final revision-bound
  review, publication, and merge remain pending.

## 2026-08-05 — repair the final panel blockers (codex sol-high implementer)

- The final panel reviewed exact revision
  `a87701ccbb493c561eece7691997703f0ec394cb` and returned 0 approve, 3 block. The
  accepted blockers were the template's missing claimant-component ceiling, unbounded
  identity-key lengths preserving quadratic comparison work, and addressed `block`
  commands missed inside accepted reviewer or finding units.
- Replaced sorted identity strings with fixed 36-bin ASCII-alphanumeric count vectors.
  The sentinel and outer tuple shape, multiset equality, containment, anagram, distance,
  placeholder, component-union, and duplicate-vote semantics remain unchanged. Long
  claimant and 64 unique long-reviewer regressions prove each pair visits fixed-size keys.
- Kept the 16-component ceiling and made the canonical verification template state the
  exact maximum and that 17 components invalidate all claimant authority. A registered
  input-owner test now binds the template wording to the enforced constant.
- Added `block` to guarded ambiguous authority commands and the explicit task-record
  authority vocabulary. Reviewer and finding components now expose addressed commands
  under either structural verdict, while benign formal verdicts stay inert and the
  declarative summary `Block size is 4096 bytes.` stays non-actionable.
- The focused 10-test slice, 325 parser/projection/core tests, 458 task-origin/reconciler
  tests, 67 staged-lane tests, and all 15 repository test files passed. The first broad
  owning attempt was interrupted after the final grammar adjustment and is not counted.
- The first committed exact-range reconciler then exposed 33 historical panel lines shaped
  as `reviewer: block — finding` that the new general token had retroactively classified
  as asks. The guarded ambiguous form now excludes only that completed-evidence
  continuation; addressed commands and malformed ASCII-hyphen near-misses remain visible.
- The compatibility-focused four tests and all six staged owners passed after that repair.
  The full repository rerun passed all 15 files in 139.65s, and exact committed revision
  `6c9568b6833a2f3b77eaa6b8581b6e920c0bbc27` passed nine-path core scope, the reconciler
  with zero findings, and the range diff check. A fresh independent review must bind the
  later record checkpoint, not this pre-record revision.

## 2026-08-05 — scope completed-panel compatibility (codex sol-high implementer)

- The final3 panel reviewed exact revision
  `c5d676988eabb248f66000ecb2f3b72c47ef46b1` and returned 1 approve, 2 block. Both
  blockers identified the global em-dash exception after `block`, which also hid ordinary
  addressed commands such as `Owner, block — this release.` outside receipts.
- Removing the exception reproduced exactly 33 task-action findings, all completed
  adversarial-panel block records in this task verification file. The active path was
  `task_action_unit_counts` to `action_like_task_record_prose` to
  `TASK_AUTHORITY_DIRECTIVE_RE`, whose match was `: block`; the general verb regex also
  saw the token but did not decide task-record actionability.
- Both general grammars now recognize em-dash block commands. Task records retain the
  declarative-summary guard, so `Block size is 4096 bytes.` remains inert.
- Compatibility now exists only in the task-root verification classification view. It
  removes an exact visible lowercase adversarial-panel evidence line, scans its stable
  reviewer and nonempty same-line finding independently, and never changes formal
  core-fit receipt authority. Wrong panels, reviewer shapes, punctuation, casing, and
  out-of-region core-fit lines remain ordinary actions.
- Focused coverage passed 6 tests in 1.210s, the two directly affected owning modules
  passed 630 tests in 214.386s, and the full isolated suite passed all 15 files in
  142.15s. The staged diff, two-path core-scope gate, and reconciler also passed before
  the implementation checkpoint `50f2cf5da74524087dabc3dfefeeb627b045c767`.
- The commit hook passed all six registered owner files in 72.65s. An initial exact-range
  command used an abbreviated head that core scope accepted but the reconciler correctly
  rejected; the immediate full-object-ID retry passed nine-path core scope, reconciliation
  with zero findings, and the range diff check. The review candidate remains without an
  approving receipt or status move.

## 2026-08-05 — preserve human-visible completed findings (codex sol-high implementer)

- The final4 panel reviewed exact revision
  `7ddab99d446bf6befcd26b57515325c9a49fd436` and returned 1 approve, 2 block. The
  accepted blockers were a conjoined courtesy command missed in an accepted formal
  finding and image, reference-link, or inline-code decoration hidden when historical
  panel compatibility removed the complete source line.
- Kept the whole exact historical panel line in the task-root verification
  classification view and blanks only its exact lowercase completed verdict token.
  The full-source context renders visible finding labels and inline-code contents;
  reviewer and finding units receive the same scoped completed-review classifier.
- Added only the guarded ASCII `and` plus `please`/`kindly` completed-review rule. It is
  not part of general task or provider prose, and benign approved-evidence, recorded
  approval, bare conjoined verbs, and code-description cases remain inert.
- Each historical panel occurrence now contributes at most one action even when both
  the whole-line and component paths match. Two duplicate hostile lines remain two
  Counter occurrences. Exact lowercase `approve` and `block` token compatibility is
  explicit; malformed panel shapes remain ordinary prose.
- The focused six-test slice passed in 2.242s, the two owning modules passed 634 tests
  in 227.864s, and the full isolated repository suite passed all 15 files in 145.19s.
  The task remains in progress without an approving receipt, status move, publication,
  or GitHub mutation.

## 2026-08-05 — continuation handover (codex planner)

- Recorded the clean checkpoint `df0a5de03d37c5046354513b011ccb4578d571c7` and the
  completed verification evidence for the next session in the
  [continuation handover](../../../history/conversations/2026-08-05-1330PDT-continue-review-receipt-parser/handover.md).
- Remaining sequence: obtain a fresh three-way independent review of that exact revision,
  record only its receipt and worklog evidence, move the task to review, then push, open,
  merge, and close GitHub issue #80.

## 2026-08-07 — sixteenth panel blocked the change (claude opus 5 orchestrator)

- Recreated the task worktree after every prior worktree was lost: they had been created
  under the system temporary directory, which the operating system cleared between sessions. No commit was
  lost, but `task/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check` was still
  unpushed and existed only in this clone. `handbook/git-workflow.md` already prescribes
  `../<task-id>`; the worktrees now live there.
- Ran a three-lens independent panel on `ccbb9e4854faf42dc423638e6b6b39a284608f4b`. The
  vote was 0 approve, 3 block. Findings and reproductions are in
  [verification.md](verification.md) under the sixteenth-panel section.
- The decisive finding is a fail-open on the merge gate's own output: a finding leaving the
  closed source alphabet ends the receipt and discards its verdict and every later verdict,
  so a one-approve, two-block panel is reported as one approve, zero block and passes. The
  orchestrating session reproduced this independently before recording it.
- The task stays in `1_in-progress` with no pull request. Nothing was published, and the
  dependent stale-base and bootstrap work is unchanged by this session's finding.
- Filed the strategic question for the owner rather than starting a seventeenth repair
  round, because the authorized decision described a smaller and fail-closed parser.
