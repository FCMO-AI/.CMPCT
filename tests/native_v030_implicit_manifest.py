#!/usr/bin/env python3
"""Independent + writer parity for canonical r25 implicit-v4 filesystem control."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from experiments import entropygraph_v030_canonical_final as canonical

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "native" / "cmpct-portable" / "target" / "release" / "cmpct-portable"
FIXTURE = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4.json"


def run(*args: str, check: bool = True, text: bool = False):
    return subprocess.run([str(CLI), *args], check=check, capture_output=True, text=text)


def assert_native_archive(path: Path, expected: dict[str, dict], *, probe: str | None = None, payload: bytes | None = None) -> None:
    run("verify", str(path))
    listed = run("list", str(path), text=True).stdout.strip().splitlines()
    rows = {line.split("\t", 3)[3]: (int(line.split("\t", 3)[1]), int(line.split("\t", 3)[2])) for line in listed}
    assert rows == {rel: (row["kind"], row["size"]) for rel, row in expected.items()}
    if probe is not None:
        assert payload is not None
        raw = run("read", str(path), probe).stdout
        assert raw == payload
        stats = dict(
            line.split("=", 1)
            for line in run("member-stats", str(path), probe, text=True).stdout.strip().splitlines()
        )
        assert int(stats["logical_bytes"]) == len(payload)
        assert float(stats["amplification"]) <= 8.0


def assert_independent_goldens(tmp: Path) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["schema"] == "cmpct-v030-native-implicit-v4-golden-v1"
    expected = fixture["filesystem"]["entries"]
    for profile in ("g04", "prefixgraph"):
        row = fixture[profile]
        raw = base64.b64decode(row["archive_base64"], validate=True)
        assert hashlib.sha256(raw).hexdigest() == row["archive_sha256"]
        path = tmp / f"independent-implicit-{profile}.cmpct"
        path.write_bytes(raw)
        assert_native_archive(path, expected)


def tree_payload(index: int) -> bytes:
    # Repetitive names/metadata make implicit-v4 decisively smaller while member bytes remain distinct enough to
    # exercise graph-derived size/SHA ownership rather than accidental content deduplication.
    return (f"member-{index:03d}-".encode() + bytes([index % 251]) * 128) * 4


def assert_writer_parity(tmp: Path) -> None:
    source = tmp / "source"
    for index in range(96):
        path = source / "src" / "pkg" / f"very_repetitive_component_{index:03d}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tree_payload(index))

    staged = tmp / "staged"
    prepared = canonical._prepare_profile_tree(source, staged)
    assert prepared["selected_manifest_encoding"] == "implicit-v4", prepared
    assert prepared["manifest_control_saving_bytes"] > 0

    archive = tmp / "writer-implicit.cmpct"
    stats = canonical._r25_build(staged, archive)
    revision, profile = canonical._profile_for_archive(archive)
    assert revision == 25 and profile in {"geometry-g04", "prefixgraph-depth1"}, (revision, profile, stats)
    verified = canonical.strong_verify(archive)
    assert verified["ok"] is True
    decoded = canonical._validated_manifest(archive)
    assert len(decoded["regular"]) == 96

    expected = {rel: {"kind": 0, "size": size} for rel, (size, _digest) in decoded["regular"].items()}
    probe = "src/pkg/very_repetitive_component_047.bin"
    payload = (source / probe).read_bytes()
    assert hashlib.sha256(payload).digest() == decoded["regular"][probe][1]
    assert_native_archive(archive, expected, probe=probe, payload=payload)


def main() -> None:
    assert CLI.is_file(), CLI
    assert FIXTURE.is_file(), FIXTURE
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-native-implicit-") as td:
        tmp = Path(td)
        # Independent bytes come first. A shared writer/reader bug therefore cannot hide a format mismatch.
        assert_independent_goldens(tmp)
        # The real canonical writer remains a separate parity boundary because fixed bytes alone cannot prove its
        # current admission seam publishes a dialect understood by native/platform readers.
        assert_writer_parity(tmp)
    print("v0.30 native implicit-v4 independent + writer parity: ok")


if __name__ == "__main__":
    main()
