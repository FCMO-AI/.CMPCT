from __future__ import annotations

"""Fail-closed structural validator for the future 2026-09-11 Genesis dossier.

This module performs no compression and contains no scoring implementation.  It exists so
an incomplete or semantically ambiguous result cannot be mistaken for an evidence-complete
gate merely because it contains attractive aggregate numbers.
"""

import argparse
import json
from pathlib import Path
from typing import Any

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
COMPARABILITY = {
    "same_semantics_direct",
    "same_goal_different_mechanism",
    "richer_semantics",
    "unavailable",
}
CONTENDERS = ("cmpct1", "v0.29", "v0.30")
REQUIRED_ROW_METRICS = (
    "storage",
    "creation",
    "whole_read",
    "selective_access",
    "integrity_resources",
    "recovery",
    "portability",
)


def _err(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _validate_metric(value: Any, path: str, errors: list[str]) -> None:
    _err(errors, isinstance(value, dict), f"{path} must be an object")
    if not isinstance(value, dict):
        return
    cls = value.get("comparability")
    _err(errors, cls in COMPARABILITY, f"{path}.comparability invalid or missing")
    available = value.get("available")
    _err(errors, isinstance(available, bool), f"{path}.available must be boolean")
    if cls == "unavailable":
        _err(errors, available is False, f"{path}: unavailable comparability requires available=false")
        # Unavailable is not zero.  Values can contain explanatory metadata but may not
        # silently manufacture a zero measurement.
        measurements = value.get("measurements")
        if isinstance(measurements, dict):
            zero_numeric = [k for k, v in measurements.items() if isinstance(v, (int, float)) and v == 0]
            _err(errors, not zero_numeric, f"{path}: unavailable metric contains zero numeric values {zero_numeric}")
    else:
        _err(errors, available is True, f"{path}: comparable metric requires available=true")
        _err(errors, isinstance(value.get("measurements"), dict), f"{path}.measurements missing")
    _err(errors, bool(value.get("semantics")), f"{path}.semantics explanation missing")


def validate(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _err(errors, result.get("schema") == "cmpct-one-genesis-gate-v1", "schema must be cmpct-one-genesis-gate-v1")
    _err(errors, result.get("scoring_executed") is True, "final dossier must explicitly state scoring_executed=true")

    authorities = result.get("authorities")
    _err(errors, isinstance(authorities, dict), "authorities missing")
    if isinstance(authorities, dict):
        _err(errors, authorities.get("v0.29") == V029_SHA, "frozen v0.29 SHA mismatch")
        _err(errors, authorities.get("v0.30") == V030_SHA, "frozen v0.30 SHA mismatch")
        candidate = authorities.get("cmpct1")
        _err(errors, isinstance(candidate, str) and len(candidate) == 40, "exact CMPCT1 gate SHA missing")

    rows = result.get("rows")
    _err(errors, isinstance(rows, list), "rows missing")
    if not isinstance(rows, list):
        return errors
    _err(errors, len(rows) == 15, f"expected exactly 15 workload rows, got {len(rows)}")

    identities: set[tuple[str, str]] = set()
    tree_hashes: set[str] = set()
    for index, row in enumerate(rows):
        p = f"rows[{index}]"
        _err(errors, isinstance(row, dict), f"{p} must be an object")
        if not isinstance(row, dict):
            continue
        suite = row.get("suite")
        name = row.get("name")
        _err(errors, isinstance(suite, str) and bool(suite), f"{p}.suite missing")
        _err(errors, isinstance(name, str) and bool(name), f"{p}.name missing")
        if isinstance(suite, str) and isinstance(name, str):
            identity = (suite, name)
            _err(errors, identity not in identities, f"duplicate workload identity {identity}")
            identities.add(identity)
        files = row.get("files")
        logical = row.get("logical_bytes")
        tree = row.get("tree_sha256")
        _err(errors, isinstance(files, int) and files >= 0, f"{p}.files invalid")
        _err(errors, isinstance(logical, int) and logical >= 0, f"{p}.logical_bytes invalid")
        _err(errors, isinstance(tree, str) and len(tree) == 64, f"{p}.tree_sha256 invalid")
        if isinstance(tree, str):
            tree_hashes.add(tree)

        contenders = row.get("contenders")
        _err(errors, isinstance(contenders, dict), f"{p}.contenders missing")
        if not isinstance(contenders, dict):
            continue
        _err(errors, set(contenders) == set(CONTENDERS), f"{p}.contenders must be exactly {CONTENDERS}")
        for contender in CONTENDERS:
            data = contenders.get(contender)
            cp = f"{p}.contenders.{contender}"
            _err(errors, isinstance(data, dict), f"{cp} missing")
            if not isinstance(data, dict):
                continue
            # Every contender row must bind back to the exact same generated tree.
            _err(errors, data.get("tree_sha256") == tree, f"{cp} did not consume row tree_sha256")
            metrics = data.get("metrics")
            _err(errors, isinstance(metrics, dict), f"{cp}.metrics missing")
            if not isinstance(metrics, dict):
                continue
            for metric in REQUIRED_ROW_METRICS:
                _err(errors, metric in metrics, f"{cp}.metrics.{metric} missing")
                if metric in metrics:
                    _validate_metric(metrics[metric], f"{cp}.metrics.{metric}", errors)

    _err(errors, len(tree_hashes) == len(rows), "workload tree identities are not unique")

    aggregates = result.get("aggregates")
    _err(errors, isinstance(aggregates, dict), "aggregates missing")
    if isinstance(aggregates, dict):
        _err(errors, aggregates.get("workloads") == 15, "aggregates.workloads must be 15")
        _err(errors, isinstance(aggregates.get("all_rows_retained"), bool) and aggregates.get("all_rows_retained") is True,
             "aggregates must assert all_rows_retained=true")
        _err(errors, isinstance(aggregates.get("losses"), list), "aggregate losses list missing")
        _err(errors, isinstance(aggregates.get("semantic_asymmetries"), list), "semantic asymmetries list missing")

    decision = result.get("decision")
    _err(errors, decision in {"KEEP_CMPCT1_PRIMARY", "REACTIVATE_V030_NEAR_TERM"}, "invalid or missing Genesis decision")
    _err(errors, bool(result.get("hostile_review")), "hostile_review missing")
    _err(errors, bool(result.get("limitations")), "limitations missing")
    return errors


def _self_test() -> None:
    # Prove the validator fails closed on the easiest forms of benchmark theater.
    empty: dict[str, Any] = {}
    errors = validate(empty)
    assert errors

    unavailable_zero: dict[str, Any] = {
        "comparability": "unavailable",
        "available": False,
        "semantics": "operation absent",
        "measurements": {"cpu_s": 0},
    }
    errs: list[str] = []
    _validate_metric(unavailable_zero, "probe", errs)
    assert any("zero numeric" in item for item in errs)

    comparable_without_semantics: dict[str, Any] = {
        "comparability": "same_semantics_direct",
        "available": True,
        "measurements": {"bytes": 1},
    }
    errs = []
    _validate_metric(comparable_without_semantics, "probe", errs)
    assert any("semantics" in item for item in errs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"self_test": "PASS", "scoring_executed": False}))
    if args.result is not None:
        document = json.loads(args.result.read_text(encoding="utf-8"))
        errors = validate(document)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        if errors:
            raise SystemExit(1)
    if not args.self_test and args.result is None:
        parser.error("provide a future result dossier or --self-test")


if __name__ == "__main__":
    main()
