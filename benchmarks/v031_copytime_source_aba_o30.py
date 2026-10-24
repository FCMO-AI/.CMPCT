#!/usr/bin/env python3
"""O30 research-only: test source ABA during sealed CMPCT copy, not after it.

The frozen prediction lives in docs/v031-research/2026-10-24-copytime-source-aba-o30-prereg.md.
Never confuse scientific harness PASS with approval of the product or security claim.
"""
from __future__ import annotations

import argparse
import binascii
import errno
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from cmpct.codec import BHDR
from cmpct.reader import CMPCT
from v031_pack_physical_sha_court import archive_bytes
from v031_verify_extract_source_lifetime_o23 import digest, in_place, view
from v031_sealed_memfd_source_o26 import BLOCK, FLAGS, PAGE, hash_fd, proc_path


def crc_equal_mutant(original: bytes) -> tuple[bytes, dict]:
    """Change data inside copy block 2; solve 32-bit CRC compensation over 4 bytes.

    CRC32's effect of flipping each independent bit is linear over GF(2).
    Basis elimination solves for exactly the desired CRC difference; the later
    SHA-256 difference is not subject to that 32-bit linearity.
    """
    edit = 1_400_000
    patch = edit + 64
    assert len(original) == 4 * 1024 * 1024
    assert BLOCK < edit < patch + 4 < 2 * BLOCK - 1024
    changed = bytearray(original)
    changed[edit] ^= 0x40
    original_crc = binascii.crc32(original) & 0xFFFFFFFF
    base_crc = binascii.crc32(changed) & 0xFFFFFFFF
    columns: dict[int, tuple[int, int]] = {}
    for bit in range(32):
        trial = bytearray(changed)
        trial[patch + bit // 8] ^= (1 << (bit % 8))
        delta = (binascii.crc32(trial) & 0xFFFFFFFF) ^ base_crc
        mask = 1 << bit
        while delta:
            top = delta.bit_length() - 1
            if top not in columns:
                columns[top] = (delta, mask)
                break
            vector, existing_mask = columns[top]
            delta ^= vector
            mask ^= existing_mask
        if not delta:
            raise AssertionError("CRC basis unexpectedly linearly dependent")
    delta = original_crc ^ base_crc
    solution = 0
    while delta:
        top = delta.bit_length() - 1
        if top not in columns:
            raise AssertionError("CRC compensation not representable")
        vector, mask = columns[top]
        delta ^= vector
        solution ^= mask
    for bit in range(32):
        if solution & (1 << bit):
            changed[patch + bit // 8] ^= (1 << (bit % 8))
    mutant = bytes(changed)
    assert mutant != original and digest(mutant) != digest(original)
    assert (binascii.crc32(mutant) & 0xFFFFFFFF) == original_crc
    assert original[:edit] == mutant[:edit]
    assert original[patch + 4:] == mutant[patch + 4:]
    return mutant, {
        "change_offsets_in_logical_payload": [edit, patch, patch + 4],
        "crc32_original_equals_mutant": original_crc,
        "sha256_original": digest(original),
        "sha256_mutant": digest(mutant),
        "crc_compensation_bitmask_hex": f"{solution:08x}",
    }


def source_writer(path: Path, image: Path) -> None:
    """Independent subprocess; preserve source dev/inode/length using pwrite."""
    expected = image.read_bytes()
    fd = os.open(path, os.O_RDWR)
    try:
        before = os.fstat(fd)
        assert before.st_size == len(expected), "writer must not resize source"
        in_place(fd, expected)
        after = os.fstat(fd)
        assert (before.st_dev, before.st_ino, before.st_size) == (
            after.st_dev, after.st_ino, after.st_size
        ), "writer unexpectedly rebound or resized source"
    finally:
        os.close(fd)
    assert digest(path.read_bytes()) == digest(expected)


def mutate_in_child(path: Path, image: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()),
         "--writer", "--source", str(path), "--image", str(image)],
        capture_output=True, text=True, check=True,
    )
    output = json.loads(result.stdout)
    assert output["sha256"] == digest(image.read_bytes())
    return output


