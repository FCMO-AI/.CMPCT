from __future__ import annotations

from pathlib import Path
import types

import pytest

import benchmarks.one.one_genesis_cmpct1_frozen_worker_launcher as mod


def test_launcher_rejects_checkout_sha_substitution(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()
    monkeypatch.chdir(checkout)
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "a" * 40)

    class Result:
        stdout = "true\n"

    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.setattr(mod.subprocess, "check_output", lambda *args, **kwargs: "b" * 40 + "\n")
    with pytest.raises(RuntimeError, match="checkout differs from executor-sealed source"):
        mod._sealed_candidate_root()


@pytest.mark.parametrize(
    "status_line",
    (
        " M experiments/one/general_law_archive.py\n",
        " D experiments/one/authenticated_archive_envelope.py\n",
        "?? experiments/one/injected_runtime.py\n",
        " M benchmarks/one/one_genesis_cmpct1_product_worker.py\n",
    ),
)
def test_launcher_rejects_runtime_worktree_drift(monkeypatch, tmp_path: Path, status_line: str):
    checkout = tmp_path / "candidate"
    checkout.mkdir()

    class Result:
        stdout = status_line

    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        assert kwargs.get("check") is True
        return Result()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="runtime worktree differs from sealed Git state"):
        mod._assert_runtime_worktree_sealed(checkout)
    assert calls == [[
        "git",
        "-C",
        str(checkout),
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *mod.SEALED_RUNTIME_PATHS,
    ]]


def test_launcher_accepts_clean_runtime_worktree(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()

    class Result:
        stdout = ""

    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: Result())
    mod._assert_runtime_worktree_sealed(checkout)


def test_launcher_import_must_resolve_inside_candidate_checkout(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()
    outside = tmp_path / "harness" / "benchmarks" / "one" / "one_genesis_cmpct1_product_worker.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("# fake\n", encoding="utf-8")
    monkeypatch.setattr(mod, "_sealed_candidate_root", lambda: checkout.resolve())
    fake = types.SimpleNamespace(__file__=str(outside))
    monkeypatch.setattr(mod.importlib, "import_module", lambda _name: fake)
    with pytest.raises(RuntimeError, match="not imported from sealed candidate checkout"):
        mod._load_candidate_worker()


def test_launcher_passes_harness_boundary_only_after_candidate_import(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    worker_path = checkout / "benchmarks" / "one" / "one_genesis_cmpct1_product_worker.py"
    worker_path.parent.mkdir(parents=True)
    worker_path.write_text("# fake\n", encoding="utf-8")
    monkeypatch.setattr(mod, "_sealed_candidate_root", lambda: checkout.resolve())
    fake = types.SimpleNamespace(__file__=str(worker_path), CANDIDATE_BOUNDARY_MANIFEST=None)
    monkeypatch.setattr(mod.importlib, "import_module", lambda _name: fake)
    loaded = mod._load_candidate_worker()
    assert loaded is fake
    assert loaded.CANDIDATE_BOUNDARY_MANIFEST == mod.HARNESS_BOUNDARY


def test_main_requires_real_gate_authorization(monkeypatch):
    monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    monkeypatch.setattr(mod, "_load_candidate_worker", lambda: pytest.fail("candidate worker must not load"))
    with pytest.raises(RuntimeError, match="explicit real-gate"):
        mod.main()
