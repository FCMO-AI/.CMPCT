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


def _expect_strong_reject(label, archive: Path):
    result = PRODUCT.strong_verify(archive)
    if not isinstance(result, dict) or result.get("ok") is not False:
        raise RuntimeError(f"{label}: strong_verify unexpectedly accepted: {result!r}")
    return {"label": label, "failed_closed": True, "error": "structured-verify-failure", "message": str(result.get("error", ""))[:240]}


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


def _rewrite_header(src: Path, dst: Path, mutate):
    shutil.copy2(src, dst)
    pos, codec, usize, csize, crc, logical_sha = _first_record_layout(dst)
    codec, usize, csize, crc, logical_sha = mutate(codec, usize, csize, crc, logical_sha)
    with dst.open("r+b") as f:
        f.seek(pos)
        f.write(R.PH.pack(codec, usize, csize, crc, logical_sha))


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


def _post_crc_fault(archive: Path, dst: Path):
    cls = R._G04Session
    original = cls.record
    fired = [False]
    def corrupt_after_record_checks(self, rid):
        value = original(self, rid)
        if not fired[0] and value:
            fired[0] = True
            return bytes([value[0] ^ 1]) + value[1:]
        return value
    cls.record = corrupt_after_record_checks
    try:
        result = _expect_fail("post-crc-in-memory-record-fault", lambda: PRODUCT.extract(archive, dst))
        result["fault_injected"] = fired[0]
        if not fired[0]:
            raise RuntimeError("post-CRC fault injector never reached a record")
        return result
    finally:
        cls.record = original


def run(root: Path):
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = root / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected_tree = PRODUCT.treehash(src)

    FOLD.install_bounded_fold()

    valid_dst = root / "valid"
    PRODUCT.extract(archive, valid_dst)
    if PRODUCT.treehash(valid_dst) != expected_tree:
        raise RuntimeError("valid extraction semantic drift")

    bad_payload = root / "bad-payload.cmpct"
    _mutate_payload(archive, bad_payload)
    payload = _expect_fail("payload-sha", lambda: PRODUCT.extract(bad_payload, root / "bad-payload-out"))

    bad_usize = root / "bad-usize.cmpct"
    _rewrite_header(archive, bad_usize, lambda c,u,s,r,h:(c,R.G04.MAX_DECODE_UNIT+1,s,r,h))
    usize = _expect_fail("physical-usize-bound", lambda: PRODUCT.extract(bad_usize, root / "bad-usize-out"))

    bad_csize = root / "bad-csize.cmpct"
    _rewrite_header(archive, bad_csize, lambda c,u,s,r,h:(c,u,R.G04.MAX_DECODE_UNIT+1024*1024+1,r,h))
    csize = _expect_fail("physical-csize-bound", lambda: PRODUCT.extract(bad_csize, root / "bad-csize-out"))

    bad_crc = root / "bad-crc.cmpct"
    _rewrite_header(archive, bad_crc, lambda c,u,s,r,h:(c,u,s,r^1,h))
    crc = _expect_fail("record-crc", lambda: PRODUCT.extract(bad_crc, root / "bad-crc-out"))

    post_crc = _post_crc_fault(archive, root / "post-crc-out")
    rollback = _assert_destination_rollback(bad_payload, root / "rollback-dst")
    strong_payload = _expect_strong_reject("strong-verify-corrupt-payload", bad_payload)

    bad_logical_sha = root / "bad-logical-sha.cmpct"
    _rewrite_header(archive, bad_logical_sha, lambda c,u,s,r,h:(c,u,s,r,bytes([h[0]^1])+h[1:]))
    folded_dst = root / "folded-logical-sha"
    PRODUCT.extract(bad_logical_sha, folded_dst)
    if PRODUCT.treehash(folded_dst) != expected_tree:
        raise RuntimeError("logical-SHA scope probe changed logical tree")
    strong_scope = PRODUCT.strong_verify(bad_logical_sha)
    strong_scope_accepted = bool(isinstance(strong_scope, dict) and strong_scope.get("ok") is True)

    return {
        "schema": "cmpct-v030-ml-semantic-fold-hostile-v5",
        "release_credit": False,
        "valid_tree_sha256": expected_tree,
        "checks": [payload, usize, csize, crc, post_crc, rollback, strong_payload],
        "scope_probe": {
            "mutation": "record logical SHA only",
            "folded_full_extract_tree_identical": True,
            "strong_verify_accepted_under_global_oracle": strong_scope_accepted,
            "strong_verify_result": strong_scope,
            "product_requirement": "strong_verify must retain nested SHA; use default-false extraction-only policy rather than global session replacement",
        },
        "preserved_claim": [
            "payload SHA fails closed",
            "physical usize/csize bounds fail closed",
            "record CRC fails closed",
            "post-CRC in-memory record corruption is caught before publication",
            "transactional destination rollback survives failure",
            "strong_verify rejects payload corruption",
        ],
        "unpaid": [
            "product-scoped strong_verify nested-SHA rejection",
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
