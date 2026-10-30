#!/usr/bin/env python3
"""J24G65 detached receipt / physical r24 auditor; imports no CMPCT code."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys

from j24g63_independent_receipt_audit import FTR, parse_wire, sha_file

CASES = ((512, 63), (2048, 1), (2048, 32), (2048, 63))


def serial_hash(samples):
    return hashlib.sha256(json.dumps(
        samples, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def med(rows, key):
    return statistics.median(r[key] for r in rows)


def audit(data: dict, receipt: Path, head: str) -> dict:
    assert data["source"]["head"] == head
    assert data["parent_commit"] == "7f509d244325d4b6ea6d0e752ea365f79c33a742"
    assert data["prereg_commit"] == "260951c6631910ed145aebc03b1868cb5770a46c"
    assert set(data["cases"]) == {f"{n}/{d}" for n, d in CASES}
    samples = data["samples"]
    assert len(samples) == 72
    assert serial_hash(samples) == data["raw_samples_sha256"]
    keys = set()
    for n, depth in CASES:
        case = data["cases"][f"{n}/{depth}"]
        assert case["n"] == n and case["depth"] == depth
        assert case["kind"] == "delete"
        assert case["expected_rows"] == n + 63 - depth
        assert case["semantics"]["verified_members"] == n + 63 - depth
        assert case["checkpoint_premium_bytes"] == (
            case["archive_bytes"]["checkpoint"] -
            case["archive_bytes"]["chain"])
        assert case["checkpoint_premium_bytes"] > 0
        assert len(case["wire"]) == depth
        initial = n + 63
        prospective = [f"f{((2*i+1)*initial)//126:04d}.dat" for i in range(63)]
        assert case["selected_paths"] == prospective[:depth]
        assert [r["name"] for r in case["wire"]] == list(
            reversed(prospective[:depth]))
        assert all(r["tag"] == "del" for r in case["wire"])
        instrumented = [s for s in samples if
                        s["n"] == n and s["depth_case"] == depth
                        and s["instrumented"]]
        assert len(instrumented) == 16
        for block in range(4):
            expect = (("chain", "checkpoint", "checkpoint", "chain") if
                      block % 2 == 0 else
                      ("checkpoint", "chain", "chain", "checkpoint"))
            rows = sorted((s for s in instrumented if s["block"] == block),
                          key=lambda s: s["position"])
            assert len(rows) == 4
            assert tuple(s["variant"] for s in rows) == expect
        for s in instrumented:
            key = (n, depth, True, s["block"], s["position"])
            assert key not in keys
            keys.add(key)
            assert type(s["wall_ns"]) is int and s["wall_ns"] > 0
            assert type(s["cpu_ns"]) is int and s["cpu_ns"] >= 0
            assert s["rows"] == case["expected_rows"]
            assert s["depth"] == (depth if s["variant"] == "chain" else 0)
            assert s["replay_calls"] == (
                depth if s["variant"] == "chain" else 0)
            assert s["footer_calls"] == (
                depth + 1 if s["variant"] == "chain" else 1)
            assert 0 <= s["replay_ns"] <= s["wall_ns"]
            assert 0 <= s["footer_ns"] <= s["wall_ns"]
            assert s["residual_ns"] == s["wall_ns"] - s["replay_ns"] - s["footer_ns"]
            assert s["residual_ns"] >= 0
        a = [s for s in instrumented if s["variant"] == "chain"]
        b = [s for s in instrumented if s["variant"] == "checkpoint"]
        summary = data["summaries"][f"{n}/{depth}"]
        fields = (
            ("wall_ns", "open_wall_ns"),
            ("cpu_ns", "open_cpu_ns"),
            ("replay_ns", "replay_ns"),
            ("footer_ns", "footer_ns"),
            ("residual_ns", "residual_ns"),
        )
        for sample_field, summary_suffix in fields:
            assert summary["chain_" + summary_suffix] == med(a, sample_field)
            assert summary["checkpoint_" + summary_suffix] == med(b, sample_field)
        assert summary["extra_open_wall_ns"] == (
            summary["chain_open_wall_ns"] - summary["checkpoint_open_wall_ns"])
        assert summary["extra_replay_ns"] == (
            summary["chain_replay_ns"] - summary["checkpoint_replay_ns"])
        assert summary["extra_footer_ns"] == (
            summary["chain_footer_ns"] - summary["checkpoint_footer_ns"])
        assert summary["extra_residual_ns"] == (
            summary["chain_residual_ns"] - summary["checkpoint_residual_ns"])
        expected_fraction = (summary["extra_replay_ns"] /
                             summary["extra_open_wall_ns"]
                             if summary["extra_open_wall_ns"] > 0 else None)
        if expected_fraction is None:
            assert summary["extra_replay_fraction"] is None
        else:
            assert abs(summary["extra_replay_fraction"] - expected_fraction) < 1e-12

    plain = [s for s in samples if not s["instrumented"]]
    assert len(plain) == 8
    for block in range(2):
        expect = (("chain", "checkpoint", "checkpoint", "chain") if block == 0
                  else ("checkpoint", "chain", "chain", "checkpoint"))
        rows = sorted((s for s in plain if s["block"] == block),
                      key=lambda s: s["position"])
        assert tuple(s["variant"] for s in rows) == expect
        for s in rows:
            key = (2048, 63, False, s["block"], s["position"])
            assert key not in keys
            keys.add(key)
            assert (s["n"], s["depth_case"], s["rows"]) == (2048, 63, 2048)
            assert s["depth"] == (63 if s["variant"] == "chain" else 0)
            assert s["replay_calls"] == s["footer_calls"] == 0
            assert s["replay_ns"] == s["footer_ns"] == 0
    assert len(keys) == 72
    a = [s for s in plain if s["variant"] == "chain"]
    b = [s for s in plain if s["variant"] == "checkpoint"]
    raw_delta = med(a, "wall_ns") - med(b, "wall_ns")
    primary = data["summaries"]["2048/63"]
    traced_delta = primary["extra_open_wall_ns"]
    control = data["control"]
    assert control["uninstrumented_chain_ns"] == med(a, "wall_ns")
    assert control["uninstrumented_checkpoint_ns"] == med(b, "wall_ns")
    assert control["uninstrumented_penalty_ns"] == raw_delta
    assert control["instrumented_penalty_ns"] == traced_delta
    perturbation = (abs(raw_delta - traced_delta) / raw_delta
                    if raw_delta > 0 else None)
    if perturbation is None:
        assert control["penalty_perturbation_fraction"] is None
    else:
        assert abs(control["penalty_perturbation_fraction"] - perturbation) < 1e-12
    if raw_delta < 3_000_000:
        decision = "DELETE_NONMATERIAL"
    elif perturbation is None or perturbation > .15 or traced_delta <= 0:
        decision = "INCONCLUSIVE_INSTRUMENTATION"
    elif primary["extra_replay_fraction"] is None or primary["extra_replay_fraction"] < .60:
        decision = "DELETE_REPLAY_NOT_PROVEN_MAJOR"
    else:
        decision = "DELETE_REPLAY_MAJOR_COST_OWNER"
    assert data["decision"] == decision

    physical = data["cases"]["2048/63"]
    saved = physical["saved_physical"]
    chain_path = receipt.parent / saved["chain"]
    checkpoint_path = receipt.parent / saved["checkpoint"]
    assert chain_path.is_file() and checkpoint_path.is_file()
    assert sha_file(chain_path) == physical["archive_sha256"]["chain"]
    assert sha_file(checkpoint_path) == physical["archive_sha256"]["checkpoint"]
    chain = chain_path.read_bytes()
    checkpoint = checkpoint_path.read_bytes()
    assert checkpoint.startswith(chain)
    assert len(checkpoint) - len(chain) == physical["checkpoint_premium_bytes"]
    ledger = parse_wire(chain, physical["wire"][0]["pos"])
    assert len(ledger) == 64 and all(k == 1 for k, _ in ledger[:63])
    assert ledger[-1][0] == 0
    selected = physical["selected_paths"]
    for i, (_, delta) in enumerate(ledger[:63]):
        ops = delta["ops"]
        assert len(ops) == 1 and ops[0] == ["del", selected[62-i]]
    full = parse_wire(checkpoint, len(checkpoint) - FTR.size)
    assert len(full) == 1 and full[0][0] == 0
    assert len(full[0][1]["files"]) == 2048
    return {"result": "PASS", "head": head, "samples": 72,
            "decision": decision, "checkpoint_premium_bytes": len(checkpoint)-len(chain)}


def hostile(prototype, receipt, head, change):
    trial = copy.deepcopy(prototype)
    change(trial)
    try:
        audit(trial, receipt, head)
    except (AssertionError, KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
        return
    raise AssertionError("forged scientific receipt accepted")


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py evidence/j24g65-result.json EXPECTED_HEAD evidence/audit.json")
    receipt, head, output = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    data = json.loads(receipt.read_text(encoding="utf-8"))
    result = audit(data, receipt, head)

    def corrupted_calls(d):
        row = next(x for x in d["samples"] if x["instrumented"]
                   and x["variant"] == "chain")
        row["replay_calls"] -= 1
        d["raw_samples_sha256"] = serial_hash(d["samples"])

    hostile(data, receipt, head, corrupted_calls)
    hostile(data, receipt, head,
            lambda d: d["summaries"]["2048/63"].__setitem__(
                "extra_replay_fraction", 100.0))
    hostile(data, receipt, head,
            lambda d: d["cases"]["2048/63"]["archive_sha256"].__setitem__(
                "chain", "0"*64))
    hostile(data, receipt, head,
            lambda d: d["cases"]["2048/63"]["wire"][0].__setitem__(
                "tag", "put"))
    result["hostile_receipts_rejected"] = 4
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24G65_DETACHED_AUDIT_PASS", head, "72 raw observations, 4/4 forged receipts rejected")


if __name__ == "__main__":
    main()
