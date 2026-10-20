"""Check the installer's account-shell decision without changing an account."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == "nt", "POSIX shell fixture; no native Windows changes")
class AccountShellSetup(unittest.TestCase):
    def test_account_state_overrides_inherited_shell_and_lookup_fails_closed(self):
        source = (ROOT / "install.sh").read_text()
        block = source.split("# 5. Default shell\n", 1)[1].split("# 6.", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "bin"
            scripts.mkdir()
            query = scripts / "dscacheutil"
            query.write_text(
                '#!/bin/sh\n: > "$FIXTURE_QUERY"\n'
                '[ "$FIXTURE_LOOKUP_FAIL" = 0 ] || exit 1\n'
                'printf "shell: %s\\n" "$FIXTURE_ACCOUNT_SHELL"\n'
            )
            change = scripts / "chsh"
            change.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FIXTURE_CHSH"\n')
            query.chmod(0o755)
            change.chmod(0o755)
            env = {key: value for key, value in os.environ.items()
                   if key not in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS")}
            env.update(PATH=str(scripts) + os.pathsep + os.defpath,
                       FIXTURE_QUERY=str(root / "queried"),
                       FIXTURE_CHSH=str(root / "changed"))
            cases = [
                ("/bin/zsh", "/bin/bash", "0", "0", 0, True),
                ("/bin/bash", "/bin/zsh", "0", "0", 0, False),
                ("/bin/zsh", "", "0", "0", 1, False),
                ("/bin/zsh", "/bin/bash", "1", "0", 1, False),
                ("/bin/bash", "/bin/bash", "1", "1", 0, False),
            ]
            for number, (inherited, account, failure, smoke, code, changes) in enumerate(cases):
                with self.subTest(case=number):
                    # Each case gets independent markers; no process may reach real chsh.
                    env.update(SHELL=inherited, FIXTURE_ACCOUNT_SHELL=account,
                               FIXTURE_LOOKUP_FAIL=failure,
                               FIXTURE_QUERY=str(root / f"query-{number}"),
                               FIXTURE_CHSH=str(root / f"change-{number}"))
                    result = subprocess.run(
                        ["/bin/bash", "-c", "set -euo pipefail\nBOOTSTRAP_SMOKE=" + smoke + "\n" + block],
                        env=env, text=True, capture_output=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                    marker = Path(env["FIXTURE_CHSH"])
                    self.assertEqual(marker.exists(), changes)
                    if changes:
                        self.assertEqual(marker.read_text(), "-s /bin/zsh\n")
                    self.assertEqual(Path(env["FIXTURE_QUERY"]).exists(), smoke == "0")


if __name__ == "__main__":
    unittest.main()
