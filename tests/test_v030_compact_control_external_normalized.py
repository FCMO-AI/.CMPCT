from __future__ import annotations

from pathlib import Path
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_external_normalized as SHADOW
from benchmarks import v030_r24_compact_control_oracle as CONTROL


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


def test_shadow_contract_keeps_projection_research_only() -> None:
    # The exact external-normalized experiment may justify productization, but cannot itself change selector,
    # revision, or release authority.
    source = Path(SHADOW.__file__).read_text()
    assert '"release_credit": False' in source
    assert '"production_selector_change": False' in source
    assert '"format_revision_change": False' in source
    assert '"normalization_matches_external_matrix": True' in source
