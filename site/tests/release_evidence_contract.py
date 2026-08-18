#!/usr/bin/env python3
from __future__ import annotations

"""Release/evidence invariants retained after moving serving to static ``gh-pages``.

Footnote: GitHub Actions is deliberately still useful here. It validates source and evidence on ``main``;
it is no longer the mechanism that makes an already-approved static site reachable to the public.
"""

import json
import math
import re
import tomllib
from pathlib import Path


def pct_smaller(candidate: int, other: int) -> float:
    return (other - candidate) / other * 100.0


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out = root / "_site"
    data = json.loads((out / "project-data.json").read_text(encoding="utf-8"))
    evidence = data.get("public_evidence") or {}

    with (root / "pyproject.toml").open("rb") as fh:
        version = str(tomllib.load(fh)["project"]["version"])
    surface = (root / "SURFACE_REVISION").read_text(encoding="utf-8").strip()

    assert re.fullmatch(r"\d+\.\d+\.[a-z]+", surface), surface
    assert data["project"]["project_version"] == version
    assert data["project"]["surface_revision"] == surface
    assert evidence.get("schema") == "cmpct-public-evidence-v1"
    assert evidence.get("project_version") == version
    assert (out / "surface-revision.txt").read_text(encoding="utf-8").strip() == surface
    assert (out / ".nojekyll").exists(), "static branch publication must bypass Jekyll"

    structural = evidence.get("structural") or {}
    candidate = int(structural.get("candidate_bytes") or 0)
    competitors = list(structural.get("competitors") or [])
    candidate_rows = [row for row in competitors if row.get("role") == "candidate"]
    assert candidate > 0 and len(candidate_rows) == 1
    assert int(candidate_rows[0]["bytes"]) == candidate
    assert structural.get("headline_comparator_short")
    assert structural.get("serious_comparator_short")
    for row in competitors:
        if row.get("role") == "candidate":
            continue
        other = int(row["bytes"])
        assert math.isclose(float(row["lead_pct"]), pct_smaller(candidate, other), rel_tol=0, abs_tol=1e-10)

    # Footnote: direct-base release improvement and whole-tree external position are different contracts;
    # their byte totals must never be silently substituted for one another.
    release = evidence.get("release_delta") or {}
    release_candidate = int(release.get("candidate_bytes") or 0)
    release_base = int(release.get("baseline_bytes") or 0)
    assert release_candidate > 0 and release_base > 0
    assert release_candidate != candidate
    assert math.isclose(float(release["lead_pct"]), pct_smaller(release_candidate, release_base), rel_tol=0, abs_tol=1e-10)
    assert int(release.get("saving_bytes") or 0) == release_base - release_candidate

    scheduler = evidence.get("scheduler") or {}
    if scheduler:
        assert scheduler.get("byte_identical") is True
        assert scheduler.get("research_gate_pass") is True
        assert int(scheduler.get("archive_bytes") or 0) == candidate
        # Footnote: the speed result is a scoped gate, not a global performance slogan.
        assert "scope" in scheduler and scheduler["scope"]

    category = evidence.get("category") or {}
    category_rows = list(category.get("rows") or [])
    if category_rows:
        wins = losses = ties = 0
        for row in category_rows:
            c = int(row["cmpct_bytes"])
            z = int(row["zstd_bytes"])
            assert math.isclose(float(row["cmpct_vs_zstd_pct"]), pct_smaller(c, z), rel_tol=0, abs_tol=1e-10)
            wins += c < z
            losses += c > z
            ties += c == z
        assert wins == int(category["wins"])
        assert losses == int(category["losses"])
        assert ties == int(category["ties"])
        assert wins + losses + ties == int(category["workloads"])
        assert wins > 0 and losses > 0, "public category frontier must preserve both wins and losses"

    assert evidence.get("known_losses"), "Red Team evidence must not disappear"
    assert data.get("parity_records"), "canonical ZIP execution-parity evidence must remain available"
    assert data.get("release_history") and data["release_history"][0]["version"] == version
    print(f"CMPCT release evidence: coherent; version={version}; surface={surface}")


if __name__ == "__main__":
    main()
