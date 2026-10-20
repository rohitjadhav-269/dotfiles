import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("zed_check", ROOT / "scripts/check-zed.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ZedCheckTests(unittest.TestCase):
    def test_repository_snapshots_parse(self):
        self.assertEqual(checker.check(ROOT, ROOT / "apps/zed", ROOT / "unused", True), [])

    def test_preference_audit_rejects_malformed_zed_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "apps/zed/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text('{"cursor_animation":{"enabled":true}},"theme":{}\n')
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/audit-app-prefs.sh")],
                env={**os.environ, "DOTFILES": str(root)}, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("invalid Zed JSONC", result.stdout + result.stderr)

    def test_settings_alone_do_not_prove_extension_or_theme_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            snapshot = repo / "apps/zed"
            snapshot.mkdir(parents=True)
            live = root / "live"
            live.mkdir()
            extensions = root / "extensions"
            settings = {"theme": {"dark": "Fixture Dark", "light": "One Light"},
                        "auto_install_extensions": {"fixture": True}}
            for folder in (snapshot, live):
                (folder / "settings.json").write_text(json.dumps(settings))
                (folder / "keymap.json").write_text("[]")
            self.assertEqual(checker.check(repo, live, extensions, True), [])
            self.assertEqual(len(checker.check(repo, live, extensions)), 2)
            package = extensions / "fixture"
            (package / "themes").mkdir(parents=True)
            (package / "extension.toml").write_text('id = "fixture"\n')
            self.assertEqual(checker.check(repo, live, extensions),
                             ["Missing selected theme resource: Fixture Dark"])
            (package / "themes/theme.json").write_text('{"themes":[{"name":"Fixture Dark"}]}')
            self.assertEqual(checker.check(repo, live, extensions), [])
            settings["theme"]["dark"] = "Other Theme"
            (live / "settings.json").write_text(json.dumps(settings))
            self.assertIn("Managed settings differ", checker.check(repo, live, extensions)[0])

    def test_local_agent_options_do_not_mask_managed_drift(self):
        expected = {"agent_servers": {"codex-acp": {"type": "registry"}}}
        actual = {"agent_servers": {"codex-acp": {"type": "registry", "local_option": "fixture"}}}
        self.assertTrue(checker.managed_matches(expected, actual))
        actual["agent_servers"]["codex-acp"]["type"] = "custom"
        self.assertFalse(checker.managed_matches(expected, actual))


if __name__ == "__main__":
    unittest.main()
