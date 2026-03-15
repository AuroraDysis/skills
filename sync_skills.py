#!/usr/bin/env python3
"""Check upstream skill sources and notify when they differ from local copies.

All skills use notify mode: prints a warning when upstream differs,
then the user reviews and updates manually.
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST = SCRIPT_DIR / "skills.json"


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()



def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "skills-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main() -> int:
    if not MANIFEST.exists():
        print(f"Error: {MANIFEST} not found", file=sys.stderr)
        return 1

    skills = json.loads(MANIFEST.read_text())
    changed = False
    has_notify = False

    for skill in skills:
        name = skill["name"]
        upstream_url = skill.get("upstream_url", "")
        if not upstream_url:
            continue
        recorded_md5 = skill.get("md5", "")

        print(f"[{name}] Checking upstream: {upstream_url}")

        try:
            upstream_data = fetch(upstream_url)
        except Exception as e:
            print(f"  ✗ Failed to fetch: {e}", file=sys.stderr)
            continue

        upstream_md5 = md5_bytes(upstream_data)

        if upstream_md5 == recorded_md5:
            print(f"  ✓ Up to date ({upstream_md5})")
            continue

        has_notify = True
        skill["md5"] = upstream_md5
        changed = True
        print(f"  ⚠ Upstream changed: {recorded_md5} → {upstream_md5}")
        print(f"    Review: {upstream_url}")

    if changed:
        MANIFEST.write_text(json.dumps(skills, indent=2) + "\n")
        print("\nUpdated skills.json")

    if has_notify:
        print("\nSome notify-mode skills have upstream changes. Review manually.")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
