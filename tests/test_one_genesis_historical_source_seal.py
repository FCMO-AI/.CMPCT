from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


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
