"""Research-only zero-copy C25CC01 extraction over the mature r24 semantic owner.

The direct C25 extractor removes compatibility-r24 materialization, but its ordinary parser still reads the whole
archive into a bytes object and slices the complete physical payload into a second bytes object.  This experiment
keeps the archive mapped read-only, authenticates/expands the exact same compact control, and exposes the unchanged
physical payload to the mature r24 reader through a zero-copy memoryview.  It changes neither archive bytes nor
selector policy and grants no release credit until exact-output/error and timing evidence are complete.
"""
from __future__ import annotations

from contextlib import contextmanager
import mmap
from pathlib import Path
import shutil
import tempfile

from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


@contextmanager
def _mapped_parse(archive: Path):
    archive = Path(archive)
    with archive.open("rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        data_view = None
        try:
            if len(mm) < R24.HDR.size + R24.FTR.size:
                raise CC.CompactControlError("truncated compact-control archive")
            magic, version, _flags, primary_cbytes, raw_bytes, data_bytes, primary_sha = R24.HDR.unpack_from(mm, 0)
            if magic != CC.MAGIC or int(version) != CC.REVISION:
                raise CC.CompactControlError("not C25CC01")

            footer_off = len(mm) - R24.FTR.size
            fmagic, _a, _b, _c, _d, tail_cbytes, tail_raw_bytes, _reserved, tail_sha = R24.FTR.unpack_from(mm, footer_off)
            if fmagic != CC.TAIL_MAGIC:
                raise CC.CompactControlError("compact-control tail magic mismatch")
            primary_start = R24.HDR.size
            primary_end = primary_start + int(primary_cbytes)
            tail_start = footer_off - int(tail_cbytes)
            if primary_end + int(data_bytes) != tail_start:
                raise CC.CompactControlError("compact-control physical span accounting mismatch")

            # Control copies are small bounded metadata.  Copying one of them is intentional; the eliminated copy is
            # the potentially multi-megabyte physical payload span.
            primary = mm[primary_start:primary_end]
            tail = mm[tail_start:footer_off]
            try:
                decoded = CC._read_control_copy(primary, int(raw_bytes), primary_sha)
                recovery = "primary"
                control_raw_bytes = int(raw_bytes)
            except Exception:
                decoded = CC._read_control_copy(tail, int(tail_raw_bytes), tail_sha)
                recovery = "tail"
                control_raw_bytes = int(tail_raw_bytes)

            compact = decoded["c"]
            index = CC.CONTROL._expand_index(compact, version=R24.VERSION, features=list(decoded["x"]))
            if CC.CONTROL._expand_index(
                CC.CONTROL._compact_index(index), version=R24.VERSION, features=list(index["features"])
            ) != index:
                raise CC.CompactControlError("compact-control semantic expansion is not stable")

            data_view = memoryview(mm)[primary_end:tail_start]
            yield {
                "index": index,
                "data": data_view,
                "recovery_source": recovery,
                "primary_control_bytes": int(primary_cbytes),
                "tail_control_bytes": int(tail_cbytes),
                "control_raw_bytes": control_raw_bytes,
                "archive_bytes": len(mm),
                "archive_mapping": True,
                "physical_payload_copy": False,
            }
        finally:
            if data_view is not None:
                data_view.release()
            mm.close()


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = PRODUCT.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    dst = Path(dst)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    with _mapped_parse(archive) as parsed:
        CC._audit_s_pack_locality(parsed["index"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-c25-mmap-", dir=dst.parent))
        installed = False
        try:
            with CC._direct_r24_reader(parsed) as reader:
                reader.extractall(staging, max_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
            PRODUCT._BASE_IMPL.C._publish_tree(staging, dst)
            installed = True
        finally:
            if not installed and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
