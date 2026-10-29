"""J24I15: unsafe-pathname O47 baseline vs HANDLE-BOUND Win32 non-following file open.

Research only. Windows file-handle opens here are NOT a complete descriptor-rooted
source tree; intermediate junctions and mutation of already opened contents remain
out of scope. Preregistration: docs/v031-research/2026-10-29-j24i15-*.md.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import stat
import sys
import tempfile
import time
import traceback
from pathlib import Path

SCHEMA = "j24i15-win32-handle-custody-v1"
ROUNDS = 4


class RejectedSource(OSError):
    """Source is a reparse point, directory, or another prohibited leaf type."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def corpus(root: Path) -> dict[str, list[Path]]:
    unique, linked = root / "unique", root / "linked"
    unique.mkdir()
    linked.mkdir()
    for i in range(256):
        data = hashlib.sha256(f"J24I15-source-{i}".encode()).digest()
        data += hashlib.sha256(f"J24I15-perturb-{i}".encode()).digest()
        (unique / f"independent-{i:04d}.bin").write_bytes(data)
    body = bytes(range(256)) * 16 + b"identical-bytes-are-not-identity"
    owner = linked / "a-owner.bin"
    alias = linked / "b-alias.bin"
    copy = linked / "c-independent-copy.bin"
    owner.write_bytes(body)
    os.link(owner, alias)
    copy.write_bytes(body)
    return {"unique256": sorted(unique.iterdir()), "topology3": [owner, alias, copy]}


def api():
    if os.name != "nt":
        raise OSError("Win32 kernel32 API unavailable; not a product failure")
    import ctypes.wintypes as w

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", w.DWORD), ("high", w.DWORD)]

    class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", w.DWORD),
            ("ftCreationTime", FILETIME), ("ftLastAccessTime", FILETIME),
            ("ftLastWriteTime", FILETIME), ("dwVolumeSerialNumber", w.DWORD),
            ("nFileSizeHigh", w.DWORD), ("nFileSizeLow", w.DWORD),
            ("nNumberOfLinks", w.DWORD), ("nFileIndexHigh", w.DWORD),
            ("nFileIndexLow", w.DWORD)
        ]

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.argtypes = [
        w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD,
        w.DWORD, ctypes.c_void_p
    ]
    k.CreateFileW.restype = ctypes.c_void_p
    k.GetFileInformationByHandle.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)
    ]
    k.GetFileInformationByHandle.restype = w.BOOL
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    k.CloseHandle.restype = w.BOOL
    return k, BY_HANDLE_FILE_INFORMATION


def win32_read_nofollow(path: Path) -> tuple[bytes, dict]:
    """No-follow the *leaf*; identify and read from exactly one kernel handle."""
    k, info_type = api()
    FILE_READ_DATA = 0x0001
    FILE_READ_ATTRIBUTES = 0x0080
    SHARE_READ_WRITE_DELETE = 0x0007
    OPEN_EXISTING = 3
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    handle = k.CreateFileW(
        str(path), FILE_READ_DATA | FILE_READ_ATTRIBUTES,
        SHARE_READ_WRITE_DELETE, None, OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS, None
    )
    invalid = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid:
        raise ctypes.WinError(ctypes.get_last_error())
    ownership_transferred = False
    try:
        info = info_type()
        if not k.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        attrs = int(info.dwFileAttributes)
        if attrs & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY):
            raise RejectedSource("reparse/directory leaf refused without reading")
        identity = (int(info.dwVolumeSerialNumber),
                    (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow))
        links = int(info.nNumberOfLinks)
        size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
        if links < 1:
            raise AssertionError("Win32 source reported invalid link count")
        import msvcrt
        fd = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_BINARY)
        ownership_transferred = True
        with os.fdopen(fd, "rb", closefd=True) as file:
            data = file.read()
        if len(data) != size:
            raise AssertionError("source changed size while reading opened handle")
        return data, {"identity": identity, "nlink": links,
                      "size": size, "attributes": attrs}
    finally:
        if not ownership_transferred:
            k.CloseHandle(handle)


