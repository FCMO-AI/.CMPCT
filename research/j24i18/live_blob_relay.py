#!/usr/bin/env python3
"""J24I18b: fail-closed descriptor-closed *live* blob relay, not a product compactor.

All physical blobs are authenticated before considering reachability. Reject virtual
recipes, unknown storage, malformed references, cyclic/dangling hardlinks. This
research-only implementation still loads the entire physical archive in memory.
"""
import argparse,copy,json,pathlib,time
import physical_relay as pr

def bounded_id(value,count):
    if type(value) is not int or value<0 or value>=count:
        raise ValueError('dangling, boolean or non-integer blob reference')
    return value

def live_ids(index):
    if index.get('recipes') or any(r[1] not in (0,1,2,3) for r in index['files']):
        raise ValueError('recipes/unknown entry kind unsupported')
    count=len(index['blobs']);live=set()
    by={r[0]:r for r in index['files']}
    if len(by)!=len(index['files']):raise ValueError('duplicate logical path')
    def add(i):live.add(bounded_id(i,count))
    if index.get('dict_blob') is not None:add(index['dict_blob'])
    def follow_owner(name,seen):
        if name in seen:raise ValueError('hardlink cycle')
        row=by.get(name)
        if row is None:raise ValueError('missing hardlink owner')
        if row[1]==3:
            if not isinstance(row[6],list) or len(row[6])!=1:
                raise ValueError('malformed hardlink target')
            return follow_owner(row[6][0],seen|{name})
        if row[1]!=0:raise ValueError('nonregular hardlink owner')
        return row
    for row in index['files']:
        kind=row[1];storage=row[6]
        if kind==1:continue
        if kind==3:
            if not isinstance(storage,list) or len(storage)!=1:raise ValueError('invalid hardlink storage')
            follow_owner(storage[0],{row[0]});continue
        if not isinstance(storage,list) or len(storage)<2:raise ValueError('invalid storage')
        mode=storage[0]
        if mode==0 and len(storage)==2:add(storage[1])
        elif kind==0 and mode==1 and len(storage)==2:
            for i in storage[1]:add(i)
        elif kind==0 and mode==3 and len(storage)==2:
            for extent in storage[1]:
                if len(extent)!=3:raise ValueError('invalid sparse extent')
                for i in extent[2]:add(i)
        elif kind==0 and mode==4 and len(storage)==4:add(storage[1])
        elif kind==0 and mode==5 and len(storage)==2:
            for length,i in storage[1]:add(i)
        else:raise ValueError('unsupported storage; refuse pruning')
    return sorted(live)

def map_index(index,kept):
    result=copy.deepcopy(index);mapping={old:new for new,old in enumerate(kept)}
    result['blobs']=[result['blobs'][i] for i in kept]
    if result.get('dict_blob') is not None:
        result['dict_blob']=mapping[result['dict_blob']]
    for row in result['files']:
        if row[1] in (1,3):continue
        storage=row[6];mode=storage[0]
        if mode in (0,4):storage[1]=mapping[storage[1]]
        elif mode==1:storage[1]=[mapping[i] for i in storage[1]]
        elif mode==3:
            for extent in storage[1]:extent[2]=[mapping[i] for i in extent[2]]
        elif mode==5:
            for chunk in storage[1]:chunk[1]=mapping[chunk[1]]
        else:raise ValueError('unsupported descriptor remapping')
    return result

def relay(source,destination):
    t0=time.perf_counter_ns();original=pathlib.Path(source).read_bytes()
    if len(original)>pr.MAX_INPUT:raise ValueError('research file limit exceeded')
    idx,base,depth=pr.read_index(original)
    records=pr.read_blobs(original,idx,base)
    keep=live_ids(idx);rewrite=map_index(idx,keep)
    stream=[];offset=0
    for b,old_id in zip(rewrite['blobs'],keep):
        b[0]=offset;rec=records[old_id];stream.append(rec);offset+=len(rec)
    raw=pr.pk(rewrite);encoded=pr.zc(raw);h=pr.sha(raw)
    wire=pr.HDR.pack(pr.MAGIC,24,0,len(encoded),len(raw),offset,h)+encoded+b''.join(stream)+encoded+pr.FTR.pack(pr.FMAGIC,0,1,0,0,len(encoded),len(raw),0,h)
    pathlib.Path(destination).write_bytes(wire)
    recovered,base2,depth2=pr.read_index(wire)
    assert pr.read_blobs(wire,recovered,base2)==stream and depth2==0
    def stable(ix):return pr.pk({**ix,'blobs':[[0]+list(b[1:]) for b in ix['blobs']]})
    assert stable(recovered)==stable(rewrite)
    assert pr.sha(pathlib.Path(source).read_bytes())==pr.sha(original)
    return {'source':pathlib.Path(source).name,'old_bytes':len(original),
        'new_bytes':len(wire),'saved_bytes':len(original)-len(wire),
        'old_sha256':pr.sha(original).hex(),'new_sha256':pr.sha(wire).hex(),
        'old_blob_count':len(records),'live_blob_count':len(keep),
        'dead_blob_count':len(records)-len(keep),'kept_ids':keep,
        'old_depth':depth,'new_depth':depth2,
        'old_index_semantic_hash':pr.sha(stable(idx)).hex(),
        'new_index_semantic_hash':pr.sha(stable(rewrite)).hex(),
        'elapsed_ms':round((time.perf_counter_ns()-t0)/1e6,3)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);p.add_argument('inputs',nargs='+')
    a=p.parse_args();d=pathlib.Path(a.output_dir);d.mkdir(parents=True,exist_ok=True)
    for src in a.inputs:
        try:print(json.dumps(relay(src,d/pathlib.Path(src).name),sort_keys=True))
        except Exception as e:print(json.dumps({'source':src,'failure':str(e)},sort_keys=True))
