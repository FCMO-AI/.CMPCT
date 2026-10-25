#!/usr/bin/env python3
"""O77: Linux openat2 root confinement versus safe per-component dirfd walk.

Research primitive only; NOT a replacement for CMPCT Builder.scan or a snapshot.
Preregistration: docs/v031-research/2026-10-25-o77-openat2-rooted-source-prereg.md
"""
from __future__ import annotations
import ctypes, errno, hashlib, json, os, platform, random, stat, statistics, tempfile, time
from pathlib import Path

NR = {"x86_64": 437, "aarch64": 437, "riscv64": 437}
ARCH = platform.machine()
if platform.system() != "Linux" or ARCH not in NR:
    raise SystemExit("UNSUPPORTED_PLATFORM")
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.syscall.restype = ctypes.c_long
class How(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_uint64), ("mode", ctypes.c_uint64),
                ("resolve", ctypes.c_uint64)]
OPEN_FLAGS = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK

def one_call(rootfd, rel):
    how = How(OPEN_FLAGS, 0, 0x08 | 0x04)  # RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS
    fd = LIBC.syscall(NR[ARCH], ctypes.c_int(rootfd),
                      ctypes.c_char_p(os.fsencode(rel)), ctypes.byref(how),
                      ctypes.c_size_t(ctypes.sizeof(how)))
    if fd < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e), rel)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "non-regular source", rel)
        return int(fd)
    except BaseException:
        os.close(fd)
        raise

def walked(rootfd, rel):
    segments = os.fsencode(rel).split(b"/")
    if not segments or any(p in (b"", b".", b"..") for p in segments):
        raise OSError(errno.EINVAL, "unsafe lexical path", rel)
    parent = rootfd
    try:
        for seg in segments[:-1]:
            fd = os.open(seg, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            if parent != rootfd:
                os.close(parent)
            parent = fd
        fd = os.open(segments[-1], OPEN_FLAGS | os.O_NOFOLLOW, dir_fd=parent)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError(errno.EINVAL, "non-regular source", rel)
            return fd
        except BaseException:
            os.close(fd)
            raise
    finally:
        if parent != rootfd:
            os.close(parent)

def main():
    report = {"episode": "O77", "prereg_commit": "4ebe7a3f4c5eb190006caeab8159778c75fe86ab",
              "platform": platform.platform(), "kernel": platform.release(),
              "arch": ARCH, "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "tests": [], "micro": {}}
    with tempfile.TemporaryDirectory(prefix="cmpct-o77-") as tmp:
        base = Path(tmp); root = base / "selected"; root.mkdir()
        outside = base / "outside"; outside.mkdir()
        (outside / "payload").write_bytes(b"NEVER-ADMIT-EXTERNAL")
        positives = {"plain.bin": b"HELLO", "dir/leaf.bin": b"GOOD",
                     "d1/d2/d3/data": b"DEEP", "unicode-\u00e9/\u03b4.bin": b"UNICODE"}
        for rel, val in positives.items():
            f = root / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(val)
        os.symlink(outside / "payload", root / "final-link")
        os.symlink(outside, root / "intermediate-link")
        os.mkfifo(root / "pipe")
        rootfd = os.open(root, os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for name, openfn in (("openat2", one_call), ("component", walked)):
                for rel, expected in positives.items():
                    fd = openfn(rootfd, rel)
                    try:
                        got = os.read(fd, 1024)
                        st = os.fstat(fd)
                    finally:
                        os.close(fd)
                    assert got == expected, (name, rel)
                    assert st.st_ino == os.stat(root / rel).st_ino
                    report["tests"].append({"case": name + ":positive:" + rel, "PASS": True,
                                            "sha256": hashlib.sha256(got).hexdigest()})
                for rel in ("final-link", "intermediate-link/payload", "../outside/payload", "pipe"):
                    start = time.perf_counter()
                    try:
                        fd = openfn(rootfd, rel)
                    except OSError as e:
                        elapsed = time.perf_counter() - start
                        assert elapsed < 1.0, (name, rel, elapsed)
                        report["tests"].append({"case": name + ":reject:" + rel, "PASS": True,
                                                "errno": e.errno, "elapsed_s": elapsed})
                    else:
                        os.close(fd)
                        raise AssertionError("unsafe object admitted: " + name + " " + rel)
            fd = one_call(rootfd, "plain.bin")
            try:
                (root / "plain.bin").write_bytes(b"MUTATED-AFTER-OPEN")
                os.lseek(fd, 0, os.SEEK_SET)
                observed = os.read(fd, 1024)
                assert observed == b"MUTATED-AFTER-OPEN"
                report["tests"].append({"case": "after-open same-inode mutation NEGATIVE", "PASS": True,
                                        "observed": observed.decode(), "snapshot_claim": False})
            finally:
                os.close(fd)
            # Paired randomized trials: same source, same I/O operation; no process startup.
            for depth in (1, 4, 8):
                folder = root
                for n in range(depth - 1):
                    folder = folder / ("level" + str(n))
                    folder.mkdir(exist_ok=True)
                f = folder / "measured.bin"; f.write_bytes(b"MEASURED-DATA")
                rel = str(f.relative_to(root))
                arms = {"openat2": one_call, "component": walked}
                trials = {k: [] for k in arms}
                rng = random.Random(66077 + depth)
                for rep in range(7):
                    order = list(arms)
                    rng.shuffle(order)
                    for name in order:
                        cpu0 = time.process_time_ns(); wall0 = time.perf_counter_ns()
                        for _ in range(250):
                            handle = arms[name](rootfd, rel)
                            try:
                                assert os.read(handle, 1) == b"M"
                            finally:
                                os.close(handle)
                        trials[name].append({
                            "wall_ns_per_open": (time.perf_counter_ns() - wall0) / 250,
                            "cpu_ns_per_open": (time.process_time_ns() - cpu0) / 250})
                one = statistics.median(x["wall_ns_per_open"] for x in trials["openat2"])
                walk = statistics.median(x["wall_ns_per_open"] for x in trials["component"])
                report["micro"][str(depth)] = {
                    "path": rel, "samples": trials, "component_to_openat2_median_wall_ratio": walk/one}
        finally:
            os.close(rootfd)
    report["status"] = "PASS"
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
