#!/usr/bin/env python3
"""J24G83: source-exact fair Writer control: fresh optimized Reader every append.
Research only. No shipping Reader, Writer, lease, release or benchmark alteration.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import msgpack
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from cmpct import transactions as tx
from j24g80_owned_writer_session import (
    attest as parent_attest, make_base, select, sha_file, trial as parent_trial,
)
from j24g74_owned_decoder_court import OwnedCMPCT

ROOT = Path(__file__).resolve().parents[1]
PREREG = "b8013e7e3ff7168949d7b1526452c3e5b31cfaf9"
DONOR = {
    "research/j24g60_single_delta_chain_court.py": "feb7939224b59ace183df81eebcd3c33ebd81451",
    "research/j24g62_crossgen_rename_oracle.py": "b700ecdad289268d765e3b2446898ace4fdaa06a",
    "research/j24g64_mixed_fsmeta_oracle.py": "7657a41d11f2b3c8136c0b69cfe62401f9b19ccb",
    "research/j24g73_reader_open.py": "9b2fa7c2d625cce84597212673c35fba29dcafd5",
    "research/j24g74_owned_decoder_court.py": "9af74e26e7585f6d88b1d59ead86514f41b0e373",
}
PRODUCT = {
    "src/cmpct/transactions.py": "71bbc8a989d1da79d0f0dbe44f7f5c39f3304854",
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
}
CASES = ((8192, "middle"), (32768, "tail"))
ORDER = (("public", 0), ("fresh", 0), ("owned", 0),
         ("owned", 1), ("fresh", 1), ("public", 1))


def attest():
    source = parent_attest()
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                   cwd=ROOT, check=True)
    for name, expected in {**PRODUCT, **DONOR}.items():
        actual = subprocess.check_output(["git", "rev-parse", "HEAD:" + name],
                                         cwd=ROOT, text=True).strip()
        assert actual == expected, ("source-identity", name, actual, expected)
    import cmpct.reader as installed_reader
    import cmpct.transactions as installed_writer
    for path, module in (("src/cmpct/reader.py", installed_reader),
                         ("src/cmpct/transactions.py", installed_writer)):
        assert Path(module.__file__).read_bytes().replace(b"\r\n", b"\n") == (
            ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    return dict(**source, prereg_control=PREREG, donor_source_blobs=DONOR,
                product_source_blobs=PRODUCT)


def fresh_trial(root, base, n, where, names, replicate):
    path = root / f"{n}-{where}-fresh-{replicate}.cmpct"
    shutil.copyfile(base, path)
    assert sha_file(path) == sha_file(base)
    samples, physical = [], []
    for generation, member in enumerate(names, 1):
        start, cpu = time.perf_counter_ns(), time.process_time_ns()
        old = tx.CMPCT
        # The public append_delete body and every physical fsync remain EXACTLY unchanged.
        # Only its per-invocation Reader type changes. Restore even on exceptions.
        try:
            tx.CMPCT = OwnedCMPCT
            tx.append_delete(path, member)
        finally:
            tx.CMPCT = old
        samples.append(dict(generation=generation,
                            wall_ns=time.perf_counter_ns()-start,
                            cpu_ns=time.process_time_ns()-cpu))
        physical.append(dict(generation=generation, sha256=sha_file(path),
                             bytes=path.stat().st_size))
        if generation == 63:
            # This extra oracle is AFTER the timed pre-checkpoint operations,
            # and confirms donor admission without changing the timed route.
            with CMPCT(path) as base_reader, OwnedCMPCT(path) as own_reader:
                assert own_reader._research_route == "owned-fresh-decoder"
                assert own_reader.index == base_reader.index
                assert own_reader.delta_depth == base_reader.delta_depth == 63
    assert tx.CMPCT is CMPCT, "test-time Reader replacement escaped operation scope"
    with CMPCT(path) as reader:
        assert reader.delta_depth == 0 and len(reader.by) == n-64
        assert reader.verify() == n-64
        final = msgpack.packb(reader.index, use_bin_type=True)
        assert set(reader.by) == {f"f{i:05d}.dat" for i in range(n)}-set(names)
        for member in ("f00000.dat", f"f{n//4:05d}.dat"):
            if member in reader.by:
                i = int(member[1:6])
                assert reader.read(member) == hashlib.sha256(
                    f"j24g80-{n}-{i}".encode()).digest()
    result = preflight_archive(path)
    assert result["files"] == n-64 and result["delta_depth"] == 0
    corrupted = root / f"{n}-{where}-fresh-{replicate}-corrupt.cmpct"
    data = bytearray(path.read_bytes())
    data[-1] ^= 0xA5
    corrupted.write_bytes(data)
    with CMPCT(corrupted) as reader:
        assert reader.delta_depth == 63 and len(reader.by) == n-63
        assert names[-1] in reader.by and reader.verify() == n-63
    if replicate == 0:
        output = Path(os.getenv("J24G83_EVIDENCE_DIR", "evidence"))
        output.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output / f"j24g83-{n}-{where}-fresh-valid.cmpct")
        shutil.copyfile(corrupted, output / f"j24g83-{n}-{where}-fresh-corrupt-tail.cmpct")
    return dict(variant="fresh", trial=replicate, per_generation=samples,
                physical=physical, init_wall_ns=0, init_cpu_ns=0,
                final_index_sha256=hashlib.sha256(final).hexdigest(),
                checkpoint64=True, corrupt_tail_recovery=True,
                owned_decoder_admission_after63=True)


def main():
    output = Path(os.getenv("J24G83_EVIDENCE_DIR", "evidence"))
    output.mkdir(parents=True, exist_ok=True)
    resultfile = output / "j24g83-result.json"
    receipt = dict(schema="j24g83-fresh-reader-writer-control-v1",
                   source=attest(), host=platform.platform(),
                   status="RUNNING", product_credit=0, cases={})
    def save():
        resultfile.write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
    save()
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g83-") as dirname:
            root = Path(dirname)
            for n, where in CASES:
                base, build_ns = make_base(root, n, where)
                names = select(n, where)
                rows = []
                key = f"{n}-{where}"
                receipt["cases"][key] = dict(status="RUNNING",
                                             base_sha256=sha_file(base),
                                             base_bytes=base.stat().st_size,
                                             builder_wall_ns=build_ns, rows=rows)
                save()
                for variant, i in ORDER:
                    if variant == "fresh":
                        row = fresh_trial(root, base, n, where, names, i)
                    else:
                        row = parent_trial(root, base, n, where, names, variant, i)
                    rows.append(row)
                    save()
                    print("J24G83", key, variant, i, "first63_s",
                          sum(x["wall_ns"] for x in row["per_generation"][:63])/1e9,
                          flush=True)
                baseline = rows[0]["physical"]
                assert all(row["physical"] == baseline for row in rows)
                assert len({row["final_index_sha256"] for row in rows}) == 1
                medians = {
                    label: statistics.median(
                        sum(t["wall_ns"] for t in row["per_generation"][:63])
                        + row["init_wall_ns"]
                        for row in rows if row["variant"] == label
                    ) for label in ("public", "fresh", "owned")
                }
                cpus = {
                    label: statistics.median(
                        sum(t["cpu_ns"] for t in row["per_generation"][:63])
                        + row["init_cpu_ns"]
                        for row in rows if row["variant"] == label
                    ) for label in ("public", "fresh", "owned")
                }
                a, b, c = medians["public"], medians["fresh"], medians["owned"]
                assert a > 0 and b > 0 and c > 0
                saved = (a-b)/(a-c) if a > c else None
                receipt["cases"][key].update(
                    status="COMPLETE", medians_63_wall_ns=medians,
                    medians_63_cpu_ns=cpus, fresh_over_owned=b/c,
                    fresh_over_public=b/a, fraction_avoidable_saved=saved,
                    physical_sha_parity_64_of_64=True,
                    donor_route_admitted=True,
                    statement="RESEARCH_ONLY_NO_MULTIWRITER_PRODUCT_CREDIT")
                save()
        receipt["status"] = "COMPLETE"
        cases = list(receipt["cases"].values())
        if all(c["fresh_over_owned"] <= 2 and
               c["fraction_avoidable_saved"] is not None and
               c["fraction_avoidable_saved"] >= .75 for c in cases):
            receipt["decision"] = "PREFER_SIMPLE_FRESH_READER_RESEARCH_ROUTE"
        elif any(c["fresh_over_owned"] > 4 for c in cases):
            receipt["decision"] = "OWNED_SESSION_REMAINS_MATERIALLY_FASTER"
        else:
            receipt["decision"] = "TRADEOFF_AMBIGUOUS"
        save()
    except BaseException as exc:
        receipt["status"], receipt["error"] = "FAILED", repr(exc)
        save()
        raise
    print("J24G83 final", receipt["decision"], flush=True)


if __name__ == "__main__":
    main()
