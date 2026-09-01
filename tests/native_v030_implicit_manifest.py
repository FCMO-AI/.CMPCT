#!/usr/bin/env python3
"""Independent, hostile, recovery, and writer parity for canonical r25 implicit-v4 filesystem control."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import msgpack

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import entropygraph_v030_canonical_final as canonical
import generate_v030_implicit_goldens as independent

CLI = ROOT / "native" / "cmpct-portable" / "target" / "release" / "cmpct-portable"
FIXTURE = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4.json"
G04_HEADER = struct.Struct("<8sQQIQQ32s32s")
G04_FOOTER = struct.Struct("<8sQQ32s32s")
PG_HEADER = struct.Struct("<8sQQ32s")
PG_FOOTER = struct.Struct("<8sQQ32s")


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


def recovery_variants(profile: str, original: bytes) -> dict[str, tuple[bytes, bool]]:
    """Damage authenticated metadata copies independently without changing the implicit control semantics."""
    if profile == "g04":
        header = G04_HEADER
        footer = G04_FOOTER
    elif profile == "prefixgraph":
        header = PG_HEADER
        footer = PG_FOOTER
    else:
        raise AssertionError(profile)

    header_size = header.size
    primary_size = header.unpack_from(original, 0)[1]
    footer_off = len(original) - footer.size
    tail_size = footer.unpack_from(original, footer_off)[1]
    tail_meta = footer_off - tail_size
    payload_start = header_size + primary_size
    assert primary_size > 0 and tail_size > 0 and payload_start < tail_meta

    primary = bytearray(original)
    tail = bytearray(original)
    both = bytearray(original)
    payload = bytearray(original)
    primary_index = header_size + min(8, primary_size - 1)
    tail_index = tail_meta + min(8, tail_size - 1)
    payload_index = payload_start + (tail_meta - payload_start) // 2

    primary[primary_index] ^= 0x40
    tail[tail_index] ^= 0x40
    both[primary_index] ^= 0x40
    both[tail_index] ^= 0x40
    payload[payload_index] ^= 0x01
    return {
        "primary-damaged": (bytes(primary), True),
        "tail-damaged": (bytes(tail), True),
        "both-metadata-damaged": (bytes(both), False),
        "payload-damaged": (bytes(payload), False),
    }


def assert_recovery(
    profile: str,
    original: bytes,
    expected: dict[str, dict],
    tmp: Path,
    *,
    prefix: str,
) -> None:
    for label, (raw, should_verify) in recovery_variants(profile, original).items():
        candidate = tmp / f"{prefix}-{profile}-{label}.cmpct"
        candidate.write_bytes(raw)
        if should_verify:
            # A green verifier alone is insufficient: failover metadata must still reconstruct the same public tree.
            assert_native_archive(candidate, expected)
            continue
        result = run("verify", str(candidate), check=False, text=True)
        assert result.returncode != 0, (profile, label, result.stdout, result.stderr)


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
        # Recovery is a property of the canonical outer r25 profile, but implicit-v4 must prove that its compact
        # authenticated control survives the same primary/tail failover boundary rather than inheriting credit
        # from filesystem-v1 fixtures. Both metadata copies or payload corruption must still fail closed.
        assert_recovery(profile, raw, expected, tmp, prefix="independent-implicit")


def assert_hostile_authenticated_controls(tmp: Path) -> None:
    """Reject malformed filesystem controls even when the enclosing graph is fully authenticated."""
    manifest, user_raw, _expected = independent.implicit_filesystem()
    root = msgpack.unpackb(manifest, raw=False)

    cases: dict[str, list] = {}

    bad_version = copy.deepcopy(root)
    bad_version[0] = 5
    cases["bad-version"] = bad_version

    bad_regular_count = copy.deepcopy(root)
    bad_regular_count[2] = []
    cases["regular-count-mismatch"] = bad_regular_count

    bad_mask = copy.deepcopy(root)
    bad_mask[2][0] = [32]
    cases["unknown-metadata-mask"] = bad_mask

    colliding_path = copy.deepcopy(root)
    colliding_path[3] = [[0, "dir/hello.bin", 1, [0], None]]
    cases["explicit-regular-collision"] = colliding_path

    bad_hardlink = copy.deepcopy(root)
    for row in bad_hardlink[3]:
        if row[2] == 3:
            row[4] = 99
            break
    cases["hardlink-owner-out-of-range"] = bad_hardlink

    unsafe_symlink = copy.deepcopy(root)
    for row in unsafe_symlink[3]:
        if row[2] == 2:
            row[4] = "../escape"
            break
    cases["unsafe-symlink-target"] = unsafe_symlink

    builders = {
        "g04": independent.g04_archive,
        "prefixgraph": independent.prefix_archive,
    }
    for label, malformed in cases.items():
        control = independent.pack(malformed)
        for profile, build in builders.items():
            archive = tmp / f"hostile-{label}-{profile}.cmpct"
            archive.write_bytes(build(control, user_raw))
            result = run("verify", str(archive), check=False, text=True)
            assert result.returncode != 0, (label, profile, result.stdout, result.stderr)


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

    profile_key = "g04" if profile == "geometry-g04" else "prefixgraph"
    # Fixed goldens prove independent grammar; this second matrix proves the live canonical writer publishes the
    # same recoverable outer-profile semantics after implicit-v4 admission rather than only matching on clean bytes.
    assert_recovery(
        profile_key,
        archive.read_bytes(),
        expected,
        tmp,
        prefix="writer-implicit",
    )


def main() -> None:
    assert CLI.is_file(), CLI
    assert FIXTURE.is_file(), FIXTURE
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-native-implicit-") as td:
        tmp = Path(td)
        # Independent bytes come first. A shared writer/reader bug therefore cannot hide a format mismatch.
        assert_independent_goldens(tmp)
        # Malformed controls are rebuilt into otherwise authenticated canonical archives. This proves the shared
        # native wrapper rejects semantic/parser defects rather than merely rejecting a corrupt outer container.
        assert_hostile_authenticated_controls(tmp)
        # The real canonical writer remains a separate parity boundary because fixed bytes alone cannot prove its
        # current admission seam publishes a dialect understood by native/platform readers.
        assert_writer_parity(tmp)
    print("v0.30 native implicit-v4 independent + hostile + recovery + writer parity: ok")


if __name__ == "__main__":
    main()
