#!/usr/bin/env python3
"""Closed, byte-exact classifier for the test-gate migration floor.

The compatibility floor may describe either side of a planned two-commit
migration.  It must never infer a generation from an API shape or from one
headline file: every executable and dependency in the controller closure is
read from the repository view being tested and matched as one exact tuple.
"""

import hashlib
import shutil
import stat
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
ABSENT = "absent"
LEGACY_GENERATION = "legacy-manual-v3"
SPLIT_GENERATION = "split-controller-v5"
DEADLINE_GENERATION = "deadline-handoff-v2"

COMMON_RECORDS = (
    ("agentfold.toml", "100644", "f23f32fa5e399bea12dd49871cd9154e0922164083876c717db96ffe7427f16c"),
    ("automation/_vendor/__init__.py", "100644", "1fe7106b30c3366c8110e291d1aa0c5a5e095f691ebc712d37a2ab5c6493128b"),
    ("automation/_vendor/tomli/__init__.py", "100644", "26153057ae830758381efb7551009531d7c2bbe220015f055e6bc353da27c5de"),
    ("automation/_vendor/tomli/_parser.py", "100644", "83df8435a00b4be07c768918a42bb35056a55a5a20ed3f922183232d9496aed3"),
    ("automation/_vendor/tomli/_re.py", "100644", "75b8e0e428594f6dca6bdcfd0c73977ddb52a4fc147dd80c5e78fc34ea25cbec"),
    ("automation/_vendor/tomli/_types.py", "100644", "f864c6d9552a929c7032ace654ee05ef26ca75d21b027b801d77e65907138b74"),
    ("automation/file_test_budget_task.py", "100644", "5ea2e7afda7194f51e78cdb431f8088307a12d9258793d1c35afdcde03473239"),
    ("automation/test_gate_config.py", "100644", "d23d684c38d265899fedd4f9c9a1adc90f3e0b0f02097e41839dd3166de380cc"),
    ("automation/test_manifest.py", "100644", "d20b545f9db9566f74be26cb3ce5518b6893544d377e389f577925b0eba5679e"),
)

LEGACY_RECORDS = tuple(sorted(COMMON_RECORDS + (
    (".github/workflows/harness.yml", "100644", "a07b4751a93e11534586ffebe33e5a34af47f4900568493eea57bcd350a66cf1"),
    ("automation/hooks/pre-commit", "100755", "0ceac7e5f0f793f043ff7f8895ac0737f7a1ba61b1c1991e20a466df6c37eb3e"),
    ("automation/run_test_gate.py", "100644", "a27b85db53896db9c81861e9e293464b3f49e014dbefc7ad4410fee30069498e"),
    ("automation/run_tests.py", "100644", "dbdc4cfeb4020551480c797944c203378ea26e9e2d2efea4d1dd5758b5b71c89"),
    ("automation/test_gate_controller.py", ABSENT, ABSENT),
)))

SPLIT_RECORDS = tuple(sorted(COMMON_RECORDS + (
    (".github/workflows/harness.yml", "100644", "d7f5dfdb98eb3d34ef46c577eb1e99ba04a42c58ccff52b718fa63d2e3f69ab0"),
    ("automation/hooks/pre-commit", "100755", "e5817b089fb2f173c0f9fd7ad998ea27bd56dee2514a54da64c99f7c3a3fb42d"),
    ("automation/run_test_gate.py", "100644", "89f4ac3c421d888c316159336863d8ce8150aba90991e9530a0e09ed32f81e74"),
    ("automation/run_tests.py", "100644", "fadefe0bb6ca063c6fbbf03a2c3fc010287d4466161ab2b564501ff4aeaf5cda"),
    ("automation/test_gate_controller.py", "100644", "de1f88d1a3529cf7f98969de5a309fe8e99b2b735ae3917049bc3fe958dcedea"),
)))

