"""O188: deterministic offline cache-admission policy falsifier; NOT CMPCT product code.
All algorithms see current accesses only, never phase labels or future trace.
Synthetic refetch-work weights are NOT Reader CPU measurements.
"""
from __future__ import annotations
import json
from collections import OrderedDict, defaultdict

MIB = 1 << 20
CAP = 64 * MIB
KEY_CAP = 32768

class LRU:
    def __init__(self):
        self.store = OrderedDict()
        self.bytes = 0
    def access(self, k, size):
        if k in self.store:
            self.store.move_to_end(k)
            return True
        if size <= CAP:
            while self.store and (self.bytes + size > CAP or len(self.store) >= KEY_CAP):
                _, old = self.store.popitem(last=False)
                self.bytes -= old
            self.store[k] = size
            self.bytes += size
        return False
    @property
    def entries(self): return len(self.store)

class Pin:
    def __init__(self):
        self.store = {}
        self.bytes = 0
    def access(self, k, size):
        if k in self.store: return True
        if self.bytes + size <= CAP and len(self.store) < KEY_CAP:
            self.store[k] = size
            self.bytes += size
        return False
    @property
    def entries(self): return len(self.store)

class Guard:
    """Exploratory fixed 48/16 protected/probation and 128-miss decay, not tuned."""
    def __init__(self):
        self.protected = OrderedDict()
        self.probation = OrderedDict()
        self.pbytes = 0
        self.qbytes = 0
        self.misses_without_protected_hit = 0
        self.resets = 0
    def access(self, k, size):
        if k in self.protected:
            self.protected.move_to_end(k)
            self.misses_without_protected_hit = 0
            return True
        if k in self.probation:
            self.probation.move_to_end(k)
            return True
        self.misses_without_protected_hit += 1
        if self.misses_without_protected_hit >= 128:
            self.protected.clear(); self.probation.clear()
            self.pbytes = self.qbytes = 0
            self.misses_without_protected_hit = 0
            self.resets += 1
        if self.pbytes + size <= 48 * MIB and len(self.protected) < 24576:
            self.protected[k] = size
            self.pbytes += size
        elif size <= 16 * MIB:
            while self.probation and (self.qbytes + size > 16 * MIB or len(self.probation) >= 8192):
                _, old = self.probation.popitem(last=False)
                self.qbytes -= old
            self.probation[k] = size
            self.qbytes += size
        return False
    @property
    def entries(self): return len(self.protected) + len(self.probation)
    @property
    def bytes(self): return self.pbytes + self.qbytes

class NoCache:
    bytes = 0
    entries = 0
    def access(self, k, size): return False


def traces():
    yield 'scan96', [(f'R{k}', MIB, 1, f'pass{p}') for p in range(1,4) for k in range(96)]
    yield 'fit48', [(f'R{k}', MIB, 1, f'pass{p}') for p in range(1,4) for k in range(48)]
    hot = [(f'H{k}', MIB, 1, 'warm') for k in range(16)]
    for p in range(1,4):
        hot += [(f'H{k}', MIB, 1, f'wave{p}') for k in range(16)]
        hot += [(f'S{p}:{k}', MIB, 1, f'wave{p}') for k in range(96)]
    yield 'hot16_scan96', hot
    yield 'phase_shift96', ([(f'A{k}', MIB, 1, f'A{p}') for p in range(1,3) for k in range(96)] +
                           [(f'B{k}', MIB, 1, f'B{p}') for p in range(1,5) for k in range(96)])
    yield 'streaming_unique', [(f'U{k}', MIB, 1, 'stream') for k in range(512)]
    weighted = []
    for p in range(1,5):
        weighted += [(f'V{k}', 4 * MIB, 32, f'wave{p}') for k in range(8)]
        weighted += [(f'W{p}:{k}', MIB, 1, f'wave{p}') for k in range(96)]
    yield 'mixed_weighted', weighted
    yield 'tiny_items', [(f'Z{k}', 0, 1, 'tiny') for k in range(40000)]


def measure(trace, cls):
    cache = cls()
    phases = defaultdict(lambda: {'hits':0, 'misses':0, 'refetch_work_units':0})
    peak_bytes = peak_entries = 0
    for request_no, (key, size, cost, phase) in enumerate(trace):
        hit = cache.access(key,size)
        row = phases[phase]
        if hit: row['hits'] += 1
        else: row['misses'] += 1; row['refetch_work_units'] += cost
        peak_bytes = max(peak_bytes, cache.bytes)
        peak_entries = max(peak_entries, cache.entries)
        assert 0 <= cache.bytes <= CAP and 0 <= cache.entries <= KEY_CAP
        if request_no % 101 == 0 or request_no == len(trace)-1:
            if hasattr(cache, 'protected'):
                assert cache.bytes == sum(cache.protected.values()) + sum(cache.probation.values())
            elif hasattr(cache, 'store'):
                assert cache.bytes == sum(cache.store.values())
    return {'phases':dict(phases), 'peak_retained_bytes':peak_bytes,
            'peak_entries':peak_entries, 'final_retained_bytes':cache.bytes,
            'resets':getattr(cache,'resets',0),
            'hits':sum(x['hits'] for x in phases.values()),
            'misses':sum(x['misses'] for x in phases.values()),
            'refetch_work_units':sum(x['refetch_work_units'] for x in phases.values())}


def main():
    policies={'lru':LRU,'fixed_pin':Pin,'guard_48_16':Guard,'no_cache':NoCache}
    result={'schema':'cmpct-o188-policy-oracle-v1',
            'evidence_tier':'deterministic policy simulation, NOT physical Reader performance',
            'capacity_bytes':CAP,'max_entries':KEY_CAP,'families':{}}
    for name, events in traces():
        result['families'][name]={p:measure(events,c) for p,c in policies.items()}
    scan=result['families']['scan96']
    assert scan['lru']['phases']['pass2']['hits']==0
    assert scan['guard_48_16']['phases']['pass2']['hits']>=48
    assert scan['fixed_pin']['phases']['pass2']['hits']==64
    assert scan['guard_48_16']['phases']['pass3']['hits']>=48
    assert result['families']['fit48']['guard_48_16']['hits']==result['families']['fit48']['lru']['hits']==96
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__': main()
