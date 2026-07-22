from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check.py"
SPEC = importlib.util.spec_from_file_location("github_auth_check", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
auth_check = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = auth_check
SPEC.loader.exec_module(auth_check)


def completed(returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class FakeRunner:
    def __init__(self, status, api_user):
        self.results = [status, api_user]
        self.commands = []

    def __call__(self, command):
        self.commands.append(list(command))
        return self.results.pop(0)


class CheckTests(unittest.TestCase):
    def probe(self, status, api_user, environment=None, configured=True):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            if configured:
                config = home / ".config" / "gh"
                config.mkdir(parents=True)
                (config / "hosts.yml").write_text("github.com:\n    user: example\n")
            return auth_check.probe(
                runner=FakeRunner(status, api_user),
                environment=environment or {},
                home=home,
            )

    def test_api_success_is_authoritative_even_when_status_fails(self):
        result = self.probe(
            completed(1, stderr="token invalid"),
            completed(0, stdout="QuentinMeow\n"),
        )
        self.assertEqual(result["classification"], "authenticated")
        self.assertEqual(result["login"], "QuentinMeow")
        self.assertFalse(result["safe_to_recommend_login"])

    def test_network_or_keychain_failure_is_inconclusive(self):
        result = self.probe(
            completed(1, stderr="The token is invalid"),
            completed(1, stderr="error connecting to api.github.com"),
        )
        self.assertEqual(result["classification"], "inconclusive")
        self.assertFalse(result["safe_to_recommend_login"])

    def test_http_401_without_override_requires_reauth(self):
        result = self.probe(
            completed(1, stderr="authentication failed"),
            completed(1, stderr="gh: Bad credentials (HTTP 401)"),
        )
        self.assertEqual(result["classification"], "reauth-required")
        self.assertTrue(result["safe_to_recommend_login"])

    def test_invalid_environment_override_is_not_fixed_by_login(self):
        result = self.probe(
            completed(1, stderr="token invalid"),
            completed(1, stderr="gh: Bad credentials (HTTP 401)"),
            environment={"GH_TOKEN": "never-printed"},
        )
        self.assertEqual(result["classification"], "invalid-environment-token")
        self.assertEqual(result["credential_source"], "GH_TOKEN")
        self.assertNotIn("never-printed", str(result))
        self.assertFalse(result["safe_to_recommend_login"])

    def test_http_403_routes_to_permissions_not_login(self):
        result = self.probe(
            completed(1),
            completed(1, stderr="gh: Resource not accessible (HTTP 403)"),
        )
        self.assertEqual(result["classification"], "permission-or-sso")
        self.assertFalse(result["safe_to_recommend_login"])

    def test_enterprise_environment_override_is_classified_without_value(self):
        result = auth_check.classify(
            "github.enterprise.example",
            completed(1),
            completed(1, stderr="gh: Bad credentials (HTTP 401)"),
            {"GH_ENTERPRISE_TOKEN": "never-printed"},
            True,
        )
        self.assertEqual(result["classification"], "invalid-environment-token")
        self.assertEqual(result["credential_source"], "GH_ENTERPRISE_TOKEN")
        self.assertNotIn("never-printed", str(result))

    def test_missing_configuration_can_require_first_login(self):
        result = self.probe(
            completed(1, stderr="You are not logged into any GitHub hosts"),
            completed(1, stderr="To get started with GitHub CLI"),
            configured=False,
        )
        self.assertEqual(result["classification"], "reauth-required")
        self.assertTrue(result["safe_to_recommend_login"])


if __name__ == "__main__":
    unittest.main()
