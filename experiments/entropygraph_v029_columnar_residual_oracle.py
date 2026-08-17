"""CMPCT v0.29 detached oracle — bounded Columnar Residual Programs.

Attempt #5 stores each delta recipe as the canonical interleaved stream emitted by `delta_encode`:
LITERAL tag + length + bytes, or COPY tag + base offset + length.  Solid residual packing already gives
zstd several recipes at once, but opcodes, small control integers and literal entropy remain interleaved.

This oracle asks a narrower question before any reader grammar is designed: if the *same* accepted
attempt-5 recipe groups were represented reversibly as separate control/address/literal columns, how many
physical bytes could the real compressor remove?  It never exports a columnar archive.  Attempt #5 bytes
remain unchanged; the oracle only records an exact compression ceiling with conservative transition
charges.

Footnote: a new grammar is expensive.  Therefore this experiment deliberately charges 32 bytes per
columnar physical group plus 8 bytes per member above measured payload cost, requires exact recipe
round-trip, retains the existing 256 KiB / <=2x materialization limits, and uses a 128 KiB aggregate gate.
A clever-looking 20 KiB result is a REJECT, not permission to grow the parser.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACK_PATH = HERE / "entropygraph_v029_residual_pack.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PACK = _load(PACK_PATH, "cmpct_v029_columnar_residual_pack_source")
PH = PACK.PH
MAGIC = b"CRP1"
COLUMNAR_GROUP_CHARGE = 32
COLUMNAR_MEMBER_CHARGE = 8
MIN_ORACLE_SAVING = 128 * 1024
MIN_IMPROVED_GROUPS = 4
_ORIGINAL_CHOOSE_PLAN = PACK._choose_plan
_LAST_ORACLE: dict = {}


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative columnar varint")
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _get_varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if pos >= len(data):
            raise ValueError("truncated columnar varint")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise ValueError("oversized columnar varint")


def _parse_recipe(raw: bytes) -> list[tuple]:
    ops = []
    pos = 0
    while pos < len(raw):
        tag = raw[pos]
        pos += 1
        if tag == 0:
            length, pos = _get_varint(raw, pos)
            if pos + length > len(raw):
                raise ValueError("literal exceeds recipe bounds")
            ops.append((0, raw[pos:pos + length]))
            pos += length
        elif tag == 1:
            offset, pos = _get_varint(raw, pos)
            length, pos = _get_varint(raw, pos)
            ops.append((1, offset, length))
        else:
            raise ValueError("unknown canonical delta opcode")
    return ops


def _columnar_encode(programs: list[dict]) -> bytes:
    """Encode canonical recipes into reversible control/address/literal columns.

    Layout after ``CRP1``: member count; op-count varints; one raw tag byte per op; literal-length
    varints; COPY-offset varints; COPY-length varints; then all literal bytes.  Counts implied by the tag
    column make extra column-length tables unnecessary while still permitting strict bounded parsing.
    """
    parsed = [_parse_recipe(row["raw_delta"]) for row in programs]
    out = bytearray(MAGIC)
    _put_varint(out, len(parsed))
    for ops in parsed:
        _put_varint(out, len(ops))

    tags = bytearray()
    literal_lengths: list[int] = []
    copy_offsets: list[int] = []
    copy_lengths: list[int] = []
    literals = bytearray()
    for ops in parsed:
        for op in ops:
            tags.append(op[0])
            if op[0] == 0:
                literal = op[1]
                literal_lengths.append(len(literal))
                literals.extend(literal)
            else:
                copy_offsets.append(int(op[1]))
                copy_lengths.append(int(op[2]))

    out.extend(tags)
    for value in literal_lengths:
        _put_varint(out, value)
    for value in copy_offsets:
        _put_varint(out, value)
    for value in copy_lengths:
        _put_varint(out, value)
    out.extend(literals)
    return bytes(out)


def _columnar_decode(blob: bytes) -> list[bytes]:
    """Reconstruct the canonical interleaved recipe bytes exactly, failing closed on malformed columns."""
    if not blob.startswith(MAGIC):
        raise ValueError("not a columnar residual oracle payload")
    pos = len(MAGIC)
    members, pos = _get_varint(blob, pos)
    if members > 1_000_000:
        raise ValueError("columnar member count exceeds oracle bound")
    op_counts = []
    for _ in range(members):
        count, pos = _get_varint(blob, pos)
        op_counts.append(count)
    total_ops = sum(op_counts)
    if total_ops > len(blob) - pos:
        raise ValueError("columnar tag stream exceeds payload")
    tags = blob[pos:pos + total_ops]
    pos += total_ops
    if any(tag not in (0, 1) for tag in tags):
        raise ValueError("unknown columnar opcode")

    literal_count = tags.count(0)
    copy_count = tags.count(1)
    literal_lengths = []
    copy_offsets = []
    copy_lengths = []
    for _ in range(literal_count):
        value, pos = _get_varint(blob, pos)
        literal_lengths.append(value)
    for _ in range(copy_count):
        value, pos = _get_varint(blob, pos)
        copy_offsets.append(value)
    for _ in range(copy_count):
        value, pos = _get_varint(blob, pos)
        copy_lengths.append(value)

    literal_total = sum(literal_lengths)
    if literal_total != len(blob) - pos:
        raise ValueError("columnar literal column length mismatch")
    literals = memoryview(blob)[pos:]
    literal_pos = tag_pos = lit_index = copy_index = 0
    recipes = []
    for op_count in op_counts:
        raw = bytearray()
        for _ in range(op_count):
            tag = tags[tag_pos]
            tag_pos += 1
            raw.append(tag)
            if tag == 0:
                length = literal_lengths[lit_index]
                lit_index += 1
                _put_varint(raw, length)
                raw.extend(literals[literal_pos:literal_pos + length])
                literal_pos += length
            else:
                _put_varint(raw, copy_offsets[copy_index])
                _put_varint(raw, copy_lengths[copy_index])
                copy_index += 1
        recipes.append(bytes(raw))
    if tag_pos != total_ops or lit_index != literal_count or copy_index != copy_count or literal_pos != literal_total:
        raise ValueError("columnar decoder did not consume all columns")
    return recipes


def _measure_group(group: dict) -> dict:
    programs = list(group["programs"])
    blob = _columnar_encode(programs)
    roundtrip = _columnar_decode(blob)
    exact = roundtrip == [row["raw_delta"] for row in programs]
    if not exact:
        raise RuntimeError("columnar oracle failed canonical recipe round-trip")

    max_amp = max((len(blob) / max(1, row["target_len"]) for row in programs), default=0.0)
    if len(blob) > PACK.MAX_RESIDUAL_PACK or max_amp > PACK.MAX_ADDITIONAL_RECIPE_AMP:
        return {
            "members": len(programs),
            "admissible": False,
            "reason": "columnar-locality-bound",
            "columnar_raw_bytes": len(blob),
            "max_amp": max_amp,
            "saving_bytes": 0,
            "roundtrip_exact": True,
        }

    codec, payload = PACK._compress_record(blob, 12)
    columnar_physical = PH.size + len(payload)
    transition_charge = COLUMNAR_GROUP_CHARGE + COLUMNAR_MEMBER_CHARGE * len(programs)
    saving = int(group["packed_physical_bytes"]) - columnar_physical - transition_charge
    return {
        "members": len(programs),
        "admissible": True,
        "reason": None,
        "canonical_raw_bytes": len(group["raw"]),
        "canonical_physical_bytes": int(group["packed_physical_bytes"]),
        "columnar_raw_bytes": len(blob),
        "columnar_physical_bytes": columnar_physical,
        "transition_charge_bytes": transition_charge,
        "saving_bytes": saving,
        "max_amp": max_amp,
        "roundtrip_exact": True,
        "codec": codec,
    }


def _choose_plan_with_oracle(programs: list[dict]) -> dict:
    global _LAST_ORACLE
    plan = _ORIGINAL_CHOOSE_PLAN(programs)
    rows = [_measure_group(group) for group in plan["eligible"]]
    selected = [row for row in rows if row["admissible"] and row["saving_bytes"] > 0]
    total = sum(row["saving_bytes"] for row in selected)
    _LAST_ORACLE = {
        "baseline_residual_limit": int(plan["limit"]),
        "baseline_eligible_groups": len(plan["eligible"]),
        "columnar_improved_groups": len(selected),
        "columnar_estimated_saving_bytes": total,
        "max_selected_columnar_amp": max((row["max_amp"] for row in selected), default=0.0),
        "all_roundtrips_exact": all(row["roundtrip_exact"] for row in rows),
        "research_gate_pass": (
            total >= MIN_ORACLE_SAVING
            and len(selected) >= MIN_IMPROVED_GROUPS
            and all(row["roundtrip_exact"] for row in rows)
            and max((row["max_amp"] for row in selected), default=0.0) <= PACK.MAX_ADDITIONAL_RECIPE_AMP
        ),
        "groups": rows,
    }
    return plan  # Oracle only: emit the exact established attempt-5 layout.


def measure(root: Path, out: Path) -> dict:
    global _LAST_ORACLE
    previous = PACK._choose_plan
    _LAST_ORACLE = {}
    PACK._choose_plan = _choose_plan_with_oracle
    try:
        stats = PACK._build_graph(root, out)
    finally:
        PACK._choose_plan = previous
    stats["columnar_residual_oracle"] = dict(_LAST_ORACLE)
    return stats


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT detached columnar residual-program oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    stats = measure(args.source, args.archive)
    text = json.dumps(stats["columnar_residual_oracle"], indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    _main()
