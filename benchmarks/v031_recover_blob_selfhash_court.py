"""Independent scientific O0: salvage's framed records versus authenticated payloads.

The real CMPCT Builder, Reader and public recover_blob_records are unchanged; the
test mutates one physical RAW payload and constructs a separate unsigned forged record.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from cmpct.core import Builder, CMPCT, recover_blob_records
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_recovered(records: list[dict], pos: int) -> dict:
    matching = [r for r in records if r["offset"] == pos]
    if len(matching) != 1:
        raise AssertionError(f"unexpected candidates at raw physical offset {pos}: {matching!r}")
    return matching[0]


def main() -> None:
    with TemporaryDirectory(prefix="cmpct-salvage-selfhash-") as tmp:
        base = Path(tmp)
        src = base / "original"
        src.mkdir()
        payload = hashlib.shake_256(b"CMPCT-GENERIC-SALVAGE-RAW-CONTROL").digest(65536)
        (src / "opaque.bin").write_bytes(payload)
        archive = base / "real.cmpct"
        Builder(src).build(archive)
        with CMPCT(archive) as reader:
            assert reader.read("opaque.bin") == payload
            matching = [
                (i, b) for i, b in enumerate(reader.blobs)
                if b[3] == CODEC_RAW and b[1] == len(payload)
            ]
            assert len(matching) == 1, matching
            i, blob = matching[0]
            physical_offset = reader.record_base + blob[0]
            fields = BHDR.unpack_from(reader.mm, physical_offset)
            assert fields[0] == BMAGIC and fields[1] == CODEC_RAW
            payload_offset = physical_offset + BHDR.size + int(fields[6])
            assert fields[4] == len(payload) and fields[5] == len(payload)
            declared_hash = bytes(fields[-1]).hex()
        before = find_recovered(recover_blob_records(archive), physical_offset)
        assert before["sha256"] == declared_hash == digest(payload)

        # Keep all declared framing/digests untouched and flip one byte of the *real* stored RAW body.
        with archive.open("r+b") as f:
            f.seek(payload_offset + 123)
            original = f.read(1)
            assert len(original) == 1
            f.seek(payload_offset + 123)
            f.write(bytes([original[0] ^ 0x40]))
        tampered = archive.read_bytes()
        actual_hash = digest(tampered[payload_offset:payload_offset + len(payload)])
        assert actual_hash != declared_hash
        after = find_recovered(recover_blob_records(archive), physical_offset)

        reader_refused = False
        reader_exc = None
        try:
            with CMPCT(archive) as reader:
                reader.read("opaque.bin")
        except (IOError, OSError, ValueError) as exc:
            reader_refused = True
            reader_exc = type(exc).__name__
        assert reader_refused, "Reader did not reject tampered payload"

        # Independent syntactically valid framing outside the committed generation.
        # Its declared SHA and CRC intentionally do not match its actual RAW bytes.
        fake = b"untrusted-standalone-physical-record" * 11
        fake_header = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(fake), len(fake), 0, 0, b"\x42" * 32)
        fake_offset = archive.stat().st_size
        with archive.open("ab") as f:
            f.write(fake_header + fake)
        forged = find_recovered(recover_blob_records(archive), fake_offset)

        outcome = {
            "authority": "FCMO-AI/.CMPCT original development Writer blob 964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c",
            "scenario": "actual authentic r24 archive + RAW payload corruption + appended framed counterfeit",
            "original_control": {
                "blob_physical_offset": physical_offset,
                "declared_sha256": declared_hash,
                "recovered_record_sha256": before["sha256"],
                "reader_accepts": True,
            },
            "corrupted_original": {
                "offset": physical_offset,
                "declared_sha256": after["sha256"],
                "actual_payload_sha256": actual_hash,
                "reported_by_recovery": after == before,
                "reader_rejected": reader_refused,
                "reader_exception": reader_exc,
            },
            "forged_uncommitted_record": {
                "offset": fake_offset,
                "reported_sha256": forged["sha256"],
                "actual_payload_sha256": digest(fake),
                "sha_matches": forged["sha256"] == digest(fake),
                "record_returned": True,
                "committed": False,
            },
            "decision": (
                "SALVAGE_RETURNS_UNVERIFIED_FRAMED_BLOBS"
                if reader_refused
                and after == before
                and forged["sha256"] != digest(fake)
                else "HYPOTHESIS_NOT_CONFIRMED"
            ),
            "claim_scope": "The callable enumerates plausible blob headers, not cryptographically verified recovered content.",
        }
        print(json.dumps(outcome, indent=2, sort_keys=True))
        assert outcome["decision"] == "SALVAGE_RETURNS_UNVERIFIED_FRAMED_BLOBS"


if __name__ == "__main__":
    main()
