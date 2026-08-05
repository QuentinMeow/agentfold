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


class ReviewReceiptSourceAllowlistTests(unittest.TestCase):
    def test_identity_and_finding_use_their_documented_plain_source_alphabets(self):
        allowed_identities = (
            "codex planner / sol-high implementer",
            "Reviewer 2 @ safety + core - clear.",
        )
        for value in allowed_identities:
            with self.subTest(identity=value):
                self.assertTrue(
                    SEMANTICS.review_receipt_identity_source_text_allowed(value)
                )
                self.assertTrue(
                    SEMANTICS.review_receipt_finding_source_text_allowed(value)
                )
        allowed_findings = (
            "Clear: yes, tested; why? because! 'single' \"double\" (group).",
        )
        for value in allowed_findings:
            with self.subTest(finding=value):
                self.assertTrue(
                    SEMANTICS.review_receipt_finding_source_text_allowed(value)
                )
                self.assertFalse(
                    SEMANTICS.review_receipt_identity_source_text_allowed(value)
                )

    def test_rejects_every_decorated_or_non_plain_source_shape(self):
        rejected = (
            "[author](profile)", "[author][id]", "[author][]", "[author]",
            "![author](profile)", "![claimant](destination)",
            "a**uth**or", "a_uth_or", "~~author~~", "`author`",
            "<span>author</span>", "auth&#111;r", "cod\\_ex",
            "{author}", "au\u200bthor", "author\tname", "author\u00a0name",
            "author\u2028name", "author\nname", "author\ufeffname",
            "Élodie", "审查者", "аuthor", "authоr", "finding — detail",
        )
        for value in rejected:
            with self.subTest(value=value):
                self.assertFalse(
                    SEMANTICS.review_receipt_identity_source_text_allowed(value)
                )
                self.assertFalse(
                    SEMANTICS.review_receipt_finding_source_text_allowed(value)
                )
                self.assertEqual((), SEMANTICS.identity_key(value))
        self.assertFalse(
            SEMANTICS.review_receipt_identity_source_text_allowed("review:team")
        )
        self.assertTrue(
            SEMANTICS.review_receipt_finding_source_text_allowed("result: clear")
        )

    def test_unicode_folding_is_detection_only_after_ascii_authority_validation(self):
        self.assertEqual(
            SEMANTICS.identity_key("AUTHOR 12"),
            SEMANTICS.identity_key("author 12"),
        )
        self.assertEqual(
            "Elodie",
            SEMANTICS.fold_unicode_marks("Élodie"),
        )
        self.assertEqual(
            SEMANTICS.fold_unicode_marks("Élodie"),
            SEMANTICS.fold_unicode_marks("E\u0301lodie"),
        )
        self.assertEqual((), SEMANTICS.identity_key("Élodie"))
        self.assertEqual((), SEMANTICS.identity_key("E\u0301lodie"))
        self.assertEqual((), SEMANTICS.identity_key("审查者 2"))
        self.assertEqual((), SEMANTICS.identity_key("![ÉLODIE](１２)"))

    def test_identity_key_ignores_ascii_boundaries_and_word_order(self):
        aliases = (
            "O'Neil", "ONeil", "o-neil", "O/Neil", "O Neil", "Neil, O",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual(
                    SEMANTICS.identity_key("ONeil"),
                    SEMANTICS.identity_key(alias),
                )
        self.assertEqual(
            SEMANTICS.identity_key("codex planner"),
            SEMANTICS.identity_key("planner/codex"),
        )

    def test_composite_claimant_keys_include_whole_and_every_component(self):
        claimant = " codex planner / sol-high implementer"
        self.assertEqual(
            (
                SEMANTICS.identity_key(claimant.strip(" ")),
                SEMANTICS.identity_key("codex planner"),
                SEMANTICS.identity_key("sol-high implementer"),
            ),
            SEMANTICS.claimant_identity_keys(claimant),
        )
        expected = SEMANTICS.claimant_identity_keys(
            "first role / second role"
        )
        for separator in ("/", "+", ";", ",", "and", "AND"):
            with self.subTest(separator=separator):
                keys = SEMANTICS.claimant_identity_keys(
                    f"first role {separator} second role"
                )
                self.assertEqual(expected, keys)
                self.assertIn(SEMANTICS.identity_key("first role"), keys)
                self.assertIn(SEMANTICS.identity_key("second role"), keys)

    def test_one_bad_composite_component_invalidates_claimant_authority(self):
        malformed = (
            "codex planner / ",
            "/ codex planner",
            "codex planner // sol-high implementer",
            "codex planner + TBD",
            "codex planner, none",
            "codex planner and ---",
            "codex planner / 审查者",
            "D/B/T",
            "D and B and T",
            "N/A",
            "N and A",
            "first role, and second role",
            "C++",
        )
        for claimant in malformed:
            with self.subTest(claimant=claimant):
                self.assertEqual(
                    (), SEMANTICS.claimant_identity_keys(claimant)
                )
                self.assertFalse(
                    SEMANTICS.independent_reviewer_identity(
                        "correctness reviewer", claimant
                    )
                )

    def test_composite_claimants_reject_component_and_multiset_aliases(self):
        claimant = "codex planner / sol-high implementer"
        self_aliases = (
            "codex",
            "planner",
            "codex planner",
            "planner, codex",
            "codex-planner",
            "codex planner reviewer",
            "sol high implementer",
            "implementer high sol",
            "codex planner sol high implementer",
            "codex plannez",
        )
        for reviewer in self_aliases:
            with self.subTest(reviewer=reviewer):
                self.assertFalse(
                    SEMANTICS.independent_reviewer_identity(reviewer, claimant)
                )
        self.assertTrue(
            SEMANTICS.independent_reviewer_identity(
                "correctness reviewer", claimant
            )
        )
        self.assertFalse(
            SEMANTICS.independent_reviewer_identity("auth0r", "author")
        )

    def test_neutralizer_derives_claimant_keys_once_for_many_verdicts(self):
        verdict_count = 256
        claimant = " / ".join(f"role{index}" for index in range(16))
        claimant_keys = SEMANTICS.claimant_identity_keys(claimant)
        self.assertEqual(17, len(claimant_keys))
        source = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
            + "".join(
                "- core-fit / correctness reviewer: approve — held\n"
                for _ in range(verdict_count)
            )
        )
        with mock.patch.object(
            SEMANTICS,
            "claimant_identity_keys",
            return_value=claimant_keys,
        ) as claimant_spy, mock.patch.object(
            SEMANTICS,
            "identity_key",
            wraps=SEMANTICS.identity_key,
        ) as reviewer_spy, mock.patch.object(
            SEMANTICS,
            "independent_reviewer_key",
            wraps=SEMANTICS.independent_reviewer_key,
        ) as comparison_spy:
            neutralized = SEMANTICS.neutralize_core_fit_review_verdict_tokens(
                source, claimant=claimant
            )
        self.assertEqual(1, claimant_spy.call_count)
        self.assertEqual(1, reviewer_spy.call_count)
        self.assertEqual(1, comparison_spy.call_count)
        self.assertEqual(0, neutralized.count("reviewer: approve"))
        self.assertEqual(verdict_count, neutralized.count(" — held"))

    def test_composite_claimant_component_count_is_bounded(self):
        accepted = " / ".join(f"role{index}" for index in range(16))
        rejected = accepted + " / role16"
        self.assertEqual(17, len(SEMANTICS.claimant_identity_keys(accepted)))
        self.assertEqual((), SEMANTICS.claimant_identity_keys(rejected))

    def test_plain_and_formatted_placeholders_have_no_identity(self):
        placeholders = (
            "unclaimed", "none yet", "TBD", "TODO", "none", "N/A", "NA",
            "unknown", "______", "<reviewer>", "[TBD](profile)",
            "![TBD](profile)", "T**B**D", "`TODO`", "[unknown][id]",
            "_none_", "T\u0301BD", "TB\u0301D", "TBD\u0301", "TBD.",
            "T.B.D.", "t-b-d", "D B T", "unknown.", "none, yet",
            "yet none", "n/a.",
        )
        for placeholder in placeholders:
            with self.subTest(placeholder=placeholder):
                self.assertEqual((), SEMANTICS.identity_key(placeholder))

    def test_combining_marks_cannot_enter_identity_or_split_action_tokens(self):
        for alias in (
            "a\u0301uthor", "au\u0301thor", "aut\u0301hor",
            "autho\u0301r", "author\u0301",
        ):
            with self.subTest(alias=alias):
                self.assertEqual((), SEMANTICS.identity_key(alias))
                self.assertEqual("author", SEMANTICS.fold_unicode_marks(alias))
        self.assertEqual(
            ("aṕprove", "blóck"),
            SEMANTICS.normalized_action_tokens("ap\u0301prove blo\u0301ck"),
        )
        self.assertEqual(
            SEMANTICS.normalized_action_tokens("Ask José to review"),
            SEMANTICS.normalized_action_tokens("Ask Jose\u0301 to review"),
        )
        self.assertNotEqual(
            SEMANTICS.normalized_action_tokens("Ask José to review"),
            SEMANTICS.normalized_action_tokens("Ask Jose to review"),
        )

    def test_claimant_identity_comes_from_one_unchanged_raw_field(self):
        self.assertEqual(
            " author",
            SEMANTICS.claimed_by_identity_source(
                "# Task\n\n**Claimed-by:** author\n"
            ),
        )
        invalid_claimants = (
            "au<!-- hidden -->thor",
            "author<!-- trailing -->",
            "<span>author</span>",
            "auth&#111;r",
            "[author](profile)",
            "![author](profile)",
            "`author`",
            "cod\\_ex",
            "au\u200bthor",
        )
        for claimant in invalid_claimants:
            with self.subTest(claimant=claimant):
                self.assertIsNone(SEMANTICS.claimed_by_identity_source(
                    f"# Task\n\n**Claimed-by:** {claimant}\n"
                ))
        self.assertIsNone(SEMANTICS.claimed_by_identity_source(
            "# Task\n\n**Claimed-by:** author\n**Claimed-by:** second\n"
        ))
        self.assertIsNone(SEMANTICS.claimed_by_identity_source(
            "# Task\n\n<!--\n**Claimed-by:** author\n-->\n"
        ))
        self.assertIsNone(SEMANTICS.claimed_by_identity_source(
            "# Task\n\n```text\n**Claimed-by:** author\n```\n"
        ))
        for lazy_prefix in (
            "ordinary paragraph\n",
            "> block quote paragraph\n",
            "- list paragraph\n",
        ):
            with self.subTest(lazy_prefix=lazy_prefix):
                self.assertIsNone(SEMANTICS.claimed_by_identity_source(
                    lazy_prefix + "**Claimed-by:** author\n"
                ))
        for underline in ("---", "===", "  ---  ", "   ===\t"):
            with self.subTest(underline=underline):
                self.assertIsNone(SEMANTICS.claimed_by_identity_source(
                    f"# Task\n\n**Claimed-by:** author\n{underline}\n"
                ))
        hidden_containers = (
            "<div>\n\n**Claimed-by:** author\n",
            "<div hidden>\n\n**Claimed-by:** author\n",
            "<span hidden>\n\n**Claimed-by:** author\n",
            "<div aria-hidden='true'>\n\n**Claimed-by:** author\n",
            "<div style='display:none'>\n\n**Claimed-by:** author\n",
            "<div style='visibility:hidden'>\n\n**Claimed-by:** author\n",
            "<div style='opacity:0'>\n\n**Claimed-by:** author\n",
            "<div class='hide'>\n\n**Claimed-by:** author\n",
            "<details>\n\n**Claimed-by:** author\n",
            "<dialog>\n\n**Claimed-by:** author\n",
            "<template>\n\n**Claimed-by:** author\n",
            "<agent-box>\n\n**Claimed-by:** author\n",
            "<div><span>\n\n**Claimed-by:** author\n",
            "<DIV\n class='visible'>\n\n**Claimed-by:** author\n",
            "<div hidden>\r\n\r\n**Claimed-by:** author\r\n",
            "<div\n\n**Claimed-by:** author\n",
            "<div\n class='visible'\n\n**Claimed-by:** author\n>\n",
            "<div class='unterminated\n\n**Claimed-by:** author\n'>\n",
            "<agent-box\r\n role='review'\r\n\r\n"
            "**Claimed-by:** author\r\n>\r\n",
            "</div\n\n**Claimed-by:** author\n",
            "<!--\n\n**Claimed-by:** author\n",
            "<?\n\n**Claimed-by:** author\n",
            "<![CDATA[\n\n**Claimed-by:** author\n",
            "<!DOCTYPE\n\n**Claimed-by:** author\n",
            "<x-box/\n\n**Claimed-by:** author\n",
            "<!-\n\n**Claimed-by:** author\n>\n",
            "</\n\n**Claimed-by:** author\n>\n",
            "<!\n\n**Claimed-by:** author\n>\n",
            "<!1\n\n**Claimed-by:** author\n>\n",
            "<!_\n\n**Claimed-by:** author\n>\n",
            "<![\r\n\r\n**Claimed-by:** author\r\n>\r\n",
        )
        for source in hidden_containers:
            with self.subTest(source=source):
                self.assertIsNone(
                    SEMANTICS.claimed_by_identity_source(source)
                )
        for source in (
            "<div hidden>\n\n**Claimed-by:** author\n",
            "<span hidden>\n\n**Claimed-by:** author\n",
            "<div aria-hidden='true'>\n\n**Claimed-by:** author\n",
            "<div style='display:none'>\n\n**Claimed-by:** author\n",
            "<div style='visibility:hidden'>\n\n**Claimed-by:** author\n",
            "<template>\n\n**Claimed-by:** author\n",
        ):
            with self.subTest(rendered_hidden_source=source):
                self.assertNotIn(
                    "**Claimed-by:** author",
                    SEMANTICS.rendered_human_text(source),
                )
        safe_prefixes = (
            "<details>visible</details>\n\n",
            "<div>\nvisible\n</div>\n\n",
            "```html\n<div>\n```\n\n",
            "`<div>`\n\n",
            "<div></div>\n\n", "<!-- closed -->\n\n",
            "<?closed?>\n\n", "<!DOCTYPE html>\n\n",
        )
        for prefix in safe_prefixes:
            source = prefix + "**Claimed-by:** author\n"
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    " author", SEMANTICS.claimed_by_identity_source(source)
                )
        for line_ending in ("\n", "\r\n"):
            with self.subTest(line_ending=line_ending):
                self.assertEqual(
                    " author",
                    SEMANTICS.claimed_by_identity_source(
                        f"**Claimed-by:** author{line_ending}"
                        f"**Filed:** 2026-08-04{line_ending}"
                    ),
                )

    def test_raw_html_container_state_ignores_code_and_closed_containers(self):
        for source in (
            "<div>", "<details>\n", "<dialog>\r\n", "<agent-box>\n",
            "<div><span>\n", "<DIV\n class='visible'>\n",
            "<div", "<div\n class='visible'", "<div class='unterminated",
            "<agent-box\r\n role='review'",
            "</div", "<!--", "<?", "<![CDATA[", "<!DOCTYPE", "<x-box/",
            "<!-\n\n", "</\n\n", "<!\n\n", "<!1\n\n",
            "<!_\n\n", "<![\n\n", "<![\r\n\r\n",
        ):
            with self.subTest(open_source=source):
                self.assertTrue(
                    SEMANTICS.raw_html_container_open_at_end(source)
                )
        for source in (
            "<details>visible</details>\n",
            "<div></div>\n", "<!-- closed -->\n", "<?closed?>\n",
            "<!DOCTYPE html>\n",
            "<div><span>visible</span></div>\n",
            "```html\n<div>\n```\n",
            "    <div>\n",
            "`<div>`\n",
            "<br><hr><img src='x'><input>\n",
            "ordinary source\n", "a < b\n", "x < y\n", "AT&T\n",
            "&amp\n", "<\n",
        ):
            with self.subTest(closed_or_code_source=source):
                self.assertFalse(
                    SEMANTICS.raw_html_container_open_at_end(source)
                )

    def test_receipt_lines_must_match_structural_and_rendered_views(self):
        revision = f"**Reviewed revision:** {'a' * 40}"
        verdict = "- core-fit / reviewer: approve — visible receipt"
        source = (
            "## Review verdicts\n\n"
            + revision
            + "\n\n"
            + verdict
            + "\n"
        )
        cases = (
            ("## Review verdicts", "section_count", 0),
            (revision, "revision_count", 0),
            (verdict, "verdicts", ()),
        )
        for line, field, expected in cases:
            rendered = source.replace(line, " " * len(line), 1)
            with self.subTest(line=line), mock.patch.object(
                SEMANTICS, "rendered_human_text", return_value=rendered
            ):
                evidence = SEMANTICS.core_fit_review_evidence(source)
                self.assertEqual(expected, evidence[field], evidence)

    def test_duplicate_heading_scan_never_reparses_prefixes(self):
        duplicates = "\n\n".join("## Review verdicts" for _ in range(1000))
        with mock.patch.object(
            SEMANTICS,
            "raw_html_container_open_at_end",
            wraps=SEMANTICS.raw_html_container_open_at_end,
        ) as open_state:
            evidence = SEMANTICS.core_fit_review_evidence(duplicates)
        self.assertEqual(1000, evidence["section_count"], evidence)
        self.assertEqual(0, open_state.call_count)

        valid = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
            "- core-fit / reviewer: approve — visible receipt\n"
        )
        with mock.patch.object(
            SEMANTICS,
            "raw_html_container_open_at_end",
            wraps=SEMANTICS.raw_html_container_open_at_end,
        ) as open_state:
            evidence = SEMANTICS.core_fit_review_evidence(valid)
        self.assertEqual(1, evidence["section_count"], evidence)
        self.assertEqual(1, open_state.call_count)

    def test_multiple_visible_heading_candidates_skip_prefix_parsing(self):
        visible_nested = (
            "<div>\n\n"
            "## Review verdicts\n\n"
            "</div>\n\n"
            "## Review verdicts\n"
        )
        with mock.patch.object(
            SEMANTICS,
            "raw_html_container_open_at_end",
            wraps=SEMANTICS.raw_html_container_open_at_end,
        ) as open_state:
            evidence = SEMANTICS.core_fit_review_evidence(visible_nested)
        self.assertEqual(2, evidence["section_count"], evidence)
        self.assertEqual(0, open_state.call_count)

    def test_revision_duplicate_only_invalidates_the_preverdict_prologue(self):
        first = f"**Reviewed revision:** {'a' * 40}\n"
        second = f"**Reviewed revision:** {'b' * 40}\n"
        verdict = "- core-fit / reviewer: approve — accepted verdict\n"
        later = "- core-fit / later reviewer: block — later action\n"

        invalid = SEMANTICS.core_fit_review_evidence(
            "## Review verdicts\n\n" + first + "\n" + second + "\n" + verdict
        )
        self.assertEqual(2, invalid["revision_count"], invalid)
        self.assertIsNone(invalid["reviewed_revision"], invalid)
        self.assertEqual((), invalid["verdicts"], invalid)

        terminated_source = (
            "## Review verdicts\n\n" + first + "\n" + verdict + "\n"
            + second + "\n" + later
        )
        accepted = SEMANTICS.core_fit_review_evidence(terminated_source)
        self.assertEqual(1, accepted["revision_count"], accepted)
        self.assertEqual("a" * 40, accepted["reviewed_revision"], accepted)
        self.assertEqual(1, len(accepted["verdicts"]), accepted)

        neutralized = SEMANTICS.neutralize_core_fit_review_verdict_tokens(
            terminated_source, claimant="author"
        )
        before_history, after_history = neutralized.split(second)
        self.assertNotIn("reviewer: approve", before_history)
        self.assertIn("later reviewer: block", after_history)

    def test_verdict_mapping_never_scans_the_semantic_prefix_per_match(self):
        verdict_count = 16000
        source = (
            "historical context\r\n\r\n"
            "## Review verdicts\r\n\r\n"
            f"**Reviewed revision:** {'a' * 40}\r\n\r\n"
            + "".join(
                "- core-fit / reviewer: approve — accepted verdict\r\n"
                for _ in range(verdict_count)
            )
        )
        evidence = SEMANTICS.core_fit_review_evidence(source)
        self.assertEqual(verdict_count, len(evidence["verdicts"]), evidence)
        semantic = evidence["semantic_text"]
        guarded_semantic = mock.MagicMock()
        guarded_semantic.__bool__.return_value = True
        guarded_semantic.replace.return_value = semantic
        guarded_semantic.count.side_effect = AssertionError(
            "per-verdict count scan"
        )
        guarded_semantic.rfind.side_effect = AssertionError(
            "per-verdict rfind scan"
        )
        evidence["semantic_text"] = guarded_semantic
        with mock.patch.object(
            SEMANTICS, "core_fit_review_evidence", return_value=evidence
        ):
            neutralized = SEMANTICS.neutralize_core_fit_review_verdict_tokens(
                source, claimant="author"
            )
        self.assertEqual(0, neutralized.count("reviewer: approve"))
        self.assertEqual(verdict_count, neutralized.count("accepted verdict"))
        self.assertEqual(source.count("\n"), neutralized.count("\n"))


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

    def test_a_setext_underline_closes_the_paragraph_above_it(self):
        self.assert_blanked("Prose line.\n---\n\n    code line\n", "code line")

    def test_a_thematic_break_closes_the_paragraph_above_it(self):
        self.assert_blanked("***\n\n    code line\n", "code line")

    def test_a_table_row_is_paragraph_text(self):
        self.assert_kept("| a | b |\n|---|---|\n    still prose\n", "still prose")

    def test_a_second_chunk_of_one_code_block_is_still_blanked(self):
        self.assert_blanked(
            "Prose line.\n\n    first chunk\n\n    second chunk\n", "second chunk"
        )

    def test_a_new_sibling_item_reopens_the_same_threshold(self):
        self.assert_kept("- a\n\n- b\n\n    four spaces\n", "four spaces")

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
