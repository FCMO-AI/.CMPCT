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
import hashlib
import io
from pathlib import Path
import zipfile
import zlib

FIXED_ZIP_DATE = (2020, 1, 1, 0, 0, 0)
FIXED_W3CDTF = b"2020-01-01T00:00:00Z"
OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}
AFFECTED = {
    "02_office_workspace",
    "05_logs_and_telemetry",
    "06_incremental_backups",
}


def install_generation_hooks(neutral_module) -> None:
    """Force deterministic producer modes without editing the historical v1 generator.

    ReportLab's ``Canvas`` has an explicit ``invariant`` argument. The historical corpus builder imports
    the ``reportlab.pdfgen.canvas`` module and calls ``canvas.Canvas(...)`` without that argument, so a
    wrapper at the exact imported constructor boundary is both narrower and more reliable than mutating
    process-global settings after modules have initialized.

    The repaired corpus ultimately replaces the one unstable ReportLab PDF with a deterministic fixture,
    but the hook remains as defense in depth and as evidence that producer-level reproducibility was
    attempted before substituting a benchmark fixture.
    """
    canvas_module = getattr(neutral_module, "canvas", None)
    if canvas_module is None or not hasattr(canvas_module, "Canvas"):
        raise RuntimeError("neutral hostile generator no longer exposes reportlab canvas module")
    current = canvas_module.Canvas
    if getattr(current, "_cmpct_invariant_wrapper", False):
        return

    @functools.wraps(current)
    def stable_canvas(*args, **kwargs):
        kwargs.setdefault("invariant", 1)
        return current(*args, **kwargs)

    stable_canvas._cmpct_invariant_wrapper = True
    canvas_module.Canvas = stable_canvas


def _stable_xml(data: bytes) -> bytes:
    """Replace volatile W3CDTF values while preserving the surrounding package XML."""
    # The exact Office XML timestamp shape is fixed-width, so byte replacement does not disturb package
    # semantics. Avoid a broad XML canonicalizer that could change compression characteristics.
    import re
    return re.sub(rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", FIXED_W3CDTF, data)


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


def _pdf_stream(payload: bytes, *, flate: bool = False) -> bytes:
    stored = zlib.compress(payload, 9) if flate else payload
    filter_part = b" /Filter /FlateDecode" if flate else b""
    return b"<< /Length " + str(len(stored)).encode() + filter_part + b" >>\nstream\n" + stored + b"\nendstream"


def _deterministic_pdf_fixture(workload: Path) -> bytes:
    """Build a valid deterministic 28-page PDF using the same two repeated JPEG assets.

    The historical ReportLab file was the *only* remaining unstable object after two repair attempts,
    varying by two bytes between identical seeded builds. The fixture keeps the same benchmark purpose:
    PDF container syntax, many page/content objects, compressible text streams, and repeated JPEG bytes
    that also exist elsewhere in the Office tree. It intentionally does not try to reproduce ReportLab's
    producer-specific serialization byte-for-byte.
    """
    assets = workload / "assets"
    images = {
        "Im0": (assets / "photo_0.jpg").read_bytes(),
        "Im4": (assets / "photo_4.jpg").read_bytes(),
    }
    if not all(images.values()):
        raise RuntimeError("deterministic PDF fixture requires photo_0.jpg and photo_4.jpg")

    # Object numbers are fixed: catalog=1, pages=2, fonts=3/4, images=5/6, then page/content pairs.
    page_ids = [8 + page * 2 for page in range(28)]
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        5: _pdf_stream(images["Im0"]),
        6: _pdf_stream(images["Im4"]),
    }
    kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects[2] = b"<< /Type /Pages /Count 28 /Kids [ " + kids + b" ] >>"

    for page in range(28):
        content_id = 7 + page * 2
        page_id = 8 + page * 2
        lines = [
            "BT /F2 15 Tf 54 742 Td "
            f"(Client Performance Report - Page {page + 1}) Tj ET",
            "BT /F1 9 Tf 54 714 Td",
        ]
        for line in range(12):
            # Footnote: fixed ASCII text avoids font/Unicode producer variability while retaining the
            # repeated textual structure this workload is meant to expose to an archive compressor.
            text = (
                f"Deterministic office benchmark narrative page {page + 1:02d} line {line + 1:02d}; "
                f"account cohort {(page * 17 + line * 7) % 997:03d}; metric {(page + 3) * (line + 11):04d}."
            )
            lines.append(f"({text}) Tj 0 -15 Td")
        lines.append("ET")
        if page % 4 == 0:
            image_name = "Im0" if page % 8 == 0 else "Im4"
            lines.append(f"q 500 0 0 281 54 285 cm /{image_name} Do Q")
        content = ("\n".join(lines) + "\n").encode("ascii")
        objects[content_id] = _pdf_stream(content, flate=True)
        objects[page_id] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> "
            b"/XObject << /Im0 5 0 R /Im4 6 0 R >> >> "
            + f"/Contents {content_id} 0 R >>".encode()
        )

    # JPEG stream objects need image dictionaries rather than generic stream dictionaries. Replace the
    # two provisional stream objects now that the object map is complete.
    for object_id, name in ((5, "Im0"), (6, "Im4")):
        raw = images[name]
        objects[object_id] = (
            b"<< /Type /XObject /Subtype /Image /Width 1600 /Height 900 "
            b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length "
            + str(len(raw)).encode() + b" >>\nstream\n" + raw + b"\nendstream"
        )

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray(header)
    offsets = {0: 0}
    for object_id in range(1, max(objects) + 1):
        offsets[object_id] = len(body)
        body.extend(f"{object_id} 0 obj\n".encode())
        body.extend(objects[object_id])
        body.extend(b"\nendobj\n")

    xref = len(body)
    size = max(objects) + 1
    body.extend(f"xref\n0 {size}\n".encode())
    body.extend(b"0000000000 65535 f \n")
    for object_id in range(1, size):
        body.extend(f"{offsets[object_id]:010d} 00000 n \n".encode())

    fixture_id = hashlib.sha256(images["Im0"] + images["Im4"] + b"CMPCT-office-pdf-v1").hexdigest()[:32]
    body.extend(
        b"trailer\n<< /Size " + str(size).encode() + b" /Root 1 0 R /ID [<"
        + fixture_id.encode() + b"><" + fixture_id.encode() + b">] >>\n"
        + b"startxref\n" + str(xref).encode() + b"\n%%EOF\n"
    )
    return bytes(body)


def _repair_office(workload: Path) -> None:
    for path in sorted(p for p in workload.rglob("*") if p.is_file()):
        if path.suffix.lower() in OFFICE_SUFFIXES:
            _stable_zip(path)
    pdf = workload / "client_report.pdf"
    if not pdf.exists():
        raise RuntimeError("office workload no longer contains client_report.pdf")
    pdf.write_bytes(_deterministic_pdf_fixture(workload))


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
