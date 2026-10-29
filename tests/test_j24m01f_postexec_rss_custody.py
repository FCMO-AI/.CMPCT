"""J24M01f: Linux fork/exec RSS metric attribution, independent of CMPCT.

The donor #549 / #453 observed this class before. This targeted control proves the
original J24V01 resource evaluator cannot use inherited ru_maxrss as a child's
post-exec peak. It deliberately does not import CMPCT or modify its production code.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc VmHWM only")
def test_new_child_vmhwm_excludes_parent_preexec_highwater() -> None:
    # Run the parent allocator in ANOTHER process, so this positive control does
    # not leave high-water memory in pytest and cannot bias later product tests.
    parent_script = """
import json,resource,subprocess,sys
buffer=bytearray(160*1024*1024)
for offset in range(0,len(buffer),4096):
    buffer[offset]=0xA5
del buffer
parent_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
child_script = '''
import json,resource
from pathlib import Path
line=next((x for x in Path('/proc/self/status').read_text().splitlines()
           if x.startswith('VmHWM:')), None)
if line is None or len(line.split())!=3 or line.split()[2]!='kB':
    raise RuntimeError('missing post-exec VmHWM')
print(json.dumps({'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'vmhwm_kib':int(line.split()[1])}))
'''
child=subprocess.run([sys.executable,'-c',child_script],
                     capture_output=True,text=True,timeout=15,check=True)
print(json.dumps({'parent_peak_kib':parent_peak,'child':json.loads(child.stdout)}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", parent_script],
        capture_output=True,
        text=True,
        timeout=40,
        check=True,
    )
    data = json.loads(proc.stdout)
    parent_kib = data["parent_peak_kib"]
    inherited_kib = data["child"]["ru_maxrss_kib"]
    postexec_kib = data["child"]["vmhwm_kib"]

    assert postexec_kib > 0, data
    # Source-bound kernel control: an artificially high parent allocation must
    # not be mistaken for memory consumed after exec by the independent child.
    assert parent_kib >= 160 * 1024, data
    # Linux may report slightly different historical peaks for parent and child:
    # exact parent<=child equivalence is not the causal requirement. Instead
    # prove BOTH truly large inherited child high-water and small post-exec RSS.
    assert inherited_kib >= 160 * 1024, data
    assert postexec_kib < 128 * 1024, data
    assert inherited_kib - postexec_kib >= 32 * 1024, data


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc resident measurement only")
def test_true_postexec_spike_exceeds_unmodified_128m_limit() -> None:
    """Negative control: a real child spike must trip the SAME strict 128-MiB gate.

    Prospectively registered in J24M01h before implementation. Keep the
    allocation in a separate process, not in pytest or the CMPCT verifier.
    """
    script = """
import json,os
from pathlib import Path
def read_metric(metric):
    matches=[line.split() for line in Path('/proc/self/status').read_text().splitlines()
             if line.startswith(metric+':')]
    if len(matches)!=1 or len(matches[0])!=3 or matches[0][2]!='kB':
        raise RuntimeError('invalid /proc '+metric+': '+repr(matches))
    value=int(matches[0][1])
    if value<=0:
        raise RuntimeError('nonpositive /proc '+metric)
    return value
before=read_metric('VmHWM')
# Materialize resident pages, not merely a virtual address reservation.
resident=bytearray(160*1024*1024)
for offset in range(0,len(resident),4096):
    resident[offset]=0xA5
peak=read_metric('VmHWM')
rss=read_metric('VmRSS')
statm_pages=int(Path('/proc/self/statm').read_text().split()[1])
statm_kib=statm_pages*os.sysconf('SC_PAGE_SIZE')//1024
print(json.dumps({'before_kib':before,'peak_kib':peak,'rss_kib':rss,
                  'statm_kib':statm_kib,'touched_bytes':len(resident)}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=40,
        check=True,
    )
    data = json.loads(proc.stdout)
    ceiling = 128 * 1024
    assert data["touched_bytes"] == 160 * 1024 * 1024, data
    assert data["peak_kib"] - data["before_kib"] >= ceiling, data
    assert data["rss_kib"] >= ceiling and data["statm_kib"] >= ceiling, data
    # Contemporaneous RSS and resident statm pages are different kernel views.
    assert abs(data["rss_kib"] - data["statm_kib"]) <= 8 * 1024, data
    assert data["peak_kib"] >= data["rss_kib"], data
    # Exact same strict predicate used by original sparse verifier: this MUST fail.
    assert not (data["peak_kib"] < ceiling), data
