#!/usr/bin/env python3
"""Independent A16-O2 envelope referee. No imports of producer/oracle.

The scientific envelope is NOT a released CMPCT archive. Uses external zstd CLI
and SHA-256 plus a separate parser and positional co-owner semantic check.
"""
from __future__ import annotations
import argparse, hashlib, json, math, statistics, struct, subprocess
from pathlib import Path
N=32; BLOCK=4096; CHUNKS=16; MEMBER=N*0+BLOCK*CHUNKS
ARMS=('direct','chunkref','binary_segref','positional_coowner')
REGIMES=('identical','prefix12','suffix12','alternating8','distinct')
EXPECTED={(r,s) for r in REGIMES for s in (20261028,20261029)}
EXPECTED|={('hostile',s) for s in (20261030,20261031)}
EXPECTED|={(r,s) for r in ('shifted','permuted') for s in (20261032,20261033)}

def digest(raw):return hashlib.sha256(raw).digest()
def take(fmt,blob,p):
    st=struct.Struct(fmt)
    if p+st.size>len(blob):raise ValueError('truncated')
    return st.unpack_from(blob,p),p+st.size

def decode_frames(frames):
    if not frames:return []
    proc=subprocess.run(['zstd','-q','-d','-c'],input=b''.join(frame for frame,raw,want in frames),
                        capture_output=True,check=False)
    if proc.returncode or len(proc.stdout)!=sum(n for frame,n,want in frames):
        raise ValueError('independent zstd/size')
    p=0;out=[]
    for frame,n,want in frames:
        part=proc.stdout[p:p+n];p+=n
        if digest(part)!=want:raise ValueError('physical SHA')
        out.append(part)
    return out

def decode_wire(blob):
    (tag,n,no,block),p=take('<4sHHI',blob,0)
    if tag not in (b'D116',b'CR16',b'SR16') or n!=N or block!=BLOCK or no>512:
        raise ValueError('header')
    if tag==b'D116' and no:raise ValueError('direct owners')
    owners=[]
    for _ in range(no):
        if tag==b'CR16':
            (width,want),p=take('<I32s',blob,p);size=BLOCK
        else:
            (size,width,want),p=take('<II32s',blob,p)
        if not 0<size<=MEMBER or not 0<width<=1<<22 or p+width>len(blob):
            raise ValueError('owner bounds')
        owners.append((blob[p:p+width],size,want));p+=width
    owner_data=decode_frames(owners)
    direct=[];member_defs=[]
    for i in range(n):
        if tag==b'D116':
            (length,want,width),p=take('<I32sI',blob,p)
            if length!=MEMBER or not 0<width<=1<<22 or p+width>len(blob):
                raise ValueError('direct bounds')
            direct.append((blob[p:p+width],length,want));p+=width
            member_defs.append((want,None))
        else:
            (length,want,refs),p=take('<I32sH',blob,p)
            if length!=MEMBER or not 0<refs<=CHUNKS or p+refs*2>len(blob):
                raise ValueError('reference bounds')
            indices,p=take('<'+'H'*refs,blob,p)
            if any(k>=len(owner_data) for k in indices):raise ValueError('owner index')
            member_defs.append((want,indices))
    if p!=len(blob):raise ValueError('trailing')
    direct_data=decode_frames(direct)
    members=[];units=[];lengths=[]
    for i,(want,refs) in enumerate(member_defs):
        raw=direct_data[i] if refs is None else b''.join(owner_data[k] for k in refs)
        widths=[MEMBER] if refs is None else [len(owner_data[k]) for k in refs]
        if len(raw)!=MEMBER or digest(raw)!=want or any(w%BLOCK for w in widths):
            raise ValueError('member')
        members.append(raw);units.append(len(widths));lengths.append(widths)
    return members,no,units,lengths

def positional_lengths(members):
    rows=[[x[i*BLOCK:(i+1)*BLOCK] for i in range(CHUNKS)] for x in members]
    mask=[{} for _ in range(CHUNKS)]
    for i,row in enumerate(rows):
        for j,chunk in enumerate(row):
            mask[j][chunk]=mask[j].get(chunk,0)|(1<<i)
    out=[]
    for row in rows:
        widths=[];previous=mask[0][row[0]];length=BLOCK
        for j in range(1,CHUNKS):
            membership=mask[j][row[j]]
            if membership!=previous:
                widths.append(length);length=0
            length+=BLOCK;previous=membership
        widths.append(length);out.append(widths)
    return out

