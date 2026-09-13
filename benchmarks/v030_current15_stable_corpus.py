from __future__ import annotations

"""Deterministic current15 corpus substrate for v0.30 research.

Mission lock
============
The current15 fingerprint referee found immediate back-to-back byte drift in exactly
three neutral workloads: office, logs/telemetry and incremental backups.  The data
recipes are deterministic; the exported container bytes were not, because wall-clock
metadata entered OOXML/PDF/ZIP/GZIP containers.

This module does not alter workload payload semantics, corpus membership, benchmark
thresholds or product policy.  It runs the existing neutral/hostile producer under a
fixed reproducible-build clock, canonicalizes only volatile container timestamps, and
then recomputes the producer manifest.  The acceptance test is byte-level: two
consecutive current15 builds on one exact runner must have identical per-workload tree
SHA-256 values and therefore an identical portfolio fingerprint.

Research substrate only.  Once independently reproduced, the normalization can be
folded into the shared public corpus producer rather than remaining a v0.30 wrapper.
"""

import gzip
import json
import os
from pathlib import Path
import re
import zipfile

from benchmarks import neutral_hostile_corpus_v1 as BASE

_FIXED_EPOCH = "1735689600"  # 2025-01-01T00:00:00Z
_FIXED_ISO = "2025-01-01T00:00:00Z"
_FIXED_ZIP_TIME = (2025, 1, 1, 0, 0, 0)
_W3CDTF = re.compile(
    rb"(<dcterms:(?:created|modified)\b[^>]*>)[^<]*(</dcterms:(?:created|modified)>)"
)


def _normalize_zip_container(path: Path) -> None:
    """Rewrite one generated ZIP-family container with a fixed DOS timestamp.

    OOXML core properties are also normalized because python-docx/openpyxl/python-pptx
    may serialize the construction clock inside docProps/core.xml even after ZIP entry
    timestamps are fixed.  No user payload member is added, removed or renamed.
    """
    with zipfile.ZipFile(path, "r") as src:
        comment = src.comment
        entries = []
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = _W3CDTF.sub(
                    lambda m: m.group(1) + _FIXED_ISO.encode("ascii") + m.group(2), data
                )
            entries.append((info, data))

    tmp = path.with_name(path.name + ".deterministic-tmp")
    try:
        with zipfile.ZipFile(tmp, "w") as dst:
            dst.comment = comment
            for old, data in entries:
                info = zipfile.ZipInfo(old.filename, _FIXED_ZIP_TIME)
                info.compress_type = old.compress_type
                info.comment = old.comment
                # Extended timestamp fields can themselves carry wall-clock values.  The
                # benchmark contract needs content semantics, not host filesystem times.
                info.extra = b""
                info.internal_attr = old.internal_attr
                info.external_attr = old.external_attr
                info.create_system = old.create_system
                info.flag_bits = old.flag_bits & 0x800  # retain UTF-8 filename intent only
                kwargs = {"compress_type": old.compress_type}
                if old.compress_type == zipfile.ZIP_DEFLATED:
                    kwargs["compresslevel"] = 6
                dst.writestr(info, data, **kwargs)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _normalize_neutral(root: Path) -> None:
    office = root / "02_office_workspace"
    for suffix in ("*.docx", "*.xlsx", "*.pptx"):
        for path in sorted(office.glob(suffix)):
            _normalize_zip_container(path)

    logs = root / "05_logs_and_telemetry"
    for path in sorted(logs.glob("*.gz")):
        raw = gzip.decompress(path.read_bytes())
        path.write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))

    backup = root / "06_incremental_backups" / "snapshot_2.zip"
    if backup.exists():
        _normalize_zip_container(backup)


def _rebuild_manifest(root: Path, manifest: dict) -> dict:
    corpora = []
    for directory in sorted(x for x in root.iterdir() if x.is_dir()):
        files = [p for p in directory.rglob("*") if p.is_file()]
        corpora.append(
            {
                "name": directory.name,
                "files": len(files),
                "logical_bytes": sum(p.stat().st_size for p in files),
                "tree_sha256": BASE.tree_hash(directory),
            }
        )
    out = dict(manifest)
    out["generated_utc"] = _FIXED_ISO
    out["corpora"] = corpora
    out["reproducibility_note"] = (
        "Current15 deterministic substrate: workload PRNG streams are fixed and volatile "
        "OOXML/PDF/ZIP/GZIP wall-clock metadata is normalized before tree hashing."
    )
    (root / "MANIFEST.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def build(root: Path) -> dict:
    previous_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = _FIXED_EPOCH

    # ReportLab's PDFDocument derives CreationDate/ModDate and the document ID from
    # the wall clock unless invariant mode is enabled.  Setting the global config was
    # insufficient on hosted CI: file-level attribution still isolated client_report.pdf.
    # Force the invariant argument at the exact Canvas constructor used by the shared
    # corpus producer, then restore both the constructor and global config afterwards.
    try:
        from reportlab import rl_config
        previous_invariant = rl_config.invariant
        rl_config.invariant = 1
    except Exception:
        rl_config = None
        previous_invariant = None

    original_canvas = BASE.canvas.Canvas

    def deterministic_canvas(*args, **kwargs):
        kwargs["invariant"] = 1
        return original_canvas(*args, **kwargs)

    BASE.canvas.Canvas = deterministic_canvas
    try:
        manifest = BASE.build(root)
    finally:
        BASE.canvas.Canvas = original_canvas
        if rl_config is not None:
            rl_config.invariant = previous_invariant
        if previous_epoch is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous_epoch

    _normalize_neutral(root)
    return _rebuild_manifest(root, manifest)
