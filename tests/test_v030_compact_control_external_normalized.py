from __future__ import annotations

from pathlib import Path
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_external_normalized as SHADOW
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from experiments import entropygraph_v030_release_product as PRODUCT


def test_external_normalization_is_the_shadow_measurement_domain(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    p = source / "payload.bin"
    p.write_bytes(b"payload" * 1024)
    p.chmod(0o600)
    p.touch()

    seen: dict[str, Path] = {}
    real_normalize = EXT._normalized_stage
    real_verified = CONTROL._verified_r24

    def normalize(root: Path, parent: Path) -> Path:
        stage = real_normalize(root, parent)
        seen["stage"] = stage
        return stage

    def verified(root: Path, out: Path):
        seen["verified_root"] = Path(root)
        return real_verified(root, out)

    monkeypatch.setattr(EXT, "_normalized_stage", normalize)
    monkeypatch.setattr(CONTROL, "_verified_r24", verified)

    with tempfile.TemporaryDirectory(dir=tmp_path) as td:
        stage = EXT._normalized_stage(source, Path(td))
        CONTROL._verified_r24(stage, Path(td) / "candidate.cmpct")

    assert seen["verified_root"] == seen["stage"]
    assert seen["stage"] != source


def test_projection_preserves_canonical_verify_but_compares_external_tree_domain(monkeypatch, tmp_path: Path) -> None:
    """A metadata-aware CMPCT tree hash must never be compared directly to the external content-tree hash."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.bin").write_bytes((b"external-tree-domain" * 4096)[:65536])
    stage_parent = tmp_path / "normalized-parent"
    stage_parent.mkdir()
    stage = EXT._normalized_stage(source, stage_parent)

    calls = {"extract": 0}
    # PRODUCT is a compatibility-mirroring module: assigning PRODUCT.extract also mirrors that override into
    # the mature base module. Calling the promoted wrapper from the spy would therefore recurse through the
    # mirrored base binding. Capture the immutable mature delegate instead; the spy still proves the public
    # projection performs exactly one independent extraction while leaving product behavior unchanged.
    real_extract = PRODUCT._BASE_ORIGINALS["extract"]

    def extract(archive: Path, dst: Path, **kwargs):
        calls["extract"] += 1
        return real_extract(archive, dst, **kwargs)

    monkeypatch.setattr(PRODUCT, "extract", extract)
    result = SHADOW._cmpct_projection(stage, tmp_path / "candidate.cmpct")

    assert calls["extract"] == 1
    assert result["canonical_tree_sha256"]
    assert result["external_tree_sha256"] == EXT._tree(stage)
    assert result["semantic_index_roundtrip_exact"] is True
    assert result["two_authenticated_control_copies_retained"] is True
    assert result["physical_payload_records_unchanged"] is True


def test_shadow_contract_keeps_projection_research_only() -> None:
    # The exact external-normalized experiment may justify productization, but cannot itself change selector,
    # revision, or release authority.
    source = Path(SHADOW.__file__).read_text()
    assert '"release_credit": False' in source
    assert '"production_selector_change": False' in source
    assert '"format_revision_change": False' in source
    assert '"normalization_matches_external_matrix": True' in source
    assert '"tree_domains_separated": True' in source
    assert '"canonical_strong_verification_mandatory": True' in source
    assert '"external_tree_verified_by_independent_extract": True' in source
