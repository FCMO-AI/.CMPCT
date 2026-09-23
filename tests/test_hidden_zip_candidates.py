from __future__ import annotations

import os
import random
import zipfile
from pathlib import Path

from cmpct.hidden_zip_candidates import ZipOwnerSource, prove_candidate_zip_ownership


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)


def _noise(seed: int, size: int = 32 * 1024) -> bytes:
    return random.Random(seed).randbytes(size)


def test_candidate_scoped_proof_uses_realized_explicit_vzip_owner(tmp_path: Path) -> None:
    """A realized explicit VZIP may anchor a hidden owner without a root walk."""
    payload = _noise(1)
    explicit = tmp_path / "owner.zip"
    hidden = tmp_path / "document.bin"
    _write_zip(explicit, payload)
    _write_zip(hidden, payload)

    proof = prove_candidate_zip_ownership(
        [ZipOwnerSource("owner.zip", explicit, fixed=True), ZipOwnerSource("document.bin", hidden)],
        min_verified_reuse=2176,
    )

    assert proof.rejects == ()
    assert proof.realized == frozenset({"owner.zip", "document.bin"})
    assert proof.credit["document.bin"] >= 2176
    assert proof.owner_identities["owner.zip"] == proof.owner_identities["document.bin"]


def test_candidate_scoped_proof_does_not_invent_fixed_ownership(tmp_path: Path) -> None:
    hidden = tmp_path / "document.bin"
    _write_zip(hidden, _noise(2))
    proof = prove_candidate_zip_ownership([ZipOwnerSource("document.bin", hidden)], min_verified_reuse=1)
    assert proof.realized == frozenset()
    assert proof.credit == {}


def test_candidate_scoped_exclusion_cascades_after_stage_failure(tmp_path: Path) -> None:
    payload = _noise(3)
    a = tmp_path / "a.bin"; b = tmp_path / "b.bin"
    _write_zip(a, payload); _write_zip(b, payload)
    initial = prove_candidate_zip_ownership([ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)], min_verified_reuse=1)
    assert initial.realized == frozenset({"a.bin", "b.bin"})
    after_failure = prove_candidate_zip_ownership(
        [ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)],
        min_verified_reuse=1,
        excluded_owners=frozenset({"b.bin"}),
    )
    assert after_failure.realized == frozenset()
    assert after_failure.credit == {}


def test_candidate_scope_ignores_unlisted_parseable_archive(tmp_path: Path) -> None:
    payload = _noise(4)
    hidden = tmp_path / "hidden.bin"; unlisted = tmp_path / "packed-or-fallback.zip"
    _write_zip(hidden, payload); _write_zip(unlisted, payload)
    proof = prove_candidate_zip_ownership([ZipOwnerSource("hidden.bin", hidden)], min_verified_reuse=1)
    assert proof.realized == frozenset()
    assert "packed-or-fallback.zip" not in proof.owner_identities


def test_candidate_scope_fails_closed_when_content_binding_cannot_fit_io_budget(tmp_path: Path) -> None:
    payload = _noise(5)
    explicit = tmp_path / "owner.zip"; hidden = tmp_path / "hidden.bin"
    _write_zip(explicit, payload); _write_zip(hidden, payload)
    proof = prove_candidate_zip_ownership(
        [ZipOwnerSource("owner.zip", explicit, fixed=True), ZipOwnerSource("hidden.bin", hidden)],
        min_verified_reuse=1,
        max_io_bytes=4096,
    )
    assert "hidden.bin" not in proof.realized
    assert dict(proof.rejects).get("io_budget", 0) >= 1


def test_candidate_scope_hardlink_aliases_cannot_fake_two_physical_owners(tmp_path: Path) -> None:
    """Two names for one inode are not two reuse owners, even if a caller supplies both."""
    first = tmp_path / "first.bin"
    alias = tmp_path / "alias.bin"
    _write_zip(first, _noise(6))
    os.link(first, alias)

    proof = prove_candidate_zip_ownership(
        [ZipOwnerSource("first.bin", first), ZipOwnerSource("alias.bin", alias)],
        min_verified_reuse=1,
    )

    assert proof.realized == frozenset()
    assert proof.owner_identities == {}
    assert dict(proof.rejects).get("physical_alias") == 2


def test_candidate_scope_fails_closed_before_per_source_work_when_owner_set_is_oversized(tmp_path: Path) -> None:
    """A hostile surfaced-owner count cannot turn candidate proof into an unbounded stat/parser pass."""
    # Paths intentionally do not exist. The source-count guard must fire before any per-source stat;
    # otherwise these would be reported as source_changed instead of one whole-proof refusal.
    sources = [ZipOwnerSource(f"candidate-{i}.bin", tmp_path / f"missing-{i}.bin") for i in range(3)]
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=1, max_sources=2)

    assert proof.realized == frozenset()
    assert proof.owner_identities == {}
    assert proof.source_states == {}
    assert proof.io_bytes == 0
    assert proof.logical_bytes == 0
    assert proof.rejects == (("source_budget", 3),)
