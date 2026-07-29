import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from automation.tests.test_gate_generations import (
    DEADLINE_RECORDS,
    PARSER_COMPAT_RECORDS,
    REVIEW_REPAIR_RECORDS,
    gate_generation_records,
)

REPO = Path(__file__).resolve().parents[2]
AUTOMATION = REPO / "automation"
sys.path.insert(0, str(AUTOMATION))
CONFIG_SPEC = importlib.util.spec_from_file_location(
    "test_gate_config_isolated", AUTOMATION / "test_gate_config.py"
)
CONFIG = importlib.util.module_from_spec(CONFIG_SPEC)
sys.modules[CONFIG_SPEC.name] = CONFIG
CONFIG_SPEC.loader.exec_module(CONFIG)
from _vendor import tomli


CURRENT_GATE_RECORDS = gate_generation_records()
if CURRENT_GATE_RECORDS == DEADLINE_RECORDS:
    POLICY_ENDPOINT = "deadline-before-parser-compat"
elif CURRENT_GATE_RECORDS == PARSER_COMPAT_RECORDS:
    POLICY_ENDPOINT = "parser-compat"
elif CURRENT_GATE_RECORDS == REVIEW_REPAIR_RECORDS:
    POLICY_ENDPOINT = "review-repair"
else:
    raise AssertionError(
        "config tests require one exact admitted policy endpoint: {!r}".format(
            CURRENT_GATE_RECORDS
        )
    )
HAS_SERVICE_DEPENDENCIES = POLICY_ENDPOINT != "deadline-before-parser-compat"
HAS_HARDENED_RISK_PATHS = POLICY_ENDPOINT != "deadline-before-parser-compat"
IS_REVIEW_REPAIR = POLICY_ENDPOINT == "review-repair"


VALID_TEXT = (REPO / "agentfold.toml").read_text(encoding="utf-8")
def replaced(old, new, text=VALID_TEXT):
    if old not in text:
        raise AssertionError("fixture fragment was not found: {!r}".format(old))
    return text.replace(old, new, 1)


DEPENDENCY_PREFIX = "service_dependencies = "
dependency_lines = tuple(
    line for line in VALID_TEXT.splitlines(keepends=True)
    if line.startswith(DEPENDENCY_PREFIX)
)
expected_dependency_lines = 1 if IS_REVIEW_REPAIR else 0
if len(dependency_lines) != expected_dependency_lines:
    raise AssertionError(
        "{} endpoint has an unexpected starter dependency shape".format(
            POLICY_ENDPOINT
        )
    )
NO_DEPENDENCIES_TEXT = "".join(
    line for line in VALID_TEXT.splitlines(keepends=True)
    if not line.startswith(DEPENDENCY_PREFIX)
)


def with_dependencies(value, text=NO_DEPENDENCIES_TEXT):
    return replaced(
        "target_seconds = 60\nmaximum_seconds = 60",
        "target_seconds = 60\nmaximum_seconds = 60\n"
        "service_dependencies = {}".format(value),
        text,
    )


EMPTY_DEPENDENCIES_TEXT = with_dependencies("{}")
DEPENDENCY_TEXT = with_dependencies('{ quote-api = ["quote-cli"] }')
PRE_SERVICE_DEPENDENCY_POLICY_DIGEST = (
    "fc882fa0e93966ca969ee94a2f4567320188d658b4c5739952f5c3e803889fe1"
)
PRE_HARDENING_POLICY_DIGEST = (
    "41b2ee7b778f6fe2821179760291fffd8ff9ed85b85d52ebbab5a09f4bc1236e"
)


def final_config(mode, text=VALID_TEXT):
    """Return an explicit final-mode fixture independent of the starter mode."""
    start = text.index("[testing.final]")
    end = text.index("\n[testing.performance]", start)
    trigger = 'trigger = "pull-request"\n' if mode == "hard" else ""
    block = (
        "[testing.final]\n"
        'mode = "{}"\n'.format(mode)
        + trigger
        + "target_seconds = 300\n"
        + "maximum_seconds = 900\n"
    )
    return text[:start] + block + text[end:]


