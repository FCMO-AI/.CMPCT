from __future__ import annotations

"""Release-only post-selection elision for dead r24 dictionaries.

A trained dictionary is pure payload overhead when the finished authenticated r24 blob table proves that no
selected physical record uses CODEC_ZSTDDICT.  This transform runs only after the ordinary revision-24 builder has
finished codec competition.  It never changes training or candidate choice.  If a dictionary is live, the archive
is left byte-identical.  If it is dead, the dictionary blob is removed, all surviving references are remapped, and
both authenticated index copies are regenerated.
"""

import os
from pathlib import Path
import tempfile

import msgpack

from cmpct import codec as C


def _remap_ref(value: int, removed: int) -> int:
    value = int(value)
    if value == removed:
        raise RuntimeError("dead r24 dictionary unexpectedly referenced by logical data")
    return value - 1 if value > removed else value


def _remap_index(index: dict, removed: int) -> None:
    for row in index.get("files", []):
        storage = row[6]
        if not storage:
            continue
        mode = int(storage[0])
        if mode == C.S_BLOB:
            storage[1] = _remap_ref(storage[1], removed)
        elif mode == C.S_CHUNKS:
            storage[1] = [_remap_ref(x, removed) for x in storage[1]]
        elif mode == C.S_CDC:
            storage[1] = [[ln, _remap_ref(ref, removed)] for ln, ref in storage[1]]
        elif mode == C.S_SPARSE:
            storage[1] = [
                [off, ln, [_remap_ref(ref, removed) for ref in refs]]
                for off, ln, refs in storage[1]
            ]
        elif mode == C.S_PACK:
            storage[1] = _remap_ref(storage[1], removed)
    for recipe in index.get("recipes", []):
        recipe[0] = _remap_ref(recipe[0], removed)
        for payload in recipe[2]:
            payload[0] = _remap_ref(payload[0], removed)
            payload[3] = _remap_ref(payload[3], removed)
    index["dict_blob"] = None


def elide_dead_dictionary_in_place(path: Path) -> dict:
    """Remove an unused r24 dictionary blob atomically; otherwise leave the archive byte-identical."""
    path = Path(path)
    raw = path.read_bytes()
    magic, version, flags, ic_len, ib_len, data_len, ih = C.HDR.unpack_from(raw, 0)
    if magic != C.MAGIC or int(version) != 24:
        raise RuntimeError("dead-dictionary elision requires canonical revision 24")

    ic = raw[C.HDR.size : C.HDR.size + ic_len]
    ib = C.zd(ic, ib_len)
    if C.sha(ib) != ih:
        raise RuntimeError("r24 primary index authentication failed before dead-dictionary elision")
    index = msgpack.unpackb(ib, raw=False)
    dict_blob = index.get("dict_blob")
    if dict_blob is None:
        return {"changed": False, "reason": "no-dictionary", "saving_bytes": 0}

    dict_blob = int(dict_blob)
    blobs = index["blobs"]
    if not 0 <= dict_blob < len(blobs):
        raise RuntimeError("r24 dictionary blob index out of range")
    live_users = [i for i, row in enumerate(blobs) if int(row[3]) == C.CODEC_ZSTDDICT]
    if live_users:
        return {
            "changed": False,
            "reason": "dictionary-live",
            "live_users": live_users,
            "saving_bytes": 0,
        }

    data_start = C.HDR.size + ic_len
    data = raw[data_start : data_start + data_len]
    records = []
    for i, row in enumerate(blobs):
        off, _usize, csize, _codec, meta_len = map(int, row)
        rec_len = C.BHDR.size + meta_len + csize
        rec = data[off : off + rec_len]
        if len(rec) != rec_len:
            raise RuntimeError("truncated r24 physical record during dead-dictionary elision")
        if i != dict_blob:
            records.append((rec, row))

    _remap_index(index, dict_blob)
    new_blobs = []
    new_records = []
    offset = 0
    for rec, row in records:
        _old_off, usize, csize, codec, meta_len = map(int, row)
        new_blobs.append([offset, usize, csize, codec, meta_len])
        new_records.append(rec)
        offset += len(rec)
    index["blobs"] = new_blobs

    new_ib = msgpack.packb(index, use_bin_type=True)
    new_ic = C.zc(new_ib, 12)
    new_ih = C.sha(new_ib)
    new_data = b"".join(new_records)
    header = C.HDR.pack(C.MAGIC, 24, flags, len(new_ic), len(new_ib), len(new_data), new_ih)
    footer = C.FTR.pack(C.FMAGIC, 0, 1, 0, 0, len(new_ic), len(new_ib), 0, new_ih)
    out = header + new_ic + new_data + new_ic + footer

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.dead-dict-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(out)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return {
        "changed": True,
        "reason": "dictionary-dead",
        "removed_blob_index": dict_blob,
        "saving_bytes": len(raw) - len(out),
        "archive_bytes_before": len(raw),
        "archive_bytes_after": len(out),
    }
