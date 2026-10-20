"""Public-owned checkout-safe fixtures; never import live preferences."""
from pathlib import Path
import os
import shutil
import plistlib
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]

class PublicBootstrap(unittest.TestCase):
    def test_dock_fallback_matches_its_public_snapshot(self):
        fallback = []
        for line in (ROOT / 'macos/dock-dev.sh').read_text().splitlines():
            declaration = line.strip()
            if declaration.startswith('add_app "') and declaration.endswith('"'):
                fallback.append(('file-tile', Path(declaration[len('add_app "'):-1]).stem))
            elif declaration == 'add_spacer':
                fallback.append(('spacer-tile', None))
            elif declaration == 'add_small_spacer':
                fallback.append(('small-spacer-tile', None))
        snapshot = plistlib.loads((ROOT / 'macos/dock-backup.plist').read_bytes())
        captured = []
        for tile in snapshot['persistent-apps']:
            app = None
            if tile['tile-type'] == 'file-tile':
                url = tile['tile-data']['file-data']['_CFURLString']
                app = Path(unquote(urlparse(url).path)).stem
            captured.append((tile['tile-type'], app))
        self.assertEqual(fallback, captured)

    @unittest.skipUnless(shutil.which('make'), 'Requires Make for command previews')
    def test_windows_media_targets_dispatch_without_mac_rejection(self):
        for target, flag in (('default-apps', '-OpenSettings'), ('default-apps-check', '-Check')):
            result = subprocess.run(['make', '-n', '-f', 'windows.mk', target], cwd=ROOT,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('default-apps ' + flag, result.stdout)

    def test_windows_media_manifest_keeps_supported_extensions_and_source_files(self):
        entries = [line for line in (ROOT / 'config/windows-vlc-associations.tsv').read_text().splitlines()
                   if line and not line.startswith('#') and line != 'extension']
        self.assertEqual(len(entries), 37)
        self.assertEqual(len(set(entries)), len(entries))
        self.assertTrue(all(re.fullmatch(r'\.[a-z0-9]+', entry) for entry in entries))
        self.assertFalse({'.ts', '.ogm', '.ogv', '.iinaplg', '.opus'}.intersection(entries))
        self.assertTrue({'.mp4', '.mkv', '.mp3', '.webm'}.issubset(entries))

    def test_skill_manifest_selectors_and_inventory_are_current(self):
        for script in ('scripts/gen-skillsfile.py', 'agents/compareskills.py'):
            result = subprocess.run([sys.executable, str(ROOT / script), '--check'],
                                    capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        selectors = [line.split(' --skill ', 1)[1].split(' -g ', 1)[0]
                     for line in (ROOT / 'Skillsfile').read_text().splitlines()
                     if line.startswith('update_skill_source "$NPX" skills add ')]
        self.assertTrue(selectors)
        self.assertTrue(all(',' not in selector for selector in selectors))

    def test_audit_requires_ripgrep(self):
        bash = (str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe')
                if os.name == 'nt' else shutil.which('bash'))
        with tempfile.TemporaryDirectory() as directory:
            # Clear PATH after Bash startup; only shell builtins reach the guard.
            result = subprocess.run(
                [bash, '-c', 'PATH="$1"; export PATH; source "$2"', 'fixture',
                 Path(directory).as_posix(), (ROOT / 'scripts/audit-app-prefs.sh').as_posix()],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 127, result.stderr)
            self.assertIn('requires ripgrep', result.stderr)
            self.assertNotIn('no issues', result.stdout)

    def test_manifest_snapshots_exist(self):
        manifest_only = {
            'macos/services.plist', 'macos/trackpad.plist',
            'macos/bluetooth-trackpad.plist', 'macos/mouse.plist',
            'macos/bluetooth-mouse.plist',
        }
        for line in (ROOT / 'apps.tsv').read_text().splitlines():
            if line and not line.startswith('#'):
                label, snapshot = line.split('\t')[1:3]
                if snapshot in manifest_only:
                    self.assertFalse((ROOT / snapshot).exists(), label)
                else:
                    self.assertTrue((ROOT / snapshot).is_file(), label)

    @unittest.skipUnless(sys.platform == 'darwin', 'Requires macOS preference tools')
    def test_mac_capture_retains_templates_and_omits_dato(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'checkout'
            root.mkdir()
            for name in ('apps', 'macos', 'services', 'scripts'):
                shutil.copytree(ROOT / name, root / name)
            for name in ('Brewfile', 'apps.tsv', '.node-version'):
                shutil.copy2(ROOT / name, root / name)
            home = Path(directory) / 'profile'
            dato = home / 'Library/Group Containers/group.com.sindresorhus.Dato/Library/Preferences/group.com.sindresorhus.Dato.plist'
            dato.parent.mkdir(parents=True)
            dato.write_bytes(plistlib.dumps({'sharedTimeZones': ['dummy-personal-zone']}))
            shim = Path(directory) / 'bin'
            shim.mkdir()
            defaults = shim / 'defaults'
            defaults.write_text('#!/bin/sh\nif [ "$1:$2" = "export:org.example.fixture" ]; then cp "$FIXTURE_EXPORT" "$3"; else exit 1; fi\n')
            snapshot = root / 'apps/fixture/settings.plist'
            snapshot.parent.mkdir()
            snapshot.write_bytes(plistlib.dumps({'enabled': True, 'order': ['one', 'two'],
                                                 'SULastCheckTime': 'old'}, fmt=plistlib.FMT_BINARY))
            prior = snapshot.read_bytes()
            captured = Path(directory) / 'capture.plist'
            captured.write_bytes(plistlib.dumps({'order': ['one', 'two'], 'enabled': True,
                                                 'SULastCheckTime': 'new'}, sort_keys=False))
            with (root / 'apps.tsv').open('a') as manifest:
                manifest.write('\norg.example.fixture\tFixture\tapps/fixture/settings.plist\n')
            defaults.chmod(0o755)
            (root / 'scripts/brewfile.sh').write_text('#!/bin/sh\ncp "$BREWFILE" "$2"\n')
            paths = [p for app in ('vscode','cursor','zed','sublime-text') for p in (root / 'apps' / app).rglob('*') if p.is_file()]
            paths.append(root / 'macos/dock-backup.plist')
            before = {p: p.read_bytes() for p in paths}
            env = dict(os.environ, DOTFILES=str(root), HOME=str(home), FIXTURE_EXPORT=str(captured), PATH=str(shim) + os.pathsep + os.environ['PATH'])
            subprocess.run(['bash', str(root / 'scripts/backup-apps.sh')], env=env, check=True, capture_output=True)
            self.assertFalse((root / 'apps/dato/dato.plist').exists())
            for p, data in before.items():
                self.assertEqual(p.read_bytes(), data, str(p.relative_to(root)))
            self.assertEqual(snapshot.read_bytes(), prior)
            # Repeating the whole backup is stable; changing an ordered setting is not.
            subprocess.run(['bash', str(root / 'scripts/backup-apps.sh')], env=env, check=True, capture_output=True)
            self.assertEqual(snapshot.read_bytes(), prior)
            captured.write_bytes(plistlib.dumps({'enabled': False, 'order': ['two', 'one']}))
            subprocess.run(['bash', str(root / 'scripts/backup-apps.sh')], env=env, check=True, capture_output=True)
            self.assertEqual(plistlib.loads(snapshot.read_bytes()), {'enabled': False, 'order': ['two', 'one']})
            # Fail after apps is published and the old macos root is moved away.
            # All managed roots must return to their previous bytes and paths.
            def managed_snapshot():
                files = [root / 'Brewfile']
                for name in ('apps', 'macos', 'services'):
                    files.extend(p for p in (root / name).rglob('*') if p.is_file())
                return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode)
                        for p in files}

            retained = managed_snapshot()
            captured.write_bytes(plistlib.dumps({'enabled': True, 'order': ['replacement']}))
            failure = Path(directory) / 'move-failed'
            move = shim / 'mv'
            move.write_text('#!/bin/sh\n'
                            'case "$2" in */.backup-rollback.*/macos)\n'
                            '  /bin/mv "$@" || exit\n'
                            '  : > "$FIXTURE_MOVE_FAILURE"\n'
                            '  exit 73;;\nesac\nexec /bin/mv "$@"\n')
            move.chmod(0o755)
            result = subprocess.run(['bash', str(root / 'scripts/backup-apps.sh')],
                                    env=dict(env, FIXTURE_MOVE_FAILURE=str(failure)),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
            self.assertTrue(failure.exists(), 'The intended publication failure was not reached')
            self.assertIn('restoring the previous repo snapshot', result.stdout)
            self.assertEqual(managed_snapshot(), retained)
            self.assertFalse(list(root.glob('.backup-stage.*')))
            self.assertFalse(list(root.glob('.backup-rollback.*')))

    @unittest.skipUnless(sys.platform == 'darwin', 'Requires macOS plutil')
    def test_public_app_sanitization_and_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.node-version').write_text((ROOT / '.node-version').read_text())
            fixtures = {
                'clop': {'Paddle-Clop-841006-SD': b'dummy-license', 'ZephyrSyncKey': 'dummy', 'savedPipelines': b'dummy-inventory', 'showMenubarIcon': True},
                'thaw': {'KnownDisplays': b'dummy-display', 'MenuBarItemManager.knownItemIdentifiers': b'dummy-app', 'ShowOnHover': True},
            }
            for app, data in fixtures.items():
                path = root / 'apps' / app / (app + '.plist')
                path.parent.mkdir(parents=True)
                path.write_bytes(plistlib.dumps(data, fmt=plistlib.FMT_BINARY))
            env = dict(os.environ, DOTFILES=str(root))
            audit = ['bash', str(ROOT / 'scripts/audit-app-prefs.sh')]
            self.assertNotEqual(subprocess.run(audit, env=env, capture_output=True).returncode, 0)
            subprocess.run(['bash', str(ROOT / 'scripts/sanitize-app-prefs.sh')], env=env, check=True, capture_output=True)
            for app, kept in [('clop', 'showMenubarIcon'), ('thaw', 'ShowOnHover')]:
                self.assertEqual(plistlib.loads((root / 'apps' / app / (app + '.plist')).read_bytes()), {kept: True})
            subprocess.run(audit, env=env, check=True, capture_output=True)
            dato = root / 'apps/dato/dato.plist'
            dato.parent.mkdir(); dato.write_bytes(plistlib.dumps({'sharedTimeZones': []}))
            self.assertNotEqual(subprocess.run(audit, env=env, capture_output=True).returncode, 0)

if __name__ == '__main__':
    unittest.main()
