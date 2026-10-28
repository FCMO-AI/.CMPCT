from __future__ import annotations

"""Final benchmark entrypoint for strict EntropyGraph-II policy.

This wrapper intentionally reuses the established benchmark schema and corpus machinery while swapping
only the research engine path. After the run it annotates the JSON provenance so committed evidence can
distinguish the historical first-pass policy from the strict <=8x read-amplification policy.
"""

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_BENCH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"
STRICT_ENGINE = ROOT / "experiments" / "entropygraph_v028_strict.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _output_arg() -> Path | None:
    for i, value in enumerate(sys.argv[:-1]):
        if value == "--output":
            return Path(sys.argv[i + 1])
    return None


def main() -> None:
    base = _load(BASE_BENCH, "entropygraph_v028_strict_benchmark_base")
    original_load = base._load

    def strict_load(path: Path, name: str):
        if Path(path).name == "entropygraph_v028.py":
            return original_load(STRICT_ENGINE, name)
        return original_load(path, name)

    base._load = strict_load
    base.main()

    output = _output_arg()
    if output and output.exists():
        record = json.loads(output.read_text())
        record["candidate"]["source"] = "experiments/entropygraph_v028_strict.py"
        record["candidate"]["strict_read_amplification_budget"] = 8.0
        record["candidate"]["policy_note"] = (
            "independent records are an explicit 1x locality floor; only pack plans <=8x are admissible"
        )
        output.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
