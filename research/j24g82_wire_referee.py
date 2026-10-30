#!/usr/bin/env python3
"""J24G82 detached signed-wire and receipt referee. No CMPCT imports."""
from __future__ import annotations
import copy, hashlib, json, struct, sys, os
from pathlib import Path
import msgpack
import zstandard as zstd

FTR = struct.Struct("<8sBBBBQQQ32s")
FMAGIC = b"CMPTF24\x00"
N = 192

CUTS = {"fully_committed", "first_uncommitted_byte", "last_payload_byte",
        "footer_start", "footer_mid", "footer_last_byte", "flipped_sha"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def footer(image: bytes, end: int):
    pos = end - FTR.size
    assert pos >= 0
    m, kind, codec, flags, reserved, compressed, uncompressed, previous, digest = FTR.unpack(image[pos:end])
    assert m == FMAGIC and flags == reserved == 0
    assert kind in (0, 1) and codec in (0, 1)
    assert 0 < compressed <= pos and 0 <= uncompressed <= 1 << 26
    enc = image[pos-compressed:pos]
    raw = enc if codec == 0 else zstd.ZstdDecompressor().decompress(enc, max_output_size=uncompressed)
    assert len(raw) == uncompressed and hashlib.sha256(raw).digest() == digest
    return pos, kind, previous, msgpack.unpackb(raw, raw=False)


def state_digest(names: set[str]) -> str:
    return sha(",".join(sorted(names)).encode())


def audit(receipt: dict, images: dict[str, bytes]) -> dict:
    assert receipt["status"] == "PASS"
    assert receipt["source"]["head"] == images["_head"]
    assert receipt["source"]["writer_blob"] == "71bbc8a989d1da79d0f0dbe44f7f5c39f3304854"
    assert receipt["source"]["source_blob"] == "4b29db0e5818faedc77ea9ff2c32b63c8b6ad2da"
    assert receipt["checked_cases_per_variant"] == 448
    names = receipt["base"]["delete_names"]
    assert len(names) == len(set(names)) == 64
    initial = {f"f{i:05d}.dat" for i in range(N)}
    records = receipt["cases"]["public"]["physical_generations"]
    assert records == receipt["cases"]["owned"]["physical_generations"]
    assert images["public"] == images["owned"]
    image = images["public"]
    lengths = [receipt["base"]["bytes"]] + [x["bytes"] for x in records]
    assert len(lengths) == 65 and all(a < b for a, b in zip(lengths, lengths[1:]))
    assert sha(image[:lengths[0]]) == receipt["base"]["sha256"]
    previous, kind, _, base = footer(image, lengths[0])
    assert kind == 0 and {r[0] for r in base["files"]} == initial

    for g in range(1, 65):
        end = lengths[g]
        assert sha(image[:end]) == records[g-1]["sha256"]
        pos, kind, ancestor, payload = footer(image, end)
        assert ancestor == previous, (g, ancestor, previous)
        if g < 64:
            assert kind == 1 and payload["blobs"] == []
            assert payload["ops"] == [["del", names[g-1]]], (g, payload)
        else:
            assert kind == 0
            assert {r[0] for r in payload["files"]} == initial - set(names)
        previous = pos

    for variant in ("public", "owned"):
        case = receipt["cases"][variant]
        assert case["status"] == "PASS"
        assert case["final_sha256"] == sha(image)
        assert case["final_bytes"] == len(image)
        by_generation = {}
        for row in case["checks"]:
            g, cut = row["generation"], row["cut"]
            assert 1 <= g <= 64 and cut in CUTS and row["outcome"] == "PASS"
            assert cut not in by_generation.setdefault(g, {})
            by_generation[g][cut] = row
            recovered = g if cut == "fully_committed" else g-1
            assert row["recovered_generation"] == recovered
            assert row["state_sha256"] == state_digest(initial - set(names[:recovered]))
            start, end = lengths[g-1:g+1]
            fb = end-FTR.size
            expected_bytes = {
                "fully_committed": end, "first_uncommitted_byte": start+1,
                "last_payload_byte": fb-1, "footer_start": fb,
                "footer_mid": fb+FTR.size//2, "footer_last_byte": end-1,
                "flipped_sha": end,
            }[cut]
            assert row["bytes"] == expected_bytes, (variant, g, cut, row["bytes"])
            if cut in CUTS - {"fully_committed", "flipped_sha"}:
                assert row["prefix_sha256"] == sha(image[:expected_bytes])
            elif cut == "flipped_sha":
                damaged = bytearray(image[:end])
                damaged[-1] ^= 0xA5
                assert row["prefix_sha256"] == sha(damaged)
        assert len(by_generation) == 64
        assert all(set(v) == CUTS for v in by_generation.values())
        assert len(case["checks"]) == 448

    a, b = [receipt["cases"][v]["checks"] for v in ("public", "owned")]
    assert [(r["generation"], r["cut"], r["bytes"], r["recovered_generation"],
             r["state_sha256"]) for r in a] == [
            (r["generation"], r["cut"], r["bytes"], r["recovered_generation"],
             r["state_sha256"]) for r in b]
    return dict(decision="DETACHED_WIRE_REFEREE_PASS",
                raw_footer_count=65, authenticated_generation_prefixes=64,
                per_variant_recovery_states=448, total_recovery_states=896,
                physical_archive_sha256=sha(image))


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence")
    original = json.loads((root/"j24g82-result.json").read_text())
    images = {v:(root/f"j24g80-192-middle-{v}-valid.cmpct").read_bytes()
              for v in ("public", "owned")}
    images["_head"] = (root/"head.txt").read_text().strip()
    result = audit(original, images)
    mutation_cases = [
        lambda r:r["cases"]["public"]["checks"][0].__setitem__("recovered_generation", -1),
        lambda r:r["cases"]["owned"]["checks"][89].__setitem__("state_sha256", "0"*64),
        lambda r:r["cases"]["public"]["physical_generations"][42].__setitem__("sha256", "0"*64),
        lambda r:r["cases"]["owned"]["checks"][227].__setitem__("bytes", 0),
    ]
    for mutate in mutation_cases:
        altered = copy.deepcopy(original)
        mutate(altered)
        try:
            audit(altered, images)
        except (AssertionError, ValueError, KeyError, IndexError, TypeError):
            pass
        else:
            raise AssertionError("forged receipt incorrectly accepted")
    result["forged_receipt_rejections"] = len(mutation_cases)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
