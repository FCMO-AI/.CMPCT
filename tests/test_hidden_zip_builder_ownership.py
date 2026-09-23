from __future__ import annotations

import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_PACK, S_VZIP


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)


def _storage_by_rel(builder: Builder) -> dict[str, list]:
    return {row[0]: row[6] for row in builder.files if row[6] is not None}


def test_seven_explicit_archives_remain_individual_vzip_candidates(tmp_path: Path) -> None:
    """A surfaced hidden ZIP must never count toward the explicit S_PACK threshold.

    Hidden-container productization is allowed to consume *realized* explicit VZIP owners as
    evidence, but it may not perturb the pre-existing explicit ZIP/WHL cohort decision.  This
    baseline test freezes the seven-explicit side of that boundary before Builder integration.
    """
    for i in range(7):
        _write_zip(tmp_path / f"explicit-{i}.zip", (f"owner-{i}-".encode()) * 512)
    (tmp_path / "ordinary.bin").write_bytes(b"not a zip")

    b = Builder(tmp_path)
    b.scan()
    storage = _storage_by_rel(b)

    explicit = [storage[f"explicit-{i}.zip"] for i in range(7)]
    assert all(s[0] == S_VZIP for s in explicit)
    assert storage["ordinary.bin"][0] != S_PACK


def test_eight_explicit_archives_are_spack_and_not_vzip_owners(tmp_path: Path) -> None:
    """S_PACK members cannot supply inner-stream reuse ownership to hidden ZIPs.

    At eight explicit ZIP/WHL files canonical Builder intentionally chooses one container pack.
    Hidden admission must therefore treat all eight as opaque with respect to their inner Deflate
    streams; only an actually materialized S_VZIP may become a fixed evidence owner.
    """
    for i in range(8):
        _write_zip(tmp_path / f"explicit-{i}.zip", (f"owner-{i}-".encode()) * 512)

    b = Builder(tmp_path)
    b.scan()
    storage = _storage_by_rel(b)

    explicit = [storage[f"explicit-{i}.zip"] for i in range(8)]
    assert all(s[0] == S_PACK for s in explicit)
    assert not any(s[0] == S_VZIP for s in explicit)
    # All eight rows must point at the same physical pack candidate.
    assert len({bytes(s[1]) for s in explicit}) == 1


def test_parseable_explicit_archive_that_falls_back_is_not_a_vzip_owner(tmp_path: Path) -> None:
    """Parser eligibility alone cannot grant hidden-reuse ownership.

    BZIP2 is a valid ZIP method understood by Python, but CMPCT's VZIP recipe intentionally does not
    reproduce it.  Canonical Builder therefore falls back to an opaque blob; future hidden admission
    must not treat this archive's inner compressed stream as physically reusable evidence.
    """
    path = tmp_path / "fallback.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_BZIP2) as z:
        z.writestr("payload.bin", b"fallback-owner" * 1024)

    # Establish that this is a valid, parseable ZIP rather than malformed-input rejection.
    with zipfile.ZipFile(path) as z:
        assert z.read("payload.bin") == b"fallback-owner" * 1024

    b = Builder(tmp_path)
    b.scan()
    storage = _storage_by_rel(b)["fallback.zip"]
    assert storage[0] == S_BLOB
    assert storage[0] != S_VZIP
