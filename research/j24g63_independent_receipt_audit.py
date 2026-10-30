#!/usr/bin/env python3
"""Independent J24G63 source-free referee for retained raw receipts and r24 wires.

Does not import cmpct or reuse the J24G63 experiment's Python statistics helpers.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import statistics
import struct
import sys

import msgpack
import zstandard as zstd

FTR = struct.Struct("<8sBBBBQQQ32s")
FMAGIC = b"CMPTF24\0"
KINDS = ("put", "delete")
NS = (512, 2048)
DEPTHS = (1, 16, 32, 63)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_wire(raw: bytes, footer: int) -> list[tuple[int, object]]:
    sequence = []
    seen = set()
    cursor = footer
    while cursor:
        assert cursor not in seen and 0 <= cursor <= len(raw) - FTR.size
        seen.add(cursor)
        magic, kind, codec, flags, reserved, cs, us, prev, digest = (
            FTR.unpack_from(raw, cursor))
        assert magic == FMAGIC and kind in (0, 1) and codec in (0, 1)
        assert flags == 0 and reserved == 0 and 0 < cs <= cursor
        assert 0 < us <= 128 * 1024 * 1024
        assert prev == 0 or 0 < prev < cursor
        encoded = raw[cursor - cs:cursor]
        plain = encoded if codec == 0 else zstd.ZstdDecompressor().decompress(
            encoded, max_output_size=us)
        assert len(plain) == us and hashlib.sha256(plain).digest() == digest
        document = msgpack.unpackb(plain, raw=False)
        sequence.append((kind, document))
        if kind == 0:
            break
        cursor = prev
    assert sequence and sequence[-1][0] == 0
    return sequence


def audit(data: dict, path: Path, expected_head: str, physical: bool = True) -> dict:
    assert data["source"]["head"] == expected_head
    assert set(data["corpus"]) == set(KINDS)
    observed = data["samples"]
    # Not an origin signature: a source-neutral digest simply detects single-field drift.
    expected_raw_sha = hashlib.sha256(json.dumps(
        observed, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert data["raw_samples_sha256"] == expected_raw_sha
    assert len(observed) == 256, len(observed)
    seen_keys = set()
    for kind in KINDS:
        assert set(data["corpus"][kind]) == {"512", "2048"}
        for n in NS:
            case = data["corpus"][kind][str(n)]
            assert case["n"] == n and case["kind"] == kind
            assert set(case["snapshots"]) == {str(d) for d in DEPTHS}
            for d in DEPTHS:
                cell = case["snapshots"][str(d)]
                assert cell["kind"] == kind and cell["n"] == n and cell["depth"] == d
                assert cell["expected_rows"] == (n if kind == "put" else n + 63 - d)
                assert cell["semantics"]["verified_members"] == cell["expected_rows"]
                assert cell["checkpoint_premium_bytes"] == (
                    cell["archive_bytes"]["checkpoint"] - cell["archive_bytes"]["chain"])
                assert len(cell["wire"]) == d
                total = n if kind == "put" else n + 63
                prospective_names = [f"f{((2*i + 1)*total)//126:04d}.dat"
                                     for i in range(63)]
                assert len(set(prospective_names)) == 63
                assert cell["selected_paths"] == prospective_names[:d]
                assert [x["name"] for x in cell["wire"]] == list(reversed(prospective_names[:d]))
                assert {x["tag"] for x in cell["wire"]} == (
                    {"put"} if kind == "put" else {"del"})
                per_case = [x for x in observed if
                            (x["kind"], x["n"], x["depth"]) == (kind, n, d)]
                assert len(per_case) == 16
                for block in range(4):
                    expect = (("chain", "checkpoint", "checkpoint", "chain") if
                              block % 2 == 0 else ("checkpoint", "chain", "chain", "checkpoint"))
                    ordered = sorted((x for x in per_case if x["block"] == block),
                                     key=lambda x: x["position"])
                    assert len(ordered) == 4
                    assert tuple(x["variant"] for x in ordered) == expect
                    for row in ordered:
                        key = (kind, n, d, row["block"], row["position"])
                        assert key not in seen_keys
                        seen_keys.add(key)
                        assert type(row["open_wall_ns"]) is int and row["open_wall_ns"] >= 0
                        assert type(row["open_cpu_ns"]) is int and row["open_cpu_ns"] >= 0
                        assert row["rows"] == cell["expected_rows"]
                        assert row["delta_depth"] == (d if row["variant"] == "chain" else 0)
                a = [x for x in per_case if x["variant"] == "chain"]
                b = [x for x in per_case if x["variant"] == "checkpoint"]
                assert len(a) == len(b) == 8
                m = cell["measurements"]
                aw = statistics.median(x["open_wall_ns"] for x in a)
                bw = statistics.median(x["open_wall_ns"] for x in b)
                assert m["chain_wall_ns_median"] == aw
                assert m["checkpoint_wall_ns_median"] == bw
                assert m["delta_wall_ns"] == aw - bw
                assert abs(m["delta_fraction_of_chain"] - (aw-bw)/aw) <= 1e-12
                assert abs(m["chain_to_checkpoint_wall_ratio"] - aw/bw) <= 1e-12
                assert m["chain_cpu_ns_median"] == statistics.median(x["open_cpu_ns"] for x in a)
                assert m["checkpoint_cpu_ns_median"] == statistics.median(x["open_cpu_ns"] for x in b)
    assert len(seen_keys) == 256
    for kind in KINDS:
        m = data["corpus"][kind]["2048"]["snapshots"]["63"]["measurements"]
        expected = ("MATERIAL" if
                    m["delta_wall_ns"] >= 3_000_000 and m["delta_fraction_of_chain"] >= 0.10
                    else "NOT_MATERIAL")
        decision = data["decisions"][kind]
        assert decision["decision"] == expected
        assert abs(decision["threshold"]["observed_absolute_ms"] -
                   m["delta_wall_ns"] / 1e6) <= 1e-9
    physical_witness = {}
    if physical:
        for kind in KINDS:
            snap = data["corpus"][kind]["2048"]["snapshots"]["63"]
            paths = snap["saved_physical"]
            chain_path = path.parent / paths["chain"]
            checkpoint_path = path.parent / paths["checkpoint"]
            assert chain_path.is_file() and checkpoint_path.is_file()
            assert sha_file(chain_path) == snap["archive_sha256"]["chain"]
            assert sha_file(checkpoint_path) == snap["archive_sha256"]["checkpoint"]
            chain_bytes = chain_path.read_bytes()
            checkpoint_bytes = checkpoint_path.read_bytes()
            # The private checkpoint must merely append a footer; never mutate physical content.
            assert checkpoint_bytes.startswith(chain_bytes)
            assert len(checkpoint_bytes) - len(chain_bytes) == snap["checkpoint_premium_bytes"]
            chain_ledger = parse_wire(chain_bytes, snap["wire"][0]["pos"])
            assert len(chain_ledger) == 64
            assert all(k == 1 for k, _ in chain_ledger[:63])
            assert chain_ledger[63][0] == 0
            total = 2048 if kind == "put" else 2111
            selected = [f"f{((2*i + 1)*total)//126:04d}.dat" for i in range(63)]
            for i, (k, delta) in enumerate(chain_ledger[:63]):
                ops = delta.get("ops")
                assert isinstance(ops, list) and len(ops) == 1
                op = ops[0]
                assert op[0] == ("put" if kind == "put" else "del")
                name = op[1][0] if kind == "put" else op[1]
                assert name == selected[62-i]
            # Exact final footer at EOF (not a magic substring guessed from unrelated bytes).
            chk_pos = len(checkpoint_bytes) - FTR.size
            final = parse_wire(checkpoint_bytes, chk_pos)
            assert len(final) == 1 and final[0][0] == 0
            assert len(final[0][1]["files"]) == 2048
            physical_witness[kind] = {
                "chain_sha256": snap["archive_sha256"]["chain"],
                "checkpoint_sha256": snap["archive_sha256"]["checkpoint"],
                "checkpoint_premium_bytes": snap["checkpoint_premium_bytes"],
                "operations": 63,
            }
    return {"status": "PASS", "head": expected_head, "samples": len(seen_keys),
            "physical": physical_witness, "decisions": data["decisions"]}


def expect_bad(prototype: dict, result: Path, head: str, mutate) -> None:
    forged = copy.deepcopy(prototype)
    mutate(forged)
    try:
        audit(forged, result, head, True)
    except (AssertionError, KeyError, IndexError, TypeError, ValueError):
        return
    raise AssertionError("corrupt independent receipt unexpectedly accepted")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py evidence/result.json expected_head evidence/audit.json")
    result = Path(sys.argv[1])
    expected_head = sys.argv[2]
    output = Path(sys.argv[3])
    doc = json.loads(result.read_text())
    good = audit(doc, result, expected_head)
    expect_bad(doc, result, expected_head,
               lambda d: d["samples"][0].__setitem__("open_wall_ns",
                                                       d["samples"][0]["open_wall_ns"] + 100_000_000))
    expect_bad(doc, result, expected_head,
               lambda d: d["corpus"]["put"]["2048"]["snapshots"]["63"]["archive_sha256"].__setitem__(
                   "chain", "0"*64))
    expect_bad(doc, result, expected_head,
               lambda d: d["corpus"]["delete"]["2048"]["snapshots"]["63"].__setitem__(
                   "checkpoint_premium_bytes", 0))
    expect_bad(doc, result, expected_head,
               lambda d: d["corpus"]["put"]["2048"]["snapshots"]["63"]["wire"][0].__setitem__(
                   "name", "not-this-file.dat"))
    good["hostile_receipts_rejected"] = 4
    output.write_text(json.dumps(good, indent=2, sort_keys=True) + "\n")
    print("J24G63_INDEPENDENT_AUDIT_PASS", expected_head, "256 raw samples, 4/4 forged receipts rejected")


if __name__ == "__main__":
    main()