HARD_CONFIG = final_config("hard")
MANUAL_CONFIG = final_config("manual")


class StarterPolicyTests(unittest.TestCase):
    def test_starter_policy_has_reviewed_gate_contract(self):
        policy = CONFIG.load_policy(REPO / "agentfold.toml")

        self.assertEqual(1, policy.schema_version)
        self.assertEqual((60.0, 60.0), (policy.routine.target_seconds, policy.routine.maximum_seconds))
        if IS_REVIEW_REPAIR:
            self.assertEqual(
                (("quote-api", ("quote-cli",)),),
                policy.service_dependencies,
            )
        elif HAS_SERVICE_DEPENDENCIES:
            self.assertEqual((), policy.service_dependencies)
        else:
            self.assertFalse(hasattr(policy, "service_dependencies"))
        self.assertEqual("manual", policy.final.mode)
        self.assertIsNone(policy.final.trigger)
        self.assertEqual((300.0, 900.0), (policy.final.target_seconds, policy.final.maximum_seconds))
        self.assertEqual("file-task", policy.on_budget_exceeded)
        self.assertTrue(policy.unmatched_is_critical)
        self.assertEqual(
            CONFIG.MANDATORY_CRITICAL_CATEGORIES,
            frozenset(binding.category for binding in policy.critical_bindings),
        )
        self.assertEqual(
            {"ordinary-repository-work"},
            {binding.id for binding in policy.reversible_bindings},
        )
        for binding in policy.critical_bindings:
            self.assertTrue(binding.path_globs)
            self.assertTrue(binding.required_check_ids)
            self.assertLessEqual(set(binding.required_check_ids), CONFIG.KNOWN_CHECK_IDS)

    def test_vendored_parser_is_pinned(self):
        self.assertEqual("2.0.1", tomli.__version__)

    def test_load_policy_reports_missing_file(self):
        with self.assertRaisesRegex(CONFIG.ConfigError, "could not read"):
            CONFIG.load_policy(REPO / "does-not-exist.toml")

    def test_parse_policy_accepts_bytes_and_rejects_non_utf8(self):
        self.assertEqual(1, CONFIG.parse_policy(VALID_TEXT.encode("utf-8")).schema_version)
        with self.assertRaisesRegex(CONFIG.ConfigError, "not valid UTF-8"):
            CONFIG.parse_policy(b"\xff")

    def test_canonical_digest_ignores_comments_order_and_number_spelling(self):
        reordered = VALID_TEXT.replace(
            'target_seconds = 60\nmaximum_seconds = 60',
            'maximum_seconds = 60.0\ntarget_seconds = 60.0',
            1,
        ).replace(
            'required_check_ids = ["core-scope", "reconcile", "repository-tests/full"]',
            'required_check_ids = ["repository-tests/full", "reconcile", "core-scope"]',
            1,
        )
        reordered = "# unrelated formatting\n" + reordered

        first = CONFIG.parse_policy(VALID_TEXT)
        second = CONFIG.parse_policy(reordered)

        self.assertEqual(CONFIG.canonical_policy_json(first), CONFIG.canonical_policy_json(second))
        self.assertEqual(first.digest, second.digest)
        self.assertRegex(first.digest, r"^[0-9a-f]{64}$")

    def test_semantic_change_changes_digest(self):
        changed = CONFIG.parse_policy(replaced("target_seconds = 300", "target_seconds = 301"))
        original = CONFIG.parse_policy(VALID_TEXT)
        self.assertNotEqual(original.digest, changed.digest)

    def test_empty_dependency_compatibility_preserves_old_policy_identity(self):
        absent = CONFIG.parse_policy(NO_DEPENDENCIES_TEXT)
        if not HAS_SERVICE_DEPENDENCIES:
            with self.assertRaisesRegex(CONFIG.ConfigError, "unknown key"):
                CONFIG.parse_policy(EMPTY_DEPENDENCIES_TEXT)
            self.assertEqual(PRE_HARDENING_POLICY_DIGEST, absent.digest)
            self.assertFalse(hasattr(absent, "service_dependencies"))
            return
        explicit_empty = CONFIG.parse_policy(EMPTY_DEPENDENCIES_TEXT)

        self.assertEqual((), absent.service_dependencies)
        self.assertEqual((), explicit_empty.service_dependencies)
        self.assertEqual(
            CONFIG.canonical_policy_json(absent),
            CONFIG.canonical_policy_json(explicit_empty),
        )
        self.assertEqual(absent.digest, explicit_empty.digest)
        self.assertEqual(PRE_SERVICE_DEPENDENCY_POLICY_DIGEST, absent.digest)
        self.assertEqual(
            CONFIG.canonical_policy_json(
                CONFIG.union_policies(absent, explicit_empty)
            ),
            CONFIG.canonical_policy_json(CONFIG.union_policies(absent, absent)),
        )
        self.assertNotIn(
            b'"service_dependencies"',
            CONFIG.canonical_policy_json(absent),
        )

    def test_nonempty_dependencies_are_digest_bound(self):
        absent = CONFIG.parse_policy(NO_DEPENDENCIES_TEXT)
        if not HAS_SERVICE_DEPENDENCIES:
            with self.assertRaisesRegex(CONFIG.ConfigError, "unknown key"):
                CONFIG.parse_policy(DEPENDENCY_TEXT)
            self.assertFalse(hasattr(absent, "service_dependencies"))
            return
        configured = CONFIG.parse_policy(DEPENDENCY_TEXT)

        self.assertEqual(
            (("quote-api", ("quote-cli",)),),
            configured.service_dependencies,
        )
        self.assertIn(
            b'"service_dependencies":{"quote-api":["quote-cli"]}',
            CONFIG.canonical_policy_json(configured),
        )
        self.assertNotEqual(absent.digest, configured.digest)

    def test_existing_positional_construction_defaults_to_no_dependencies(self):
        policy = CONFIG.parse_policy(NO_DEPENDENCIES_TEXT)
        reconstructed = CONFIG.TestGatePolicy(
            policy.schema_version,
            policy.routine,
            policy.final,
            policy.on_budget_exceeded,
            policy.critical_bindings,
            policy.reversible_bindings,
            policy.unmatched_is_critical,
        )

        if HAS_SERVICE_DEPENDENCIES:
            self.assertEqual((), reconstructed.service_dependencies)
        else:
            self.assertFalse(hasattr(reconstructed, "service_dependencies"))
        self.assertEqual(policy.digest, reconstructed.digest)
        if HAS_SERVICE_DEPENDENCIES:
            configured = CONFIG.parse_policy(DEPENDENCY_TEXT)
            configured_reconstructed = CONFIG.TestGatePolicy(
                configured.schema_version,
                configured.routine,
                configured.final,
                configured.on_budget_exceeded,
                configured.critical_bindings,
                configured.reversible_bindings,
                configured.unmatched_is_critical,
                configured.service_dependencies,
            )
            self.assertEqual(
                (("quote-api", ("quote-cli",)),),
                configured_reconstructed.service_dependencies,
            )
            self.assertEqual(configured.digest, configured_reconstructed.digest)


