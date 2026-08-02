"""What `strip_indented_code` may blank, and what every gate must still see.

Blanking a line is how this repository stops an example path or field from satisfying
a structural check. Blanking one line too many is how a real ask, a real link, and a
real rewrite of a live queue item become invisible to every gate at once, which is the
bypass these tests pin shut. Each reproduction below is written twice — the same bytes
at top level and one level inside a list — because the top-level half is what already
worked, and the pair is what proves the rule no longer depends on indentation.
"""
import contextlib
import datetime
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AUTOMATION = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEMANTICS = load(
    "markdown_semantics_under_test", AUTOMATION / "markdown_semantics.py"
)
RECONCILE = load(
    "reconcile_under_test", AUTOMATION / "reconcile" / "reconcile.py"
)
PROJECTION = load(
    "check_action_projection_under_test",
    AUTOMATION / "check_action_projection.py",
)

QUEUE_ITEM_PATH = (
    "message-queue/needs-agent/requests/non-blocking-do-the-thing.md"
)
TASK_RECORD_PATH = "tasks/1_in-progress/2026-08-02-example/task.md"
HUMAN_ASK = "Please confirm the retention window before this lands."
MISSING_TARGET = "automation/does-not-exist.py"


class IndentedCodeViewTests(unittest.TestCase):
    """CommonMark's rule for an indented code block, case by case."""

    def assert_kept(self, source, token):
        blanked = SEMANTICS.semantic_text(source)
        self.assertIn(token, blanked, blanked)
        self.assertEqual(source.count("\n"), blanked.count("\n"))

    def assert_blanked(self, source, token):
        blanked = SEMANTICS.semantic_text(source)
        self.assertNotIn(token, blanked, blanked)
        self.assertEqual(source.count("\n"), blanked.count("\n"))

    def test_a_four_space_line_under_a_list_item_is_prose(self):
        """The reported bypass, at its smallest: `- a` then four spaces."""
        self.assert_kept("- a\n    b\n", "b")

    def test_a_four_space_line_under_a_list_item_is_prose_after_a_blank_line(self):
        self.assert_kept("- a\n\n    b\n", "b")

    def test_a_four_space_line_cannot_interrupt_a_paragraph(self):
        self.assert_kept("Prose line.\n    still prose\n", "still prose")

    def test_a_top_level_indented_code_block_is_still_blanked(self):
        self.assert_blanked("Prose line.\n\n    code line\n", "code line")

    def test_a_tab_indented_code_block_is_still_blanked(self):
        self.assert_blanked("Prose line.\n\n\tcode line\n", "code line")

    def test_an_indented_code_block_after_a_heading_is_still_blanked(self):
        self.assert_blanked("# Heading\n\n    code line\n", "code line")

    def test_a_list_item_moves_the_threshold_to_its_content_column(self):
        self.assert_blanked("- a\n\n      code line\n", "code line")
        self.assert_kept("- a\n\n     five spaces\n", "five spaces")

    def test_an_ordered_item_moves_the_threshold_to_its_own_content_column(self):
        """`1. ` is three columns wide, so code starts at seven, not six."""
        self.assert_blanked("1. a\n\n       code line\n", "code line")
        self.assert_kept("1. a\n\n      six spaces\n", "six spaces")

    def test_a_nested_list_item_moves_the_threshold_again(self):
        self.assert_blanked("- a\n  - b\n\n        code line\n", "code line")
        self.assert_kept("- a\n  - b\n\n      six spaces\n", "six spaces")

    def test_an_empty_list_item_still_opens_a_content_column(self):
        self.assert_kept("-\n\n    four spaces\n", "four spaces")
        self.assert_blanked("-\n\n      code line\n", "code line")

    def test_a_thematic_break_closes_the_list_it_follows(self):
        """`- - -` is a thematic break, so the item above it is no longer open."""
        self.assert_blanked("- a\n- - -\n\n    code line\n", "code line")

    def test_a_less_indented_paragraph_closes_the_list_it_follows(self):
        self.assert_blanked("- a\n\nback at the margin\n\n    code line\n",
                            "code line")

    def test_a_lazy_continuation_keeps_its_list_item_open(self):
        self.assert_kept("- a\nlazy continuation\n\n    four spaces\n",
                         "four spaces")

    def test_a_fence_nested_in_a_list_item_is_still_blanked(self):
        self.assert_blanked(
            "- Item\n\n  ```python\n  code here\n  ```\n\n- Next\n", "code here"
        )

    def test_a_block_quoted_indented_line_keeps_its_historical_answer(self):
        """Quoted source is out of scope: it was never blanked and still is not."""
        self.assert_kept(">     quoted text\n", "quoted text")

    def test_a_quoted_paragraph_lazily_continues_into_the_next_line(self):
        self.assert_kept("> quoted\n    lazy tail\n", "lazy tail")

    def test_an_indented_block_after_a_closed_quote_is_still_blanked(self):
        self.assert_blanked("> quoted\n>\n\n    code line\n", "code line")

    def test_indentation_width_is_shared_with_the_projection_gate(self):
        """One implementation of CommonMark column arithmetic, not two."""
        self.assertEqual(
            "markdown_semantics", PROJECTION.indentation_width.__module__
        )
        self.assertEqual(4, SEMANTICS.indentation_width("\t"))
        self.assertEqual(4, SEMANTICS.indentation_width("  \t"))
        self.assertEqual(8, SEMANTICS.indentation_width("\t\tx"))


