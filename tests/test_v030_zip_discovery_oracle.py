from __future__ import annotations

from pathlib import Path
import zipfile

from benchmarks.v030_zip_discovery_oracle import analyze


def _zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, payload in members.items():
            info = zipfile.ZipInfo(name)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


def test_oracle_discovers_zip_structure_without_suffix_and_charges_stream_reuse(tmp_path: Path) -> None:
    payload = (b"shared-payload-" * 4096) + b"tail"
    (tmp_path / "loose.bin").write_bytes(payload)
    _zip(tmp_path / "one.docx", {"media/shared.bin": payload, "meta/a.txt": b"A" * 2048})
    _zip(tmp_path / "two.npz", {"data/shared.bin": payload, "meta/b.txt": b"B" * 2048})

    result = analyze(tmp_path)

    assert result["valid_zip_containers"] == 2
    assert result["new_content_discovered_containers"] == 2
    assert all(not row["recognized_by_current_r24_suffix_gate"] for row in result["containers"])
    assert result["exact_duplicate_stream_headroom_bytes"] > 0
    assert result["loose_plaintext_inverse_matches"] == 1
    assert result["inverse_match_plain_bytes"] == len(payload)
    assert result["claim_boundary"].endswith("no archive/product credit")


def test_oracle_preserves_existing_zip_gate_classification(tmp_path: Path) -> None:
    _zip(tmp_path / "ordinary.zip", {"a.txt": b"hello" * 100})
    result = analyze(tmp_path)
    assert result["valid_zip_containers"] == 1
    assert result["new_content_discovered_containers"] == 0
    assert result["containers"][0]["recognized_by_current_r24_suffix_gate"] is True
