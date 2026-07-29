import contextlib
import datetime
import errno
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    import fcntl
except ImportError:
    fcntl = None


AUTOMATION = Path(__file__).resolve().parents[1]
GENERATION_PATH = AUTOMATION / "tests" / "test_gate_generations.py"
GENERATION_SPEC = importlib.util.spec_from_file_location(
    "test_budget_gate_generations", GENERATION_PATH
)
GATE_GENERATIONS = importlib.util.module_from_spec(GENERATION_SPEC)
GENERATION_SPEC.loader.exec_module(GATE_GENERATIONS)
GATE_GENERATIONS.gate_generation(AUTOMATION.parent)
PRODUCT_RECORDS = GATE_GENERATIONS.gate_generation_records(AUTOMATION.parent)
PARSER_COMPAT_ENDPOINT = "parser-compat"
REVIEW_REPAIR_ENDPOINT = "review-repair"
if PRODUCT_RECORDS == GATE_GENERATIONS.PARSER_COMPAT_RECORDS:
    PRODUCT_ENDPOINT = PARSER_COMPAT_ENDPOINT
elif PRODUCT_RECORDS == GATE_GENERATIONS.REVIEW_REPAIR_RECORDS:
    PRODUCT_ENDPOINT = REVIEW_REPAIR_ENDPOINT
else:
    raise AssertionError(
        "test-budget endpoint is neither exact parser-compat nor exact review-repair"
    )

MODULE_PATH = AUTOMATION / "file_test_budget_task.py"
SPEC = importlib.util.spec_from_file_location("file_test_budget_task", MODULE_PATH)
FILER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FILER
SPEC.loader.exec_module(FILER)

RECONCILE_PATH = AUTOMATION / "reconcile" / "reconcile.py"
RECONCILE_SPEC = importlib.util.spec_from_file_location(
    "reconcile_for_test_budget", RECONCILE_PATH
)
RECONCILE = importlib.util.module_from_spec(RECONCILE_SPEC)
sys.modules[RECONCILE_SPEC.name] = RECONCILE
RECONCILE_SPEC.loader.exec_module(RECONCILE)

CANDIDATE_A = "a" * 64
CANDIDATE_B = "b" * 64
RECEIPT_A = "c" * 64
RECEIPT_B = "d" * 64
RECEIPT_C = "e" * 64


class FileTestBudgetTaskTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "templates/task").mkdir(parents=True)
            (root / "templates/queue").mkdir(parents=True)
            (root / "templates/task/task.md").write_text(
                (MODULE_PATH.parents[1] / "templates/task/task.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            (root / "templates/queue/request.md").write_text(
                (MODULE_PATH.parents[1] / "templates/queue/request.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            yield root

    @staticmethod
    def occurrence(**changes):
        value = {
            "schema_id": "agentfold.testing.v1",
            "gate_id": "routine",
            "config_slot": "testing.routine.target_seconds",
            "actual_seconds": 72.5,
            "target_seconds": 60,
            "components": {"selection": 1.25, "tests": 70.5},
            "candidate": CANDIDATE_A,
            "receipt": RECEIPT_A,
            "command": "python3 automation/run_tests.py --routine",
            "trigger": "pre-commit",
            "environment": {
                "python_implementation": "CPython",
                "python_version": "3.13.4",
                "git_version": "git version 2.50.1",
            },
        }
        value.update(changes)
        return value

    @staticmethod
    def task_file(root, result):
        return root / result.task_path

    @staticmethod
    def request_file(root, result):
        return root / result.request_path

    @staticmethod
    def state(task):
        identity = FILER._field(task.read_text(encoding="utf-8"), "Finding identity").split(":", 1)[1]
        return FILER._read_journal(task.parent / FILER.JOURNAL_NAME, identity)[-1]

    @staticmethod
    def actor_owned_bytes(text):
        return text.encode("utf-8")

    def claim(self, root, created, status, actor_text="Actor note stays byte-identical."):
        old_dir = self.task_file(root, created).parent
        new_dir = root / "tasks" / status / old_dir.name
        new_dir.parent.mkdir(parents=True)
        old_dir.rename(new_dir)
        task = new_dir / "task.md"
        text = task.read_text(encoding="utf-8")
        text = text.replace("**Claimed-by:** unclaimed", "**Claimed-by:** test-agent")
        text = text.replace(
            f"**Queue actions:** `{created.request_path}`", "**Queue actions:** none"
        )
        text = text.replace("None yet.", actor_text)
        task.write_text(text, encoding="utf-8")
        self.request_file(root, created).unlink()
        return task

    def file(self, root, occurrence=None, **kwargs):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            result = FILER.file_budget_task(
                root,
                occurrence or self.occurrence(),
                today=kwargs.pop("today", "2026-07-27"),
                **kwargs,
            )
        return result, stderr.getvalue()

    def test_finding_identity_excludes_run_values(self):
        with self.repo() as root:
            first = FILER._normalize_occurrence(self.occurrence(), root)
            second = FILER._normalize_occurrence(
                self.occurrence(
                    actual_seconds=999,
                    target_seconds=10,
                    candidate=CANDIDATE_B,
                    receipt=RECEIPT_B,
                    components={"other": 999},
                ),
                root,
            )
            self.assertEqual(FILER.finding_identity(first), FILER.finding_identity(second))
            self.assertEqual(FILER.finding_key(first), FILER.finding_key(second))
            changed_schema = FILER._normalize_occurrence(
                self.occurrence(schema_id="agentfold.testing.v2"), root
            )
            self.assertEqual(
                FILER.finding_identity(first), FILER.finding_identity(changed_schema)
            )
            changed_slot = FILER._normalize_occurrence(
                self.occurrence(config_slot="testing.final.target_seconds"), root
            )
            self.assertNotEqual(
                FILER.finding_identity(first), FILER.finding_identity(changed_slot)
            )

    def test_new_finding_creates_task_and_pickup_and_prints_one_instruction(self):
        with self.repo() as root:
            result, stderr = self.file(root)
            self.assertEqual("created", result.disposition)
            self.assertTrue(result.mutated)
            self.assertTrue(self.task_file(root, result).is_file())
            self.assertTrue(self.request_file(root, result).is_file())
            task_text = self.task_file(root, result).read_text(encoding="utf-8")
            request_text = self.request_file(root, result).read_text(encoding="utf-8")
            self.assertIn(f"**Finding key:** {result.finding_key}", task_text)
            self.assertIn(f"`{result.request_path}`", task_text)
            self.assertIn("**Request kind:** task-pickup", request_text)
            self.assertIn("Stage the generated task and pickup request", stderr)
            self.assertEqual(1, stderr.count("Stage the generated"))
            self.assertTrue((root / "tmp/.file-test-budget-task.lock").exists())
            self.assertEqual(result.disposition, result["disposition"])
            self.assertEqual(result.as_dict(), dict(result))

    def test_new_receipt_appends_journal_and_preserves_task_body(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.task_file(root, created)
            original = task.read_text(encoding="utf-8")
            actor_text = "Actor diagnosed a process-spawn bottleneck."
            task.write_text(original.replace("None yet.", actor_text), encoding="utf-8")
            request_before = self.request_file(root, created).read_bytes()

            updated, stderr = self.file(
                root,
                self.occurrence(
                    actual_seconds=68,
                    target_seconds=55,
                    receipt=RECEIPT_B,
                    candidate=CANDIDATE_B,
                    components={"selection": 2, "tests": 60, "report": 1},
                ),
            )

            self.assertEqual("updated", updated.disposition)
            self.assertEqual("", stderr)
            text = task.read_text(encoding="utf-8")
            self.assertIn(actor_text, text)
            state = self.state(task)
            self.assertEqual(2, state["count"])
            self.assertEqual(68, state["latest_actual_seconds"])
            self.assertEqual(72.5, state["worst_actual_seconds"])
            self.assertEqual(55, state["target_seconds"])
            self.assertEqual(CANDIDATE_B, state["candidate"])
            self.assertEqual(RECEIPT_B, state["receipt"])
            self.assertEqual(2, state["worst_components"]["selection"])
            self.assertEqual(70.5, state["worst_components"]["tests"])
            self.assertEqual(request_before, self.request_file(root, created).read_bytes())

    def test_identical_receipt_does_not_rewrite_or_reprint(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.task_file(root, created)
            before = task.stat().st_mtime_ns, task.read_bytes()
            unchanged, stderr = self.file(
                root, self.occurrence(actual_seconds=800, candidate=CANDIDATE_B)
            )
            after = task.stat().st_mtime_ns, task.read_bytes()
            self.assertEqual("unchanged", unchanged.disposition)
            self.assertFalse(unchanged.mutated)
            self.assertEqual(before, after)
            self.assertEqual("", stderr)

    def test_two_open_matches_report_conflict_without_mutation(self):
        with self.repo() as root:
            created, _ = self.file(root)
            original_task = self.task_file(root, created)
            duplicate = root / "tasks/3_in-review/2026-07-27-duplicate/task.md"
            duplicate.parent.mkdir(parents=True)
            duplicate.write_bytes(original_task.read_bytes())
            before = original_task.read_bytes(), duplicate.read_bytes()
            result, _ = self.file(root, self.occurrence(receipt=RECEIPT_B))
            self.assertEqual("conflict", result.disposition)
            self.assertFalse(result.mutated)
            self.assertEqual(before, (original_task.read_bytes(), duplicate.read_bytes()))

    def test_claimed_task_appends_journal_in_each_live_status(self):
        for status in ("1_in-progress", "2_blocked", "3_in-review"):
            with self.subTest(status=status), self.repo() as root:
                created, _ = self.file(root)
                task = self.claim(root, created, status)
                original_path = task
                before_actor = self.actor_owned_bytes(task.read_text(encoding="utf-8"))
                result, _ = self.file(root, self.occurrence(receipt=RECEIPT_B))
                self.assertEqual("updated", result.disposition)
                self.assertTrue(result.mutated)
                self.assertEqual(original_path, root / result.task_path)
                text = task.read_text(encoding="utf-8")
                self.assertEqual(before_actor, self.actor_owned_bytes(text))
                self.assertIn("**Claimed-by:** test-agent", text)
                self.assertEqual(RECEIPT_B, self.state(task)["receipt"])
                self.assertEqual(2, self.state(task)["count"])

    def test_claimed_task_identical_receipt_is_unchanged(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.claim(root, created, "1_in-progress")
            before = task.stat().st_mtime_ns, task.read_bytes()
            result, stderr = self.file(root)
            after = task.stat().st_mtime_ns, task.read_bytes()
            self.assertEqual("unchanged", result.disposition)
            self.assertFalse(result.mutated)
            self.assertEqual(before, after)
            self.assertEqual("", stderr)

    def test_concurrent_actor_edit_retries_and_preserves_the_edit(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.claim(root, created, "1_in-progress", actor_text="Initial actor note.")
            real_append = FILER._append_journal_record
            attempts = 0

            def actor_wins_first_append(path, identity, state):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    current = task.read_text(encoding="utf-8")
                    task.write_text(
                        current.replace(
                            "Initial actor note.",
                            "Initial actor note.\nConcurrent actor diagnosis.",
                        ),
                        encoding="utf-8",
                    )
                    return False
                return real_append(path, identity, state)

            with mock.patch.object(
                FILER, "_append_journal_record", side_effect=actor_wins_first_append
            ):
                result, _ = self.file(root, self.occurrence(receipt=RECEIPT_B))
            self.assertEqual("updated", result.disposition)
            self.assertEqual(2, attempts)
            text = task.read_text(encoding="utf-8")
            self.assertIn("Concurrent actor diagnosis.", text)
            self.assertEqual(RECEIPT_B, self.state(task)["receipt"])

    def test_replaced_journal_path_is_never_overwritten(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.task_file(root, created)
            journal = task.parent / FILER.JOURNAL_NAME
            identity = FILER._field(task.read_text(encoding="utf-8"), "Finding identity").split(":", 1)[1]
            state = FILER._state_for(
                FILER._normalize_occurrence(
                    self.occurrence(receipt=RECEIPT_B), root
                ),
                self.state(task),
            )
            real_write = os.write
            replacement = b'{"actor":"replacement"}\n'

            def replace_path_before_append(descriptor, payload):
                actor_path = journal.with_name("actor-journal")
                actor_path.write_bytes(replacement)
                os.replace(actor_path, journal)
                return real_write(descriptor, payload)

            with mock.patch.object(FILER.os, "write", side_effect=replace_path_before_append):
                appended = FILER._append_journal_record(journal, identity, state)
            self.assertFalse(appended)
            self.assertEqual(replacement, journal.read_bytes())

    def test_nonowned_lookalike_is_a_conflict(self):
        with self.repo() as root:
            created, _ = self.file(root)
            task = self.task_file(root, created)
            task.write_text(
                task.read_text(encoding="utf-8").replace(
                    f"**Generated by:** {FILER.GENERATOR}",
                    "**Generated by:** somebody-else",
                ),
                encoding="utf-8",
            )
            before = task.read_bytes()
            result, _ = self.file(root, self.occurrence(receipt=RECEIPT_B))
            self.assertEqual("conflict", result.disposition)
            self.assertEqual(before, task.read_bytes())

    def test_done_match_creates_linked_same_day_recurrence_with_stable_suffix(self):
        with self.repo() as root:
            first, _ = self.file(root)
            old_dir = self.task_file(root, first).parent
            done_dir = root / "tasks/4_done" / old_dir.name
            done_dir.parent.mkdir(parents=True)
            old_dir.rename(done_dir)
            (root / first.request_path).unlink()
            task = done_dir / "task.md"
            task.write_text(
                task.read_text(encoding="utf-8")
                .replace("**Claimed-by:** unclaimed", "**Claimed-by:** test-agent")
                .replace(f"**Queue actions:** `{first.request_path}`", "**Queue actions:** none"),
                encoding="utf-8",
            )

            recurrence, stderr = self.file(root, self.occurrence(receipt=RECEIPT_B))
            self.assertEqual("created", recurrence.disposition)
            self.assertIn("-r1/task.md", recurrence.task_path)
            recurrent_text = self.task_file(root, recurrence).read_text(encoding="utf-8")
            self.assertIn(f"**Recurs after:** `{done_dir.name}`", recurrent_text)
            self.assertEqual(1, stderr.count("Stage the generated"))

    def test_next_day_recurrence_uses_new_date_without_suffix(self):
        with self.repo() as root:
            first, _ = self.file(root)
            old_dir = self.task_file(root, first).parent
            done_dir = root / "tasks/4_done" / old_dir.name
            done_dir.parent.mkdir(parents=True)
            old_dir.rename(done_dir)
            (root / first.request_path).unlink()
            task = done_dir / "task.md"
            task.write_text(
                task.read_text(encoding="utf-8")
                .replace("**Claimed-by:** unclaimed", "**Claimed-by:** test-agent")
                .replace(f"**Queue actions:** `{first.request_path}`", "**Queue actions:** none"),
                encoding="utf-8",
            )
            recurrence, _ = self.file(
                root, self.occurrence(receipt=RECEIPT_B), today="2026-07-28"
            )
            self.assertIn("tasks/0_backlog/2026-07-28-", recurrence.task_path)
            self.assertNotIn("-r1/", recurrence.task_path)

    def test_recurrence_link_uses_numeric_order_after_r9(self):
        with self.repo() as root:
            first, _ = self.file(root)
            source_dir = self.task_file(root, first).parent
            done_root = root / "tasks/4_done"
            done_root.mkdir(parents=True)
            base_name = source_dir.name
            (root / first.request_path).unlink()
            for number in range(1, 11):
                destination = done_root / f"{base_name}-r{number}"
                shutil.copytree(source_dir, destination)
            source_dir.rename(done_root / base_name)
            recurrence, _ = self.file(root, self.occurrence(receipt=RECEIPT_B))
            self.assertIn("-r11/task.md", recurrence.task_path)
            text = self.task_file(root, recurrence).read_text(encoding="utf-8")
            self.assertIn(f"**Recurs after:** `{base_name}-r10`", text)

    def test_rendering_preserves_unrelated_template_evolution(self):
        with self.repo() as root:
            task_template = root / "templates/task/task.md"
            request_template = root / "templates/queue/request.md"
            task_template.write_text(
                task_template.read_text(encoding="utf-8").replace(
                    "## Goal", "<!-- adopter task marker -->\n\n## Goal"
                ),
                encoding="utf-8",
            )
            request_template.write_text(
                request_template.read_text(encoding="utf-8").replace(
                    "## What you need to know",
                    "<!-- adopter request marker -->\n\n## What you need to know",
                ),
                encoding="utf-8",
            )
            result, _ = self.file(root)
            self.assertIn(
                "<!-- adopter task marker -->",
                self.task_file(root, result).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "<!-- adopter request marker -->",
                self.request_file(root, result).read_text(encoding="utf-8"),
            )

    def test_command_trigger_and_environment_persist_only_safe_identity(self):
        with self.repo() as root:
            result, _ = self.file(
                root,
                self.occurrence(
                    command=(
                        "automation/run_test_gate.py --gate routine "
                        "--api-token SHOULD_NOT_APPEAR --config /private/secret.toml"
                    ),
                    trigger="merge SHOULD_NOT_APPEAR",
                    environment={
                        "API_TOKEN": "SHOULD_NOT_APPEAR",
                        "python_implementation": "CPython",
                        "python_version": "3.13.4",
                        "git_version": "git version 2.50.1",
                        "platform": "SHOULD_NOT_APPEAR",
                    }
                ),
            )
            text = self.task_file(root, result).read_text(encoding="utf-8")
            self.assertNotIn("SHOULD_NOT_APPEAR", text)
            self.assertNotIn("/private/secret.toml", text)
            state = self.state(self.task_file(root, result))
            self.assertEqual("test-gate", state["command"])
            self.assertEqual("unrecognized-trigger", state["trigger"])
            self.assertEqual(
                {
                    "git_version": "2.50.1",
                    "python_implementation": "CPython",
                    "python_version": "3.13.4",
                },
                state["environment"],
            )

    def test_secret_like_candidate_and_receipt_are_rejected_without_echo(self):
        for field in ("candidate", "receipt"):
            with self.subTest(field=field), self.repo() as root:
                occurrence = self.occurrence(**{field: "SHOULD_NOT_APPEAR"})
                result, stderr = self.file(root, occurrence)
                self.assertEqual("error", result.disposition)
                self.assertFalse(result.mutated)
                self.assertNotIn("SHOULD_NOT_APPEAR", result.message)
                self.assertEqual("", stderr)
                self.assertFalse((root / "tasks").exists())

    def test_lock_timeout_returns_machine_finding_and_does_not_mutate(self):
        if fcntl is None:
            self.skipTest("POSIX flock is unavailable")
        with self.repo() as root:
            lock_dir = root / "tmp"
            lock_dir.mkdir()
            with (lock_dir / ".file-test-budget-task.lock").open("a+") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                result, stderr = self.file(root, lock_timeout=0)
            self.assertEqual("lock-timeout", result.disposition)
            self.assertFalse(result.mutated)
            self.assertEqual("", stderr)
            self.assertFalse((root / "tasks").exists())

    def test_lock_directory_fallback_is_cross_platform_and_times_out(self):
        with self.repo() as root:
            lock_dir = root / "tmp/.file-test-budget-task.lock.d"
            lock_dir.mkdir(parents=True)
            with mock.patch.object(FILER, "_fcntl", None), mock.patch.object(
                FILER, "_msvcrt", None
            ):
                result, _ = self.file(root, lock_timeout=0)
            self.assertEqual("lock-timeout", result.disposition)
            self.assertFalse(result.mutated)

    def test_windows_lock_backend_is_used_when_fcntl_is_unavailable(self):
        calls = []

        class FakeMsvcrt:
            LK_NBLCK = 1
            LK_UNLCK = 2

            @staticmethod
            def locking(_descriptor, operation, size):
                calls.append((operation, size))

        with self.repo() as root, mock.patch.object(FILER, "_fcntl", None), mock.patch.object(
            FILER, "_msvcrt", FakeMsvcrt
        ):
            with FILER._lock(root, 0):
                pass
        self.assertEqual([(FakeMsvcrt.LK_NBLCK, 1), (FakeMsvcrt.LK_UNLCK, 1)], calls)

    def test_read_only_and_invalid_input_are_nonraising_machine_findings(self):
        with self.repo() as root:
            with mock.patch.object(
                FILER, "_lock", side_effect=PermissionError(13, "read only")
            ):
                result, _ = self.file(root)
            self.assertEqual("read-only", result.disposition)
            self.assertFalse(result.mutated)

            invalid, _ = self.file(root, {"gate_id": "routine"})
            self.assertEqual("error", invalid.disposition)
            self.assertFalse(invalid.mutated)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == PARSER_COMPAT_ENDPOINT,
        "legacy rollback belongs to the parser-compat endpoint",
    )
    def test_parser_compat_pair_write_failure_rolls_back(self):
        with self.repo() as root:
            real_replace = os.replace
            calls = 0

            def fail_second(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated pickup write failure")
                return real_replace(source, destination)

            with mock.patch.object(FILER.os, "replace", side_effect=fail_second):
                result, stderr = self.file(root)
            self.assertEqual("error", result.disposition)
            self.assertFalse(result.mutated)
            self.assertEqual("", stderr)
            self.assertEqual([], list((root / "tasks/0_backlog").glob("*")))
            self.assertEqual(
                [], list((root / "message-queue/needs-agent/requests").glob("*.md"))
            )

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "no-delete publication belongs to the review-repair endpoint",
    )
    def test_pair_write_failure_leaves_visible_partial_pair_and_reports_mutation(self):
        with self.repo() as root:
            real_publish = FILER._publish_exclusive_file
            calls = 0

            def fail_request(source, destination):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("simulated pickup write failure")
                return real_publish(source, destination)

            with mock.patch.object(
                FILER, "_publish_exclusive_file", side_effect=fail_request
            ):
                result, stderr = self.file(root)
            self.assertEqual("error", result.disposition)
            self.assertTrue(result.mutated)
            self.assertEqual("", stderr)
            tasks = list((root / "tasks/0_backlog").glob("*"))
            self.assertEqual(1, len(tasks))
            self.assertTrue((tasks[0] / "task.md").is_file())
            self.assertTrue((tasks[0] / FILER.JOURNAL_NAME).is_file())
            self.assertEqual(
                [], list((root / "message-queue/needs-agent/requests").glob("*.md"))
            )

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "exclusive publication belongs to the review-repair endpoint",
    )
    def test_concurrent_actor_request_is_never_replaced(self):
        with self.repo() as root:
            real_publish = FILER._publish_exclusive_file
            actor_bytes = b"actor-owned request\n"

            def create_actor_request(source, destination):
                if destination.parent.name == "requests":
                    destination.write_bytes(actor_bytes)
                return real_publish(source, destination)

            with mock.patch.object(
                FILER,
                "_publish_exclusive_file",
                side_effect=create_actor_request,
            ):
                result, _ = self.file(root)

            self.assertEqual("conflict", result.disposition)
            self.assertTrue(result.mutated)
            requests = list(
                (root / "message-queue/needs-agent/requests").glob("*.md")
            )
            self.assertEqual(1, len(requests))
            self.assertEqual(actor_bytes, requests[0].read_bytes())
            self.assertEqual(1, len(list((root / "tasks/0_backlog").glob("*"))))

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "no-delete publication belongs to the review-repair endpoint",
    )
    def test_rollback_preserves_actor_file_added_to_owned_task_directory(self):
        with self.repo() as root:
            real_publish = FILER._publish_exclusive_file
            actor_name = "actor-note.txt"

            def add_actor_file_then_fail(source, destination):
                if destination.parent.name == "requests":
                    task_directories = list((root / "tasks/0_backlog").glob("*"))
                    self.assertEqual(1, len(task_directories))
                    (task_directories[0] / actor_name).write_text("preserve me\n")
                    raise OSError("simulated request race")
                return real_publish(source, destination)

            with mock.patch.object(
                FILER,
                "_publish_exclusive_file",
                side_effect=add_actor_file_then_fail,
            ):
                result, _ = self.file(root)

            self.assertEqual("error", result.disposition)
            self.assertTrue(result.mutated)
            task_directories = list((root / "tasks/0_backlog").glob("*"))
            self.assertEqual(1, len(task_directories))
            self.assertEqual("preserve me\n", (task_directories[0] / actor_name).read_text())
            self.assertTrue((task_directories[0] / "task.md").exists())
            self.assertTrue((task_directories[0] / FILER.JOURNAL_NAME).exists())

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "no-delete publication belongs to the review-repair endpoint",
    )
    def test_actor_replacement_after_publish_survives_later_failure(self):
        with self.repo() as root:
            real_publish = FILER._publish_exclusive_file
            actor_bytes = b"actor replacement\n"
            calls = 0

            def replace_then_fail(source, destination):
                nonlocal calls
                calls += 1
                if calls == 1:
                    real_publish(source, destination)
                    destination.unlink()
                    destination.write_bytes(actor_bytes)
                    return
                if calls == 3:
                    raise OSError("simulated request failure")
                return real_publish(source, destination)

            with mock.patch.object(
                FILER, "_publish_exclusive_file", side_effect=replace_then_fail
            ):
                result, _ = self.file(root)

            self.assertEqual("error", result.disposition)
            self.assertTrue(result.mutated)
            task_directories = list((root / "tasks/0_backlog").glob("*"))
            self.assertEqual(1, len(task_directories))
            self.assertEqual(actor_bytes, (task_directories[0] / "task.md").read_bytes())

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "exclusive fallback belongs to the review-repair endpoint",
    )
    def test_exclusive_fallback_failure_never_unlinks_partial_destination(self):
        with self.repo() as root:
            source = root / "source.txt"
            destination = root / "destination.txt"
            source.write_text("complete source\n")
            with mock.patch.object(
                FILER.os, "link", side_effect=OSError(errno.EPERM, "unsupported")
            ), mock.patch.object(
                FILER.os, "write", side_effect=OSError("simulated write failure")
            ):
                with self.assertRaises(FILER._PublicationFailure) as raised:
                    FILER._publish_exclusive_file(source, destination)
            self.assertTrue(raised.exception.mutated)
            self.assertTrue(destination.exists())

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "reciprocal request validation belongs to the review-repair endpoint",
    )
    def test_orphan_backlog_task_conflicts_instead_of_appending(self):
        with self.repo() as root:
            real_publish = FILER._publish_exclusive_file
            calls = 0

            def fail_request(source, destination):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("simulated request failure")
                return real_publish(source, destination)

            with mock.patch.object(
                FILER, "_publish_exclusive_file", side_effect=fail_request
            ):
                first, _ = self.file(root)
            self.assertEqual("error", first.disposition)
            task = next((root / "tasks/0_backlog").iterdir())
            journal = task / FILER.JOURNAL_NAME
            before = journal.read_bytes()

            second, _ = self.file(root, self.occurrence(receipt="b" * 64))
            self.assertEqual("conflict", second.disposition)
            self.assertFalse(second.mutated)
            self.assertEqual(before, journal.read_bytes())

    def test_generated_records_pass_current_task_and_queue_reconciler_checks(self):
        with self.repo() as root:
            (root / "tasks/AGENTS.md").parent.mkdir(parents=True, exist_ok=True)
            (root / "tasks/AGENTS.md").write_text(
                "**Task admission schema:** v1\n", encoding="utf-8"
            )
            (root / "message-queue/AGENTS.md").parent.mkdir(parents=True, exist_ok=True)
            (root / "message-queue/AGENTS.md").write_text(
                "**Queue resolution schema:** v1\n", encoding="utf-8"
            )
            result, _ = self.file(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            replacements = {
                "REPO": root,
                "QUEUE": root / "message-queue",
                "RETRIES": root / "message-queue/needs-agent/retries",
                "TASKS": root / "tasks",
                "CONVERSATIONS": root / "history/conversations",
                "MEMORY": root / "memory",
                "ACTIVE_TASK_ID": None,
                "ACTIVE_TRANSITIONS": set(),
                "CHANGE_RANGE": None,
                "DISPLACED_TIP": None,
            }
            with mock.patch.multiple(RECONCILE, **replacements):
                findings = []
                for check in (
                    RECONCILE.check_queue_name,
                    RECONCILE.check_queue_schema,
                    RECONCILE.check_queue_task_reciprocity,
                    RECONCILE.check_task_structure,
                ):
                    findings.extend(check())
            self.assertEqual(
                [],
                [f"[{finding.check}] {finding.subject}: {finding.message}" for finding in findings],
            )
            self.assertTrue(self.task_file(root, result).exists())

    def test_cli_always_exits_zero_and_emits_result_json(self):
        with self.repo() as root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = FILER.main(
                    ["--repo", str(root), "--occurrence-json", json.dumps(self.occurrence())]
                )
            self.assertEqual(0, exit_code)
            result = json.loads(stdout.getvalue())
            self.assertEqual("created", result["disposition"])
            self.assertTrue(result["mutated"])


if __name__ == "__main__":
    unittest.main()