def queue_item(ask):
    """Return one live agent request whose ask sits inside a list continuation."""
    return (
        "# Do the thing\n"
        "\n"
        "**Status:** open\n"
        "**Filed:** 2026-08-02, by claude, from a task\n"
        "**Action:** Carry out the ask recorded below.\n"
        f"**Full context:** `{TASK_RECORD_PATH}`\n"
        "**Resolution evidence:** `docs/disposition.md`\n"
        "**If unanswered:** Nothing stops.\n"
        "\n"
        "## What you need to know\n"
        "\n"
        "- The request has one step:\n"
        f"    {ask}\n"
        "\n"
        "## Done when\n"
        "\n"
        "The step above has been carried out.\n"
    )


def queue_item_at_top_level(ask):
    return queue_item("").replace(
        "- The request has one step:\n    \n", f"{ask}\n"
    )


class QueueMutationTests(unittest.TestCase):
    """A live queue item's ask may not be replaced, wherever it is written."""

    def assert_rewrite_is_refused(self, before, after):
        self.assertNotEqual(
            RECONCILE.queue_action_identity(QUEUE_ITEM_PATH, before),
            RECONCILE.queue_action_identity(QUEUE_ITEM_PATH, after),
        )
        self.assertEqual(
            "action identity changed while the queue item remained live",
            RECONCILE.queue_mutation_problem(
                QUEUE_ITEM_PATH, QUEUE_ITEM_PATH, before, after
            ),
        )

    def test_replacing_an_ask_inside_a_list_continuation_is_refused(self):
        self.assert_rewrite_is_refused(
            queue_item("Delete the stale cache file."),
            queue_item("Delete every audit record in the repository."),
        )

    def test_replacing_an_ask_at_top_level_is_refused(self):
        self.assert_rewrite_is_refused(
            queue_item_at_top_level("Delete the stale cache file."),
            queue_item_at_top_level(
                "Delete every audit record in the repository."
            ),
        )

    def test_a_lifecycle_only_update_is_still_permitted(self):
        before = queue_item("Delete the stale cache file.")
        after = before.replace("**Status:** open", "**Status:** in-repair")
        self.assertEqual(
            RECONCILE.queue_action_identity(QUEUE_ITEM_PATH, before),
            RECONCILE.queue_action_identity(QUEUE_ITEM_PATH, after),
        )


class TaskActionOriginTests(unittest.TestCase):
    """An unqueued human ask in a task record counts wherever it is written."""

    @staticmethod
    def units(body):
        return PROJECTION.task_action_unit_counts(
            f"# Example task\n\n## Goal\n\n{body}", TASK_RECORD_PATH
        )

    def test_an_ask_inside_a_list_continuation_is_counted(self):
        units = self.units(f"- The window matters:\n    {HUMAN_ASK}\n")
        self.assertEqual(1, sum(units.values()), units)
        self.assertIn(HUMAN_ASK, "".join(units))

    def test_an_ask_at_top_level_is_counted(self):
        units = self.units(f"{HUMAN_ASK}\n")
        self.assertEqual(1, sum(units.values()), units)
        self.assertIn(HUMAN_ASK, "".join(units))

    def test_a_fenced_example_ask_is_still_not_counted(self):
        """The narrower indented-code rule leaves fenced examples exactly as they
        were: this gate reads a rendered-human view, and a fence is what reliably
        keeps an illustrative sentence out of it."""
        units = self.units(
            f"An example of what not to write:\n\n```\n{HUMAN_ASK}\n```\n"
        )
        self.assertEqual({}, dict(units))