def sealed_copy_with_aba(source: Path, archive_b: Path, archive_a: Path) -> tuple[int, dict]:
    """Explicit interleaving: copy A block0, B block1, A remaining blocks.

    This tests the possibility of a writer interleaving, not the probability
    of winning a timing race. The writer is a separate process each time.
    """
    fd = os.memfd_create("cmpct-o30-aba", os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
    copied = 0
    stage = []
    writes = []
    try:
        with source.open("rb") as stream:
            index = 0
            while chunk := stream.read(BLOCK):
                offset = 0
                while offset < len(chunk):
                    sent = os.write(fd, chunk[offset:])
                    if sent <= 0:
                        raise OSError("short memfd write")
                    offset += sent
                copied += len(chunk)
                stage.append({
                    "block": index,
                    "bytes": len(chunk),
                    "sha256": digest(chunk),
                })
                if index == 0:
                    writes.append(mutate_in_child(source, archive_b))
                elif index == 1:
                    writes.append(mutate_in_child(source, archive_a))
                index += 1
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, FLAGS)
        assert fcntl.fcntl(fd, fcntl.F_GET_SEALS) & FLAGS == FLAGS
        assert os.fstat(fd).st_size == copied
        return fd, {
            "copy_read_bytes": copied,
            "copy_write_bytes": copied,
            "blocks_copied": stage,
            "writer_interleavings": writes,
            "memfd_minimum_page_charge": math.ceil(copied / PAGE) * PAGE,
        }
    except BaseException:
        os.close(fd)
        raise


def verify_and_extract(archive: Path, destination: Path, expected: bytes) -> dict:
    with CMPCT(archive) as reader:
        verified = reader.verify()
        assert verified == 1, f"expected one RAW file, got {verified}"
        reader.extractall(destination, metadata=False)
    actual = view(destination, False)
    assert actual == expected
    return {"logical_sha256": digest(actual), "physical_verify": "PASS"}


