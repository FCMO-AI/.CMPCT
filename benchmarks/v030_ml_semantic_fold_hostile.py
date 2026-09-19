from __future__ import annotations
import json, shutil
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_ml_semantic_fold_bounded_oracle as FOLD
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VR

R = VR.C.POLICY.R


def _expect_fail(label, fn):
    try:
        fn()
    except Exception as exc:
        return {"label": label, "failed_closed": True, "error": type(exc).__name__, "message": str(exc)[:240]}
    raise RuntimeError(f"{label}: corruption unexpectedly accepted")


def _first_record_layout(archive: Path):
    stream, _meta, start, offsets, _merkle, _tail = R._g04_open(archive)
    try:
        pos = start + offsets[0]
        stream.seek(pos)
        header = stream.read(R.PH.size)
        codec, usize, csize, crc, logical_sha = R.PH.unpack(header)
        return pos, codec, usize, csize, crc, logical_sha
    finally:
        stream.close()


def _mutate_payload(src: Path, dst: Path):
    shutil.copy2(src, dst)
    pos, _codec, _usize, csize, _crc, _sha = _first_record_layout(dst)
    if csize < 1:
        raise RuntimeError("fixture has empty first payload")
    with dst.open("r+b") as f:
        f.seek(pos + R.PH.size)
        b = f.read(1)
        f.seek(pos + R.PH.size)
        f.write(bytes([b[0] ^ 0x01]))


def _mutate_header_bound(src: Path, dst: Path):
    shutil.copy2(src, dst)
    pos, codec, _usize, csize, crc, logical_sha = _first_record_layout(dst)
    with dst.open("r+b") as f:
        f.seek(pos)
        f.write(R.PH.pack(codec, R.G04.MAX_DECODE_UNIT + 1, csize, crc, logical_sha))


def _mutate_logical_sha(src: Path, dst: Path):
    shutil.copy2(src, dst)
    pos, codec, usize, csize, crc, logical_sha = _first_record_layout(dst)
    bad = bytes([logical_sha[0] ^ 1]) + logical_sha[1:]
    with dst.open("r+b") as f:
        f.seek(pos)
        f.write(R.PH.pack(codec, usize, csize, crc, bad))


def _assert_destination_rollback(archive: Path, dst: Path):
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    marker = dst / "preexisting.txt"
    marker.write_text("keep-me\n")
    before = PRODUCT.treehash(dst)
    failure = _expect_fail("transactional-corrupt-payload", lambda: PRODUCT.extract(archive, dst))
    after = PRODUCT.treehash(dst)
    if before != after or marker.read_text() != "keep-me\n":
        raise RuntimeError("failed extraction modified pre-existing destination")
    failure["destination_tree_preserved"] = True
    return failure


def run(root: Path):
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = root / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected_tree = PRODUCT.treehash(src)

    # Install exactly the corrected bounded research fold. This is intentionally
    # global and therefore is NOT the desired product policy; the scope probe below
    # exists to prove why productization must be target-root/default-false scoped.
    FOLD.install_bounded_fold()

    valid_dst = root / "valid"
    PRODUCT.extract(archive, valid_dst)
    if PRODUCT.treehash(valid_dst) != expected_tree:
        raise RuntimeError("valid extraction semantic drift")

    bad_payload = root / "bad-payload.cmpct"
    _mutate_payload(archive, bad_payload)
    payload = _expect_fail("payload-sha", lambda: PRODUCT.extract(bad_payload, root / "bad-payload-out"))

    bad_bound = root / "bad-bound.cmpct"
    _mutate_header_bound(archive, bad_bound)
    bound = _expect_fail("physical-usize-bound", lambda: PRODUCT.extract(bad_bound, root / "bad-bound-out"))
    rollback = _assert_destination_rollback(bad_payload, root / "rollback-dst")
    strong_payload = _expect_fail("strong-verify-corrupt-payload", lambda: PRODUCT.strong_verify(bad_payload))

    # Decision-changing scope discriminator: corrupt only the reconstructed-record SHA
    # in the physical header. The terminal tree still describes the correct logical
    # bytes, so folded full extraction may accept it; strong_verify must NOT inherit
    # that deferral. The research monkeypatch is global, so record the expected scope
    # gap rather than laundering it into product evidence.
    bad_logical_sha = root / "bad-logical-sha.cmpct"
    _mutate_logical_sha(archive, bad_logical_sha)
    folded_dst = root / "folded-logical-sha"
    PRODUCT.extract(bad_logical_sha, folded_dst)
    if PRODUCT.treehash(folded_dst) != expected_tree:
        raise RuntimeError("logical-SHA scope probe changed logical tree")
    strong_scope_accepted = True
    try:
        PRODUCT.strong_verify(bad_logical_sha)
    except Exception:
        strong_scope_accepted = False

    return {
        "schema": "cmpct-v030-ml-semantic-fold-hostile-v2",
        "release_credit": False,
        "valid_tree_sha256": expected_tree,
        "checks": [payload, bound, rollback, strong_payload],
        "scope_probe": {
            "mutation": "record logical SHA only",
            "folded_full_extract_tree_identical": True,
            "strong_verify_accepted_under_global_oracle": strong_scope_accepted,
            "product_requirement": "strong_verify must retain nested SHA; use default-false extraction-only policy rather than global session replacement",
        },
        "preserved_claim": [
            "payload SHA fails closed",
            "physical usize bound fails closed",
            "transactional destination rollback survives failure",
            "strong_verify rejects payload corruption",
        ],
        "unpaid": [
            "product-scoped strong_verify nested-SHA rejection",
            "post-CRC logical-node corruption",
            "authenticated metadata path/file/size hostile mutation",
            "selective-read nested-SHA scope proof",
            "product-owner implementation and fresh-process release evidence",
        ],
    }


if __name__ == "__main__":
    out = run(Path("benchmark-artifacts/v030-ml-semantic-fold-hostile"))
    path = Path("benchmark-artifacts/v030-ml-semantic-fold-hostile.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
