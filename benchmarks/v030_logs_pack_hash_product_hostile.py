from __future__ import annotations

import binascii
import json
from pathlib import Path
import tempfile

import zstandard as zstd

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_logs_fused_extract as F
from experiments import entropygraph_v030_release_product as PRODUCT


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-product-hostile-") as td:
        root = Path(td)
        src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "05_logs_and_telemetry")]
        archive = root / "logs.cmpct"
        PRODUCT.build(src, archive)
        with F._FusedExtractionArchive(archive) as reader:
            covered = set(reader._fused_member_owned_packs)
            all_packs = set(range(len(reader.pack_offsets)))
            if covered != all_packs:
                raise RuntimeError(f"writer archive not fully owned: {covered} != {all_packs}")

        base = F._FusedExtractionArchive
        class PostCrcFault(base):
            def __init__(self, path: Path):
                super().__init__(path)
                self._faulted = False
            def _read_pack(self, index: int) -> bytes:
                if index not in self._fused_member_owned_packs:
                    return super()._read_pack(index)
                offset, codec, usize, csize, crc, _sha = self.pack_offsets[index]
                self.handle.seek(offset)
                payload = self.handle.read(csize)
                raw = payload if codec == F.LOGS.V2.P.CODEC_RAW else zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
                if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                    raise RuntimeError("logs profile pack identity")
                if not self._faulted and raw:
                    damaged = bytearray(raw); damaged[0] ^= 1; raw = bytes(damaged); self._faulted = True
                return raw

        old = F._FusedExtractionArchive
        dst = root / "must-not-publish"
        rejected = False
        F._FusedExtractionArchive = PostCrcFault
        try:
            try:
                PRODUCT.extract(archive, dst)
            except RuntimeError as exc:
                rejected = "logical identity" in str(exc)
        finally:
            F._FusedExtractionArchive = old
        if not rejected or dst.exists():
            raise RuntimeError(f"post-CRC product fault escaped: rejected={rejected}, published={dst.exists()}")

        # Strict reader remains a distinct class and must still reject a pack-SHA-only metadata fault.
        if F._FusedExtractionArchive is F.LOGS.Archive:
            raise RuntimeError("fused scoped reader unexpectedly aliases strict reader")
        return {
            "schema":"cmpct-v030-logs-pack-hash-product-hostile-v1",
            "release_credit":False,
            "covered_packs":sorted(covered),
            "pack_count":len(all_packs),
            "post_crc_member_sha_rejected":rejected,
            "transaction_published":dst.exists(),
            "strict_reader_distinct":True,
            "result":"PASS",
        }

if __name__ == "__main__":
    result=run()
    out=Path("benchmark-artifacts/v030-logs-pack-hash-product-hostile.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
