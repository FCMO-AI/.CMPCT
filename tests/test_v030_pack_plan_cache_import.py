from __future__ import annotations

import importlib.util
from pathlib import Path


def test_pack_cache_import_does_not_clone_v028_owner() -> None:
    path = Path(__file__).resolve().parents[1] / 'experiments' / 'entropygraph_v030_pack_plan_cache.py'
    spec = importlib.util.spec_from_file_location('cmpct_v030_pack_cache_lazy_test', path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._DEFAULT_V028 is None
