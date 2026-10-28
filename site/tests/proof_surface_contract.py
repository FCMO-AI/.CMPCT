#!/usr/bin/env python3
from __future__ import annotations

"""Validate CMPCT's public-proof truth and restored cinematic visual contract.

Footnote: the historical shell and the later rendered ratchets are explicit regression surfaces. Future
content work may change evidence or copy, but it must not silently flatten the intricate hero, graph stage,
light authority band, Browser Lab, evidence-driven graphics, the Ember Eclipse signal hierarchy, or the
ratio-aware responsive behavior that make the public site recognizably CMPCT across physical screen classes.
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
    assert headline in by_short, "headline comparator must remain in the matched arena"
    assert serious in by_short, "serious compressor must remain beside the familiar headline"
    for row in rows:
        if row.get("role") == "candidate":
            continue
        other = int(row["bytes"])
        expected = (other - candidate) / other * 100.0
        assert math.isclose(float(row["lead_pct"]), expected, rel_tol=0, abs_tol=1e-10), row.get("short")

    losses = list(evidence.get("known_losses") or [])
    assert losses, "Red Team Board requires current qualifications when the frontier records them"
    policy = evidence.get("claim_policy") or {}
    assert policy.get("wins_and_losses_visible") is True
    assert policy.get("research_canonical_boundary_required") is True
    assert policy.get("headline_values_derived_from_committed_evidence") is True
    provenance = evidence.get("provenance") or {}
    assert provenance.get("record"), "public claims must name their durable record"
    assert provenance.get("contract"), "public claims must preserve benchmark scope/contract"

    html = (out / "index.html").read_text(encoding="utf-8")
    for needle in (
        'Archive formats made peace with compromise.',
        '<em>CMPCT did not.</em>',
        'id="entropy-sun"',
        'class="hero-score"',
        'class="score-ruler"',
        'class="graph-stage cinematic-surface"',
        'class="graph-lines"',
        'class="canonical-band"',
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
        assert needle in html, f"missing public visual/proof surface: {needle}"

    # Footnote: this catches the exact publication downgrade that once served raw source markers.
    for marker in ("__CMPCT_VERSION__", "__FORMAT_REVISION__", "__BUILD_COMMIT__"):
        assert marker not in html, f"unexpanded generated-site marker: {marker}"

    for asset in (
        "styles.css", "motion.css", "polish.css", "experience.css", "cinematic.css", "masterclass.css",
        "ember-eclipse.css", "responsive.css", "motion.js", "experience.js", "proof-renderer.js", "cinematic.js",
    ):
        assert (out / "assets" / asset).is_file(), f"missing generated visual asset: {asset}"

    # Footnote: the pre-redesign stylesheet remains the owner of composition. Later layers may amplify it
    # but must remain additive and auditable; re-importing the rejected atelier stack recreates the bug.
    experience = (out / "assets" / "experience.css").read_text(encoding="utf-8")
    assert 'cinematic.css' in experience
    assert 'masterclass.css' in experience
    assert 'ember-eclipse.css' in experience
    assert 'responsive.css' in experience
    assert (
        experience.index('cinematic.css')
        < experience.index('masterclass.css')
        < experience.index('ember-eclipse.css')
        < experience.index('responsive.css')
    )
    assert 'atelier.css' not in experience

    styles = (out / "assets" / "styles.css").read_text(encoding="utf-8")
    for historical_signature in ('.hero-copy h1', '.hero-copy h1 em', '.hero-score:before', '.graph-stage', '.canonical-band'):
        assert historical_signature in styles, f"historical visual grammar missing: {historical_signature}"

    cinematic = (out / "assets" / "cinematic.css").read_text(encoding="utf-8")
    for signature in ('.entropy-sun', '.canonical-crossing', '.chapter-rail', '.engineer-cta'):
        assert signature in cinematic, f"cinematic campaign feature missing: {signature}"

    # Footnote: these signatures correspond to defects/features that were visually verified, not arbitrary
    # CSS trivia. In particular, the sun once existed in code but sat behind the hero stacking context.
    masterclass = (out / "assets" / "masterclass.css").read_text(encoding="utf-8")
    for signature in ('mix-blend-mode: screen', '@keyframes cmpct-route-flow', '.canonical-band .canonical-status'):
        assert signature in masterclass, f"rendered visual-ratchet feature missing: {signature}"
    assert '.entropy-sun' in masterclass and 'z-index: 1' in masterclass
    assert 'prefers-reduced-motion' in masterclass and 'animation:none !important' in masterclass

    # Footnote: Surface 0.29.i deliberately makes orange a localized light source rather than a uniform
    # hero condition. These signatures protect the dark environmental default, eclipse corona and
    # scroll-collapse mechanism while leaving actual visual approval to the Chromium screenshot matrix.
    eclipse = (out / "assets" / "ember-eclipse.css").read_text(encoding="utf-8")
    for signature in (
        'CMPCT Surface 0.29.i',
        '--hero-progress: 0',
        'main::before',
        '.hero::before',
        'rgba(8,8,8,.92)',
        'scale(calc(1 - var(--hero-progress) * .14))',
        '@media (orientation: landscape) and (max-height: 520px)',
        '@media (prefers-reduced-motion: reduce)',
    ):
        assert signature in eclipse, f"Ember Eclipse visual-ratchet feature missing: {signature}"

    # Footnote: width-only responsive CSS is insufficient for notched landscape phones, short laptops and
    # ultrawide displays. These signatures keep the actual ratio-aware design contract present in output;
    # Chromium viewport-matrix CI then proves that the contract renders without measurable collisions.
    responsive = (out / "assets" / "responsive.css").read_text(encoding="utf-8")
    for signature in (
        'env(safe-area-inset-left)',
        'min-aspect-ratio: 21/9',
        'max-aspect-ratio: 4/5',
        'orientation: landscape',
        'max-height: 520px',
        '@media (max-width: 520px)',
        '.graph-stage::after',
        '.result-mini-grid { grid-template-columns: 1fr; }',
        'pointer: coarse',
    ):
        assert signature in responsive, f"responsive visual-ratchet feature missing: {signature}"

    behavior = (out / "assets" / "cinematic.js").read_text(encoding="utf-8")
    assert 'length: 1120' in behavior, "masterclass dot-field density regressed"
    assert 'scrollCompression' in behavior, "evidence field must retain scroll-driven physical compression"
    assert 'compressionRatio' in behavior and 'candidate_bytes' in behavior

    motion = (out / "assets" / "motion.js").read_text(encoding="utf-8")
    assert '--hero-progress' in motion and 'hero.offsetHeight * .72' in motion

    viewport_gate = Path("site/tests/viewport-matrix.mjs")
    assert viewport_gate.is_file(), "real-browser viewport matrix gate is required"
    viewport_text = viewport_gate.read_text(encoding="utf-8")
    for viewport in (
        'phone-compact-320x568',
        'phone-landscape-844x390',
        'tablet-portrait-768x1024',
        'tablet-landscape-1024x768',
        'short-panel-1024x600',
        'laptop-short-1366x768',
        'desktop-16x9-1920x1080',
        'ultrawide-2560x1080',
        'large-qhd-2560x1440',
    ):
        assert viewport in viewport_text, f"viewport class missing from render matrix: {viewport}"
    assert 'documentScrollWidth' in viewport_text
    assert 'information-graph node collision' in viewport_text
    assert 'hero proof value clips outside score card' in viewport_text

    # Headline values stay runtime-derived. A later release must never inherit today's marketing number.
    assert "38.5%" not in html
    proof_renderer = (source / "assets" / "proof-renderer.js").read_text(encoding="utf-8")
    assert SCHEMA in proof_renderer
    assert "mosaic-v029" not in proof_renderer
    assert "entropygraph-v028" not in proof_renderer
    assembly = (source / "assets" / "experience.js").read_text(encoding="utf-8")
    assert 'proof-renderer.js' in assembly and 'cinematic.js' in assembly

    print(f"CMPCT public proof + restored cinematic + Ember Eclipse + responsive surface: coherent ({SCHEMA})")


if __name__ == "__main__":
    main()
