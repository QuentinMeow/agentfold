from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "codex_hook.py"
SPEC = importlib.util.spec_from_file_location("github_auth_codex_hook", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
hook = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hook
SPEC.loader.exec_module(hook)


def probe(classification="inconclusive", safe=False):
    return lambda hostname: {
        "classification": classification,
        "safe_to_recommend_login": safe,
        "next_step": "diagnostic next step",
    }


class CodexHookTests(unittest.TestCase):
    def test_pre_tool_blocks_login_when_probe_is_inconclusive(self):
        result = hook.handle(
            {
                "hook_event_name": "PreToolUse",
                "tool_input": {"command": "gh auth login --hostname github.com"},
            },
            probe=probe(),
        )
        decision = result["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("inconclusive", decision["permissionDecisionReason"])

    def test_pre_tool_allows_login_only_after_confirmed_rejection(self):
        result = hook.handle(
            {
                "hook_event_name": "PreToolUse",
                "tool_input": {"command": "/opt/homebrew/bin/gh auth login"},
            },
            probe=probe("reauth-required", True),
        )
        self.assertNotIn("permissionDecision", result["hookSpecificOutput"])

    def test_status_adds_model_visible_context(self):
        result = hook.handle(
            {
                "hook_event_name": "PostToolUse",
                "tool_input": {"cmd": "gh auth status --hostname github.com"},
            },
            probe=probe(),
        )
        self.assertIn("not proof", result["hookSpecificOutput"]["additionalContext"])

    def test_stop_blocks_positive_login_recommendation(self):
        result = hook.handle(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Please run `gh auth login` to fix this.",
            },
            probe=probe("authenticated", False),
        )
        self.assertEqual(result["decision"], "block")

    def test_stop_allows_explicit_warning_not_to_login(self):
        result = hook.handle(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Do not run `gh auth login`; the sandbox result is inconclusive.",
            },
            probe=probe(),
        )
        self.assertIsNone(result)

    def test_stop_allows_login_after_confirmed_rejection(self):
        result = hook.handle(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Please run `gh auth login` now.",
            },
            probe=probe("reauth-required", True),
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
