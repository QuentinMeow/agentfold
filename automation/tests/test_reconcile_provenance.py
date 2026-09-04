"""Owner words, labelled criteria, goal fit, and roadmap goal entries.

Four reconciler check ids, each observed green on an undamaged fixture and red on a
fixture damaged for that finding's own reason: blocking `task-provenance` and
`roadmap-goals`, advisory `task-provenance-advice` and `roadmap-goals-advice`. The
fixtures carry no `.git`, which is the reconciler's no-Git tree mode, because none of
these checks read history: they read the task folders, the roadmap, and the queue.
"""

import contextlib
import datetime
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "reconcile" / "reconcile.py"
SPEC = importlib.util.spec_from_file_location("reconcile_provenance", MODULE_PATH)
RECONCILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECONCILE)

# Filed on or after TASK_PROVENANCE_SINCE, so the blocking rules apply.
NEW_TASK = "2026-09-10-example"
# Filed before it, so only the advisory reminder applies while the task is live.
OLD_TASK = "2026-07-23-example"
CLARIFICATION = "message-queue/needs-human/clarifications/non-blocking-which-goal.md"
DECISION = "message-queue/needs-human/decisions/non-blocking-goal-or-request.md"
G1_TITLE = "Keep the owner's words in every task"
G2_TITLE = "A goal an agent proposed"
G3_TITLE = "A goal the owner retired"
PROPOSED = f"no — agent-proposed, clarification `{CLARIFICATION}`"

REQUIREMENTS = (
    "# Requirements — Example\n\n"
    "Owner words only, verbatim and dated.\n\n"
    "## 2026-09-10 — chat\n\n"
    "```text\nmake the thing\n```\n"
)
NO_WORDS = (
    "# Requirements — Example\n\n"
    "Owner words only, verbatim and dated.\n\n"
    "No owner words — filed by test from `docs/audit.md`.\n"
)
CRITERIA = (
    "- [ ] [user 2026-09-10] WHEN a thing is asked, THE SYSTEM SHALL make it.\n"
    "- [x] [derived] A test covers it — because the owner's words need proof.\n"
)
DERIVED_ONLY = "- [ ] [derived] A test covers it — because the words need proof.\n"


def fit_section(serves=f"G1 — {G1_TITLE}", fit="aligned — the request sits inside G1.",
                today="nothing keeps the owner's words today."):
    return (
        "## Fit\n\n"
        f"**Serves:** {serves}\n"
        f"**Today:** {today}\n"
        f"**Fit:** {fit}\n\n"
    )


def task_text(scope="core", queue_actions="none", criteria=CRITERIA, fit=None):
    fit = fit_section() if fit is None else fit
    return (
        "# Example\n\n"
        "**Claimed-by:** test\n"
        "**Filed:** 2026-09-10, by test, from chat\n"
        "**Parent:** none\n"
        f"**Repository scope:** {scope}\n"
        f"**Queue actions:** {queue_actions}\n\n"
        "## Goal\n\nMake the thing.\n\n"
        "## Acceptance criteria\n\n"
        + criteria + "\n"
        + fit
        + "## Links\n\n- none\n"
    )


def goal_entry(goal_id, title, asked="2026-09-04, by the owner, from chat",
               state="**Confirmed:** 2026-09-04 by owner", words="keep my words"):
    return (
        f"## {goal_id} — {title}\n\n"
        f"**Asked:** {asked}\n"
        f"{state}\n\n"
        f"```text\n{words}\n```\n\n"
        "Done means the goal is met. *(Not started.)*\n\n"
    )


def roadmap_text(*entries):
    if not entries:
        entries = (
            goal_entry("G1", G1_TITLE),
            goal_entry(
                "G2", G2_TITLE,
                asked="2026-09-01, by agent test, from `docs/design.md`",
                state=f"**Confirmed:** {PROPOSED}",
                words="the sentence to confirm",
            ),
        )
    return (
        "# Desired state\n\n"
        "**Last-updated:** 2026-09-04\n\n"
        "Goal entries in priority order.\n\n"
        + "".join(entries)
    )


