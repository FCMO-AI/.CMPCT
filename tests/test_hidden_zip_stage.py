from __future__ import annotations

import random
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.hidden_zip_candidates import ZipOwnerSource, prove_candidate_zip_ownership
from cmpct.hidden_zip_stage import commit_stable_hidden_cohort, stage_stable_hidden_cohort


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)


def _noise(seed: int, size: int = 32 * 1024) -> bytes:
    return random.Random(seed).randbytes(size)


def test_stage_failure_cascades_and_discards_previously_staged_peer(tmp_path: Path) -> None:
    payload = _noise(20); a = tmp_path / "a.bin"; b = tmp_path / "b.bin"
    _write_zip(a, payload); _write_zip(b, payload)
    sources = [ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1)
    assert proof.realized == frozenset({"a.bin", "b.bin"})
    b.unlink(); cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=1)
    assert cohort.realized == frozenset(); assert cohort.staged == {}
    assert cohort.excluded == frozenset({"b.bin"}); assert cohort.retained_candidate_bytes == 0


def test_post_proof_replacement_is_rejected_before_recipe_staging(tmp_path: Path) -> None:
    payload = _noise(23); explicit = tmp_path / "owner.zip"; hidden = tmp_path / "hidden.bin"
    _write_zip(explicit, payload); _write_zip(hidden, payload)
    sources = [ZipOwnerSource("owner.zip", explicit, fixed=True), ZipOwnerSource("hidden.bin", hidden)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1)
    assert "hidden.bin" in proof.realized
    hidden.write_bytes(b"PK\x03\x04" + b"hostile-replacement" * 10000)
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=1)
    assert cohort.realized == frozenset({"owner.zip"}); assert cohort.excluded == frozenset({"hidden.bin"})
    assert cohort.staged == {}


def test_staging_memory_refusal_becomes_owner_exclusion_before_commit(tmp_path: Path) -> None:
    payload = _noise(21); explicit = tmp_path / "owner.zip"; hidden = tmp_path / "hidden.bin"
    _write_zip(explicit, payload); _write_zip(hidden, payload)
    sources = [ZipOwnerSource("owner.zip", explicit, fixed=True), ZipOwnerSource("hidden.bin", hidden)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1)
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=1, max_staged_candidate_bytes=1)
    assert cohort.realized == frozenset({"owner.zip"}); assert cohort.staged == {}
    assert cohort.excluded == frozenset({"hidden.bin"}); assert cohort.retained_candidate_bytes == 0


def test_successful_staging_retains_no_more_than_explicit_memory_ceiling(tmp_path: Path) -> None:
    payload = _noise(22, 8 * 1024); explicit = tmp_path / "owner.zip"; hidden = tmp_path / "hidden.bin"
    _write_zip(explicit, payload); _write_zip(hidden, payload)
    sources = [ZipOwnerSource("owner.zip", explicit, fixed=True), ZipOwnerSource("hidden.bin", hidden)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1); ceiling = 64 * 1024
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=1, max_staged_candidate_bytes=ceiling)
    assert cohort.realized == frozenset({"owner.zip", "hidden.bin"}); assert set(cohort.staged) == {"hidden.bin"}
    assert 0 < cohort.retained_candidate_bytes <= ceiling; assert cohort.source_bytes_read > 0


def test_staging_does_not_mutate_builder_until_explicit_commit(tmp_path: Path) -> None:
    payload = _noise(24); a = tmp_path / "a.bin"; b = tmp_path / "b.bin"
    _write_zip(a, payload); _write_zip(b, payload)
    sources = [ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1)
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=1)
    builder = Builder(tmp_path)
    assert builder.cands == {}; assert builder.recipes == []

    storage = commit_stable_hidden_cohort(builder, cohort)
    assert set(storage) == {"a.bin", "b.bin"}
    assert all(value[0] == S_VZIP for value in storage.values())
    assert len(builder.recipes) == 2
    assert builder.cands
