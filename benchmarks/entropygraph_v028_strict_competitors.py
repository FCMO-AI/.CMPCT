from __future__ import annotations

"""Aggregate structural-competitor sweep using the strict EntropyGraph-II policy."""

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks" / "entropygraph_v028_competitors.py"
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
    base = _load(BASE, "entropygraph_v028_strict_competitor_base")
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
        record.setdefault("method", {})["cmpct_policy"] = (
            "EntropyGraph-II strict locality: independent 1x floor; solid packs must be <=8x weighted read amplification"
        )
        output.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
