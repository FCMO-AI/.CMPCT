#!/usr/bin/env python3
from __future__ import annotations

"""Apply the non-semantic CMPCT presentation layer to a built static site.

Footnote: this deliberately runs *after* build_site.py. Visual motion, surface polish, the public-proof
experience and surface-revision labeling are presentation concerns; keeping them downstream of the
canonical benchmark/data builder reduces the chance that a cosmetic pass can accidentally alter archive
evidence or Browser Lab behavior.
"""

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any

from frontier_v028_adapter import patch_project_data as patch_v028_project_data
from frontier_v029_adapter import patch_project_data as patch_v029_project_data

ROOT = Path(__file__).resolve().parents[1]
SURFACE_FILE = ROOT / "SURFACE_REVISION"
PUBLIC_EVIDENCE_SCHEMA = "cmpct-public-evidence-v1"


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["version"])


def surface_revision(version: str) -> str:
    value = SURFACE_FILE.read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"(\d+)\.(\d+)\.([a-z]+)", value)
    if not match:
        raise RuntimeError(f"SURFACE_REVISION must use x.x.a lettering, got {value!r}")
    major, minor, _ = match.groups()
    project_major, project_minor, *_ = version.split(".")
    if (major, minor) != (project_major, project_minor):
        raise RuntimeError(
            f"surface revision {value} must remain on project line {project_major}.{project_minor}.x"
        )
    return value


