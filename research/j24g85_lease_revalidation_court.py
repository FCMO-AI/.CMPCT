#!/usr/bin/env python3
"""J24G85: cooperating per-append POSIX lease + external-change invalidation.
Research only: no shipping cache, lease, product API, format, or release change.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import msgpack
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from cmpct import transactions as tx
from j24g80_owned_writer_session import make_base, select, sha_file

ROOT = Path(__file__).resolve().parents[1]
PARENT = "bcbb377dffdcc1ccae1c8510b3abb8bc89233098"
PREREG = "0ff99f93063b059e1b2d08d54a667b9125f641dc"
PRODUCT = {
    "src/cmpct/transactions.py": "71bbc8a989d1da79d0f0dbe44f7f5c39f3304854",
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
}
CASES = ((8192, "middle"), (32768, "tail"))
ORDER = (("public", 0), ("cached", 0), ("cached", 1), ("public", 1))
EXTERNAL = {17: ("f00001.dat", "external-f00001.dat"),
            44: ("f00002.dat", "external-f00002.dat")}


def attest():
    assert sys.platform.startswith("linux"), "POSIX Linux-only scoped court"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for ancestor in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                       cwd=ROOT, check=True)
    for path, expected in PRODUCT.items():
        got = subprocess.check_output(["git", "rev-parse", "HEAD:" + path],
                                      cwd=ROOT, text=True).strip()
        assert got == expected, (path, got, expected)
    import cmpct.transactions as installed
    assert Path(installed.__file__).read_bytes().replace(b"\r\n", b"\n") == (
        ROOT / "src/cmpct/transactions.py").read_bytes().replace(b"\r\n", b"\n")
    return dict(head=head, parent=PARENT, prereg=PREREG, product_blobs=PRODUCT)


@contextlib.contextmanager
def lease(path):
    fd = os.open(path, os.O_RDWR | os.O_APPEND)
    acquired = False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        acquired = True
        # A pathname rebound to another inode invalidates THIS narrow harness.
        f = os.fstat(fd)
        p = os.stat(path)
        assert (f.st_dev, f.st_ino) == (p.st_dev, p.st_ino), "path/inode divergence"
        yield fd
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def snapshot(path, fd):
    with CMPCT(path) as ar:
        idx = msgpack.unpackb(msgpack.packb(ar.index, use_bin_type=True), raw=False)
        prev, depth = ar.latest_footer_pos, ar.delta_depth
    st = os.fstat(fd)
    return dict(index=idx, prev=prev, depth=depth,
                dev=st.st_dev, ino=st.st_ino, size=st.st_size,
                live={row[0] for row in idx["files"]})


def cached_append(path, fd, name, owner):
    st = os.fstat(fd)
    if owner["state"] is None:
        owner["state"] = snapshot(path, fd)
        owner["initial_loads"] += 1
    else:
        s = owner["state"]
        assert (st.st_dev, st.st_ino) == (s["dev"], s["ino"]), "inode replacement"
        if st.st_size != s["size"]:
            assert st.st_size > s["size"], "not append-only cooperative history"
            owner["state"] = snapshot(path, fd)
            owner["external_refreshes"] += 1
    s = owner["state"]
    assert name in s["live"], "deleted/stale member"
    tx._reject_hardlink_owner_mutation(s["index"], name, "delete")
    op = ["del", name]
    tx._index_after_op(s["index"], op)
    checkpoint = s["index"] if s["depth"] >= 63 else None
    next_prev, _ = tx._append_generation(path, {"blobs": [], "ops": [op]},
                                          s["prev"], checkpoint)
    s["prev"] = next_prev
    s["depth"] = 0 if checkpoint is not None else s["depth"] + 1
    s["live"].remove(name)
    post = os.fstat(fd)
    assert (post.st_dev, post.st_ino) == (s["dev"], s["ino"])
    assert post.st_size > st.st_size, "no monotone physical append"
    assert (os.stat(path).st_dev, os.stat(path).st_ino) == (s["dev"], s["ino"])
    s["size"] = post.st_size


def child_external(path, old, new, ready, done):
    ready.write_text("ready\n")
    before = time.perf_counter_ns()
    with lease(path):
        acquired = time.perf_counter_ns()
        tx.append_rename(path, old, new)
    done.write_text(json.dumps(dict(wait_ns=acquired-before,
                                    elapsed_ns=time.perf_counter_ns()-before,
                                    old=old, new=new)) + "\n")


def inject_independent_writer(path, root, case, variant, replicate, generation):
    old, new = EXTERNAL[generation]
    token = f"{case}-{variant}-{replicate}-{generation}"
    ready, done = root / (token + ".ready"), root / (token + ".done")
    cmd = [sys.executable, str(Path(__file__).resolve()), "external",
           str(path), old, new, str(ready), str(done)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        deadline = time.monotonic() + 15
        while not ready.exists() and time.monotonic() < deadline:
            assert proc.poll() is None, "child exited before lease attempt"
            time.sleep(.01)
        assert ready.exists(), "independent child did not attempt lock"
        # Parent still owns LOCK_EX. An actual independent process must not enter.
        time.sleep(.1)
        assert not done.exists() and proc.poll() is None, "external lock did not block"
        return proc, ready, done
    except BaseException:
        proc.kill()
        proc.communicate(timeout=10)
        raise


def finalize_independent_writer(proc, done):
    stdout, stderr = proc.communicate(timeout=120)
    assert proc.returncode == 0, ("external Writer failed", stdout, stderr)
    assert done.is_file(), "child did not commit"
    return json.loads(done.read_text())


def prove_final(path, base_count, names, root, case, variant, replicate, evidence):
    with CMPCT(path) as ar:
        assert ar.delta_depth == 2, "expected two post-checkpoint deltas"
        expected = {f"f{i:05d}.dat" for i in range(base_count)} - set(names)
        expected -= {"f00001.dat", "f00002.dat"}
        expected |= {"external-f00001.dat", "external-f00002.dat"}
        assert set(ar.by) == expected, "foreign Writer operation lost"
        assert ar.verify() == base_count - 64
        for i in (1, 2):
            assert ar.read(f"external-f{i:05d}.dat") == hashlib.sha256(
                f"j24g80-{base_count}-{i}".encode()).digest()
        index_digest = hashlib.sha256(msgpack.packb(
            ar.index, use_bin_type=True)).hexdigest()
    p = preflight_archive(path)
    assert p["files"] == base_count - 64 and p["delta_depth"] == 2
    corrupt = root / f"{case}-{variant}-{replicate}-damaged.cmpct"
    raw = bytearray(path.read_bytes())
    raw[-1] ^= 0xA5
    corrupt.write_bytes(raw)
    with CMPCT(corrupt) as ar:
        assert ar.delta_depth == 1
        assert len(ar.by) == base_count - 63
        assert names[-1] in ar.by
        assert ar.verify() == base_count - 63
    if replicate == 0:
        shutil.copyfile(path, evidence / f"j24g85-{case}-{variant}-valid.cmpct")
        shutil.copyfile(corrupt, evidence / f"j24g85-{case}-{variant}-corrupt-tail.cmpct")
    return index_digest


def trial(root, evidence, progress, base, n, where, names, variant, replicate):
    case = f"{n}-{where}"
    path = root / f"{case}-{variant}-{replicate}.cmpct"
    shutil.copyfile(base, path)
    assert sha_file(path) == sha_file(base)
    owner = dict(state=None, initial_loads=0, external_refreshes=0)
    local, physical, children = [], [], []
    for gen, name in enumerate(names, 1):
        proc = done = None
        start, cpu = time.perf_counter_ns(), time.process_time_ns()
        with lease(path) as fd:
            if variant == "public":
                tx.append_delete(path, name)
            else:
                cached_append(path, fd, name, owner)
            wall, cpu_elapsed = time.perf_counter_ns()-start, time.process_time_ns()-cpu
            local.append(dict(generation=gen, wall_ns=wall, cpu_ns=cpu_elapsed))
            # Receipt before the lock is released: otherwise the independent
            # subprocess could commit before this delete-prefix SHA is captured.
            # Both arms pay identical receipt work outside the timed mutation.
            physical.append(dict(operation="del", generation=gen,
                                 sha256=sha_file(path), bytes=path.stat().st_size))
            if gen in EXTERNAL:
                proc, _, done = inject_independent_writer(
                    path, root, case, variant, replicate, gen)
        if proc is not None:
            child = finalize_independent_writer(proc, done)
            children.append(dict(after_generation=gen, **child))
            physical.append(dict(operation="external_rename", after_generation=gen,
                                 sha256=sha_file(path), bytes=path.stat().st_size))
        with progress.open("a") as p:
            p.write(json.dumps(dict(case=case, variant=variant, replicate=replicate,
                                    generation=gen, last=physical[-1])) + "\n")
    assert len(local) == 64 and len(physical) == 66 and len(children) == 2
    if variant == "cached":
        assert owner["initial_loads"] == 1 and owner["external_refreshes"] == 2, owner
    final_index = prove_final(path, n, names, root, case, variant, replicate, evidence)
    return dict(variant=variant, replicate=replicate, per_generation=local,
                physical=physical, external_children=children,
                initial_loads=owner["initial_loads"],
                external_refreshes=owner["external_refreshes"],
                final_index_sha256=final_index,
                final_sha256=sha_file(path), final_bytes=path.stat().st_size,
                checkpoint64_and_two_post_deltas=True,
                corrupt_tail_recovery=True)


def main():
    evidence = Path(os.getenv("J24G85_EVIDENCE_DIR", "evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    result_path, progress = evidence / "j24g85-result.json", evidence / "j24g85-progress.jsonl"
    result = dict(schema="cmpct-j24g85-cooperative-lease-revalidation-v1",
                  status="RUNNING", decision="UNMEASURED",
                  source=attest(), host=platform.platform(),
                  product_credit=0, safety_credit=0, cases={})
    def save():
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    save()
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g85-") as td:
            root = Path(td)
            for n, where in CASES:
                case = f"{n}-{where}"
                base, builder_ns = make_base(root, n, where)
                names = select(n, where)
                rows = []
                result["cases"][case] = dict(status="RUNNING", builder_ns=builder_ns,
                                             base_bytes=base.stat().st_size,
                                             base_sha256=sha_file(base), rows=rows)
                save()
                for variant, replicate in ORDER:
                    row = trial(root, evidence, progress, base, n, where,
                                names, variant, replicate)
                    rows.append(row)
                    save()
                    print("J24G85", case, variant, replicate,
                          sum(x["wall_ns"] for x in row["per_generation"])/1e9, flush=True)
                first = rows[0]
                assert all(r["physical"] == first["physical"] for r in rows), "66 physical prefixes"
                assert all(r["final_sha256"] == first["final_sha256"] for r in rows)
                assert len({r["final_index_sha256"] for r in rows}) == 1
                medians = {
                    v: statistics.median(sum(x["wall_ns"] for x in r["per_generation"])
                                         for r in rows if r["variant"] == v)
                    for v in ("public", "cached")
                }
                cpus = {
                    v: statistics.median(sum(x["cpu_ns"] for x in r["per_generation"])
                                         for r in rows if r["variant"] == v)
                    for v in ("public", "cached")
                }
                speed = medians["public"] / medians["cached"]
                result["cases"][case].update(status="COMPLETE",
                    medians_64_wall_ns=medians, medians_64_cpu_ns=cpus,
                    public_over_cached=speed, h1_6x=speed >= 6,
                    all_66_intermediate_physical_sha_parity=True,
                    independent_process_lock_blocked=True,
                    two_external_writer_refreshes_per_cached_trial=True)
                save()
        result["status"] = "COMPLETE"
        result["decision"] = ("COOPERATIVE_LEASE_REVALIDATION_SEED_SURVIVES"
                              if all(c["h1_6x"] for c in result["cases"].values())
                              else "BELOW_MATERIALITY")
        save()
    except BaseException as error:
        result["status"] = "FAILED"
        result["decision"] = "UNSAFE_OR_EVIDENCE_FAILURE"
        result["error"] = repr(error)
        save()
        raise
    print("J24G85", result["decision"], flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "external":
        _, _, path, old, new, ready, done = sys.argv
        child_external(Path(path), old, new, Path(ready), Path(done))
    else:
        main()
