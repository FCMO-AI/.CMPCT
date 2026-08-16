#!/usr/bin/env python3
from __future__ import annotations

"""Build the CMPCT website from canonical repository state and durable benchmark history.

The public site does not hand-type performance claims. It derives project version, executable format
revision, release history, canonical parity evidence, and research-frontier evidence at build time.
That makes stale or selectively copied marketing numbers much harder to ship.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SOURCE = SITE / "src"
HISTORY = ROOT / "benchmarks" / "history"


def _read_project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["version"])


def _read_format_revision() -> int:
    text = (ROOT / "src" / "cmpct" / "codec.py").read_text(encoding="utf-8")
    match = re.search(r"(?m)^VERSION\s*=\s*(\d+)\s*$", text)
    if not match:
        raise RuntimeError("Unable to find executable CMPCT VERSION in src/cmpct/codec.py")
    return int(match.group(1))


def _git_commit() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "local-build"


def _date_from_name(path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else "0000-00-00"


def _version_key(value: str | None) -> tuple[int, int, int]:
    try:
        bits = [int(x) for x in str(value or "0.0.0").split(".")]
        return tuple((bits + [0, 0, 0])[:3])  # type: ignore[return-value]
    except ValueError:
        return (0, 0, 0)


def _lead_pct(candidate: Any, competitor: Any) -> float | None:
    try:
        c = float(candidate)
        other = float(competitor)
    except (TypeError, ValueError):
        return None
    if other <= 0:
        return None
    return 100.0 * (other - c) / other


def _sum_numeric(rows: list[dict[str, Any]], key: str) -> int:
    total = 0
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            total += int(value)
    return total


def _structural_summary(record: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize the expensive aggregate structural-competitor sweep.

    Footnote: a competitor is surfaced only when it was available for every recorded aggregate suite.
    Summing a tool over one suite while silently omitting another would manufacture a flattering total.
    """
    if not record:
        return {"candidate_bytes": None, "competitors": [], "semantics": []}
    rows = [row for row in record.get("rows", []) if isinstance(row, dict)]
    if not rows:
        return {"candidate_bytes": None, "competitors": [], "semantics": []}
    candidate = sum(int(row.get("cmpct_bytes") or 0) for row in rows)
    mapping = {
        "zip_deflate9": ("ZIP + Deflate-9", "ZIP / Deflate", "competitor"),
        "tar_zstd19_solid": ("solid tar + Zstandard-19", "tar / Zstd solid", "diagnostic"),
        "seven_zip_lzma2": ("7z + LZMA2", "7z / LZMA2", "competitor"),
        "zpaq_m5": ("ZPAQ method 5", "ZPAQ / m5", "competitor"),
        "dwarfs": ("DwarFS image", "DwarFS", "structural"),
        "borg": ("Borg repository + Zstandard", "Borg / Zstd", "structural"),
    }
    competitors: list[dict[str, Any]] = []
    semantics: list[str] = []
    for key, (name, short, role) in mapping.items():
        observations = []
        available = True
        for row in rows:
            item = (row.get("competitors") or {}).get(key) or {}
            if not item.get("available") or not isinstance(item.get("bytes"), (int, float)):
                available = False
                break
            observations.append(item)
        if not available or not observations:
            continue
        stored = sum(int(item["bytes"]) for item in observations)
        competitors.append(
            {
                "name": name,
                "short": short,
                "bytes": stored,
                "lead_pct": _lead_pct(candidate, stored),
                "role": role,
            }
        )
        notes = sorted({str(item.get("semantics") or "").strip() for item in observations if item.get("semantics")})
        if notes:
            semantics.append(f"{short}: {' | '.join(notes)}")
    return {"candidate_bytes": candidate, "competitors": competitors, "semantics": semantics}


