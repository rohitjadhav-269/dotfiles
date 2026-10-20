"""Missing resources and engines must fail instead of a lock-only clean bill."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import subprocess
import shutil
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("installation", ROOT / "scripts/check-skill-installation.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class SkillInstallationTests(unittest.TestCase):
    def test_required_resource_missing_and_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents/skills/example").mkdir(parents=True)
            (root / "agents/skills/example/SKILL.md").write_text("example")
            (root / "agents/.skill-lock.json").write_text(json.dumps({"skills": {"example": {}}}))
            (root / "config").mkdir()
            (root / "config/skill-install-resources.json").write_text(json.dumps({"resources": [{"path": "agents/CONNECTORS.md", "sha256": hashlib.sha256(b"expected").hexdigest()}]}))
            self.assertIn("missing", CHECK.check_resources(root)[0])
            resource = root / "agents/CONNECTORS.md"
            resource.write_text("wrong")
            self.assertIn("checksum", CHECK.check_resources(root)[0])
            resource.write_text("expected")
            self.assertEqual([], CHECK.check_resources(root))

    @unittest.skipIf(os.name == "nt", "shell fixture exercises the Mac/Linux binary cache")
    def test_engine_missing_wrong_version_and_ready(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            scripts = root / "agents/skills/impeccable/scripts"
            scripts.mkdir(parents=True)
            (scripts / "VERSION").write_text("1.2.3")
            cache = root / "cache"
            self.assertIn("missing", CHECK.check_engine(root, cache)[0])
            binary = cache / "bin/1.2.3/impeccable"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\necho impeccable-engine 1.2.2\n")
            binary.chmod(0o755)
            self.assertIn("mismatch", CHECK.check_engine(root, cache)[0])
            binary.write_text("#!/bin/sh\necho impeccable-engine 1.2.3\n")
            self.assertEqual([], CHECK.check_engine(root, cache))

    def test_fluid_dependency_is_not_inferred_from_the_skill_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIn("missing", CHECK.check_browser_dependency(root)[0])
            dependency = root / "agents/skills/fluid-functionalism/scripts/node_modules/playwright-core/package.json"
            dependency.parent.mkdir(parents=True)
            dependency.write_text('{"name":"playwright-core"}')
            self.assertEqual([], CHECK.check_browser_dependency(root))

    def test_screenshot_helpers_resolve_the_projects_playwright(self):
        node = Path.home() / ".local/bin/node-stable"
        if not node.exists():
            found = shutil.which("node")
            if not found:
                self.skipTest("Node is unavailable")
            node = Path(found)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            package = project / "node_modules/playwright"
            package.mkdir(parents=True)
            # A sentinel proves the project module was reached, without a browser.
            (package / "index.js").write_text("exports.chromium = { launch() { throw new Error('PROJECT_PLAYWRIGHT_LOADED'); } };\n")
            for helper in (ROOT / "agents/skills/localhost-screenshots/assets/scripts").glob("*.js"):
                result = subprocess.run([str(node), str(helper)], cwd=project, capture_output=True, text=True, timeout=10)
                self.assertIn("PROJECT_PLAYWRIGHT_LOADED", result.stderr, helper.name)
                self.assertNotIn("Missing dependency", result.stderr, helper.name)


if __name__ == "__main__":
    unittest.main()
