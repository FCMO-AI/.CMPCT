from benchmarks.one.one_g02_triplet_relation_sketch import FAMILIES,SIZES,decide

def rows():
    return [{'size':s,'family':f,'semantic_ok':True,'baseline_common_equal':True,'source_scan_ratio':1.0,'wall_ratio':1.0,'cpu_ratio':1.0,'wall_mib_s':300.0,'cpu_mib_s':300.0} for s in SIZES for f in FAMILIES]

def test_green_advances(): assert decide(rows())=='ADVANCE_TRIPLET_RELATION_SKETCH'
def test_semantic_invalidates():
    r=rows();r[0]['semantic_ok']=False;assert decide(r)=='INVALIDATE_TRIPLET_RELATION_SKETCH'
def test_missing_invalidates(): assert decide(rows()[:-1])=='INVALIDATE_TRIPLET_RELATION_SKETCH'
def test_wall_holds():
    r=rows();r[0]['wall_ratio']=1.36;assert decide(r)=='HOLD_TRIPLET_RELATION_SKETCH'
def test_throughput_holds():
    r=rows();next(x for x in r if x['size']==1024*1024)['wall_mib_s']=249;assert decide(r)=='HOLD_TRIPLET_RELATION_SKETCH'
