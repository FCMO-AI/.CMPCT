#!/usr/bin/env python3
from __future__ import annotations

"""Validate the generated CMPCT public-proof experience.

Footnote: this gate intentionally checks both evidence truth and presentation presence. A structurally
valid JSON file is not enough if the homepage drops the loss board or canonical/research boundary; a
beautiful page is not enough if its headline can drift away from the committed benchmark record.
"""

import argparse
import json
import math
from pathlib import Path

SCHEMA = "cmpct-public-evidence-v1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    parser.add_argument("--source", type=Path, default=Path("site/src"))
    args = parser.parse_args()

    out = args.site.resolve()
    source = args.source.resolve()
    data = json.loads((out / "project-data.json").read_text(encoding="utf-8"))
    evidence = data.get("public_evidence") or {}
    assert evidence.get("schema") == SCHEMA, evidence.get("schema")

    structural = evidence.get("structural") or {}
    rows = list(structural.get("competitors") or [])
    assert len(rows) >= 4, "public arena needs a credible competitor set"
    candidate_rows = [row for row in rows if row.get("role") == "candidate"]
    assert len(candidate_rows) == 1, "structural arena requires exactly one CMPCT candidate"
    candidate = int(structural.get("candidate_bytes") or 0)
    assert candidate > 0 and candidate == int(candidate_rows[0]["bytes"])

    by_short = {str(row.get("short")): row for row in rows}
    headline = str(structural.get("headline_comparator_short") or "")
    serious = str(structural.get("serious_comparator_short") or "")
    assert headline in by_short, "headline comparator must be present in the same matched arena"
    assert serious in by_short, "serious compressor must remain present beside the familiar headline"
    for row in rows:
        if row.get("role") == "candidate":
            continue
        other = int(row["bytes"])
        expected = (other - candidate) / other * 100.0
        assert math.isclose(float(row["lead_pct"]), expected, rel_tol=0, abs_tol=1e-10), row.get("short")

    losses = list(evidence.get("known_losses") or [])
    assert losses, "Red Team Board requires at least one current qualification when the frontier records one"
    policy = evidence.get("claim_policy") or {}
    assert policy.get("wins_and_losses_visible") is True
    assert policy.get("research_canonical_boundary_required") is True
    assert policy.get("headline_values_derived_from_committed_evidence") is True

    provenance = evidence.get("provenance") or {}
    assert provenance.get("record"), "public claims must name their durable record"
    assert provenance.get("contract"), "public claims must preserve benchmark scope/contract"

    html = (out / "index.html").read_text(encoding="utf-8")
    for needle in (
        'id="hero-gain"',
        'id="hero-metrics"',
        'id="competitor-ladder"',
        'id="known-losses"',
        'id="evidence-receipt"',
        'SHIPPING / CANONICAL',
        'RESEARCH FRONTIER',
        'RED TEAM BOARD',
        'assets/motion.css',
        'assets/polish.css',
        'assets/experience.css',
        'assets/motion.js',
        'assets/experience.js',
    ):
        assert needle in html, f"missing public-proof surface: {needle}"

    # Footnote: the August 17 publication regression served the raw source template instead of the
    # enhanced build. Checking generated markers here makes that exact failure mode release-blocking.
    for marker in ("__CMPCT_VERSION__", "__FORMAT_REVISION__", "__BUILD_COMMIT__"):
        assert marker not in html, f"unexpanded generated-site marker: {marker}"

    # Footnote: the visual campaign is layered rather than destructive. Both the preserved baseline and
    # the current atelier override must survive the build so future redesigns do not erase accumulated UI.
    for asset in (
        "motion.css",
        "polish.css",
        "experience.css",
        "experience-base.css",
        "atelier.css",
        "motion.js",
        "experience.js",
    ):
        assert (out / "assets" / asset).is_file(), f"missing generated visual asset: {asset}"

    experience = (out / "assets" / "experience.css").read_text(encoding="utf-8")
    assert 'experience-base.css' in experience, "visual assembly must preserve the established proof CSS"
    assert 'atelier.css' in experience, "visual assembly must load the current FCMO campaign last"

    # Footnote: the headline must remain a runtime evidence value. If someone types the current 38.5%
    # into HTML, a later release can look current while silently showing stale marketing copy.
    assert "38.5%" not in html

    renderer = (source / "assets" / "experience.js").read_text(encoding="utf-8")
    assert SCHEMA in renderer
    assert "mosaic-v029" not in renderer
    assert "entropygraph-v028" not in renderer
    assert "render_contract" not in renderer

    print(f"CMPCT public proof surface: coherent ({SCHEMA})")


if __name__ == "__main__":
    main()
