#!/usr/bin/env python3
"""J24I73: exact-AST replay algorithm under an ablated research-only import cone.

Independent out-of-tree experiment; no shipped Reader/Writer/format changes.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "_reference_j24g91"
OWNER_SOURCE = ROOT / "research" / "j24g74_owned_decoder_court.py"
FACTORED_SOURCE = ROOT / "research" / "j24g64_mixed_fsmeta_oracle.py"
PREREG = "6403d44390a4305099c98516d2ed8a7bbdb7458a"
INHERITED = "f8ef04c149a09f62fc3d5cb9dfdb006b439b5efc"
REFERENCE_HEAD = "129edec976efe8bb604584517de39553487fec34"
EXPECTED_READER_BLOB = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
LABELS = ("public", "original", "minimal")
MODNAME = "j24i73_ablation_owned"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_source(path: Path):
    raw = path.read_text(encoding="utf-8")
    return raw, ast.parse(raw, filename=str(path))


def find_function(tree: ast.AST, name: str, class_name: str | None = None):
    body = tree.body
    if class_name:
        cls = [n for n in body if isinstance(n, ast.ClassDef) and n.name == class_name]
        assert len(cls) == 1, (class_name, len(cls))
        body = cls[0].body
    nodes = [n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0]


def stable_ast(node):
    return digest(ast.dump(node, include_attributes=False).encode())


def generate_minimal_module(destination: Path) -> dict:
    """Copy donor algorithm ASTs unchanged; remove only unrelated test import edges."""
    parent_src, parent_tree = checked_source(FACTORED_SOURCE)
    owned_src, owned_tree = checked_source(OWNER_SOURCE)
    factored_names = ("reference", "admit", "factored")
    donor_nodes = {n: find_function(parent_tree, n) for n in factored_names}
    donor_nodes["owned_factored_fresh"] = find_function(owned_tree, "owned_factored_fresh")
    donor_nodes["_index_from_footer"] = find_function(owned_tree, "_index_from_footer", "OwnedCMPCT")
    imports = """from __future__ import annotations
import copy
import msgpack
from cmpct.reader import CMPCT
from cmpct.journal_replay import (
    JournalReplayAdmissionError, _apply_journal_ops, _validate_journal_ops
)

