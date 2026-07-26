"""Unit tests for the co-change mining CLI.

Every fixture is a real repository in a temporary directory, because the tool's whole
input is Git history. Kept out of test_reconcile_queue.py, which alone is roughly half
of the suite's runtime.
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "mine_cochange.py"
SPEC = importlib.util.spec_from_file_location("mine_cochange", MODULE_PATH)
MINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MINE)

LOG_ARGS = ("log", "--root", "-z", "--name-status", "--format=%x00%H%x00%s")


class MineCochangeTests(unittest.TestCase):
    @staticmethod
    def git(root, *args):
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.strip()

    @contextlib.contextmanager
    def repo(self):
        """A repository with a sanitized identity, no signing, and no inherited hooks."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git(root, "init", "-q")
            self.git(root, "config", "user.name", "Test")
            self.git(root, "config", "user.email", "test@example.invalid")
            self.git(root, "config", "commit.gpgsign", "false")
            self.git(root, "config", "core.hooksPath", str(root / ".git" / "no-hooks"))
            yield root

    def commit(self, root, subject, files):
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-qm", subject)

    def couple(self, root, first, second, times=3, start=1, extra=None):
        """Commit `first` and `second` together `times` times.

        Every payload body carries the index, so each file really changes in each
        commit; identical content would be no change at all to Git.
        """
        for index in range(start, start + times):
            payload = {first: f"a{index}\n", second: f"b{index}\n"}
            payload.update({name: f"{body}{index}\n"
                            for name, body in (extra or {}).items()})
            self.commit(root, f"pair {index}", payload)

    def mine(self, root, **kwargs):
        return MINE.mine(repo=root, **kwargs)

    @staticmethod
    def directed(result):
        return {(c["source"], c["target"]) for c in result["candidates"]}

    def walk(self, root):
        return list(MINE.walk_commits(MINE.git(*LOG_ARGS, repo=root)))

    @contextlib.contextmanager
    def cli(self, root):
        """Point the module's repository and ledger at the fixture; capture each run."""
        ledger = root / "automation" / "cochange-ledger.txt"

        def run(*argv):
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(MINE, "REPO", root), \
                    mock.patch.object(MINE, "LEDGER", ledger), \
                    contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = MINE.main(list(argv))
            return code, out.getvalue()

        yield run, ledger

    # --- mining ---------------------------------------------------------------

    def test_support_floor_needs_three_shared_commits(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=2)
            self.assertEqual(set(), self.directed(self.mine(root)))
            self.couple(root, "one/a.md", "two/b.md", times=1, start=3)
            self.assertEqual(
                {("one/a.md", "two/b.md"), ("two/b.md", "one/a.md")},
                self.directed(self.mine(root)),
            )
            self.assertEqual(
                set(), self.directed(self.mine(root, support_floor=4))
            )

    def test_confidence_is_asymmetric_and_floored(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=4)
            # a.md changes alone often enough that P(b|a) falls under the floor while
            # P(a|b) stays at 1.0. That asymmetry is the mined edge's direction.
            for index in range(4):
                self.commit(root, f"solo {index}", {"one/a.md": f"solo{index}\n"})
            result = self.mine(root)
            self.assertEqual({("two/b.md", "one/a.md")}, self.directed(result))
            [candidate] = result["candidates"]
            self.assertEqual(1.0, candidate["confidence"])
            self.assertEqual(4, candidate["support"])
            self.assertEqual(4, candidate["source_commits"])
            loose = self.mine(root, confidence_floor=0.5)
            self.assertEqual(
                {("one/a.md", "two/b.md"), ("two/b.md", "one/a.md")},
                self.directed(loose),
            )
            reverse = [c for c in loose["candidates"] if c["source"] == "one/a.md"][0]
            self.assertEqual(0.5, reverse["confidence"])
            self.assertEqual(8, reverse["source_commits"])

    def test_commit_size_cap_skips_tangled_commits(self):
        with self.repo() as root:
            for index in range(3):
                payload = {f"noise/n{n}.md": f"{index}\n" for n in range(5)}
                payload["one/a.md"] = f"a{index}\n"
                payload["two/b.md"] = f"b{index}\n"
                self.commit(root, f"tangled {index}", payload)
            capped = self.mine(root, commit_cap=4)
            self.assertEqual(set(), self.directed(capped))
            self.assertEqual(3, capped["tangled"])
            self.assertEqual(0, capped["scoped"])
            wide = self.mine(root, commit_cap=40)
            self.assertIn(("one/a.md", "two/b.md"), self.directed(wide))
            self.assertEqual(0, wide["tangled"])

    def test_stop_list_removes_mandated_coupling(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=3,
                        extra={"roadmap/current-state.md": "ritual\n"})
            self.commit(root, "bump", {"roadmap/current-state.md": "again\n"})
            self.assertEqual(
                {("one/a.md", "two/b.md"), ("two/b.md", "one/a.md")},
                self.directed(self.mine(root)),
            )
            without = self.directed(self.mine(root, stop_list=()))
            self.assertIn(("one/a.md", "roadmap/current-state.md"), without)

    def test_worklog_and_generated_index_are_stopped_by_default(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=3, extra={
                "tasks/1_in-progress/2026-07-25-x/worklog.md": "log\n",
                "memory/index.md": "index\n",
            })
            for name in ("tasks/1_in-progress/2026-07-25-x/worklog.md",
                         "memory/index.md", "roadmap/current-state.md"):
                self.assertTrue(MINE.stopped(name, MINE.STOP_LIST), name)
            self.assertFalse(MINE.stopped("memory/facts/x.md", MINE.STOP_LIST))
            reported = {name for pair in self.directed(self.mine(root))
                        for name in pair}
            self.assertEqual({"one/a.md", "two/b.md"}, reported)

    def test_same_directory_pairs_are_suppressed(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "one/b.md", times=4)
            self.assertEqual(set(), self.directed(self.mine(root)))
        self.assertTrue(MINE.same_directory("one/a.md", "one/b.md"))
        self.assertFalse(MINE.same_directory("one/a.md", "one/two/b.md"))
        self.assertTrue(MINE.same_directory("a.md", "b.md"))

    def test_scope_excludes_records_schemas_and_non_markdown(self):
        excluded = ("history/session/handover.md",
                    "memory/decisions/2026-07-25-x.md", "tmp/scratch.md",
                    "message-queue/needs-agent/retries/r.md", ".github/notes.md",
                    "one/code.py")
        with self.repo() as root:
            for offset, name in enumerate(excluded):
                self.assertFalse(MINE.in_scope(name, MINE.SCOPE_EXCLUDES), name)
                self.couple(root, "one/a.md", "two/b.md", times=3, start=offset * 10,
                            extra={name: "x\n"})
                self.commit(root, f"solo {offset}", {name: "y\n"})
            reported = {name for pair in self.directed(self.mine(root))
                        for name in pair}
            self.assertEqual({"one/a.md", "two/b.md"}, reported)
        self.assertTrue(MINE.in_scope("templates/task/task.md", ()))
        # Templates stay in scope by default: a template that restates a contract it
        # never names is the case mining exists to find.
        self.assertTrue(MINE.in_scope("templates/queue/review.md",
                                      MINE.SCOPE_EXCLUDES))
        self.assertTrue(MINE.in_scope("handbook/git-workflow.md",
                                      MINE.SCOPE_EXCLUDES))

    def test_rename_records_are_parsed_and_both_names_counted(self):
        with self.repo() as root:
            self.commit(root, "seed", {"one/a.md": "a\n" * 20, "two/b.md": "b\n"})
            (root / "three").mkdir()
            self.git(root, "mv", "one/a.md", "three/moved.md")
            self.commit(root, "rename", {"two/b.md": "b2\n"})
            log = MINE.git(*LOG_ARGS, repo=root)
            self.assertRegex(log, r"R\d*\x00one/a\.md\x00three/moved\.md")
            renamed = [paths for subject, paths in self.walk(root)
                       if subject == "rename"][0]
            self.assertEqual(["one/a.md", "three/moved.md", "two/b.md"],
                             sorted(renamed))

    def test_root_commit_is_visible(self):
        with self.repo() as root:
            self.commit(root, "root", {"one/a.md": "a\n", "two/b.md": "b\n"})
            self.assertEqual([("root", ["one/a.md", "two/b.md"])],
                             [(s, sorted(p)) for s, p in self.walk(root)])
            self.couple(root, "one/a.md", "two/b.md", times=2, start=2)
            # Support reaches 3 only if the root commit's files were visible.
            result = self.mine(root)
            self.assertIn(("one/a.md", "two/b.md"), self.directed(result))
            self.assertEqual(3, result["candidates"][0]["support"])

    def test_pairs_naming_untracked_paths_are_dropped(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/gone.md", times=3)
            self.commit(root, "keep", {"one/a.md": "kept\n"})
            self.git(root, "rm", "-q", "two/gone.md")
            self.git(root, "commit", "-qm", "delete the partner")
            result = self.mine(root)
            self.assertEqual(set(), self.directed(result))
            self.assertEqual(1, result["stale"])

    def test_report_is_byte_identical_across_runs(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=3)
            self.couple(root, "one/a.md", "three/c.md", times=3, start=10)
            with self.cli(root) as (run, _):
                first_code, first = run("report")
                second_code, second = run("report")
            self.assertEqual((0, 0), (first_code, second_code))
            self.assertEqual(first, second)
            self.assertIn("also review", first)

    # --- report surface -------------------------------------------------------

    def test_report_always_exits_zero_and_states_its_cap(self):
        with self.repo() as root:
            for index in range(6):
                self.couple(root, "one/a.md", f"two/b{index}.md", times=3,
                            start=index * 10)
            with self.cli(root) as (run, _):
                code, output = run("report", "--limit", "2")
                self.assertEqual(0, code)
                json_code, payload_text = run("report", "--limit", "0", "--json")
            self.assertIn("2 shown", output)
            self.assertIn("dropped by the ranking above", output)
            self.assertIn("see them all: --limit 0", output)
            self.assertIn("provisional", output)
            self.assertEqual(0, json_code)
            payload = json.loads(payload_text)
            self.assertEqual(payload["total"], len(payload["shown"]))
            self.assertTrue(payload["total"] > 2)
            self.assertTrue(payload["provisional"])
            self.assertEqual(MINE.RANKING, payload["ranking"])

    def test_evidence_is_shared_commit_subjects_and_capped(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=5)
            with self.cli(root) as (run, _):
                _, output = run("report", "--evidence", "2")
            # Newest shared commit first, then the cap and an honest remainder.
            self.assertIn("because  pair 5", output)
            self.assertIn("pair 4", output)
            self.assertIn("+3 more shared commit(s)", output)
            self.assertNotIn("pair 2", output)

    def test_ranking_is_confidence_then_support_then_paths(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=5)
            self.couple(root, "one/a.md", "two/a.md", times=5, start=10)
            self.couple(root, "zz/high.md", "yy/high.md", times=3, start=20)
            self.commit(root, "solo", {"zz/high.md": "z\n"})
            ranked = [(c["confidence"], c["support"], c["source"], c["target"])
                      for c in self.mine(root)["candidates"]]
            self.assertEqual(
                sorted(ranked, key=lambda row: (-row[0], -row[1], row[2], row[3])),
                ranked,
            )
            self.assertEqual(3, len(ranked))

    def test_report_says_so_when_nothing_clears_the_floors(self):
        with self.repo() as root:
            self.commit(root, "only", {"one/a.md": "a\n"})
            with self.cli(root) as (run, _):
                code, output = run("report")
            self.assertEqual(0, code)
            self.assertIn("no pair clears both floors", output)

    def test_unborn_head_and_empty_repository_no_op(self):
        with self.repo() as root:
            result = self.mine(root)
            self.assertFalse(result["available"])
            self.assertEqual([], result["candidates"])
            with self.cli(root) as (run, _):
                code, output = run("report")
                self.assertEqual(0, code)
                self.assertIn("no history to mine", output)
                json_code, payload_text = run("report", "--json")
            self.assertEqual(0, json_code)
            self.assertFalse(json.loads(payload_text)["available"])
            (root / "one").mkdir()
            (root / "one" / "a.md").write_text("a\n", encoding="utf-8")
            self.assertFalse(self.mine(root)["available"])

    # --- ledger ---------------------------------------------------------------

    def test_ledger_line_is_parsed_by_the_documented_regex(self):
        line = "2026-07-25\treject\tone/a.md\ttwo/b.md\tsame release ritual"
        matched = MINE.LEDGER_RE.match(line)
        self.assertEqual(
            ("2026-07-25", "reject", "one/a.md", "two/b.md", "same release ritual"),
            matched.groups()[:5],
        )
        self.assertIsNone(matched.group(6))
        future = MINE.LEDGER_RE.match(line + "\tagent=example\tmore=1")
        self.assertEqual("agent=example\tmore=1", future.group(6))
        self.assertEqual("reject", future.group(2))
        self.assertIsNone(MINE.LEDGER_RE.match("2026-07-25 reject one/a.md two/b.md x"))
        self.assertIsNone(MINE.LEDGER_RE.match("2026-07-25\tmaybe\ta.md\tb.md\t"))

    def test_rejected_pair_never_resurfaces_and_direction_is_explicit(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=3)
            with self.cli(root) as (run, ledger):
                code, output = run("reject", "one/a.md", "two/b.md",
                                   "--reason", "release ritual", "--date", "2026-07-25")
                self.assertEqual(0, code)
                self.assertIn("recorded reject", output)
                _, payload_text = run("report", "--json")
            payload = json.loads(payload_text)
            self.assertEqual([("two/b.md", "one/a.md")],
                             [(c["source"], c["target"]) for c in payload["shown"]])
            self.assertEqual(1, payload["suppressed"])
            self.assertTrue(ledger.read_text(encoding="utf-8").endswith(
                "2026-07-25\treject\tone/a.md\ttwo/b.md\trelease ritual\n"))

    def test_accepted_pair_also_leaves_the_candidate_queue(self):
        with self.repo() as root:
            self.couple(root, "one/a.md", "two/b.md", times=3)
            with self.cli(root) as (run, _):
                self.assertEqual(0, run("accept", "one/a.md", "two/b.md",
                                        "--date", "2026-07-25")[0])
                self.assertEqual(0, run("accept", "two/b.md", "one/a.md",
                                        "--date", "2026-07-25")[0])
                _, payload_text = run("report", "--json")
            payload = json.loads(payload_text)
            self.assertEqual([], payload["shown"])
            self.assertEqual(2, payload["suppressed"])

    def test_ledger_is_append_only_and_refuses_a_second_verdict(self):
        with self.repo() as root:
            self.commit(root, "seed", {"one/a.md": "a\n"})
            with self.cli(root) as (run, ledger):
                self.assertEqual(0, run("accept", "one/a.md", "two/b.md",
                                        "--date", "2026-07-25")[0])
                code, output = run("reject", "one/a.md", "two/b.md",
                                   "--reason", "changed my mind", "--date", "2026-07-26")
                self.assertEqual(2, code)
                self.assertIn("already recorded as accept", output)
                self.assertEqual(0, run("reject", "two/b.md", "one/a.md",
                                        "--reason", "other direction",
                                        "--date", "2026-07-26")[0])
            verdicts, malformed = MINE.load_ledger(ledger)
            self.assertEqual([], malformed)
            self.assertEqual(
                [("accept", "one/a.md", "two/b.md", "2026-07-25", ""),
                 ("reject", "two/b.md", "one/a.md", "2026-07-26", "other direction")],
                verdicts,
            )
            self.assertTrue(ledger.read_text(encoding="utf-8").startswith("# "))

    def test_verdict_usage_refusals_exit_two(self):
        with self.repo() as root:
            with self.cli(root) as (run, ledger):
                code, output = run("reject", "one/a.md", "two/b.md")
                self.assertEqual(2, code)
                self.assertIn("--reason is required", output)
                self.assertEqual(2, run("accept", "one/a.md", "one/a.md")[0])
                self.assertEqual(2, run("accept", "one/a.md", "two\tb.md")[0])
                self.assertFalse(ledger.exists())
                for argv in (["report", "--support", "not-a-number"], [], ["nonsense"],
                             ["accept", "a.md", "b.md", "--date", "yesterday"]):
                    with self.assertRaises(SystemExit) as raised:
                        run(*argv)
                    self.assertEqual(2, raised.exception.code, argv)
                self.assertFalse(ledger.exists())

    def test_multi_line_reason_is_collapsed_to_one_line(self):
        with self.repo() as root:
            with self.cli(root) as (run, ledger):
                self.assertEqual(0, run("reject", "one/a.md", "two/b.md",
                                        "--date", "2026-07-25",
                                        "--reason", "first\tline\nsecond  line")[0])
            self.assertEqual(
                ["2026-07-25\treject\tone/a.md\ttwo/b.md\tfirst line second line"],
                [line for line in ledger.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.startswith("#")],
            )

    def test_shipped_ledger_documents_its_format_and_parses_every_verdict(self):
        # Asserting the shipped ledger is *empty* would forbid ever using the feature:
        # the verbs write only to this tracked file and expose no path override, so the
        # first real verdict would fail the suite and block every later commit. What has
        # to hold for any ledger state is that every verdict line parses.
        shipped = MODULE_PATH.parent / "cochange-ledger.txt"
        verdicts, malformed = MINE.load_ledger(shipped)
        self.assertEqual([], malformed)
        for verdict, source, target, when, reason in verdicts:
            self.assertIn(verdict, ("accept", "reject"))
            self.assertRegex(when, r"^\d{4}-\d{2}-\d{2}$")
            for field in (source, target, reason):
                self.assertNotIn("\t", field)
            self.assertNotEqual(source, target)
            if verdict == "reject":
                self.assertTrue(reason.strip(), (source, target))
        text = shipped.read_text(encoding="utf-8")
        self.assertIn("append-only", text)
        self.assertIn(MINE.LEDGER_RE.pattern, text)

    # --- governance -----------------------------------------------------------

    def test_rejection_rate_arithmetic_and_three_states(self):
        accept = ("accept", "a.md", "b.md", "2026-07-25", "")
        reject = ("reject", "a.md", "b.md", "2026-07-25", "why")
        self.assertEqual((0, 0, None, "unmeasured"), MINE.governance([]))
        self.assertEqual((10, 0, 0.0, "on-target"), MINE.governance([accept] * 10))
        self.assertEqual("on-target", MINE.governance([accept] * 19 + [reject])[3])
        self.assertEqual((10, 1, 0.1, "probation"),
                         MINE.governance([accept] * 9 + [reject]))
        self.assertEqual("probation", MINE.governance([accept] * 3 + [reject])[3])
        self.assertEqual("off", MINE.governance([accept] * 2 + [reject])[3])
        self.assertEqual((4, 3, 0.75, "off"), MINE.governance([accept] + [reject] * 3))
        self.assertEqual("off", MINE.governance([reject])[3])

    def test_status_verb_exit_codes_follow_the_thresholds(self):
        with self.repo() as root:
            with self.cli(root) as (run, ledger):
                code, output = run("status")
                self.assertEqual(0, code)
                self.assertIn("unmeasured", output)
                self.assertIn("n/a", output)
                for index in range(9):
                    run("accept", f"a{index}.md", "b.md", "--date", "2026-07-25")
                self.assertEqual(0, run("status")[0])
                self.assertIn("on-target", run("status")[1])
                run("reject", "r.md", "b.md", "--reason", "no", "--date", "2026-07-25")
                code, output = run("status")
                self.assertEqual(1, code)
                self.assertIn("probation", output)
                self.assertIn("10.0%", output)
                for index in range(3):
                    run("reject", f"r{index}.md", "b.md", "--reason", "no",
                        "--date", "2026-07-25")
                code, payload_text = run("status", "--json")
            self.assertEqual(1, code)
            payload = json.loads(payload_text)
            self.assertEqual("off", payload["governance"])
            self.assertEqual(13, payload["verdicts"])
            self.assertEqual(4, payload["rejected"])
            self.assertEqual(9, payload["accepted"])
            self.assertEqual(0.3077, payload["effective_false_positive_rate"])
            self.assertEqual(4, len(
                [line for line in ledger.read_text(encoding="utf-8").splitlines()
                 if line.startswith("2026-07-25\treject")]))

    def test_status_reports_malformed_lines(self):
        with self.repo() as root:
            with self.cli(root) as (run, ledger):
                run("accept", "a.md", "b.md", "--date", "2026-07-25")
                with open(ledger, "a", encoding="utf-8") as handle:
                    handle.write("garbage line\n")
                code, output = run("status")
            self.assertEqual(0, code)
            self.assertIn("malformed   1 unparseable", output)

    # --- house rules ----------------------------------------------------------

    def test_help_shows_the_stop_list_and_the_provisional_caveat(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), self.assertRaises(SystemExit):
            MINE.main(["report", "--help"])
        text = buffer.getvalue()
        for pattern in MINE.STOP_LIST:
            self.assertIn(pattern, text)
        self.assertIn("provisional", text)

    def test_tool_keeps_state_repository_local(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        for marker in ("expanduser", "USERPROFILE", "$HOME", "~/."):
            self.assertNotIn(marker, source)
        self.assertIn('LEDGER = REPO / "automation" / "cochange-ledger.txt"', source)


if __name__ == "__main__":
    unittest.main()
