"""O192: prospective bounded 2Q admission falsifier. Simulation, NEVER Reader product evidence."""
from __future__ import annotations
import json
from collections import OrderedDict, defaultdict
from o188_cache_admission_oracle import LRU, Pin, Guard, NoCache
MIB=1<<20
CAP=64*MIB
KEY_CAP=32768
META=128  # modeled metadata; Python heap RSS unmeasured
COLD_MAX=16*MIB
HOT_MAX=48*MIB
GHOST_MAX=64

class ChargedLRU:
    def __init__(self): self.store=OrderedDict(); self.bytes=0
    def access(self,k,size):
        if k in self.store:
            self.store.move_to_end(k)
            return True
        ch=size+META
        if ch>CAP:return False
        while self.store and (self.bytes+ch>CAP or len(self.store)>=KEY_CAP):
            _,v=self.store.popitem(last=False);self.bytes-=v+META
        self.store[k]=size;self.bytes+=ch
        return False
    @property
    def entries(self):return len(self.store)
    def check(self):assert self.bytes==sum(v+META for v in self.store.values())

class SecondTouch:
    """Simpler control: first-touch bypass and ghost; second-touch LRU admission."""
    def __init__(self):self.store=OrderedDict();self.ghost=OrderedDict();self.bytes=0
    @property
    def entries(self):return len(self.store)+len(self.ghost)
    @property
    def charged_bytes(self):return self.bytes+META*len(self.ghost)
    def _prune(self):
        while self.ghost and (len(self.ghost)>GHOST_MAX or self.charged_bytes>CAP or self.entries>KEY_CAP):
            self.ghost.popitem(last=False)
    def access(self,k,size):
        if k in self.store:
            self.store.move_to_end(k);return True
        if k not in self.ghost:
            self.ghost[k]=None;self._prune();return False
        del self.ghost[k]
        ch=size+META
        if ch>CAP:return False
        while self.store and (self.charged_bytes+ch>CAP or self.entries>=KEY_CAP):
            _,v=self.store.popitem(last=False);self.bytes-=v+META
        self.store[k]=size;self.bytes+=ch
        self._prune()
        return False
    def check(self):
        assert self.bytes==sum(v+META for v in self.store.values())
        assert self.charged_bytes<=CAP and self.entries<=KEY_CAP

class TwoQ:
    """Cold FIFO, reuse-proven LRU, bounded FIFO ghosts. No future/phase knowledge."""
    def __init__(self):
        self.cold=OrderedDict();self.hot=OrderedDict();self.ghost=OrderedDict()
        self.cold_bytes=self.hot_bytes=self.ghost_bytes=0
        self.evictions=0
    @property
    def bytes(self):return self.cold_bytes+self.hot_bytes+self.ghost_bytes
    @property
    def entries(self):return len(self.cold)+len(self.hot)+len(self.ghost)
    def _drop_ghost(self):
        if self.ghost:
            self.ghost.popitem(last=False);self.ghost_bytes-=META
    def _trim_ghost(self):
        while self.ghost and (len(self.ghost)>GHOST_MAX or self.entries>KEY_CAP or self.bytes>CAP):
            self._drop_ghost()
    def _ghost(self,k):
        if k in self.ghost:self.ghost.move_to_end(k)
        else:self.ghost[k]=None;self.ghost_bytes+=META
        self._trim_ghost()
    def _evict_cold(self):
        k,v=self.cold.popitem(last=False)
        self.cold_bytes-=v+META;self.evictions+=1;self._ghost(k)
    def _evict_hot(self):
        _,v=self.hot.popitem(last=False)
        self.hot_bytes-=v+META;self.evictions+=1
    def _admit_hot(self,k,size):
        ch=size+META
        if ch>HOT_MAX:return False
        while self.hot and (self.hot_bytes+ch>HOT_MAX or self.bytes+ch>CAP or self.entries>=KEY_CAP):
            self._evict_hot()
        while self.ghost and (self.bytes+ch>CAP or self.entries>=KEY_CAP):
            self._drop_ghost()
        if self.bytes+ch>CAP or self.entries>=KEY_CAP:return False
        self.hot[k]=size;self.hot_bytes+=ch
        return True
    def _admit_cold(self,k,size):
        ch=size+META
        if ch>COLD_MAX:return
        while self.cold and (self.cold_bytes+ch>COLD_MAX or self.bytes+ch>CAP or self.entries>=KEY_CAP):
            self._evict_cold()
        while self.ghost and (self.bytes+ch>CAP or self.entries>=KEY_CAP):
            self._drop_ghost()
        if self.bytes+ch<=CAP and self.entries<KEY_CAP:
            self.cold[k]=size;self.cold_bytes+=ch
    def access(self,k,size):
        if k in self.hot:
            self.hot.move_to_end(k);return True
        if k in self.cold:
            old=self.cold[k]
            if old+META<=HOT_MAX:
                del self.cold[k];self.cold_bytes-=old+META
                if not self._admit_hot(k,old):self._admit_cold(k,old)
            return True
        if k in self.ghost:
            del self.ghost[k];self.ghost_bytes-=META
            if not self._admit_hot(k,size):self._admit_cold(k,size)
            return False
        self._admit_cold(k,size)
        return False
    def check(self):
        assert not (set(self.cold)&set(self.hot) or set(self.cold)&set(self.ghost) or set(self.hot)&set(self.ghost))
        assert self.cold_bytes==sum(v+META for v in self.cold.values())
        assert self.hot_bytes==sum(v+META for v in self.hot.values())
        assert self.ghost_bytes==len(self.ghost)*META
        assert self.cold_bytes<=COLD_MAX and self.hot_bytes<=HOT_MAX
        assert len(self.ghost)<=GHOST_MAX and 0<=self.bytes<=CAP and 0<=self.entries<=KEY_CAP

