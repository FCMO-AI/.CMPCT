from __future__ import annotations

from pathlib import Path

import pytest

import benchmarks.one.one_genesis_historical_product_worker as worker


class FakeSurface:
    def __init__(self, *, corrupt_extract: bool = False, corrupt_selective: bool = False, verify_ok: bool = True):
        self.corrupt_extract = corrupt_extract
        self.corrupt_selective = corrupt_selective
        self.verify_ok = verify_ok

    def build(self, root: Path, archive: Path):
        payload = b"FAKE-ARCHIVE\0" + b"".join(
            p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()
        )
        archive.write_bytes(payload)
        return {"bytes": len(payload)}

    def strong_verify(self, _archive: Path):
        return {"ok": self.verify_ok}

    def extract(self, _archive: Path, dst: Path):
        dst.mkdir(parents=True, exist_ok=True)
        # Tests use a fixed source tree; copy it from injected attribute.
        for path in self.source_root.rglob("*"):
            if path.is_file():
                out = dst / path.relative_to(self.source_root)
                out.parent.mkdir(parents=True, exist_ok=True)
                data = path.read_bytes()
                if self.corrupt_extract and path.name == "a.bin":
                    data = data + b"!"
                out.write_bytes(data)

    def read_member_with_stats(self, _archive: Path, member: str):
        data = (self.source_root / member).read_bytes()
        if self.corrupt_selective:
            data = data + b"!"
        return data, {"archive_bytes_read": 123, "member_bytes": len(data)}


def _tree(tmp_path: Path) -> Path:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.bin").write_bytes(b"alpha" * 100)
    (root / "nested").mkdir()
    (root / "nested" / "b.bin").write_bytes(b"beta" * 77)
    return root


def _install(monkeypatch: pytest.MonkeyPatch, contender: str, surface: FakeSurface, root: Path):
    monkeypatch.setattr(worker, "_git_head", lambda _checkout: worker.FROZEN[contender]["sha"])
    surface.source_root = root
    fake_roots = {"cmpct": str((root.parent / "src" / "cmpct" / "__init__.py").resolve())}
    monkeypatch.setattr(worker, "_load_surface", lambda _contender, _checkout: (surface, fake_roots))
    monkeypatch.setattr(worker, "_assert_frozen_cmpct_imports", lambda _checkout: fake_roots)
    monkeypatch.setattr(worker, "_forbidden_imports", lambda: [])


def test_wrong_frozen_checkout_sha_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    monkeypatch.setattr(worker, "_forbidden_imports", lambda: [])
    monkeypatch.setattr(worker, "_git_head", lambda _checkout: "0" * 40)
    with pytest.raises(RuntimeError, match="checkout SHA mismatch"):
        worker.run(
            contender="v029", mode="build", checkout=tmp_path, root=root,
            archive=tmp_path / "a.cmpct", member=None, transfer_fixture=True,
        )


def test_production_requires_executor_authorization(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    monkeypatch.setattr(worker, "_forbidden_imports", lambda: [])
    monkeypatch.setattr(worker, "_git_head", lambda _checkout: worker.FROZEN["v029"]["sha"])
    monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    with pytest.raises(RuntimeError, match="requires executor authorization"):
        worker.run(
            contender="v029", mode="build", checkout=tmp_path, root=root,
            archive=tmp_path / "a.cmpct", member=None, transfer_fixture=False,
        )


def test_build_reports_actual_persistent_archive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface()
    _install(monkeypatch, "v029", surface, root)
    archive = tmp_path / "a.cmpct"
    row = worker.run(
        contender="v029", mode="build", checkout=tmp_path, root=root,
        archive=archive, member=None, transfer_fixture=True,
    )
    assert row["stored_bytes"] == archive.stat().st_size
    assert row["stored_bytes"] > 0
    assert row["authorization"]["production_authorized"] is False
    assert row["frozen_source_sha"] == worker.FROZEN["v029"]["sha"]
    assert row["frozen_cmpct_import_roots"]
    assert row["comparison_executed"] is False
    assert row["scoring_executed"] is False
    assert row["cpu_s"] >= 0
    assert row["wall_s"] >= 0
    assert row["peak_rss_bytes"] >= 0


def test_whole_reconstruction_is_checked_independently(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface(corrupt_extract=True)
    _install(monkeypatch, "v030", surface, root)
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"placeholder")
    with pytest.raises(RuntimeError, match="whole reconstruction mismatch"):
        worker.run(
            contender="v030", mode="whole", checkout=tmp_path, root=root,
            archive=archive, member=None, transfer_fixture=True,
        )


def test_failed_strong_verify_is_not_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface(verify_ok=False)
    _install(monkeypatch, "v030", surface, root)
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"placeholder")
    with pytest.raises(RuntimeError, match="strong_verify failed"):
        worker.run(
            contender="v030", mode="whole", checkout=tmp_path, root=root,
            archive=archive, member=None, transfer_fixture=True,
        )


def test_v029_selective_is_explicitly_unsupported(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface()
    _install(monkeypatch, "v029", surface, root)
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"placeholder")
    with pytest.raises(RuntimeError, match="no proven frozen selective member surface"):
        worker.run(
            contender="v029", mode="selective", checkout=tmp_path, root=root,
            archive=archive, member="a.bin", transfer_fixture=True,
        )


def test_v030_selective_requires_exact_returned_bytes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface(corrupt_selective=True)
    _install(monkeypatch, "v030", surface, root)
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"placeholder")
    with pytest.raises(RuntimeError, match="selective reconstruction mismatch"):
        worker.run(
            contender="v030", mode="selective", checkout=tmp_path, root=root,
            archive=archive, member="a.bin", transfer_fixture=True,
        )


def test_v030_selective_preserves_raw_access_stats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    root = _tree(tmp_path)
    surface = FakeSurface()
    _install(monkeypatch, "v030", surface, root)
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"placeholder")
    row = worker.run(
        contender="v030", mode="selective", checkout=tmp_path, root=root,
        archive=archive, member="a.bin", transfer_fixture=True,
    )
    assert row["exact"] is True
    assert row["returned_bytes"] == len((root / "a.bin").read_bytes())
    assert row["product_access_stats"]["archive_bytes_read"] == 123
    assert row["frozen_source_sha"] == worker.FROZEN["v030"]["sha"]
    assert row["frozen_cmpct_import_roots"]
    assert row["comparison_executed"] is False
    assert row["winner_selected"] is False
