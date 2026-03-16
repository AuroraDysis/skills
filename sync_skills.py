#!/usr/bin/env python3
"""Check upstream skill sources and sync references.

Skills use notify mode: prints a warning when upstream differs,
then the user reviews and updates manually.

References support two modes:
  - notify: same as skills (alert only)
  - fetch: automatically overwrite local file with upstream content
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


def sync_skill(skill: dict) -> tuple[bool, bool]:
    """Sync a skill's SKILL.md. Returns (changed, has_notify)."""
    name = skill["name"]
    upstream_url = skill.get("upstream_url", "")
    if not upstream_url:
        return False, False

    recorded_md5 = skill.get("md5", "")
    print(f"[{name}] Checking upstream: {upstream_url}")

    try:
        upstream_data = fetch(upstream_url)
    except Exception as e:
        print(f"  ✗ Failed to fetch: {e}", file=sys.stderr)
        return False, False

    upstream_md5 = md5_bytes(upstream_data)

    if upstream_md5 == recorded_md5:
        print(f"  ✓ Up to date ({upstream_md5})")
        return False, False

    skill["md5"] = upstream_md5
    print(f"  ⚠ Upstream changed: {recorded_md5} → {upstream_md5}")
    print(f"    Review: {upstream_url}")
    return True, True


def sync_references(skill: dict) -> tuple[bool, bool]:
    """Sync a skill's references. Returns (changed, has_notify)."""
    name = skill["name"]
    references = skill.get("references", [])
    if not references:
        return False, False

    changed = False
    has_notify = False

    for ref in references:
        upstream_url = ref.get("upstream_url", "")
        if not upstream_url:
            continue

        local_path = SCRIPT_DIR / ref["local_path"]
        mode = ref.get("mode", "notify")
        recorded_md5 = ref.get("md5", "")

        print(f"[{name}] Reference {local_path.name}: {upstream_url}")

        try:
            upstream_data = fetch(upstream_url)
        except Exception as e:
            print(f"  ✗ Failed to fetch: {e}", file=sys.stderr)
            continue

        upstream_md5 = md5_bytes(upstream_data)

        if upstream_md5 == recorded_md5:
            print(f"  ✓ Up to date ({upstream_md5})")
            continue

        if mode == "fetch":
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(upstream_data)
            ref["md5"] = upstream_md5
            changed = True
            print(f"  ↓ Fetched ({recorded_md5 or 'new'} → {upstream_md5})")
        else:
            ref["md5"] = upstream_md5
            changed = True
            has_notify = True
            print(f"  ⚠ Upstream changed: {recorded_md5} → {upstream_md5}")
            print(f"    Review: {upstream_url}")

    return changed, has_notify


def main() -> int:
    if not MANIFEST.exists():
        print(f"Error: {MANIFEST} not found", file=sys.stderr)
        return 1

    skills = json.loads(MANIFEST.read_text())
    manifest_changed = False
    has_notify = False

    for skill in skills:
        s_changed, s_notify = sync_skill(skill)
        manifest_changed |= s_changed
        has_notify |= s_notify

        r_changed, r_notify = sync_references(skill)
        manifest_changed |= r_changed
        has_notify |= r_notify

    if manifest_changed:
        MANIFEST.write_text(json.dumps(skills, indent=2) + "\n")
        print("\nUpdated skills.json")

    if has_notify:
        print("\nSome notify-mode entries have upstream changes. Review manually.")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
