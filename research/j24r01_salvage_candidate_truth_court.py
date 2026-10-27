"""J24R01: source-exact physical-salvage trust-label acceptance.

A PASS verifies honest classification, NOT successful content recovery.
Preregistration: docs/v031-research/2026-10-27-j24r01-recovery-trust-prereg.md
Inherited independently hosted falsifier: O0 PR #291 / Issue #292.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
from cmpct.core import Builder, CMPCT, recover_blob_records


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def at(records: list[dict], offset: int) -> dict:
    found = [r for r in records if r["offset"] == offset]
    assert len(found) == 1, (offset, found)
    row = found[0]
    assert row["verified"] is False, ("salvage incorrectly claims authenticated contents", row)
    assert isinstance(row["sha256"], str) and len(row["sha256"]) == 64, row
    return row


def main() -> None:
    with TemporaryDirectory(prefix="cmpct-j24r01-") as td:
        root = Path(td)
        tree = root / "tree"
        tree.mkdir()
        raw = hashlib.shake_256(b"J24R01-RAW-SALVAGE-ENTROPY-CONTROL").digest(65536)
        (tree / "opaque.bin").write_bytes(raw)
        archive = root / "actual.cmpct"
        Builder(tree).build(archive)

        with CMPCT(archive) as rd:
            assert rd.read("opaque.bin") == raw
            matches = [b for b in rd.blobs if b[3] == CODEC_RAW and b[1] == len(raw)]
            assert len(matches) == 1, matches
            off = rd.record_base + matches[0][0]
            h = BHDR.unpack_from(rd.mm, off)
            assert h[0] == BMAGIC and h[1] == CODEC_RAW
            start = off + BHDR.size + h[6]
            assert h[4] == len(raw) and h[5] == len(raw)
            declared = bytes(h[-1]).hex()
            assert declared == digest(raw)

        original = at(recover_blob_records(archive), off)
        assert original["sha256"] == declared
        assert original["usize"] == original["csize"] == len(raw)
        assert "sha256_verified" not in original  # no second ambiguous authority

        with archive.open("r+b") as f:
            f.seek(start + 101)
            b = f.read(1)
            assert len(b) == 1
            f.seek(start + 101)
            f.write(bytes([b[0] ^ 0x01]))
        corrupted_raw = bytearray(raw)
        corrupted_raw[101] ^= 0x01
        assert digest(corrupted_raw) != declared
        corrupted = at(recover_blob_records(archive), off)
        assert corrupted == original, "scanner discovery must remain independent of payload authentication"

        rejected = False
        try:
            with CMPCT(archive) as rd:
                rd.read("opaque.bin")
        except (IOError, OSError, ValueError):
            rejected = True
        assert rejected, "authentic Reader must reject corrupted RAW data"

        # Counterfeit outside the committed generation with falsified CRC and SHA.
        counterfeit_payload = b"not-committed-payload" * 17
        forged_off = archive.stat().st_size
        bogus_sha = bytes.fromhex("42" * 32)
        forged_header = BHDR.pack(
            BMAGIC, CODEC_RAW, 0, 0, len(counterfeit_payload),
            len(counterfeit_payload), 0, 0, bogus_sha,
        )
        with archive.open("ab") as f:
            f.write(forged_header + counterfeit_payload)
        forged = at(recover_blob_records(archive), forged_off)
        assert forged["sha256"] == bogus_sha.hex()
        assert forged["sha256"] != digest(counterfeit_payload)

        # Even a self-consistent header outside every committed generation has NOT
        # been proven to belong to the archive's authenticated logical tree.
        orphan_payload = b"self-consistent-but-uncommitted" * 17
        orphan_off = archive.stat().st_size
        orphan_header = BHDR.pack(
            BMAGIC, CODEC_RAW, 0, 0, len(orphan_payload),
            len(orphan_payload), 0, binascii.crc32(orphan_payload) & 0xffffffff,
            hashlib.sha256(orphan_payload).digest(),
        )
        with archive.open("ab") as f:
            f.write(orphan_header + orphan_payload)
        orphan = at(recover_blob_records(archive), orphan_off)
        assert orphan["sha256"] == digest(orphan_payload)
        assert orphan["verified"] is False

        direct = recover_blob_records(archive)
        proc = subprocess.run(
            [sys.executable, "-m", "cmpct", "recover-blobs", str(archive)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
        )
        cli = json.loads(proc.stdout)
        assert cli == direct, "CLI and library must export the same evidence tier"
        assert all(r["verified"] is False for r in cli)
        assert not any(r["verified"] is True for r in cli)

        evidence = {
            "classification": "HEADER_CANDIDATE_LABEL_PASS",
            "evidence_tier": "product-behavior-positive/forensic-header-only",
            "logical_raw_sha256": declared,
            "corrupted_actual_sha256": digest(corrupted_raw),
            "original_offset": off,
            "forged_offset": forged_off,
            "orphan_offset": orphan_off,
            "original_flag": original["verified"],
            "corrupted_flag": corrupted["verified"],
            "forged_flag": forged["verified"],
            "self_consistent_uncommitted_flag": orphan["verified"],
            "reader_rejected_corruption": rejected,
            "candidate_count": len(direct),
            "cli_exact_match": cli == direct,
            "raw_full_scanner_ram_bound": "UNBOUNDED: source reads entire archive into memory",
            "content_authentication_performed_by_salvage": False,
            "committed_generation_membership_proven": False,
        }
        print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