def _source_frontier_record(frontier: dict[str, Any]) -> dict[str, Any]:
    """Load the durable record named by the normalized frontier when it is public and present.

    Footnote: the UI should not invent provenance fields that an old adapter did not normalize. Reading
    the already-committed source record lets the stable public evidence contract retain tree fingerprints
    and benchmark contracts without teaching the browser about every historical benchmark schema.
    """
    name = str(frontier.get("file") or "")
    if not name or Path(name).name != name:
        return {}
    path = ROOT / "benchmarks" / "history" / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def build_public_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize the current public frontier into one release-independent presentation contract.

    Footnote: release-specific adapters remain valid ingestion code. They are no longer allowed to become
    the long-term DOM API. Future v0.30/v0.31 work should normalize evidence here (or upstream into the same
    schema) rather than adding another release-specific browser renderer.
    """
    frontier = dict(payload.get("frontier") or {})
    project = dict(payload.get("project") or {})
    overall = dict(frontier.get("overall_comparison") or {})
    category = dict(frontier.get("category_comparison") or {})
    source = _source_frontier_record(frontier)
    structural_source = dict(source.get("structural_aggregate") or {})
    contract = dict(source.get("benchmark_contract") or frontier.get("contract") or {})

    competitors = list(overall.get("competitors") or frontier.get("competitors") or [])
    serious = str(overall.get("serious_comparator_short") or "tar / Zstd solid")
    headline = str(overall.get("headline_comparator_short") or "ZIP / Deflate")

    # Footnote: capabilities below are authority labels, not benchmark wins. The browser uses them to
    # explain why raw size is not the whole product without implying equivalent semantics across formats.
    capabilities = [
        {"key": "lossless", "label": "Lossless reconstruction", "authority": "canonical"},
        {"key": "identity", "label": "Exact-content identity and deduplication", "authority": "canonical"},
        {"key": "selective_access", "label": "Indexed selective access", "authority": "canonical-design"},
        {"key": "integrity", "label": "Authenticated/checksummed physical data and metadata", "authority": "canonical"},
        {"key": "recovery", "label": "Physical metadata recovery path", "authority": "canonical"},
        {"key": "bounded_decode", "label": "Bounded context / decode-work discipline", "authority": "design-and-research"},
        {"key": "performance_gate", "label": "Zero-byte deterministic size-regression gate at promotion", "authority": "release-policy"},
    ]

    return {
        "schema": PUBLIC_EVIDENCE_SCHEMA,
        "project_version": frontier.get("project_version") or project.get("project_version"),
        "canonical_format_revision": frontier.get("canonical_format_revision") or project.get("format_revision"),
        "frontier_name": (frontier.get("candidate") or {}).get("name") or "CMPCT research frontier",
        "frontier_status": (frontier.get("candidate") or {}).get("status") or frontier.get("kind") or "research frontier",
        "authority": {
            "canonical": "shipping reader/writer and on-disk interoperability contract",
            "research": "measured project frontier; not automatically canonical-readable",
        },
        "structural": {
            "candidate_bytes": overall.get("candidate_bytes") or frontier.get("archive_bytes"),
            "logical_bytes": overall.get("logical_bytes") or frontier.get("logical_bytes"),
            "files": overall.get("files") or frontier.get("files"),
            "headline_comparator_short": headline,
            "serious_comparator_short": serious,
            "competitors": competitors,
            "method": overall.get("method") or frontier.get("structural_competitor_contract") or {},
        },
        "category": {
            "baseline_short": category.get("baseline_short") or serious,
            "secondary_short": category.get("secondary_short") or "ZIP / Deflate",
            "workloads": category.get("workloads") or frontier.get("workload_count") or 0,
            "wins": category.get("wins_vs_zstd"),
            "losses": category.get("losses_vs_zstd"),
            "ties": category.get("ties_vs_zstd"),
            "lead_pct": category.get("lead_vs_zstd_pct"),
            "rows": list(category.get("rows") or []),
            "contract": category.get("contract") or {},
        },
        "scheduler": frontier.get("scheduler") or {},
        "release_delta": frontier.get("release_delta") or {},
        "known_losses": list(frontier.get("known_losses") or []),
        "capabilities": capabilities,
        "provenance": {
            "record": frontier.get("file"),
            "date": frontier.get("date"),
            "tree_sha256": structural_source.get("tree_sha256"),
            "suite": structural_source.get("suite"),
            "source_artifact": (structural_source.get("method") or {}).get("source_artifact_digest"),
            "contract": contract,
        },
        "claim_policy": {
            "wins_and_losses_visible": True,
            "research_canonical_boundary_required": True,
            "headline_values_derived_from_committed_evidence": True,
            "missing_evidence_behavior": "suppress-or-mark-unavailable; never reuse stale headline data",
            "semantic_difference_behavior": "label differences; raw-size comparison does not imply feature parity",
        },
    }


def patch_index(output: Path, version: str, surface: str) -> None:
    path = output / "index.html"
    html = path.read_text(encoding="utf-8")

    if "assets/motion.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="assets/styles.css">',
            '<link rel="stylesheet" href="assets/styles.css">\n'
            '  <!-- Footnote: motion.css is optional presentation; styles.css remains the structural baseline. -->\n'
            '  <link rel="stylesheet" href="assets/motion.css">',
        )
    if "assets/polish.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="assets/motion.css">',
            '<link rel="stylesheet" href="assets/motion.css">\n'
            '  <!-- Footnote: polish.css contains visually verified responsive/accessibility corrections only. -->\n'
            '  <link rel="stylesheet" href="assets/polish.css">',
        )
    if "assets/experience.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="assets/polish.css">',
            '<link rel="stylesheet" href="assets/polish.css">\n'
            '  <!-- Footnote: experience.css is the stable public-proof layer and loads last by design. -->\n'
            '  <link rel="stylesheet" href="assets/experience.css">',
        )

    if "assets/motion.js" not in html:
        html = html.replace(
            '<script type="module" src="assets/app.js"></script>',
            '<script type="module" src="assets/app.js"></script>\n'
            '  <script type="module" src="assets/motion.js"></script>',
        )

    # Footnote: historical release-specific renderer files remain in the repository for archaeology,
    # but the generated current site does not load them. One stable experience renderer now owns the DOM.
    if "assets/experience.js" not in html:
        html = html.replace(
            '<script type="module" src="assets/motion.js"></script>',
            '<script type="module" src="assets/motion.js"></script>\n'
            '  <!-- Footnote: one stable renderer owns the current/future proof experience. -->\n'
            '  <script type="module" src="assets/experience.js"></script>',
        )

    html = re.sub(
        r'<span class="release-chip">v[^<]+? · r(\d+)</span>',
        lambda match: f'<span class="release-chip">v{version} · surface {surface} · r{match.group(1)}</span>',
        html,
        count=1,
    )
    html = html.replace(
        f'<span>Project v{version}</span><span>Canonical format',
        f'<span>Project v{version}</span><span>Surface {surface}</span><span>Canonical format',
        1,
    )

    # Backward-compatible copy corrections for old source snapshots. The redesigned source already uses
    # these sentences, so replacements become harmless no-ops once the new index is present.
    html = html.replace(
        '<strong>No silent performance regression.</strong>',
        '<strong>Discover boldly. Promote without regression.</strong>',
        1,
    )
    html = html.replace(
        'Every material step<br><em>gets a version and a benchmark.</em>',
        'Core releases must<br><em>earn the number.</em>',
        1,
    )

    path.write_text(html, encoding="utf-8")
    (output / "surface-revision.txt").write_text(surface + "\n", encoding="utf-8")


def patch_machine_state(output: Path, surface: str) -> None:
    agent_path = output / "agent.json"
    project_data_path = output / "project-data.json"

    agent: dict[str, Any] | None = None
    if agent_path.exists():
        agent = json.loads(agent_path.read_text(encoding="utf-8"))
        agent["surface_revision"] = surface
        rules = list(agent.get("non_negotiables") or [])
        old_rule = "Material updates are versioned and benchmarked against their direct base."
        new_rule = (
            "Numeric core versions are reserved for material CMPCT format/engine improvements; "
            "presentation-only work advances the alphabetic surface revision instead."
        )
        rules = [new_rule if rule == old_rule else rule for rule in rules]
        breakthrough_rule = (
            "No-regression is a core-release promotion boundary, not an exploration ban: preserve a "
            "verified breakthrough seed with explicit regression debt, then rehabilitate the debt while "
            "retaining the gain before promotion."
        )
        proof_surface_rule = (
            "The public site is a proof surface: headline numbers come from committed evidence, relevant "
            "losses remain visible, and research results never borrow canonical authority."
        )
        for rule in (breakthrough_rule, proof_surface_rule):
            if rule not in rules:
                rules.append(rule)
        agent["non_negotiables"] = rules
        agent_path.write_text(json.dumps(agent, indent=2) + "\n", encoding="utf-8")

    if project_data_path.exists():
        payload = json.loads(project_data_path.read_text(encoding="utf-8"))
        if agent is not None:
            payload["project"] = agent
        payload["public_evidence"] = build_public_evidence(payload)
        project_data_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    llms_path = output / "llms.txt"
    if llms_path.exists():
        text = llms_path.read_text(encoding="utf-8")
        text = re.sub(
            r"> Project v([^·\n]+) · canonical format r(\d+)\.",
            rf"> Project v\1 · surface {surface} · canonical format r\2.",
            text,
            count=1,
        )
        text = text.replace(
            "Performance is a release contract: material updates are benchmarked against their direct base and deterministic size regressions are rejected.",
            "Performance is a core-release contract: breakthrough research may carry explicit regression debt, but promotion requires rehabilitation while retaining the breakthrough. Presentation-only work uses the alphabetic surface track.",
            1,
        )
        proof_note = (
            "\nPublic proof surface: use project-data.json.public_evidence for release-independent headline "
            "claims, competitor positions, known losses, capability authority and provenance.\n"
        )
        if "project-data.json.public_evidence" not in text:
            text += proof_note
        llms_path.write_text(text, encoding="utf-8")


def enhance(output: Path) -> None:
    version = project_version()
    surface = surface_revision(version)
    # Footnote: adapters are schema-selective. Running both keeps historical build compatibility while
    # only the record matching the current project version is allowed to become the public frontier.
    patch_v028_project_data(output)
    patch_v029_project_data(output)
    patch_index(output, version, surface)
    patch_machine_state(output, surface)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply CMPCT presentation enhancements to a built site")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    enhance(args.output.resolve())
    print(f"Enhanced CMPCT site at {args.output.resolve()}")


if __name__ == "__main__":
    main()