class LinkCheckTests(unittest.TestCase):
    """A broken repository link counts wherever it is written."""

    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.multiple(
                RECONCILE,
                REPO=root,
                QUEUE=root / "message-queue",
                RETRIES=root / "message-queue" / "needs-agent" / "retries",
                TASKS=root / "tasks",
                CONVERSATIONS=root / "history" / "conversations",
                MEMORY=root / "memory",
                TODAY=datetime.date(2026, 8, 2),
                ACTIVE_TASK_ID=None,
                ACTIVE_TRANSITIONS=set(),
                CHANGE_RANGE=None,
                DISPLACED_TIP=None,
            ):
                yield root

    @staticmethod
    def write(root, relative, text):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def findings_for(self, body):
        with self.repo() as root:
            self.write(root, "handbook/prose.md", body)
            return [
                finding.message for finding in RECONCILE.check_links()
            ]

    def test_a_broken_link_inside_a_list_continuation_is_reported(self):
        messages = self.findings_for(
            f"- The gate lives here:\n    `{MISSING_TARGET}` runs on every commit.\n"
        )
        self.assertEqual(1, len(messages), messages)
        self.assertIn(MISSING_TARGET, messages[0])

    def test_a_broken_link_at_top_level_is_reported(self):
        messages = self.findings_for(f"`{MISSING_TARGET}` runs on every commit.\n")
        self.assertEqual(1, len(messages), messages)
        self.assertIn(MISSING_TARGET, messages[0])

    def test_a_path_inside_a_real_indented_code_block_is_still_ignored(self):
        self.assertEqual(
            [],
            self.findings_for(
                f"Indented code block, not a live link:\n\n    `{MISSING_TARGET}`\n"
            ),
        )

    def test_a_path_inside_a_list_item_code_block_is_still_ignored(self):
        self.assertEqual(
            [],
            self.findings_for(
                f"- The example is:\n\n      `{MISSING_TARGET}`\n"
            ),
        )


HUMAN_ITEM = (
    "# Choose the retention window\n"
    "\n"
    "**Status:** waiting\n"
    "\n"
    "- The blocked work is:\n"
    "    task:2026-08-02-example, recorded in\n"
    f"    {TASK_RECORD_PATH}\n"
    "\n"
    "## What you need to know\n"
    "\n"
    "- The window matters because:\n"
    "    Nothing purges the audit log today.\n"
    "\n"
    "**Your answer:** ______\n"
)


class SemanticConsumerTests(unittest.TestCase):
    """Every named reader of the semantic view sees list-continuation prose."""

    def test_task_tokens_reads_a_list_continuation(self):
        self.assertEqual({"2026-08-02-example"}, RECONCILE.task_tokens(HUMAN_ITEM))

    def test_task_status_references_reads_a_list_continuation(self):
        self.assertEqual(
            [TASK_RECORD_PATH], RECONCILE.task_status_references(HUMAN_ITEM)
        )

    def test_human_header_block_reads_a_list_continuation(self):
        block = RECONCILE.human_header_block(HUMAN_ITEM)
        self.assertIn("task:2026-08-02-example", block)
        self.assertIn(TASK_RECORD_PATH, block)

    def test_human_attention_above_fold_reads_a_list_continuation(self):
        above = RECONCILE.human_attention_above_fold(HUMAN_ITEM)
        self.assertIn("Nothing purges the audit log today.", above)
        self.assertNotIn("**Your answer:**", above)

    def test_section_body_reads_a_list_continuation(self):
        self.assertIn(
            "Nothing purges the audit log today.",
            RECONCILE.section_body(HUMAN_ITEM, "## What you need to know"),
        )

    def test_level_two_section_body_reads_a_list_continuation(self):
        self.assertIn(
            "Nothing purges the audit log today.",
            RECONCILE.level_two_section_body(
                HUMAN_ITEM, "## What you need to know"
            ),
        )

    def test_field_counts_never_depended_on_this_view(self):
        """The one named consumer this bug could not reach, pinned as such.

        `FIELD_RE` is anchored at column zero, so a field written on an indented
        line was never a field before the fix either. Nothing here changed, and
        this test says so rather than leaving a reader to assume otherwise.
        """
        self.assertEqual({"Status": 1}, RECONCILE.field_counts(
            "**Status:** open\n\n- item\n    **Status:** closed\n"
        ))
        self.assertEqual({"Status": 2}, RECONCILE.field_counts(
            "**Status:** open\n\n**Status:** closed\n"
        ))


if __name__ == "__main__":
    unittest.main()
