#!/usr/bin/env python3
"""Writer -> shared-native parity for the admitted canonical r25 implicit-v4 filesystem control.

This is deliberately complementary to the builder-independent filesystem-v1 goldens in
``tests/conformance/v030-r25-canonical.json``.  Those fixed bytes pin the original r25 filesystem grammar, but the
canonical Python writer may now publish the strictly-smaller implicit-v4 control.  Native release authority must
therefore consume bytes emitted through that real admission seam as well; otherwise a green fixed-golden test can
mask a shipping writer/native-reader dialect split.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile

from experiments import entropygraph_v030_canonical_final as canonical

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "native" / "cmpct-portable" / "target" / "release" / "cmpct-portable"


def run(*args: str, check: bool = True, text: bool = False):
    return subprocess.run([str(CLI), *args], check=check, capture_output=True, text=text)


def tree_payload(index: int) -> bytes:
    # Repetitive names/metadata make implicit-v4 decisively smaller while member bytes remain distinct enough to
    # exercise graph-derived size/SHA ownership rather than accidental content deduplication.
    return (f"member-{index:03d}-".encode() + bytes([index % 251]) * 128) * 4


def main() -> None:
    assert CLI.is_file(), CLI
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-native-implicit-") as td:
        tmp = Path(td)
        source = tmp / "source"
        for index in range(96):
            path = source / "src" / "pkg" / f"very_repetitive_component_{index:03d}.bin"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(tree_payload(index))

        staged = tmp / "staged"
        prepared = canonical._prepare_profile_tree(source, staged)
        assert prepared["selected_manifest_encoding"] == "implicit-v4", prepared
        assert prepared["manifest_control_saving_bytes"] > 0

        archive = tmp / "canonical-r25-implicit.cmpct"
        stats = canonical._r25_build(staged, archive)
        revision, profile = canonical._profile_for_archive(archive)
        assert revision == 25 and profile in {"geometry-g04", "prefixgraph-depth1"}, (revision, profile, stats)

        verified = canonical.strong_verify(archive)
        assert verified["ok"] is True
        decoded = canonical._validated_manifest(archive)
        assert len(decoded["regular"]) == 96

        # The shared native process must open the exact writer-emitted archive, not a translated v1 surrogate.
        run("verify", str(archive))
        listed = run("list", str(archive), text=True).stdout.strip().splitlines()
        native_paths = {line.split("\t", 3)[3] for line in listed}
        assert native_paths == set(decoded["regular"])

        probe = "src/pkg/very_repetitive_component_047.bin"
        raw = run("read", str(archive), probe).stdout
        expected = (source / probe).read_bytes()
        assert raw == expected
        assert hashlib.sha256(raw).digest() == decoded["regular"][probe][1]

        member_stats = dict(
            line.split("=", 1)
            for line in run("member-stats", str(archive), probe, text=True).stdout.strip().splitlines()
        )
        assert int(member_stats["logical_bytes"]) == len(expected)
        assert float(member_stats["amplification"]) <= 8.0

    print("v0.30 native implicit-v4 writer parity: ok")


if __name__ == "__main__":
    main()
