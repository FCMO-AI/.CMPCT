"""O73: gap-separated physical ZIP ownership versus fully charged original controls (research only).

Each counterfactual loads an isolated in-memory actual Builder, never an editable install;
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



_CASES = {
    "six_large_two_small": (6, 2),
    "five_large_three_small": (5, 3),
    "seven_large_one_small": (7, 1),
    "homogeneous_eight_large": (8, 0),
}

def _corpus(root: Path, case: str) -> dict[str, str]:
    root.mkdir()
    nlarge, nsmall = _CASES[case]
    output = {}
    for i in range(nlarge + nsmall):
        name = f"m{i:02d}.zip"
        n = 128 * 1024 if i < nlarge else 1024
        data = random.Random(73000 + i * 19 + len(case) * 791).randbytes(n)
        member = zipfile.ZipInfo(f"payload_{i}.bin", date_time=(2020, 1, 2, 3, 4, 6))
        member.compress_type = zipfile.ZIP_DEFLATED
        member.external_attr = 0o100644 << 16
        with zipfile.ZipFile(root / name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            z.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        output[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert len(output) == 8
    return output


def _oracle_classes():
    source_path = Path(shipping_builder.__file__)
    original = source_path.read_text(encoding="utf-8")
    gate = "if len(deferred)>=8:"
    assert original.count(gate) == 1, "Source changed: original O70 owner no longer available"
    disabled = original.replace(gate, "if len(deferred)>=1073741824:")
    # The split-owner design is a distinct physical-ownership frame, not a count-only gate.
    original_block = (
        "        if len(deferred)>=8:\n"
        "            buf=bytearray();packed=[]\n"
        "            for p,rel,st,mode in deferred:\n"
        "                raw=p.read_bytes();off=len(buf);buf+=raw;packed.append((rel,st,mode,off,len(raw),sha(raw)))\n"
        "            ph=self.add_content(bytes(buf),'.cmpct-container-pack')\n"
        "            for rel,st,mode,off,ln,rh in packed:\n"
        "                self.files.append([rel,K_FILE,mode,st.st_mtime_ns,ln,rh,[S_PACK,ph,off,ln]])\n"
        "        else:\n"
    )
    assert original.count(original_block) == 1, "Unsafe oracle patch: source block drift"
    new_block = (
        "        if len(deferred)>=8:\n"
        "            # O73 ORACLE ONLY: find largest generic size gap, never look at fixture identities.\n"
        "            _sizes=sorted(int(row[2].st_size) for row in deferred)\n"
        "            _cut=max(range(1,len(_sizes)),key=lambda j:_sizes[j]/max(1,_sizes[j-1]))\n"
        "            _gap=_sizes[_cut]/max(1,_sizes[_cut-1])\n"
        "            if _gap>=16:\n"
        "                _big=[row for row in deferred if row[2].st_size>=_sizes[_cut]]\n"
        "                _small=[row for row in deferred if row[2].st_size<_sizes[_cut]]\n"
        "            else:\n"
        "                _big=deferred;_small=[]\n"
        "            assert _big and len(_big)+len(_small)==len(deferred)\n"
        "            buf=bytearray();packed=[]\n"
        "            for p,rel,st,mode in _big:\n"
        "                raw=p.read_bytes();off=len(buf);buf+=raw;packed.append((rel,st,mode,off,len(raw),sha(raw)))\n"
        "            ph=self.add_content(bytes(buf),'.cmpct-container-pack')\n"
        "            for rel,st,mode,off,ln,rh in packed:\n"
        "                self.files.append([rel,K_FILE,mode,st.st_mtime_ns,ln,rh,[S_PACK,ph,off,ln]])\n"
        "            for p,rel,st,mode in _small:\n"
        "                recipe=make_vzip_recipe(p,self.add_content)\n"
        "                if recipe is None:\n"
        "                    raw=p.read_bytes();ref=self.add_content(raw,p.suffix.lower());storage=[S_BLOB,ref]\n"
        "                else:\n"
        "                    rid=len(self.recipes);self.recipes.append(recipe);storage=[S_VZIP,rid]\n"
        "                rawsha=sha(p.read_bytes())\n"
        "                self.files.append([rel,K_FILE,mode,st.st_mtime_ns,st.st_size,rawsha,storage])\n"
        "        else:\n"
    )
    split = original.replace(original_block, new_block)
    assert split.replace(new_block, original_block) == original
    def load(name: str, source: str):
        module = types.ModuleType("cmpct._o73_" + name)
        module.__package__ = "cmpct"
        module.__file__ = str(source_path)
        sys.modules[module.__name__] = module
        exec(compile(source, str(source_path) + ":O73-" + name, "exec"), module.__dict__)
        return module.Builder, hashlib.sha256(source.encode()).hexdigest()
    independent, individual_sha = load("individual", disabled)
    split_owner, split_sha = load("split", split)
    return {"shipping": shipping_builder.Builder, "individual": independent, "split": split_owner}, {
        "shipping_source_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "individual_source_sha256": individual_sha,
        "split_source_sha256": split_sha,
    }

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



def test_o73_gap_owner_charged_originals_and_structural_holdouts(tmp_path: Path):
    builders, source_shas = _oracle_classes()
    results = {"hypothesis": "physical size-gap separated owner versus all-pack/all-individual same-input controls",
               "status": "ORACLE_ONLY_NO_PRODUCT_CREDIT", "git_base_head": "887e419b4ccbef06ac21a7920e06f55743333664",
               "shipping_builder_blob": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
               "source_shas": source_shas, "gap_rule": "largest_adjacent_physical_size_ratio>=16",
               "cases": {}, "limitations": [
                   "one Ubuntu host; isolated in-memory candidate, not a product change",
                   "multiple Builder instances in same installed Python process, not independent interpreter startups",
                   "fresh Reader objects but OS page cache not controlled",
                   "decoded_blob_bytes are actual blob invocations, not kernel disk I/O",
                   "synthetic limited eight-member ZIP corpora, no external competitors",
                   "no source-concurrency, update, full release performance or platform gate credit"]}
    evidence_path = Path("o73-evidence.json")
    def preserve():
        evidence_path.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")

    for case in _CASES:
        root = tmp_path / (case + "-source")
        source_hashes = _corpus(root, case)
        selected = "m07.zip"
        expected = (root / selected).read_bytes()
        prefix = expected[:64]
        # Six complete archive builds per structural case; order counterbalanced.
        sequence = ["shipping", "split", "individual", "individual", "split", "shipping"]
        raw = []
        for k, tag in enumerate(sequence):
            output = tmp_path / f"{case}-{tag}-{k}.cmpct"
            wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
            builders[tag](root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(output)
            create_wall_ns = time.perf_counter_ns() - wall0
            create_cpu_ns = time.process_time_ns() - cpu0
            with CMPCT(output) as ar:
                assert ar.verify() == len(source_hashes)
                rows = {row[0]: row for row in ar.index["files"]}
                assert sorted(rows) == sorted(source_hashes)
                kinds = {name: int(rows[name][6][0]) for name in source_hashes}
                for name, checksum in source_hashes.items():
                    assert hashlib.sha256(ar.read(name)).hexdigest() == checksum, (case, tag, name)
                # Run full-tree extract on every arm at least once, not only logical read.
                if k < 3:
                    out_tree = tmp_path / f"{case}-extract-{tag}"
                    ar.extractall(out_tree, metadata=False)
                    for name, checksum in source_hashes.items():
                        assert hashlib.sha256((out_tree / name).read_bytes()).hexdigest() == checksum
            samples = [_cold_sample(output, selected, prefix) for _ in range(4)]
            raw.append({
                "policy": tag, "sequence": k, "archive_size": output.stat().st_size,
                "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "create_wall_ns": create_wall_ns, "create_cpu_ns": create_cpu_ns,
                "selected_storage_kind": kinds[selected], "all_storage_kinds": kinds,
                "read_samples": samples,
            })
        for tag in builders:
            same = [r for r in raw if r["policy"] == tag]
            assert len(same) == 2
            assert same[0]["archive_sha256"] == same[1]["archive_sha256"], (case, tag, "nondeterministic bytes")
            assert same[0]["archive_size"] == same[1]["archive_size"]
        def metric(tag: str, field: str):
            rows = [r for r in raw if r["policy"] == tag]
            if field in ("wall_ns", "cpu_ns", "decoded_blob_bytes", "stored_blob_bytes", "unique_blob_count"):
                return statistics.median([s[field] for r in rows for s in r["read_samples"]])
            return statistics.median(r[field] for r in rows)
        summary = {}
        for tag in builders:
            summary[tag] = {
                "archive_size": metric(tag, "archive_size"),
                "create_wall_ns": metric(tag, "create_wall_ns"),
                "create_cpu_ns": metric(tag, "create_cpu_ns"),
                "read_wall_ns": metric(tag, "wall_ns"),
                "read_cpu_ns": metric(tag, "cpu_ns"),
                "decoded_blob_bytes": metric(tag, "decoded_blob_bytes"),
                "stored_blob_bytes": metric(tag, "stored_blob_bytes"),
                "unique_blob_count": metric(tag, "unique_blob_count"),
                "selected_kind": [r["selected_storage_kind"] for r in raw if r["policy"] == tag],
            }
        assert all(x == S_PACK for x in summary["shipping"]["selected_kind"])
        assert summary["split"]["decoded_blob_bytes"] > 0
        savings = summary["shipping"]["decoded_blob_bytes"] / summary["split"]["decoded_blob_bytes"]
        create_ratio = summary["split"]["create_wall_ns"] / summary["shipping"]["create_wall_ns"]
        size_debt = (summary["split"]["archive_size"] - summary["shipping"]["archive_size"]) / summary["shipping"]["archive_size"]
        credible = savings >= 20 and create_ratio < 2 and size_debt <= 0.01
        if case == "homogeneous_eight_large":
            shipping_shas = {r["archive_sha256"] for r in raw if r["policy"] == "shipping"}
            split_shas = {r["archive_sha256"] for r in raw if r["policy"] == "split"}
            assert shipping_shas == split_shas, "homogeneous no-gap path changed physical archive bytes"
            assert savings == 1, "homogeneous split should not invent another owner"
        else:
            assert all(k != S_PACK for k in summary["split"]["selected_kind"]), (case, "small member still captive")
            assert all(k == S_PACK for k in summary["shipping"]["selected_kind"])
        results["cases"][case] = {
            "input_sha256": source_hashes,
            "input_sizes": {name: (root / name).stat().st_size for name in source_hashes},
            "selected": selected, "selected_length": len(expected), "read_length": len(prefix),
            "summary": summary, "decoded_savings_ratio": savings, "create_wall_ratio": create_ratio,
            "complete_size_debt_fraction": size_debt, "credible_split_conjunction": credible, "raw": raw,
        }
        preserve()
        print("O73_CASE_RESULT=" + json.dumps({"case": case, "decoded_savings_ratio": savings, "create_wall_ratio": create_ratio,
                                               "complete_size_debt_fraction": size_debt, "credible_split_conjunction": credible}, sort_keys=True))
    results["primary_decision"] = ("CREDIBLE_SPLIT_HEADROOM" if results["cases"]["six_large_two_small"]["credible_split_conjunction"]
                                   else "NOT_CREDIBLE_IN_TESTED_SCOPE")
    preserve()
    print("O73_DECISION=" + results["primary_decision"])
