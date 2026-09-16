from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

from experiments import entropygraph_v030_release_product as product
from experiments import entropygraph_v030_release_reader_policy as policy


def test_verified_staging_streams_without_nested_transaction(tmp_path, monkeypatch) -> None:
    archive = tmp_path / "candidate.cmpct"
    archive.write_bytes(b"fixture")
    staging = tmp_path / "staging"
    calls: list[tuple[Path, Path, int]] = []

    monkeypatch.setattr(policy.R, "_magic", lambda _archive: policy.R.G04.MAG)

    def stream(source: Path, target: Path, budget: int) -> dict:
        calls.append((Path(source), Path(target), int(budget)))
        target.mkdir(parents=True, exist_ok=True)
        (target / "payload.bin").write_bytes(b"verified")
        return {"ok": True, "tree_sha256": "fixture"}

    monkeypatch.setattr(policy.R, "_stream_g04", stream)
    monkeypatch.setattr(
        policy.R,
        "_transactional_extract",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("verified staging helper must not create its own publication transaction")
        ),
    )

    result = policy.extract_verified_into_staging(archive, staging, max_output_bytes=123)

    assert result["ok"] is True
    assert calls == [(archive, staging, 123)]
    assert (staging / "payload.bin").read_bytes() == b"verified"


def test_release_product_r25_extract_owns_single_publication_boundary(tmp_path, monkeypatch) -> None:
    archive = tmp_path / "candidate.cmpct"
    archive.write_bytes(b"fixture")
    destination = tmp_path / "out"
    decoded = {"regular": {}, "manifest": {"entries": []}}
    events: list[str] = []

    monkeypatch.setattr(product, "_revision_for_archive", lambda _archive: (product.REVISION, "geometry-g04"))
    monkeypatch.setattr(product.C, "_validated_manifest", lambda _archive: decoded)
    monkeypatch.setattr(product.C, "_validate_safe_symlinks", lambda _decoded: None)
    monkeypatch.setattr(product.C, "_revision25_profile_context", lambda: nullcontext())
    monkeypatch.setattr(
        product.POLICY,
        "extract",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("shipping r25 extraction must not invoke nested transactional POLICY.extract")
        ),
    )
    monkeypatch.setattr(
        product.FS,
        "restore_manifest_tree",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("shipping r25 extraction must not re-enter the generic digest-restoration path")
        ),
    )

    def stream(_archive: Path, staging: Path, *, max_output_bytes: int) -> dict:
        events.append("stream")
        staging.mkdir(parents=True, exist_ok=True)
        (staging / "payload.bin").write_bytes(b"verified")
        assert max_output_bytes >= 1
        return {"ok": True}

    def restore(staging: Path, observed: dict, *, safe_symlinks: bool) -> None:
        events.append("restore")
        assert observed is decoded
        assert safe_symlinks is False
        assert (staging / "payload.bin").read_bytes() == b"verified"

    def publish(staging: Path, dst: Path) -> None:
        events.append("publish")
        staging.rename(dst)

    monkeypatch.setattr(product.POLICY, "extract_verified_into_staging", stream)
    monkeypatch.setattr(product.VERIFIED_RESTORE, "restore_verified_manifest_tree", restore)
    monkeypatch.setattr(product.C, "_publish_tree", publish)

    product.extract(archive, destination, max_output_bytes=1024)

    assert events == ["stream", "restore", "publish"]
    assert (destination / "payload.bin").read_bytes() == b"verified"
