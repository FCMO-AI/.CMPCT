from __future__ import annotations

"""Research-only hostile-equivalence gate for the EOCD-indexed ZIP-factor parser.

The EOCD-first parser A/B materially reduces the exact ZIP-factor scan hot path while
preserving the frozen valid candidate. Before any canonical integration, this oracle
requires the faster parser to be at least as strict as the mature parser over a broad,
deterministic malformed-input surface. For every mutation:

* if the mature parser rejects, the candidate must also reject;
* if the mature parser accepts, the candidate must return the exact same semantic object.

The corpus targets local/central/EOCD signatures, counts, offsets, sizes, comments,
flags, methods, names, CRC/sizes, truncation and deterministic bit mutations. No timing
or release credit is granted here. A pass is only a security/productization prerequisite.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import struct
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_eocd_indexed_parser_oracle as EOCD
from experiments import entropygraph_v030_zipfactor_profile as BASE

SEED = 0xC030E0CD
RANDOM_MUTATIONS_PER_FILE = 128
LOCAL = struct.Struct("<IHHHHHIIIHH")
CENTRAL = struct.Struct("<IHHHHHHIIIHHHHHII")
EOCD_HDR = struct.Struct("<IHHHHIIH")


def _first_valid_zip() -> bytes:
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-hostile-source-") as td:
        corpus = Path(td) / "corpus"
        CORPUS.build(corpus)
        source = corpus / "04_deflate_family"
        with tempfile.TemporaryDirectory(prefix="cmpct-zf-hostile-stage-") as sd:
            stage = EXT._normalized_stage(source, Path(sd))
            for p in sorted(stage.rglob("*.zip")):
                raw = p.read_bytes()
                if BASE._parse_zip(raw) is not None:
                    return raw
    raise RuntimeError("no valid ZIP source found")


def _eocd_at(raw: bytes) -> int:
    at = raw.rfind(b"PK\x05\x06")
    if at < 0:
        raise RuntimeError("fixture lacks EOCD")
    return at


def _central_offsets(raw: bytes) -> list[int]:
    e = _eocd_at(raw)
    fields = EOCD_HDR.unpack_from(raw, e)
    cd_offset = int(fields[6])
    count = int(fields[4])
    out = []
    at = cd_offset
    for _ in range(count):
        if at + CENTRAL.size > e:
            break
        vals = CENTRAL.unpack_from(raw, at)
        out.append(at)
        at += CENTRAL.size + int(vals[10]) + int(vals[11]) + int(vals[12])
    return out


def _local_offsets(raw: bytes) -> list[int]:
    offsets = []
    for c_at in _central_offsets(raw):
        offsets.append(int(CENTRAL.unpack_from(raw, c_at)[16]))
    return offsets


def _patch_u16(raw: bytes, at: int, value: int) -> bytes:
    out = bytearray(raw); struct.pack_into("<H", out, at, value & 0xFFFF); return bytes(out)


def _patch_u32(raw: bytes, at: int, value: int) -> bytes:
    out = bytearray(raw); struct.pack_into("<I", out, at, value & 0xFFFFFFFF); return bytes(out)


def _targeted(raw: bytes) -> list[tuple[str, bytes]]:
    rows: list[tuple[str, bytes]] = []
    e = _eocd_at(raw)
    centrals = _central_offsets(raw)
    locals_ = _local_offsets(raw)

    # Whole-archive structural damage.
    for n in (0, 1, 3, 10, 21, 22, 23, len(raw) // 2, max(0, len(raw) - 1)):
        rows.append((f"truncate-{n}", raw[:n]))
    rows.append(("append-garbage", raw + b"X"))
    rows.append(("bad-eocd-signature", _patch_u32(raw, e, 0)))
    rows.append(("eocd-disk", _patch_u16(raw, e + 4, 1)))
    rows.append(("eocd-cd-disk", _patch_u16(raw, e + 6, 1)))
    rows.append(("eocd-count-disk-zero", _patch_u16(raw, e + 8, 0)))
    rows.append(("eocd-count-total-zero", _patch_u16(raw, e + 10, 0)))
    rows.append(("eocd-count-total-plus", _patch_u16(raw, e + 10, len(centrals) + 1)))
    rows.append(("eocd-cd-size-zero", _patch_u32(raw, e + 12, 0)))
    rows.append(("eocd-cd-offset-zero", _patch_u32(raw, e + 16, 0)))
    rows.append(("eocd-comment-len-one", _patch_u16(raw, e + 20, 1)))
    rows.append(("eocd-comment-len-max", _patch_u16(raw, e + 20, 0xFFFF)))

    if centrals:
        c = centrals[0]
        # Central header fixed fields.
        rows.append(("bad-central-signature", _patch_u32(raw, c, 0)))
        rows.append(("central-encrypted", _patch_u16(raw, c + 8, CENTRAL.unpack_from(raw, c)[3] | 1)))
        rows.append(("central-data-descriptor", _patch_u16(raw, c + 8, CENTRAL.unpack_from(raw, c)[3] | 8)))
        rows.append(("central-method-unsupported", _patch_u16(raw, c + 10, 99)))
        rows.append(("central-crc-drift", _patch_u32(raw, c + 16, CENTRAL.unpack_from(raw, c)[7] ^ 1)))
        rows.append(("central-csize-drift", _patch_u32(raw, c + 20, CENTRAL.unpack_from(raw, c)[8] + 1)))
        rows.append(("central-usize-drift", _patch_u32(raw, c + 24, CENTRAL.unpack_from(raw, c)[9] + 1)))
        rows.append(("central-name-len-max", _patch_u16(raw, c + 28, 0xFFFF)))
        rows.append(("central-extra-len-max", _patch_u16(raw, c + 30, 0xFFFF)))
        rows.append(("central-comment-len-max", _patch_u16(raw, c + 32, 0xFFFF)))
        rows.append(("central-local-offset-zero", _patch_u32(raw, c + 42, 0)))
        rows.append(("central-local-offset-oob", _patch_u32(raw, c + 42, len(raw) + 4096)))
        name_len = int(CENTRAL.unpack_from(raw, c)[10])
        if name_len:
            out = bytearray(raw); out[c + CENTRAL.size] ^= 1; rows.append(("central-name-drift", bytes(out)))

    if locals_:
        l = locals_[0]
        fields = LOCAL.unpack_from(raw, l)
        rows.append(("bad-local-signature", _patch_u32(raw, l, 0)))
        rows.append(("local-encrypted", _patch_u16(raw, l + 6, int(fields[2]) | 1)))
        rows.append(("local-data-descriptor", _patch_u16(raw, l + 6, int(fields[2]) | 8)))
        rows.append(("local-method-unsupported", _patch_u16(raw, l + 8, 99)))
        rows.append(("local-crc-drift", _patch_u32(raw, l + 14, int(fields[6]) ^ 1)))
        rows.append(("local-csize-drift", _patch_u32(raw, l + 18, int(fields[7]) + 1)))
        rows.append(("local-usize-drift", _patch_u32(raw, l + 22, int(fields[8]) + 1)))
        rows.append(("local-name-len-max", _patch_u16(raw, l + 26, 0xFFFF)))
        rows.append(("local-extra-len-max", _patch_u16(raw, l + 28, 0xFFFF)))
        name_len = int(fields[9])
        if name_len:
            out = bytearray(raw); out[l + LOCAL.size] ^= 1; rows.append(("local-name-drift", bytes(out)))

    return rows


def _random_mutations(raw: bytes) -> list[tuple[str, bytes]]:
    rng = random.Random(SEED)
    out = []
    # Single-bit mutations deliberately span the entire archive rather than only headers.
    for i in range(RANDOM_MUTATIONS_PER_FILE):
        pos = rng.randrange(len(raw))
        bit = 1 << rng.randrange(8)
        b = bytearray(raw); b[pos] ^= bit
        out.append((f"random-bit-{i:03d}-at-{pos}-mask-{bit}", bytes(b)))
    return out


def _classify(name: str, raw: bytes) -> dict:
    try:
        mature = BASE._parse_zip(raw)
        mature_exc = None
    except Exception as exc:  # A parser exception is a rejection, but preserve it as evidence.
        mature = None; mature_exc = type(exc).__name__
    try:
        candidate = EOCD._candidate_parse_zip(raw)
        candidate_exc = None
    except Exception as exc:
        candidate = None; candidate_exc = type(exc).__name__

    mature_accept = mature is not None
    candidate_accept = candidate is not None
    safe = (not mature_accept and not candidate_accept) or (mature_accept and candidate_accept and candidate == mature)
    return {
        "case": name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mature_accept": mature_accept,
        "candidate_accept": candidate_accept,
        "mature_exception": mature_exc,
        "candidate_exception": candidate_exc,
        "semantic_equal_when_accepted": bool(mature_accept and candidate_accept and candidate == mature),
        "safe_equivalence": bool(safe),
    }


def run() -> dict:
    raw = _first_valid_zip()
    baseline_mature = BASE._parse_zip(raw)
    baseline_candidate = EOCD._candidate_parse_zip(raw)
    if baseline_mature is None or baseline_candidate != baseline_mature:
        raise RuntimeError("valid baseline does not have exact parser equivalence")

    mutations = _targeted(raw) + _random_mutations(raw)
    rows = [_classify(name, mutated) for name, mutated in mutations]
    unsafe = [row for row in rows if not row["safe_equivalence"]]
    accepted_by_mature = sum(1 for row in rows if row["mature_accept"])
    rejected_by_mature = len(rows) - accepted_by_mature
    valid = bool(rows) and not unsafe
    return {
        "schema": "cmpct-v030-zipfactor-eocd-hostile-equivalence-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "timing_credit": False,
            "candidate_may_not_accept_any_input_rejected_by_mature_parser": True,
            "shared_acceptance_requires_exact_semantic_object": True,
            "deterministic_seed": SEED,
        },
        "baseline": {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "exact_valid_equivalence": baseline_candidate == baseline_mature,
        },
        "coverage": {
            "cases": len(rows),
            "targeted_cases": len(_targeted(raw)),
            "random_bit_cases": RANDOM_MUTATIONS_PER_FILE,
            "mature_accepts": accepted_by_mature,
            "mature_rejects": rejected_by_mature,
        },
        "unsafe_cases": unsafe,
        "gate": {
            "experiment_valid": valid,
            "candidate_not_more_permissive": not any(row["candidate_accept"] and not row["mature_accept"] for row in rows),
            "exact_on_shared_acceptance": not any(row["mature_accept"] and row["candidate_accept"] and not row["semantic_equal_when_accepted"] for row in rows),
            "passed": valid,
        },
        "claim_boundary": (
            "Deterministic hostile differential evidence only. A pass permits canonical-integration work but does not "
            "replace fuzzing, reader/recovery, native/Android or final release authority."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-hostile-equivalence.json"))
    a = p.parse_args()
    result = run()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"coverage": result["coverage"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("EOCD parser hostile-equivalence gate failed")


if __name__ == "__main__":
    main()