DEADLINE_RECORDS = tuple(sorted((
    ("agentfold.toml", "100644", "f23f32fa5e399bea12dd49871cd9154e0922164083876c717db96ffe7427f16c"),
    ("automation/_vendor/__init__.py", "100644", "1fe7106b30c3366c8110e291d1aa0c5a5e095f691ebc712d37a2ab5c6493128b"),
    ("automation/_vendor/tomli/__init__.py", "100644", "26153057ae830758381efb7551009531d7c2bbe220015f055e6bc353da27c5de"),
    ("automation/_vendor/tomli/_parser.py", "100644", "83df8435a00b4be07c768918a42bb35056a55a5a20ed3f922183232d9496aed3"),
    ("automation/_vendor/tomli/_re.py", "100644", "75b8e0e428594f6dca6bdcfd0c73977ddb52a4fc147dd80c5e78fc34ea25cbec"),
    ("automation/_vendor/tomli/_types.py", "100644", "f864c6d9552a929c7032ace654ee05ef26ca75d21b027b801d77e65907138b74"),
    ("automation/file_test_budget_task.py", "100644", "5ea2e7afda7194f51e78cdb431f8088307a12d9258793d1c35afdcde03473239"),
    ("automation/test_gate_config.py", "100644", "e0aaedbadfb06675ab9bb3a6179a925db0cc6adf0f5f52ec1d963440a44255a7"),
    ("automation/test_manifest.py", "100644", "d20b545f9db9566f74be26cb3ce5518b6893544d377e389f577925b0eba5679e"),
    (".github/workflows/harness.yml", "100644", "d7f5dfdb98eb3d34ef46c577eb1e99ba04a42c58ccff52b718fa63d2e3f69ab0"),
    ("automation/hooks/pre-commit", "100755", "e5817b089fb2f173c0f9fd7ad998ea27bd56dee2514a54da64c99f7c3a3fb42d"),
    ("automation/run_test_gate.py", "100644", "f11b9ca71684b18b9dd3be913f95a5b27662b8f6f0ccece304945a06540a8a88"),
    ("automation/run_tests.py", "100644", "fadefe0bb6ca063c6fbbf03a2c3fc010287d4466161ab2b564501ff4aeaf5cda"),
    ("automation/test_gate_controller.py", "100644", "d52f5ce066d0415250678d9d2a8e5c32b0a6deeb1a8dcf7f988483fba6f5772c"),
)))

PARSER_COMPAT_RECORDS = tuple(sorted((
    ("agentfold.toml", "100644", "e1db9aea6f6f21415709fd1e566e55323dbc2db0594869d1e74a186ab10d54e9"),
    ("automation/_vendor/__init__.py", "100644", "1fe7106b30c3366c8110e291d1aa0c5a5e095f691ebc712d37a2ab5c6493128b"),
    ("automation/_vendor/tomli/__init__.py", "100644", "26153057ae830758381efb7551009531d7c2bbe220015f055e6bc353da27c5de"),
    ("automation/_vendor/tomli/_parser.py", "100644", "83df8435a00b4be07c768918a42bb35056a55a5a20ed3f922183232d9496aed3"),
    ("automation/_vendor/tomli/_re.py", "100644", "75b8e0e428594f6dca6bdcfd0c73977ddb52a4fc147dd80c5e78fc34ea25cbec"),
    ("automation/_vendor/tomli/_types.py", "100644", "f864c6d9552a929c7032ace654ee05ef26ca75d21b027b801d77e65907138b74"),
    ("automation/file_test_budget_task.py", "100644", "5ea2e7afda7194f51e78cdb431f8088307a12d9258793d1c35afdcde03473239"),
    ("automation/test_gate_config.py", "100644", "4b883d081f4472f4dd73465d440f71438637acd65d5c7f6a82b437639a2d9853"),
    ("automation/test_manifest.py", "100644", "d20b545f9db9566f74be26cb3ce5518b6893544d377e389f577925b0eba5679e"),
    (".github/workflows/harness.yml", "100644", "d7f5dfdb98eb3d34ef46c577eb1e99ba04a42c58ccff52b718fa63d2e3f69ab0"),
    ("automation/hooks/pre-commit", "100755", "e5817b089fb2f173c0f9fd7ad998ea27bd56dee2514a54da64c99f7c3a3fb42d"),
    ("automation/run_test_gate.py", "100644", "f11b9ca71684b18b9dd3be913f95a5b27662b8f6f0ccece304945a06540a8a88"),
    ("automation/run_tests.py", "100644", "fadefe0bb6ca063c6fbbf03a2c3fc010287d4466161ab2b564501ff4aeaf5cda"),
    ("automation/test_gate_controller.py", "100644", "d52f5ce066d0415250678d9d2a8e5c32b0a6deeb1a8dcf7f988483fba6f5772c"),
)))

