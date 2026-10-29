#!/usr/bin/env python3
"""J24G34: physical product-candidate court for #620 Reader atop #735 compaction.

Separate derivative of unchanged historical #737 negative experiment; tests
prospective successful bound, preserving original negative evidence unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

PAGE = 4096
SIZES = (2 << 20, 128 << 20)
READER_BLOB = "f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f"
TRANSACTIONS_BLOB = "8d1e46e1fdf408c1d95ce9091e25fa159f0e6264"
BUILDER_BLOB = "387192edd783e02bf7a44a38945214bf9d6c183e"
HEAD = b"H" * PAGE
TAIL = b"T" * PAGE
UPDATE = b"J24I17 exact appended generation\n" * 10


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def create_source(work: Path, size: int, alias: bool) -> Path:
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, K_HARDLINK, S_SPARSE
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_update

    root = work / "tree"
    root.mkdir()
    owner = root / "a-owner.bin"
    with owner.open("wb") as f:
        f.write(HEAD)
        f.seek(size - PAGE)
        f.write(TAIL)
    allocated = owner.stat().st_blocks * 512
    assert allocated < size // 4, ("not physically sparse", size, allocated)
    if alias:
        linked = root / "z-alias.bin"
        os.link(owner, linked)
        assert (owner.stat().st_dev, owner.stat().st_ino) == (
            linked.stat().st_dev, linked.stat().st_ino)
    (root / "small.bin").write_bytes(b"before update")
    path = work / "source.cmpct"
    Builder(root, reproducible=True, workers=1).build(path)
    replacement = work / "new-small.bin"
    replacement.write_bytes(UPDATE)
    append_update(path, "small.bin", replacement)
    with CMPCT(path) as reader:
        row = reader.by["a-owner.bin"]
        assert row[1] == K_FILE and row[4] == size, row
        assert row[6][0] == S_SPARSE, row[6]
        assert reader.read_range("a-owner.bin", 0, PAGE) == HEAD
        assert reader.read_range("a-owner.bin", size - PAGE, PAGE) == TAIL
        assert reader.read("small.bin") == UPDATE
        assert reader.delta_depth >= 1
        if alias:
            linkrow = reader.by["z-alias.bin"]
            assert linkrow[1] == K_HARDLINK, linkrow
            assert linkrow[6][0] == "a-owner.bin", linkrow
            assert linkrow[4] == size
        else:
            assert "z-alias.bin" not in reader.by
    return path


def metadata_snapshot(reader) -> dict:
    from cmpct.codec import K_DIR
    from cmpct.transactions import _compaction_source_metadata
    return {
        "rows": [tuple(row[:5]) for row in reader.files],
        "hardlinks": {row[0]: tuple(row[6]) for row in reader.files
                      if row[1] == 3},
        "metadata": _compaction_source_metadata(reader),
        "file_sha": {row[0]: reader.file_sha256(row[0]).hex()
                     for row in reader.files if row[1] != K_DIR},
        "depth": reader.delta_depth,
    }


def child(source: Path, output: Path, receipt: Path, size: int, alias: bool) -> None:
    from cmpct.reader import CMPCT
    from cmpct.transactions import compact_archive
    import cmpct.reader as reader_module
    installed_path = Path(reader_module.__file__).resolve()
    installed_bytes = installed_path.read_bytes()
    installed_blob = hashlib.sha1(
        b"blob " + str(len(installed_bytes)).encode("ascii") + b"\0" + installed_bytes
    ).hexdigest()
    expected_blob = os.environ.get("J24G34_EXPECTED_READER_BLOB", READER_BLOB)
    assert installed_blob == expected_blob, (
        "samewire historical/candidate Reader provenance mismatch",
        str(installed_path), installed_blob, expected_blob
    )
    source_sha = digest(source)
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    compact_archive(source, output)
    wall = time.perf_counter_ns() - t0
    cpu = time.process_time_ns() - c0
    # Capture RSS before extra postcondition inspection to isolate compaction itself.
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with CMPCT(source) as a, CMPCT(output) as b:
        before = metadata_snapshot(a)
        after = metadata_snapshot(b)
        assert {k: v for k, v in before.items() if k != "depth"} == {
            k: v for k, v in after.items() if k != "depth"
        }, "archive logical/indexed metadata drift"
        assert before["depth"] >= 1 and after["depth"] == 0, "not a true compaction"
        assert b.by["a-owner.bin"][4] == size
        assert b.read_range("a-owner.bin", 0, PAGE) == HEAD
        assert b.read_range("a-owner.bin", size - PAGE, PAGE) == TAIL
        assert b.read("small.bin") == UPDATE
        assert ("z-alias.bin" in b.by) == alias
        if alias:
            assert b.by["z-alias.bin"][6][0] == "a-owner.bin"
            assert b.read_range("z-alias.bin", 0, PAGE) == HEAD
    assert digest(source) == source_sha, "source mutated by compaction"
    record = {
        "logical_owner_bytes": size,
        "alias": alias,
        "source_sha256": source_sha,
        "source_bytes": source.stat().st_size,
        "output_sha256": digest(output),
        "output_bytes": output.stat().st_size,
        "source_depth": before["depth"],
        "output_depth": after["depth"],
        "peak_rss_kib_compaction": peak_kib,
        "compaction_wall_ns": wall,
        "compaction_cpu_ns": cpu,
        "rows_metadata_and_sha_equal": True,
        "source_unchanged": True,
        "exact_sparse_owner": True,
        "genuine_hardlink_alias": alias,
        "release_credit": 0,
        "installed_reader_git_blob": installed_blob,
        "installed_reader_path": str(installed_path),
    }
    receipt.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps(record, sort_keys=True))


def parent() -> None:
    root = Path(os.environ["J24G34_ARTIFACT_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="j24g34-court-") as td:
        work = Path(td)
        cases = {}
        for size in SIZES:
            for alias in (False, True):
                w = work / f"{size}-alias{int(alias)}"
                w.mkdir()
                source = create_source(w, size, alias)
                prefix = f"{size}-alias{int(alias)}"
                shutil.copyfile(source, root / f"source-{prefix}.cmpct")
                cases[(size, alias)] = {
                    "path": source, "sha": digest(source), "runs": [],
                    "name": prefix,
                }

        # A/B/B/A per size; each condition reuses its exact source bytes.
        for size in SIZES:
            for index, alias in enumerate((False, True, True, False)):
                case = cases[(size, alias)]
                prefix = f"{case['name']}-trial{index}"
                output = work / f"{prefix}.cmpct"
                receipt = work / f"{prefix}.json"
                proc = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--child",
                     str(size), str(int(alias)), str(case["path"]),
                     str(output), str(receipt)],
                    cwd=work, capture_output=True, text=True, timeout=300,
                    env={**os.environ, "CMPCT_ENCODE_WORKERS": "1"}
                )
                (root / f"{prefix}.stdout.txt").write_text(proc.stdout)
                (root / f"{prefix}.stderr.txt").write_text(proc.stderr)
                if proc.returncode:
                    raise AssertionError(f"child {prefix} rc={proc.returncode}: {proc.stderr[-3500:]}")
                item = json.loads(receipt.read_text())
                assert item["source_sha256"] == case["sha"]
                assert item["rows_metadata_and_sha_equal"]
                case["runs"].append(item)
                shutil.copyfile(output, root / f"output-{prefix}.cmpct")
                shutil.copyfile(receipt, root / f"receipt-{prefix}.json")

        for case in cases.values():
            assert len(case["runs"]) == 2
            assert digest(case["path"]) == case["sha"]
            assert len({x["output_sha256"] for x in case["runs"]}) == 1, (
                "same-source output not deterministic", case["name"]
            )

        results = []
        for size in SIZES:
            own = cases[(size, False)]["runs"]
            aliases = cases[(size, True)]["runs"]
            owner_peak = max(x["peak_rss_kib_compaction"] for x in own)
            alias_peak = min(x["peak_rss_kib_compaction"] for x in aliases)
            delta = alias_peak - owner_peak
            results.append({
                "size": size, "owner_only_peak_max_kib": owner_peak,
                "alias_peak_min_kib": alias_peak, "conservative_delta_kib": delta,
                "source_owner_only_sha": cases[(size, False)]["sha"],
                "source_alias_sha": cases[(size, True)]["sha"],
                "owner_only_trials": own, "alias_trials": aliases,
            })
        large = next(x for x in results if x["size"] == 128 << 20)
        decision = ("SPARSE_ALIAS_RSS_BOUND_CANDIDATE_CONFIRMED"
                    if (all(t["peak_rss_kib_compaction"] < 64 * 1024 for t in large["alias_trials"]) and large["conservative_delta_kib"] < 32 * 1024)
                    else "SPARSE_ALIAS_COMPACTION_RSS_DEBT_PERSISTS")
        outcome = {
            "schema": "cmpct-j24g34-owner-alias-product-composition-v1",
            "exact_parent": "82e90eca58ed0580df191378947004e4061d53c3",
            "reader_source_blob": READER_BLOB,
            "builder_source_blob": BUILDER_BLOB,
            "transactions_source_blob": TRANSACTIONS_BLOB,
            "topology_controls": "2MiB/128MiB, owner alone vs genuine owner+alias",
            "trials_per_condition": 2,
            "observations": results,
            "decision": decision,
            "product_candidate_only": True,
            "release_credit": 0,
        }
        (root / "report.json").write_text(json.dumps(outcome, sort_keys=True, indent=2) + "\n")
        print(json.dumps(outcome, sort_keys=True, indent=2))
        # Separate prospective positive court; keep original #737 negative historical
        # instrument, frozen comparisons and source artifacts entirely untouched.
        assert decision == "SPARSE_ALIAS_RSS_BOUND_CANDIDATE_CONFIRMED", outcome


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(Path(sys.argv[4]), Path(sys.argv[5]), Path(sys.argv[6]),
              int(sys.argv[2]), bool(int(sys.argv[3])))
    else:
        parent()
