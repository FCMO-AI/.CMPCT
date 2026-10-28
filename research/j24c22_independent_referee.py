#!/usr/bin/env python3
"""J24C22 independent full-owner referee: no CMPCT or court imports.

Uses a second direct owner/byte derivation, fixed historical signed archive SHA,
complete installed-source/response/process matrix and adversarial receipt probes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
from statistics import median

SOURCE_COMMITS = {
    "published": "80c358f8824ec1b20d349c92ed94c898090969b0",
    "fused": "a66fd593a83cc4c71556d3d86d835c51abd20a96",
    "sealed": "3b6a73f9205f40f11124cd9ff332407e52cebb93",
}
SOURCE_HASHES = {
    "published": "83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff",
    "fused": "b9d7c86d021f26a252d2d8cb4d2ba6cbf4613b9fb743abf1a8264a2343a4ecfe",
    "sealed": "ccb5dfcd45bbef16c880a85b2f66cd91a8b48fa5f42ddab8c506205404f66a5b",
}
ARCHIVE_SHA = "eb695e0236db6d8d7e7896fcc8d3a2b69a47a66f601e47c8c333879176f58067"
ARMS = ("published", "fused", "sealed")
SHAPES = ("Q1_early", "Q16_front_full", "Q16_tail_full")
COUNTS = {"Q1_early": 1, "Q16_front_full": 16, "Q16_tail_full": 16}
METRICS = ("open_wall_ns", "open_cpu_ns", "list_wall_ns", "list_cpu_ns",
           "read_wall_ns", "read_cpu_ns", "session_wall_ns", "session_cpu_ns",
           "outer_process_wall_ns")
BLOCK = 4096
OWNERS = 4096
MIB = 1048576


def reject(msg):
    raise ValueError("J24C22 independent referee: " + msg)


def file_sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for part in iter(lambda: fd.read(MIB), b""):
            h.update(part)
    return h.hexdigest()


def replica_owner(i: int):
    assert 0 <= i < OWNERS
    return hashlib.shake_256(b"CMPCT-J24C21-owner-" + i.to_bytes(4, "big")).digest(BLOCK)


def truth_query(offset: int, count: int, blobs):
    first = offset // BLOCK
    last = (offset + count + BLOCK - 1) // BLOCK
    owner_ids = [((j * 2053 + 17) % OWNERS) for j in range(first, last)]
    joined = b"".join(blobs[k] for k in owner_ids)
    wanted = joined[offset - BLOCK * first:offset - BLOCK * first + count]
    if len(wanted) != count:
        reject("independent query length mismatch")
    return wanted, owner_ids


def validate(report, workset, fixtures_dir):
    if report.get("schema") != "j24c22-full-owner-court-v1":
        reject("report schema")
    if workset.get("schema") != "j24c22-full-owner-workset-v1":
        reject("workset schema")
    if report.get("source_commits") != SOURCE_COMMITS or workset.get("source_commits") != SOURCE_COMMITS:
        reject("historical source commits changed")
    if report.get("source_reader_hashes") != SOURCE_HASHES or workset.get("source_reader_hashes") != SOURCE_HASHES:
        reject("historical installed Reader hashes changed")
    manifest = fixtures_dir / "manifest.json"
    if file_sha(manifest) != workset.get("parent_fixture_manifest_sha256"):
        reject("parent J24C21 fixture manifest changed")
    if report.get("parent_fixture_manifest_sha256") != file_sha(manifest):
        reject("report fixture identity changed")
    parent = json.loads(manifest.read_text(encoding="utf-8"))
    if parent.get("schema") != "j24c21-fixtures-v1":
        reject("parent fixture schema changed")
    profile = parent["profiles"]["large_distinct_8k"]
    if (profile["archive_sha256"] != ARCHIVE_SHA
            or profile["physical_blob_count"] != OWNERS
            or profile["physical_payload_bytes"] != 16 * MIB
            or profile["reference_count"] != 8192
            or profile["logical_bytes"] != 32 * MIB):
        reject("authenticated historical source changed")
    if workset.get("signed_archive_sha256") != ARCHIVE_SHA:
        reject("workset physical archive SHA changed")
    if workset.get("signed_archive") != "large_distinct_8k.cmpct":
        reject("archive name changed")
    archive = fixtures_dir / "large_distinct_8k.cmpct"
    if file_sha(archive) != ARCHIVE_SHA or archive.stat().st_size != 17072796:
        reject("physical archive bytes != independently authenticated historical archive")
    if workset.get("archive_bytes") != archive.stat().st_size or workset.get("logical_bytes") != 32 * MIB:
        reject("archive accounting changed")
    if set(workset.get("shapes", {})) != set(SHAPES):
        reject("workset shape set changed")

    # Independent SHAKE and affine mapping, not the generator's decoder or CMPCT.
    blobs = tuple(replica_owner(i) for i in range(OWNERS))
    truth = {}
    for shape in SHAPES:
        group = workset["shapes"][shape]
        queries = group["queries"]
        if len(queries) != COUNTS[shape]:
            reject("question count changed: " + shape)
        if shape == "Q1_early":
            expected_positions = [(5, 8192)]
        elif shape == "Q16_front_full":
            expected_positions = [(i * MIB, MIB) for i in range(16)]
        else:
            expected_positions = [(16 * MIB + i * MIB, MIB) for i in range(16)]
        combined = hashlib.sha256()
        touched = set()
        for q, (s, n) in zip(queries, expected_positions):
            if (type(q.get("start")) is not int or type(q.get("length")) is not int
                    or (q["start"], q["length"]) != (s, n)):
                reject("preregistered request geometry changed: " + shape)
            expected, ids = truth_query(s, n, blobs)
            touched.update(ids)
            if q.get("sha256") != hashlib.sha256(expected).hexdigest():
                reject("independent answer mismatch: " + shape)
            combined.update(expected)
        expected_bytes = sum(q["length"] for q in queries)
        if group.get("answer_bytes") != expected_bytes:
            reject("answer byte budget changed")
        if group.get("combined_answer_sha256") != combined.hexdigest():
            reject("combined byte identity changed")
        if group.get("distinct_owners_touched") != len(touched):
            reject("declared owner touch count mismatches derived")
        if group.get("unique_owner_payload_bytes") != len(touched) * BLOCK:
            reject("owner byte accounting mismatch")
        if shape != "Q1_early" and (len(touched) != OWNERS or expected_bytes != 16 * MIB):
            reject("full owner coverage not achieved")
        truth[shape] = {"count": len(queries), "bytes": expected_bytes,
                        "owners_touched": len(touched), "stream": combined.hexdigest()}

    repetitions = report.get("repetitions")
    if type(repetitions) is not int or repetitions < 4:
        reject("insufficient independent processes")
    rows = report.get("observations")
    if not isinstance(rows, list) or len(rows) != 3 * 3 * repetitions:
        reject("incomplete 3-arm x 3-shape process matrix")
    groups = defaultdict(list)
    for row in rows:
        if row.get("schema") != "j24c22-full-owner-probe-v1":
            reject("probe schema")
        arm, shape, rep = row.get("arm"), row.get("shape"), row.get("repeat")
        if arm not in ARMS or shape not in SHAPES or type(rep) is not int or not 0 <= rep < repetitions:
            reject("arm/shape/repetition invalid")
        if row.get("source_commit") != SOURCE_COMMITS[arm]:
            reject("source identity drift")
        if row.get("installed_reader_sha256") != SOURCE_HASHES[arm]:
            reject("installed Reader digest mismatch")
        if row.get("signed_archive_sha256") != ARCHIVE_SHA:
            reject("read wrong signed archive")
        if (row.get("answer_count") != truth[shape]["count"]
                or row.get("answer_bytes") != truth[shape]["bytes"]
                or row.get("answer_stream_sha256") != truth[shape]["stream"]):
            reject("byte answer evidence mismatch")
        if not str(row.get("python", "")).startswith("3.11."):
            reject("historical arm not measured with installed CPython 3.11")
        for name in METRICS:
            value = row.get(name)
            if type(value) is not int or value < 0:
                reject("invalid nonnegative timing: " + name)
        if row["session_wall_ns"] < row["open_wall_ns"] + row["list_wall_ns"]:
            reject("impossible wall phase budget")
        if row["session_cpu_ns"] < row["open_cpu_ns"] + row["list_cpu_ns"]:
            reject("impossible CPU phase budget")
        rss = row.get("peak_rss_kib")
        if rss is not None and (type(rss) is not int or rss <= 0):
            reject("invalid RSS sample")
        groups[(shape, arm)].append(row)
    for k, group in groups.items():
        if sorted(row["repeat"] for row in group) != list(range(repetitions)):
            reject("duplicate/missing balanced repetition: " + str(k))
    if len(groups) != len(SHAPES) * len(ARMS):
        reject("incomplete group matrix")

    summary = {}
    for shape in SHAPES:
        by_arm = {}
        for arm in ARMS:
            obs = groups[(shape, arm)]
            by_arm[arm] = {metric: median(x[metric] for x in obs) for metric in METRICS}
            rss = [x["peak_rss_kib"] for x in obs]
            by_arm[arm]["peak_rss_kib"] = median(rss) if all(v is not None for v in rss) else None
            by_arm[arm]["repetitions_sealed_faster_than_published"] = None
        reference, candidate = by_arm["published"], by_arm["sealed"]
        wall_saved = reference["session_wall_ns"] - candidate["session_wall_ns"]
        cpu_saved = reference["session_cpu_ns"] - candidate["session_cpu_ns"]
        material = (wall_saved >= 3000000 and cpu_saved >= 3000000
                    and candidate["session_wall_ns"] <= .95 * reference["session_wall_ns"]
                    and candidate["session_cpu_ns"] <= .95 * reference["session_cpu_ns"])
        q1_veto = (candidate["session_wall_ns"] - reference["session_wall_ns"] >= 3000000
                   and candidate["session_wall_ns"] >= 1.05 * reference["session_wall_ns"]) or (
                   candidate["session_cpu_ns"] - reference["session_cpu_ns"] >= 3000000
                   and candidate["session_cpu_ns"] >= 1.05 * reference["session_cpu_ns"])
        rss_a, rss_b = candidate["peak_rss_kib"], reference["peak_rss_kib"]
        summary[shape] = {
            "median_by_arm": by_arm,
            "sealed_over_published_wall": candidate["session_wall_ns"] / reference["session_wall_ns"],
            "sealed_over_published_cpu": candidate["session_cpu_ns"] / reference["session_cpu_ns"],
            "material_full_owner_research_gain": material if shape != "Q1_early" else None,
            "q1_promotion_veto": q1_veto if shape == "Q1_early" else None,
            "rss_gt_eight_mib_debt": (rss_a - rss_b > 8192) if rss_a is not None and rss_b is not None else None,
        }
    first = summary["Q16_front_full"]["material_full_owner_research_gain"]
    last = summary["Q16_tail_full"]["material_full_owner_research_gain"]
    if first and last:
        decision = "FULL_OWNER_BOTH_TRANSFER"
    elif first or last:
        decision = "FULL_OWNER_PARTIAL_TRANSFER"
    else:
        decision = "NO_MATERIAL_FULL_OWNER_TRANSFER"
    return {
        "schema": "j24c22-independent-full-owner-decision-v1",
        "research_decision": decision, "promotion_authorized": False,
        "validated_independent_processes": len(rows),
        "original_signed_fixture_sha256": ARCHIVE_SHA,
        "fixed_full_owner_coverage": {shape: truth[shape] for shape in SHAPES},
        "results": summary,
        "scope": "installed CPython3.11 Ubuntu, unchanged signed RAW r24; no cold disk IO or release claim",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--workset", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    work_bytes = args.workset.read_bytes()
    report = json.loads(raw)
    workset = json.loads(work_bytes)
    if report.get("workset_sha256") != hashlib.sha256(work_bytes).hexdigest():
        reject("raw report did not bind exact workset")
    result = validate(report, workset, args.fixtures)
    attacks = {
        "source": lambda x: x["observations"][0].__setitem__("source_commit", "0" * 40),
        "reader": lambda x: x["observations"][0].__setitem__("installed_reader_sha256", "0" * 64),
        "archive": lambda x: x["observations"][0].__setitem__("signed_archive_sha256", "0" * 64),
        "answer": lambda x: x["observations"][0].__setitem__("answer_stream_sha256", "0" * 64),
        "timer": lambda x: x["observations"][0].__setitem__("session_cpu_ns", -1),
        "repeat": lambda x: x["observations"][0].__setitem__("repeat", 50),
        "missing": lambda x: x["observations"].pop(),
        "workset": lambda x: x.__setitem__("workset_sha256", "0" * 64),
    }
    for name, attack in attacks.items():
        altered = copy.deepcopy(report)
        attack(altered)
        try:
            if altered.get("workset_sha256") != hashlib.sha256(work_bytes).hexdigest():
                reject("forged workset binding")
            validate(altered, workset, args.fixtures)
        except (ValueError, KeyError, TypeError, AssertionError):
            continue
        reject("accepted forged receipt: " + name)
    result["adversarial_receipts_rejected"] = len(attacks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "research_decision": result["research_decision"],
        "validated_processes": result["validated_independent_processes"],
        "adversarial_receipts_rejected": result["adversarial_receipts_rejected"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
