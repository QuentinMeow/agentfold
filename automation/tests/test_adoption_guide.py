import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class AdoptionGuideTests(unittest.TestCase):
    def test_new_project_owns_its_baseline_before_hook_installation(self):
        guide = (REPO / "handbook/adoption-guide.md").read_text(encoding="utf-8")
        section = guide.split("## Starting a new project", 1)[1].split(
            "## Retrofitting an existing repo", 1
        )[0]

        ordered = (
            "without its `.git/` directory",
            "Configure the routine and final lanes in `agentfold.toml`",
            "`git init`",
            "first commit",
            "`python3 automation/reconcile/reconcile.py --check`",
            "`python3 automation/install.py`",
        )
        positions = tuple(section.index(marker) for marker in ordered)
        self.assertEqual(tuple(sorted(positions)), positions)
        self.assertIn("byte-exact migration fixtures", section)
        self.assertIn("base-pinned final tests never inherit", section)
        self.assertIn("no commit needs to bypass an installed hook", section)
        self.assertNotIn("--no-verify", section)


if __name__ == "__main__":
    unittest.main()
