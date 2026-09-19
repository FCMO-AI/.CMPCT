from __future__ import annotations

"""Hostile/scope proof for the Logs pack-hash ownership research seed.

This does not alter product code.  It proves the proposed admission predicate rejects
malformed ownership and that corruption after the retained pack CRC is still rejected by
an owning logical-member SHA before transactional publication.
"""

import binascii
import copy
import json
from pathlib import Path
import shutil
import tempfile

import zstandard as zstd

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_logs_fused_extract as F
from experiments import entropygraph_v030_release_product as PRODUCT


def covered_packs(files: list, pack_offsets: list[tuple]) -> set[int]:
    intervals: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(pack_offsets))}
    for row in files:
        size = int(row[2])
        storage = row[4]
        if storage[0] not in ("pack", "raw"):
            continue
        pack_id, offset, length = map(int, storage[1:])
        if pack_id < 0 or pack_id >= len(pack_offsets) or offset < 0 or length != size:
            continue
        intervals[pack_id].append((offset, offset + length))
    covered: set[int] = set()
    for pack_id, pack_row in enumerate(pack_offsets):
        usize = int(pack_row[2])
        spans = sorted(intervals[pack_id])
        cursor = 0
        valid = bool(spans)
        for start, end in spans:
            if start != cursor or end < start or end > usize:
                valid = False
                break
            cursor = end
        if valid and cursor == usize:
            covered.add(pack_id)
    return covered


def _mutated_rows(files: list, mode: str) -> tuple[list, int]:
    rows = copy.deepcopy(files)
    direct = [(i, r) for i, r in enumerate(rows) if r[4][0] in ("pack", "raw")]
    if not direct:
        raise RuntimeError("no direct rows")
    if mode == "gap":
        i, row = direct[0]
        pack_id = int(row[4][1])
        row[4][2] = int(row[4][2]) + 1
        return rows, pack_id
    if mode == "out-of-bounds":
        i, row = direct[0]
        pack_id = int(row[4][1])
        row[4][3] = int(row[4][3]) + 1
        return rows, pack_id
    if mode == "overlap":
        by_pack: dict[int, list] = {}
        for _i, row in direct:
            by_pack.setdefault(int(row[4][1]), []).append(row)
        for pack_id, members in by_pack.items():
            members.sort(key=lambda r: int(r[4][2]))
            if len(members) >= 2 and int(members[1][4][2]) > 0:
                members[1][4][2] = int(members[1][4][2]) - 1
                return rows, pack_id
        # A one-owner pack can still be made overlapping/overlong; admission must reject it.
        _i, row = direct[0]
        pack_id = int(row[4][1])
        row[4][3] = int(row[4][3]) + 1
        return rows, pack_id
    raise ValueError(mode)


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-pack-owner-hostile-") as td:
        root = Path(td)
        src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "05_logs_and_telemetry")]
        archive = root / "logs.cmpct"
        stats = PRODUCT.build(src, archive)
        if not stats.get("logs_terminal"):
            raise RuntimeError("frozen Logs workload did not select logs terminal")

        with F.LOGS.Archive(archive) as reader:
            baseline = covered_packs(reader.files, reader.pack_offsets)
            all_packs = set(range(len(reader.pack_offsets)))
            if baseline != all_packs:
                raise RuntimeError("writer-produced archive lacks exact pack ownership")
            malformed = {}
            for mode in ("gap", "overlap", "out-of-bounds"):
                rows, target = _mutated_rows(reader.files, mode)
                admitted = covered_packs(rows, reader.pack_offsets)
                malformed[mode] = {"target_pack": target, "still_admitted": target in admitted}
                if target in admitted:
                    raise RuntimeError(f"{mode} ownership was admitted")

        base = F.LOGS.Archive
        corruption_observed = {"member_sha_rejected": False, "published": False}

        class PostCrcCorruptArchive(base):
            def __init__(self, path: Path):
                super().__init__(path)
                self._covered = covered_packs(self.files, self.pack_offsets)
                self._flipped = False

            def _read_pack(self, index: int) -> bytes:
                if index not in self._covered:
                    return super()._read_pack(index)
                offset, codec, usize, csize, crc, _sha = self.pack_offsets[index]
                self.handle.seek(offset)
                payload = self.handle.read(csize)
                if len(payload) != csize:
                    raise RuntimeError("short logs profile pack")
                raw = payload if codec == F.LOGS.V2.P.CODEC_RAW else zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
                if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                    raise RuntimeError("logs profile pack identity")
                # Fault is deliberately injected *after* the retained CRC proof.  If pack SHA
                # ownership is sound, an authenticated direct-member SHA must still catch it.
                if not self._flipped and raw:
                    damaged = bytearray(raw)
                    damaged[0] ^= 0x01
                    raw = bytes(damaged)
                    self._flipped = True
                return raw

        original = F.LOGS.Archive
        dst = root / "must-not-publish"
        F.LOGS.Archive = PostCrcCorruptArchive
        try:
            try:
                PRODUCT.extract(archive, dst)
            except RuntimeError as exc:
                corruption_observed["member_sha_rejected"] = "logical identity" in str(exc)
            corruption_observed["published"] = dst.exists()
        finally:
            F.LOGS.Archive = original
        if not corruption_observed["member_sha_rejected"] or corruption_observed["published"]:
            raise RuntimeError(f"post-CRC corruption proof failed: {corruption_observed}")

        # Strict surfaces remain on the unmodified reader class and therefore still execute pack SHA.
        with F.LOGS.Archive(archive) as reader:
            strict_pack_sha_present = all(isinstance(row[5], bytes) and len(row[5]) == 32 for row in reader.pack_offsets)
        if not strict_pack_sha_present:
            raise RuntimeError("strict reader lost pack SHA")

        return {
            "schema": "cmpct-v030-logs-pack-hash-ownership-hostile-v1",
            "release_credit": False,
            "baseline_covered_packs": sorted(baseline),
            "pack_count": len(all_packs),
            "malformed_partition_rejection": malformed,
            "post_crc_corruption": corruption_observed,
            "strict_reader_pack_sha_present": strict_pack_sha_present,
            "result": "PASS",
        }


if __name__ == "__main__":
    result = run()
    out = Path("benchmark-artifacts/v030-logs-pack-hash-ownership-hostile.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
