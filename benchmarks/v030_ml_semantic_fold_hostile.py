from __future__ import annotations
import binascii, json, shutil, struct, tempfile
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
    bad_usize = R.G04.MAX_DECODE_UNIT + 1
    with dst.open("r+b") as f:
        f.seek(pos)
        f.write(R.PH.pack(codec, bad_usize, csize, crc, logical_sha))


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

    # Install exactly the corrected bounded research fold. This is still an oracle:
    # it must fail hostile proof before any product integration can earn credit.
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

    # Scope proof: a fresh strong_verify call is deliberately made after the fold is installed.
    # The fold only replaces the release-reader session used by this process, so corruption must
    # still be rejected by strong verification rather than silently accepted.
    strong = _expect_fail("strong-verify-corrupt-payload", lambda: PRODUCT.strong_verify(bad_payload))

    return {
        "schema": "cmpct-v030-ml-semantic-fold-hostile-v1",
        "release_credit": False,
        "valid_tree_sha256": expected_tree,
        "checks": [payload, bound, rollback, strong],
        "preserved_claim": [
            "payload SHA fails closed",
            "physical usize bound fails closed",
            "transactional destination rollback survives failure",
            "strong_verify rejects corrupted payload",
        ],
        "unpaid": [
            "post-CRC logical-node corruption",
            "file/path/size hostile metadata under authenticated fixture mutation",
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
