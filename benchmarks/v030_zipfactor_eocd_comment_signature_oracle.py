from __future__ import annotations

"""Valid-generalization guard for EOCD signatures embedded in legal ZIP comments.

ZIP comments are arbitrary bytes, so an EOCD-first parser may not treat the last EOCD signature
byte sequence as authoritative without validating the complete topology. These fixtures are
independent of the frozen corpus and must remain exact against the mature parser.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

from experiments import entropygraph_v030_zipfactor_eocd_parser as CANDIDATE
from experiments import entropygraph_v030_zipfactor_profile as MATURE

EOCD_HDR = struct.Struct("<IHHHHIIH")


def _zip(comment: bytes, *, count: int = 2) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for i in range(count):
            info = zipfile.ZipInfo(f"member-{i}.txt", date_time=(2024, 2, 3 + i, 4, 5, 6))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.extra = b"\x99\x99\x02\x00OK"
            info.comment = f"row-{i}".encode()
            zf.writestr(info, (f"payload-{i}\n" * (17 + i)).encode())
        zf.comment = comment
    return bio.getvalue()


def _fixtures() -> list[tuple[str, bytes]]:
    # The second case deliberately gives the false signature enough trailing bytes to look like
    # a header candidate. The declared values are nonsense for the actual topology and must be
    # rejected before the search continues to the real EOCD.
    fake_header = EOCD_HDR.pack(0x06054B50, 0, 0, 1, 1, 0, 0, 4) + b"TAIL"
    return [
        ("comment-signature-middle", _zip(b"prefix-PK\x05\x06-suffix")),
        ("comment-signature-tail", _zip(b"arbitrary-comment-PK\x05\x06")),
        ("comment-fake-eocd-header", _zip(b"prefix-" + fake_header)),
        ("comment-two-signatures", _zip(b"PK\x05\x06-middle-PK\x05\x06-end", count=5)),
    ]


def run() -> dict:
    rows = []
    for name, raw in _fixtures():
        mature = MATURE._parse_zip(raw)
        candidate = CANDIDATE.parse_zip(raw)
        exact = mature is not None and candidate == mature
        rows.append({
            "case": name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "mature_accept": mature is not None,
            "candidate_accept": candidate is not None,
            "semantic_exact": exact,
        })
    passed = bool(rows) and all(row["semantic_exact"] for row in rows)
    return {
        "schema": "cmpct-v030-zipfactor-eocd-comment-signature-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "frozen_workload_dependency": False,
            "valid_zip_comments_are_arbitrary_bytes": True,
            "mature_acceptance_requires_candidate_exactness": True,
        },
        "cases": rows,
        "gate": {"valid_generalization_exact": passed, "passed": passed},
        "claim_boundary": "Targeted valid-parser regression guard only; it does not replace hostile fuzz, recovery, native/Android or final authority.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-comment-signature.json"))
    a = p.parse_args()
    result = run()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": result["cases"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("EOCD comment-signature valid-generalization gate failed")


if __name__ == "__main__":
    main()
