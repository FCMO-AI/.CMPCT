"""O70: exact-source, same-input eight-ZIP cohort admission oracle (research only).

The counterfactual changes one isolated Builder policy expression in memory;
the shipping product and historical runner are never mutated.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import statistics
import sys
import time
import types
import zipfile
from pathlib import Path

import cmpct.builder as shipping_builder
from cmpct.codec import S_PACK, S_VZIP
from cmpct.reader import CMPCT


def _corpus(root: Path) -> dict[str, str]:
    root.mkdir()
    output = {}
    for i in range(8):
        name = f"m{i:02d}.zip"
        n = 128 * 1024 if i < 6 else 1024
        # Fixed per-file PRNG creates unrelated, stable opaque-compression sources.
        data = random.Random(70000 + i).randbytes(n)
        member = zipfile.ZipInfo(f"payload_{i}.bin", date_time=(2020, 1, 2, 3, 4, 6))
        member.compress_type = zipfile.ZIP_DEFLATED
        member.external_attr = 0o100644 << 16
        with zipfile.ZipFile(root / name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            z.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        output[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    return output


def _oracle_class():
    source_path = Path(shipping_builder.__file__)
    original = source_path.read_text(encoding="utf-8")
    old = "if len(deferred)>=8:"
    assert original.count(old) == 1, "source changed: this bounded oracle cannot be trusted"
    # The only experimental degree of freedom is creator cohort admission.
    derived = original.replace(old, "if len(deferred)>=1073741824:")
    assert derived.replace("if len(deferred)>=1073741824:", old) == original
    module = types.ModuleType("cmpct._o70_noncohort_oracle")
    module.__package__ = "cmpct"
    module.__file__ = str(source_path)
    # CPython dataclasses resolves postponed annotations through sys.modules.
    # Register this ephemeral standalone science module without altering cmpct.builder.
    sys.modules[module.__name__] = module
    exec(compile(derived, str(source_path) + ":O70-oracle", "exec"), module.__dict__)
    return module.Builder, hashlib.sha256(original.encode()).hexdigest(), hashlib.sha256(derived.encode()).hexdigest()


def _cold_sample(path: Path, selected: str, prefix: bytes) -> dict:
    with CMPCT(path) as ar:
        touched = []
        unwrapped = ar._blob

        def counted(idx):
            desc = ar.blobs[idx]
            touched.append((idx, int(desc[1]), int(desc[2])))
            return unwrapped(idx)

        ar._blob = counted
        t0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
        actual = ar.read_range(selected, 0, len(prefix))
        wall = time.perf_counter_ns() - t0
        cpu = time.process_time_ns() - cpu0
        assert actual == prefix
        unique = {i: (usize, csize) for i, usize, csize in touched}
        return {
            "wall_ns": wall, "cpu_ns": cpu,
            "decoded_blob_bytes": sum(v[0] for v in unique.values()),
            "stored_blob_bytes": sum(v[1] for v in unique.values()),
            "blob_invocations": touched,
            "unique_blob_count": len(unique),
        }


def test_exact_same_tree_eight_zip_admission_discontinuity(tmp_path: Path):
    root = tmp_path / "source"
    source_hashes = _corpus(root)
    Oracle, shipping_sha, oracle_sha = _oracle_class()
    selected = "m07.zip"
    expected = (root / selected).read_bytes()
    prefix = expected[:64]
    results = []
    patterns = [("shipping", shipping_builder.Builder), ("oracle", Oracle),
                ("oracle", Oracle), ("shipping", shipping_builder.Builder)]
    for k, (tag, builder_class) in enumerate(patterns):
        output = tmp_path / f"real-{tag}-{k}.cmpct"
        wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
        builder_class(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(output)
        create_wall = time.perf_counter_ns() - wall0
        create_cpu = time.process_time_ns() - cpu0
        with CMPCT(output) as ar:
            assert ar.verify() == len(source_hashes)
            rows = {r[0]: r for r in ar.index["files"]}
            assert sorted(rows) == sorted(source_hashes)
            kinds = {name: int(rows[name][6][0]) for name in source_hashes}
            for name, checksum in source_hashes.items():
                assert hashlib.sha256(ar.read(name)).hexdigest() == checksum
            extracted = tmp_path / f"extracted-{tag}-{k}"
            ar.extractall(extracted, metadata=False)
            for name in source_hashes:
                assert (extracted / name).read_bytes() == (root / name).read_bytes()
        trials = [_cold_sample(output, selected, prefix) for _ in range(5)]
        results.append({
            "policy": tag, "sequence": k, "archive_size": output.stat().st_size,
            "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "create_wall_ns": create_wall, "create_cpu_ns": create_cpu,
            "selected_storage_kind": kinds[selected], "all_storage_kinds": kinds,
            "selected_sample": trials,
        })

    assert all(r["selected_storage_kind"] == S_PACK for r in results if r["policy"] == "shipping")
    assert all(r["selected_storage_kind"] == S_VZIP for r in results if r["policy"] == "oracle")
    for tag in ("shipping", "oracle"):
        pair = [r for r in results if r["policy"] == tag]
        assert pair[0]["archive_sha256"] == pair[1]["archive_sha256"], "same-policy build not deterministic"
        assert pair[0]["archive_size"] == pair[1]["archive_size"]

    def get_median(tag, metric):
        rows = [r for r in results if r["policy"] == tag]
        if metric in ("wall_ns", "cpu_ns", "decoded_blob_bytes", "stored_blob_bytes"):
            return statistics.median([s[metric] for r in rows for s in r["selected_sample"]])
        return statistics.median([r[metric] for r in rows])

    current = get_median("shipping", "decoded_blob_bytes")
    control = get_median("oracle", "decoded_blob_bytes")
    assert control > 0
    ratio = current / control
    evidence = {
        "question": "eight-ZIP whole-cohort policy vs same-input non-cohort policy oracle",
        "status": "ORACLE_ONLY_NO_PRODUCT_CREDIT",
        "shipping_builder_git_blob": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
        "shipping_source_sha256": shipping_sha,
        "single_expression_oracle_sha256": oracle_sha,
        "input_sha256": source_hashes,
        "selected_member": selected, "selected_length": len(expected), "read_length": len(prefix),
        "decoded_bytes_ratio_shipping_to_oracle": ratio,
        "hypothesis_over_20x": ratio > 20,
        "archive_size_shipping": get_median("shipping", "archive_size"),
        "archive_size_oracle": get_median("oracle", "archive_size"),
        "create_wall_ns_shipping": get_median("shipping", "create_wall_ns"),
        "create_wall_ns_oracle": get_median("oracle", "create_wall_ns"),
        "selective_read_wall_ns_shipping": get_median("shipping", "wall_ns"),
        "selective_read_wall_ns_oracle": get_median("oracle", "wall_ns"),
        "raw": results,
        "limitations": ["single deterministic same-input synthetic tree", "one host", "page cache not controlled",
                        "in-memory one-expression policy oracle, not shippable product",
                        "decoded blob bytes reflect actual read calls, not measured physical disk I/O"],
    }
    Path("o70-evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print("O70_RESULT_JSON=" + json.dumps({k: v for k, v in evidence.items() if k != "raw"}, sort_keys=True))
