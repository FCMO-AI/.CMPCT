"""F-01 / O0.1 General Reversible Structure Compiler composition oracle.

Research-only.  This module implements the frozen tiny grammar in
``docs/v030-rnd/REVERSIBLE_STRUCTURE_COMPILER_O01_PREREG.md``.  It intentionally
contains no benchmark-name/path/hash dispatch and grants no release credit.

The grammar is deliberately small: DIRECT terminal storage, one existing
fixed-width Lattice lane transform, one existing Geometry delimiter transform,
and one bounded SPLIT/CONCAT node.  Search cost may be gifted at O0.1; every
byte needed to reconstruct the target is serialized and charged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from dataclasses import dataclass

from experiments import entropygraph_v030_geometry as G
from experiments import entropygraph_v030_lattice as L

GRAMMAR = "f01-o01-grammar-v0-split-lane-delimiter"
GRID = 4096
MAX_TARGET_BYTES = 256 * 1024
MAX_PROGRAM_DEPTH = 4
MATERIAL_SAVING_BYTES = 128
MATERIAL_SAVING_RATIO = 0.005


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative F-01 varint")
    while True:
        b = value & 0x7F
        value >>= 7
        out.append(b | (0x80 if value else 0))
        if not value:
            return


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    for _ in range(10):
        if pos >= len(buf):
            raise ValueError("short F-01 varint")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, pos
        shift += 7
    raise ValueError("overlong F-01 varint")


def _terminal(raw: bytes, *, force_raw: bool = False) -> bytes:
    compressed = L.zc(raw, 19)
    use_zstd = not force_raw and len(compressed) < len(raw)
    payload = compressed if use_zstd else raw
    out = bytearray(b"Z" if use_zstd else b"R")
    _put_varint(out, len(raw))
    _put_varint(out, len(payload))
    out.extend(payload)
    return bytes(out)


def _wrap_lane(raw: bytes, width: int) -> bytes:
    physical = L.lane_forward(raw, width)
    if L.lane_inverse(physical, width, len(raw)) != raw:
        raise RuntimeError("lane inverse failed before F-01 admission")
    child = _terminal(physical)
    out = bytearray(b"W")
    _put_varint(out, len(raw))
    _put_varint(out, width)
    _put_varint(out, len(child))
    out.extend(child)
    return bytes(out)


def _wrap_delimiter(raw: bytes, delimiter: int) -> bytes:
    physical = G.delimiter_forward(raw, delimiter)
    if G.delimiter_inverse(physical, len(raw)) != raw:
        raise RuntimeError("delimiter inverse failed before F-01 admission")
    child = _terminal(physical)
    out = bytearray(b"D")
    _put_varint(out, len(raw))
    _put_varint(out, delimiter)
    _put_varint(out, len(child))
    out.extend(child)
    return bytes(out)


def _split(raw: bytes, offset: int, left: bytes, right: bytes) -> bytes:
    if not 0 < offset < len(raw):
        raise ValueError("invalid F-01 split")
    out = bytearray(b"S")
    _put_varint(out, len(raw))
    _put_varint(out, offset)
    _put_varint(out, len(left))
    out.extend(left)
    _put_varint(out, len(right))
    out.extend(right)
    return bytes(out)


def _decode_at(program: bytes, pos: int = 0, depth: int = 0) -> tuple[bytes, int]:
    if depth > MAX_PROGRAM_DEPTH or pos >= len(program):
        raise ValueError("F-01 program depth/length violation")
    op = program[pos:pos + 1]
    pos += 1
    logical, pos = _get_varint(program, pos)
    if logical > MAX_TARGET_BYTES:
        raise ValueError("F-01 logical-size ceiling exceeded")
    if op in {b"R", b"Z"}:
        stored, pos = _get_varint(program, pos)
        end = pos + stored
        if end > len(program):
            raise ValueError("short F-01 terminal")
        payload = program[pos:end]
        raw = payload if op == b"R" else L.zd(payload, logical)
        if len(raw) != logical:
            raise ValueError("F-01 terminal logical-size mismatch")
        return raw, end
    if op in {b"W", b"D"}:
        param, pos = _get_varint(program, pos)
        child_len, pos = _get_varint(program, pos)
        end = pos + child_len
        if end > len(program):
            raise ValueError("short F-01 transform child")
        physical, child_end = _decode_at(program[pos:end], 0, depth + 1)
        if child_end != child_len:
            raise ValueError("trailing F-01 transform child")
        if op == b"W":
            raw = L.lane_inverse(physical, param, logical)
        else:
            raw = G.delimiter_inverse(physical, logical)
        if len(raw) != logical:
            raise ValueError("F-01 transform logical-size mismatch")
        return raw, end
    if op == b"S":
        offset, pos = _get_varint(program, pos)
        left_len, pos = _get_varint(program, pos)
        left_end = pos + left_len
        if left_end > len(program):
            raise ValueError("short F-01 left child")
        left, used = _decode_at(program[pos:left_end], 0, depth + 1)
        if used != left_len:
            raise ValueError("trailing F-01 left child")
        pos = left_end
        right_len, pos = _get_varint(program, pos)
        right_end = pos + right_len
        if right_end > len(program):
            raise ValueError("short F-01 right child")
        right, used = _decode_at(program[pos:right_end], 0, depth + 1)
        if used != right_len:
            raise ValueError("trailing F-01 right child")
        raw = left + right
        if len(left) != offset or len(raw) != logical:
            raise ValueError("F-01 split shape mismatch")
        return raw, right_end
    raise ValueError(f"unknown F-01 opcode {op!r}")


def decode_program(program: bytes) -> bytes:
    raw, used = _decode_at(program)
    if used != len(program):
        raise ValueError("trailing F-01 program bytes")
    return raw


@dataclass(frozen=True)
class Candidate:
    program: bytes
    motif: str
    control_bytes: int
    terminal_payload_bytes: int

    @property
    def total(self) -> int:
        return len(self.program)


def _terminal_payload_bytes(program: bytes) -> int:
    """Count only R/Z payload bytes by parsing the actual research serialization."""
    def walk(buf: bytes, pos: int = 0) -> tuple[int, int]:
        op = buf[pos:pos + 1]
        pos += 1
        _, pos = _get_varint(buf, pos)
        if op in {b"R", b"Z"}:
            n, pos = _get_varint(buf, pos)
            return n, pos + n
        if op in {b"W", b"D"}:
            _, pos = _get_varint(buf, pos)
            n, pos = _get_varint(buf, pos)
            payload, used = walk(buf[pos:pos + n], 0)
            if used != n:
                raise ValueError("F-01 child accounting mismatch")
            return payload, pos + n
        if op == b"S":
            _, pos = _get_varint(buf, pos)
            ln, pos = _get_varint(buf, pos)
            lp, used = walk(buf[pos:pos + ln], 0)
            if used != ln:
                raise ValueError("F-01 left accounting mismatch")
            pos += ln
            rn, pos = _get_varint(buf, pos)
            rp, used = walk(buf[pos:pos + rn], 0)
            if used != rn:
                raise ValueError("F-01 right accounting mismatch")
            return lp + rp, pos + rn
        raise ValueError("unknown F-01 accounting opcode")
    payload, used = walk(program)
    if used != len(program):
        raise ValueError("trailing F-01 accounting bytes")
    return payload


def _candidate(program: bytes, motif: str, target: bytes) -> Candidate:
    if decode_program(program) != target:
        raise RuntimeError(f"F-01 exact reconstruction failed for {motif}")
    payload = _terminal_payload_bytes(program)
    return Candidate(program, motif, len(program) - payload, payload)


def _alternatives(raw: bytes, stats: dict[str, int]) -> list[Candidate]:
    candidates = [_candidate(_terminal(raw), "DIRECT[zstd19/raw]", raw)]
    stats["generated"] += 1
    stats["costed"] += 1
    for width in L.LANE_WIDTHS:
        candidates.append(_candidate(_wrap_lane(raw, width), f"LANE[{width}]", raw))
        stats["generated"] += 1
        stats["costed"] += 1
    for delimiter in G._delimiter_rank(raw):
        candidates.append(_candidate(_wrap_delimiter(raw, delimiter), f"DELIM[{delimiter}]", raw))
        stats["generated"] += 1
        stats["costed"] += 1
    return candidates


def _best(candidates: list[Candidate]) -> Candidate:
    return min(candidates, key=lambda c: (c.total, c.motif, c.program))


def search(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_TARGET_BYTES:
        raise ValueError("F-01 target outside frozen bounded range")
    started = time.perf_counter()
    stats = {"generated": 0, "costed": 0, "exact_bound_prunes": 0, "heuristic_prunes": 0}
    manual_candidates = _alternatives(raw, stats)
    manual = _best(manual_candidates)
    direct = manual_candidates[0]
    literal = _candidate(_terminal(raw, force_raw=True), "LITERAL", raw)
    stats["generated"] += 1
    stats["costed"] += 1
    best = manual
    best_split = None
    split_points = list(range(GRID, len(raw), GRID))
    for offset in split_points:
        left_alts = _alternatives(raw[:offset], stats)
        right_alts = _alternatives(raw[offset:], stats)
        left = _best(left_alts)
        right = _best(right_alts)
        # Exact optimistic bound: SPLIT can never be smaller than the already-serialized children.
        if left.total + right.total >= best.total:
            stats["exact_bound_prunes"] += 1
            continue
        program = _split(raw, offset, left.program, right.program)
        motif = f"SPLIT@grid({left.motif}+{right.motif})"
        candidate = _candidate(program, motif, raw)
        stats["generated"] += 1
        stats["costed"] += 1
        if (candidate.total, candidate.motif, candidate.program) < (best.total, best.motif, best.program):
            best = candidate
            best_split = offset
    elapsed = time.perf_counter() - started
    saving = manual.total - best.total
    ratio = saving / manual.total if manual.total else 0.0
    material = saving >= MATERIAL_SAVING_BYTES and ratio >= MATERIAL_SAVING_RATIO
    return {
        "logical_bytes": len(raw),
        "direct_bytes": direct.total,
        "literal_bytes": literal.total,
        "manual_bytes": manual.total,
        "manual_motif": manual.motif,
        "synthesized_bytes": best.total,
        "synthesized_motif": best.motif,
        "control_bytes": best.control_bytes,
        "terminal_payload_bytes": best.terminal_payload_bytes,
        "saving_vs_manual_bytes": saving,
        "saving_vs_manual_ratio": ratio,
        "material_composed_win": bool(material and best.motif.startswith("SPLIT")),
        "best_split": best_split,
        "exact_reconstruction": decode_program(best.program) == raw,
        "search": {
            **stats,
            "split_points": len(split_points),
            "max_depth": MAX_PROGRAM_DEPTH,
            "optimality": "proven-within-frozen-grid-grammar",
            "wall_s": elapsed,
        },
    }


def _shake(label: str, n: int) -> bytes:
    return hashlib.shake_256(label.encode("utf-8")).digest(n)


def _lane_block(rows: int, width: int, salt: int) -> bytes:
    out = bytearray()
    for row in range(rows):
        for col in range(width):
            # Each lane evolves slowly but interleaving lanes destroys much of that locality.
            out.append(((row // (7 + col % 3)) + col * 29 + salt) & 0xFF)
    return bytes(out)


def _record_block(rows: int, sep: int, salt: int) -> bytes:
    s = bytes((sep,))
    records = []
    for i in range(rows):
        records.append(
            b"acct=" + f"{(i + salt) % 97:02d}".encode() + b"|region=" +
            bytes((65 + ((i // 11 + salt) % 7),)) * 5 + b"|value=" +
            f"{(i * 17 + salt) % 10000:04d}".encode()
        )
    return s.join(records)


def _discovery_cases() -> list[tuple[str, bytes]]:
    a = _lane_block(6144, 8, 3)
    b = _record_block(2600, 10, 5)
    c = _lane_block(4096, 16, 19)
    d = _record_block(1800, 30, 11)
    return [
        ("discovery_mixed_lane_records", a[:49152] + b[:49152]),
        ("discovery_mixed_lane16_records", c[:57344] + d[:40960]),
        ("discovery_lane_only", _lane_block(12288, 8, 31)[:98304]),
    ]


def _hostile_cases() -> list[tuple[str, bytes]]:
    return [
        ("hostile_random_64k", _shake("f01-hostile-random", 65536)),
        ("hostile_tiny_structured", (b"a|b|c|d\n" * 96)[:1024]),
        ("hostile_false_delimiters", b"\n".join(_shake(f"row-{i}", 63) for i in range(1024))[:65536]),
    ]


def _transfer_cases(seed: str) -> list[tuple[str, bytes]]:
    digest = hashlib.sha256(seed.encode("ascii", "strict")).digest()
    width = (4, 8, 16)[digest[0] % 3]
    sep = (9, 10, 28, 30)[digest[1] % 4]
    salt = int.from_bytes(digest[2:4], "little")
    pad = _shake("f01-transfer-pad-" + seed, 113 + digest[4] % 127)
    lane = _lane_block(16384, width, salt)
    records = _record_block(3200, sep, salt >> 3)
    mixed = pad + lane[:53248] + records[:45056]

    # Generator-distinct matrix/CSV-like structure: independent construction logic from discovery helpers.
    rows = []
    for r in range(2400):
        fields = [
            f"{(r * (j + 3) + digest[j + 5]) % 100000:05d}".encode()
            for j in range(6)
        ]
        if digest[12] & 1:
            fields[1], fields[4] = fields[4], fields[1]
        rows.append(bytes((sep,)).join(fields))
    matrix = b"\n".join(rows)
    return [
        ("transfer_postfreeze_mixed_shifted", mixed[:110592]),
        ("transfer_generator_distinct_matrix", matrix[:110592]),
    ]


def _operator_family(motif: str) -> str:
    if motif.startswith("SPLIT"):
        return motif.replace("@grid", "")
    return motif


def run(seed: str) -> dict:
    cases = []
    recurring: dict[str, int] = {}
    material_discovery = material_transfer = hostile_false = 0
    explanation_weighted = 0.0
    logical_total = 0
    manual_total = synthesized_total = control_total = 0
    for role, source in (
        ("discovery", _discovery_cases()),
        ("hostile", _hostile_cases()),
        ("transfer", _transfer_cases(seed)),
    ):
        for name, raw in source:
            result = search(raw)
            result.update({"role": role, "case": name})
            cases.append(result)
            motif = _operator_family(result["synthesized_motif"])
            recurring[motif] = recurring.get(motif, 0) + 1
            manual_total += result["manual_bytes"]
            synthesized_total += result["synthesized_bytes"]
            control_total += result["control_bytes"]
            logical_total += result["logical_bytes"]
            explanation_weighted += result["logical_bytes"] * (
                1.0 - result["terminal_payload_bytes"] / max(1, result["logical_bytes"])
            )
            if role == "discovery" and result["material_composed_win"]:
                material_discovery += 1
            if role == "transfer" and result["material_composed_win"]:
                material_transfer += 1
            if role == "hostile" and result["synthesized_motif"].startswith("SPLIT") and result["synthesized_bytes"] < result["manual_bytes"]:
                hostile_false += 1

    recurring_composed = sorted(
        ((count, motif) for motif, count in recurring.items() if motif.startswith("SPLIT")),
        reverse=True,
    )
    if material_discovery >= 2 and material_transfer >= 1 and hostile_false == 0:
        if recurring_composed and recurring_composed[0][0] >= 3:
            decision = "DISCOVER_PRIMITIVE"
            next_test = "Ablate the recurring split/transform motif and test whether it should be distilled into one orthogonal primitive."
        else:
            decision = "ADVANCE_COMPOSITION"
            next_test = "Prune operator liabilities and run causal ablations before any O0.2 vocabulary expansion."
    elif material_discovery == 0 and material_transfer == 0 and hostile_false == 0:
        decision = "MANUAL_FRONTIER_CONFIRMED"
        next_test = "Inspect residuals once; retire F-01 unless they motivate one specific missing generic operator under the preregistration."
    elif hostile_false > 0:
        decision = "RETIRE_F01"
        next_test = "Preserve the false-positive constraint and return Foundry priority to the Assumption Ledger."
    else:
        decision = "MANUAL_FRONTIER_CONFIRMED"
        next_test = "Perform the preregistered hostile thesis review before granting any O0.2 operator budget."

    generated = sum(c["search"]["generated"] for c in cases)
    costed = sum(c["search"]["costed"] for c in cases)
    pruned = sum(c["search"]["exact_bound_prunes"] for c in cases)
    search_wall = sum(c["search"]["wall_s"] for c in cases)
    return {
        "schema": "cmpct-v030-foundry-f01-o01-v1",
        "thesis": "F-01 General Reversible Structure Compiler",
        "oracle": "O0.1 composition-only",
        "source_commit": seed,
        "frozen_grammar": GRAMMAR,
        "grammar_fingerprint": hashlib.sha256(
            f"{GRAMMAR}|grid={GRID}|material={MATERIAL_SAVING_BYTES}:{MATERIAL_SAVING_RATIO}".encode()
        ).hexdigest(),
        "postfreeze_transfer_seed": hashlib.sha256(seed.encode()).hexdigest(),
        "oracle_gift_ledger": {
            "gifted": ["discovery/search wall time", "broad bounded enumeration", "identity-independent candidate ordering"],
            "never_gifted": ["program/control bytes", "terminal bytes", "exact reconstruction", "required basis bytes", "serialized-size comparator"],
            "deferred_debt": ["canonical framing/recovery", "full archive tree/index", "native/Android/platform", "product create-time", "whole-archive locality/selective read", "hostile parser/fuzz"],
        },
        "search_optimality": "proven-within-frozen-grid-grammar",
        "search_states": {"generated": generated, "costed": costed, "exact_bound_pruned": pruned, "heuristic_pruned": 0},
        "incumbent_bytes": {"aggregate": manual_total, "per_case": {c["case"]: c["manual_bytes"] for c in cases}},
        "synthesized_bytes": {"aggregate": synthesized_total, "per_case": {c["case"]: c["synthesized_bytes"] for c in cases}},
        "control_bytes": {"aggregate": control_total, "per_case": {c["case"]: c["control_bytes"] for c in cases}},
        "material_composed_wins": material_discovery,
        "hostile_false_wins": hostile_false,
        "transfer_wins": material_transfer,
        "recurring_program_motifs": [{"motif": m, "count": n} for n, m in recurring_composed],
        "explanation_fraction": explanation_weighted / max(1, logical_total),
        "search_time_rss": {
            "summed_case_search_wall_s": search_wall,
            "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "explicit_o0_debt": True,
        },
        "strongest_simpler_explanation": "Any win may be ordinary Zstd-19 benefiting from a known exact transform; DIRECT Zstd-19 is charged as the primary control.",
        "strongest_surviving_objection": "The frozen 4 KiB split grid tests compositional headroom, not arbitrary-boundary universal synthesis.",
        "decision": decision,
        "next_decisive_test": next_test,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=os.environ.get("EVIDENCE_HEAD", ""))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.seed or len(args.seed) < 12:
        raise SystemExit("F-01 O0.1 requires a post-freeze public commit seed")
    result = run(args.seed)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
