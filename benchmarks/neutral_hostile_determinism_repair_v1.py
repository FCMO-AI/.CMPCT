from __future__ import annotations

"""Minimal determinism repair for three historical neutral/hostile v1 workloads.

The v0.29 generalization tranche exposed producer metadata that can drift even when the synthetic payload
PRNG is seeded.  This layer keeps the historical workload generators intact and normalizes only container
metadata whose value is unrelated to compression policy: Office ZIP timestamps/core dates, ReportLab PDF
dates/document IDs, gzip mtime, and nested-backup ZIP metadata.

Footnote: an earlier research attempt replaced ``client_report.pdf`` with a hand-built deterministic PDF.
That made the proof green but changed the Office v0.28 baseline by roughly thirteen percent, which is far
too invasive for a benchmark-substrate repair.  The replacement was therefore rejected.  The accepted
repair must preserve the historical ReportLab content and only canonicalize producer metadata in place.
"""

import gzip
import io
from pathlib import Path
import re
import zipfile

FIXED_ZIP_DATE = (2020, 1, 1, 0, 0, 0)
FIXED_W3CDTF = b"2020-01-01T00:00:00Z"
OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}
AFFECTED = {
    "02_office_workspace",
    "05_logs_and_telemetry",
    "06_incremental_backups",
}

_W3CDTF_RE = re.compile(rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
_PDF_DATE_RE = re.compile(rb"D:\d{14}(?:[+\-Z']\d{0,4}'?)?")
_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\]")


def _stable_xml(data: bytes) -> bytes:
    """Replace volatile Office core timestamps without changing XML structure."""
    return _W3CDTF_RE.sub(FIXED_W3CDTF, data)


def _stable_pdf(path: Path) -> None:
    """Canonicalize only fixed-width ReportLab date/ID metadata in place.

    Footnote: ReportLab also derives XObject resource names from image source paths.  That is not producer
    nondeterminism and must not be rewritten here.  The two-pass proof therefore regenerates at the same
    absolute workspace path; this function handles only metadata that can genuinely vary at that path.
    Length preservation keeps the already-written xref offsets valid.
    """
    data = path.read_bytes()

    def date_repl(match: re.Match[bytes]) -> bytes:
        raw = match.group(0)
        fixed = b"D:20000101000000Z"
        return (fixed + b"0" * len(raw))[: len(raw)]

    def id_repl(match: re.Match[bytes]) -> bytes:
        raw = match.group(0)
        left = b"0" * len(match.group(1))
        right = b"0" * len(match.group(2))
        rebuilt = b"/ID [<" + left + b"><" + right + b">]"
        return (rebuilt + b" " * len(raw))[: len(raw)]

    data = _PDF_DATE_RE.sub(date_repl, data)
    data = _PDF_ID_RE.sub(id_repl, data)
    path.write_bytes(data)


def _stable_zip(path: Path) -> None:
    """Rewrite a ZIP-family container with fixed member metadata and deterministic ordering."""
    with zipfile.ZipFile(path, "r") as source:
        rows = [(info, source.read(info.filename)) for info in source.infolist()]

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", allowZip64=True) as target:
        for info, payload in sorted(rows, key=lambda row: row[0].filename):
            if info.filename == "docProps/core.xml":
                payload = _stable_xml(payload)
            stable = zipfile.ZipInfo(info.filename, date_time=FIXED_ZIP_DATE)
            stable.compress_type = info.compress_type
            stable.create_system = 3
            stable.external_attr = info.external_attr
            stable.internal_attr = info.internal_attr
            stable.flag_bits = info.flag_bits & 0x800
            stable.comment = b""
            stable.extra = b""
            if info.compress_type == zipfile.ZIP_DEFLATED:
                target.writestr(stable, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            else:
                target.writestr(stable, payload, compress_type=info.compress_type)
    path.write_bytes(out.getvalue())


def _repair_office(workload: Path) -> None:
    for path in sorted(p for p in workload.rglob("*") if p.is_file()):
        suffix = path.suffix.lower()
        if suffix in OFFICE_SUFFIXES:
            _stable_zip(path)
        elif suffix == ".pdf":
            _stable_pdf(path)


def _repair_logs(workload: Path) -> None:
    for gz_path in sorted(workload.glob("*.log.gz")):
        raw_path = workload / gz_path.name[:-3]
        if not raw_path.exists():
            raise RuntimeError(f"missing deterministic gzip source for {gz_path.name}")
        # Footnote: gzip.compress defaults to wall-clock mtime.  mtime=0 changes only the member header;
        # the compressed payload and benchmark semantics are otherwise identical.
        gz_path.write_bytes(gzip.compress(raw_path.read_bytes(), compresslevel=6, mtime=0))


def _repair_backups(workload: Path) -> None:
    nested = workload / "snapshot_2.zip"
    if nested.exists():
        _stable_zip(nested)


def normalize_workload(workload: Path) -> None:
    if workload.name not in AFFECTED:
        return
    if workload.name == "02_office_workspace":
        _repair_office(workload)
    elif workload.name == "05_logs_and_telemetry":
        _repair_logs(workload)
    elif workload.name == "06_incremental_backups":
        _repair_backups(workload)


def normalize_root(root: Path) -> None:
    for name in sorted(AFFECTED):
        path = root / name
        if path.exists():
            normalize_workload(path)