class ClosedSchemaTests(unittest.TestCase):
    def assert_config_error(self, text, pattern):
        with self.assertRaisesRegex(CONFIG.ConfigError, pattern):
            CONFIG.parse_policy(text)

    def test_unknown_root_testing_gate_risk_and_binding_keys_fail(self):
        cases = (
            (replaced("schema_version = 1", "schema_version = 1\nunknown = 1"), r"root has unknown key"),
            (replaced("[testing.routine]", "[testing]\ntesting_typo = 1\n\n[testing.routine]"), r"testing has unknown key"),
            (replaced("target_seconds = 60", "target_seconds = 60\ntyop = 1"), r"testing\.routine has unknown key"),
            (replaced("unmatched = \"critical\"", "unmatched = \"critical\"\ntyop = 1"), r"testing\.risk has unknown key"),
            (replaced('category = "credentials-and-secrets"', 'category = "credentials-and-secrets"\ntyop = 1'), r"testing\.risk\.critical\[0\] has unknown key"),
            (replaced('id = "ordinary-repository-work"', 'id = "ordinary-repository-work"\ntyop = 1'), r"testing\.risk\.reversible\[0\] has unknown key"),
        )
        for text, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_schema_version_must_be_integer_one(self):
        for value in ("2", "true", '"1"'):
            with self.subTest(value=value):
                self.assert_config_error(
                    replaced("schema_version = 1", "schema_version = " + value),
                    "schema_version must be the integer 1",
                )

    def test_manual_omits_trigger_and_hard_requires_supported_trigger(self):
        self.assertEqual("manual", CONFIG.parse_policy(MANUAL_CONFIG).final.mode)
        self.assertEqual("hard", CONFIG.parse_policy(HARD_CONFIG).final.mode)
        self.assertEqual(frozenset(("pull-request",)), CONFIG.FINAL_TRIGGERS)

        invalid = (
            (
                replaced(
                    'mode = "manual"',
                    'mode = "manual"\ntrigger = "merge"',
                    MANUAL_CONFIG,
                ),
                "trigger must be omitted",
            ),
            (replaced('trigger = "pull-request"\n', "", HARD_CONFIG), "trigger is required"),
            (replaced('trigger = "pull-request"', 'trigger = "pre-commit"', HARD_CONFIG), "trigger must be one of"),
            (replaced('trigger = "pull-request"', 'trigger = "task-review"', HARD_CONFIG), "trigger must be one of"),
            (replaced('trigger = "pull-request"', 'trigger = "merge"', HARD_CONFIG), "trigger must be one of"),
            (replaced('mode = "hard"', 'mode = "soft"', HARD_CONFIG), "mode must be one of"),
            (replaced('mode = "hard"', 'mode = "off"', HARD_CONFIG), "mode must be one of"),
        )
        for text, pattern in invalid:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_budget_action_is_closed(self):
        self.assert_config_error(
            replaced('on_budget_exceeded = "file-task"', 'on_budget_exceeded = "warn"'),
            "on_budget_exceeded must be one of",
        )

    def test_service_dependencies_are_closed_and_lowercase_kebab_case(self):
        if not HAS_SERVICE_DEPENDENCIES:
            for text in (
                EMPTY_DEPENDENCIES_TEXT,
                DEPENDENCY_TEXT,
            ):
                with self.subTest(endpoint=POLICY_ENDPOINT, text=text):
                    self.assert_config_error(text, "unknown key")
            return
        cases = (
            (
                replaced(
                    'service_dependencies = { quote-api = ["quote-cli"] }',
                    'service_dependencies = { "Quote API" = ["quote-cli"] }',
                    DEPENDENCY_TEXT,
                ),
                "lowercase kebab-case",
            ),
            (
                replaced(
                    'service_dependencies = { quote-api = ["quote-cli"] }',
                    'service_dependencies = { quote-api = ["Quote CLI"] }',
                    DEPENDENCY_TEXT,
                ),
                "lowercase kebab-case",
            ),
            (
                replaced(
                    'service_dependencies = { quote-api = ["quote-cli"] }',
                    'service_dependencies = { quote-api = ["quote-api"] }',
                    DEPENDENCY_TEXT,
                ),
                "must not depend on itself",
            ),
            (
                replaced(
                    'service_dependencies = { quote-api = ["quote-cli"] }',
                    'service_dependencies = { quote-api = ["quote-cli", "quote-cli"] }',
                    DEPENDENCY_TEXT,
                ),
                "duplicate values",
            ),
        )
        for text, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_budget_numbers_reject_boolean_nonfinite_nonpositive_and_target_over_maximum(self):
        cases = (
            (replaced("target_seconds = 60", "target_seconds = true"), "not a boolean"),
            (replaced("target_seconds = 60", "target_seconds = inf"), "must be finite"),
            (replaced("target_seconds = 60", "target_seconds = nan"), "must be finite"),
            (replaced("target_seconds = 60", "target_seconds = 0"), "greater than zero"),
            (replaced("target_seconds = 60", "target_seconds = -1"), "greater than zero"),
            (replaced("target_seconds = 60", "target_seconds = 61"), "must not exceed maximum_seconds"),
            (replaced("maximum_seconds = 900", "maximum_seconds = 299"), "must not exceed maximum_seconds"),
        )
        for text, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_all_six_critical_categories_are_mandatory_and_unique(self):
        start = VALID_TEXT.index("[[testing.risk.critical]]")
        end = VALID_TEXT.index("[[testing.risk.critical]]", start + 1)
        missing = VALID_TEXT[:start] + VALID_TEXT[end:]
        self.assert_config_error(missing, "missing mandatory category/categories: credentials-and-secrets")

        duplicate = replaced('category = "pii"', 'category = "credentials-and-secrets"')
        self.assert_config_error(duplicate, "repeats category 'credentials-and-secrets'")

    def test_unknown_category_check_and_unmatched_action_fail(self):
        cases = (
            (replaced('category = "pii"', 'category = "health-data"'), "category is unknown"),
            (replaced('"repository-tests/full"]', '"unknown-check"]'), "unknown check id"),
            (replaced('unmatched = "critical"', 'unmatched = "reversible"'), "unmatched must be 'critical'"),
        )
        for text, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_binding_arrays_must_be_nonempty_unique_strings(self):
        cases = (
            (replaced('path_globs = [\n  "**/.env",', "path_globs = [\n  4,"), "non-empty string"),
            (replaced('required_check_ids = ["core-scope", "reconcile", "repository-tests/full"]', "required_check_ids = []"), "non-empty array"),
            (replaced('required_check_ids = ["core-scope", "reconcile", "repository-tests/full"]', 'required_check_ids = ["core-scope", "core-scope"]'), "duplicate values"),
        )
        for text, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_config_error(text, pattern)

    def test_globs_are_strict_relative_posix_patterns(self):
        bad_patterns = (
            "/absolute/**",
            "windows\\**",
            "services//**",
            "../services/**",
            "services/***/file",
            "services/[abc/file",
            "services/abc]/file",
        )
        for pattern in bad_patterns:
            with self.subTest(pattern=pattern):
                text = replaced('"**/.env"', repr(pattern).replace("'", '"'))
                self.assert_config_error(text, "path glob|POSIX|relative|segments|invalid|unterminated|unmatched")


