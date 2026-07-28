"""Exact runtime snapshots admitted during the hard-v2 to manual-v3 migration."""

import hashlib
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
CLEANUP_FIXED_HARD_V2 = "cleanup-fixed-hard-v2"
MANUAL_V3 = "manual-v3"

HARD_V2_CONFIG_SHA256 = (
    "8b0ac65230d4bece59cf71305cdbb071e4d70817dbb127b4f6e7a0294aceabb2"
)
CLEANUP_FIXED_HARD_V2_RUNNER_SHA256 = (
    "6897db54179d6b106157c484d801d483eaab503b21792b7f4299aeccb3897107"
)
HARD_V2_TEST_RUNNER_SHA256 = (
    "8d3d1f6004e32b25a04a03a2da6fbd88f1bfea314e90f0ee37244abfa67336df"
)
HARD_V2_WORKFLOW_SHA256 = (
    "d3d2882bbe3a701071de68ffeb58b9c2d8d59371e75c660b7255fc6f0b55d4c3"
)
MANUAL_V3_CONFIG_SHA256 = (
    "f23f32fa5e399bea12dd49871cd9154e0922164083876c717db96ffe7427f16c"
)
MANUAL_V3_RUNNER_SHA256 = (
    "fb37e8361263a054859e13789b645f57b88eb8f922161ec2818156471d0a50cc"
)
MANUAL_V3_TEST_RUNNER_SHA256 = (
    "dbdc4cfeb4020551480c797944c203378ea26e9e2d2efea4d1dd5758b5b71c89"
)
MANUAL_V3_WORKFLOW_SHA256 = (
    "a07b4751a93e11534586ffebe33e5a34af47f4900568493eea57bcd350a66cf1"
)

_EXACT_PAIRS = {
    (
        HARD_V2_CONFIG_SHA256,
        CLEANUP_FIXED_HARD_V2_RUNNER_SHA256,
        HARD_V2_TEST_RUNNER_SHA256,
        HARD_V2_WORKFLOW_SHA256,
    ): CLEANUP_FIXED_HARD_V2,
    (
        MANUAL_V3_CONFIG_SHA256,
        MANUAL_V3_RUNNER_SHA256,
        MANUAL_V3_TEST_RUNNER_SHA256,
        MANUAL_V3_WORKFLOW_SHA256,
    ): MANUAL_V3,
}

# These are the only legacy assertions whose expected value changes with the
# admitted runtime pair. All other behavior stays invariant across the migration.
EXPECTATIONS = {
    CLEANUP_FIXED_HARD_V2: {
        "manual_named_outcome": "not-run",
        "hard_matching_outcome": None,
        "hard_other_outcome": "not-run",
        "transition_enforcement": "unobserved",
        "receipt_schema": "agentfold.test-component-receipt/v2",
        "starter_final_mode": "hard",
        "starter_final_trigger": "pull-request",
        "identical_union_hard_triggers": ("pull-request",),
    },
    MANUAL_V3: {
        "manual_named_outcome": "blocked-incomplete",
        "hard_matching_outcome": "blocked-incomplete",
        "hard_other_outcome": "blocked-incomplete",
        "transition_enforcement": "not-enforced",
        "receipt_schema": "agentfold.test-component-receipt/v3",
        "starter_final_mode": "manual",
        "starter_final_trigger": None,
        "identical_union_hard_triggers": (),
    },
}


def _sha256(content):
    if not isinstance(content, bytes):
        raise TypeError("gate migration snapshots must be classified from bytes")
    return hashlib.sha256(content).hexdigest()


def classify(config_bytes, runner_bytes, test_runner_bytes, workflow_bytes):
    """Return the exact admitted tuple name; reject crossed or unknown bytes."""
    pair = (
        _sha256(config_bytes),
        _sha256(runner_bytes),
        _sha256(test_runner_bytes),
        _sha256(workflow_bytes),
    )
    regime = _EXACT_PAIRS.get(pair)
    if regime is None:
        raise AssertionError(
            "the four test-gate runtime files are not one exact admitted "
            "migration tuple: config_sha256={} gate_runner_sha256={} "
            "test_runner_sha256={} workflow_sha256={}".format(
                pair[0], pair[1], pair[2], pair[3]
            )
        )
    return regime


