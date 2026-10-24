"""Cross-owner product court: authenticated duplicate-index refusal closes acquired Reader handles.

PR #316 authentic signed-MessagePack duplicate rejection plus PR #283 constructor ownership.
The immutable negative witness for #316 is evaluated with its unmodified source; no GC is invoked.
"""
from __future__ import annotations

import base64
import builtins
import hashlib
import json
import sys
from pathlib import Path

import pytest

import cmpct.reader as reader

# Reuse the preregistered PR #316 exact-byte adversary, do not reimplement its index signer.
sys.path.insert(0, str(Path(__file__).parent))
from native_duplicate_root_index_oracle import HDR, Zstd, forge_authenticated_duplicate


@pytest.mark.parametrize("vector_number", [0, 1, 2])
@pytest.mark.parametrize("first_empty", [True, False])
@pytest.mark.parametrize("primary_only", [False, True])
def test_authenticated_ambiguous_index_refused_and_fd_closed(
    tmp_path, monkeypatch, vector_number, first_empty, primary_only
):
    vectors = json.loads(
        (Path(__file__).parent / "conformance" / "v24-direct-codecs.json").read_text()
    )["vectors"]
    vector = vectors[vector_number]
    original = base64.b64decode(vector["archive_base64"], validate=True)
    assert hashlib.sha256(original).hexdigest() == vector["archive_sha256"]
    hostile = forge_authenticated_duplicate(original, Zstd(), first_empty=first_empty)
    if primary_only:
        # Strip only the trailing copy+footer; leave the authenticated primary
        # MessagePack index and all physical blob records byte-identical.
        _, _, _, index_bytes, _, physical_span, _ = HDR.unpack_from(hostile)
        hostile = hostile[:HDR.size + index_bytes + physical_span]
    archive = tmp_path / f"hostile-{vector_number}-{first_empty}-{primary_only}.cmpct"
    archive.write_bytes(hostile)

    acquired = []
    real_open = builtins.open

    def watch_open(*args, **kwargs):
        f = real_open(*args, **kwargs)
        acquired.append(f)
        return f

    monkeypatch.setattr(reader, "open", watch_open, raising=False)
    with pytest.raises((ValueError, IOError)) as caught:
        reader.CMPCT(archive)
    # An exception and its traceback are deliberately retained. A false PASS via
    # refcount/GC cleanup is disallowed. PR #316 alone fails this assertion.
    assert caught.value is not None
    assert len(acquired) == 1
    assert acquired[0].closed, "authenticated duplicate-map rejection leaked Reader fd"

@pytest.mark.parametrize("vector_number", [0, 1, 2])
def test_valid_independent_primary_only_archive_survives_fallback(
    tmp_path, vector_number
):
    vectors = json.loads(
        (Path(__file__).parent / "conformance" / "v24-direct-codecs.json").read_text()
    )["vectors"]
    vector = vectors[vector_number]
    original = base64.b64decode(vector["archive_base64"], validate=True)
    assert hashlib.sha256(original).hexdigest() == vector["archive_sha256"]
    _, _, _, index_bytes, _, physical_span, _ = HDR.unpack_from(original)
    primary_only = original[:HDR.size + index_bytes + physical_span]
    archive = tmp_path / f"valid-primary-only-{vector_number}.cmpct"
    archive.write_bytes(primary_only)
    with reader.CMPCT(archive) as opened:
        assert hashlib.sha256(opened.read(vector["name"])).hexdigest() == vector["logical_sha256"]
