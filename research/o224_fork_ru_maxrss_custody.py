#!/usr/bin/env python3
"""O224 independent child RSS custody falsifier (post-prereg causal finding).

Linux getrusage(RUSAGE_SELF).ru_maxrss in a subprocess may include inherited
parent high-water RSS on fork/exec, whereas /proc/self/status:VmHWM describes
the exec'd child's own virtual-memory image. The test is deliberately separate
from the Reader and from the O224 preregistered phase classifier.
"""
import argparse
import gc
import json
import os
from pathlib import Path
import resource
import subprocess
import sys


def measurement():
    fields = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:", "VmPeak:")):
            key, val = line.split(":", 1)
            fields[key + "_kib"] = int(val.strip().split()[0])
    fields["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fields["pid"] = os.getpid()
    return fields


def run():
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child"]
    def child():
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(proc.stdout)
    before = child()
    allocation = bytearray(256 * 1024 * 1024)
    for i in range(0, len(allocation), 4096):
        allocation[i] = 1
    parent_during = measurement()
    after = child()
    del allocation
    gc.collect()
    parent_after = measurement()
    after_release = child()
    rise_in_inherited = after["ru_maxrss_kib"] - before["ru_maxrss_kib"]
    rise_in_true = after["VmHWM_kib"] - before["VmHWM_kib"]
    inference = "RUSAGE_CHILD_INHERITS_PARENT_HWM" if (
        rise_in_inherited >= 128 * 1024 and
        abs(rise_in_true) <= 64 * 1024 and
        after_release["ru_maxrss_kib"] >= after["ru_maxrss_kib"] - 16384
    ) else "INCONCLUSIVE_ON_THIS_HOST"
    result = {
        "schema": "o224-linux-fork-hwm-custody-v1",
        "baseline_child": before, "parent_with_256m": parent_during,
        "child_after_parent_allocation": after,
        "parent_after_release": parent_after,
        "child_after_release": after_release,
        "difference_ru_maxrss_kib": rise_in_inherited,
        "difference_proc_vmhwm_kib": rise_in_true,
        "classification": inference,
        "evidence_tier": "posthoc independently replicated kernel/process metric mechanism",
        "warning": "ru_maxrss is unfit as sole per-exec child-memory causal measure when parent RSS changes",
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.child:
        print(json.dumps(measurement(), sort_keys=True))
    else:
        result = run()
        rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered)
        print(rendered)
