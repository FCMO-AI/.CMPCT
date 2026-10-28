from __future__ import annotations

"""Research-only hostile + valid-generalization gate for the EOCD-indexed ZIP-factor parser.

The faster parser may never accept an input rejected by the mature parser, and every archive
accepted by both must yield the exact same semantic object. The differential corpus combines
a frozen valid ZIP, independently generated supported ZIP variants, targeted structural damage,
and deterministic whole-archive bit mutations. No timing or release credit is granted here.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import random
import struct
import tempfile
import zipfile

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


def _valid_variants() -> list[tuple[str, bytes]]:
    """Generate supported ordinary ZIP shapes independent of the frozen workload."""
    out: list[tuple[str, bytes]] = []
    payloads = [b"", b"a", b"hello\n" * 7, bytes(range(256)) * 3, b"A" * 8192]
    for compression, label in ((zipfile.ZIP_STORED, "stored"), (zipfile.ZIP_DEFLATED, "deflate")):
        for count in (1, 2, 5):
            bio = io.BytesIO()
            with zipfile.ZipFile(bio, "w", compression=compression, compresslevel=9 if compression == zipfile.ZIP_DEFLATED else None) as zf:
                zf.comment = (f"cmpct-{label}-{count}").encode()
                for i in range(count):
                    info = zipfile.ZipInfo(f"dir-{i % 2}/member-{i}-caf\u00e9.txt", date_time=(2024, 1 + i, 2 + i, 3, 4, 6))
                    info.compress_type = compression
                    info.extra = b"\x99\x99\x02\x00OK"
                    info.comment = f"member-{i}".encode()
                    zf.writestr(info, payloads[i % len(payloads)])
            out.append((f"valid-{label}-{count}", bio.getvalue()))

    # Mixed stored/deflated methods in one central directory.
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("stored.bin", b"S" * 1024, compress_type=zipfile.ZIP_STORED)
        zf.writestr("deflated.bin", b"D" * 4096, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    out.append(("valid-mixed-methods", bio.getvalue()))
    return out


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
    return [int(CENTRAL.unpack_from(raw, c_at)[16]) for c_at in _central_offsets(raw)]


def _patch_u16(raw: bytes, at: int, value: int) -> bytes:
    out = bytearray(raw); struct.pack_into("<H", out, at, value & 0xFFFF); return bytes(out)


def _patch_u32(raw: bytes, at: int, value: int) -> bytes:
    out = bytearray(raw); struct.pack_into("<I", out, at, value & 0xFFFFFFFF); return bytes(out)


def _targeted(raw: bytes) -> list[tuple[str, bytes]]:
    rows: list[tuple[str, bytes]] = []
    e = _eocd_at(raw)
    centrals = _central_offsets(raw)
    locals_ = _local_offsets(raw)
    for n in (0, 1, 3, 10, 21, 22, 23, len(raw) // 2, max(0, len(raw) - 1)):
        rows.append((f"truncate-{n}", raw[:n]))
    rows += [
        ("append-garbage", raw + b"X"),
        ("bad-eocd-signature", _patch_u32(raw, e, 0)),
        ("eocd-disk", _patch_u16(raw, e + 4, 1)),
        ("eocd-cd-disk", _patch_u16(raw, e + 6, 1)),
        ("eocd-count-disk-zero", _patch_u16(raw, e + 8, 0)),
        ("eocd-count-total-zero", _patch_u16(raw, e + 10, 0)),
        ("eocd-count-total-plus", _patch_u16(raw, e + 10, len(centrals) + 1)),
        ("eocd-cd-size-zero", _patch_u32(raw, e + 12, 0)),
        ("eocd-cd-offset-zero", _patch_u32(raw, e + 16, 0)),
        ("eocd-comment-len-one", _patch_u16(raw, e + 20, 1)),
        ("eocd-comment-len-max", _patch_u16(raw, e + 20, 0xFFFF)),
    ]
    if centrals:
        c = centrals[0]; f = CENTRAL.unpack_from(raw, c)
        rows += [
            ("bad-central-signature", _patch_u32(raw, c, 0)),
            ("central-encrypted", _patch_u16(raw, c + 8, int(f[3]) | 1)),
            ("central-data-descriptor", _patch_u16(raw, c + 8, int(f[3]) | 8)),
            ("central-method-unsupported", _patch_u16(raw, c + 10, 99)),
            ("central-crc-drift", _patch_u32(raw, c + 16, int(f[7]) ^ 1)),
            ("central-csize-drift", _patch_u32(raw, c + 20, int(f[8]) + 1)),
            ("central-usize-drift", _patch_u32(raw, c + 24, int(f[9]) + 1)),
            ("central-name-len-max", _patch_u16(raw, c + 28, 0xFFFF)),
            ("central-extra-len-max", _patch_u16(raw, c + 30, 0xFFFF)),
            ("central-comment-len-max", _patch_u16(raw, c + 32, 0xFFFF)),
            ("central-local-offset-zero", _patch_u32(raw, c + 42, 0)),
            ("central-local-offset-oob", _patch_u32(raw, c + 42, len(raw) + 4096)),
        ]
        if int(f[10]):
            b = bytearray(raw); b[c + CENTRAL.size] ^= 1; rows.append(("central-name-drift", bytes(b)))
    if locals_:
        l = locals_[0]; f = LOCAL.unpack_from(raw, l)
        rows += [
            ("bad-local-signature", _patch_u32(raw, l, 0)),
            ("local-encrypted", _patch_u16(raw, l + 6, int(f[2]) | 1)),
            ("local-data-descriptor", _patch_u16(raw, l + 6, int(f[2]) | 8)),
            ("local-method-unsupported", _patch_u16(raw, l + 8, 99)),
            ("local-crc-drift", _patch_u32(raw, l + 14, int(f[6]) ^ 1)),
            ("local-csize-drift", _patch_u32(raw, l + 18, int(f[7]) + 1)),
            ("local-usize-drift", _patch_u32(raw, l + 22, int(f[8]) + 1)),
            ("local-name-len-max", _patch_u16(raw, l + 26, 0xFFFF)),
            ("local-extra-len-max", _patch_u16(raw, l + 28, 0xFFFF)),
        ]
        if int(f[9]):
            b = bytearray(raw); b[l + LOCAL.size] ^= 1; rows.append(("local-name-drift", bytes(b)))
    return rows


def _random_mutations(raw: bytes) -> list[tuple[str, bytes]]:
    rng = random.Random(SEED)
    out = []
    for i in range(RANDOM_MUTATIONS_PER_FILE):
        pos = rng.randrange(len(raw)); bit = 1 << rng.randrange(8)
        b = bytearray(raw); b[pos] ^= bit
        out.append((f"random-bit-{i:03d}-at-{pos}-mask-{bit}", bytes(b)))
    return out


def _classify(name: str, raw: bytes) -> dict:
    try:
        mature = BASE._parse_zip(raw); mature_exc = None
    except Exception as exc:
        mature = None; mature_exc = type(exc).__name__
    try:
        candidate = EOCD._candidate_parse_zip(raw); candidate_exc = None
    except Exception as exc:
        candidate = None; candidate_exc = type(exc).__name__
    ma = mature is not None; ca = candidate is not None
    safe = (not ma and not ca) or (ma and ca and candidate == mature)
    return {
        "case": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "mature_accept": ma, "candidate_accept": ca,
        "mature_exception": mature_exc, "candidate_exception": candidate_exc,
        "semantic_equal_when_accepted": bool(ma and ca and candidate == mature),
        "safe_equivalence": bool(safe),
    }


def run() -> dict:
    raw = _first_valid_zip()
    baseline_mature = BASE._parse_zip(raw); baseline_candidate = EOCD._candidate_parse_zip(raw)
    if baseline_mature is None or baseline_candidate != baseline_mature:
        raise RuntimeError("valid baseline does not have exact parser equivalence")

    valid_rows = [_classify(name, data) for name, data in _valid_variants()]
    # Every independently generated variant in the mature parser's supported envelope must remain accepted exactly.
    valid_generalization = bool(valid_rows) and all(
        row["mature_accept"] and row["candidate_accept"] and row["semantic_equal_when_accepted"] for row in valid_rows
    )
    mutations = _targeted(raw) + _random_mutations(raw)
    rows = [_classify(name, mutated) for name, mutated in mutations]
    unsafe = [row for row in rows if not row["safe_equivalence"]]
    accepted_by_mature = sum(1 for row in rows if row["mature_accept"])
    rejected_by_mature = len(rows) - accepted_by_mature
    valid = bool(rows) and not unsafe and valid_generalization
    return {
        "schema": "cmpct-v030-zipfactor-eocd-hostile-equivalence-oracle-v2",
        "contract": {
            "release_credit": False, "production_change": False, "timing_credit": False,
            "candidate_may_not_accept_any_input_rejected_by_mature_parser": True,
            "shared_acceptance_requires_exact_semantic_object": True,
            "independent_valid_generalization_required": True,
            "deterministic_seed": SEED,
        },
        "baseline": {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "exact_valid_equivalence": baseline_candidate == baseline_mature},
        "valid_generalization": {"cases": len(valid_rows), "all_exact": valid_generalization, "rows": valid_rows},
        "coverage": {
            "cases": len(rows) + len(valid_rows), "hostile_cases": len(rows), "valid_cases": len(valid_rows),
            "targeted_cases": len(_targeted(raw)), "random_bit_cases": RANDOM_MUTATIONS_PER_FILE,
            "mature_accepts_hostile": accepted_by_mature, "mature_rejects_hostile": rejected_by_mature,
        },
        "unsafe_cases": unsafe,
        "gate": {
            "experiment_valid": valid,
            "candidate_not_more_permissive": not any(row["candidate_accept"] and not row["mature_accept"] for row in rows),
            "exact_on_shared_acceptance": not any(row["mature_accept"] and row["candidate_accept"] and not row["semantic_equal_when_accepted"] for row in rows),
            "valid_generalization_exact": valid_generalization,
            "passed": valid,
        },
        "claim_boundary": "Deterministic parser differential evidence only. A pass permits canonical-integration work but does not replace fuzzing, reader/recovery, native/Android or final release authority.",
    }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-hostile-equivalence.json")); a = p.parse_args()
    result = run(); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"coverage": result["coverage"], "valid_generalization": result["valid_generalization"]["all_exact"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]: raise SystemExit("EOCD parser hostile/generalization equivalence gate failed")


if __name__ == "__main__":
    main()
