from __future__ import annotations

import zipfile
from pathlib import Path

from cmpct.hidden_zip_candidates import ZipOwnerSource, prove_candidate_zip_ownership


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)


def test_candidate_scoped_proof_uses_realized_explicit_vzip_owner(tmp_path: Path) -> None:
    """A realized explicit VZIP may anchor a hidden owner without a root walk."""
    payload = b"shared-deflate-stream-" * 4096
    explicit = tmp_path / "owner.zip"
    hidden = tmp_path / "document.bin"
    _write_zip(explicit, payload)
    _write_zip(hidden, payload)

    proof = prove_candidate_zip_ownership(
        [
            ZipOwnerSource("owner.zip", explicit, fixed=True),
            ZipOwnerSource("document.bin", hidden),
        ],
        min_verified_reuse=2176,
    )

    assert proof.rejects == ()
    assert proof.realized == frozenset({"owner.zip", "document.bin"})
    assert proof.credit["document.bin"] >= 2176
    assert proof.owner_identities["owner.zip"] == proof.owner_identities["document.bin"]


def test_candidate_scoped_proof_does_not_invent_fixed_ownership(tmp_path: Path) -> None:
    """Without a realized explicit owner, one hidden candidate cannot subsidize itself."""
    hidden = tmp_path / "document.bin"
    _write_zip(hidden, b"solo-hidden-stream-" * 4096)

    proof = prove_candidate_zip_ownership(
        [ZipOwnerSource("document.bin", hidden)],
        min_verified_reuse=1,
    )

    assert proof.realized == frozenset()
    assert proof.credit == {}


def test_candidate_scoped_exclusion_cascades_after_stage_failure(tmp_path: Path) -> None:
    """A failed hidden stage is removed before another hidden owner may use its credit."""
    payload = b"shared-hidden-stream-" * 4096
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    _write_zip(a, payload)
    _write_zip(b, payload)

    initial = prove_candidate_zip_ownership(
        [ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)],
        min_verified_reuse=1,
    )
    assert initial.realized == frozenset({"a.bin", "b.bin"})

    after_failure = prove_candidate_zip_ownership(
        [ZipOwnerSource("a.bin", a), ZipOwnerSource("b.bin", b)],
        min_verified_reuse=1,
        excluded_owners=frozenset({"b.bin"}),
    )
    assert after_failure.realized == frozenset()
    assert after_failure.credit == {}


def test_candidate_scope_ignores_unlisted_parseable_archive(tmp_path: Path) -> None:
    """S_PACK/fallback owners cannot leak into proof merely because they exist on disk."""
    payload = b"same-stream-" * 4096
    hidden = tmp_path / "hidden.bin"
    unlisted = tmp_path / "packed-or-fallback.zip"
    _write_zip(hidden, payload)
    _write_zip(unlisted, payload)

    proof = prove_candidate_zip_ownership(
        [ZipOwnerSource("hidden.bin", hidden)],
        min_verified_reuse=1,
    )

    assert proof.realized == frozenset()
    assert "packed-or-fallback.zip" not in proof.owner_identities
