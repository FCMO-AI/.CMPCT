from __future__ import annotations

"""Exact-public-corpus incremental oracle for v0.30 Latent Sequence Microprograms.

The incumbent is the *actual G3/G4 Hierarchical Geometry payload* on each <=512 KiB node.  LTM1 therefore
has to earn bytes beyond the already-large Geometry win.  For every selected LTM1 node the probe also rebuilds
that exact separator layout with lexical-integer synthesis disabled.  This separates the value of generic
period/dictionary/alphabet codelets from the new latent-integer/microprogram layer.

Claim boundary: detached physical-node payload accounting only.  A green result authorizes later authenticated
GIR integration research, not a release, version bump, or merge.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_sequence_microprograms as LTM
from experiments import entropygraph_v030_sequence_microprograms_safe as SAFE  # installs hardened grammar

EXPECTED_TREES = {
    "05_logs_and_telemetry": "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931",
    "04_analytics_and_database": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "09_ml_artifacts": "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d",
}
TARGETS = (
    ("05_logs_and_telemetry", "app-00.log", "logs"),
    ("05_logs_and_telemetry", "app-01.log", "logs"),
    ("05_logs_and_telemetry", "app-02.log", "logs"),
    ("05_logs_and_telemetry", "app-03.log", "logs"),
    ("05_logs_and_telemetry", "app-04.log", "logs"),
    ("05_logs_and_telemetry", "app-05.log", "logs"),
    ("04_analytics_and_database", "events.csv", "analytics-text"),
    ("04_analytics_and_database", "events.jsonl", "analytics-text"),
    ("09_ml_artifacts", "training.log", "ml-text"),
    ("09_ml_artifacts", "tokenizer.json", "ml-text"),
)

MIN_SINGLE_FILE_SAVING = 32 * 1024
MIN_AGGREGATE_SAVING = 128 * 1024
MIN_LATENT_INTEGER_EXTRA = 32 * 1024

MODEL_NAMES = {
    LTM.INT_VARINT: "varint",
    LTM.INT_FOR: "for",
    LTM.INT_DELTA: "delta",
    LTM.INT_DELTA2: "delta2",
    LTM.INT_AFFINE: "affine",
    LTM.INT_SAWTOOTH: "sawtooth",
}
CODELET_NAMES = {
    LTM.TAG_RAW: "raw",
    LTM.TAG_PERIOD: "period",
    LTM.TAG_DICTIONARY: "dictionary",
    LTM.TAG_ALPHABET: "alphabet",
    LTM.TAG_LEXINT: "lexint",
}


def _generate(parent: Path) -> dict[str, Path]:
    shutil.rmtree(parent, ignore_errors=True)
    parent.mkdir(parents=True)
    neutral.corpus_logs(parent)
    repair.normalize_workload(parent / "05_logs_and_telemetry")
    neutral.corpus_analytics(parent)
    neutral.corpus_ml(parent)
    roots = {name: parent / name for name in EXPECTED_TREES}
    for name, root in roots.items():
        got = neutral.tree_hash(root)
        if got != EXPECTED_TREES[name]:
            raise RuntimeError(f"LTM source identity drift for {name}: expected {EXPECTED_TREES[name]}, got {got}")
    return roots


def _compress(transformed: bytes) -> bytes:
    payload = LTM.G.zc(transformed, LTM.EXACT_LEVEL)
    return payload if len(payload) < len(transformed) else transformed


def _parse_codelets(transformed: bytes) -> tuple[dict[str, int], dict[str, int]]:
    if transformed[:4] != LTM.MAGIC:
        raise RuntimeError("LTM stats parser received non-LTM physical bytes")
    row_count, pos = LTM._get_varint(transformed, 6)
    field_counts = []
    for _ in range(row_count):
        count, pos = LTM._get_varint(transformed, pos)
        field_counts.append(count)
    max_fields, pos = LTM._get_varint(transformed, pos)
    if max_fields != max(field_counts, default=0):
        raise RuntimeError("LTM stats parser field declaration mismatch")

    codelets = {name: 0 for name in CODELET_NAMES.values()}
    models = {name: 0 for name in MODEL_NAMES.values()}
    for _ in range(max_fields):
        if pos >= len(transformed):
            raise RuntimeError("short LTM stats column")
        tag = transformed[pos]
        pos += 1
        payload_len, pos = LTM._get_varint(transformed, pos)
        end = pos + payload_len
        if end > len(transformed) or tag not in CODELET_NAMES:
            raise RuntimeError("invalid LTM stats column")
        codelets[CODELET_NAMES[tag]] += 1
        if tag == LTM.TAG_LEXINT:
            payload = transformed[pos:end]
            cursor = 1
            prefix_len, cursor = LTM._get_varint(payload, cursor)
            cursor += prefix_len
            suffix_len, cursor = LTM._get_varint(payload, cursor)
            cursor += suffix_len
            _, cursor = LTM._get_varint(payload, cursor)  # lexical width
            model_len, cursor = LTM._get_varint(payload, cursor)
            model_end = cursor + model_len
            if model_end != len(payload) or model_len < 1:
                raise RuntimeError("invalid LTM lexint model framing")
            kind = payload[cursor]
            if kind not in MODEL_NAMES:
                raise RuntimeError("unknown LTM integer model in stats parser")
            models[MODEL_NAMES[kind]] += 1
        pos = end
    if pos != len(transformed):
        raise RuntimeError("trailing LTM stats bytes")
    return codelets, models


def _without_lexint_payload(raw: bytes, primary: int, secondary: int, hierarchical_payload_bytes: int) -> int:
    """Return the best no-lexint alternative for causal novelty attribution.

    The transform grammar and separator pair remain identical.  Only lexical-integer synthesis is disabled;
    inherited G3/G4 remains a competitor so a bad generic-codelet layout cannot make latent integers look good.
    """
    original = LTM._encode_lexint
    try:
        LTM._encode_lexint = lambda _values: None
        transformed, _ = SAFE.build_transform(raw, primary, secondary)
    finally:
        LTM._encode_lexint = original
    if SAFE.inverse(transformed, len(raw)) != raw:
        raise RuntimeError("no-lexint LTM counterfactual failed exact inverse")
    return min(hierarchical_payload_bytes, len(_compress(transformed)))


def _run_file(path: Path, role: str) -> dict:
    raw = path.read_bytes()
    chunks = LTM.G.L._balanced_chunks(raw)
    rows = []
    for index, chunk in enumerate(chunks):
        result = SAFE.audition(chunk)
        candidate_bytes = int(result["payload_bytes"])
        saving = int(result["saving_vs_hierarchical_bytes"])
        incumbent_bytes = candidate_bytes + saving
        latent_extra = 0
        codelets = {name: 0 for name in CODELET_NAMES.values()}
        models = {name: 0 for name in MODEL_NAMES.values()}
        if result["kind"] == "latent-microprogram":
            transformed = bytes(result["physical"])
            if SAFE.inverse(transformed, len(chunk)) != chunk:
                raise RuntimeError("selected LTM node failed independent benchmark inverse")
            codelets, models = _parse_codelets(transformed)
            no_lexint = _without_lexint_payload(
                chunk,
                int(result["primary"]),
                int(result["secondary"]),
                incumbent_bytes,
            )
            latent_extra = max(0, no_lexint - candidate_bytes)
        rows.append({
            "chunk": index,
            "logical_bytes": len(chunk),
            "incumbent_payload_bytes": incumbent_bytes,
            "candidate_payload_bytes": candidate_bytes,
            "saving_vs_g3g4_bytes": saving,
            "selected": result["kind"] == "latent-microprogram",
            "primary": result["primary"],
            "secondary": result["secondary"],
            "latent_integer_extra_bytes": latent_extra,
            "codelets": codelets,
            "integer_models": models,
        })

    incumbent_total = sum(row["incumbent_payload_bytes"] for row in rows)
    candidate_total = sum(row["candidate_payload_bytes"] for row in rows)
    saving_total = incumbent_total - candidate_total
    codelets = {name: sum(row["codelets"][name] for row in rows) for name in CODELET_NAMES.values()}
    models = {name: sum(row["integer_models"][name] for row in rows) for name in MODEL_NAMES.values()}
    return {
        "file": path.name,
        "role": role,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "logical_bytes": len(raw),
        "chunks": len(rows),
        "g3g4_payload_bytes": incumbent_total,
        "ltm_payload_bytes": candidate_total,
        "saving_vs_g3g4_bytes": saving_total,
        "smaller_than_g3g4_pct": saving_total / max(1, incumbent_total) * 100.0,
        "selected_chunks": sum(row["selected"] for row in rows),
        "latent_integer_extra_bytes": sum(row["latent_integer_extra_bytes"] for row in rows),
        "codelets": codelets,
        "integer_models": models,
        "rows": rows,
    }


def run(work_root: Path) -> dict:
    roots = _generate(work_root / "corpora")
    files = []
    for workload, rel, role in TARGETS:
        path = roots[workload] / rel
        if not path.is_file():
            raise RuntimeError(f"missing frozen LTM target: {path}")
        row = _run_file(path, role)
        row["workload"] = workload
        files.append(row)

    saving = sum(row["saving_vs_g3g4_bytes"] for row in files)
    latent_extra = sum(row["latent_integer_extra_bytes"] for row in files)
    codelets = {name: sum(row["codelets"][name] for row in files) for name in CODELET_NAMES.values()}
    models = {name: sum(row["integer_models"][name] for row in files) for name in MODEL_NAMES.values()}
    totals = {
        "files": len(files),
        "g3g4_payload_bytes": sum(row["g3g4_payload_bytes"] for row in files),
        "ltm_payload_bytes": sum(row["ltm_payload_bytes"] for row in files),
        "saving_vs_g3g4_bytes": saving,
        "max_single_file_saving_bytes": max(row["saving_vs_g3g4_bytes"] for row in files),
        "files_improved": sum(row["saving_vs_g3g4_bytes"] > 0 for row in files),
        "files_regressed": sum(row["saving_vs_g3g4_bytes"] < 0 for row in files),
        "selected_chunks": sum(row["selected_chunks"] for row in files),
        "latent_integer_extra_bytes": latent_extra,
        "codelets": codelets,
        "integer_models": models,
        "residualized_models": models["affine"] + models["sawtooth"],
        "mechanism_gate": (
            saving >= MIN_AGGREGATE_SAVING
            and max(row["saving_vs_g3g4_bytes"] for row in files) >= MIN_SINGLE_FILE_SAVING
            and latent_extra >= MIN_LATENT_INTEGER_EXTRA
            and all(row["saving_vs_g3g4_bytes"] >= 0 for row in files)
            and sum(row["selected_chunks"] for row in files) > 0
            and codelets["lexint"] > 0
            and (models["affine"] + models["sawtooth"]) > 0
        ),
    }
    return {
        "schema": "cmpct-v030-sequence-microprograms-probe-v1",
        "status": "CHILD_RESEARCH_INCREMENTAL_PAYLOAD_ORACLE_NOT_RELEASE",
        "claim_boundary": (
            "Exact public-generator text-file bytes; detached <=512 KiB node payload accounting only. "
            "The incumbent is actual G3/G4 Hierarchical Geometry on each same node. No archive-size claim."
        ),
        "novelty_boundary": (
            "Dictionary/period/alphabet codelets are generic/SOTA-adjacent. latent_integer_extra_bytes is a "
            "counterfactual measurement of lexical-integer microprogram value beyond both G3/G4 and the same "
            "LTM layout with lexint disabled. Residualized affine/sawtooth behavior is separately counted."
        ),
        "contract": {
            "expected_trees": EXPECTED_TREES,
            "targets": list(TARGETS),
            "minimum_single_file_saving_bytes": MIN_SINGLE_FILE_SAVING,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "minimum_latent_integer_extra_bytes": MIN_LATENT_INTEGER_EXTRA,
            "size_regression_tolerance_bytes": 0,
            "require_lexint": True,
            "require_affine_or_sawtooth": True,
            "sparse_exception_policy": "<=1/16 values and <=2048 exceptions; unit tests include perturbed affine/sawtooth sequences",
        },
        "files": files,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
