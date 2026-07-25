# Worklog — isolate repository tests from Git hook state

## 2026-07-24 — layered-workspace-research (codex)

- A pre-commit run in a linked worktree moved `main` through synthetic test commits,
  set `core.bare=true`, injected the test identity, and replaced the linked-worktree
  index. The active task branch itself stayed intact.
- Reflog and remote-tracking evidence identified `acc23b6289f5ca66744718af379aba0468be93e2`
  as the exact prior `main`; recovery used compare-and-swap ref repair, exact config
  cleanup, and index-only reconstruction, preserving the human-answer transcription.
- Root cause traced to Git-local hook variables inherited by test subprocesses in
  `automation/run_tests.py`; no production fix was written before the regression.

## 2026-07-24 — test-runner-isolation-repair (codex)

- Claimed the main-side blocking repair, preserved the recovered task records, and
  reran the focused regression before implementation. Two tests failed because the
  isolation boundary did not exist; the preserved test also needed its final
  Python 3.7-compatible mock-call assertion.
- Added one canonical boundary in `automation/run_tests.py`: discover Git's complete
  local-variable list, fail closed on discovery error, remove every name from a copied
  environment, and pass that environment to each test process.
- Consolidated the repair on the layered workspace branch because the older isolation
  branch could not see the queue record that lives on `main`; no check was bypassed.
- Admitted the recovered records through the current backlog schema before making the
  claim durable; the earlier linked-worktree files had never been committed.
- The first consolidated claim commit ran all nine repository test files through the
  repaired runner and preserved the shared config, unrelated refs, and both other
  worktree indexes byte-for-byte.
- A detached linked worktree at revision `006783c5645a9a15df59c791f931087af72d342b`
  completed a real hook-driven commit. Shared config, all four durable branch refs,
  and every unrelated worktree index remained byte-identical; the disposable worktree
  was removed afterward.
- The first three-reviewer panel unanimously blocked revision `006783c`: successful
  but incomplete discovery could leak critical pointers, pre-receive quarantine state
  was outside Git's reported list, and the probe did not verify its own index/parent.
  The repair remains in progress and the blocking queue item stays live.
- A second candidate review found the fixed required-name baseline was both incomplete
  (`GIT_CONFIG` could leak) and incompatible with older Git, while repository-root
  child working directories still permitted ambient discovery. The replacement strips
  every inherited `GIT_*` name and starts each test behind a scratch-root ceiling.
- The focused five-test regression and all nine repository test files pass with that
  version-neutral boundary; each test file receives its own directory below one
  disposable scratch root outside the repository.
- A third panel found three remaining gaps: the tests did not exercise ambient
  `os.environ`, an unsafe or path-separator-containing temporary root could defeat the
  discovery ceiling, and the new empty working directory broke repository-relative
  tests while removing harmless Git identity/noninteractive settings.
- The next candidate validates that no Git repository is discoverable before running
  children, rejects unrepresentable ceiling paths, tests ambient contamination
  directly, restores only a closed safe-behavior set, and gives each test a copied
  `.git`-free view of the current working tree.
- The fourth panel unanimously blocked recursive `copytree`: it dereferenced dangling
  and looping symlinks, excluded valid nested directories named `tmp`, and multiplied
  ignored dependency trees once per test.
- The replacement enumerates exactly Git's tracked and non-ignored untracked paths,
  copies regular files, and recreates symlink objects without following them. Focused
  coverage includes a dangling link, a self-loop, a tracked nested tmp fixture, an
  untracked file, and an ignored `.venv`.
- The fifth panel found that recursion did not create an omitted parent directory and
  that comparing `rev-parse` output with `.strip()` corrupted legal trailing
  whitespace. Nested repositories now use their local `.git` marker, and the regression
  places one below an omitted parent with both trailing space and newline characters.
- The projection follows the owner-selected macOS/Linux baseline. Windows runs the
  nonsymlink coverage and retains the existing Developer Mode/WSL limitation rather
  than claiming a portable symlink fallback.
- The sixth panel found that legal tracked files named like a bare repository could
  make the copied root discoverable after its initial topology check, and that a
  user-global `core.excludesFile` could silently remove untracked test inputs.
- Bare-shaped projected roots now receive an invalid `.git` boundary marker after
  files are copied, and enumeration pins `core.excludesFile` to the platform null file.
  The regression creates bare-shaped tracked files and a global excludes rule, then
  proves the view is not a repository and still contains the otherwise excluded fixture.
