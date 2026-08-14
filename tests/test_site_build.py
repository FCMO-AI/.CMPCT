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
