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


def _load_public_benchmarks() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parity: list[dict[str, Any]] = []
    frontier: list[dict[str, Any]] = []
    if not HISTORY.exists():
        return parity, frontier

    for path in sorted(HISTORY.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
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
