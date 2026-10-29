"""Opt-in J24M01d full-suite sidecar.

Runs the ORIGINAL inherited test child unchanged; only afterwards performs a
separate fresh-process forensic replay on the same physical archive. The extra
process must never be mistaken for the original child or release-gate evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ORIGINAL_RUN = subprocess.run
INTERCEPTS = []

# Staged child intentionally imports extra stdlib modules before baseline:
# interpret its RSS as a separate experiment, not a proxy for the original.
STAGE_SCRIPT = """
import hashlib,json,os,pathlib,resource,sys
def hwm():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
before=hwm()
from cmpct.reader import CMPCT
import cmpct.reader as imported
after_import=hwm()
p=pathlib.Path(imported.__file__).resolve()
s=p.read_bytes()
blob=hashlib.sha1(b'blob '+str(len(s)).encode()+b'\\0'+s).hexdigest()
with CMPCT(sys.argv[1]) as reader:
  after_open=hwm()
  count=reader.verify()
  after_verify=hwm()
  row=reader.by['large.bin']
  result={'verified':count,'before_import_kib':before,'after_import_kib':after_import,
    'after_open_kib':after_open,'peak_kib':after_verify,'reader_git_blob':blob,
    'reader_path':str(p),'storage_tag':row[6][0],
    'logical_bytes':row[4],'logical_sha256':bytes(row[5]).hex(),
    'extent_bytes':sum(int(x[1]) for x in row[6][1]),
    'cache_entries':len(reader.cache)}
print(json.dumps(result,sort_keys=True))
"""


def _fingerprint_env():
    keys = ("PYTHONPATH", "PYTHONHOME", "PYTHONMALLOC", "PYTHONSAFEPATH",
            "PYTHONSTARTUP", "VIRTUAL_ENV", "COVERAGE_PROCESS_START", "PYTEST_ADDOPTS")
    # Never put potentially private raw environmental values in public artifacts.
    return {k: {"present": k in os.environ,
                "sha256": hashlib.sha256(os.environ.get(k, "").encode()).hexdigest()
                if k in os.environ else None} for k in keys}


def pytest_configure(config):
    out = os.environ.get("J24M01D_OUT")
    if not out:
        return
    Path(out).mkdir(parents=True, exist_ok=True)

    def capture_run(*args, **kwargs):
        command = args[0] if args else kwargs.get("args")
        if not (isinstance(command, (list, tuple)) and len(command) >= 4
                and command[1] == "-c" and isinstance(command[2], str)
                and "reader.verify()" in command[2] and "'peak_kib'" in command[2]
                and str(command[3]).endswith("/large.cmpct")):
            return ORIGINAL_RUN(*args, **kwargs)

        # The original command+kwargs must be passed byte-for-byte unchanged.
        started = time.perf_counter_ns()
        env = _fingerprint_env()
        raw = ORIGINAL_RUN(*args, **kwargs)
        report = {
            "schema": "cmpct-j24m01d-full-suite-original-plus-sidecar-v1",
            "intercept_index": len(INTERCEPTS),
            "original_child_command_sha256":
                hashlib.sha256(command[2].encode()).hexdigest(),
            "original_duration_ms": (time.perf_counter_ns()-started)/1e6,
            "original_exit": raw.returncode,
            "original_stdout": str(raw.stdout)[-4096:],
            "original_stderr": str(raw.stderr)[-4096:],
            "parent_env_sha": env,
            "original_archive_path": str(command[3]),
            "sidecar_separate_child": True,
            "release_credit": 0,
        }
        try:
            archive = Path(command[3])
            data = archive.read_bytes()
            report["physical_archive_bytes"] = len(data)
            report["physical_archive_sha256"] = hashlib.sha256(data).hexdigest()
            shadow_start = time.perf_counter_ns()
            shadow = ORIGINAL_RUN(
                [sys.executable, "-c", STAGE_SCRIPT, str(archive)],
                capture_output=True, text=True, check=False, timeout=100)
            report["sidecar_duration_ms"] = (time.perf_counter_ns()-shadow_start)/1e6
            report["sidecar_exit"] = shadow.returncode
            report["sidecar_stdout"] = shadow.stdout[-4096:]
            report["sidecar_stderr"] = shadow.stderr[-4096:]
            if shadow.returncode == 0:
                report["sidecar_provenance"] = json.loads(shadow.stdout)
        except Exception as e:
            report["sidecar_error"] = repr(e)
        INTERCEPTS.append(report)
        with (Path(out)/"original-child-plus-sidecar.jsonl").open("a") as fh:
            fh.write(json.dumps(report,sort_keys=True)+"\n")
        return raw

    subprocess.run = capture_run


def pytest_unconfigure(config):
    subprocess.run = ORIGINAL_RUN
