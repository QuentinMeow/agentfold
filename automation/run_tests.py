#!/usr/bin/env python3
"""Run every service test: services/*/tests/test_*.py, each in its own process.

Subprocess-per-file keeps hyphenated service folders importable-free and any
test crash isolated. Exit 0 only if every file passes.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main():
    test_files = sorted((REPO / "services").glob("*/tests/test_*.py"))
    if not test_files:
        print("no service tests found")
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
