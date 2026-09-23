from __future__ import annotations

import os
import random
import zipfile
from pathlib import Path

from cmpct.builder import Builder
import cmpct.builder_hidden_zip as builder_hidden_zip
from cmpct.builder_hidden_zip import (
    SurfacedHiddenCandidate, ordinary_storage_for_hidden_fallback, ownership_sources_from_builder,
    read_surfaced_candidate, resolve_hidden_zip_candidates, surface_hidden_candidate,
)
from cmpct.codec import CHUNK, S_BLOB, S_CDC, S_PACK, S_VZIP, sha
from cmpct.hidden_zip_candidates import prove_candidate_zip_ownership


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z: z.writestr("payload.bin", payload)


def _stamp(path: Path) -> tuple[int, int, int, int]:
    st = path.stat(); return int(st.st_dev), int(st.st_ino), int(st.st_size), int(st.st_mtime_ns)


def _storage(builder: Builder) -> dict[str, list]: return {row[0]: row[6] for row in builder.files if row[6] is not None}


def _fixture(root: Path, explicit_count: int) -> Path:
    payload = random.Random(77).randbytes(32 * 1024)
    for i in range(explicit_count): _write_zip(root / f"explicit-{i}.zip", payload)
    hidden = root / "hidden-document.bin"; _write_zip(hidden, payload); return hidden


def test_seven_explicit_plus_hidden_preserves_explicit_cohort_and_allows_realized_evidence(tmp_path: Path) -> None:
    hidden = _fixture(tmp_path, 7); builder = Builder(tmp_path); builder.scan(); storage = _storage(builder)
    assert all(storage[f"explicit-{i}.zip"][0] == S_VZIP for i in range(7))
    sources = ownership_sources_from_builder(builder, [("hidden-document.bin", hidden)])
    assert {source.rel for source in sources if source.fixed} == {f"explicit-{i}.zip" for i in range(7)}
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=2176)
    assert "hidden-document.bin" in proof.realized; assert proof.credit["hidden-document.bin"] >= 2176


def test_eight_explicit_plus_hidden_preserves_spack_and_supplies_zero_inner_evidence(tmp_path: Path) -> None:
    hidden = _fixture(tmp_path, 8); builder = Builder(tmp_path); builder.scan(); storage = _storage(builder)
    assert all(storage[f"explicit-{i}.zip"][0] == S_PACK for i in range(8))
    sources = ownership_sources_from_builder(builder, [("hidden-document.bin", hidden)])
    assert not any(source.fixed for source in sources); assert {source.rel for source in sources} == {"hidden-document.bin"}
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1)
    assert proof.realized == frozenset(); assert proof.credit == {}


def test_composed_resolution_commits_only_stable_hidden_winner(tmp_path: Path) -> None:
    hidden = _fixture(tmp_path, 7); builder = Builder(tmp_path); builder.scan(); recipes_before = len(builder.recipes)
    result = resolve_hidden_zip_candidates(builder, [("hidden-document.bin", hidden)], min_verified_reuse=2176)
    assert "hidden-document.bin" in result.proof.realized; assert "hidden-document.bin" in result.cohort.realized
    assert result.storage["hidden-document.bin"][0] == S_VZIP; assert len(builder.recipes) == recipes_before + 1


def test_composed_resolution_cannot_borrow_from_spack(tmp_path: Path) -> None:
    hidden = _fixture(tmp_path, 8); builder = Builder(tmp_path); builder.scan(); recipes_before = len(builder.recipes); candidates_before = set(builder.cands)
    result = resolve_hidden_zip_candidates(builder, [("hidden-document.bin", hidden)], min_verified_reuse=1)
    assert result.proof.realized == frozenset(); assert result.cohort.realized == frozenset(); assert result.storage == {}
    assert len(builder.recipes) == recipes_before; assert set(builder.cands) == candidates_before


def test_bridge_source_cap_refuses_optional_resolution_before_copying_hostile_candidate_set(tmp_path: Path, monkeypatch) -> None:
    builder = Builder(tmp_path); monkeypatch.setattr(builder_hidden_zip, "MAX_OBSERVATION_FILES", 2)
    candidates = [(f"missing-{i}.bin", tmp_path / f"missing-{i}.bin") for i in range(3)]
    result = resolve_hidden_zip_candidates(builder, candidates, min_verified_reuse=1)
    assert result.sources == (); assert result.proof.realized == frozenset(); assert result.cohort.realized == frozenset(); assert result.storage == {}
    assert builder.cands == {}; assert builder.recipes == []


def test_realized_explicit_owner_is_bound_to_bytes_builder_materialized(tmp_path: Path) -> None:
    payload = random.Random(91).randbytes(32 * 1024); explicit = tmp_path / "owner.zip"; hidden = tmp_path / "hidden.bin"
    _write_zip(explicit, payload); _write_zip(hidden, payload); builder = Builder(tmp_path); builder.scan()
    assert _storage(builder)["owner.zip"][0] == S_VZIP
    with zipfile.ZipFile(explicit, "a") as z: z.comment = b"replacement-container"
    proof = prove_candidate_zip_ownership(ownership_sources_from_builder(builder, [("hidden.bin", hidden)]), min_verified_reuse=1)
    assert "owner.zip" not in proof.source_states; assert "hidden.bin" not in proof.realized
    assert dict(proof.rejects).get("source_changed", 0) >= 1


def test_surfaced_hidden_fallback_read_requires_same_scan_snapshot(tmp_path: Path) -> None:
    hidden = tmp_path / "hidden.bin"; _write_zip(hidden, random.Random(93).randbytes(4096)); raw = hidden.read_bytes()
    surfaced = surface_hidden_candidate("hidden.bin", hidden, hidden.stat(), raw)
    assert surfaced == SurfacedHiddenCandidate("hidden.bin", hidden, _stamp(hidden), sha(raw))
    assert read_surfaced_candidate(surfaced) == raw
    replacement = tmp_path / "replacement.bin"; _write_zip(replacement, random.Random(94).randbytes(4096)); os.replace(replacement, hidden)
    assert read_surfaced_candidate(surfaced) is None


def test_hidden_fallback_small_blob_policy_matches_canonical_ordinary_path(tmp_path: Path) -> None:
    raw = b"ordinary-small" * 100
    ordinary_root = tmp_path / "ordinary"; ordinary_root.mkdir(); (ordinary_root / "x.bin").write_bytes(raw)
    canonical = Builder(ordinary_root); canonical.scan(); canonical_storage = _storage(canonical)["x.bin"]
    fallback = Builder(tmp_path / "unused"); fallback_storage = ordinary_storage_for_hidden_fallback(fallback, raw, ".bin")
    assert canonical_storage[0] == fallback_storage[0] == S_BLOB
    assert canonical_storage[1] == fallback_storage[1] == sha(raw)


def test_hidden_fallback_large_cdc_policy_matches_canonical_ordinary_path(tmp_path: Path) -> None:
    raw = random.Random(95).randbytes(4 * CHUNK + 1)
    ordinary_root = tmp_path / "ordinary"; ordinary_root.mkdir(); (ordinary_root / "x.bin").write_bytes(raw)
    canonical = Builder(ordinary_root); canonical.scan(); canonical_storage = _storage(canonical)["x.bin"]
    fallback = Builder(tmp_path / "unused"); fallback_storage = ordinary_storage_for_hidden_fallback(fallback, raw, ".bin")
    assert canonical_storage[0] == fallback_storage[0] == S_CDC
    assert canonical_storage[1] == fallback_storage[1]