REVIEW_REPAIR_RECORDS = tuple(sorted((
    ("agentfold.toml", "100644", "b126e7224c1236bfd6f7bbe2f2bd61cd759d42c282aaf59433fdbc93d8ca5e6f"),
    ("automation/_vendor/__init__.py", "100644", "1fe7106b30c3366c8110e291d1aa0c5a5e095f691ebc712d37a2ab5c6493128b"),
    ("automation/_vendor/tomli/__init__.py", "100644", "26153057ae830758381efb7551009531d7c2bbe220015f055e6bc353da27c5de"),
    ("automation/_vendor/tomli/_parser.py", "100644", "83df8435a00b4be07c768918a42bb35056a55a5a20ed3f922183232d9496aed3"),
    ("automation/_vendor/tomli/_re.py", "100644", "75b8e0e428594f6dca6bdcfd0c73977ddb52a4fc147dd80c5e78fc34ea25cbec"),
    ("automation/_vendor/tomli/_types.py", "100644", "f864c6d9552a929c7032ace654ee05ef26ca75d21b027b801d77e65907138b74"),
    ("automation/file_test_budget_task.py", "100644", "bbd756ba55ebafb25b76992d36bc81de396641295532dd15f7462494903990de"),
    ("automation/test_gate_config.py", "100644", "4b883d081f4472f4dd73465d440f71438637acd65d5c7f6a82b437639a2d9853"),
    ("automation/test_manifest.py", "100644", "d20b545f9db9566f74be26cb3ce5518b6893544d377e389f577925b0eba5679e"),
    (".github/workflows/harness.yml", "100644", "d7f5dfdb98eb3d34ef46c577eb1e99ba04a42c58ccff52b718fa63d2e3f69ab0"),
    ("automation/hooks/pre-commit", "100755", "e5817b089fb2f173c0f9fd7ad998ea27bd56dee2514a54da64c99f7c3a3fb42d"),
    ("automation/run_test_gate.py", "100644", "834c4d1b917228c87ed881ef48915313483a1b234a1d0612c5d30e7220c35c8a"),
    ("automation/run_tests.py", "100644", "18cd241b5616ab91e996dd3e5b88331d490ccefabebb00cb10da982448d26fd7"),
    ("automation/test_gate_controller.py", "100644", "0feaffbd70c014d9a0b44082042512fc77ff3c42d962ae830443947da76dcab2"),
)))

CLASSIFIED_PATHS = tuple(record[0] for record in LEGACY_RECORDS)


def _file_record(root, relative):
    path = root / relative
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return relative, ABSENT, ABSENT
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return relative, "unsupported", ABSENT
    mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
    return relative, mode, hashlib.sha256(path.read_bytes()).hexdigest()


def gate_generation_records(root=REPO):
    """Read the exact generation tuple from the repository view under test."""
    root = Path(root)
    return tuple(_file_record(root, relative) for relative in CLASSIFIED_PATHS)


def classify_gate_generation_records(records):
    """Classify only either complete admitted tuple; reject every hybrid."""
    records = tuple(records)
    if records == LEGACY_RECORDS:
        return LEGACY_GENERATION
    if records == SPLIT_RECORDS:
        return SPLIT_GENERATION
    if records == DEADLINE_RECORDS:
        return DEADLINE_GENERATION
    if records == PARSER_COMPAT_RECORDS:
        return DEADLINE_GENERATION
    if records == REVIEW_REPAIR_RECORDS:
        return DEADLINE_GENERATION
    return "invalid"


def gate_generation(root=REPO):
    records = gate_generation_records(root)
    generation = classify_gate_generation_records(records)
    if generation == "invalid":
        raise AssertionError(
            "tested repository view is outside both admitted gate generations: {!r}".format(
                records
            )
        )
    return generation


