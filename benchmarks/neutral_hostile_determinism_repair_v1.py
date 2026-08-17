from __future__ import annotations

"""Determinism repair layer for three historical neutral/hostile v1 workloads.

The original v1 generator correctly seeded synthetic *payload* randomness, but several real container
libraries also embed wall-clock metadata that the payload PRNG cannot control. The v0.29 generalization
tranche exposed that hidden substrate defect as three drifting tree hashes and six aggregate baseline
bytes.

This module deliberately leaves the historical generator and v0.28 evidence untouched. It normalizes
only the unstable metadata after generation, producing a new deterministic benchmark substrate whose
identity must be captured in a separate repair manifest before it can replace the old rows in a gate.

Footnote: normalization is not compression policy. Both v0.28 and every candidate consume the exact
same repaired tree. A repair is accepted only after two independent regenerations produce identical tree
hashes, so a new timestamp bug cannot quietly become a compression 'improvement'.
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
    """Force deterministic producer modes without editing the historical v1 generator.

    ReportLab's ``Canvas`` has an explicit ``invariant`` argument. The historical corpus builder imports
    the ``reportlab.pdfgen.canvas`` module and calls ``canvas.Canvas(...)`` without that argument, so a
    wrapper at the exact imported constructor boundary is both narrower and more reliable than mutating
    process-global settings after modules have initialized.
    """
    canvas_module = getattr(neutral_module, "canvas", None)
    if canvas_module is None or not hasattr(canvas_module, "Canvas"):
        raise RuntimeError("neutral hostile generator no longer exposes reportlab canvas module")
    current = canvas_module.Canvas
    if getattr(current, "_cmpct_invariant_wrapper", False):
        return

    @functools.wraps(current)
    def stable_canvas(*args, **kwargs):
        # Footnote: ``setdefault`` respects an explicit future corpus choice while making the historical
        # no-argument call reproducible. It does not alter page contents, compression, or layout policy.
        kwargs.setdefault("invariant", 1)
        return current(*args, **kwargs)

    stable_canvas._cmpct_invariant_wrapper = True
    canvas_module.Canvas = stable_canvas


def _stable_xml(data: bytes) -> bytes:
    """Replace volatile W3CDTF values while preserving the surrounding package XML."""
    return _W3CDTF_RE.sub(FIXED_W3CDTF, data)


def _stable_pdf(path: Path) -> None:
    """Normalize residual ReportLab date/ID fields in-place without shifting xref offsets.

    Invariant generation is the primary fix. This pass remains as defense in depth in case a producer
    revision retains deterministic-but-environment-specific metadata fields outside its invariant mode.
    """
    data = path.read_bytes()

    def date_repl(match: re.Match[bytes]) -> bytes:
        template = b"D:20000101000000Z"
        raw = match.group(0)
        return (template + b"0" * len(raw))[: len(raw)]

    def id_repl(match: re.Match[bytes]) -> bytes:
        left = b"0" * len(match.group(1))
        right = b"0" * len(match.group(2))
        raw = match.group(0)
        rebuilt = b"/ID [<" + left + b"><" + right + b">]"
        # PDF whitespace is semantically insignificant outside streams; length preservation keeps the
        # already-written cross-reference offsets valid.
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
        # gzip.compress defaults to wall-clock mtime. mtime=0 fixes the member header while preserving
        # the workload's actual compressed-data shape.
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
