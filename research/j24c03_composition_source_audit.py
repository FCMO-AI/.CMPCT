#!/usr/bin/env python3
"""J24C03 exact-parent surface custodian: no unclaimed Reader methods may change."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path

READER_ALLOW = frozenset({
    "_blob", "read", "read_range", "_raw_blob_view_for_extract", "_direct_deflate_stream"
})
VALIDATOR_ALLOW = frozenset({"_validate_storage"})
PARENT_READER_BLOB = "dbd4ac576a05a47eae97e1e40de89cf1de440516"
PARENT_VALIDATOR_BLOB = "51c2849061f99a4afeddb7666956b24566ce7de0"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize(text: str, role: str):
    tree = ast.parse(text)
    if role == "reader":
        candidates = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CMPCT"]
        assert len(candidates) == 1, "Reader CMPCT class count changed"
        functions = [n for n in candidates[0].body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        allowed = READER_ALLOW
    else:
        functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        allowed = VALIDATOR_ALLOW
    found = {n.name for n in functions if n.name in allowed}
    assert found == allowed, (role, found, allowed)
    assert len({n.name for n in functions}) == len(functions), "duplicate function names"
    signatures = {n.name: ast.dump(n.args, include_attributes=False) for n in functions if n.name in allowed}
    lines = text.splitlines(keepends=True)
    for n in sorted((n for n in functions if n.name in allowed), key=lambda z: z.lineno, reverse=True):
        # Replace the complete function including its body, retaining only the permitted method name.
        lines[n.lineno - 1:n.end_lineno] = [f"    # J24C03-owned-method:{n.name}\n"]
    return "".join(lines), signatures


def check(parent: Path, candidate: Path, role: str):
    pa = parent.read_text(encoding="utf-8")
    ca = candidate.read_text(encoding="utf-8")
    norm_a, sig_a = normalize(pa, role)
    norm_b, sig_b = normalize(ca, role)
    assert sig_a == sig_b, f"{role} changed a method signature"
    assert norm_a == norm_b, f"{role} changed source outside named J24C03 guard methods"
    assert pa != ca, f"{role} unchanged; missing promised guard"
    assert pa.encode() != ca.encode()
    return {"role": role, "parent_sha256": sha(pa.encode()), "candidate_sha256": sha(ca.encode()),
            "allowed_functions": sorted(sig_a), "unmodified_source_equal": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for role, rel in (("reader", "src/cmpct/reader.py"), ("validation", "src/cmpct/validation.py")):
        results.append(check(args.parent_root / rel, args.candidate_root / rel, role))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"decision": "J24C03_PARENT_SURFACE_PRESERVED",
                                       "evidence": results}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": "J24C03_PARENT_SURFACE_PRESERVED", "roles": 2}, sort_keys=True))
