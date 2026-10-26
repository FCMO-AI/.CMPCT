#!/usr/bin/env python3
"""O168: genuine macOS-created r24 archive transported to independent Linux Reader.

O155/O162/O165 remain byte-unchanged. This is the reverse direction of O165,
not a new portable metadata policy or a performance/release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
O165 = ROOT / "research/o165_one_archive_cross_host_court.py"
O165_BLOB = "2fb9cf5c9ecc072a0e692a64f21b6273f0b28fd6"
SCHEMA = "cmpct-o168-macos-to-linux-one-archive-v1"


def imported_o165():
    spec = importlib.util.spec_from_file_location("o165_exact_owner", O165)
    if spec is None or spec.loader is None:
        raise RuntimeError("O165 source-exact research helper missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_identity(o165, o162):
    actual = subprocess.check_output(
        ["git", "hash-object", str(O165.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()
    if actual != O165_BLOB:
        raise AssertionError(f"inherited O165 instrument changed: {actual} != {O165_BLOB}")
    return {**o165.identity(o162), "o165_blob": actual, "os": platform.system()}


def prove_original_archive(o165, archive: Path, expected_sha: str | None = None):
    if archive.read_bytes()[:8] != b"CMPCT24\0":
        raise AssertionError("not revision-24 CMPCT binary")
    sha = o165.sha256(archive)
    if expected_sha is not None and sha != expected_sha:
        raise AssertionError(f"transport/archive source SHA mismatch: {sha} != {expected_sha}")
    return sha, archive.stat().st_size


def make_on_macos(o165, o162, oracle, args, identity):
    if platform.system() != "Darwin":
        raise AssertionError("producer must be macOS, not " + platform.system())
    if args.archive.exists():
        raise AssertionError("origin archive path is not new")
    with tempfile.TemporaryDirectory(prefix="cmpct-o168-mac-origin-", dir=os.environ.get("RUNNER_TEMP")) as td:
        scratch = Path(td)
        source, restored = scratch / "source", scratch / "same-host"
        old_mask = os.umask(0o022)
        try:
            o162.build_fixture(source)
            source_strict_sha, source_strict = oracle.strict_digest(source)
            if len(source_strict["entries"]) != 10:
                raise AssertionError("source fixture entry census differs from O162")
            if len(source_strict["hardlink_classes"]) != 1:
                raise AssertionError("source fixture lost physical hardlink")
            if sum(e["type"] == "symlink" for e in source_strict["entries"]) != 3:
                raise AssertionError("source fixture symlink census changed")
            create = o162.call_cli(
                ["create", str(source), str(args.archive), "--workers", "1"], scratch
            )
            verify = o162.call_cli(["verify", str(args.archive)], scratch)
            extract = o162.call_cli(["extract", str(args.archive), str(restored)], scratch)
            restored_sha, restored_strict = oracle.strict_digest(restored)
            if restored_strict != source_strict or restored_sha != source_strict_sha:
                raise AssertionError("macOS source-exact same-host reconstruction is not strict")
            if not os.path.samefile(restored / "a-base.bin", restored / "nested/hardcopy.bin"):
                raise AssertionError("same-host macOS hardlink physical ownership lost")
            if os.readlink(restored / "nested/ln-nested") != "leaf.txt":
                raise AssertionError("macOS symlink target not restored")
        finally:
            os.umask(old_mask)
    archive_sha, archive_bytes = prove_original_archive(o165, args.archive)
    portable = o165.portable_manifest(source_strict)
    receipt = {
        "schema": "cmpct-o168-macos-origin-receipt-v1",
        "head": identity["git_head"],
        "provenance": identity,
        "archive_sha256": archive_sha,
        "archive_bytes": archive_bytes,
        "origin_strict_sha256": source_strict_sha,
        "origin_strict_manifest": source_strict,
        "origin_portable_sha256": o165.digest_dict(portable),
        "origin_portable_manifest": portable,
        "same_host_reconstruction_strict": True,
        "installed_create": create,
        "installed_verify": verify,
        "installed_same_host_extract": extract,
        "result": "MACOS_R24_ORIGIN_AND_STRICT_ROUNDTRIP_VERIFIED",
    }
    o165.write_json(args.receipt, receipt)
    return {
        "phase": "macos-origin",
        "head": identity["git_head"],
        "archive_sha256": archive_sha,
        "archive_bytes": archive_bytes,
        "strict_sha256": source_strict_sha,
        "portable_sha256": receipt["origin_portable_sha256"],
        "source_entries": 10,
        "symlink_entries": 3,
        "hardlink_classes": 1,
        "local_strict_equal": True,
        "result": receipt["result"],
    }


def receive_on_linux(o165, o162, oracle, args, identity):
    if platform.system() != "Linux":
        raise AssertionError("receiver must be Linux, not " + platform.system())
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt["schema"] != "cmpct-o168-macos-origin-receipt-v1":
        raise AssertionError("wrong original macOS artifact receipt schema")
    if receipt["head"] != identity["git_head"]:
        raise AssertionError("producer/receiver checkout HEAD mismatch")
    if receipt["provenance"]["source_blobs"] != identity["source_blobs"]:
        raise AssertionError("producer/receiver installed Builder/Reader source drift")
    if receipt["provenance"]["o165_blob"] != identity["o165_blob"]:
        raise AssertionError("producer/receiver comparator source drift")
    archive_sha, size = prove_original_archive(o165, args.archive, receipt["archive_sha256"])
    if size != receipt["archive_bytes"]:
        raise AssertionError("transferred artifact length differs")
    expected_portable = o165.portable_manifest(receipt["origin_strict_manifest"])
    if expected_portable != receipt["origin_portable_manifest"]:
        raise AssertionError("producer portable projection unsupported or corrupt")
    if o165.digest_dict(expected_portable) != receipt["origin_portable_sha256"]:
        raise AssertionError("producer original portable digest mismatch")

    with tempfile.TemporaryDirectory(prefix="cmpct-o168-linux-receiver-", dir=os.environ.get("RUNNER_TEMP")) as td:
        scratch = Path(td)
        restored = scratch / "received"
        verify = o162.call_cli(["verify", str(args.archive)], scratch)
        extract = o162.call_cli(["extract", str(args.archive), str(restored)], scratch)
        strict_sha, strict_actual = oracle.strict_digest(restored)
        projected = o165.portable_manifest(strict_actual)
        projected_sha = o165.digest_dict(projected)
        deltas = o165.physical_deltas(receipt["origin_strict_manifest"], strict_actual)
        if any(
            d["origin_type"] != "symlink"
            or d["receiver_type"] != "symlink"
            or d["changed_fields"] != ["mode"]
            for d in deltas
        ):
            raise AssertionError(f"macOS->Linux fidelity loss outside symlink mode: {deltas}")
        if projected != expected_portable or projected_sha != receipt["origin_portable_sha256"]:
            raise AssertionError("macOS->Linux portable topology mismatch")

        base = restored / "a-base.bin"
        hardcopy = restored / "nested/hardcopy.bin"
        link = restored / "nested/ln-nested"
        hardlink_before = os.path.samefile(base, hardcopy)
        if not hardlink_before or os.readlink(link) != "leaf.txt":
            raise AssertionError("independent physical topology control failed")

        # Hostile control A: same bytes + same mode; different inode relationship.
        old_payload = hardcopy.read_bytes()
        old_mode = stat.S_IMODE(os.lstat(hardcopy).st_mode)
        hardcopy.unlink()
        hardcopy.write_bytes(old_payload)
        hardcopy.chmod(old_mode)
        hardlink_after = os.path.samefile(base, hardcopy)
        _, hardlink_mutant = oracle.strict_digest(restored)
        hardlink_mutant_digest = o165.digest_dict(o165.portable_manifest(hardlink_mutant))
        if hardlink_after or old_payload != base.read_bytes():
            raise AssertionError("hardlink hostile perturbation was not isolated")
        if hardlink_mutant_digest == projected_sha:
            raise AssertionError("portable oracle failed to detect severed hardlink")

        # Restore the precise original hardlink relationship before a second,
        # differently rooted hostile change, so neither negative borrows the other.
        hardcopy.unlink()
        os.link(base, hardcopy)
        _, repaired = oracle.strict_digest(restored)
        if o165.digest_dict(o165.portable_manifest(repaired)) != projected_sha:
            raise AssertionError("hardlink repair failed to restore original topology")

        # Hostile control B: symlink stays a symlink, but targets another in-tree file.
        link.unlink()
        link.symlink_to("../a-base.bin")
        if os.readlink(link) != "../a-base.bin":
            raise AssertionError("symlink-target hostile perturbation not applied")
        _, link_mutant = oracle.strict_digest(restored)
        link_mutant_digest = o165.digest_dict(o165.portable_manifest(link_mutant))
        if link_mutant_digest == projected_sha:
            raise AssertionError("portable oracle ignored a changed symlink target")

    after_sha, after_size = prove_original_archive(o165, args.archive, archive_sha)
    if after_size != size:
        raise AssertionError("original archive changed during Linux validation")
    return {
        "phase": "linux-receiver",
        "head": identity["git_head"],
        "producer_head": receipt["head"],
        "transferred_sha256": after_sha,
        "transferred_bytes": size,
        "macos_origin_strict_sha256": receipt["origin_strict_sha256"],
        "linux_restored_strict_sha256": strict_sha,
        "strict_equal": strict_actual == receipt["origin_strict_manifest"],
        "physical_deltas": deltas,
        "projection": o165.PROJECTION,
        "origin_portable_sha256": receipt["origin_portable_sha256"],
        "linux_portable_sha256": projected_sha,
        "portable_equal": True,
        "hardlink_same_inode": hardlink_before,
        "hostile_hardlink_severed": not hardlink_after,
        "hostile_hardlink_detected": hardlink_mutant_digest != projected_sha,
        "hostile_symlink_target_detected": link_mutant_digest != projected_sha,
        "original_archive_unchanged": True,
        "receiver_strict_manifest": strict_actual,
        "installed_verify": verify,
        "installed_extract": extract,
        "result": "SINGLE_MACOS_ARCHIVE_LINUX_PORTABLE_TOPOLOGY_VERIFIED",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=("producer", "receiver"))
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--receipt", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    try:
        o165 = imported_o165()
        o162 = o165.load_o162()
        identity = validate_identity(o165, o162)
        oracle, _ = o162.load_independent_witnesses()
        if args.role == "producer":
            result = make_on_macos(o165, o162, oracle, args, identity)
        else:
            result = receive_on_linux(o165, o162, oracle, args, identity)
        exit_code = 0
    except Exception as exc:
        exit_code = 1
        result = {
            "role": args.role,
            "result": "FAILED_OR_INFRASTRUCTURE_INCONCLUSIVE",
            "exception": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-6500:],
        }
    from_origin = imported_o165()
    from_origin.write_json(args.output, {"schema": SCHEMA, **result})
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("receiver_strict_manifest", "physical_deltas")},
                     sort_keys=True))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
