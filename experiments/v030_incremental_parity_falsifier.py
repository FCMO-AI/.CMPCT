from __future__ import annotations

"""Cheap same-input falsifier for the v0.30 incremental-backups zero-byte regression.

This is evidence tooling, not a product change. It regenerates only the deterministic
neutral/hostile incremental-backups workload and compares three build ownership paths:

1. promoted release front door (shipping candidate),
2. preserved mature release-product base front door,
3. genuine locality-bounded r24 product.

The question is intentionally narrow: did the promoted shared-preflight shortcut alter
winner selection, or does the regression already exist below that shortcut?
"""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v5 as R5
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE

EXPECTED_TREE_SHA256 = "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"
EXPECTED_FILES = 769
EXPECTED_LOGICAL_BYTES = 14_006_619


def _tree_identity(root: Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    files = 0
    logical = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        raw = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
        files += 1
        logical += len(raw)
    return h.hexdigest(), files, logical


def _build_row(name: str, builder, root: Path, out: Path) -> dict:
    stats = dict(builder(root, out))
    verified = dict(PROMOTED.strong_verify(out))
    if not verified.get("ok"):
        raise RuntimeError(f"{name} failed strong verification: {verified!r}")
    return {
        "name": name,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "terminal_r24": stats.get("terminal_r24", False),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
    }


def main() -> None:
    # Repair-v5 composes the accepted deterministic repairs that affect this workload.
    R5.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-inc-parity-") as td:
        td = Path(td)
        corpus = td / "corpus"
        corpus.mkdir()
        N.corpus_backups(corpus)
        root = corpus / "06_incremental_backups"
        tree_sha, files, logical = _tree_identity(root)
        if (tree_sha, files, logical) != (EXPECTED_TREE_SHA256, EXPECTED_FILES, EXPECTED_LOGICAL_BYTES):
            raise RuntimeError(
                "incremental-backups substrate identity mismatch: "
                f"sha={tree_sha} files={files} logical={logical}"
            )

        rows = [
            _build_row("promoted_frontdoor", PROMOTED.build, root, td / "promoted.cmpct"),
            _build_row("mature_base_frontdoor", BASE.build, root, td / "base.cmpct"),
            _build_row("genuine_r24", PROMOTED._locality_bounded_r24_build, root, td / "r24.cmpct"),
        ]
        by_name = {row["name"]: row for row in rows}
        r24 = int(by_name["genuine_r24"]["archive_bytes"])
        for row in rows:
            row["delta_vs_r24_bytes"] = int(row["archive_bytes"]) - r24

        promoted_delta = int(by_name["promoted_frontdoor"]["delta_vs_r24_bytes"])
        base_delta = int(by_name["mature_base_frontdoor"]["delta_vs_r24_bytes"])
        if promoted_delta > 0 and base_delta <= 0:
            decision = "PROMOTED_FRONTDOOR_SHORTCUT_CAUSAL"
        elif promoted_delta > 0 and base_delta > 0:
            decision = "REGRESSION_BELOW_PROMOTED_SHORTCUT"
        elif promoted_delta <= 0:
            decision = "REGRESSION_NOT_REPRODUCED"
        else:
            decision = "AMBIGUOUS"

        print(json.dumps({
            "schema": "cmpct-v030-incremental-parity-falsifier-v1",
            "source_tree": {"sha256": tree_sha, "files": files, "logical_bytes": logical},
            "rows": rows,
            "decision": decision,
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
