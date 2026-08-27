from __future__ import annotations

"""Release-only r24 dictionary cost removal after exact promotion evidence.

Two independent optimizations live here because they address the same trained-dictionary lifecycle while keeping
historical revision-24 builders untouched:

* Before training, the promoted release r24 build skips dictionary training only inside its own thread-local build
  boundary when the generic proven envelope ``regular_files >= 5`` and ``dictionary_sample_count >= 32`` holds.
  The frozen 15-workload campaign plus nine unseen/adversarial families found zero byte/tree counterexamples; two
  positive unseen trees exercised real training and saved ~127 ms and ~163 ms while remaining byte-identical.
* After codec selection, a trained dictionary is removed only when the authenticated blob table proves that no
  selected physical record uses ``CODEC_ZSTDDICT``. Live dictionaries remain byte-identical.

The pre-training optimization is deliberately scoped around the promoted release r24 builder rather than installed
as a new mature Builder heuristic. Research and historical callers therefore continue to observe the unmodified
trainer unless they explicitly enter the release r24 build boundary. Neither optimization changes revision-24
grammar, reader semantics, locality, recovery, or codec selection for a live dictionary.
"""

import os
from pathlib import Path
import sys
import tempfile
import threading

import msgpack

from cmpct import builder as R24_BUILDER
from cmpct import codec as C

DICTIONARY_SKIP_MIN_REGULAR_FILES = 5
DICTIONARY_SKIP_MIN_SAMPLE_COUNT = 32
_DICTIONARY_SKIP_POLICY = threading.local()


# Preserve the mature trainer once even if this release-only module is reloaded by tests/diagnostics.
if not hasattr(R24_BUILDER.Builder, "_cmpct_v030_original_train_dictionary"):
    R24_BUILDER.Builder._cmpct_v030_original_train_dictionary = R24_BUILDER.Builder._train_dictionary
_ORIGINAL_TRAIN_DICTIONARY = R24_BUILDER.Builder._cmpct_v030_original_train_dictionary


def _dictionary_training_features(builder) -> dict[str, int]:
    """Return the exact cheap facts available immediately before mature dictionary training."""
    regular_files = sum(
        1
        for row in builder.files
        if row and int(row[1]) in (C.K_FILE, C.K_HARDLINK)
    )
    samples = [
        cand.raw
        for cand in builder.cands.values()
        if len(cand.raw) >= 64
        and ".cmpct-pack" not in cand.hints
        and any(hint in R24_BUILDER.TEXT_EXT for hint in cand.hints)
    ]
    return {
        "regular_files": regular_files,
        "dictionary_sample_count": len(samples),
        "dictionary_sample_bytes": sum(map(len, samples)),
    }


def _dictionary_training_skip_admitted(features: dict[str, int]) -> bool:
    return (
        int(features["regular_files"]) >= DICTIONARY_SKIP_MIN_REGULAR_FILES
        and int(features["dictionary_sample_count"]) >= DICTIONARY_SKIP_MIN_SAMPLE_COUNT
    )


def _release_dictionary_train(self):
    """Dispatch to the mature trainer except inside the promoted release-r24 build boundary."""
    if not getattr(_DICTIONARY_SKIP_POLICY, "active", False):
        return _ORIGINAL_TRAIN_DICTIONARY(self)

    features = _dictionary_training_features(self)
    self._v030_dictionary_training_features = dict(features)
    if _dictionary_training_skip_admitted(features):
        self.dictionary = b""
        self.dict_hash = None
        self._v030_dictionary_training_skip_applied = True
        return None

    self._v030_dictionary_training_skip_applied = False
    return _ORIGINAL_TRAIN_DICTIONARY(self)


# The dispatcher itself is permanent and thread-safe; outside the release-owned thread-local boundary it is an
# exact delegation to the mature trainer. This avoids process-global mutate/restore races with concurrent r25 and
# research builds.
R24_BUILDER.Builder._train_dictionary = _release_dictionary_train


def _install_release_r24_boundary() -> None:
    """Wrap only the promoted release r24 materializer when its base module is already loaded.

    ``entropygraph_v030_release_product`` imports its base first and this module second, then captures the resulting
    r24 build function. Direct research Builder calls therefore remain outside this boundary and preserve the
    independent promotion oracle's historical shipping-vs-no-dictionary A/B.
    """
    base = sys.modules.get("experiments.entropygraph_v030_release_product_base")
    if base is None or getattr(base, "_cmpct_v030_dictionary_skip_boundary_installed", False):
        return

    original = base._locality_bounded_r24_build

    def release_r24_build(root, out):
        previous = getattr(_DICTIONARY_SKIP_POLICY, "active", False)
        _DICTIONARY_SKIP_POLICY.active = True
        try:
            stats = dict(original(root, out))
        finally:
            _DICTIONARY_SKIP_POLICY.active = previous
        return {
            **stats,
            "r24_dictionary_training_skip": "structural-pretraining-v1",
            "r24_dictionary_training_skip_min_regular_files": DICTIONARY_SKIP_MIN_REGULAR_FILES,
            "r24_dictionary_training_skip_min_sample_count": DICTIONARY_SKIP_MIN_SAMPLE_COUNT,
        }

    base._locality_bounded_r24_build = release_r24_build
    base._cmpct_v030_dictionary_skip_boundary_installed = True
    base._cmpct_v030_dictionary_skip_original_r24_build = original


_install_release_r24_boundary()


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