def main() -> dict:
    original = hashlib.shake_256(b"CMPCT-O30-A-original-contents").digest(
        4 * 1024 * 1024
    )
    mutant, crc = crc_equal_mutant(original)
    archive_a = archive_bytes(original, original, packed=False)
    archive_b = archive_bytes(mutant, mutant, packed=False)
    assert archive_a != archive_b and len(archive_a) == len(archive_b)
    assert archive_a[:64] == archive_b[:64]  # identical primary index commitment
    expected_hybrid = (archive_a[:BLOCK] + archive_b[BLOCK:2 * BLOCK] +
                       archive_a[2 * BLOCK:])
    assert expected_hybrid != archive_a and expected_hybrid != archive_b
    assert len(expected_hybrid) == len(archive_a)

    with tempfile.TemporaryDirectory(prefix="cmpct-o30-aba-") as temp:
        root = Path(temp)
        source = root / "mutable.cmpct"
        bpath = root / "version-b.cmpct"
        apath = root / "version-a.cmpct"
        source.write_bytes(archive_a)
        apath.write_bytes(archive_a)
        bpath.write_bytes(archive_b)
        control_a = verify_and_extract(
            apath, root / "control-a", original
        )
        control_b = verify_and_extract(
            bpath, root / "control-b", mutant
        )
        source_before = source.stat()
        source_sha_before = digest(source.read_bytes())
        assert source_sha_before == digest(archive_a)
        fd, costs = sealed_copy_with_aba(source, bpath, apath)
        try:
            source_after = source.stat()
            source_sha_after = digest(source.read_bytes())
            snapshot_hash = hash_fd(fd)
            assert source_sha_after == source_sha_before
            assert (source_before.st_dev, source_before.st_ino,
                    source_before.st_size) == (
                source_after.st_dev, source_after.st_ino,
                source_after.st_size
            )
            assert snapshot_hash == digest(expected_hybrid)
            assert snapshot_hash not in (digest(archive_a), digest(archive_b))
            assert os.pread(fd, len(archive_a), 0) == expected_hybrid
            assert costs["copy_read_bytes"] == len(archive_a)
            # The lower-tier read must succeed with a CRC collision, so a
            # later rejection proves a *SHA-specific* integrity boundary.
            with CMPCT(proc_path(fd)) as reader:
                assert reader.read("direct.md") == mutant
                record = reader.record_base + int(reader.blobs[0][0])
                header_h = BHDR.unpack_from(expected_hybrid, record)
                header_a = BHDR.unpack_from(archive_a, record)
                header_b = BHDR.unpack_from(archive_b, record)
                assert header_h[-2] == header_a[-2] == header_b[-2]
                assert header_h[-1] == header_a[-1]
                assert header_a[-1] != header_b[-1]
                try:
                    reader.verify()
                except (IOError, OSError, ValueError) as exc:
                    assert "SHA-256 verification failure" in str(exc), (
                        f"wrong failure layer: {type(exc).__name__}: {exc}"
                    )
                    verified_hybrid = "REJECTED_EXACT_PHYSICAL_SHA"
                else:
                    raise AssertionError("strong verify accepted CRC-consistent hybrid")

            refused = False
            destination = root / "hybrid-not-published"
            try:
                verify_and_extract(proc_path(fd), destination, mutant)
            except (IOError, OSError, ValueError) as exc:
                refused = "SHA-256 verification failure" in str(exc)
            assert refused, "verified extraction did not refuse hybrid SHA"
            assert not destination.exists(), "hybrid data became visible"

            # Source ABA fully restored: an independently opened Reader
            # verifies A even though the immutable H continues to differ.
            restored = verify_and_extract(source, root / "restored-a", original)
            try:
                os.pwrite(fd, b"!", 0)
            except OSError as exc:
                assert exc.errno in (errno.EPERM, errno.EACCES)
                seal_write_denied = exc.errno
            else:
                raise AssertionError("completed snapshot was not sealed")
            assert hash_fd(fd) == snapshot_hash
            return {
                "status": "PASS",
                "decision": "SOURCE_ABA_START_END_SHA_DOES_NOT_PROVE_ATOMIC_CLONE",
                "scientific_scope": "CONTROLLED_SAME_USER_CONCURRENT_INTERLEAVING_LINUX",
                "source_head_sha256": source_sha_before,
                "source_tail_sha256": source_sha_after,
                "source_inode_and_size_stable": True,
                "source_sha_before_after_equal": True,
                "source_ctime_ns_changed": (
                    source_before.st_ctime_ns != source_after.st_ctime_ns
                ),
                "archive_a_sha256": digest(archive_a),
                "archive_b_sha256": digest(archive_b),
                "sealed_hybrid_archive_sha256": snapshot_hash,
                "sealed_hybrid_not_either_source_generation": True,
                "physical_crc32_collision": crc,
                "baseline_a": control_a,
                "baseline_b": control_b,
                "post_aba_source": restored,
                "hybrid_crc_tier_read": "PASS_MUTANT_LOGICAL_BYTES",
                "hybrid_verify": verified_hybrid,
                "verified_extraction": "REJECTED_BEFORE_PUBLICATION",
                "memfd_write_denied_errno": seal_write_denied,
                "sealed_memfd_minimum_page_charge": costs["memfd_minimum_page_charge"],
                "source_archive_bytes": len(archive_a),
                "costs": costs,
                "limits": [
                    "Deterministic interleaving by an authorized separate writer, not a timing race probability",
                    "Source ctime changes and was NOT claimed equal; SHA before/after is equal",
                    "Snapshot strong SHA rejects H, but does not authenticate provenance",
                    "No arbitrary concurrent writer isolation, platform portability, tree publication or recovery",
                    "N-byte full memfd copy charge; no product or compression performance claim",
                ],
            }
        finally:
            os.close(fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--writer", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--out", type=Path)
    options = parser.parse_args()
    if options.writer:
        assert options.source and options.image
        source_writer(options.source, options.image)
        print(json.dumps({"sha256": digest(options.image.read_bytes()),
                          "pid": os.getpid(), "mode": "separate_subprocess"}))
    else:
        result = main()
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if options.out:
            options.out.parent.mkdir(parents=True, exist_ok=True)
            options.out.write_text(encoded)
        print(encoded)