"""
    sections = [imports]
    for name in (*factored_names, "owned_factored_fresh"):
        tree = parent_tree if name in factored_names else owned_tree
        source = parent_src if name in factored_names else owned_src
        sections.append(ast.get_source_segment(source, donor_nodes[name]) + "\n\n")
    # Only change from original class: direct public CMPCT base instead of
    # research FactoredCMPCT. That class has only this same method override.
    method = ast.get_source_segment(owned_src, donor_nodes["_index_from_footer"])
    sections.append("class OwnedCMPCT(CMPCT):\n    \"\"\"J24I73 exact-algorithm research import-cone ablation.\"\"\"\n")
    sections.append("    " + method + "\n")
    text = "".join(sections)
    compiled = ast.parse(text, filename=str(destination))
    for name, donor in donor_nodes.items():
        node = (find_function(compiled, name, "OwnedCMPCT")
                if name == "_index_from_footer" else find_function(compiled, name))
        assert stable_ast(node) == stable_ast(donor), "algorithm AST mismatch: " + name
    destination.write_text(text, encoding="utf-8")
    return {
        "sha256": digest(destination.read_bytes()),
        "size": destination.stat().st_size,
        "donor_ast_sha256": {name: stable_ast(node) for name, node in donor_nodes.items()},
        "donor_sha256": {
            str(FACTORED_SOURCE.relative_to(ROOT)): digest(FACTORED_SOURCE.read_bytes()),
            str(OWNER_SOURCE.relative_to(ROOT)): digest(OWNER_SOURCE.read_bytes()),
        },
        "changed_semantic_surface": "import cone + class superclass only; all replay functions AST-identical",
    }


def selected_class(label: str):
    if label == "public":
        from cmpct.reader import CMPCT
        return CMPCT
    if label == "original":
        from j24g74_owned_decoder_court import OwnedCMPCT
        return OwnedCMPCT
    if label == "minimal":
        from j24i73_ablation_owned import OwnedCMPCT
        return OwnedCMPCT
    raise ValueError("invalid Reader label")


def child(args):
    label, mode = args[0:2]
    assert label in LABELS and mode in ("open", "import")
    sys.path.insert(0, os.environ["J24I73_MODULE_DIR"])
    sys.path.insert(0, str(REFERENCE / "research"))
    sys.path.insert(0, str(ROOT / "research"))
    ti, ci = time.perf_counter_ns(), time.process_time_ns()
    klass = selected_class(label)
    tj, cj = time.perf_counter_ns(), time.process_time_ns()
    receipt = {
        "label": label, "mode": mode,
        "import_wall_ns": tj - ti, "import_cpu_ns": cj - ci,
        "platform": sys.platform, "python": sys.version.split()[0],
    }
    if mode == "open":
        if len(args) != 8:
            raise ValueError("need label,mode,path,count,indexsha,member,membersha,depth")
        target, count, wire_sha, member, member_sha, depth = (
            Path(args[2]), int(args[3]), args[4], args[5], args[6], int(args[7]))
        ts, cs = time.perf_counter_ns(), time.process_time_ns()
        with klass(target) as reader:
            te, ce = time.perf_counter_ns(), time.process_time_ns()
            import msgpack
            assert len(reader.by) == count
            assert reader.delta_depth == depth
            assert digest(msgpack.packb(reader.index, use_bin_type=True)) == wire_sha
            assert digest(reader.read(member)) == member_sha
            route = getattr(reader, "_research_route", None)
            if label != "public":
                assert route == ("owned-fresh-decoder" if depth else "checkpoint"), (label, depth, route)
        tf, cf = time.perf_counter_ns(), time.process_time_ns()
        receipt.update({
            "archive": os.environ["J24I73_ARCHIVE"],
            "count": count, "index_sha256": wire_sha,
            "member": member, "member_sha256": member_sha,
            "depth": depth, "route": route,
            "constructor_wall_ns": te - ts, "constructor_cpu_ns": ce - cs,
            "open_proof_wall_ns": tf - ts, "open_proof_cpu_ns": cf - cs,
        })
    print(json.dumps(receipt, sort_keys=True), flush=True)


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def attest() -> dict:
    assert git("merge-base", INHERITED, "HEAD") == INHERITED
    assert git("merge-base", PREREG, "HEAD") == PREREG
    assert git("rev-parse", "HEAD:src/cmpct/reader.py") == EXPECTED_READER_BLOB
    assert git("rev-parse", "HEAD", cwd=REFERENCE) == REFERENCE_HEAD
    return {
        "head": git("rev-parse", "HEAD"),
        "main": "80c358f8824ec1b20d349c92ed94c898090969b0",
        "inherited": INHERITED,
        "prereg": PREREG,
        "product_reader_blob": EXPECTED_READER_BLOB,
        "reference_head": REFERENCE_HEAD,
        "python": sys.version,
        "host": platform.platform(),
    }


def original_and_minimal_parity(case, module_dir: Path, count: int) -> dict:
    """Verify source-bound physical archive content independently of timings."""
    import importlib
    import msgpack
    from j24i70_cross_owner_reader import check_all_readers
    previous = sys.path[:]
    sys.path.insert(0, str(module_dir))
    sys.path.insert(0, str(REFERENCE / "research"))
    sys.path.insert(0, str(ROOT / "research"))
    try:
        inherited = check_all_readers(case, count)
        a = importlib.import_module(MODNAME)
        from j24g74_owned_decoder_court import OwnedCMPCT as Original
        from cmpct.reader import CMPCT
        expected_count = count - 63
        member = "f00063.dat"
        assert member in case["expected"]
        for mode in ("A", "B"):
            target = case["paths"][mode]
            physical_before = digest(target.read_bytes())
            with CMPCT(target) as public, Original(target) as original, a.OwnedCMPCT(target) as minimal:
                readers = (public, original, minimal)
                index_bytes = [msgpack.packb(o.index, use_bin_type=True) for o in readers]
                assert index_bytes[0] == index_bytes[1] == index_bytes[2]
                assert all(len(o.by) == expected_count for o in readers)
                assert all(o.read(member) == readers[0].read(member) for o in readers)
                assert all(o.verify() == expected_count for o in readers)
                expected_depth = 63 if mode == "A" else 0
                assert all(o.delta_depth == expected_depth for o in readers)
                assert original._research_route == minimal._research_route == (
                    "owned-fresh-decoder" if mode == "A" else "checkpoint"
                )
            assert digest(target.read_bytes()) == physical_before
        # An impossible 3-byte archive must be rejected on both research routes.
        bogus = module_dir / "invalid.cmpct"
        bogus.write_bytes(b"\x00\x01\x02")
        observations = []
        for klass in (Original, a.OwnedCMPCT):
            try:
                with klass(bogus):
                    pass
                observations.append("ACCEPT")
            except Exception:
                observations.append("REJECT")
        assert observations == ["REJECT", "REJECT"], observations
        return {"inherited_source_semantics": inherited, "malformed_short": observations}
    finally:
        sys.path[:] = previous


def run():
    import hashlib
    from j24i70_cross_owner_reader import make_court
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    output = Path(os.environ.get("J24I73_EVIDENCE", "evidence/j24i73"))
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "cmpct-j24i73-import-cone-v1",
        "status": "STARTED", "source": attest(), "product_credit": 0,
        "protocol": {
            "size": 8192, "depth": 63, "repeats": 8, "import_repeats": 4,
            "labels": list(LABELS), "archive_modes": ["A", "B"],
            "gross": "parent wall spawn -> complete child exit including member SHA",
            "original_algorithm": "source-identical AST, original research donor",
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix="j24i73-") as tmp:
            tmpdir = Path(tmp)
            minimal_path = tmpdir / (MODNAME + ".py")
            report["minimal_module"] = generate_minimal_module(minimal_path)
            shutil.copyfile(minimal_path, output / minimal_path.name)
            case = make_court(tmpdir, 8192)
            report["physical"] = {}
            for mode in ("A", "B"):
                path = case["paths"][mode]
                dst = output / f"{mode}.cmpct"
                shutil.copyfile(path, dst)
                report["physical"][mode] = {
                    "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size,
                    "file": dst.name,
                }
            report["semantic_control"] = original_and_minimal_parity(case, tmpdir, 8192)
            count = 8192 - 63
            member = "f00063.dat"
            common = [str(count), case["index_sha256"], member, case["expected"][member]]
            env = dict(os.environ)
            env["J24I73_MODULE_DIR"] = str(tmpdir)
            raw = {mode: {label: [] for label in LABELS} for mode in ("A", "B")}
            for i in range(8):
                labels = list(LABELS[i % 3:] + LABELS[:i % 3])
                if i >= 4:
                    labels.reverse()
                for mode in (("A", "B") if i % 2 == 0 else ("B", "A")):
                    for label in labels:
                        env["J24I73_ARCHIVE"] = mode
                        args = [
                            sys.executable, str(Path(__file__).resolve()),
                            "--child", label, "open", str(case["paths"][mode]),
                            *common, str(63 if mode == "A" else 0),
                        ]
                        start = time.perf_counter_ns()
                        result = subprocess.run(args, env=env, text=True, capture_output=True)
                        elapsed = time.perf_counter_ns() - start
                        if result.returncode:
                            raise RuntimeError(f"child {label}/{mode}/{i}: {result.stderr}\n{result.stdout}")
                        row = json.loads(result.stdout)
                        assert row["label"] == label and row["archive"] == mode
                        assert row["depth"] == (63 if mode == "A" else 0)
                        row.update({"iteration": i, "whole_process_wall_ns": elapsed})
                        raw[mode][label].append(row)
            import_raw = {label: [] for label in LABELS}
            for i in range(4):
                for label in LABELS:
                    env["J24I73_ARCHIVE"] = "none"
                    args = [sys.executable, str(Path(__file__).resolve()),
                            "--child", label, "import"]
                    start = time.perf_counter_ns()
                    result = subprocess.run(args, env=env, text=True, capture_output=True)
                    elapsed = time.perf_counter_ns() - start
                    if result.returncode:
                        raise RuntimeError(f"import child {label}/{i}: {result.stderr}\n{result.stdout}")
                    row = json.loads(result.stdout)
                    assert row["label"] == label and row["mode"] == "import"
                    row.update({"iteration": i, "whole_process_wall_ns": elapsed})
                    import_raw[label].append(row)
            median = lambda xs, metric: statistics.median(int(x[metric]) for x in xs)
            medians = {
                mode: {
                    label: {
                        metric: median(raw[mode][label], metric)
                        for metric in ("whole_process_wall_ns", "import_wall_ns",
                                       "constructor_wall_ns", "constructor_cpu_ns")
                    }
                    for label in LABELS
                }
                for mode in ("A", "B")
            }
            import_medians = {
                label: {m: median(import_raw[label], m) for m in
                        ("import_wall_ns", "import_cpu_ns", "whole_process_wall_ns")}
                for label in LABELS
            }
            import_saved = (import_medians["original"]["import_wall_ns"]
                            - import_medians["minimal"]["import_wall_ns"])
            crossover = (medians["A"]["minimal"]["whole_process_wall_ns"] /
                         medians["B"]["public"]["whole_process_wall_ns"])
            report.update({
                "raw": raw, "import_only_raw": import_raw,
                "medians": medians, "import_only_medians": import_medians,
                "ratios": {
                    "minimal_A_over_public_B_gross": crossover,
                    "original_A_over_public_B_gross": (
                        medians["A"]["original"]["whole_process_wall_ns"] /
                        medians["B"]["public"]["whole_process_wall_ns"]),
                    "minimal_A_over_original_A_gross": (
                        medians["A"]["minimal"]["whole_process_wall_ns"] /
                        medians["A"]["original"]["whole_process_wall_ns"]),
                },
                "predictions": {
                    "H1_import_cone_saved_10ms": import_saved >= 10_000_000,
                    "H2_gross_minimal_A_at_most_1p20_public_B": crossover <= 1.20,
                    "H3_semantic_identity": True,
                },
                "import_saved_ns": import_saved,
                "status": "PASS_COURT_NOT_PROMOTION",
            })
            assert all(len(raw[m][label]) == 8 for m in raw for label in LABELS)
            assert all(len(import_raw[label]) == 4 for label in LABELS)
            for mode in ("A", "B"):
                assert digest(case["paths"][mode].read_bytes()) == report["physical"][mode]["sha256"]
            print("J24I73_RESULT", json.dumps({
                "predictions": report["predictions"],
                "ratios": report["ratios"],
                "import_saved_ns": import_saved,
            }, sort_keys=True), flush=True)
    except BaseException as exc:
        report["status"] = "FAIL"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(sys.argv[2:])
    elif len(sys.argv) == 1:
        run()
    else:
        raise SystemExit("internal child mode only")
