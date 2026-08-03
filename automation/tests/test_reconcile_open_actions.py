"""Tests for the generated open-action list.

The digest is a projection of `message-queue/`, so every test here asks one of two
questions: does it say exactly what the queue says, and does it say it in the order a
person should read it. Nothing here asserts prose quality — a checker cannot see that
(`memory/decisions/2026-08-02-readability-enforcement-disposition.md`), and neither can
a test.

One test carries more weight than its size suggests:
`test_generated_bytes_do_not_depend_on_today` pins the constraint that makes a blocking
check safe here. If the digest ever rendered lateness, an untouched clean tree would
start failing the morning a deadline passed.
"""

import contextlib
import datetime
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "reconcile" / "reconcile.py"
)
SPEC = importlib.util.spec_from_file_location("reconcile_open_actions", MODULE_PATH)
RECONCILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECONCILE)

SCHEMA_MARKERS = (
    "**Queue resolution schema:** v1\n"
    "**Human-attention format:** v1\n"
)


def decision(action, why, unattended, answer_by="2026-10-31", status="waiting",
             response="______", extra=""):
    return (
        f"# Is this the thing?\n\n"
        f"**Action:** {action}\n"
        f"**Why this matters:** {why}\n"
        f"**If you do nothing:** {unattended}\n\n"
        f"## What you need to know\n\nSomething true about today.\n\n"
        f"**Your answer:** {response}\n\n"
        f"## For the record\n\n"
        f"**Status:** {status}\n"
        f"**Filed:** 2026-07-01, by claude\n"
        f"**Answer by:** {answer_by}\n"
        f"{extra}"
    )


def request(action, unattended, status="open", extra=""):
    return (
        f"# Do the thing\n\n"
        f"**Status:** {status}\n"
        f"**Filed:** 2026-07-01, by claude, from context\n"
        f"**Action:** {action}\n"
        f"**If unanswered:** {unattended}\n"
        f"{extra}"
        f"\n## What you need to know\n\nContext.\n\n## Done when\n\nIt is done.\n"
    )


class OpenActionListTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self, today=datetime.date(2026, 7, 23)):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "message-queue").mkdir()
            (root / "message-queue" / "AGENTS.md").write_text(
                SCHEMA_MARKERS, encoding="utf-8"
            )
            with mock.patch.multiple(
                RECONCILE,
                REPO=root,
                QUEUE=root / "message-queue",
                TODAY=today,
                CHANGE_RANGE=None,
            ):
                yield root

    @staticmethod
    def write(root, rel, text):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def regenerate(self, root):
        text = RECONCILE.generated_open_actions()
        (root / "message-queue" / "open-actions.md").write_text(
            text, encoding="utf-8"
        )
        return text

    # ------------------------------------------------------------ content

    def test_bullet_carries_the_items_own_action_and_links_it(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-pick-a-lane.md",
                decision("Choose the lane.", "Lanes matter.", "Nothing stops."),
            )
            text = RECONCILE.generated_open_actions()
        self.assertIn(
            "- [Choose the lane.]"
            "(needs-human/decisions/non-blocking-pick-a-lane.md)",
            text,
        )
        self.assertIn("**Why this matters:** Lanes matter.", text)
        self.assertIn("**If you do nothing:** Nothing stops.", text)

    def test_the_explanation_is_folded_and_the_action_is_not(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-pick-a-lane.md",
                decision("Choose the lane.", "Lanes matter.", "Nothing stops."),
            )
            text = RECONCILE.generated_open_actions()
        lines = text.splitlines()
        bullet = next(i for i, l in enumerate(lines) if l.startswith("- [Choose"))
        # The one visible sentence, then the disclosure, then a blank line — the
        # blank is what makes GitHub render Markdown inside the element.
        self.assertTrue(lines[bullet + 1].strip().startswith("<details>"))
        self.assertEqual(lines[bullet + 2], "")
        self.assertIn("</details>", text)
        self.assertNotIn("Lanes matter.", lines[bullet])

    def test_older_field_spelling_is_read_rather_than_shown_blank(self):
        """Ten live items still use the pre-rename field names, and may not be
        rewritten in place, so the digest reads both spellings."""
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-legacy.md",
                "# Legacy?\n\n**Action:** Decide it.\n"
                "**Why-you-might-care:** It is load-bearing.\n"
                "**If-you-do-nothing:** It stays as written.\n\n"
                "**Your answer:** ______\n\n"
                "**Status:** waiting\n**Filed:** 2026-07-01, by claude\n"
                "**Answer by:** 2026-10-31\n",
            )
            text = RECONCILE.generated_open_actions()
        self.assertIn("**Why this matters:** It is load-bearing.", text)
        self.assertIn("**If you do nothing:** It stays as written.", text)

    def test_an_item_with_no_consequence_field_renders_without_a_fold(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-bare.md",
                "# Bare\n\n**Status:** open\n**Filed:** 2026-07-01, by claude\n"
                "**Action:** Do the bare thing.\n",
            )
            text = RECONCILE.generated_open_actions()
        self.assertIn("- [Do the bare thing.]", text)
        self.assertNotIn("<details>", text)

    def test_a_bracket_in_an_action_cannot_end_the_link_label(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-brackets.md",
                request("Fix the [1] case.", "Nothing stops."),
            )
            text = RECONCILE.generated_open_actions()
        self.assertIn("- [Fix the \\[1\\] case.]", text)

    # ------------------------------------------------------------ ordering

    def test_actor_then_timing_then_date_is_the_order(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-agent-work.md",
                request("Agent work.", "Nothing stops."),
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-late.md",
                decision("Later question.", "why", "nothing", answer_by="2026-12-01"),
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-early.md",
                decision("Earlier question.", "why", "nothing", answer_by="2026-09-01"),
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-stopper.md",
                decision("Stopping question.", "why", "nothing",
                         answer_by="2026-12-31",
                         extra="**Blocks now:** operation:publish\n"),
            )
            text = RECONCILE.generated_open_actions()
        order = [
            text.index("Stopping question."),
            text.index("Earlier question."),
            text.index("Later question."),
            text.index("Agent work."),
        ]
        self.assertEqual(order, sorted(order))

    def test_the_headline_names_what_is_stopping_work(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-quiet.md",
                decision("A quiet question.", "why", "nothing"),
            )
            calm = RECONCILE.generated_open_actions()
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-loud.md",
                decision("A stopping question.", "why", "nothing",
                         extra="**Blocks now:** operation:publish\n"),
            )
            loud = RECONCILE.generated_open_actions()
        self.assertIn("**Nothing is stopping work.** 1 question waiting on you", calm)
        self.assertIn("**1 action stopping work right now.**", loud)
        self.assertNotIn("(s)", calm)

    # ------------------------------------------- what is and is not the owner's

    def test_an_answered_item_leaves_the_owners_section(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-answered.md",
                decision("Already decided.", "why", "nothing",
                         response="Yes, do option B.", status="waiting"),
            )
            text = RECONCILE.generated_open_actions()
        head, _, tail = text.partition("## Not yours right now")
        self.assertNotIn("Already decided.", head)
        self.assertIn("Already decided.", tail)
        self.assertIn("already answered — an agent owes the fold", tail)

    def test_a_folding_item_leaves_the_owners_section(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-folding.md",
                decision("Being folded.", "why", "nothing", status="folding"),
            )
            text = RECONCILE.generated_open_actions()
        head, _, tail = text.partition("## Not yours right now")
        self.assertNotIn("Being folded.", head)
        self.assertIn("status folding", tail)

    def test_repeated_pickup_requests_collapse_into_one_counted_line(self):
        with self.repo() as root:
            for slug in ("alpha", "beta", "gamma"):
                self.write(
                    root,
                    f"message-queue/needs-agent/requests/"
                    f"non-blocking-pick-up-{slug}.md",
                    request(
                        "When this backlog item is selected, claim it.",
                        "It stays unclaimed.",
                        extra="**Request kind:** task-pickup\n",
                    ),
                )
            text = RECONCILE.generated_open_actions()
        self.assertIn("- **3 backlog tasks are waiting for an agent", text)
        self.assertEqual(text.count("When this backlog item is selected"), 0)
        self.assertIn("- [alpha](needs-agent/requests/"
                      "non-blocking-pick-up-alpha.md)", text)

    # --------------------------------------------------------- the invariant

    def test_generated_bytes_do_not_depend_on_today(self):
        """The whole reason this check may be blocking.

        A digest that rendered lateness would make a clean tree that nobody
        touched start failing the morning a deadline passed.
        """
        with self.repo(today=datetime.date(2026, 7, 23)) as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-dated.md",
                decision("Decide it.", "why", "nothing", answer_by="2026-08-01"),
            )
            before = RECONCILE.generated_open_actions()
            with mock.patch.object(RECONCILE, "TODAY", datetime.date(2027, 1, 1)):
                after = RECONCILE.generated_open_actions()
        self.assertEqual(before, after)
        self.assertIn("answer by 2026-08-01", before)

    def test_regeneration_is_idempotent(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-one.md",
                decision("Decide it.", "why", "nothing"),
            )
            self.assertEqual(self.regenerate(root), self.regenerate(root))

    # ------------------------------------------------------------- the check

    def test_the_check_reports_a_missing_or_stale_digest_and_clears(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-one.md",
                decision("Decide it.", "why", "nothing"),
            )
            missing = list(RECONCILE.check_open_actions())
            self.assertEqual(
                [f.message for f in missing],
                ["the open-action list does not match the queue"],
            )
            self.assertIn("--fix-open-actions", missing[0].fix)

            self.regenerate(root)
            self.assertEqual(list(RECONCILE.check_open_actions()), [])

            self.write(
                root,
                "message-queue/needs-human/decisions/non-blocking-two.md",
                decision("Decide the other one.", "why", "nothing"),
            )
            self.assertEqual(
                [f.message for f in RECONCILE.check_open_actions()],
                ["the open-action list does not match the queue"],
            )

    def test_the_check_is_blocking_rather_than_advisory(self):
        self.assertNotIn("open-actions", RECONCILE.ADVISORY_CHECKS)
        self.assertIs(RECONCILE.CHECKS["open-actions"], RECONCILE.check_open_actions)

    def test_an_adopter_without_a_queue_owes_no_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.multiple(
                RECONCILE,
                REPO=root,
                QUEUE=root / "message-queue",
                TODAY=datetime.date(2026, 7, 23),
                CHANGE_RANGE=None,
            ):
                self.assertEqual(list(RECONCILE.check_open_actions()), [])

    def test_the_digest_is_a_queue_root_document_not_an_item(self):
        """Otherwise every queue check would report it as a malformed item."""
        self.assertTrue(
            RECONCILE.queue_document_path("message-queue/open-actions.md")
        )
        with self.repo() as root:
            self.regenerate(root)
            self.assertEqual(list(RECONCILE.check_queue_location()), [])
            self.assertEqual(list(RECONCILE.check_queue_name()), [])
            self.assertEqual(list(RECONCILE.check_stale_queue()), [])


if __name__ == "__main__":
    unittest.main()
