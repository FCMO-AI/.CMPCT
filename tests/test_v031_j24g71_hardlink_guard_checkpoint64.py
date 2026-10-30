"""J24G71 source-exact composition: ensure the 64th signed checkpoint cannot
commit a dangling hardlink alias, without changing Reader/journal grammar.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FTR, K_HARDLINK
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, append_rename
from cmpct.validation import preflight_archive


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_63_signed_renames_reject_owner_delete_then_checkpoint_after_alias_delete():
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g71-") as td:
        root = Path(td)
        tree = root / "source"
        tree.mkdir()
        owner = tree / "a.dat"
        owner.write_bytes(b"authentic-hardlink-owner" * 200)
        alias = tree / "h.dat"
        os.link(owner, alias)
        (tree / "neutral.dat").write_bytes(b"independent" * 19)
        assert owner.stat().st_ino == alias.stat().st_ino

        archive = root / "signed.cmpct"
        Builder(tree, reproducible=True).build(archive)
        preflight_archive(archive)
        with CMPCT(archive) as reader:
            # The first Windows court revealed that equal source bytes were
            # not enough: the old Win32 Builder emitted two K_FILE rows.
            # Require the exact physical alias *representation*, not merely
            # success of a later guard or exact content equality.
            assert reader.by["h.dat"][1] == K_HARDLINK
            assert reader.by["h.dat"][6] == ["a.dat"]
            assert reader.read("h.dat") == reader.read("a.dat")
            assert reader.delta_depth == 0

        # Exercise the ordinary public one-op Writer, not a handmade oracle.
        current = "neutral.dat"
        for step in range(63):
            new = "neutral-alt.dat" if current == "neutral.dat" else "neutral.dat"
            append_rename(archive, current, new)
            current = new
        with CMPCT(archive) as reader:
            assert reader.delta_depth == 63
            assert reader.verify() == 3
            assert reader.read("h.dat") == reader.read("a.dat")
        preflight_archive(archive)
        before = archive.read_bytes()
        before_digest = sha(before)
        before_size = len(before)

        with pytest.raises(ValueError, match="hardlink owner"):
            append_delete(archive, "a.dat")
        with pytest.raises(ValueError, match="hardlink owner"):
            append_rename(archive, "a.dat", "z.dat")
        assert archive.read_bytes() == before, "a rejected mutation wrote archive bytes"
        assert sha(archive.read_bytes()) == before_digest
        with CMPCT(archive) as reader:
            assert reader.delta_depth == 63
            assert reader.read("h.dat") == reader.read("a.dat")
        preflight_archive(archive)

        # The 64th Writer operation legitimately removes the dependent alias.
        # This operation must checkpoint using the inherited shared replay
        # rather than silently manufacturing a dangling physical hardlink.
        append_delete(archive, "h.dat")
        final_bytes = archive.read_bytes()
        with CMPCT(archive) as reader:
            assert reader.delta_depth == 0, "writer did not commit checkpoint64"
            assert reader.verify() == 2
            assert "h.dat" not in reader.by
            assert reader.read("a.dat") == b"authentic-hardlink-owner" * 200
            assert reader.read(current) == b"independent" * 19
            final_index_sha = sha(msgpack.packb(reader.index, use_bin_type=True))
            extracted = root / "extracted"
            reader.extractall(extracted)
            assert (extracted / "a.dat").read_bytes() == owner.read_bytes()
        preflight_archive(archive)

        assert len(final_bytes) > before_size
        footer = FTR.unpack(final_bytes[-FTR.size:])
        assert footer[1] == 0, "64th generation was not a full checkpoint"
        # The now-unreferenced owner may be renamed without violating a link.
        append_rename(archive, "a.dat", "z.dat")
        with CMPCT(archive) as reader:
            assert reader.read("z.dat") == b"authentic-hardlink-owner" * 200
            assert reader.verify() == 2
        preflight_archive(archive)

        # Preserve a physically reproducible signed r24 artifact for a
        # separately-rooted parser. The receipt is honest about warm-cache
        # timing and does not assign release or compression credit.
        artifact_path = os.environ.get("J24G71_PHYSICAL")
        if artifact_path:
            dest = Path(artifact_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(final_bytes)
        receipt_path = os.environ.get("J24G71_RECEIPT")
        if receipt_path:
            receipt = {
                "schema": "cmpct-j24g71-hardlink-guard-checkpoint64-v1",
                "decision": "COMPOSED_PRECOMMIT_GUARD_CHECKPOINT64_PASS",
                "parent": "1935c14c76f1bb39fd218d73cdbee93d3c2b76a1",
                "donor": "4863ab3653e111b73ee6591f87a177f7919f25b1",
                "delta_generations_before_rejected_mutation": 63,
                "checkpoint_generation": 64,
                "rejected_owner_mutations": 2,
                "rejected_no_write_archive_sha256": before_digest,
                "checkpoint_archive_sha256": sha(final_bytes),
                "checkpoint_archive_bytes": len(final_bytes),
                "checkpoint_index_msgpack_sha256": final_index_sha,
                "wall_ns_total_builder_renames_checkpoint_extraction": time.perf_counter_ns()-t0,
                "cpu_ns_total_builder_renames_checkpoint_extraction": time.process_time_ns()-c0,
                "limitations": [
                    "Generated small corpus, 1 hardlink alias, no sparse xattrs or owner override",
                    "Warm local filesystem cache, no dedicated ABBA or RSS",
                    "No simultaneous Writers/crash injection or native C ABI parity",
                    "No release, format, frozen benchmark or full-product economics credit",
                ],
            }
            dest = Path(receipt_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