def _v028_frontier(
    path: Path, data: dict[str, Any], structural: dict[str, Any] | None
) -> dict[str, Any] | None:
    rows = [row for row in data.get("rows", []) if isinstance(row, dict)]
    totals = data.get("totals") or {}
    if not rows or not isinstance(totals, dict):
        return None
    candidate_bytes = totals.get("candidate_bytes")
    inherited_bytes = totals.get("inherited_v025_bytes")
    logical_bytes = _sum_numeric(rows, "logical_bytes")
    file_count = _sum_numeric(rows, "files")
    saved_pct = _lead_pct(candidate_bytes, logical_bytes)
    primary_lead = totals.get("smaller_than_v025_pct")
    project_version = data.get("project_version")
    structural_summary = _structural_summary(structural)

    competitors: list[dict[str, Any]] = [
        {
            "name": "CMPCT EntropyGraph II — strict",
            "short": "CMPCT v0.28",
            "bytes": candidate_bytes,
            "lead_pct": 0.0,
            "role": "candidate",
        },
        {
            "name": "Inherited EntropyGraph v0.25 engine",
            "short": "CMPCT v0.25",
            "bytes": inherited_bytes,
            "lead_pct": primary_lead,
            "role": "baseline",
        },
    ]
    # The structural sweep rebuilds the same two public suite trees as aggregate archives. Require byte
    # agreement before using its third-party ladder; otherwise preserve the causal record and expose the
    # mismatch as negative evidence rather than joining incomparable totals.
    structural_mismatch = False
    if structural_summary.get("candidate_bytes") is not None:
        structural_mismatch = int(structural_summary["candidate_bytes"]) != int(candidate_bytes or -1)
        if not structural_mismatch:
            competitors.extend(structural_summary.get("competitors") or [])

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        candidate = row.get("candidate_bytes")
        inherited = row.get("inherited_v025_bytes")
        delta = _lead_pct(candidate, inherited)
        improved = isinstance(delta, (int, float)) and delta > 0
        normalized = dict(row)
        normalized["comparison_pct"] = delta
        normalized["comparison_label"] = (
            "smaller than inherited v0.25" if improved else "exact inherited fallback parity"
        )
        normalized_rows.append(normalized)

    known_losses = []
    for row in normalized_rows:
        if row.get("selected") != "resemblance":
            known_losses.append(
                f"{str(row.get('name') or 'workload').replace('_', ' ')}: the strict CMPNX8 graph did not beat inherited v0.25, so the exact fallback was retained."
            )
    for competitor in competitors:
        lead = competitor.get("lead_pct")
        if competitor.get("role") != "candidate" and isinstance(lead, (int, float)) and lead < 0:
            known_losses.append(
                f"Aggregate structural sweep: {competitor['short']} stored {abs(lead):.2f}% fewer bytes than CMPCT under its recorded semantics."
            )
    if structural_mismatch:
        known_losses.append(
            "Structural competitor record did not reproduce the causal candidate byte total; its ladder is withheld rather than mixed into the headline."
        )
    known_losses.append(
        "The research portfolio deliberately pays extra creation CPU by building inherited and new candidates; canonical r24 create speed is reported separately by the release-parity gate."
    )

    best_rows = sorted(
        (row for row in normalized_rows if isinstance(row.get("comparison_pct"), (int, float))),
        key=lambda row: float(row.get("comparison_pct") or 0),
        reverse=True,
    )
    hero_metrics = [
        ["VS ENTROPYGRAPH v0.25", primary_lead, "expanded neutral + hostile suite", "pct"],
        ["SIZE REGRESSIONS", int(totals.get("workloads_regressed") or 0), f"of {len(rows)} workloads", "count"],
        ["DEPTH-1 DELTA NODES", int(totals.get("delta_nodes") or 0), "accepted resemblance edges", "count"],
        ["PREFLATE WINS", int(totals.get("preflate_wins") or 0), "exact container transforms", "count"],
    ]
    if best_rows:
        hero_metrics[1] = [
            str(best_rows[0].get("name") or "best workload").replace("_", " ").upper(),
            best_rows[0].get("comparison_pct"),
            "largest measured v0.25 reduction",
            "pct",
        ]

    return {
        "file": path.name,
        "date": data.get("date") or _date_from_name(path),
        "kind": "research-frontier",
        "project_version": project_version,
        "canonical_format_revision": data.get("canonical_format_revision"),
        "candidate": data.get("candidate") or {},
        "contract": data.get("contract") or {},
        "logical_bytes": logical_bytes,
        "files": file_count,
        "workload_count": len(rows),
        "archive_bytes": candidate_bytes,
        "ratio": (float(candidate_bytes) / logical_bytes) if logical_bytes and candidate_bytes is not None else None,
        "saved_pct": saved_pct,
        "primary_lead_pct": primary_lead,
        "primary_comparison": "inherited EntropyGraph v0.25",
        "wins_primary": int(totals.get("workloads_improved") or 0),
        "regressions": int(totals.get("workloads_regressed") or 0),
        "hero_metrics": hero_metrics,
        "competitors": competitors,
        "workloads": normalized_rows,
        "workload_comparison_label": "vs inherited v0.25",
        "known_losses": known_losses,
        "selective_reads": [],
        "design_changes": [
            "bounded FastCDC resemblance nodes + LSH candidate discovery",
            "measured depth-1 rolling COPY/LITERAL deltas",
            "strict <=8x weighted read-amplification pack policy with independent 1x floor",
            "Merkle-authenticated physical records + operational tail recovery",
            "bounded exact Preflate whole-container transform",
            "strict HTTP range-reader research path",
        ],
        "structural_semantics": structural_summary.get("semantics") or [],
    }


