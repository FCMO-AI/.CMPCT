#!/usr/bin/env python3
"""Generate a builder-independent r25 golden with a supplementary-Unicode public path.

This fixture exists to prove that platform bindings preserve canonical UTF-8 paths exactly.
The archive grammar and deterministic Zstandard framing come from the primary canonical
golden generator; only the filesystem manifest differs. One canonical G04 archive is enough
because the defect under test lives in the shared post-dispatch JNI path conversion.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from generate_v030_canonical_goldens import INTERNAL, MANIFEST_PROFILE, g04_archive, pack, sha

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "tests" / "conformance" / "v030-r25-unicode-path.json"
UNICODE_PATH = "dir/rocket-\U0001F680.bin"


def document() -> dict:
    raw = (b"canonical-r25-portability\n" * 11) + bytes(range(32))
    digest = sha(raw)
    owner_metadata = [
        0o640,
        1_700_000_000_000_000_002,
        1000,
        1000,
        [["user.cmpct.golden", b"canonical-v1"]],
    ]
    entries = [
        ["dir", "d", 0o755, 1_700_000_000_000_000_001, 1000, 1000, [], None],
        ["dir/hello.bin", "f", *owner_metadata, [len(raw), digest]],
        [UNICODE_PATH, "h", *owner_metadata, "dir/hello.bin"],
    ]
    manifest = pack(
        {
            "v": 1,
            "profile": MANIFEST_PROFILE,
            "internal_path": INTERNAL,
            "entries": entries,
        }
    )
    archive, tree = g04_archive(manifest, raw)
    return {
        "schema": "cmpct-v030-native-unicode-path-golden-v1",
        "provenance": (
            "Generated from the frozen canonical r25 byte grammar by "
            "tests/generate_v030_unicode_path_golden.py; no CMPCT Builder or product writer participates."
        ),
        "unicode_path": UNICODE_PATH,
        "owner_path": "dir/hello.bin",
        "owner_sha256": digest.hex(),
        "owner_size": len(raw),
        "manifest_sha256": sha(manifest).hex(),
        "g04": {
            "profile": "g04-r25",
            "revision": 25,
            "archive_base64": base64.b64encode(archive).decode("ascii"),
            "archive_sha256": sha(archive).hex(),
            "tree_sha256": tree.hex(),
            "archive_size": len(archive),
        },
    }


def render() -> str:
    return json.dumps(document(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = render()
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != generated:
            raise SystemExit(f"unicode-path golden drift: regenerate {args.output}")
        print(f"unicode-path golden reproducible: {args.output}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