def baseline_read(path: Path) -> tuple[bytes, dict]:
    """Existing O47 physical-identity census followed by ordinary data open."""
    st = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(st.st_mode):
        raise RejectedSource("not a regular leaf")
    with open(path, "rb") as source:
        data = source.read()
    if len(data) != st.st_size:
        raise AssertionError("source size changed")
    return data, {"identity": (int(st.st_dev), int(st.st_ino)),
                  "nlink": int(st.st_nlink), "size": int(st.st_size),
                  "mode": int(st.st_mode)}


def ownership_partition(owners: list[dict]) -> list[int]:
    first = {}
    result = []
    for o in owners:
        ident = tuple(o["identity"])
        if ident not in first:
            first[ident] = len(first)
        result.append(first[ident])
    return result


def measure(paths: list[Path], side: str) -> dict:
    t0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    h = hashlib.sha256()
    owners = []
    total = 0
    for path in paths:
        raw, info = (baseline_read(path) if side == "A"
                     else win32_read_nofollow(path))
        h.update(path.name.encode("utf-8"))
        h.update(len(raw).to_bytes(8, "little"))
        h.update(hashlib.sha256(raw).digest())
        total += len(raw)
        owners.append(info)
    return {"wall_ns": time.perf_counter_ns()-t0,
            "cpu_ns": time.process_time_ns()-cpu0,
            "sha256": h.hexdigest(), "read_bytes": total,
            "owners": owners, "partition": ownership_partition(owners)}


def reject_hostile_leaves(root: Path) -> dict:
    owner = root / "linked" / "a-owner.bin"
    # A link pointing at an actual payload outside the nominated root must never be
    # followed, even if os.stat classified an earlier spelling as a regular file.
    outside = root.parent / f"{root.name}-outside-source.bin"
    outside.write_bytes(b"J24I15 OUTSIDE SECRET MUST NEVER BE READ")
    sym = root / "source-symlink.bin"
    result = {}
    try:
        try:
            sym.symlink_to(outside)
        except OSError as exc:
            raise AssertionError(
                "host cannot create required symlink negative: " + repr(exc)
            )
        st = os.stat(sym, follow_symlinks=False)
        if not stat.S_ISLNK(st.st_mode):
            raise AssertionError("symlink admission control is not a symlink")
        try:
            raw, info = win32_read_nofollow(sym)
        except (RejectedSource, OSError) as exc:
            result["symlink"] = {"rejected": True, "type": type(exc).__name__,
                                 "error": str(exc)}
        else:
            result["symlink"] = {"rejected": False, "sha256": digest(raw), "info": info}
            raise AssertionError("Win32 nofollow candidate READ symlink target")
        d = root / "forbidden-directory"
        d.mkdir()
        try:
            raw, _ = win32_read_nofollow(d)
        except (RejectedSource, OSError) as exc:
            result["directory"] = {"rejected": True, "type": type(exc).__name__}
        else:
            raise AssertionError("Win32 candidate READ a directory as regular")
        # The legitimate ordinary leaf must remain admissible.
        body, info = win32_read_nofollow(owner)
        if not body or info["nlink"] < 2:
            raise AssertionError("nonfollowing ordinary source not readable")
        result["regular_owner"] = {"accepted": True,
                                   "sha256": digest(body), "nlink": info["nlink"]}
    finally:
        if sym.is_symlink():
            sym.unlink()
        outside.unlink(missing_ok=True)
    return result


