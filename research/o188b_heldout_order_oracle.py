"""O188b: prospectively specified post-O188 adversarial order/phase experiments."""
import json
from o188_cache_admission_oracle import MIB, LRU, Pin, Guard, NoCache, measure


def trace(name):
    if name == "reverse96":
        return ([(f'R{k}', MIB, 1, 'forward') for k in range(96)] +
                [(f'R{k}', MIB, 1, 'reverse') for k in reversed(range(96))])
    if name == "fit_shift48":
        return ([(f'A{k}', MIB, 1, f'A{p}') for p in range(1,3) for k in range(96)] +
                [(f'B{k}', MIB, 1, f'B{p}') for p in range(1,6) for k in range(48)])
    if name == "same_fit64":
        return [(f'C{k}', MIB, 1, f'pass{p}') for p in range(1,5) for k in range(64)]
    raise KeyError(name)


def main():
    arms={'lru':LRU, 'fixed_pin':Pin, 'guard_48_16':Guard, 'no_cache':NoCache}
    result={'schema':'cmpct-o188b-heldout-v1',
            'evidence_tier':'offline ordered-trace policy simulation, NOT real Reader',
            'families':{f:{a:measure(trace(f), cls) for a,cls in arms.items()}
                        for f in ['reverse96','fit_shift48','same_fit64']}}
    f=result['families']
    assert f['reverse96']['lru']['phases']['reverse']['hits']==64
    assert f['fit_shift48']['lru']['phases']['B2']['hits']==48
    assert f['fit_shift48']['fixed_pin']['phases']['B2']['hits']==0
    assert f['fit_shift48']['guard_48_16']['phases']['B2']['hits']<48
    assert all(f['same_fit64'][x]['phases']['pass2']['hits']==64 for x in ('lru','fixed_pin','guard_48_16'))
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__': main()
