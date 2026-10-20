#!/usr/bin/env python3
"""Check installed skill resources; optionally probe the versioned local engine.

Offline and read-only: never download, install, load credentials, or run a skill
workflow. Source freshness is a separate comparison against GitHub snapshots.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def check_resources(root):
    errors = []
    lock = json.loads((root / "agents/.skill-lock.json").read_text())
    for name in lock["skills"]:
        if not (root / "agents/skills" / name / "SKILL.md").is_file():
            errors.append(f"{name}: SKILL.md is missing")
    manifest = json.loads((root / "config/skill-install-resources.json").read_text())
    for entry in manifest["resources"]:
        target = root / entry["path"]
        if not target.is_file():
            errors.append(f"{entry['path']}: required external skill resource is missing")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
            errors.append(f"{entry['path']}: resource checksum differs from its source record")
    for target in (root / "agents/skills").rglob("*"):
        if target.is_symlink() and not target.exists():
            errors.append(f"{target.relative_to(root)}: broken symlink")
    return errors


def check_engine(root, engine_home):
    scripts = root / "agents/skills/impeccable/scripts"
    version = (scripts / "VERSION").read_text().strip()
    os_name = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}.get(platform.system())
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "AMD64": "x64"}.get(platform.machine())
    if not os_name or not arch:
        return ["Impeccable: unsupported platform for the engine readiness check"]
    name = "impeccable.exe" if os_name == "windows" else "impeccable"
    candidates = [scripts / "bin" / f"{os_name}-{arch}" / name, engine_home / "bin" / version / name]
    if os.environ.get("IMPECCABLE_BIN"):
        candidates.insert(0, Path(os.environ["IMPECCABLE_BIN"]))
    for binary in candidates:
        if not binary.is_file():
            continue
        if not os.access(binary, os.X_OK):
            return [f"Impeccable engine {version}: installed binary is not executable"]
        try:
            result = subprocess.run([str(binary), "engine-probe"], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return [f"Impeccable engine {version}: handshake could not run"]
        if result.returncode or result.stdout.strip() != f"impeccable-engine {version}":
            return [f"Impeccable engine {version}: handshake/version mismatch"]
        return []
    return [f"Impeccable engine {version} is missing; run the reviewed skill launcher with engine-probe in a network-enabled terminal"]


def check_browser_dependency(root):
    dependency = root / "agents/skills/fluid-functionalism/scripts/node_modules/playwright-core/package.json"
    if not dependency.is_file():
        return ["Fluid Functionalism: playwright-core is missing; install the scripts/package.json dependencies with lifecycle scripts disabled"]
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime", action="store_true", help="also require a working version-matched Impeccable engine")
    parser.add_argument("--engine-home", type=Path, default=Path(os.environ.get("IMPECCABLE_HOME", Path.home() / ".impeccable")))
    args = parser.parse_args()
    try:
        errors = check_resources(args.root)
        if args.runtime:
            errors += check_engine(args.root, args.engine_home)
            errors += check_browser_dependency(args.root)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Skill installation check could not complete: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Skill installation resources verified" + ("; Impeccable engine and Fluid Functionalism dependency ready" if args.runtime else "; runtime checks: make skills-runtime"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