class GateMigrationGenerationTests(unittest.TestCase):
    def test_current_tested_view_is_one_exact_generation(self):
        self.assertIn(
            gate_generation(),
            (LEGACY_GENERATION, SPLIT_GENERATION, DEADLINE_GENERATION),
            gate_generation_records(),
        )

    def test_both_closed_tuples_are_admitted(self):
        self.assertEqual(
            LEGACY_GENERATION, classify_gate_generation_records(LEGACY_RECORDS)
        )
        self.assertEqual(
            SPLIT_GENERATION, classify_gate_generation_records(SPLIT_RECORDS)
        )
        self.assertEqual(
            DEADLINE_GENERATION, classify_gate_generation_records(DEADLINE_RECORDS)
        )
        self.assertEqual(
            DEADLINE_GENERATION,
            classify_gate_generation_records(PARSER_COMPAT_RECORDS),
        )
        self.assertEqual(
            DEADLINE_GENERATION,
            classify_gate_generation_records(REVIEW_REPAIR_RECORDS),
        )

    def test_sealed_regular_modes_preserve_exact_generation_admission(self):
        generation = gate_generation()
        expected_records = gate_generation_records()
        observed_modes = set()
        with tempfile.TemporaryDirectory() as scratch:
            sealed_root = Path(scratch) / "sealed-view"
            sealed_root.mkdir()
            for record in expected_records:
                relative, mode, _digest = record
                if mode == ABSENT:
                    continue
                source = REPO / relative
                destination = sealed_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                sealed_mode = 0o500 if mode == "100755" else 0o400
                destination.chmod(sealed_mode)
                self.assertEqual(sealed_mode, destination.stat().st_mode & 0o777)
                self.assertEqual(record, _file_record(sealed_root, relative))
                observed_modes.add(mode)
            self.assertEqual({"100644", "100755"}, observed_modes)
            self.assertEqual(generation, gate_generation(sealed_root))
            executable_record = next(
                record for record in expected_records if record[1] == "100755"
            )
            executable_path = sealed_root / executable_record[0]
            for sealed_mode in (0o410, 0o401):
                with self.subTest(group_or_world_only_execute=oct(sealed_mode)):
                    executable_path.chmod(sealed_mode)
                    observed = _file_record(sealed_root, executable_record[0])
                    self.assertEqual("100644", observed[1])
                    self.assertEqual(executable_record[2], observed[2])
                    records = gate_generation_records(sealed_root)
                    self.assertEqual(
                        "invalid", classify_gate_generation_records(records)
                    )
                    with self.assertRaisesRegex(
                        AssertionError, "outside both admitted gate generations"
                    ):
                        gate_generation(sealed_root)
            executable_path.chmod(0o500)
            self.assertEqual(generation, gate_generation(sealed_root))

    def test_one_path_from_every_other_generation_always_rejects_the_tuple(self):
        generations = (
            (LEGACY_GENERATION, LEGACY_RECORDS),
            (SPLIT_GENERATION, SPLIT_RECORDS),
            (DEADLINE_GENERATION + "-before-review", DEADLINE_RECORDS),
            (DEADLINE_GENERATION + "-parser-compat", PARSER_COMPAT_RECORDS),
            (DEADLINE_GENERATION + "-review-repair", REVIEW_REPAIR_RECORDS),
        )
        for base_name, base_records in generations:
            base = dict((record[0], record) for record in base_records)
            for donor_name, donor_records in generations:
                if donor_name == base_name:
                    continue
                donor = dict((record[0], record) for record in donor_records)
                differing = tuple(
                    path for path in CLASSIFIED_PATHS if base[path] != donor[path]
                )
                self.assertTrue(differing)
                for path in differing:
                    with self.subTest(
                        path=path, base=base_name, donor=donor_name
                    ):
                        mixed = dict(base)
                        mixed[path] = donor[path]
                        self.assertEqual(
                            "invalid",
                            classify_gate_generation_records(
                                tuple(mixed[name] for name in CLASSIFIED_PATHS)
                            ),
                        )

    def test_mode_hash_missing_and_common_dependency_mutations_reject(self):
        for generation, admitted in (
            (LEGACY_GENERATION, LEGACY_RECORDS),
            (SPLIT_GENERATION, SPLIT_RECORDS),
            (DEADLINE_GENERATION, DEADLINE_RECORDS),
            (DEADLINE_GENERATION + "-parser-compat", PARSER_COMPAT_RECORDS),
            (DEADLINE_GENERATION + "-review-repair", REVIEW_REPAIR_RECORDS),
        ):
            for index, record in enumerate(admitted):
                relative, mode, digest = record
                mutations = []
                changed_mode = "100755" if mode != "100755" else "100644"
                changed = list(admitted)
                changed[index] = (relative, changed_mode, digest)
                mutations.append(("mode", tuple(changed)))
                changed = list(admitted)
                changed[index] = (relative, mode, "0" * 64)
                mutations.append(("hash", tuple(changed)))
                changed = list(admitted)
                changed[index] = (relative, ABSENT, ABSENT)
                mutations.append(("missing", tuple(changed)))
                for mutation, records in mutations:
                    if records == admitted:
                        continue
                    with self.subTest(
                        generation=generation,
                        path=relative,
                        mutation=mutation,
                    ):
                        self.assertEqual(
                            "invalid", classify_gate_generation_records(records)
                        )

    def test_repository_classifier_raises_instead_of_branching_on_unknown_view(self):
        with self.assertRaisesRegex(
            AssertionError, "outside both admitted gate generations"
        ):
            gate_generation(Path(__file__).resolve().parents[2] / "missing-view")


if __name__ == "__main__":
    unittest.main()
