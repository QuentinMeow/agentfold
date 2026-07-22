#!/usr/bin/env python3
"""Run every repository test file, each in its own process.

Discovery covers services, canonical skills, and automation. Subprocess-per-file keeps
hyphenated folders importable-free and any
test crash isolated. Exit 0 only if every file passes.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEST_GLOBS = (
    "services/*/tests/test_*.py",
    "skills/*/tests/test_*.py",
    "automation/**/tests/test_*.py",
)


def main():
    test_files = sorted({test for pattern in TEST_GLOBS for test in REPO.glob(pattern)})
    if not test_files:
        print("no repository tests found")
        return 0
    failed = []
    for test in test_files:
        rel = test.relative_to(REPO)
        result = subprocess.run([sys.executable, str(test)], cwd=REPO)
        (print(f"PASS {rel}") if result.returncode == 0 else failed.append(rel))
    for rel in failed:
        print(f"FAIL {rel}")
    print(f"tests: {len(test_files) - len(failed)}/{len(test_files)} files passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
