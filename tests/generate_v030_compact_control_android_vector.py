from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
from pathlib import Path
import shutil
import sys

# Android CI invokes vector generators directly, so pin imports to the checked-out PR source tree.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import entropygraph_v030_r24_compact_control_profile as CC


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _source_truth(src: Path) -> dict[str, dict[str, object]]:
    truth: dict[str, dict[str, object]] = {}
    for path in sorted(p for p in src.rglob("*") if p.is_file()):
        rel = path.relative_to(src).as_posix()
        raw = path.read_bytes()
        truth[rel] = {
            "size": len(raw),
            "sha256": _sha256(raw),
            "head_base64": base64.b64encode(raw[:64]).decode("ascii"),
        }
    return truth


def _directory_truth(src: Path) -> list[str]:
    return sorted(path.relative_to(src).as_posix() for path in src.rglob("*") if path.is_dir())


def build_vector(output: Path, archive_output: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    src = work_root / "src"
    src.mkdir(parents=True)
    rng = random.Random(0xC25CC01)

    # Exercise the same generic shape that made compact control useful: many tiny/medium high-entropy .bin members.
    for i in range(256):
        path = src / "tiny" / f"block-{i:04d}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rng.randbytes(256 + (i % 31)))
    for i in range(40):
        path = src / "medium" / f"chunk-{i:03d}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rng.randbytes(96 * 1024 + (i % 5) * 1024))

    archive = work_root / "v030-compact-control-android.cmpct"
    stats = CC.build(src, archive)
    verified = CC.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"compact-control Android vector failed strong verification: {verified!r}")
    if not stats.get("physical_payload_records_unchanged"):
        raise RuntimeError(f"compact-control vector changed the mature r24 physical payload: {stats!r}")
    if not stats.get("two_authenticated_control_copies"):
        raise RuntimeError(f"compact-control vector lost two-way control recovery: {stats!r}")
    if int(stats["archive_bytes"]) >= int(stats["source_r24_bytes"]):
        raise RuntimeError(f"compact-control vector must exercise a strict control-plane size win: {stats!r}")

    truth = _source_truth(src)
    directories = _directory_truth(src)
    archive_raw = archive.read_bytes()
    representative = "medium/chunk-000.bin"

    # Keep the multi-megabyte archive as a binary Android test asset instead of base64-embedding it
    # in JSON. The latter transiently doubles the vector in a Java String and can exceed the API-29
    # instrumentation heap before the JNI reader is even exercised. Metadata still binds the binary
    # asset by exact size + SHA-256, so this changes test transport only, not the conformance vector.
    archive_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, archive_output)
    vector = {
        "schema": "cmpct-v030-android-compact-control-vector-v2",
        "profile": "r24-compact-control-v1",
        "revision": 25,
        "archive_asset": archive_output.name,
        "archive_sha256": _sha256(archive_raw),
        "archive_bytes": len(archive_raw),
        "expected_paths": sorted(truth),
        "expected_directory_paths": directories,
        "expected_regular_entry_count": len(truth),
        "expected_entry_count": len(truth) + len(directories),
        "representative_path": representative,
        "representative_size": truth[representative]["size"],
        "representative_sha256": truth[representative]["sha256"],
        "representative_head_base64": truth[representative]["head_base64"],
        "facts": {
            "strong_verify": True,
            "physical_payload_records_unchanged": True,
            "two_authenticated_control_copies": True,
            "strictly_smaller_than_source_r24": True,
            "source_r24_bytes": int(stats["source_r24_bytes"]),
            "archive_bytes": int(stats["archive_bytes"]),
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(vector, indent=2) + "\n", encoding="utf-8")
    return vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive-output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    vector = build_vector(args.output, args.archive_output, args.work_root)
    print(
        json.dumps(
            {
                "schema": vector["schema"],
                "archive_asset": vector["archive_asset"],
                "archive_sha256": vector["archive_sha256"],
                "archive_bytes": vector["archive_bytes"],
                "expected_entry_count": vector["expected_entry_count"],
                "facts": vector["facts"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
