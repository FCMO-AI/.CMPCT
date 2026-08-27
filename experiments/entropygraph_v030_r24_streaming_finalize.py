from __future__ import annotations

"""Reusable byte-identical r24 streaming finalizer for v0.30 productization.

This module is deliberately not wired into shipping selection yet.  It moves the successful memory-shape
prototype out of benchmark-only code so exact-byte/RSS evidence can promote one implementation instead of
copying an oracle into production later.  Encoder policy, revision-24 grammar, codec competition, ordering,
integrity and metadata semantics are inherited unchanged from ``cmpct.builder.Builder``.
"""

import binascii
import concurrent.futures
from pathlib import Path
import shutil
import tempfile
import zipfile

import msgpack

import cmpct.builder as B

SPOOL_MEMORY_BYTES = 1024 * 1024
MAX_IN_FLIGHT_FACTOR = 2


class StreamingFinalizeBuilder(B.Builder):
    """Revision-24 Builder that bounds compressed-record/final-archive materialization.

    Output ordering is exactly the mature sorted-content-hash order.  The only architectural change is that
    compressed records are consumed in order into a bounded spool and the final archive is written sequentially,
    avoiding the mature ``encoded`` + ``records`` + joined-data + whole-archive concatenation residency stack.
    """

    def build(self, out: Path):
        self.scan()
        self._build_micro_packs()
        self._prepare_deflate_reuse()
        self._train_dictionary()

        ordered_hashes = sorted(self.cands)
        blobs = []
        href = {}
        offset = 0

        def encode(h):
            c = self.cands[h]
            codec, comp, meta = self._encode_candidate(h, c)
            return h, len(c.raw), codec, comp, meta

        with tempfile.SpooledTemporaryFile(max_size=SPOOL_MEMORY_BYTES, mode="w+b") as spool:
            if self.encode_workers > 1 and len(ordered_hashes) > 1:
                worker_count = min(self.encode_workers, len(ordered_hashes))
                max_in_flight = max(worker_count, worker_count * MAX_IN_FLIGHT_FACTOR)
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=worker_count, thread_name_prefix="cmpct-encode-stream"
                ) as pool:
                    pending = {}
                    submit_index = 0
                    consume_index = 0
                    while submit_index < min(max_in_flight, len(ordered_hashes)):
                        h = ordered_hashes[submit_index]
                        pending[submit_index] = pool.submit(encode, h)
                        submit_index += 1
                    while consume_index < len(ordered_hashes):
                        h, raw_len, codec, comp, meta = pending.pop(consume_index).result()
                        if submit_index < len(ordered_hashes):
                            nh = ordered_hashes[submit_index]
                            pending[submit_index] = pool.submit(encode, nh)
                            submit_index += 1
                        raw = self.cands[h].raw
                        rec = (
                            B.BHDR.pack(
                                B.BMAGIC,
                                codec,
                                0,
                                0,
                                raw_len,
                                len(comp),
                                len(meta),
                                binascii.crc32(raw) & 0xFFFFFFFF,
                                h,
                            )
                            + meta
                            + comp
                        )
                        href[h] = len(blobs)
                        blobs.append([offset, raw_len, len(comp), codec, len(meta)])
                        spool.write(rec)
                        offset += len(rec)
                        self.cands[h].raw = b""
                        self.cands[h].deflates.clear()
                        consume_index += 1
            else:
                for h in ordered_hashes:
                    h, raw_len, codec, comp, meta = encode(h)
                    raw = self.cands[h].raw
                    rec = (
                        B.BHDR.pack(
                            B.BMAGIC,
                            codec,
                            0,
                            0,
                            raw_len,
                            len(comp),
                            len(meta),
                            binascii.crc32(raw) & 0xFFFFFFFF,
                            h,
                        )
                        + meta
                        + comp
                    )
                    href[h] = len(blobs)
                    blobs.append([offset, raw_len, len(comp), codec, len(meta)])
                    spool.write(rec)
                    offset += len(rec)
                    self.cands[h].raw = b""
                    self.cands[h].deflates.clear()

            def mapref(value):
                return href[bytes(value)]

            files = []
            for row in self.files:
                rel, kind, mode, mtime, size, digest, storage = row
                if storage and storage[0] == B.S_BLOB:
                    storage = [B.S_BLOB, mapref(storage[1])]
                elif storage and storage[0] == B.S_CHUNKS:
                    storage = [B.S_CHUNKS, [mapref(x) for x in storage[1]]]
                elif storage and storage[0] == B.S_CDC:
                    storage = [B.S_CDC, [[length, mapref(x)] for length, x in storage[1]]]
                elif storage and storage[0] == B.S_SPARSE:
                    storage = [
                        B.S_SPARSE,
                        [[data_offset, length, [mapref(x) for x in refs]] for data_offset, length, refs in storage[1]],
                    ]
                elif storage and storage[0] == B.S_PACK:
                    storage = [B.S_PACK, mapref(storage[1]), storage[2], storage[3]]
                keep_hash = digest if storage and storage[0] in (B.S_CHUNKS, B.S_CDC, B.S_SPARSE) else None
                files.append([rel, kind, mode, mtime, size, keep_hash, storage])

            recipes = []
            for skeleton_ref, lengths, payloads, vsha, vsize, vcrc in self.recipes:
                mapped = []
                for rawref, method, stream_hash, csize, level in payloads:
                    rawidx = mapref(rawref)
                    if method == zipfile.ZIP_STORED:
                        mapped.append([rawidx, method, 0, rawidx, csize, -1])
                        continue
                    if bytes(stream_hash) == self.canonical_deflate.get(bytes(rawref)):
                        mapped.append([rawidx, method, 0, rawidx, csize, level])
                    elif bytes(stream_hash) in self.secondary_stream_hashes:
                        mapped.append([rawidx, method, 1, mapref(stream_hash), csize, level])
                    else:
                        mapped.append([rawidx, method, 2, rawidx, csize, level])
                recipes.append([mapref(skeleton_ref), lengths, mapped, vsha, vsize, vcrc])

            owner_counts = {}
            for row in files:
                uid, gid, _ = self.meta_by_rel.get(row[0], (0, 0, {}))
                owner_counts[(uid, gid)] = owner_counts.get((uid, gid), 0) + 1
            common_owner = max(owner_counts, key=owner_counts.get) if owner_counts else (0, 0)
            owner_overrides = []
            xattrs = []
            for index, row in enumerate(files):
                uid, gid, xa = self.meta_by_rel.get(row[0], (*common_owner, {}))
                if (uid, gid) != common_owner:
                    owner_overrides.append([index, uid, gid])
                if xa:
                    xattrs.append([index, [[key, value] for key, value in sorted(xa.items())]])
            fsmeta = {"owner": list(common_owner), "owner_overrides": owner_overrides, "xattrs": xattrs}
            index = {
                "v": B.VERSION,
                "files": files,
                "blobs": blobs,
                "recipes": recipes,
                "dict_blob": mapref(self.dict_hash) if self.dict_hash else None,
                "fsmeta": fsmeta,
                "features": [
                    "micro-solid-packs",
                    "nested-container-packs",
                    "transitive-pack-integrity",
                    "dedup",
                    "hardlinks",
                    "sparse-files",
                    "content-defined-chunking",
                    "chunk-seeking",
                    "parallel-chunks",
                    "zstd",
                    "zstd-dictionary",
                    "wavflac",
                    "deflate-reuse",
                    "virtual-zip-hybrid-recompress",
                    "crc32-fastpath",
                    "sha256",
                    "dual-index",
                    "transaction-journal",
                    "uid-gid",
                    "xattrs",
                ],
            }
            index_raw = msgpack.packb(index, use_bin_type=True)
            index_comp = B.zc(index_raw, 12)
            index_hash = B.sha(index_raw)
            data_bytes = spool.tell()
            header = B.HDR.pack(B.MAGIC, B.VERSION, 0, len(index_comp), len(index_raw), data_bytes, index_hash)
            footer = B.FTR.pack(B.FMAGIC, 0, 1, 0, 0, len(index_comp), len(index_raw), 0, index_hash)
            out = Path(out)
            spool.seek(0)
            with out.open("wb") as handle:
                handle.write(header)
                handle.write(index_comp)
                shutil.copyfileobj(spool, handle, length=1024 * 1024)
                handle.write(index_comp)
                handle.write(footer)

        return {
            "bytes": out.stat().st_size,
            "logical_bytes": sum(row[4] for row in files if row[1] != B.K_DIR),
            "unique_blobs": len(blobs),
            "logical_files": sum(row[1] != B.K_DIR for row in files),
            "recipes": len(recipes),
            "index_raw": len(index_raw),
            "index_comp": len(index_comp),
            "data_bytes": data_bytes,
            "encode_workers": self.encode_workers,
            "reproducible": self.reproducible,
        }


PROMOTION_BOUNDARY = {
    "archive_bytes_changed": False,
    "grammar_changed": False,
    "codec_policy_changed": False,
    "selector_changed": False,
    "release_credit": False,
    "next_gate": "exact r24 + promoted-product identity, RSS and wall-time oracle",
}
