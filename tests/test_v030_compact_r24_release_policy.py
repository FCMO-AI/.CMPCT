from __future__ import annotations

import json
import subprocess
import sys


def test_compact_r24_candidate_policy_boundary_isolated_from_test_process():
    # The candidate intentionally patches the preserved release Builder at import time.  Exercise it
    # in a fresh interpreter so this regression test cannot contaminate unrelated canonical tests.
    code = r'''
import json
from experiments import entropygraph_v030_release_product_compact_r24 as candidate
base = candidate._BASE
hints = base._ReleaseTextHints()
print(json.dumps({
    "candidate": candidate.PRODUCT_CANDIDATE,
    "candidate_deflate_min": candidate.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
    "base_deflate_min": base.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
    "medium_binary_pack": candidate.R24_COMPACT_MEDIUM_BINARY_PACKING,
    "medium_terminal": candidate.R24_COMPACT_MEDIUM_TERMINAL,
    "bin_in_hints": ".bin" in hints,
    "hints_equal_original": set(hints) == set(base._R24_ORIGINAL_TEXT_EXT),
    "micro_max": base.R24_RELEASE_MICRO_MAX_FILE_BYTES,
    "pack_cap": base.R24_RELEASE_PACK_CAP_BYTES,
    "wide_chunk": base.R24_RELEASE_WIDE_CHUNK_BYTES,
    "revision_equal": candidate.REVISION == base.REVISION,
}))
'''
    proc = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(proc.stdout)
    assert receipt == {
        "candidate": "v030-compact-r24-release-policy-v1",
        "candidate_deflate_min": 64 * 1024,
        "base_deflate_min": 64 * 1024,
        "medium_binary_pack": False,
        "medium_terminal": False,
        "bin_in_hints": False,
        "hints_equal_original": True,
        "micro_max": 256 * 1024,
        "pack_cap": 2 * 1024 * 1024,
        "wide_chunk": 8 * 1024 * 1024,
        "revision_equal": True,
    }
