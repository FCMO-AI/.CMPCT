from __future__ import annotations

"""Fail-closed validator for Genesis comparator selective-access authority.

The manifest distinguishes direct same-input measurement capability from historical locality
oracles.  This validator binds every cited artifact to the frozen comparator tree and prevents
``unavailable`` access metrics from being silently converted to zero or automatic losses.
"""

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
EXPECTED = {
    (V029_SHA, "experiments/entropygraph_v029_residual_strict.py"): "4fabe7102bbd727acd7c72ba41c055829676a731",
    (V029_SHA, ".github/workflows/mosaic-v029-reference-context.yml"): "5b90488f605c48c9c539c42df08fdd481710870f",
    (V030_SHA, "experiments/entropygraph_v030_release_product_base.py"): "b6b87b5c2b2f50fe53114ad3b5d228cd1e887367",
}


def _git_blob(repo: Path, source_sha: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", f"{source_sha}:{path}"], text=True
    ).strip()


def validate(manifest: dict[str, Any], repo: Path) -> dict[str, Any]:
    if manifest.get("schema") != "cmpct-one-genesis-selective-access-authority-v1":
        raise RuntimeError("unexpected selective-access authority schema")
    rules = manifest.get("rules")
    if not isinstance(rules, dict):
        raise RuntimeError("selective-access authority rules missing")
    for key in (
        "missing_direct_measurement_is_unavailable_not_zero",
        "missing_direct_measurement_is_not_an_automatic_loss",
        "historical_evidence_may_not_be_relabelled_as_same-input_gate_measurement",
        "wrappers_may_instrument_existing_operations_but_may_not_add_new_reader_semantics",
    ):
        if rules.get(key) is not True:
            raise RuntimeError(f"required selective-access rule disabled: {key}")

    comparators = manifest.get("comparators")
    if not isinstance(comparators, dict) or set(comparators) != {"v0.29", "v0.30"}:
        raise RuntimeError("selective-access authority must define exactly v0.29 and v0.30")
    if comparators["v0.29"].get("source_sha") != V029_SHA or comparators["v0.30"].get("source_sha") != V030_SHA:
        raise RuntimeError("selective-access comparator SHA drift")

    v29 = comparators["v0.29"]["direct_product_surface"]
    if v29.get("public_selective_member_read") is not False:
        raise RuntimeError("v0.29 strict surface must not acquire invented selective-reader authority")
    if not str(v29.get("gate_direct_selective_measurement_state", "")).startswith("unavailable"):
        raise RuntimeError("v0.29 absent direct selective measurement must remain unavailable")
    inherited = comparators["v0.29"]["inherited_locality_authority"]
    if inherited.get("kind") != "historical-research-oracle-not-same-input-gate-measurement":
        raise RuntimeError("v0.29 inherited locality evidence boundary drift")
    if inherited.get("max_total_read_amplification_ceiling") != 8.0:
        raise RuntimeError("v0.29 total read-amplification ceiling drift")
    if inherited.get("max_context_only_read_amplification_ceiling") != 4.0:
        raise RuntimeError("v0.29 context-only read-amplification ceiling drift")

    v30 = comparators["v0.30"]["direct_product_surface"]
    for key in ("list_members", "read_member", "read_member_with_stats"):
        if v30.get(key) is not True:
            raise RuntimeError(f"v0.30 frozen selective API missing authority bit: {key}")
    if not str(v30.get("r24_direct_locality_accounting", "")).startswith("unavailable"):
        raise RuntimeError("v0.30 r24 facade locality gap must remain explicit")
    if "falsified" not in str(v30.get("r25_direct_locality_accounting", "")):
        raise RuntimeError("v0.30 r25 locality must remain probe-gated")

    checked: list[dict[str, str]] = []
    for (source_sha, path), expected_blob in EXPECTED.items():
        actual = _git_blob(repo, source_sha, path)
        if actual != expected_blob:
            raise RuntimeError(f"frozen selective authority blob drift: {source_sha}:{path} {actual} != {expected_blob}")
        checked.append({"source_sha": source_sha, "path": path, "blob_sha": actual})

    return {
        "schema": "cmpct-one-genesis-selective-access-authority-validation-v1",
        "decision": "SELECTIVE_ACCESS_AUTHORITY_VALID",
        "checked_blobs": checked,
        "genesis_measurement_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("benchmarks/one/genesis_selective_access_authority_v1.json"))
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.manifest.read_text(encoding="utf-8")), args.repo)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
