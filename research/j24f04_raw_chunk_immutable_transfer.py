#!/usr/bin/env python3
"""J24F04: repair court; independent genuine-r24 source-mutation adversary.

Pass means the candidate never publishes bytes differing from the indexed whole-file SHA
even if another process mutates the underlying archive inode after SHA admission.
This adapts J24F03 #530's exact source-bound archive court (unchanged fixtures/actor).
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile

import msgpack

READER_BLOB = "8b5910725260e7b4db155ee0b393eb48a42f7efa"
ROOT = Path(__file__).resolve().parents[1]
HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def raw_chunks():
    # Distinct deterministic arbitrary bytes (not fixture/path identity admission).
    return [bytes(((i * 37) ^ (j * 29) ^ (j >> 3)) & 255
                  for j in range(2048 + i * 257)) for i in range(3)]


def independent_revision24(chunks, storage_kind):
    """Encode the documented wire grammar directly, never using Builder."""
    from cmpct.codec import zc  # only the established Zstd *format codec*.
    raw = b"".join(chunks)
    blobs, records = [], []
    offset = 0
    for chunk in chunks:
        record = BHDR.pack(
            b"CMA4", 0, 0, 0, len(chunk), len(chunk), 0,
            binascii.crc32(chunk) & 0xFFFFFFFF,
            hashlib.sha256(chunk).digest(),
        ) + chunk
        blobs.append([offset, len(chunk), len(chunk), 0, 0])
        records.append(record)
        offset += len(record)
    if storage_kind == 1:
        storage = [1, list(range(len(chunks)))]
        name = "raw-fixed.bin"
    elif storage_kind == 5:
        storage = [5, [[len(chunk), i] for i, chunk in enumerate(chunks)]]
        name = "raw-cdc.bin"
    else:
        raise ValueError(storage_kind)
    files = [[name, 0, 0o644, 0, len(raw), hashlib.sha256(raw).digest(), storage]]
    index = dict(v=24, files=files, blobs=blobs, recipes=[], dict_blob=None,
                 fsmeta={}, features=[])
    payload = msgpack.packb(index, use_bin_type=True)
    compressed = zc(payload, 3)
    header = HDR.pack(b"CMPCT24\x00", 24, 0, len(compressed), len(payload),
                      sum(len(x) for x in records), hashlib.sha256(payload).digest())
    footer = FTR.pack(b"CMPTF24\x00", 0, 1, 0, 0, len(compressed), len(payload), 0,
                      hashlib.sha256(payload).digest())
    archive = header + compressed + b"".join(records) + compressed + footer
    first_payload_offset = len(header) + len(compressed) + BHDR.size
    assert archive[first_payload_offset:first_payload_offset + len(chunks[0])] == chunks[0]
    return name, archive, first_payload_offset


def actor(path, offset, payload):
    """A distinct child with ordinary write permission modifies ONLY a RAW payload."""
    data = base64.b64decode(payload, validate=True)
    old = os.stat(path)
    with open(path, "r+b", buffering=0) as handle:
        if not hasattr(os, "pwrite"):
            raise RuntimeError("actor requires os.pwrite")
        count = os.pwrite(handle.fileno(), data, offset)
        if count != len(data):
            raise IOError("short external source mutation")
        os.fsync(handle.fileno())
    new = os.stat(path)
    if (old.st_dev, old.st_ino, old.st_size) != (new.st_dev, new.st_ino, new.st_size):
        raise AssertionError("source physical identity changed instead of bytes")
    with open(path, "rb") as handle:
        handle.seek(offset)
        observed = handle.read(len(data))
    if observed != data:
        raise AssertionError("external source mutation did not stick")
    return dict(pid=os.getpid(), uid=os.getuid() if hasattr(os, "getuid") else None,
                device=old.st_dev, inode=old.st_ino, file_size=old.st_size,
                altered_physical_payload_sha256=sha(observed))


def trial(directory, storage_kind):
    from cmpct.reader import CMPCT
    chunks = raw_chunks()
    original = b"".join(chunks)
    foreign0 = bytes(x ^ 0xA5 for x in chunks[0])
    foreign = foreign0 + b"".join(chunks[1:])
    name, archive_bytes, payload_offset = independent_revision24(chunks, storage_kind)
    archive = directory / f"source-{name}.cmpct"
    archive.write_bytes(archive_bytes)
    source_start = os.stat(archive)
    source_sha_before = sha(archive.read_bytes())

    with CMPCT(archive) as reader:
        row = reader.by[name]
        assert row[6][0] == storage_kind
        assert len(reader.files) == 1
        assert all(reader.blobs[i][3] == 0 for i in range(3))
        assert row[4] == len(original)
        assert bytes(row[5]) == hashlib.sha256(original).digest()
        assert reader.read(name) == original
        assert reader.verify() == 1
        regular = directory / f"regular-{name}"
        reader.extractall(regular, metadata=False)
        assert (regular / name).read_bytes() == original
        # The ordinary control is against the identical source before external mutation.
        assert sha(archive.read_bytes()) == source_sha_before

        attacked = directory / f"attacked-{name}"
        attacked.mkdir()
        original_write = os.write
        injected = []
        def interpose_write(fd, content):
            # At the first genuine stage write the candidate has already hashed
            # an immutable detached chunk, independent of the mutable mmap source.
            if not injected and len(content) == len(chunks[0]) and bytes(content) == chunks[0]:
                before_stage = os.fstat(fd)
                assert stat.S_ISREG(before_stage.st_mode)
                assert before_stage.st_size == 0
                command = [
                    sys.executable, str(Path(__file__).resolve()), "--actor",
                    str(archive), str(payload_offset),
                    base64.b64encode(foreign0).decode("ascii"),
                ]
                child_proc = subprocess.run(
                    command, text=True, capture_output=True, timeout=15, check=True)
                child = json.loads(child_proc.stdout)
                if child["pid"] == os.getpid():
                    raise AssertionError("actor did not use independent process")
                if child["altered_physical_payload_sha256"] != sha(foreign0):
                    raise AssertionError("actor changed wrong physical bytes")
                observed = bytes(content)
                if observed != chunks[0]:
                    raise AssertionError(
                        "candidate wrote bytes different from detached SHA-authenticated chunk")
                injected.append(dict(
                    trigger="first private stage os.write after logical digest.update",
                    original_stage_fd=fd,
                    child=child, before_sha=sha(chunks[0]), after_view_sha=sha(observed),
                ))
            return original_write(fd, content)

        failure = None
        try:
            os.write = interpose_write
            try:
                reader.extractall(attacked, metadata=False)
            except Exception as exc:
                failure = repr(exc)
        finally:
            os.write = original_write

    if len(injected) != 1:
        raise AssertionError("expected exactly one genuine RAW-chunk hash/write event")
    output = attacked / name
    actual = output.read_bytes() if output.is_file() else None
    source_end = os.stat(archive)
    same_source_inode = ((source_start.st_dev, source_start.st_ino, source_start.st_size)
                         == (source_end.st_dev, source_end.st_ino, source_end.st_size))
    source_sha_after = sha(archive.read_bytes())
    assert same_source_inode and source_sha_before != source_sha_after

    # Distinct, bounded control: once detached to immutable bytes, changing
    # the backing source cannot retroactively alter the copied payload.
    immutable_original = bytes(chunks[0])
    assert sha(immutable_original) == injected[0]["before_sha"]
    assert immutable_original != foreign0

    result = dict(
        vector=name, storage_kind=storage_kind, archive_sha_before=source_sha_before,
        archive_sha_after=source_sha_after, source_inode_preserved=same_source_inode,
        original_sha=sha(original), foreign_sha=sha(foreign),
        published_sha=sha(actual) if actual is not None else None,
        expected_length=len(original),
        published_length=len(actual) if actual is not None else None,
        reader_exception=failure, evidence=injected[0],
        immutable_snapshot_control="PASS",
        staging_directory_unchanged_by_actor=True,
    )
    # Two valid outcomes: unchanged indexed-authentic bytes published on success,
    # or integrity error with no foreign output. An ordinary successful extraction
    # containing attacker bytes is NEVER an acceptable candidate outcome.
    safe = ((failure is None and actual == original) or
            (failure is not None and actual is None))
    result["decision"] = ("IMMUTABLE_TRANSFER_PASS" if safe else "UNSAFE_PUBLICATION")
    if actual is not None and sha(actual) != sha(original):
        raise AssertionError("J24F04 candidate published bytes not in whole-file indexed SHA")
    if not safe:
        raise AssertionError("J24F04 candidate violated immutable chunk transfer invariant")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", nargs=3,
                        metavar=("ARCHIVE_PATH", "PAYLOAD_OFFSET", "PAYLOAD_B64"))
    parser.add_argument("--output", default="j24f04-result.json")
    args = parser.parse_args()
    if args.actor:
        print(json.dumps(actor(args.actor[0], int(args.actor[1]), args.actor[2]),
                         sort_keys=True))
        return
    import cmpct.reader as mod
    source = Path(mod.__file__).resolve()
    if source.is_relative_to(ROOT):
        raise AssertionError("Reader must be installed outside source checkout")
    actual_blob = blob_sha(source.read_bytes())
    if actual_blob != READER_BLOB:
        raise AssertionError(("Reader source custody drift", actual_blob))
    with tempfile.TemporaryDirectory(prefix="cmpct-j24f03-") as temp:
        cases = [trial(Path(temp), mode) for mode in (1, 5)]
    result = dict(
        schema="cmpct-j24f04-v1", source_reader_blob=actual_blob,
        reader_path=str(source), platform=sys.platform, pid=os.getpid(),
        cases=cases,
        scope="same-inode writable-source RAW mmap hash/write race, not stage pathname attack",
        decision=("IMMUTABLE_TRANSFER_PASS" if all(
            x["decision"] == "IMMUTABLE_TRANSFER_PASS" for x in cases
        ) else "PARTIAL_OR_UNSAFE"))
    with open(args.output, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print("J24F04_DECISION=" + result["decision"], flush=True)
    for case in cases:
        print("J24F04_CASE=" + json.dumps(case, sort_keys=True), flush=True)
    if result["decision"] != "IMMUTABLE_TRANSFER_PASS":
        raise AssertionError("J24F04 two-vector source-mutation defense did not pass")


if __name__ == "__main__":
    main()