def equal(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-8)
def assess(root,receipt):
    if receipt.get('schema')!='a16-o2-positional-coowner-hosted-v1':raise ValueError('schema')
    if receipt.get('source_parent')!='acaa48a74c2e8859e476c629bf1debab25e89f37':raise ValueError('parent')
    if receipt.get('prereg_sha')!='a0b75a33f17c67c749c467227266092ba799c224':raise ValueError('prereg')
    rows=receipt['cases']
    if len(rows)!=len(EXPECTED):raise ValueError('number of cases')
    seen=set();verified=0
    for row in rows:
        k=(row.get('regime'),row.get('seed'))
        if k not in EXPECTED or k in seen:raise ValueError('unexpected/duplicate')
        seen.add(k);folder=root/(str(k[0])+'_'+str(k[1]))
        src=(folder/'source.bin').read_bytes()
        if len(src)!=N*MEMBER or digest(src).hex()!=row['source_sha256']:
            raise ValueError('source identity')
        originals=[src[i*MEMBER:(i+1)*MEMBER] for i in range(N)]
        expected_units=positional_lengths(originals)
        sizes={}
        for arm in ARMS:
            raw=(folder/(arm+'.bin')).read_bytes()
            sizes[arm]=len(raw)
            rebuilt,owners,units,widths=decode_wire(raw)
            if rebuilt!=originals:raise ValueError('lossless failure')
            stats=row['geometry'][arm]
            if stats['owners']!=owners or stats['units']!=units:raise ValueError('geometry')
            if arm=='positional_coowner' and widths!=expected_units:
                raise ValueError('positional co-owner proof')
            verified+=N
        if sizes!=row['complete_bytes']:raise ValueError('archive lengths')
        if row['portfolio_baseline_bytes']!=min(sizes['direct'],sizes['chunkref'])+1:
            raise ValueError('baseline selector')
        if row['portfolio_candidate_bytes']!=min(sizes['direct'],sizes['chunkref'],sizes['positional_coowner'])+1:
            raise ValueError('candidate selector')
        if row['portfolio_selected']!=min(('direct','chunkref','positional_coowner'),key=sizes.get):
            raise ValueError('chosen arm')
        if not equal(row['ratio_positional_over_fixed'],sizes['positional_coowner']/sizes['chunkref']):
            raise ValueError('wrong ratio')
        for arm,v in row['read_wall_ms'].items():
            for samples,median in (('q1_ms','median_q1_ms'),('whole_ms','median_whole_ms'),
                                   ('q1_cpu_ms','median_q1_cpu_ms'),('whole_cpu_ms','median_whole_cpu_ms')):
                if len(v[samples])!=7 or not all(x>=0 for x in v[samples]):
                    raise ValueError('raw samples')
                if not equal(v[median],statistics.median(v[samples])):
                    raise ValueError('median')
        if not equal(row['read_speedup_fixed_over_positional'],
                     row['read_wall_ms']['chunkref']['median_whole_ms']/
                     row['read_wall_ms']['positional_coowner']['median_whole_ms']):
            raise ValueError('wall speedup')
        if not equal(row['cpu_speedup_fixed_over_positional'],
                     row['read_wall_ms']['chunkref']['median_whole_cpu_ms']/
                     row['read_wall_ms']['positional_coowner']['median_whole_cpu_ms']):
            raise ValueError('CPU speedup')
    if seen!=EXPECTED:raise ValueError('coverage')
    hostile=all(x['ratio_positional_over_fixed']<=1.01 and
                x['geometry']['positional_coowner']['units']==[16]*N
                for x in rows if x['regime']=='hostile')
    transfer=all(x['geometry']['positional_coowner']['units']==[2]*N and
                 x['complete_bytes']['positional_coowner']<=1.005*x['complete_bytes']['binary_segref']
                 for x in rows if x['regime'] in ('prefix12','suffix12'))
    joint=all(x['ratio_positional_over_fixed']<=.99 and
              x['read_speedup_fixed_over_positional']>=1.5
              and x['cpu_speedup_fixed_over_positional']>=1.5
              for x in rows if x['regime'] in ('prefix12','suffix12'))
    if receipt['hostile_containment']!=hostile or receipt['positive_transfer']!=transfer or receipt['inherited_joint_byte_wall_pass']!=joint:
        raise ValueError('altered decision')
    return {'cases':len(rows),'independently_reconstructed_members':verified,
            'hostile_containment':hostile,'positive_transfer':transfer,'joint_size_wall':joint}

def run(root):
    receipt=json.loads((root/'result.json').read_text())
    result=assess(root,receipt)
    mutations=[]
    def forged(name,edit):
        r=json.loads(json.dumps(receipt));edit(r)
        try:assess(root,r)
        except ValueError:mutations.append(name);return
        raise AssertionError('forged receipt accepted: '+name)
    forged('false_success',lambda r:r.update(inherited_joint_byte_wall_pass=not r['inherited_joint_byte_wall_pass']))
    forged('wrong_source',lambda r:r['cases'][0].update(source_sha256='0'*64))
    forged('wrong_bytes',lambda r:r['cases'][1]['complete_bytes'].update(positional_coowner=0))
    forged('wrong_units',lambda r:r['cases'][2]['geometry']['positional_coowner']['units'].__setitem__(0,0))
    forged('wrong_median',lambda r:r['cases'][3]['read_wall_ms']['chunkref'].update(median_whole_ms=0.0))
    forged('wrong_selector',lambda r:r['cases'][4].update(portfolio_selected='forged'))
    forged('duplicate_case',lambda r:r['cases'][5].update(regime=r['cases'][4]['regime'],seed=r['cases'][4]['seed']))
    forged('false_hostile',lambda r:r.update(hostile_containment=not r['hostile_containment']))
    sample=(root/'prefix12_20261028'/'positional_coowner.bin').read_bytes()
    for name,altered in (('trailing',sample+b'0'),('truncated',sample[:-1]),('magic',b'XXXX'+sample[4:]),
                         ('payload_corrupt',sample[:1024]+bytes([sample[1024]^1])+sample[1025:])):
        try:decode_wire(altered)
        except ValueError:mutations.append(name);continue
        raise AssertionError('hostile accepted '+name)
    result['forgeries_and_hostiles_rejected']=mutations
    (root/'independent_referee.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    run(ap.parse_args().root)
