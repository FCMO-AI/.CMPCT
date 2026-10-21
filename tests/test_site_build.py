from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_site_build_tracks_canonical_version_and_benchmarks(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "site"
    subprocess.run(
        [sys.executable, str(root / "site" / "build_site.py"), "--out", str(out)],
        cwd=root,
        check=True,
    )

    payload = json.loads((out / "project-data.json").read_text(encoding="utf-8"))
    assert payload["project"]["project"] == ".CMPCT"
    assert payload["project"]["project_version"]
    assert payload["project"]["format_revision"] >= 24
    assert payload["benchmark_records"], "durable benchmark history should be visible to the site"
    assert (out / "agent.json").exists()
    assert (out / "llms.txt").exists()
    assert "__CMPCT_VERSION__" not in (out / "index.html").read_text(encoding="utf-8")

    # Footnote: the browser writer is intentionally revision-gated. A format bump should make this
    # test fail until the online writer is reviewed against the new bytes instead of silently emitting
    # an archive that only looks current in the UI.
    writer = (root / "site" / "src" / "assets" / "cmpct-browser-writer.js").read_text(encoding="utf-8")
    assert f"SUPPORTED_FORMAT_REVISION = {payload['project']['format_revision']}" in writer


def test_site_enhancement_preserves_historical_evidence_identity(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "site"
    subprocess.run([sys.executable, str(root / "site" / "build_site.py"), "--out", str(out)], check=True)
    # Exercise a future serving identity against real committed historical measurements.
    agent_path = out / "agent.json"
    agent = json.loads(agent_path.read_text())
    agent["project_version"] = "9.0.0"
    agent["format_revision"] = 99
    agent_path.write_text(json.dumps(agent))
    subprocess.run([sys.executable, str(root / "site" / "enhance_site.py"), str(out)], check=True)
    payload = json.loads((out / "project-data.json").read_text())
    evidence = payload["public_evidence"]
    frontier = payload["frontier"]
    assert evidence["project_version"] == "9.0.0"
    assert evidence["canonical_format_revision"] == 99
    assert evidence["provenance"]["project_version"] == frontier["project_version"] != "9.0.0"
    assert evidence["provenance"]["canonical_format_revision"] == frontier["canonical_format_revision"] != 99
    assert evidence["structural"]["competitors"] == frontier["overall_comparison"]["competitors"]
    assert evidence["release_delta"] == frontier["release_delta"]
    assert evidence["known_losses"] == frontier["known_losses"]
