#!/usr/bin/env python3
"""Keychain resolution contracts using a fake security executable; no live credentials."""
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class KeychainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'bin').mkdir()
        (self.root / 'scripts/lib').mkdir(parents=True)
        self.security = self.root / 'security'
        self.security.write_text('#!/bin/sh\n[ "$1" = find-generic-password ] || exit 3\n[ "$3" = fixture/service ] || exit 4\nprintf fixture-value\n')
        self.security.chmod(0o700)
        helper = (ROOT / 'scripts/lib/keychain.sh').read_text().replace('/usr/bin/security', str(self.security))
        (self.root / 'scripts/lib/keychain.sh').write_text(helper)
        self.env = {**os.environ, 'DOTFILES_SECRETS_DIR': str(self.root)}
        (self.root / 'config/env').mkdir(parents=True)

    def invoke(self, name, *args):
        shutil.copyfile(ROOT / 'bin' / name, self.root / 'bin' / name)
        return subprocess.run(['bash', '-x', str(self.root / 'bin' / name), *args],
                              env=self.env, capture_output=True, text=True)

    def test_reference_resolution_child_isolation_and_exit_status(self):
        for name, key in [('figma', 'FIGMA_TOKEN'), ('typesafe', 'TYPESAFE_API_KEY')]:
            (self.root / f'config/env/{name}.env').write_text(f"export {key}='keychain://fixture/service'\nexport UNRELATED=hidden\n")
            self.env[key] = 'stale-inherited'
            result = self.invoke(name+'-env', '--', 'bash', '-c',
                                 '[[ "${!1}" == fixture-value && -z "${UNRELATED:-}" && "$2" == "two words" ]] || exit 8; exit 17',
                                 '_', key, 'two words')
            self.assertEqual(result.returncode, 17, result.stderr)
            self.assertNotIn('fixture-value', result.stdout + result.stderr)
            self.assertNotIn('stale-inherited', result.stdout + result.stderr)

    def test_denied_missing_empty_keychain_fails_closed_without_logging(self):
        path = self.root / 'config/env/figma.env'
        path.write_text("export FIGMA_TOKEN='keychain://fixture/service'\n")
        self.env['FIGMA_TOKEN'] = 'stale-inherited'
        for body in ('echo leaked-value >&2; exit 44', 'exit 0'):
            self.security.write_text('#!/bin/sh\n'+body+'\n')
            result = self.invoke('figma-env', '--check')
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('leaked-value', result.stdout + result.stderr)
            self.assertNotIn('stale-inherited', result.stdout + result.stderr)

    def test_context7_uses_keychain_with_existing_runtime_contract(self):
        (self.root / 'config/env/context7.env').write_text("export CONTEXT7_API_KEY='keychain://fixture/service'\n")
        node = self.root / 'node'
        node.write_text('#!/bin/bash\n[[ "$CONTEXT7_API_KEY" == fixture-value && "$3" == @upstash/context7-mcp@4.0.3 && "$4" == "two words" ]] || exit 8\nexit 17\n')
        node.chmod(0o700)
        target = self.root / 'npx-real'; target.touch()
        npx = self.root / 'npx'; npx.symlink_to(target)
        self.env.update(NODE_STABLE=str(node), NPX_STABLE=str(npx))
        result = self.invoke('context7-mcp', 'two words')
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertNotIn('fixture-value', result.stdout + result.stderr)

    def test_generic_profile_parses_without_executing_shell_and_hides_errors(self):
        loader = importlib.machinery.SourceFileLoader('tool_env', str(ROOT / 'bin/tool-env'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec); loader.exec_module(module)
        path = self.root / 'config/env/exa.env'
        path.write_text("export EXA_API_KEY='keychain://fixture/service'\n")
        output = io.StringIO()
        with patch.dict(os.environ, self.env), patch.object(module.sys, 'argv', ['tool-env','exa','--','echo','two words']), \
             patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([],0,'fixture-value\n','')), \
             patch.object(module.os, 'execvpe') as execute, redirect_stdout(output), redirect_stderr(output):
            module.main()
            self.assertEqual(execute.call_args.args[1], ['echo','two words'])
            self.assertEqual(execute.call_args.args[2]['EXA_API_KEY'], 'fixture-value')
        self.assertNotIn('fixture-value', output.getvalue())
        marker=self.root/'executed'
        path.write_text(f'touch {marker}\n')
        result=subprocess.run(['python3',str(ROOT/'bin/tool-env'),'exa','--check'],env=self.env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(marker.exists())

if __name__ == '__main__':
    unittest.main()