def classify_repository(repository):
    """Classify the four runtime files without parsing or executing any of them."""
    return classify(
        (repository / "agentfold.toml").read_bytes(),
        (repository / "automation/run_test_gate.py").read_bytes(),
        (repository / "automation/run_tests.py").read_bytes(),
        (repository / ".github/workflows/harness.yml").read_bytes(),
    )


class GateMigrationSnapshotTests(unittest.TestCase):
    def test_repository_pair_is_an_exact_admitted_diagonal(self):
        self.assertIn(
            classify_repository(REPO), (CLEANUP_FIXED_HARD_V2, MANUAL_V3)
        )

    def test_both_exact_digest_diagonals_are_admitted(self):
        cases = (
            (
                CLEANUP_FIXED_HARD_V2,
                (
                    HARD_V2_CONFIG_SHA256,
                    CLEANUP_FIXED_HARD_V2_RUNNER_SHA256,
                    HARD_V2_TEST_RUNNER_SHA256,
                    HARD_V2_WORKFLOW_SHA256,
                ),
            ),
            (
                MANUAL_V3,
                (
                    MANUAL_V3_CONFIG_SHA256,
                    MANUAL_V3_RUNNER_SHA256,
                    MANUAL_V3_TEST_RUNNER_SHA256,
                    MANUAL_V3_WORKFLOW_SHA256,
                ),
            ),
        )
        for expected, digests in cases:
            with self.subTest(expected=expected), mock.patch(
                "{}._sha256".format(__name__), side_effect=digests
            ):
                self.assertEqual(
                    expected,
                    classify(b"config", b"gate", b"tests", b"workflow"),
                )

    def test_crossing_each_digest_axis_between_regimes_is_rejected(self):
        hard = (
            HARD_V2_CONFIG_SHA256,
            CLEANUP_FIXED_HARD_V2_RUNNER_SHA256,
            HARD_V2_TEST_RUNNER_SHA256,
            HARD_V2_WORKFLOW_SHA256,
        )
        manual = (
            MANUAL_V3_CONFIG_SHA256,
            MANUAL_V3_RUNNER_SHA256,
            MANUAL_V3_TEST_RUNNER_SHA256,
            MANUAL_V3_WORKFLOW_SHA256,
        )
        for starting, replacement in ((hard, manual), (manual, hard)):
            for axis in range(4):
                crossed = list(starting)
                crossed[axis] = replacement[axis]
                with self.subTest(starting=starting, axis=axis), mock.patch(
                    "{}._sha256".format(__name__), side_effect=tuple(crossed)
                ):
                    with self.assertRaisesRegex(AssertionError, "not one exact admitted"):
                        classify(b"config", b"gate", b"tests", b"workflow")

    def test_unknown_digest_on_each_axis_is_rejected(self):
        hard = (
            HARD_V2_CONFIG_SHA256,
            CLEANUP_FIXED_HARD_V2_RUNNER_SHA256,
            HARD_V2_TEST_RUNNER_SHA256,
            HARD_V2_WORKFLOW_SHA256,
        )
        for axis in range(4):
            unknown = list(hard)
            unknown[axis] = "0" * 64
            with self.subTest(axis=axis), mock.patch(
                "{}._sha256".format(__name__), side_effect=tuple(unknown)
            ):
                with self.assertRaisesRegex(AssertionError, "not one exact admitted"):
                    classify(b"config", b"gate", b"tests", b"workflow")

    def test_one_byte_mutation_of_each_runtime_file_is_rejected(self):
        runtime = (
            (REPO / "agentfold.toml").read_bytes(),
            (REPO / "automation/run_test_gate.py").read_bytes(),
            (REPO / "automation/run_tests.py").read_bytes(),
            (REPO / ".github/workflows/harness.yml").read_bytes(),
        )
        for axis in range(4):
            mutated = list(runtime)
            content = mutated[axis]
            mutated[axis] = bytes((content[0] ^ 1,)) + content[1:]
            with self.subTest(axis=axis):
                with self.assertRaisesRegex(AssertionError, "not one exact admitted"):
                    classify(*mutated)


if __name__ == "__main__":
    unittest.main()
