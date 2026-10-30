#!/usr/bin/env python3
"""J24G93: authentic public Writer continuation after an unrooted SHA-valid r24 footer.

Research instrument only. Do not change Reader, Writer, format, validation or release law.
"""
from __future__ import annotations
import hashlib, json, os, platform, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import preflight_archive
from j24g92_footer_link_court import FOOTER, PREV_OFFSET, footer, lineage, sha, inspect_reader, inspect_preflight

PARENT = "f29561c5e2d36a8f47aa35f61191911c0611be6b"
PREREG = "d6bdcdf7"
READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"

def attest():
    def git(*args):
        return subprocess.check_output(["git", *args], text=True).strip()
    head = git("rev-parse", "HEAD")
    subprocess.run(["git", "merge-base", "--is-ancestor", PARENT, "HEAD"], check=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"], check=True)
    assert git("rev-parse", "HEAD:src/cmpct/reader.py") == READER_BLOB
    return {"head": head, "parent": PARENT, "prereg": PREREG, "reader_blob": READER_BLOB}

def check_reader(path, expected, hashes, footer_pos):
    got = inspect_reader(path)
    strict = inspect_preflight(path)
    assert got["accepted"], got
    assert strict["accepted"], strict
    assert set(got["paths"]) == expected, (got, expected)
    assert got["footer"] == footer_pos, (got["footer"], footer_pos)
    assert strict["result"]["files"] == len(expected), strict
    assert strict["result"]["latest_footer"] == footer_pos, strict
    for name, digest in got["sha256_by_path"].items():
        assert digest == hashes[name], name
    return {"reader": got, "preflight": strict}

def case(root: Path, evidence: Path, n: int):
    source = root / f"source_{n}"
    source.mkdir()
    hashes = {}
    for i in range(n):
        name = f"f{i:05d}.dat"
        payload = hashlib.sha256(f"j24g93-{n}-{i}".encode()).digest()
        (source / name).write_bytes(payload)
        hashes[name] = sha(payload)

    original = root / f"{n}-pre.cmpct"
    Builder(source, workers=1, reproducible=False).build(original)
    for i in range(3):
        append_delete(original, f"f{i:05d}.dat")
    prefix = original.read_bytes()
    history = lineage(prefix)
    assert len(history) == 4
    last_committed = history[-1]
    assert last_committed["kind"] == 1
    before = set(hashes) - {f"f{i:05d}.dat" for i in range(3)}
    answers = {"before": check_reader(original, before, hashes, last_committed["pos"])}
    shutil.copyfile(original, evidence / f"{n}-pre.cmpct")

    # Simulate an interrupted/abandoned generation that has a structurally
    # correct SHA-bearing footer but no checkpoint-rooted lineage. This is
    # *manual injection*, not a physical crash or an authentic Writer commit.
    orphan_payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    orphan = orphan_payload + FOOTER.pack(
        b"CMPTF24\x00", 1, 0, 0, 0, len(orphan_payload),
        len(orphan_payload), 0, hashlib.sha256(orphan_payload).digest())
    orphan_pos = len(prefix) + len(orphan_payload)
    assert orphan_pos > last_committed["pos"]
    with original.open("ab", buffering=0) as f:
        f.write(orphan)
        os.fsync(f.fileno())
    pending = original.read_bytes()
    assert pending == prefix + orphan
    orphan_checked = footer(pending, orphan_pos)
    assert orphan_checked["kind"] == 1 and orphan_checked["prev"] == 0
    assert orphan_checked["payload"] == {"blobs": [], "ops": []}
    answers["orphan_only"] = check_reader(
        original, before, hashes, last_committed["pos"])
    shutil.copyfile(original, evidence / f"{n}-orphan-only.cmpct")

    # Decisive step: run the *unchanged installed public Writer*.
    append_delete(original, "f00003.dat")
    final = original.read_bytes()
    assert final.startswith(pending)
    new_chain = lineage(final)
    assert len(new_chain) == 5
    latest = new_chain[-1]
    assert latest["prev"] == last_committed["pos"] != orphan_pos
    assert latest["payload"]["ops"] == [["del", "f00003.dat"]]
    assert latest["kind"] == 1
    after = before - {"f00003.dat"}
    answers["after_writer"] = check_reader(original, after, hashes, latest["pos"])
    shutil.copyfile(original, evidence / f"{n}-after-writer.cmpct")

    # Stronger simpler control: the same fourth public DELETE, with no orphan.
    control = root / f"{n}-clean-fourth.cmpct"
    control.write_bytes(prefix)
    append_delete(control, "f00003.dat")
    clean = control.read_bytes()
    control_chain = lineage(clean)
    assert len(control_chain) == 5
    answers["clean_control"] = check_reader(control, after, hashes, control_chain[-1]["pos"])
    assert answers["clean_control"]["reader"]["sha256_by_path"] == answers["after_writer"]["reader"]["sha256_by_path"]
    shutil.copyfile(control, evidence / f"{n}-clean-fourth.cmpct")

    # Torn/corrupt terminal commit should recover pre-fourth-delete state,
    # skipping both invalid latest and unrooted orphan.
    bad = bytearray(final)
    bad[-1] ^= 0x5A
    corrupt = root / f"{n}-corrupt-final.cmpct"
    corrupt.write_bytes(bad)
    answers["bad_newest_digest"] = check_reader(
        corrupt, before, hashes, last_committed["pos"])
    shutil.copyfile(corrupt, evidence / f"{n}-corrupt-final.cmpct")

    return {
        "n": n,
        "source_original_sha256": sha(prefix),
        "orphan_only_sha256": sha(pending),
        "after_writer_sha256": sha(final),
        "clean_control_sha256": sha(clean),
        "corrupt_final_sha256": sha(bytes(bad)),
        "pre_existing_footer": last_committed["pos"],
        "orphan_footer": orphan_pos,
        "writer_final_footer": latest["pos"],
        "writer_parent": latest["prev"],
        "orphan_parent": orphan_checked["prev"],
        "before_count": len(before),
        "after_count": len(after),
        "orphan_physical_bytes": len(orphan),
        "final_added_bytes_after_orphan": len(final) - len(pending),
        "valid_committed_footer_depth_after": len(new_chain) - 1,
        "answers": answers,
        "nearest_physical_sha_footer_is_not_writer_parent": orphan_pos != latest["prev"],
    }

def main():
    evidence = Path(os.environ.get("J24G93_EVIDENCE", "evidence/j24g93"))
    evidence.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "cmpct-j24g93-genuine-public-writer-orphan-recovery-v1",
        "source": attest(), "host": platform.platform(), "python": sys.version,
        "result_class": "INSTALLED_PRODUCT_IN_RESEARCH_COURT",
        "release_credit": 0, "product_source_modified": False,
        "status": "STARTED", "cases": {},
        "scope": "manually injected unrooted orphan, not induced OS crash",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g93-") as d:
            for n in (16, 128):
                report["cases"][str(n)] = case(Path(d), evidence, n)
        assert all(x["nearest_physical_sha_footer_is_not_writer_parent"]
                   for x in report["cases"].values())
        report["status"] = "PASS"
        report["decision"] = "PUBLIC_WRITER_SKIPS_SHA_VALID_UNROOTED_ORPHAN"
    except BaseException as exc:
        report["status"] = "FAIL"
        report["fatal"] = {"type": type(exc).__name__, "detail": str(exc)}
        raise
    finally:
        (evidence / "receipt.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("J24G93_REPORT", json.dumps({
            "status": report["status"], "decision": report.get("decision"),
            "cases": {k: {"before": v["before_count"], "after": v["after_count"],
                "orphan_pos": v["orphan_footer"], "actual_prev": v["writer_parent"]}
                for k, v in report["cases"].items()}
        }, sort_keys=True))

if __name__ == "__main__":
    main()