def run() -> dict:
    result = {
        "schema": SCHEMA, "status": "RUNNING", "product_change": False,
        "release_credit": False, "host": platform.platform(),
        "python": sys.version, "os_name": os.name,
        "head": os.environ.get("CMPCT_J24I15_HEAD", "UNBOUND"),
        "source": "A=os.stat(nofollow)+open; B=Win32 CreateFileW(nofollow leaf)+GetFileInformationByHandle+read",
        "raw": []
    }
    try:
        if os.name != "nt":
            result["status"] = "PLATFORM_UNAVAILABLE"
            return result
        import cmpct
        checkout = Path(os.environ["CMPCT_J24I15_CHECKOUT"]).resolve()
        installed = Path(cmpct.__file__).resolve()
        result["installed_package_path"] = str(installed)
        if installed == checkout or checkout in installed.parents:
            raise AssertionError("instrument imported checkout instead of installed package")
        with tempfile.TemporaryDirectory(prefix="j24i15-") as d:
            root = Path(d)
            groups = corpus(root)
            result["hostile"] = reject_hostile_leaves(root)
            for family, paths in groups.items():
                a = measure(paths, "A")
                b = measure(paths, "B")
                if a["sha256"] != b["sha256"] or a["read_bytes"] != b["read_bytes"]:
                    raise AssertionError("same-source content or byte count changed")
                if a["partition"] != b["partition"]:
                    raise AssertionError("different physical hardlink partition")
                if family == "topology3" and a["partition"] != [0,0,1]:
                    raise AssertionError("true hardlink vs independent copy misclassified")
                if family == "unique256" and len(set(a["partition"])) != 256:
                    raise AssertionError("independent regular files were grouped")
                if [o["nlink"] for o in a["owners"]] != [o["nlink"] for o in b["owners"]]:
                    raise AssertionError("source handle link counts differ from O47")
                result.setdefault("controls", {})[family] = {
                    "files": len(paths), "sha256": a["sha256"],
                    "read_bytes": a["read_bytes"], "ownership_partition": a["partition"],
                    "link_counts": [o["nlink"] for o in a["owners"]]
                }
                for trial in ("AA","AB"):
                    for round_id in range(ROUNDS):
                        seq = ("A","A","A","A") if trial=="AA" else ("A","B","B","A")
                        for index, side in enumerate(seq):
                            observed = measure(paths, side)
                            if (observed["sha256"] != a["sha256"] or
                                observed["partition"] != a["partition"] or
                                observed["read_bytes"] != a["read_bytes"]):
                                raise AssertionError("timed arm changed corpus/physical identity")
                            result["raw"].append({
                                "family": family, "trial": trial, "round": round_id,
                                "index": index, "side": side,
                                "wall_ns": observed["wall_ns"],
                                "cpu_ns": observed["cpu_ns"],
                                "sha256": observed["sha256"],
                                "read_bytes": observed["read_bytes"]
                            })
                paired = []
                for round_id in range(ROUNDS):
                    cell = [r for r in result["raw"] if
                            r["family"]==family and r["trial"]=="AB" and r["round"]==round_id]
                    if [r["side"] for r in cell] != ["A","B","B","A"]:
                        raise AssertionError("ABBA order violated")
                    a_wall = (cell[0]["wall_ns"]+cell[3]["wall_ns"])/2
                    b_wall = (cell[1]["wall_ns"]+cell[2]["wall_ns"])/2
                    paired.append({"round": round_id, "A_wall_ns": a_wall,
                                   "B_wall_ns": b_wall, "B_over_A": b_wall/a_wall})
                result.setdefault("paired", {})[family] = paired
            good = sum(p["B_over_A"] <= 0.90 for p in result["paired"]["unique256"])
            result["rounds_10pct_faster"] = good
            result["status"] = ("SAFE_LEAF_MICRO_CANDIDATE" if good >= 3
                                else "SAFE_LEAF_COST_WIN_FALSIFIED")
            result["decision"] = ("Only consider a future product prototype with root/parent "
                                  "custody, full Builder cost and hostile mutations; no release credit"
                                  if good >= 3 else
                                  "Retire this Win32 leaf-handle speed route at current evidence; "
                                  "preserve O47 and pursue safer architecture without speed claims")
    except BaseException as exc:
        result["status"] = "NONPASS"
        result["error"] = type(exc).__name__ + ": " + str(exc)
        result["traceback"] = traceback.format_exc(limit=12)
        raise
    finally:
        out = Path(os.environ["CMPCT_J24I15_RECEIPT"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                       encoding="utf-8")
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"status": r["status"], "head": r["head"],
                      "paired": r.get("paired")}, sort_keys=True))
