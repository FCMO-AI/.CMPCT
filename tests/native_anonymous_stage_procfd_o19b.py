#!/usr/bin/env python3
"""O19b independent host probe, NOT a CMPCT product or security regression test.

Does O_TMPFILE hide a pathname but remain openable to a same-UID child via
/proc/<pid>/fd/<fd> on the actual CI kernel? Record denial/unsupported honestly.
"""
import ctypes
import errno
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

AT_EMPTY_PATH = 0x1000

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_anonymous_stage_procfd_o19b.py RESULT.json")
    receipt_path = Path(sys.argv[1]).resolve()
    result = {
        "schema": "cmpct-o19b-anonymous-stage-procfd-host-v1",
        "os": platform.platform(),
        "uid": os.getuid(),
        "source_head": os.environ.get("EVIDENCE_HEAD", "LOCAL_UNATTESTED"),
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o19b-") as temp:
        root = Path(temp)
        rootfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            try:
                fd = os.open(".", os.O_TMPFILE | os.O_RDWR | os.O_CLOEXEC, 0o600, dir_fd=rootfd)
            except OSError as e:
                result.update(decision="O_TMPFILE_UNSUPPORTED", errno=e.errno)
            else:
                try:
                    assert os.write(fd, b"ABCDEFGH") == 8
                    os.fsync(fd)
                    result["entries_before_publish"] = len(list(root.iterdir()))
                    assert result["entries_before_publish"] == 0
                    procfd = f"/proc/{os.getpid()}/fd/{fd}"
                    child = (
                        "import os,sys\n"
                        "try:\n"
                        " fd=os.open(sys.argv[1],os.O_RDWR)\n"
                        " assert os.pwrite(fd,b'Z',0)==1\n"
                        " os.fsync(fd)\n"
                        " os.close(fd)\n"
                        " print('REOPEN_MUTATION_OK')\n"
                        "except OSError as e:\n"
                        " print('REOPEN_DENIED',e.errno)\n"
                        " sys.exit(3)\n"
                    )
                    p = subprocess.run(
                        [sys.executable, "-c", child, procfd],
                        capture_output=True, text=True, timeout=15,
                    )
                    result["child_exit"] = p.returncode
                    result["child_stdout"] = p.stdout.strip()
                    result["child_stderr"] = p.stderr.strip()
                    result["anonymous_bytes_after_child"] = os.pread(fd, 8, 0).hex()
                    permitted = p.returncode == 0
                    result["same_uid_reopen_mutated"] = permitted
                    assert result["anonymous_bytes_after_child"] == (
                        b"ZBCDEFGH" if permitted else b"ABCDEFGH"
                    ).hex()
                    libc = ctypes.CDLL(None, use_errno=True)
                    rc = libc.linkat(
                        ctypes.c_int(fd), ctypes.c_char_p(b""),
                        ctypes.c_int(rootfd), ctypes.c_char_p(b"final.bin"),
                        ctypes.c_int(AT_EMPTY_PATH),
                    )
                    result["linkat_at_empty_path_rc"] = rc
                    if rc == 0:
                        result["published_bytes"] = (root / "final.bin").read_bytes().hex()
                        assert result["published_bytes"] == result["anonymous_bytes_after_child"]
                        result["decision"] = (
                            "ANONYMOUS_PATHLESS_BUT_SAME_UID_MUTABLE"
                            if permitted else "ANONYMOUS_PROC_FD_REOPEN_DENIED"
                        )
                    else:
                        result["linkat_errno"] = ctypes.get_errno()
                        result["decision"] = "ANONYMOUS_STAGE_LINK_UNSUPPORTED"
                finally:
                    os.close(fd)
        finally:
            os.close(rootfd)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        k: result.get(k) for k in (
            "decision", "uid", "source_head", "entries_before_publish",
            "same_uid_reopen_mutated", "linkat_at_empty_path_rc",
        )
    }, sort_keys=True))

if __name__ == "__main__":
    main()