RETIRED_G3 = goal_entry(
    "G3", G3_TITLE,
    asked="2026-07-01, by agent test, from `docs/design.md`",
    state="**Retired:** 2026-09-01 — `memory/decisions/2026-09-01-retire-g3.md`",
    words="old words",
)


class ReconcileProvenanceTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self, today=datetime.date(2026, 9, 20)):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replacements = {
                "REPO": root,
                "QUEUE": root / "message-queue",
                "RETRIES": root / "message-queue" / "needs-agent" / "retries",
                "TASKS": root / "tasks",
                "CONVERSATIONS": root / "history" / "conversations",
                "MEMORY": root / "memory",
                "TODAY": today,
                "ACTIVE_TASK_ID": None,
                "ACTIVE_TRANSITIONS": set(),
                "CHANGE_RANGE": None,
                "DISPLACED_TIP": None,
            }
            with mock.patch.multiple(RECONCILE, **replacements):
                yield root

    @staticmethod
    def write(root, rel, text=""):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    @staticmethod
    def messages(findings):
        return [finding.message for finding in findings]

    def findings(self, check):
        return self.messages(list(RECONCILE.CHECKS[check]()))

    def roadmap(self, root, text=None):
        self.write(root, "roadmap/desired-state.md",
                   roadmap_text() if text is None else text)
        self.write(root, CLARIFICATION, "# Which goal does this serve?\n")
        self.write(root, DECISION, "# The goal or the request?\n")
        self.write(root, "memory/decisions/2026-09-01-retire-g3.md", "# Retire G3\n")
        self.write(root, "docs/design.md", "# Design\n")

    def task(self, root, task_id=NEW_TASK, status="1_in-progress", text=None,
             requirements=REQUIREMENTS):
        task = root / "tasks" / status / task_id
        task.mkdir(parents=True)
        (task / "task.md").write_text(
            task_text() if text is None else text, encoding="utf-8"
        )
        if requirements is not None:
            (task / "requirements.md").write_text(requirements, encoding="utf-8")
        if status != "0_backlog":
            (task / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (task / "worklog.md").write_text("# Worklog\n", encoding="utf-8")
        return task

    def assertOnly(self, expected_fragments, findings):
        """Every finding matches one expected fragment, and every fragment is found."""
        self.assertEqual(len(expected_fragments), len(findings), findings)
        for fragment in expected_fragments:
            self.assertTrue(
                any(fragment in message for message in findings),
                f"{fragment!r} not in {findings}",
            )

    # --- registration -----------------------------------------------------------

    def test_the_four_check_ids_are_registered_with_one_severity_each(self):
        blocking = ("task-provenance", "roadmap-goals")
        advisory = ("task-provenance-advice", "roadmap-goals-advice")
        for check in blocking + advisory:
            self.assertIn(check, RECONCILE.CHECKS)
        for check in blocking:
            self.assertNotIn(check, RECONCILE.ADVISORY_CHECKS)
            self.assertEqual(
                "blocking", RECONCILE.Finding(check, "x", "", "").severity
            )
        for check in advisory:
            self.assertIn(check, RECONCILE.ADVISORY_CHECKS)
            self.assertEqual(
                "advisory", RECONCILE.Finding(check, "x", "", "").severity
            )
        # One function per id, so a registry pass reports each finding once.
        self.assertEqual(
            4, len({RECONCILE.CHECKS[check] for check in blocking + advisory})
        )
        self.assertEqual(datetime.date(2026, 9, 4), RECONCILE.TASK_PROVENANCE_SINCE)

    # --- task-provenance: green -------------------------------------------------

    def test_a_new_task_with_words_labels_and_a_fit_passes_every_check(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root)
            for check in (
                "task-provenance", "task-provenance-advice",
                "roadmap-goals", "roadmap-goals-advice",
            ):
                with self.subTest(check=check):
                    self.assertEqual([], self.findings(check))

    def test_the_no_owner_words_line_with_a_goal_passes(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(
                root, text=task_text(criteria=DERIVED_ONLY), requirements=NO_WORDS
            )
            self.assertEqual([], self.findings("task-provenance"))

    def test_a_copied_template_comment_and_fenced_words_are_not_read(self):
        """The template's guidance comment survives a copy; the fence holds data."""
        with self.repo() as root:
            self.roadmap(root)
            copied = REQUIREMENTS + (
                "\n<!-- A task with no owner words keeps this single line:\n"
                "No owner words — filed by <who> from `<durable source path>`. -->\n"
            )
            self.task(root, requirements=copied)
            self.assertEqual([], self.findings("task-provenance"))
        with self.repo() as root:
            self.roadmap(root)
            fenced = (
                "# Requirements — Example\n\n"
                "```text\nNo owner words — filed by x from `docs/y.md`.\n```\n"
            )
            self.task(root, requirements=fenced)
            self.assertOnly(
                ["holds neither a dated owner entry nor the no-owner-words line"],
                self.findings("task-provenance"),
            )

    # --- task-provenance: red, one reason each ---------------------------------

    def test_a_new_task_without_requirements_is_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, requirements=None)
            self.assertOnly(["missing requirements.md"], self.findings("task-provenance"))

    def test_an_entry_needs_a_text_fence_with_words_under_it(self):
        cases = (
            ("no fence", "## 2026-09-10 — chat\n\nmake the thing\n"),
            ("empty fence", "## 2026-09-10 — chat\n\n```text\n\n```\n"),
            ("unclosed fence", "## 2026-09-10 — chat\n\n```text\nmake the thing\n"),
            ("plain fence", "## 2026-09-10 — chat\n\n```\nmake the thing\n```\n"),
        )
        for name, body in cases:
            with self.subTest(case=name), self.repo() as root:
                self.roadmap(root)
                self.task(root, requirements="# Requirements — Example\n\n" + body)
                self.assertOnly(
                    ["`## 2026-09-10 — chat` is not followed by a ```text fence"],
                    self.findings("task-provenance"),
                )

    def test_a_heading_that_is_not_a_dated_entry_is_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, requirements=REQUIREMENTS + "\n## Interpretation\n\nours\n")
            self.assertOnly(
                ["heading `## Interpretation` is not a dated owner entry"],
                self.findings("task-provenance"),
            )

    def test_both_or_neither_owner_words_are_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            both = REQUIREMENTS + "\nNo owner words — filed by test from `docs/a.md`.\n"
            self.task(root, requirements=both)
            self.assertOnly(
                ["carries both dated owner entries and the no-owner-words line"],
                self.findings("task-provenance"),
            )
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, requirements="# Requirements — Example\n\nOwner words only.\n")
            self.assertOnly(
                ["holds neither a dated owner entry nor the no-owner-words line"],
                self.findings("task-provenance"),
            )

    def test_every_criterion_carries_a_label_that_resolves(self):
        cases = (
            (
                "- [ ] WHEN a thing is asked, THE SYSTEM SHALL make it.\n",
                "acceptance criterion lacks a provenance label",
            ),
            (
                "- [ ] [user 2026-09-11] WHEN a thing is asked, THE SYSTEM SHALL make it.\n",
                "cites `[user 2026-09-11]` but requirements.md has no entry dated 2026-09-11",
            ),
            (
                "- [x] [derived] A test covers it.\n",
                "`[derived]` criterion gives no reason",
            ),
        )
        for criteria, expected in cases:
            with self.subTest(criteria=criteria), self.repo() as root:
                self.roadmap(root)
                self.task(root, text=task_text(criteria=criteria))
                self.assertOnly([expected], self.findings("task-provenance"))

    def test_fit_is_required_from_in_progress_for_behaviour_changing_scope(self):
        required = (("core", "1_in-progress"), ("service:api", "4_done"),
                    ("core", "2_blocked"), ("core", "3_in-review"))
        for scope, status in required:
            with self.subTest(scope=scope, status=status), self.repo() as root:
                self.roadmap(root)
                self.task(root, status=status, text=task_text(scope=scope, fit=""))
                self.assertOnly(["missing `## Fit` section"], self.findings("task-provenance"))
        exempt = (("core", "0_backlog"), ("records-only", "1_in-progress"))
        for scope, status in exempt:
            with self.subTest(scope=scope, status=status), self.repo() as root:
                self.roadmap(root)
                self.task(root, status=status, text=task_text(scope=scope, fit=""))
                self.assertEqual([], self.findings("task-provenance"))

    def test_a_placeholder_fit_line_is_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=fit_section(today="<tbd>")))
            self.assertOnly(
                ["`## Fit` needs a concrete **Today:** line"],
                self.findings("task-provenance"),
            )

    def test_no_owner_words_and_no_goal_is_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(
                root,
                text=task_text(
                    criteria=DERIVED_ONLY,
                    queue_actions=f"`{CLARIFICATION}`",
                    fit=fit_section(serves=f"none — `{CLARIFICATION}`"),
                ),
                requirements=NO_WORDS,
            )
            self.assertOnly(
                ["neither owner words nor a goal"], self.findings("task-provenance")
            )
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(criteria=DERIVED_ONLY, fit=""),
                      requirements=NO_WORDS)
            self.assertOnly(
                ["missing `## Fit` section", "neither owner words nor a goal"],
                self.findings("task-provenance"),
            )

    def test_serves_names_an_existing_goal_or_a_listed_clarification(self):
        missing = "message-queue/needs-human/clarifications/non-blocking-missing.md"
        cases = (
            ("G7 — A goal nobody wrote", "none",
             "**Serves:** names G7, which is not a `## G7 — ` heading"),
            (f"none — `{missing}`", "none",
             f"**Serves:** none names `{missing}`, which is not a live item"),
            (f"none — `{DECISION}`", f"`{DECISION}`",
             f"**Serves:** none names `{DECISION}`, which is not a live item"),
            (f"none — `{CLARIFICATION}`", "none",
             f"**Serves:** none names `{CLARIFICATION}`, which **Queue actions:** does not list"),
            ("whatever", "none",
             "**Serves:** is neither `G<n> — <the goal's title>`"),
        )
        for serves, queue_actions, expected in cases:
            with self.subTest(serves=serves), self.repo() as root:
                self.roadmap(root)
                self.task(root, text=task_text(
                    queue_actions=queue_actions, fit=fit_section(serves=serves)
                ))
                self.assertOnly([expected], self.findings("task-provenance"))
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(
                queue_actions=f"`{CLARIFICATION}`",
                fit=fit_section(serves=f"none — `{CLARIFICATION}`"),
            ))
            self.assertEqual([], self.findings("task-provenance"))

    def test_a_fit_section_is_checked_on_a_task_filed_before_activation(self):
        """Opting in to `## Fit` means the section is held to its schema, whatever the date."""
        with self.repo() as root:
            self.roadmap(root)
            self.task(
                root, task_id=OLD_TASK, requirements=None,
                text=task_text(fit=fit_section(serves="G7 — A goal nobody wrote")),
            )
            self.assertOnly(
                ["**Serves:** names G7, which is not a `## G7 — ` heading"],
                self.findings("task-provenance"),
            )

    def test_the_fit_value_and_its_queue_item(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=fit_section(fit="maybe — who knows.")))
            self.assertOnly(
                ["**Fit:** 'maybe — who knows.' does not open with aligned"],
                self.findings("task-provenance"),
            )
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=fit_section(fit="conflicts — G1 says otherwise.")))
            self.assertOnly(
                ["**Fit:** conflicts without a needs-human clarification or decision"],
                self.findings("task-provenance"),
            )
        for value, listed in (("conflicts", DECISION), ("unclear", CLARIFICATION)):
            with self.subTest(value=value), self.repo() as root:
                self.roadmap(root)
                self.task(root, text=task_text(
                    queue_actions=f"`{listed}`",
                    fit=fit_section(fit=f"{value} — the owner decides."),
                ))
                self.assertEqual([], self.findings("task-provenance"))

    # --- task-provenance-advice -------------------------------------------------

    def test_all_derived_criteria_while_serving_a_goal_is_advisory(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(criteria=DERIVED_ONLY))
            self.assertEqual([], self.findings("task-provenance"))
            self.assertOnly(
                ["every acceptance criterion is `[derived]` while the task serves G1"],
                self.findings("task-provenance-advice"),
            )
        with self.repo() as root:
            self.roadmap(root)
            self.task(root)
            self.assertEqual([], self.findings("task-provenance-advice"))

    def test_a_stale_title_copy_and_an_unconfirmed_goal_are_advisory(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=fit_section(serves="G1 — An older title")))
            self.assertEqual([], self.findings("task-provenance"))
            self.assertOnly(
                ["**Serves:** copies a title that differs from the current `## G1 — "
                 + G1_TITLE + "`"],
                self.findings("task-provenance-advice"),
            )
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=fit_section(serves=f"G2 — {G2_TITLE}")))
            self.assertEqual([], self.findings("task-provenance"))
            self.assertOnly(
                ["G2 is agent-proposed and not yet confirmed by the owner"],
                self.findings("task-provenance-advice"),
            )

    def test_a_task_filed_before_activation_gets_advice_only_while_live(self):
        unlabelled = "- [ ] WHEN a thing is asked, THE SYSTEM SHALL make it.\n"
        live = (
            ("1_in-progress", "core",
             ["has no requirements.md", "has no `## Fit` section"]),
            ("2_blocked", "core",
             ["has no requirements.md", "has no `## Fit` section"]),
        )
        for status, scope, expected in live:
            with self.subTest(status=status), self.repo() as root:
                self.roadmap(root)
                self.task(root, task_id=OLD_TASK, status=status, requirements=None,
                          text=task_text(scope=scope, criteria=unlabelled, fit=""))
                self.assertEqual([], self.findings("task-provenance"))
                self.assertOnly(expected, self.findings("task-provenance-advice"))
        for status in ("0_backlog", "3_in-review", "4_done"):
            with self.subTest(status=status), self.repo() as root:
                self.roadmap(root)
                self.task(root, task_id=OLD_TASK, status=status, requirements=None,
                          text=task_text(criteria=unlabelled, fit=""))
                self.assertEqual([], self.findings("task-provenance"))
                self.assertEqual([], self.findings("task-provenance-advice"))

    def test_a_user_label_with_only_the_no_owner_words_line_is_refused(self):
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, requirements=NO_WORDS)
            self.assertOnly(
                ["criterion cites `[user 2026-09-10]` but requirements.md has no entry dated 2026-09-10"],
                self.findings("task-provenance"),
            )

    def test_an_untouched_template_fit_is_judged_only_where_a_fit_is_due(self):
        template = (
            "## Fit\n\n"
            "**Serves:** <G<n> — the goal's title copied exactly | none — `<needs-human clarification path>`>\n"
            "**Today:** <the current-state fact this task changes, one sentence>\n"
            "**Fit:** <aligned | extends | conflicts | unclear> — <one sentence on how the request meets the goal and today>\n\n"
        )
        for status, scope in (("0_backlog", "core"), ("1_in-progress", "records-only")):
            with self.subTest(status=status, scope=scope), self.repo() as root:
                self.roadmap(root)
                self.task(root, status=status, text=task_text(scope=scope, fit=template))
                self.assertEqual([], self.findings("task-provenance"))
        with self.repo() as root:
            self.roadmap(root)
            self.task(root, text=task_text(fit=template))
            self.assertOnly(
                ["`## Fit` needs a concrete **Serves:** line",
                 "`## Fit` needs a concrete **Today:** line",
                 "`## Fit` needs a concrete **Fit:** line"],
                self.findings("task-provenance"),
            )

    def test_an_absolute_clarification_path_is_refused_without_crashing_the_advice(self):
        absolute = "/tmp/elsewhere/non-blocking-which-goal.md"
        roadmap = roadmap_text(goal_entry("G1", G1_TITLE), goal_entry(
            "G2", G2_TITLE, asked="2026-07-01, by agent test, from `docs/design.md`",
            state=f"**Confirmed:** no — agent-proposed, clarification `{absolute}`",
        ))
        with self.repo(today=datetime.date(2026, 10, 15)) as root:
            self.roadmap(root, roadmap)
            self.assertOnly(
                [f"G2 names clarification `{absolute}`, which is not a live item"],
                self.findings("roadmap-goals"),
            )
            self.assertOnly(
                ["G2 has been agent-proposed for 106 days without the owner's confirmation"],
                self.findings("roadmap-goals-advice"),
            )

    def test_a_retired_goal_names_an_existing_decision(self):
        roadmap = roadmap_text(goal_entry("G1", G1_TITLE), RETIRED_G3)
        with self.repo() as root:
            self.roadmap(root, roadmap)
            self.assertEqual([], self.findings("roadmap-goals"))
        with self.repo() as root:
            self.roadmap(root, roadmap)
            (root / "memory/decisions/2026-09-01-retire-g3.md").unlink()
            self.assertOnly(
                ["G3 names decision `memory/decisions/2026-09-01-retire-g3.md`, which does not exist"],
                self.findings("roadmap-goals"),
            )
        with self.repo() as root:
            self.roadmap(root, roadmap_text(goal_entry("G1", G1_TITLE), goal_entry(
                "G3", G3_TITLE, asked="2026-07-01, by agent test, from `docs/design.md`",
                state="**Retired:** 2026-09-01 — a decision without a path",
            )))
            self.assertOnly(
                ["G3 carries a **Retired:** line without a date and a backticked decision path"],
                self.findings("roadmap-goals"),
            )

    # --- roadmap-goals ----------------------------------------------------------

    def test_a_roadmap_with_confirmed_proposed_and_retired_goals_passes(self):
        with self.repo() as root:
            self.roadmap(root, roadmap_text(
                goal_entry("G1", G1_TITLE),
                goal_entry("G2", G2_TITLE, state=f"**Confirmed:** {PROPOSED}"),
                RETIRED_G3,
            ))
            self.assertEqual([], self.findings("roadmap-goals"))
            self.assertEqual([], self.findings("roadmap-goals-advice"))

    def test_a_repository_without_a_roadmap_has_nothing_to_check(self):
        with self.repo() as root:
            self.task(root, text=task_text(fit=""))
            self.assertEqual([], self.findings("roadmap-goals"))
            self.assertEqual([], self.findings("roadmap-goals-advice"))

    def test_each_roadmap_defect_is_refused_for_its_own_reason(self):
        missing = "message-queue/needs-human/clarifications/non-blocking-missing.md"
        cases = (
            ("## Not a goal\n\nprose\n\n", "heading `## Not a goal` is not a goal entry"),
            (goal_entry("G1", "A second G1"), "goal id G1 appears more than once"),
            (goal_entry("G4", "No asker", asked="the owner, in chat"),
             "G4 lacks a dated **Asked:** line"),
            (goal_entry("G4", "Both states",
                        state="**Confirmed:** 2026-09-04 by owner\n"
                              "**Retired:** 2026-09-05 — `memory/decisions/x.md`"),
             "G4 needs exactly one of **Confirmed:** and **Retired:**"),
            (goal_entry("G4", "No state", state="**Status:** live"),
             "G4 needs exactly one of **Confirmed:** and **Retired:**"),
            (goal_entry("G4", "Undated retirement",
                        state="**Retired:** someday — `memory/decisions/x.md`"),
             "G4 carries a **Retired:** line without a date and a backticked decision path"),
            (goal_entry("G4", "Unreadable", state="**Confirmed:** yes"),
             "G4 has an unreadable **Confirmed:** value 'yes'"),
            (goal_entry("G4", "Missing item",
                        state=f"**Confirmed:** no — agent-proposed, clarification `{missing}`"),
             f"G4 names clarification `{missing}`, which is not a live item"),
            (goal_entry("G4", "Wrong leaf",
                        state=f"**Confirmed:** no — agent-proposed, clarification `{DECISION}`"),
             f"G4 names clarification `{DECISION}`, which is not a live item"),
        )
        for entry, expected in cases:
            with self.subTest(expected=expected), self.repo() as root:
                self.roadmap(root, roadmap_text(goal_entry("G1", G1_TITLE), entry))
                self.assertOnly([expected], self.findings("roadmap-goals"))

    def test_a_goal_heading_inside_a_fence_is_data(self):
        with self.repo() as root:
            self.roadmap(root, roadmap_text(goal_entry(
                "G1", G1_TITLE, words="## Not a goal\n\nquoted from the owner's document",
            )))
            self.assertEqual([], self.findings("roadmap-goals"))

    # --- roadmap-goals-advice ---------------------------------------------------

    def test_an_unconfirmed_goal_older_than_thirty_days_is_advisory(self):
        with self.repo(today=datetime.date(2026, 10, 15)) as root:
            self.roadmap(root)
            self.assertEqual([], self.findings("roadmap-goals"))
            self.assertOnly(
                ["G2 has been agent-proposed for 44 days without the owner's confirmation"],
                self.findings("roadmap-goals-advice"),
            )
        with self.repo(today=datetime.date(2026, 9, 20)) as root:
            self.roadmap(root)
            self.assertEqual([], self.findings("roadmap-goals-advice"))

    def test_the_unconfirmed_goal_clock_starts_when_the_clarification_was_filed(self):
        recent = "# Which goal does this serve?\n\n**Filed:** 2026-10-01, by test\n"
        old = "# Which goal does this serve?\n\n**Filed:** 2026-08-01, by test\n"
        with self.repo(today=datetime.date(2026, 10, 15)) as root:
            self.roadmap(root)
            self.write(root, CLARIFICATION, recent)
            self.assertEqual([], self.findings("roadmap-goals-advice"))
        with self.repo(today=datetime.date(2026, 10, 15)) as root:
            self.roadmap(root)
            self.write(root, CLARIFICATION, old)
            self.assertOnly(
                ["G2 has been agent-proposed for 75 days without the owner's confirmation"],
                self.findings("roadmap-goals-advice"),
            )

    def test_a_live_task_serving_a_retired_goal_is_advisory(self):
        roadmap = roadmap_text(goal_entry("G1", G1_TITLE), RETIRED_G3)
        with self.repo() as root:
            self.roadmap(root, roadmap)
            self.task(root, text=task_text(fit=fit_section(serves=f"G3 — {G3_TITLE}")))
            self.assertEqual([], self.findings("task-provenance"))
            self.assertOnly(
                ["**Serves:** names G3, which is retired"],
                self.findings("roadmap-goals-advice"),
            )
        with self.repo() as root:
            self.roadmap(root, roadmap)
            self.task(root, status="4_done",
                      text=task_text(fit=fit_section(serves=f"G3 — {G3_TITLE}")))
            self.assertEqual([], self.findings("roadmap-goals-advice"))


if __name__ == "__main__":
    unittest.main()