def traces():
    yield 'forward96',[(f'R{k}',MIB,1,f'pass{p}') for p in range(1,4) for k in range(96)]
    yield 'reverse96',[(f'R{k}',MIB,1,'ascending') for k in range(96)]+[(f'R{k}',MIB,1,'descending') for k in reversed(range(96))]
    yield 'fit48',[(f'R{k}',MIB,1,f'pass{p}') for p in range(1,4) for k in range(48)]
    yield 'phase_B48', ([(f'A{k}',MIB,1,f'A{p}') for p in range(1,3) for k in range(96)]
         +[(f'B{k}',MIB,1,f'B{p}') for p in range(1,5) for k in range(48)])
    yield 'hot16',([(f'H{k}',MIB,1,'warmup') for k in range(16)]
       +[e for p in range(1,4) for e in ([(f'H{k}',MIB,1,f'wave{p}') for k in range(16)]
       +[(f'S{p}:{k}',MIB,1,f'wave{p}') for k in range(96)])])
    yield 'vzip_proxy',[e for p in range(1,5) for e in ([(f'V{k}',4*MIB,32,f'wave{p}') for k in range(8)]
         +[(f'W{p}:{k}',MIB,1,f'wave{p}') for k in range(96)])]
    yield 'cold512',[(f'C{k}',MIB,1,'cold') for k in range(512)]
    yield 'zero40000',[(f'Z{k}',0,1,'zero') for k in range(40000)]

def measure(trace,ctor):
    c=ctor()
    phases=defaultdict(lambda:{'hits':0,'misses':0,'proxy_refetch_units':0})
    peak=peak_keys=0
    for i,(k,size,cost,phase) in enumerate(trace):
        hit=c.access(k,size)
        row=phases[phase]
        row['hits' if hit else 'misses']+=1
        if not hit:row['proxy_refetch_units']+=cost
        charge=getattr(c,'charged_bytes',None)
        if charge is None:charge=c.bytes
        peak=max(peak,charge);peak_keys=max(peak_keys,c.entries)
        assert charge<=CAP and c.entries<=KEY_CAP
        if i%113==0 or i==len(trace)-1:
            if hasattr(c,'check'):c.check()
    return {'phases':dict(phases),'hits':sum(v['hits'] for v in phases.values()),
      'misses':sum(v['misses'] for v in phases.values()),
      'proxy_refetch_units':sum(v['proxy_refetch_units'] for v in phases.values()),
      'peak_model_bytes_or_legacy_payload_bytes':peak,'peak_keys':peak_keys,
      'final_model_bytes_or_legacy_payload_bytes':getattr(c,'charged_bytes',c.bytes),
      'evictions':getattr(c,'evictions',None)}

def main():
    policies={'historical_lru_payload_only':LRU,'historical_fixed_pin_payload_only':Pin,
      'historical_guard_payload_only':Guard,'no_cache':NoCache,
      'charged_lru':ChargedLRU,'simple_two_touch':SecondTouch,'two_queue_2q':TwoQ}
    data={'schema':'cmpct-o192-twoqueue-model-v1','evidence_tier':'cache simulator; not physical Reader',
      'original_controls':'unmodified O188 historical source','budget_bytes':CAP,
      'model_metadata_bytes_per_key':META,'max_entries_including_ghosts':KEY_CAP,'traces':{}}
    for name,events in traces():
        data['traces'][name]={p:measure(events,ctor) for p,ctor in policies.items()}
    def h(t,p,phase):return data['traces'][t][p]['phases'][phase]['hits']
    conditions={'forward_pass2_ge32':h('forward96','two_queue_2q','pass2')>=32,
      'reverse_ge56':h('reverse96','two_queue_2q','descending')>=56,
      'B48_pass2_ge40':h('phase_B48','two_queue_2q','B2')>=40,
      'fit48_pass2_eq48':h('fit48','two_queue_2q','pass2')==48}
    data['prospective_conditions']=conditions
    data['decision']='PASSES_LOWER_RUNG_FILTER_ONLY' if all(conditions.values()) else 'TWO_QUEUE_CONFIG_FALSIFIED_FOR_GENERIC_ADOPTION'
    print(json.dumps(data,sort_keys=True,indent=2))
if __name__=='__main__':main()
