#!/usr/bin/env python3
"""Regression tests for exact candidate and tested-view manifests."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


AUTOMATION = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "test_manifest_under_test", AUTOMATION / "test_manifest.py"
)
MANIFEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MANIFEST)


class TestManifestTests(unittest.TestCase):
    def test_tracked_symlink_mode_is_not_an_executable_candidate_entry(self):
        oid = b"a" * 40
        for target_kind in ("absolute", "dangling", "loop"):
            with self.subTest(target_kind=target_kind):
                encoded_index = b"120000 " + oid + b" 0\tlinked\0"
                with self.assertRaisesRegex(
                    MANIFEST.ManifestError, "unsupported index entry"
                ):
                    MANIFEST._parse_index(encoded_index)

    def test_tested_view_rejects_absolute_dangling_and_looping_symlinks(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            outside = root.parent / "outside-agentfold-manifest"
            cases = {
                "absolute": str(outside),
                "dangling": "missing-target",
                "loop": ".",
            }
            for name, target in cases.items():
                path = root / name
                try:
                    os.symlink(target, str(path))
                except (NotImplementedError, OSError):
                    self.skipTest("symlinks are unavailable")
                with self.subTest(name=name), self.assertRaisesRegex(
                    MANIFEST.ManifestError, "tested-view symlinks are unsupported"
                ):
                    MANIFEST.tree_manifest(root)
                path.unlink()

    def test_regular_files_remain_bound_by_mode_and_bytes(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            path = root / "regular.txt"
            path.write_text("candidate bytes\n", encoding="utf-8")
            value = MANIFEST.tree_manifest(root)
            self.assertEqual(["regular.txt"], value["paths"])
            self.assertEqual("file", value["records"][0]["kind"])
            self.assertEqual(MANIFEST.file_digest(path), value["records"][0]["sha256"])

    def test_directory_topology_changes_the_tested_view_digest(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            before = MANIFEST.tree_manifest(root)
            (root / "schema-leaf").mkdir()
            after = MANIFEST.tree_manifest(root)

            self.assertNotEqual(before["digest"], after["digest"])
            self.assertEqual(["schema-leaf"], after["paths"])
            self.assertEqual(
                {"path": "schema-leaf", "kind": "directory"},
                after["records"][0],
            )


if __name__ == "__main__":
    unittest.main()