class RiskClassificationTests(unittest.TestCase):
    def setUp(self):
        self.policy = CONFIG.parse_policy(VALID_TEXT)

    def test_known_ordinary_path_is_reversible(self):
        result = CONFIG.classify_paths(("services/quote-api/quote_api.py",), self.policy)
        self.assertFalse(result.is_critical)
        self.assertEqual(("ordinary-repository-work",), result.reversible_ids)
        self.assertEqual(("services/quote-api/quote_api.py",), result.reversible_paths)
        self.assertEqual((), result.required_check_ids)

    def test_gate_control_paths_are_authorization_critical(self):
        paths = (
            "agentfold.toml",
            "automation/file_test_budget_task.py",
            "automation/hooks/pre-commit",
            "automation/run_test_gate.py",
            "automation/run_tests.py",
            "automation/test_gate_config.py",
            "automation/test_gate_controller.py",
            "automation/test_manifest.py",
            "automation/_vendor/tomli/_parser.py",
        )
        for path in paths:
            with self.subTest(path=path):
                result = CONFIG.classify_paths((path,), self.policy)
                if HAS_HARDENED_RISK_PATHS:
                    self.assertTrue(result.is_critical)
                    self.assertIn("repository-tests/full", result.required_check_ids)
                else:
                    self.assertFalse(result.is_critical)
                    self.assertEqual((path,), result.reversible_paths)
                    self.assertEqual((), result.required_check_ids)

    def test_new_executable_paths_fail_closed_while_allowlisted_paths_stay_reversible(self):
        for path in ("services/quote-api/handler.py", "automation/helper.py"):
            with self.subTest(path=path):
                result = CONFIG.classify_paths((path,), self.policy)
                if HAS_HARDENED_RISK_PATHS:
                    self.assertTrue(result.is_critical)
                    self.assertEqual((path,), result.unmatched_paths)
                else:
                    self.assertFalse(result.is_critical)
                    self.assertEqual((path,), result.reversible_paths)
        for path in (
            "services/quote-api/quote_api.py",
            "automation/mine_cochange.py",
        ):
            with self.subTest(path=path):
                self.assertFalse(CONFIG.classify_paths((path,), self.policy).is_critical)

    def test_critical_match_wins_over_reversible_and_unions_checks(self):
        result = CONFIG.classify_paths(
            ("services/quote-api/private-auth-secret.py",),
            self.policy,
        )
        self.assertTrue(result.is_critical)
        self.assertEqual(
            ("authorization", "credentials-and-secrets"),
            tuple(binding.category for binding in result.critical_bindings),
        )
        self.assertEqual(tuple(sorted(CONFIG.KNOWN_CHECK_IDS)), result.required_check_ids)
        self.assertEqual((), result.reversible_ids)

    def test_double_star_matches_root_and_nested_paths(self):
        root = CONFIG.classify_paths((".env",), self.policy)
        nested = CONFIG.classify_paths(("services/example/.env.local",), self.policy)
        self.assertTrue(root.is_critical)
        self.assertTrue(nested.is_critical)

    def test_unmatched_path_is_synthetic_critical_with_fail_closed_checks(self):
        result = CONFIG.classify_paths(("new-top-level/file.py",), self.policy)
        self.assertTrue(result.is_critical)
        self.assertEqual(("new-top-level/file.py",), result.unmatched_paths)
        self.assertEqual(tuple(sorted(CONFIG.KNOWN_CHECK_IDS)), result.required_check_ids)
        self.assertEqual((), result.critical_bindings)

    def test_classification_deduplicates_and_sorts_paths(self):
        result = CONFIG.classify_paths(
            (
                "services/quote-cli/quote_cli.py",
                "services/quote-api/quote_api.py",
                "services/quote-cli/quote_cli.py",
            ),
            self.policy,
        )
        self.assertEqual(
            (
                "services/quote-api/quote_api.py",
                "services/quote-cli/quote_cli.py",
            ),
            result.reversible_paths,
        )

    def test_runtime_paths_must_also_be_relative_posix(self):
        for path in ("/absolute", "../escape", "windows\\path"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "relative POSIX|must not contain"):
                    CONFIG.classify_paths((path,), self.policy)

    def test_compatibility_helpers_return_the_same_required_checks(self):
        path = ("services/quote-api/auth.py",)
        result = CONFIG.match_critical_paths(path, self.policy)
        self.assertEqual(result.required_check_ids, CONFIG.required_critical_checks(path, self.policy))