- The seventh panel reached a two-to-one no-blocker majority, but its dissent showed
  that an unconditional marker prevented an ordinary test from explicitly initializing
  its fresh current directory.
- The marker is now conditional on the completed projection already being a bare
  repository. The regression still proves the bare-shaped outer view is sealed and now
  also proves the ordinary nested view accepts `git init`.
- The eighth panel reached another two-to-one no-blocker majority. Its dissent found
  that the conditional check could discover a bare-shaped ancestor while examining a
  nested projection.
- The check now pins the candidate itself as `--git-dir=.`. The outer fixture includes
  an explicit bare config while the nested projection must remain unsealed and
  initializable.
- The ninth panel unanimously found no blocker in immutable revision `4d5f769`; all
  eleven focused tests and all nine repository test files passed on that revision.
  The exact-detection change leaves the linked-worktree process boundary unchanged
  from the latest byte-preserving probe.

## 2026-07-24 — stacked-publication-reconstruction (codex)

- Rebuilt the publication branch directly on message-queue review tail `c05e800`
  instead of publishing the earlier consolidated branch, whose history mixed this
  repair with the layered-workspace task.
- Preserved the final implementation and focused regression from the approved source.
  The runner differs from that source only in two documentation lines that state the
  bounded contract; the test module is byte-identical.
- Restored this task to `3_in-review`, resolved the agent repair action with same-commit
  implementation evidence, and filed one artifact-pending human merge review. Its
  exact base will be bound only after the preceding message-queue PR merges.
- The reconstructed range passes the exact task-scope gate, reconciler, and diff
  hygiene checks. The branch is published without rewriting its reviewed predecessor.

## 2026-07-24 — main-recovery-review (codex)

- Confirmed that PR #8 had been merged into PR #7's task branch after PR #7 had
  already merged to `main`; its implementation therefore never reached `main`.
- Replayed the exact PR #8 implementation on the latest origin/main and reviewed it
  as part of the stranded PR #8/#10 range with three independent reviewers.
- The panel unanimously blocked the old candidate. Two reviewers found that tests
  still executed by absolute path from the real checkout; one also found inherited
  global/system Git hooks, and one found all per-test repository copies remained live
  until the suite ended.
- Changed the runner to execute the projected test path, isolate `HOME`,
  `XDG_CONFIG_HOME`, global Git configuration, and system Git configuration, and
  delete each projection before creating the next one.
- Added regressions for projected execution, caller-global hooks, isolated Git
  configuration, and bounded projection lifetime. The focused and full suites pass.
- A fresh blast-radius review found that the first repair also removed ordinary
  config-backed Git identity, still copied the repository once per test, and could
  discover an ignored/generated test that was absent from the projected view.
- The runner now resolves only caller name/email into explicit author/committer
  variables, builds one suite-wide disposable view, and explicitly includes every
  discovered test path even when Git ignore rules exclude it.
- The next final-candidate review found that an ignored test's sibling helper/fixture
  tree was still absent, a test discovered through a directory symlink could write
  outside the scratch root during projection, and redirecting the whole child `HOME`
  would break unrelated toolchains.
- Test support directories are now projected without following directory symlinks,
  every destination path is checked against already projected symlinks, and only Git
  receives an isolated home through a disposable `PATH` wrapper. This remains
  compatible with the repository's Git 2.23 baseline, where
  `GIT_CONFIG_GLOBAL` alone is not enforced.
- The first full-suite run exposed a nested-runner case in the global-hook regression:
  an inner wrapper could select the already wrapped Git path and therefore reuse the
  outer wrapper's isolated configuration. The child now carries the validated original
  executable path, and both the focused regression and full projected suite pass.
- The following immutable-candidate panel found that ignored test support enumeration
  could still copy a linked-worktree `.git` file or nested `.git` directory. Support
  discovery now prunes both shapes, and materialization independently rejects every
  path containing a `.git` component.
- The next panel reproduced the same escape with a `.GIT` case variant on the
  supported default case-insensitive macOS filesystem. Both discovery and the
  independent materialization guard now compare every path component with
  `casefold()`.
- The next immutable review found that a bare-repository fixture needs no `.git`
  component and could remain active when copied below the suite root. The completed
  projection now finds and seals every bare-shaped directory without following
  symlinks, not only the root.
