"""J24C04 diagnostic of authentic unchanged source-locked first worker (no metric credit)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

court = Path("frozen-guard-court/research/j24b03_direct_session_cost.py").resolve()
spec = importlib.util.spec_from_file_location("original_j24b03_m", court)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
entry = module.create_inputs(Path("benchmark-artifacts/j24c04-probe-inputs").resolve())[0]
results = {}
for arm in ("baseline", "candidate"):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path("frozen-baseline/src" if arm == "baseline" else "src").resolve())
    result = subprocess.run(
        [sys.executable, str(court), "--worker", json.dumps(entry)],
        env=env, capture_output=True, text=True, timeout=90,
    )
    results[arm] = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "fixture_sha256": entry["archive_sha256"],
    }
out = Path("benchmark-artifacts/j24c04-first-worker-diagnostic.json")
out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
for arm, result in results.items():
    print("J24C04_FIRST_WORKER=" + arm + " returncode=" + str(result["returncode"]))
    if result["returncode"]:
        print(result["stderr"][-5000:])
if any(result["returncode"] for result in results.values()):
    raise SystemExit("The original first worker failed; see archived stdout/stderr.")