class PolicyUnionTests(unittest.TestCase):
    def setUp(self):
        self.base = CONFIG.parse_policy(VALID_TEXT)

    def test_union_preserves_base_critical_when_candidate_glob_no_longer_matches(self):
        candidate_text = replaced('"**/*secret*"', '"**/*classified*"')
        candidate = CONFIG.parse_policy(candidate_text)
        union = CONFIG.union_policies(self.base, candidate)

        result = CONFIG.classify_paths(("services/example/secret_store.py",), union)

        self.assertTrue(result.is_critical)
        self.assertEqual(("credentials-and-secrets",), tuple(b.category for b in result.critical_bindings))

    def test_candidate_cannot_make_base_unmatched_path_reversible(self):
        candidate_text = VALID_TEXT.replace(
            '  "templates/**",\n]',
            '  "templates/**",\n  "new-top-level/**",\n]',
            1,
        )
        union = CONFIG.union_policies(self.base, CONFIG.parse_policy(candidate_text))

        result = CONFIG.classify_paths(("new-top-level/file.py",), union)

        self.assertTrue(result.is_critical)
        self.assertEqual(("new-top-level/file.py",), result.unmatched_paths)
        self.assertEqual((), result.reversible_ids)

    def test_path_reversible_under_both_policies_stays_reversible(self):
        union = CONFIG.union_policies(self.base, CONFIG.parse_policy(VALID_TEXT))
        result = CONFIG.classify_paths(("services/quote-api/quote_api.py",), union)
        self.assertFalse(result.is_critical)
        self.assertEqual(("ordinary-repository-work",), result.reversible_ids)
        self.assertEqual((), union.hard_triggers)

    def test_union_preserves_base_service_dependencies(self):
        if not HAS_SERVICE_DEPENDENCIES:
            with self.assertRaisesRegex(CONFIG.ConfigError, "unknown key"):
                CONFIG.parse_policy(DEPENDENCY_TEXT)
            return
        union = CONFIG.union_policies(
            CONFIG.parse_policy(DEPENDENCY_TEXT),
            self.base,
        )
        self.assertEqual((("quote-api", ("quote-cli",)),), union.service_dependencies)

    def test_union_combines_distinct_base_and_candidate_dependencies(self):
        if not HAS_SERVICE_DEPENDENCIES:
            with self.assertRaisesRegex(CONFIG.ConfigError, "unknown key"):
                CONFIG.parse_policy(DEPENDENCY_TEXT)
            return
        base = CONFIG.parse_policy(DEPENDENCY_TEXT)
        candidate = CONFIG.parse_policy(
            with_dependencies('{ payments = ["worker"] }')
        )

        union = CONFIG.union_policies(base, candidate)

        self.assertEqual(
            (
                ("payments", ("worker",)),
                ("quote-api", ("quote-cli",)),
            ),
            union.service_dependencies,
        )

    def test_hard_trigger_and_smaller_limits_survive_candidate_downgrade(self):
        candidate_text = MANUAL_CONFIG.replace(
            "target_seconds = 300\nmaximum_seconds = 900",
            "target_seconds = 600\nmaximum_seconds = 1200",
            1,
        ).replace(
            "target_seconds = 60\nmaximum_seconds = 60",
            "target_seconds = 120\nmaximum_seconds = 120",
            1,
        )
        union = CONFIG.union_policies(
            CONFIG.parse_policy(HARD_CONFIG), CONFIG.parse_policy(candidate_text)
        )

        self.assertEqual(("pull-request",), union.hard_triggers)
        self.assertEqual((60.0, 60.0), (union.routine.target_seconds, union.routine.maximum_seconds))
        self.assertEqual(300.0, union.final_target_seconds)
        self.assertEqual(900.0, union.final_maximum_seconds)

    def test_union_digest_binds_both_policy_roles(self):
        candidate = CONFIG.parse_policy(replaced("target_seconds = 300", "target_seconds = 301"))
        forward = CONFIG.union_policies(self.base, candidate)
        reverse = CONFIG.union_policies(candidate, self.base)
        self.assertNotEqual(forward.digest, reverse.digest)

    def test_load_policy_union_reads_both_files(self):
        with tempfile.TemporaryDirectory() as scratch:
            base_path = Path(scratch) / "base.toml"
            candidate_path = Path(scratch) / "candidate.toml"
            base_path.write_text(VALID_TEXT, encoding="utf-8")
            candidate_path.write_text(VALID_TEXT, encoding="utf-8")
            union = CONFIG.load_policy_union(base_path, candidate_path)
        self.assertIsInstance(union, CONFIG.PolicyUnion)


if __name__ == "__main__":
    unittest.main()
