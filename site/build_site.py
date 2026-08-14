#!/usr/bin/env python3
from __future__ import annotations

"""Build the CMPCT website from canonical repository state.

The site intentionally derives version/revision/benchmark facts at build time instead of hard-coding
marketing copy. This keeps the public surface tied to the same files agents and developers use, and
prevents a release from silently leaving stale website claims behind.
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


def _read_project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        data = tomllib.load(fh)
    return str(data["project"]["version"])


def _read_format_revision() -> int:
    text = (ROOT / "src" / "cmpct" / "codec.py").read_text(encoding="utf-8")
    # Footnote: VERSION is the executable reader/writer contract. Reading the code rather than a prose
    # document means the website fails loudly if the implementation changes without the docs following.
    match = re.search(r"(?m)^VERSION\s*=\s*(\d+)\s*$", text)
    if not match:
        raise RuntimeError("Unable to find CMPCT format VERSION in src/cmpct/codec.py")
    return int(match.group(1))


def _git_commit() -> str:
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "local-build"


def _benchmark_date(path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else "0000-00-00"


def _load_benchmarks() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    history = ROOT / "benchmarks" / "history"
    if not history.exists():
        return records

    for path in sorted(history.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("schema") != "cmpct-zip-parity-v1" or not isinstance(data.get("corpora"), dict):
            continue
        records.append(
            {
                "file": path.name,
                "date": _benchmark_date(path),
                "repetitions": data.get("repetitions"),
                "timing_statistic": data.get("timing_statistic"),
                "cache_semantics": data.get("cache_semantics"),
                "integrity_semantics": data.get("integrity_semantics"),
                "filesystem_semantic_mismatch": data.get("filesystem_semantic_mismatch"),
                "record_kind": data.get("record_kind"),
                "source_commit": data.get("source_commit"),
                "format_revision": data.get("format_revision"),
                "harness": data.get("harness"),
                "environment": data.get("environment"),
                "interpretation": data.get("interpretation"),
                "corpora": data["corpora"],
            }
        )

    # New benchmark filenames begin with an ISO date. When several durable records land on the same
    # day, default to the higher-repetition record while retaining every record in the selector. This
    # is only a UI default; nothing is deleted or rewritten to manufacture a prettier benchmark story.
    records.sort(key=lambda r: (r["date"], int(r.get("repetitions") or 0), r["file"]), reverse=True)
    return records


def _agent_manifest(version: str, revision: int, commit: str) -> dict[str, Any]:
    return {
        "project": ".CMPCT",
        "project_version": version,
        "format_revision": revision,
        "status": "pre-1.0 / active development",
        "canonical_repository": "FCMO-AI/.CMPCT",
        "canonical_branch": "main",
        "site_build_commit": commit,
        "publication": {
            "mode": "manual",
            "status": "validation-only until explicitly published",
        },
        "licensing": {
            "proposal": "Apache-2.0",
            "adopted": False,
            "guide": "LICENSING.md",
            "proposed_text": "LICENSE-APACHE-2.0-PROPOSED.txt",
        },
        "public_surface_policy": "docs/PUBLIC_SURFACE.md",
        "reading_order": [
            "README.md",
            "AGENTS.md",
            "docs/CURRENT_STATE.md",
            "docs/HARDENING.md",
            "docs/PORTABILITY.md",
            "docs/NATIVE_CORE.md",
            "docs/FORMAT.md",
            "docs/HISTORY.md",
            "docs/RESEARCH_LOG.md",
            "docs/BENCHMARKS.md",
            "docs/PUBLIC_SURFACE.md",
            "LICENSING.md",
            "docs/ROADMAP.md",
        ],
        "non_negotiables": [
            "Byte-exact losslessness unless a caller explicitly requests a different semantic transform.",
            "Content-driven representation selection; extensions are hints, never codec commands.",
            "Random access, filesystem fidelity, integrity, recovery and portability are product requirements.",
            "Benchmark claims must use equivalent semantics and preserve losing/adversarial cases.",
            "Public project surfaces must not depend on or expose unrelated private provenance.",
            "Apache-2.0 is proposed, not adopted, until LICENSING.md records the final adoption step.",
            "Pre-1.0 format behavior is not yet a frozen interoperability promise.",
        ],
    }


def _write_llms(out: Path, manifest: dict[str, Any]) -> None:
    repo = "https://github.com/FCMO-AI/.CMPCT"
    lines = [
        "# .CMPCT",
        "",
        f"> Canonical CMPCT project site generated from version {manifest['project_version']} / format revision {manifest['format_revision']}.",
        "",
        "CMPCT is an experimental general-purpose, byte-exact, content-aware archive/container designed to improve on legacy ZIP across more than compression ratio: selective access, filesystem fidelity, integrity, recovery, transactional updates and modern storage semantics all matter.",
        "",
        "## Agent orientation",
    ]
    for item in manifest["reading_order"]:
        lines.append(f"- {item}: {repo}/blob/main/{item}")
    lines.extend(
        [
            "",
            "## Machine-readable project state",
            "- agent.json",
            "- project-data.json",
            "",
            "## Important qualifications",
            "CMPCT is pre-1.0. Development benchmarks are reproducible regression evidence, not universal performance guarantees.",
            "Apache-2.0 is a proposed license and has not yet been adopted as the canonical project license.",
            "Website publication is manual; ordinary repository pushes validate the site but do not publish it.",
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
    benchmarks = _load_benchmarks()
    manifest = _agent_manifest(version, revision, commit)

    payload = {
        "project": manifest,
        "benchmark_records": benchmarks,
        "benchmark_default": benchmarks[0]["file"] if benchmarks else None,
    }
    (output / "project-data.json").write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    (output / "agent.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    _write_llms(output, manifest)

    index = (output / "index.html").read_text(encoding="utf-8")
    index = index.replace("__CMPCT_VERSION__", version)
    index = index.replace("__FORMAT_REVISION__", str(revision))
    index = index.replace("__BUILD_COMMIT__", commit[:12])
    (output / "index.html").write_text(index, encoding="utf-8")

    # GitHub Pages can invoke Jekyll implicitly for branch-based publishing. The workflow publishes a
    # prepared artifact, but .nojekyll keeps the directory safe if the publication mechanism changes.
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CMPCT static website")
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    build(args.out.resolve())
    print(f"Built CMPCT site at {args.out.resolve()}")


if __name__ == "__main__":
    main()
