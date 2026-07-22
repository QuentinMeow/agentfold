from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_codex.py"


class InstallCodexTests(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            (home / "AGENTS.md").write_text("# Existing global guidance\n\nKeep this.\n")
            (home / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "UserPromptSubmit": [
                                {"hooks": [{"type": "command", "command": "existing-hook"}]}
                            ]
                        }
                    }
                )
            )
            manager = home / "skills" / "global-github-manager"
            (manager / "references").mkdir(parents=True)
            (manager / "scripts").mkdir()
            (manager / "SKILL.md").write_text(
                "# GitHub Manager\n\n| `gh` | Always — install and `gh auth login` **inside Cursor's terminal** if agents lack auth |\n"
            )
            (manager / "references" / "gh-identity.md").write_text(
                "# Identity\n\n## One-Time Bootstrap\n\nOld advice.\n"
            )
            (manager / "references" / "pr-workflows-comprehensive.md").write_text(
                "#### Cursor IDE setup\n\nOld login-first advice.\n\n#### SSH certificate auth\n\nKeep this.\n"
            )
            (manager / "scripts" / "gh_identity.py").write_text(
                'hint = "Could not determine the active gh login. Run `gh auth login` first if needed.",\n'
                'other = "If that account is not logged in yet, run `gh auth login` in Cursor first.",\n'
            )
            plugin_skill = home / "plugins" / "cache" / "github" / "skills" / "yeet" / "SKILL.md"
            plugin_skill.parent.mkdir(parents=True)
            plugin_skill.write_text(
                "- Require authenticated `gh` session. Run `gh auth status`. If not authenticated, ask the user to run `gh auth login` (and re-run `gh auth status`) before continuing.\n"
            )

            command = [sys.executable, str(SCRIPT), "--codex-home", str(home)]
            first = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            snapshot = {
                path.relative_to(home): path.read_bytes()
                for path in home.rglob("*")
                if path.is_file()
            }
            second = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(
                snapshot,
                {
                    path.relative_to(home): path.read_bytes()
                    for path in home.rglob("*")
                    if path.is_file()
                },
            )

            agents = (home / "AGENTS.md").read_text()
            self.assertIn("Keep this.", agents)
            self.assertEqual(agents.count("github-auth-guard:start"), 1)
            hooks = json.loads((home / "hooks.json").read_text())["hooks"]
            self.assertIn("UserPromptSubmit", hooks)
            self.assertEqual(len(hooks["PreToolUse"]), 1)
            self.assertEqual(len(hooks["PostToolUse"]), 1)
            self.assertEqual(len(hooks["Stop"]), 1)
            rules = (home / "rules" / "github-auth-guard.rules").read_text()
            self.assertIn('"/usr/local/bin/gh", "/opt/homebrew/bin/gh"', rules)
            self.assertIn('decision = "forbidden"', rules)
            skill = (manager / "SKILL.md").read_text()
            self.assertIn("Authentication evidence gate", skill)
            self.assertNotIn("if agents lack auth", skill)
            identity_script = (manager / "scripts" / "gh_identity.py").read_text()
            self.assertNotIn("Run `gh auth login` first", identity_script)
            identity_doc = (manager / "references" / "gh-identity.md").read_text()
            self.assertNotIn("\ngh auth login\n", identity_doc)
            self.assertNotIn("ask the user to run `gh auth login`", plugin_skill.read_text())


if __name__ == "__main__":
    unittest.main()
