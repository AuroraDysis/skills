#!/usr/bin/env python3
"""Check upstream skill sources and sync or notify based on skills.json config.

Modes:
  - sync:   auto-download upstream file and update local copy + md5
  - notify: only print a warning when upstream differs
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


def md5_file(path: Path) -> str:
    return md5_bytes(path.read_bytes())


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
        local_path = SCRIPT_DIR / skill["local_path"]
        upstream_url = skill["upstream_url"]
        mode = skill.get("mode", "notify")
        recorded_md5 = skill.get("md5", "")

        print(f"[{name}] Checking upstream: {upstream_url}")

        try:
            upstream_data = fetch(upstream_url)
        except Exception as e:
            print(f"  ✗ Failed to fetch: {e}", file=sys.stderr)
            continue

        upstream_md5 = md5_bytes(upstream_data)
        local_md5 = md5_file(local_path) if local_path.exists() else ""

        if upstream_md5 == local_md5 and upstream_md5 == recorded_md5:
            print(f"  ✓ Up to date ({upstream_md5})")
            continue

        if mode == "sync":
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(upstream_data)
            skill["md5"] = upstream_md5
            changed = True
            if upstream_md5 == local_md5:
                print(f"  ✓ MD5 record updated ({upstream_md5})")
            else:
                print(f"  ↓ Synced: {local_md5 or '(new)'} → {upstream_md5}")
        else:
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
