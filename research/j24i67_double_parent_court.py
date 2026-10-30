#!/usr/bin/env python3
"""J24I67: two-pointer r24 parent camouflage, installed Reader/preflight adversarial court.
Research only. The standalone wire O0 preceded the prospective hosted prereg.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, platform, shutil, struct, subprocess, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j24g92_footer_link_court import (Builder, append_delete, FOOTER, PREV_OFFSET,
    footer, lineage, independent_rows, inspect_reader, inspect_preflight, sha)

PARENT = "f29561c5e2d36a8f47aa35f61191911c0611be6b"
PREREG = "36b3a7747018d2a1ee7313a5f4e17d10f8e1c300"
READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def attest():
    head = git("rev-parse", "HEAD")
    for anc in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", anc, "HEAD"], check=True)
    assert git("rev-parse", "HEAD:src/cmpct/reader.py") == READER_BLOB
    assert FOOTER.size == 68 and PREV_OFFSET == 28
    return {"head": head, "source_parent": PARENT, "prereg": PREREG,
            "reader_blob": READER_BLOB,
            "instrument_blob": git("rev-parse", "HEAD:research/j24i67_double_parent_court.py")}

def rooted(raw, pos):
    visited = set()
    while pos:
        if pos in visited or len(visited) > 64:
            return False
        visited.add(pos)
        try:
            f = footer(raw, pos)
        except (AssertionError, ValueError):
            return False
        if f["kind"] == 0:
            return f["prev"] == 0
        if not 0 < f["prev"] < pos:
            return False
        pos = f["prev"]
    return False

def nearest_rooted(raw, positions):
    latest = positions[-1]
    rooted_positions = [pos for pos in positions if rooted(raw, pos)]
    previous = [pos for pos in rooted_positions if pos < latest]
    declared = footer(raw, latest)["prev"]
    return {"accepted": latest in rooted_positions and bool(previous)
                and declared == max(previous),
            "declared_parent": declared,
            "nearest_rooted": max(previous) if previous else None,
            "unrooted": [pos for pos in positions if pos not in rooted_positions]}

def case(n, root, evidence):
    src = root / f"source_{n}"
    src.mkdir()
    originals = {}
    for i in range(n):
        name = f"f{i:05d}.dat"
        raw = hashlib.sha256(f"j24i67-{n}-{i}".encode()).digest()
        (src/name).write_bytes(raw)
        originals[name] = sha(raw)
    target = root / f"original_{n}.cmpct"
    Builder(src, workers=1, reproducible=False).build(target)
    for i in range(3):
        append_delete(target, f"f{i:05d}.dat")
    original = target.read_bytes()
    chain = lineage(original)
    assert len(chain) == 4
    root_footer, f1, f2, f3 = chain
    assert [f["payload"]["ops"][0] for f in chain[1:]] == [
        ["del", f"f{i:05d}.dat"] for i in range(3)]
    assert (f1["prev"], f2["prev"], f3["prev"]) == (
        root_footer["pos"], f1["pos"], f2["pos"])
    original_names = independent_rows(chain)
    assert len(original_names) == n - 3

    single = bytearray(original)
    struct.pack_into("<Q", single, f3["pos"] + PREV_OFFSET, f1["pos"])
    single = bytes(single)
    double = bytearray(single)
    struct.pack_into("<Q", double, f2["pos"] + PREV_OFFSET, 0)
    double = bytes(double)
    assert len(original) == len(single) == len(double)
    for changed in (single, double):
        assert len(lineage(changed)) == 3
        assert independent_rows(lineage(changed)) == original_names | {"f00001.dat"}
        for f in chain:
            assert footer(changed, f["pos"])["payload_sha"] == f["payload_sha"]
    positions = [f["pos"] for f in chain]
    guard = {"original": nearest_rooted(original, positions),
             "single": nearest_rooted(single, positions),
             "double": nearest_rooted(double, positions)}
    assert guard["original"]["accepted"]
    assert not guard["single"]["accepted"]
    assert guard["double"]["accepted"]
    assert guard["double"]["unrooted"] == [f2["pos"]]
    changed_bytes = [i for i, (a, b) in enumerate(zip(original, double)) if a != b]
    assert 1 <= len(changed_bytes) <= 16
    assert all(any(p + PREV_OFFSET <= i < p + PREV_OFFSET + 8 for p in
                   (f2["pos"], f3["pos"])) for i in changed_bytes)
    assert sha(original) != sha(single) != sha(double)
    bad_sha = bytearray(original)
    bad_sha[-1] ^= 0x5a
    variants = {"original": original, "single": single,
                "double": double, "bad_latest_sha": bytes(bad_sha)}
    answers = {}
    for label, raw in variants.items():
        path = root / f"{n}-{label}.cmpct"
        path.write_bytes(raw)
        reader = inspect_reader(path)
        preflight = inspect_preflight(path)
        answers[label] = {"sha256": sha(raw), "reader": reader,
                          "preflight": preflight}
        shutil.copyfile(path, evidence / f"{n}-{label}.cmpct")
    assert answers["original"]["reader"]["accepted"]
    assert answers["original"]["preflight"]["accepted"]
    assert set(answers["original"]["reader"]["paths"]) == original_names
    bad = answers["bad_latest_sha"]
    assert bad["reader"]["accepted"] and bad["preflight"]["accepted"]
    assert set(bad["reader"]["paths"]) == original_names | {"f00002.dat"}
    for label in ("single", "double"):
        reader = answers[label]["reader"]
        strict = answers[label]["preflight"]
        assert reader["accepted"] and strict["accepted"], (label, reader, strict)
        assert set(reader["paths"]) == original_names | {"f00001.dat"}
        assert reader["footer"] == f3["pos"]
        assert strict["result"]["files"] == n - 2
        assert strict["result"]["latest_footer"] == f3["pos"]
        for name, digest in reader["sha256_by_path"].items():
            assert digest == originals[name]
    return {"original_count": n-3, "rewired_count": n-2,
            "resurrected": "f00001.dat", "archive_bytes": len(original),
            "mutated_physical_positions": changed_bytes,
            "same_all_footer_payload_sha256": True,
            "whole_archive_sha256_changed": True,
            "rooted_heuristic": guard, "variants": answers}

def main():
    evidence = pathlib.Path(os.environ.get("J24I67_EVIDENCE", "evidence/j24i67"))
    evidence.mkdir(parents=True, exist_ok=True)
    report = {"schema": "cmpct-j24i67-installed-guard-oracle-v1",
              "host": platform.platform(), "python": sys.version,
              "source": attest(), "product_credit": 0,
              "status": "STARTED", "cases": {}}
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24i67-") as td:
            for n in (16, 128):
                report["cases"][str(n)] = case(n, pathlib.Path(td), evidence)
        report["decision"] = "INSTALLED_DOUBLE_PARENT_CAMOUFLAGE_ACCEPTED"
        report["status"] = "PASS"
    except BaseException as exc:
        report["fatal"] = {"type": type(exc).__name__, "detail": str(exc)}
        report["status"] = "FAIL"
        raise
    finally:
        (evidence / "receipt.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n")
        print("J24I67", report["status"], report.get("decision"), flush=True)

if __name__ == "__main__":
    main()