def _load_public_benchmarks() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parity: list[dict[str, Any]] = []
    frontier: list[dict[str, Any]] = []
    if not HISTORY.exists():
        return parity, frontier

    raw_records: list[tuple[Path, dict[str, Any]]] = []
    structural_by_version: dict[str, dict[str, Any]] = {}
    for path in sorted(HISTORY.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        raw_records.append((path, data))
        if data.get("schema") == "cmpct-entropygraph-v028-structural-competitors-v1":
            version = str(data.get("project_version") or "")
            if version:
                structural_by_version[version] = data

    for path, data in raw_records:
        schema = data.get("schema")
        if schema == "cmpct-zip-parity-v1" and isinstance(data.get("corpora"), dict):
            data = dict(data)
            data["file"] = path.name
            data["date"] = data.get("date") or _date_from_name(path)
            data["kind"] = "canonical-parity"
            parity.append(data)
        elif schema == "cmpct-public-entropygraph-v025-benchmark-v1":
            suite = data.get("neutral_hostile_suite")
            if not isinstance(suite, dict) or not isinstance(suite.get("rows"), list):
                continue
            frontier.append(
                {
                    "file": path.name,
                    "date": data.get("date") or _date_from_name(path),
                    "kind": "research-frontier",
                    "project_version": data.get("project_version"),
                    "canonical_format_revision": data.get("canonical_format_revision"),
                    "candidate": data.get("candidate") or {},
                    "contract": data.get("benchmark_contract") or {},
                    "logical_bytes": suite.get("logical_bytes"),
                    "files": suite.get("files"),
                    "workload_count": suite.get("workloads"),
                    "archive_bytes": (suite.get("totals") or {}).get("cmpct_v12_bytes"),
                    "ratio": suite.get("cmpct_weighted_ratio"),
                    "saved_pct": suite.get("cmpct_saved_vs_logical_pct"),
                    "wins_zip_zstd": suite.get("cmpct_wins_vs_zip93"),
                    "wins_solid": suite.get("cmpct_wins_vs_solid_tar_zstd19"),
                    "worst_ratio": suite.get("worst_ratio"),
                    "competitors": [
                        {
                            "name": "CMPCT EntropyGraph",
                            "short": "CMPCT",
                            "bytes": (suite.get("totals") or {}).get("cmpct_v12_bytes"),
                            "lead_pct": 0.0,
                            "role": "candidate",
                        },
                        {
                            "name": "ZIP + Zstandard method 93",
                            "short": "ZIP / Zstd",
                            "bytes": (suite.get("totals") or {}).get("zip_zstd93_bytes"),
                            "lead_pct": suite.get("cmpct_smaller_than_zip93_pct"),
                            "role": "competitor",
                        },
                        {
                            "name": "ZIP + Deflate-9",
                            "short": "ZIP / Deflate",
                            "bytes": (suite.get("totals") or {}).get("zip_deflate9_bytes"),
                            "lead_pct": suite.get("cmpct_smaller_than_zip_deflate9_pct"),
                            "role": "competitor",
                        },
                        {
                            "name": "solid tar + Zstandard-19 diagnostic",
                            "short": "tar / Zstd solid",
                            "bytes": (suite.get("totals") or {}).get("tar_zstd19_solid_bytes"),
                            "lead_pct": suite.get("cmpct_smaller_than_solid_tar_zstd19_pct"),
                            "role": "diagnostic",
                        },
                    ],
                    "workloads": suite.get("rows"),
                    "known_losses": data.get("known_losses") or [],
                    "selective_reads": data.get("selective_hot_reads") or [],
                    "design_changes": data.get("design_changes") or [],
                }
            )
        elif schema == "cmpct-entropygraph-v028-benchmark-v1":
            version = str(data.get("project_version") or "")
            normalized = _v028_frontier(path, data, structural_by_version.get(version))
            if normalized:
                frontier.append(normalized)

    parity.sort(
        key=lambda r: (
            _version_key(r.get("project_version") or (r.get("environment") or {}).get("version")),
            r.get("date", ""),
            int(r.get("repetitions") or 0),
        ),
        reverse=True,
    )
    frontier.sort(
        key=lambda r: (_version_key(r.get("project_version")), r.get("date", "")), reverse=True
    )
    return parity, frontier


def _release_history() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    release_dir = ROOT / "docs" / "releases"
    for path in release_dir.glob("v*.md"):
        match = re.match(r"v(\d+\.\d+\.\d+)\.md$", path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        date_match = re.search(r"(?m)^Date:\s*(\d{4}-\d{2}-\d{2})", text)
        rows.append(
            {"version": match.group(1), "title": title, "date": date_match.group(1) if date_match else ""}
        )
    rows.sort(key=lambda r: _version_key(r["version"]), reverse=True)
    return rows


def _agent_manifest(version: str, revision: int, commit: str) -> dict[str, Any]:
    return {
        "project": ".CMPCT",
        "project_version": version,
        "format_revision": revision,
        "status": "pre-1.0 / active development",
        "canonical_repository": "FCMO-AI/.CMPCT",
        "canonical_branch": "main",
        "site_build_commit": commit,
        "publication": {"mode": "public", "status": "public website"},
        "licensing": {
            "proposal": "Apache-2.0",
            "adopted": False,
            "guide": "LICENSING.md",
            "proposed_text": "LICENSE-APACHE-2.0-PROPOSED.txt",
        },
        "reading_order": [
            "README.md",
            "AGENTS.md",
            "docs/CURRENT_STATE.md",
            "docs/ENTROPYGRAPH.md",
            "docs/HARDENING.md",
            "docs/PORTABILITY.md",
            "docs/NATIVE_CORE.md",
            "docs/FORMAT.md",
            "docs/HISTORY.md",
            "docs/RESEARCH_LOG.md",
            "docs/BENCHMARKS.md",
            "docs/PUBLIC_SURFACE.md",
            "docs/ROADMAP.md",
        ],
        "non_negotiables": [
            "Byte-exact losslessness unless a caller explicitly requests a different semantic transform.",
            "Material updates are versioned and benchmarked against their direct base.",
            "Deterministic archive-size regressions are not accepted on the release parity corpus.",
            "Confirmed speed regressions outside the same-runner noise envelope block release.",
            "Benchmark losses and adversarial workloads remain visible.",
            "Random access, filesystem fidelity, integrity, recovery and portability are product requirements.",
            "Pre-1.0 format behavior is not yet a frozen interoperability promise.",
        ],
    }


def _write_llms(out: Path, manifest: dict[str, Any]) -> None:
    repo = "https://github.com/FCMO-AI/.CMPCT"
    lines = [
        "# .CMPCT",
        "",
        f"> Project v{manifest['project_version']} · canonical format r{manifest['format_revision']}.",
        "",
        "CMPCT is an experimental general-purpose lossless archive/container. Performance is a release contract: material updates are benchmarked against their direct base and deterministic size regressions are rejected.",
        "",
        "## Agent orientation",
    ]
    lines.extend(f"- {item}: {repo}/blob/main/{item}" for item in manifest["reading_order"])
    lines.extend(
        [
            "",
            "## Machine-readable site state",
            "- agent.json",
            "- project-data.json",
            "",
            "## Qualification",
            "The site distinguishes canonical revision-24 behavior from research-frontier EntropyGraph results. Do not promote research-only grammar as canonical interoperability support.",
        ]
    )
    (out / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(SOURCE, output)

    version = _read_project_version()
    revision = _read_format_revision()
    commit = _git_commit()
    parity, frontier = _load_public_benchmarks()
    manifest = _agent_manifest(version, revision, commit)

    payload = {
        "project": manifest,
        "frontier": frontier[0] if frontier else None,
        "frontier_history": frontier,
        "parity_records": parity,
        "latest_parity": parity[0] if parity else None,
        "release_history": _release_history(),
        # Footnote: keep the old key during the v0.26 site migration so cached clients and small tools
        # written against the previous site payload fail soft rather than losing their benchmark view.
        "benchmark_records": parity,
    }
    (output / "project-data.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (output / "agent.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_llms(output, manifest)

    index_path = output / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index = index.replace("__CMPCT_VERSION__", version)
    index = index.replace("__FORMAT_REVISION__", str(revision))
    index = index.replace("__BUILD_COMMIT__", commit[:12])
    index_path.write_text(index, encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CMPCT static website")
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    build(args.out.resolve())
    print(f"Built CMPCT site at {args.out.resolve()}")


if __name__ == "__main__":
    main()
