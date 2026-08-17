from __future__ import annotations

"""Minimal deterministic substrate repair for three neutral/hostile v1 workloads.

The repair keeps historical logical content intact while removing producer identity that is unrelated to
compression policy: Office ZIP timestamps/core dates, ReportLab PDF dates/document IDs, ReportLab image
resource names derived from absolute filenames, gzip mtime, and nested-backup ZIP metadata.

Footnote: two earlier repair attempts are intentionally superseded rather than hidden.  Replacing the PDF
with a custom fixture moved the Office v0.28 baseline by ~13% and was rejected.  Testing two builds at one
absolute path proved local repeatability but not portable benchmark identity.  This version makes only the
ReportLab XObject *name source* content-derived, then requires equality across different work directories.
"""

import functools
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


def install_generation_hooks(neutral_module) -> None:
    """Make ReportLab embedded-image resource identity independent of the temporary corpus path.

    ``Canvas.drawImage`` hashes a filename when given a filename.  The corpus uses identical deterministic
    JPEG bytes in every regeneration, but different CI/work roots therefore produce different
    ``FormXob.<digest>`` names and consequently different compressed page streams.  Passing an
    ``ImageReader`` instead makes ReportLab derive the resource identity from image content.

    Footnote: the image bytes, dimensions, placement, page text, PDF grammar and compression settings are
    unchanged.  Only the internal resource-name input changes from an absolute path to the same bytes the
    PDF already embeds.  Date and trailer-ID metadata are still canonicalized post-generation below.
    """
    canvas_module = getattr(neutral_module, "canvas", None)
    if canvas_module is None or not hasattr(canvas_module, "Canvas"):
        raise RuntimeError("neutral hostile generator no longer exposes reportlab canvas module")

    current = canvas_module.Canvas.drawImage
    if getattr(current, "_cmpct_content_identity_wrapper", False):
        return

    from reportlab.lib.utils import ImageReader

    @functools.wraps(current)
    def stable_draw_image(self, image, *args, **kwargs):
        if isinstance(image, (str, Path)):
            image = ImageReader(str(image))
        return current(self, image, *args, **kwargs)

    stable_draw_image._cmpct_content_identity_wrapper = True
    canvas_module.Canvas.drawImage = stable_draw_image


def _stable_xml(data: bytes) -> bytes:
    return _W3CDTF_RE.sub(FIXED_W3CDTF, data)


def _stable_pdf(path: Path) -> None:
    """Canonicalize only fixed-width ReportLab date/ID metadata in place."""
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
        # Footnote: length preservation leaves the existing xref offsets valid.
        return (rebuilt + b" " * len(raw))[: len(raw)]

    data = _PDF_DATE_RE.sub(date_repl, data)
    data = _PDF_ID_RE.sub(id_repl, data)
    path.write_bytes(data)


def _stable_zip(path: Path) -> None:
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
