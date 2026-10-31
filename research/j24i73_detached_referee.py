#!/usr/bin/env python3
"""J24I73 detached, no-CMPCT referee. Verifies evidence against original physical bytes."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("public", "original", "minimal")
MEASURES = ("whole_process_wall_ns", "import_wall_ns", "constructor_wall_ns", "constructor_cpu_ns")
DONORS = {
    "reference": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "admit": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "factored": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "owned_factored_fresh": ("research/j24g74_owned_decoder_court.py", None),
    "_index_from_footer": ("research/j24g74_owned_decoder_court.py", "OwnedCMPCT"),
}


def strict_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate JSON key " + k)
        out[k] = v
    return out


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def function(tree, name, cls=None):
    nodes = tree.body
    if cls:
        matches = [n for n in nodes if isinstance(n, ast.ClassDef) and n.name == cls]
        assert len(matches) == 1
        nodes = matches[0].body
    matches = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(matches) == 1, (cls, name)
    return matches[0]


def ast_hash(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def checked_number(x):
    assert type(x) is int and x >= 0, repr(x)
    return x


def verify(out: Path):
    r = json.loads((out / "receipt.json").read_text(), object_pairs_hook=strict_object)
    assert r["schema"] == "cmpct-j24i73-import-cone-v1"
    assert r["status"] == "PASS_COURT_NOT_PROMOTION" and type(r["product_credit"]) is int and r["product_credit"] == 0
    assert r["source"]["main"] == "80c358f8824ec1b20d349c92ed94c898090969b0"
    assert r["source"]["inherited"] == "f8ef04c149a09f62fc3d5cb9dfdb006b439b5efc"
    assert r["source"]["prereg"] == "6403d44390a4305099c98516d2ed8a7bbdb7458a"
    assert r["source"]["product_reader_blob"] == "29a8be64f3acfb027750351c6a567fd82cf7dc97"
    assert r["source"]["reference_head"] == "129edec976efe8bb604584517de39553487fec34"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == r["source"]["head"]
    assert r["protocol"]["labels"] == list(NAMES) and r["protocol"]["size"] == 8192
    assert r["protocol"]["repeats"] == 8 and r["protocol"]["import_repeats"] == 4
    for mode in ("A", "B"):
        item = r["physical"][mode]
        assert item["file"] == mode + ".cmpct"
        assert checked_number(item["bytes"]) == (out / item["file"]).stat().st_size
        assert item["sha256"] == sha(out / item["file"])
        assert item["bytes"] > 0
    module = out / "j24i73_ablation_owned.py"
    assert sha(module) == r["minimal_module"]["sha256"]
    assert checked_number(r["minimal_module"]["size"]) == module.stat().st_size
    tree = ast.parse(module.read_text())
    cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OwnedCMPCT"]
    assert len(cls) == 1 and [x.id for x in cls[0].bases if isinstance(x, ast.Name)] == ["CMPCT"]
    for name, (path, class_name) in DONORS.items():
        donor = ast.parse((ROOT / path).read_text())
        dst_hash = ast_hash(function(tree, name, "OwnedCMPCT" if name == "_index_from_footer" else None))
        src_hash = ast_hash(function(donor, name, class_name))
        assert dst_hash == src_hash == r["minimal_module"]["donor_ast_sha256"][name], name
    assert set(r["raw"]) == {"A", "B"}
    medians = {}
    for mode in ("A", "B"):
        assert set(r["raw"][mode]) == set(NAMES)
        medians[mode] = {}
        for name in NAMES:
            rows = r["raw"][mode][name]
            assert len(rows) == 8
            assert {row["iteration"] for row in rows} == set(range(8))
            for row in rows:
                assert row["label"] == name and row["archive"] == mode
                assert row["mode"] == "open"
                assert row["count"] == 8129 and row["depth"] == (63 if mode == "A" else 0)
                assert row["index_sha256"] == r["semantic_control"]["inherited_source_semantics"][mode]["public"]["index_sha256"]
                assert row["member"] == "f00063.dat"
                for measure in MEASURES:
                    checked_number(row[measure])
            medians[mode][name] = {
                measure: statistics.median(row[measure] for row in rows)
                for measure in MEASURES
            }
            assert medians[mode][name] == r["medians"][mode][name], (mode, name)
    assert r["semantic_control"]["malformed_short"] == ["REJECT", "REJECT"]
    import_medians = {}
    assert set(r["import_only_raw"]) == set(NAMES)
    for name in NAMES:
        rows = r["import_only_raw"][name]
        assert len(rows) == 4 and {x["iteration"] for x in rows} == set(range(4))
        for row in rows:
            assert row["label"] == name and row["mode"] == "import"
            for measure in ("import_wall_ns", "import_cpu_ns", "whole_process_wall_ns"):
                checked_number(row[measure])
        import_medians[name] = {
            measure: statistics.median(row[measure] for row in rows)
            for measure in ("import_wall_ns", "import_cpu_ns", "whole_process_wall_ns")
        }
        assert import_medians[name] == r["import_only_medians"][name]
    saved = import_medians["original"]["import_wall_ns"] - import_medians["minimal"]["import_wall_ns"]
    crossover = medians["A"]["minimal"]["whole_process_wall_ns"] / medians["B"]["public"]["whole_process_wall_ns"]
    original = medians["A"]["original"]["whole_process_wall_ns"] / medians["B"]["public"]["whole_process_wall_ns"]
    minimal_vs_original = medians["A"]["minimal"]["whole_process_wall_ns"] / medians["A"]["original"]["whole_process_wall_ns"]
    assert r["import_saved_ns"] == saved
    assert abs(r["ratios"]["minimal_A_over_public_B_gross"] - crossover) < 1e-12
    assert abs(r["ratios"]["original_A_over_public_B_gross"] - original) < 1e-12
    assert abs(r["ratios"]["minimal_A_over_original_A_gross"] - minimal_vs_original) < 1e-12
    expect = {
        "H1_import_cone_saved_10ms": saved >= 10_000_000,
        "H2_gross_minimal_A_at_most_1p20_public_B": crossover <= 1.20,
        "H3_semantic_identity": True,
    }
    assert r["predictions"] == expect, (r["predictions"], expect)
    return {"source_sha": r["source"]["head"], "predictions": expect,
            "import_saved_ms": saved / 1e6, "minimal_A_over_public_B": crossover,
            "original_A_over_public_B": original,
            "physical_sha": {m: r["physical"][m]["sha256"] for m in ("A", "B")},
            "study": "research only, not product or release evidence"}


def adversarial(out):
    """Use independent forged copies without altering source receipts."""
    import tempfile
    import shutil
    checks = 0
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td)
        for p in out.iterdir():
            if p.is_file():
                shutil.copyfile(p, fake / p.name)
        def check_patch(patch):
            nonlocal checks
            obj = json.loads((out / "receipt.json").read_text(), object_pairs_hook=strict_object)
            patch(obj)
            (fake / "receipt.json").write_text(json.dumps(obj))
            try:
                verify(fake)
            except (AssertionError, ValueError, KeyError):
                checks += 1
            else:
                raise AssertionError("forged receipt accepted")
        check_patch(lambda d: d["medians"]["A"]["minimal"].__setitem__("import_wall_ns", 1))
        check_patch(lambda d: d["source"].__setitem__("head", "0" * 40))
        check_patch(lambda d: d["physical"]["A"].__setitem__("bytes", 42))
        check_patch(lambda d: d["predictions"].__setitem__("H2_gross_minimal_A_at_most_1p20_public_B", not d["predictions"]["H2_gross_minimal_A_at_most_1p20_public_B"]))
        check_patch(lambda d: d["raw"]["A"]["minimal"][0].__setitem__("depth", 0))
        check_patch(lambda d: d["raw"]["B"]["public"][0].__setitem__("whole_process_wall_ns", True))
    return checks


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence/j24i73")
    result = verify(target)
    result["adversarial_forged_receipts_rejected"] = adversarial(target)
    print("J24I73_DETACHED_REFEREE", json.dumps(result, sort_keys=True))
