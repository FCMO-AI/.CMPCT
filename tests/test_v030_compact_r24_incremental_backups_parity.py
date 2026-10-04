from __future__ import annotations

"""Focused complete-r24 parity falsifier for the correctly bound compact candidate.

This is intentionally narrower than the full release matrix.  PR #212 exists because
the earlier product attempt changed policy in a parent interpreter while the nested
process that physically emitted r24 bytes still imported canonical policy.  The two
existing custody regressions prove that the corrected shipping seam reaches the
candidate-owned child.  This test answers the next decision question on the exact
accepted Incremental Backups content tree:

    does that correctly bound child produce a complete r24 artifact no larger than
    genuine r24 on the *same* immutable source and filesystem state?

A red result retires the compact-r24 family; it must not be rescued by threshold or
workload gardening.  A green result earns only the unchanged full compression matrix.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


EXPECTED_CONTENT_TREE_SHA256 = (
    "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"
)
EXPECTED_FILES = 769
EXPECTED_LOGICAL_BYTES = 14_006_619
CANONICAL_WORKER = "experiments.entropygraph_v030_r24_process_prebuild"
CANDIDATE_WORKER = "experiments.entropygraph_v030_r24_compact_candidate_prebuild"


def _historical_content_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(4, "little"))
        digest.update(rel)
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def _accepted_incremental_backups(tmp_path: Path) -> Path:
    # Generate only the accepted workload rather than paying for the complete 15-row
    # matrix.  The same repair used by current release evidence canonicalizes the
    # nested snapshot ZIP, while content-tree identity independently proves substrate
    # continuity before either encoder is allowed to run.
    from benchmarks import neutral_hostile_corpus_v1 as neutral
    from benchmarks import neutral_hostile_determinism_repair_v5 as repair

    repair.install_generation_hooks(neutral)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    neutral.corpus_backups(corpus)
    repair.normalize_root(corpus)
    source = corpus / "06_incremental_backups"

    files = sorted(item for item in source.rglob("*") if item.is_file())
    assert len(files) == EXPECTED_FILES
    assert sum(path.stat().st_size for path in files) == EXPECTED_LOGICAL_BYTES
    assert _historical_content_tree_sha256(source) == EXPECTED_CONTENT_TREE_SHA256
    return source


def _run_fresh_arm(source: Path, archive: Path, worker_module: str) -> dict:
    # Keep each arm in a separate parent interpreter.  R24PrebuildProcess then starts
    # the actual byte-owning nested child, so neither candidate import-side effects nor
    # process-global Builder state can contaminate the genuine-r24 control.
    code = r"""
import hashlib
import json
from pathlib import Path
import sys

from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess

source = Path(sys.argv[1])
archive = Path(sys.argv[2])
worker = sys.argv[3]

with R24PrebuildProcess(source, archive, timeout_s=None, worker_module=worker) as proc:
    stats = dict(proc.result())

# Import verification only after the byte-owning child has exited.  Both arms use the
# same canonical reader/strong-verifier; the candidate changes encoder policy only.
from experiments import entropygraph_v030_release_product as product

proof = dict(product.strong_verify(archive))
expected_tree = product.treehash(source)
assert proof.get("ok") is True, proof
assert proof.get("format_revision") == 24, proof
assert proof.get("tree_sha256") == expected_tree, (proof, expected_tree)

h = hashlib.sha256()
with archive.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)

print(json.dumps({
    "worker_module": worker,
    "archive_bytes": archive.stat().st_size,
    "archive_sha256": h.hexdigest(),
    "tree_sha256": proof["tree_sha256"],
    "stats": stats,
}, sort_keys=True))
"""
    proc = subprocess.run(
        [sys.executable, "-c", code, str(source), str(archive), worker_module],
        check=True,
        capture_output=True,
        text=True,
        timeout=240,
    )
    return json.loads(proc.stdout.splitlines()[-1])


def test_correctly_bound_compact_r24_does_not_lose_incremental_backups_bytes(
    tmp_path: Path,
) -> None:
    source = _accepted_incremental_backups(tmp_path)

    genuine = _run_fresh_arm(
        source,
        tmp_path / "genuine-r24.cmpct",
        CANONICAL_WORKER,
    )
    candidate = _run_fresh_arm(
        source,
        tmp_path / "candidate-r24.cmpct",
        CANDIDATE_WORKER,
    )

    # Both artifacts reconstruct the same richer current user-tree semantics.  Archive
    # SHA need not match because the candidate deliberately changes physical r24
    # representation; complete bytes, not representation identity, decide this fork.
    assert candidate["tree_sha256"] == genuine["tree_sha256"]

    effective = candidate["stats"].get("r24_prebuild_effective_policy")
    assert effective == {
        "candidate": "v030-compact-r24-release-policy-v1",
        "deflate_reuse_min_bytes": 64 * 1024,
        "build_reported_deflate_reuse_min_bytes": 64 * 1024,
        "micro_pack_max_file_release_bytes": 256 * 1024,
        "builder_text_ext_is_release_view": True,
        "medium_binary_packing": False,
        "hints_equal_original": True,
        "medium_terminal_disabled": True,
    }

    # Compare on the exact same generated tree instead of hard-coding a historical
    # complete-archive byte count whose filesystem metadata can vary while the frozen
    # content-tree fingerprint remains identical.  A single byte of candidate loss is
    # disproof under PR #212's preregistered no-gardening law.
    assert candidate["archive_bytes"] <= genuine["archive_bytes"], (
        "correctly bound compact-r24 candidate regressed accepted Incremental Backups: "
        f"candidate={candidate['archive_bytes']} genuine={genuine['archive_bytes']} "
        f"candidate_sha={candidate['archive_sha256']} genuine_sha={genuine['archive_sha256']}"
    )
