"""O215 hostile-wire baseline causal probe; never substitutes for corrected-product tests.

Must execute from an independently installed exact O214 #564 source, not candidate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive
from test_o215_fixed_chunk_admission import _make_archive, PATH

def main():
    with tempfile.TemporaryDirectory(prefix="o215-parent-") as d:
        path = Path(d) / "hostile.cmpct"
        wire = _make_archive([0], b"ABCD", declared_size=5)
        path.write_bytes(wire)
        rejected = False
        try:
            preflight_archive(path, verify_blob_headers=True)
        except ValidationError:
            rejected = True
        assert rejected, "strict preflight must reject invalid size"
        with CMPCT(path) as reader:
            assert reader.read_range(PATH, 0, 4) == b"ABCD"
            wrong = reader.read_range(PATH, 4, 1)
            assert wrong == b"", ("parent no longer exhibits expected gap", wrong)
            complete_read_rejected = False
            try:
                reader.read(PATH)
            except IOError:
                complete_read_rejected = True
            assert complete_read_rejected, "full read must reject mismatch; O215 not O198"
            verify_rejected = False
            try:
                reader.verify()
            except IOError:
                verify_rejected = True
            assert verify_rejected, "verify must reject wrong total logical length"
        result = {
            "classification": "PARENT_SELECTIVE_IN_BOUNDS_SHORT_READ",
            "archive_sha256": hashlib.sha256(wire).hexdigest(),
            "actual_raw_blob_bytes": 4,
            "declared_logical_bytes": 5,
            "read_range_offset": 4,
            "read_range_length": 1,
            "observed_bytes_hex": wrong.hex(),
            "strict_preflight_rejected": rejected,
            "full_read_rejected": complete_read_rejected,
            "verify_rejected": verify_rejected,
            "authentic_root_version": 24,
        }
        print(json.dumps(result, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
