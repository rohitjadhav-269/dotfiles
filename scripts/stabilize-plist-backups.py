#!/usr/bin/env python3
"""Retain prior plist bytes when capture differs only by backup housekeeping.

Run on the disposable backup stage against a SANITIZED copy of prior snapshots,
so retained bytes cannot bypass current secret/path removal rules. Use the same
volatile-key policy as apps-drift; dictionary/JSON key order is insignificant,
but array order and meaningful preference values remain significant.
"""

from pathlib import Path
import sys

from lib.plist_drift import load


def stabilize(stage: Path, previous: Path) -> int:
    retained = 0
    for root in ("apps", "macos", "services"):
        for candidate in (stage / root).rglob("*.plist"):
            saved = previous / candidate.relative_to(stage)
            if not saved.is_file():
                continue
            # An invalid prior snapshot must not prevent capture from repairing it.
            try:
                prior = load(str(saved))
            except (OSError, ValueError):
                continue
            if load(str(candidate)) == prior:
                candidate.write_bytes(saved.read_bytes())
                retained += 1
    return retained


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <stage> <previous>", file=sys.stderr)
        return 2
    stage, previous = (Path(arg).resolve() for arg in sys.argv[1:])
    if stage == previous or not stage.is_dir() or not previous.is_dir():
        print("expected separate existing stage and previous directories", file=sys.stderr)
        return 2
    retained = stabilize(stage, previous)
    print(f"  retained {retained} equivalent plist snapshot(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
