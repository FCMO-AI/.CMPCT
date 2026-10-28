from __future__ import annotations

"""Research-only exact cross-view tabular redundancy oracle for the federated frontier.

The analytics evidence shows that compression effort alone cannot satisfy both the accepted-v0.29 byte floor and
ZIP creation budget: the current fast policy remains hundreds of kilobytes above v0.29, while the all-best payload
floor requires seconds of high-level Zstd work.  This oracle tests a different representation class: two ordinary
text files may encode the same ordered table in different serializations.

Admission is content-derived, never path/workload/hash-dispatch.  The oracle sniffs UTF-8 CSV-like and JSONL-like
regular files, proves that their ordered fields and typed values are identical for every row, infers only a tiny
field-type recipe, regenerates the JSONL byte-for-byte from the CSV, and then prices the removable level-1 payload.
The candidate is valid only when the source view fits the existing <=8 MiB decode-unit law and reconstructing the
other view stays <=8x logical read amplification.

This does NOT define a shipping grammar.  It establishes whether a generic exact 'tabular mirror' representation
has enough byte and CPU headroom to justify the next canonical grammar/reader/recovery prototype.  Native/Android,
hostile parsing, recovery, selector/generalization and full release authority remain mandatory.
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS

MAX_TEXT_BYTES = 32 * 1024 * 1024
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_READ_AMP = 8.0
ROUNDS = 5
# Exact predecessor evidence: the best measured fast analytics policy remained 415,441 B above accepted v0.29.
# This is a research hurdle only, never a production selector input.
REQUIRED_STRUCTURAL_SAVING_BYTES = 415_442
# The predecessor fast federated path had roughly 0.77 s of conservative ZIP-budget headroom.
MAX_RELATION_PROOF_S = 0.70


def _json_rows(data: bytes) -> tuple[list[str], list[dict]] | None:
    if len(data) > MAX_TEXT_BYTES:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    if len(lines) < 100:
        return None
    rows: list[dict] = []
    keys: list[str] | None = None
    try:
        for line in lines:
            value = json.loads(line)
            if not isinstance(value, dict):
                return None
            current = list(value.keys())
            if keys is None:
                keys = current
            elif current != keys:
                return None
            rows.append(value)
    except (json.JSONDecodeError, UnicodeError):
        return None
    if not keys or len(keys) < 2:
        return None
    return keys, rows


def _csv_rows(data: bytes) -> tuple[list[str], list[list[str]], str] | None:
    if len(data) > MAX_TEXT_BYTES:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    # Preserve the physical newline law in the recipe. csv.writer's default dialect emits CRLF.
    newline = "\r\n" if "\r\n" in text[:4096] else "\n"
    try:
        reader = csv.reader(io.StringIO(text, newline=""))
        header = next(reader)
        rows = list(reader)
    except (csv.Error, StopIteration):
        return None
    if len(header) < 2 or len(set(header)) != len(header) or len(rows) < 100:
        return None
    if any(len(row) != len(header) for row in rows):
        return None
    # Do not accidentally classify JSONL as a one-row CSV dialect.
    if any(token.startswith("{") or token.startswith("[") for token in header):
        return None
    return header, rows, newline


def _kind(values: list[object]) -> str | None:
    kinds = {"bool" if isinstance(v, bool) else "int" if isinstance(v, int) else "float" if isinstance(v, float) else "str" if isinstance(v, str) else "other" for v in values}
    return next(iter(kinds)) if len(kinds) == 1 and "other" not in kinds else None


def _parse_cell(raw: str, kind: str):
    if kind == "str":
        return raw
    if kind == "int":
        return int(raw)
    if kind == "float":
        return float(raw)
    if kind == "bool":
        if raw == "True":
            return True
        if raw == "False":
            return False
        raise ValueError("non-canonical CSV boolean")
    raise ValueError(f"unsupported tabular scalar kind: {kind}")


def _prove_pair(csv_data: bytes, json_data: bytes) -> dict | None:
    csv_decoded = _csv_rows(csv_data)
    json_decoded = _json_rows(json_data)
    if csv_decoded is None or json_decoded is None:
        return None
    header, csv_rows, csv_newline = csv_decoded
    keys, json_rows = json_decoded
    if header != keys or len(csv_rows) != len(json_rows):
        return None
    kinds: list[str] = []
    for key in keys:
        kind = _kind([row[key] for row in json_rows])
        if kind is None:
            return None
        kinds.append(kind)
    try:
        for csv_row, json_row in zip(csv_rows, json_rows, strict=True):
            for index, key in enumerate(keys):
                if _parse_cell(csv_row[index], kinds[index]) != json_row[key]:
                    return None
    except (ValueError, OverflowError):
        return None

    # The reconstruction law itself is the final authority: semantic equality is insufficient unless physical
    # bytes also reproduce exactly, including JSON key order, separators, float spelling and final newline.
    output = io.StringIO(newline="")
    for csv_row in csv_rows:
        row = {key: _parse_cell(csv_row[index], kinds[index]) for index, key in enumerate(keys)}
        output.write(json.dumps(row, separators=(",", ":")) + "\n")
    regenerated = output.getvalue().encode("utf-8")
    if regenerated != json_data:
        return None
    recipe = {
        "kind": "tabular-mirror-csv-to-jsonl-v1",
        "fields": keys,
        "types": kinds,
        "csv_newline": csv_newline,
        "json_newline": "\n",
        "rows": len(csv_rows),
    }
    return {
        "recipe": recipe,
        "recipe_bytes": len(json.dumps(recipe, separators=(",", ":")).encode("utf-8")),
        "rows": len(csv_rows),
        "source_bytes": len(csv_data),
        "reconstructed_bytes": len(json_data),
        "reconstructed_sha256": hashlib.sha256(regenerated).hexdigest(),
        "byte_exact": True,
    }


def _zstd_size(path: Path, level: int = 1) -> int:
    output = path.with_name(path.name + f".zstd{level}.tmp")
    try:
        subprocess.run(["zstd", "-q", "-f", f"-{level}", str(path), "-o", str(output)], check=True)
        return output.stat().st_size
    finally:
        output.unlink(missing_ok=True)


def _discover(root: Path) -> list[dict]:
    files = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.stat().st_size <= MAX_TEXT_BYTES):
        data = path.read_bytes()
        files.append((path, data, _csv_rows(data), _json_rows(data)))
    results: list[dict] = []
    for csv_path, csv_data, csv_shape, _ in files:
        if csv_shape is None:
            continue
        for json_path, json_data, _, json_shape in files:
            if json_shape is None or json_path == csv_path:
                continue
            started = time.perf_counter()
            proof = _prove_pair(csv_data, json_data)
            elapsed = time.perf_counter() - started
            if proof is None:
                continue
            results.append(
                {
                    # Paths are evidence labels only. They are not admitted to the relation detector or recipe.
                    "source_label": csv_path.relative_to(root).as_posix(),
                    "mirror_label": json_path.relative_to(root).as_posix(),
                    **proof,
                    "relation_proof_s": float(elapsed),
                    "source_level1_bytes": _zstd_size(csv_path, 1),
                    "mirror_level1_bytes": _zstd_size(json_path, 1),
                }
            )
    return results


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus_root = work_root / "corpus"
    CORPUS.corpus_analytics(corpus_root.parent)
    source = corpus_root.parent / "04_analytics_and_database"

    samples: list[float] = []
    discovered: list[dict] | None = None
    for _ in range(ROUNDS):
        started = time.perf_counter()
        rows = _discover(source)
        elapsed = time.perf_counter() - started
        samples.append(float(elapsed))
        if discovered is None:
            discovered = rows
        else:
            stable = [(row["recipe"], row["reconstructed_sha256"]) for row in rows]
            expected = [(row["recipe"], row["reconstructed_sha256"]) for row in discovered]
            if stable != expected:
                raise RuntimeError("tabular mirror discovery is nondeterministic")
    assert discovered is not None
    if len(discovered) != 1:
        raise RuntimeError(f"expected one exact tabular mirror relation in research source, found {len(discovered)}")
    relation = discovered[0]
    removable = int(relation["mirror_level1_bytes"]) - int(relation["recipe_bytes"])
    amplification = float(relation["source_bytes"] / max(1, relation["reconstructed_bytes"]))
    median_proof = statistics.median(samples)
    gate = {
        "one_content_derived_exact_relation": True,
        "byte_exact_reconstruction": bool(relation["byte_exact"]),
        "source_decode_unit_within_8mib": int(relation["source_bytes"]) <= MAX_DECODE_UNIT,
        "mirror_read_amplification_within_8x": amplification <= MAX_READ_AMP,
        "structural_saving_clears_known_fast_policy_gap": removable >= REQUIRED_STRUCTURAL_SAVING_BYTES,
        "relation_proof_within_known_zip_headroom": median_proof <= MAX_RELATION_PROOF_S,
    }
    return {
        "schema": "cmpct-v030-federated-tabular-mirror-oracle-v1",
        "contract": {
            "relation_policy_inputs": ["utf8-parseability", "ordered-field-schema", "typed-row-equality", "exact-byte-regeneration"],
            "forbidden_policy_inputs": ["path", "filename", "workload_label", "benchmark_name", "pack_hash_dispatch"],
            "max_decode_unit_bytes": MAX_DECODE_UNIT,
            "max_read_amplification": MAX_READ_AMP,
            "required_structural_saving_bytes": REQUIRED_STRUCTURAL_SAVING_BYTES,
            "max_relation_proof_s": MAX_RELATION_PROOF_S,
            "archive_grammar_changed": False,
            "selector_changed": False,
            "release_credit": False,
        },
        "relation": relation,
        "pair_level1_bytes_before": int(relation["source_level1_bytes"] + relation["mirror_level1_bytes"]),
        "pair_level1_bytes_after_projection": int(relation["source_level1_bytes"] + relation["recipe_bytes"]),
        "projected_structural_saving_bytes": removable,
        "mirror_read_amplification": amplification,
        "discovery_samples_s": samples,
        "median_relation_proof_s": float(median_proof),
        "gate": {**gate, "passed": all(gate.values())},
        "promotion_signal": bool(all(gate.values())),
        "claim_boundary": (
            "Research feasibility only. A positive result authorizes an EG-family tabular-mirror grammar/reader "
            "prototype with exact all-15/adversarial admission, recovery, locality, native/Android and full timed "
            "release authority; it does not authorize production selection."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-federated-tabular-mirror-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-federated-tabular-mirror.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "projected_structural_saving_bytes": result["projected_structural_saving_bytes"],
        "median_relation_proof_s": result["median_relation_proof_s"],
        "mirror_read_amplification": result["mirror_read_amplification"],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("tabular mirror feasibility gate failed")


if __name__ == "__main__":
    main()
