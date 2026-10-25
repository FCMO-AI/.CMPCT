"""O84: independent installed-product court using O81 original CRC-collision construction.\n\nThis file copies the original O81 GF(2) collision constructor unchanged, then tests\na *separate* opt-in full-member SHA API on physically modified r24 bytes.\nThe historical fast read and strong whole-archive verify remain unchanged.\n"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
import random
import shutil
import tempfile
import zipfile
import os
import time
import statistics
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, CODEC_RAW, S_VZIP
from cmpct.reader import CMPCT


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def crc(blob):
    return binascii.crc32(blob) & 0xffffffff


def same_crc_mutation(source: bytes, flip: int, patch: int) -> bytes:
    """Solve the exact CRC32 linear compensation, without using a found collision."""
    out = bytearray(source)
    out[flip] ^= 1
    target = crc(source) ^ crc(out)
    intermediate = crc(out)
    basis = {}
    for bit in range(32):
        trial = bytearray(out)
        trial[patch + bit // 8] ^= 1 << (bit % 8)
        vector = crc(trial) ^ intermediate
        mask = 1 << bit
        for pivot in sorted(basis, reverse=True):
            if vector & (1 << pivot):
                old_vector, old_mask = basis[pivot]
                vector ^= old_vector
                mask ^= old_mask
        if vector:
            basis[vector.bit_length() - 1] = (vector, mask)
    combination = 0
    for pivot in range(31, -1, -1):
        if target & (1 << pivot):
            if pivot not in basis:
                raise AssertionError("CRC correction matrix not invertible")
            vector, mask = basis[pivot]
            target ^= vector
            combination ^= mask
    if target:
        raise AssertionError("CRC correction did not close")
    for bit in range(32):
        if combination & (1 << bit):
            out[patch + bit // 8] ^= 1 << (bit % 8)
    result = bytes(out)
    assert result != source and len(result) == len(source)
    assert crc(result) == crc(source) and sha(result) != sha(source)
    return result


def make_sources():
    buf = io.BytesIO()
    comment = random.Random(810_025).randbytes(25000)
    original_member = bytes(range(256)) * 3
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr("a", original_member, compress_type=zipfile.ZIP_STORED)
        z.comment = comment
    source = buf.getvalue()
    mutated = same_crc_mutation(source, len(source) - len(comment) + 42, len(source) - 8)
    for data in (source, mutated):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None
            assert z.namelist() == ["a"]
            assert z.read("a") == original_member
    assert source[:-len(comment)] == mutated[:-len(comment)]
    return source, mutated, len(comment)


def expect_raises(exc_type, operation, what):
    try:
        operation()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}: {what}")


def _samples(operation, runs=7):
    measurements=[]
    for _ in range(runs):
        start=time.perf_counter_ns()
        operation()
        measurements.append(time.perf_counter_ns()-start)
    return measurements


def main():
    source, changed, comment_len=make_sources()
    report={
        "schema":"cmpct-o84-vzip-strong-read-v1",
        "historical_reader_git_blob":"e716233403dabd0966863c45635e18fa5ac6afb8",
        "inherited_oracle":"PR #438 O81 code blob 0ef661269a92609bfb6aeb599a7f78f2b682c9df",
        "original_zip_sha256":sha(source),
        "changed_zip_sha256":sha(changed),
        "crc32_equal":crc(source)==crc(changed),
        "default_read_tier":"CRC32",
        "source_bytes":len(source),
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o84-") as directory:
        root=Path(directory)/"root";root.mkdir()
        (root/"sample.zip").write_bytes(source)
        (root/"plain.bin").write_bytes(b"UNRELATED-MEMBER"*4096)
        alias=None
        try:
            os.link(root/"sample.zip",root/"zz-alias.zip")
            alias="zz-alias.zip"
        except (OSError, NotImplementedError):
            pass
        archive=Path(directory)/"good.cmpct"
        Builder(root,workers=1,reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            entry=reader.by["sample.zip"]
            assert entry[6][0]==S_VZIP,"invalid setup: expected genuine VZIP storage"
            rid=entry[6][1];recipe=reader.recipes[rid]
            assert reader.read("sample.zip")==source
            assert reader.read_vzip_verified("sample.zip")==source
            assert reader.read_range("sample.zip",0,32)==source[:32]
            assert reader.file_sha256("sample.zip")==bytes.fromhex(sha(source))
            if alias is not None:
                assert reader.read(alias)==source
                assert reader.read_vzip_verified(alias)==source
                report["hardlink_alias_verified"]=True
            else:
                report["hardlink_alias_verified"]="unavailable"
            assert reader.verify()>=2
            for invalid in (-1, True, None, 2.5):
                expect_raises(ValueError,lambda invalid=invalid:reader.read_vzip_verified("sample.zip",max_scan_bytes=invalid),"bad scan budget")
            saved_read=reader.read
            def forbidden_read(name):
                raise AssertionError("budget must reject before any VZIP materialization")
            reader.read=forbidden_read
            try:
                expect_raises(IOError,lambda:reader.read_vzip_verified("sample.zip",max_scan_bytes=len(source)-1),"pre-read scan budget")
                expect_raises(ValueError,lambda:reader.read_vzip_verified("plain.bin"),"non VZIP source")
            finally:
                reader.read=saved_read
            # Simulate a hostile authenticated hardlink cycle in index rows, without using
            # recursion or modifying committed on-disk format. A real forged signed index
            # remains a separate threat contract.
            if alias is not None:
                alias_row=reader.by[alias]
                saved_target=alias_row[6][0]
                alias_row[6][0]=alias
                try:
                    expect_raises(IOError,lambda:reader.read_vzip_verified(alias),"hardlink self-cycle")
                finally:
                    alias_row[6][0]=saved_target
            report["archive_bytes"]=archive.stat().st_size
            report["archive_sha256"]=sha(archive.read_bytes())
            fast_samples=_samples(lambda:reader.read("sample.zip"))
            strong_samples=_samples(lambda:reader.read_vzip_verified("sample.zip"))
            report["fast_read_wall_ns"]=fast_samples
            report["strong_read_wall_ns"]=strong_samples
            report["fast_median_ns"]=statistics.median(fast_samples)
            report["strong_median_ns"]=statistics.median(strong_samples)
            skref=recipe[0];skeleton=reader._blob(skref)
            assert skeleton[-comment_len:]==source[-comment_len:]
            mutated_skeleton=skeleton[:-comment_len]+changed[-comment_len:]
            assert crc(skeleton)==crc(mutated_skeleton)
            assert sha(skeleton)!=sha(mutated_skeleton)
            off,usize,csize,codec,ml=reader.blobs[skref]
            assert codec==CODEC_RAW and usize==csize==len(skeleton),(
                "this hosted physical tamper court requires the same RAW skeleton as O81"
            )
            record=reader.record_base+off;physical=record+BHDR.size+ml
        poisoned=Path(directory)/"poisoned.cmpct"
        shutil.copyfile(archive,poisoned)
        archive_content=bytearray(poisoned.read_bytes())
        assert bytes(archive_content[physical:physical+csize])==skeleton
        archive_content[physical:physical+csize]=mutated_skeleton
        poisoned.write_bytes(archive_content)
        with CMPCT(poisoned) as reader:
            assert reader._blob(skref)==mutated_skeleton,"CRC matched O81 original"
            assert reader.read("sample.zip")==changed,"default fast CRC tier intentionally unchanged"
            assert reader.read_range("sample.zip",0,64)==changed[:64],"normal range tier changed unexpectedly"
            expect_raises(IOError,lambda:reader.read_vzip_verified("sample.zip"),"same-CRC hostile bytes")
            if alias is not None:
                expect_raises(IOError,lambda:reader.read_vzip_verified(alias),"hardlink to corrupted VZIP")
            expect_raises(IOError,reader.verify,"original strong whole-archive verify")
            report["physical_crc_preserving_tamper_rejected"]=True
            report["physical_poisoned_archive_sha256"]=sha(poisoned.read_bytes())
        with CMPCT(archive) as reader:
            assert reader.read_vzip_verified("sample.zip")==source
            report["valid_source_control_retained"]=True
    report["decision"]="OPTIN_SHA_REJECTS_O81_PHYSICAL_COLLISION; FAST_READ_UNCHANGED"
    return report


if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
