from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from benchmarks.one.one_genesis_contender_workload_measurement import (
    _historical_runtime_provenance,
)


def test_historical_surface_prefers_frozen_cmpct_over_ambient_package(tmp_path: Path) -> None:
    frozen = tmp_path / "frozen"
    ambient = tmp_path / "ambient"
    (frozen / "experiments").mkdir(parents=True)
    (frozen / "src" / "cmpct").mkdir(parents=True)
    (ambient / "cmpct").mkdir(parents=True)

    (frozen / "src" / "cmpct" / "__init__.py").write_text(
        "ORIGIN = 'frozen'\n", encoding="utf-8"
    )
    (ambient / "cmpct" / "__init__.py").write_text(
        "ORIGIN = 'ambient'\n", encoding="utf-8"
    )
    (frozen / "experiments" / "fixture_product.py").write_text(
        "import cmpct\nORIGIN = cmpct.ORIGIN\n", encoding="utf-8"
    )

    script = r'''
import json
from pathlib import Path
import sys
from benchmarks.one import one_genesis_historical_product_worker as worker
frozen = Path(sys.argv[1]).resolve()
ambient = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(ambient))
worker.FROZEN["fixture"] = {
    "sha": "0" * 40,
    "module": "experiments/fixture_product.py",
    "selective": False,
}
surface, roots = worker._load_surface("fixture", frozen)
print(json.dumps({"origin": surface.ORIGIN, "roots": roots}, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, str(frozen), str(ambient)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = json.loads(completed.stdout)
    assert payload["origin"] == "frozen"
    assert payload["roots"]["cmpct"].startswith(str((frozen / "src" / "cmpct").resolve()))


def test_historical_source_seal_rejects_already_loaded_ambient_cmpct(tmp_path: Path) -> None:
    frozen = tmp_path / "frozen"
    ambient = tmp_path / "ambient"
    (frozen / "experiments").mkdir(parents=True)
    (frozen / "src" / "cmpct").mkdir(parents=True)
    (ambient / "cmpct").mkdir(parents=True)
    (frozen / "src" / "cmpct" / "__init__.py").write_text("ORIGIN='frozen'\n", encoding="utf-8")
    (ambient / "cmpct" / "__init__.py").write_text("ORIGIN='ambient'\n", encoding="utf-8")
    (frozen / "experiments" / "fixture_product.py").write_text("import cmpct\n", encoding="utf-8")

    script = r'''
from pathlib import Path
import sys
ambient = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(ambient))
import cmpct
from benchmarks.one import one_genesis_historical_product_worker as worker
frozen = Path(sys.argv[1]).resolve()
worker.FROZEN["fixture"] = {
    "sha": "0" * 40,
    "module": "experiments/fixture_product.py",
    "selective": False,
}
worker._load_surface("fixture", frozen)
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, str(frozen), str(ambient)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode != 0
    assert "imported cmpct outside frozen checkout" in completed.stderr


def test_measurement_retains_stable_frozen_runtime_provenance(tmp_path: Path) -> None:
    checkout = tmp_path / "v030"
    package = checkout / "src" / "cmpct"
    package.mkdir(parents=True)
    package_file = package / "builder.py"
    package_file.write_text("# fixture\n", encoding="utf-8")
    source_sha = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
    sample = {
        "frozen_source_sha": source_sha,
        "frozen_cmpct_import_roots": {"cmpct.builder": str(package_file)},
    }

    result = _historical_runtime_provenance(
        contender="v0.30",
        checkout=checkout,
        sample_families=[[dict(sample) for _ in range(5)], [dict(sample) for _ in range(5)]],
    )

    assert result is not None
    assert result["status"] == "source_sealed"
    assert result["source_sha"] == source_sha
    assert result["sample_count"] == 10
    assert result["loaded_cmpct_modules"]["cmpct.builder"] == str(package_file.resolve())


def test_measurement_rejects_runtime_provenance_outside_frozen_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "v030"
    (checkout / "src" / "cmpct").mkdir(parents=True)
    escaped = tmp_path / "harness" / "src" / "cmpct" / "builder.py"
    escaped.parent.mkdir(parents=True)
    escaped.write_text("# fixture\n", encoding="utf-8")
    sample = {
        "frozen_source_sha": "f4b158a55a08b9b18b50e4e4abe4b9251048c772",
        "frozen_cmpct_import_roots": {"cmpct.builder": str(escaped)},
    }

    with pytest.raises(RuntimeError, match="escaped frozen checkout"):
        _historical_runtime_provenance(
            contender="v0.30",
            checkout=checkout,
            sample_families=[[sample]],
        )
