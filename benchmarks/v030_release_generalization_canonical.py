from __future__ import annotations

"""Canonical-byte authority for the frozen v0.30 15-workload release gate.

All numeric thresholds and historical source identities remain owned by ``v030_release_generalization``. This
adapter binds that immutable harness to the single release product front door and enriches every selected archive
with its exact SHA-256 and actual canonical revision/profile.

Footnote: this file does not redefine the frozen 137,501,815-byte historical v0.29 substrate. Product r24-vs-r25
framing parity is an additional gate in ``v030_release_ablation_canonical``; historical causality remains historical.
"""

import argparse
import hashlib
import json
from pathlib import Path

from benchmarks import v030_release_generalization as B
from experiments import entropygraph_v030_release_product as CANON

B.RC = CANON


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    revisions: dict[str, int] = {}
    profiles: dict[str, int] = {}
    for row in result["rows"]:
        archive = work_root / "archives" / row["suite"] / f"{row['name']}.cmpct"
        if not archive.is_file():
            raise RuntimeError(f"canonical generalization archive missing: {archive}")
        revision, profile = CANON._revision_for_archive(archive)
        verified = CANON.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != row["tree_sha256"]:
            raise RuntimeError(f"canonical archive verification drift: {row['suite']}/{row['name']}: {verified!r}")
        row["archive_sha256"] = _sha256_file(archive)
        row["format_revision"] = revision
        row["format_profile"] = profile
        row["canonical_magic_hex"] = archive.read_bytes()[:8].hex()
        revisions[str(revision)] = revisions.get(str(revision), 0) + 1
        profiles[profile] = profiles.get(profile, 0) + 1

    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["canonical_format"] = {
        "new_revision": 25,
        "fallback_revision": 24,
        "g04_magic_hex": CANON.G04_MAGIC.hex(),
        "prefixgraph_magic_hex": CANON.PG_MAGIC.hex(),
        "revisions_selected": revisions,
        "profiles_selected": profiles,
        "fallback_is_unwrapped": True,
        "exact_product_floor": "r25 must strictly beat genuine r24 bytes; ties keep r24",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "format": result["canonical_format"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 compression/generalization gate failed")


if __name__ == "__main__":
    main()
