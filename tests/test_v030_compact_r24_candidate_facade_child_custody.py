from __future__ import annotations

"""Prove the compact candidate facade routes its shipping r24 prebuild to the candidate child.

The lower-level custody regression can prove that the candidate worker itself owns the intended
Builder policy. This test closes the adjacent integration gap: importing the compact *product
facade* must reinstall the existing shipping prebuild seam with that worker, and the r24 build
consumed through the canonical-final owner must return the candidate child's effective-policy
attestation. The probe runs in a fresh interpreter so candidate import-side effects cannot leak into
other canonical tests.
"""

import json
import subprocess
import sys


def test_compact_candidate_facade_routes_r24_through_candidate_child(tmp_path):
    code = r'''
import json
from pathlib import Path
import tempfile
import zipfile

from cmpct.codec import S_PACK, S_VZIP
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product_compact_r24 as candidate

root = Path(r"__ROOT__")
root.mkdir(parents=True, exist_ok=True)
for i in range(8):
    payload = bytes([i]) * (48 * 1024 - 64) + bytes(range(64))
    (root / f"medium-{i:02d}.bin").write_bytes(payload)
with zipfile.ZipFile(root / "small-stream.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    zf.writestr("payload.txt", ("alpha beta gamma delta\\n" * 8192).encode())

work = root.parent / "work"
staging = work / "profile"
staging.mkdir(parents=True, exist_ok=True)
out = work / "canonical-r24.cmpct"

# The candidate facade must have replaced the canonical registry with the candidate worker.
expected_worker = "experiments.entropygraph_v030_r24_compact_candidate_prebuild"
assert candidate._R24_PROCESS_REGISTRY.worker_module == expected_worker
assert candidate._PRODUCT._R24_PROCESS_REGISTRY is candidate._R24_PROCESS_REGISTRY

# Exercise the exact shipping seam: prepare starts the child; r24_build consumes its artifact.
try:
    candidate._BASE.C._prepare_profile_tree(root, staging)
except candidate._BASE.ProfileNotEligible:
    pass
stats = candidate._BASE.C._r24_build(root, out)
assert stats["r24_prebuild_owner"] == "child-process-v1"
assert stats["r24_prebuild_reused"] is True
assert stats["r24_prebuild_effective_policy"] == {
    "candidate": "v030-compact-r24-release-policy-v1",
    "deflate_reuse_min_bytes": 64 * 1024,
    "build_reported_deflate_reuse_min_bytes": 64 * 1024,
    "micro_pack_max_file_release_bytes": 256 * 1024,
    "builder_text_ext_is_release_view": True,
    "medium_binary_packing": False,
    "hints_equal_original": True,
    "medium_terminal_disabled": True,
}

with CMPCT(out) as reader:
    reader.verify()
    bins = [row for row in reader.files if row[0].endswith(".bin")]
    zip_row = reader.by["small-stream.zip"]
    assert all(row[6][0] != S_PACK for row in bins)
    assert zip_row[6][0] == S_VZIP
    payloads = reader.recipes[zip_row[6][1]][2]
    assert len(payloads) == 1
    assert int(payloads[0][2]) == 2

print(json.dumps({
    "worker_module": candidate._R24_PROCESS_REGISTRY.worker_module,
    "owner": stats["r24_prebuild_owner"],
    "effective_policy": stats["r24_prebuild_effective_policy"],
    "archive_bytes": out.stat().st_size,
}, sort_keys=True))
'''.replace("__ROOT__", str(tmp_path / "src"))
    proc = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    receipt = json.loads(proc.stdout.splitlines()[-1])
    assert receipt["worker_module"] == "experiments.entropygraph_v030_r24_compact_candidate_prebuild"
    assert receipt["owner"] == "child-process-v1"
    assert receipt["effective_policy"]["candidate"] == "v030-compact-r24-release-policy-v1"
