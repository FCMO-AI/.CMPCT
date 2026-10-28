#!/usr/bin/env python3
"""Independent A14-O1b referee. Does not import research/a14_o1b_natural_crc_oracle.py."""
from __future__ import annotations
import argparse,hashlib,json,os,struct,subprocess,zlib,gzip,lzma
from pathlib import Path
import brotli

HEADER=struct.Struct('<8sBQQ32s')
SIGNATURE=bytes.fromhex('89504e470d0a1a0a')

def sha(x):return hashlib.sha256(x).hexdigest()

def controls(original):
    return {'zstd19':subprocess.run(['zstd','-q','-19','-c'],input=original,capture_output=True,check=True).stdout,
            'xz9':lzma.compress(original,preset=9),
            'brotli11':brotli.compress(original,quality=11)}

def source_set(ext):
    candidates=[]
    for root in ('/usr','/opt'):
        for d,dirs,files in os.walk(root,followlinks=False):
            dirs[:]=[n for n in dirs if not (Path(d)/n).is_symlink()]
            for f in files:
                if not f.lower().endswith(ext):continue
                p=Path(d)/f
                if p.is_symlink():continue
                try:size=p.stat().st_size
                except OSError:continue
                if 256<=size<=1048576:candidates.append(p)
    candidates.sort(key=lambda p:hashlib.sha256(os.fsencode(str(p))).digest())
    selected=[];digests=set()
    for p in candidates:
        try:content=p.read_bytes()
        except OSError:continue
        if not 256<=len(content)<=1048576:continue
        h=sha(content)
        if h in digests:continue
        digests.add(h);selected.append(content)
        if len(selected)==64:break
    return selected

def removed_png(src):
    if src[:8]!=SIGNATURE:raise ValueError('PNG signature')
    result=bytearray(src[:8]);pos=8;num=0
    while pos<len(src):
        if pos+12>len(src):raise ValueError('truncated PNG')
        size=int.from_bytes(src[pos:pos+4],'big');last=pos+12+size
        if last>len(src):raise ValueError('PNG length')
        typ=src[pos+4:pos+8];body=src[pos+8:pos+8+size]
        actual=int.from_bytes(src[last-4:last],'big')
        if zlib.crc32(typ+body)!=actual:raise ValueError('PNG CRC')
        result.extend(src[pos:last-4]);num+=1;pos=last
        if typ==b'IEND':break
    result.extend(src[pos:])
    return bytes(result),num

def removed_gzip(src):
    if len(src)<18 or src[:3]!=b'\x1f\x8b\x08':raise ValueError('GZIP signature')
    obj=zlib.decompressobj(31);decoded=obj.decompress(src,8*1024*1024+1)
    if not obj.eof or obj.unused_data or obj.unconsumed_tail or len(decoded)>8*1024*1024:raise ValueError('gzip member validity')
    if src[-8:]!=struct.pack('<II',zlib.crc32(decoded),len(decoded)&0xffffffff):raise ValueError('gzip footer')
    return src[:-8],1

def judge(r,check_codec=True):
    if r.get('schema')!='cmpct-a14-o1b-natural-crc-v1':raise AssertionError('schema')
    checked=0;total={};details=[]
    for format_label,ext,fmt in (('png','.png',1),('gzip','.gz',2)):
        source=source_set(ext)
        expected=r['selection'][ext]
        if len(source)!=expected['selected']:raise AssertionError('selected count')
        if sha(('\n'.join(sha(s) for s in source)).encode())!=expected['selection_manifest_sha256']:raise AssertionError('selected manifest')
        rows=[x for x in r['results'] if x['family']==format_label]
        if len(rows)!=len(source):raise AssertionError('result family count')
        aggregates=dict(selected=len(source),valid=0,refused=0,positive5_files=0,total_raw_bytes=0,
                       total_crc_bytes=0,total_candidate_bytes=0,total_best_control_bytes=0)
        for i,(src,row) in enumerate(zip(source,rows)):
            if row['id']!=f'{fmt}:{i:03d}' or row['raw_sha256']!=sha(src) or row['raw_bytes']!=len(src):raise AssertionError('row identity')
            if row['status']!='admitted':aggregates['refused']+=1;continue
            content,count=(removed_png(src) if fmt==1 else removed_gzip(src))
            compressed=subprocess.run(['zstd','-q','-19','-c'],input=content,capture_output=True,check=True).stdout
            artifact=HEADER.pack(b'A14CRC01',fmt,len(src),len(compressed),hashlib.sha256(src).digest())+compressed
            if len(artifact)!=row['candidate_bytes'] or sha(artifact)!=row['artifact_sha256']:raise AssertionError('candidate identity')
            if row['field_count']!=count or row['crc_bytes_saved']!=(4*count if fmt==1 else 8):raise AssertionError('CRC count')
            if row['roundtrip_sha256']!=sha(src):raise AssertionError('roundtrip source')
            if check_codec:
                c=controls(src)
                for label,data in c.items():
                    got=row['controls'][label]
                    if got['bytes']!=len(data) or got['sha256']!=sha(data):raise AssertionError('control mismatch '+label)
            sizes={k:v['bytes'] for k,v in row['controls'].items()}
            best_size=min(sizes.values())
            if row['best_control'] not in sizes or sizes[row['best_control']]!=best_size or row['best_control_bytes']!=best_size:raise AssertionError('best control')
            if row['gain_bytes']!=best_size-len(artifact):raise AssertionError('gain bytes')
            if abs(row['gain_pct']-100*(best_size-len(artifact))/best_size)>1e-10:raise AssertionError('gain percent')
            if abs(row['raw_crc_opportunity_pct']-100*row['crc_bytes_saved']/len(src))>1e-10:raise AssertionError('crc opportunity')
            aggregates['valid']+=1
            if row['gain_pct']>=5:aggregates['positive5_files']+=1
            aggregates['total_raw_bytes']+=len(src);aggregates['total_crc_bytes']+=row['crc_bytes_saved']
            aggregates['total_candidate_bytes']+=len(artifact);aggregates['total_best_control_bytes']+=best_size
            checked+=1
        found=r['summary'][format_label]
        for key,v in aggregates.items():
            if found[key]!=v:raise AssertionError('aggregate mismatch '+key)
        calc=100*(aggregates['total_best_control_bytes']-aggregates['total_candidate_bytes'])/aggregates['total_best_control_bytes']
        if abs(found['aggregate_gain_pct']-calc)>1e-10:raise AssertionError('aggregate percent')
        total[format_label]=dict(checked=aggregates['valid'],gain_pct=calc,positive5_files=aggregates['positive5_files'])
    decision='INSUFFICIENT_CORPUS' if any(x['checked']<16 for x in total.values()) else ('ADVANCE_O1B' if all(x['positive5_files']>=2 and x['gain_pct']>=1 for x in total.values()) else 'PARK_FORMAT_CHECKSUM_FAMILY')
    if r['decision']!=decision:raise AssertionError('decision')
    return dict(decision=decision,total=total,checked=checked)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);a=p.parse_args()
    raw=Path(a.input).read_bytes();original=json.loads(raw)
    result=judge(original)
    attacks={
        'candidate_bytes':('results',0,'candidate_bytes',1),
        'gain_percent':('results',0,'gain_pct',1),
        'source_sha':('results',0,'raw_sha256','0'*64),
        'aggregate_total':('summary','png','total_candidate_bytes',1),
        'manifest':('selection','.png','selection_manifest_sha256','0'*64),
        'decision':('decision',None,None,'ADVANCE_O1B'),
    }
    for key,(part,item,field,val) in attacks.items():
        obj=json.loads(raw)
        if part=='decision':obj['decision']=val
        elif isinstance(obj[part],list):obj[part][item][field]=(obj[part][item][field]+val if isinstance(val,int) else val)
        else:obj[part][item][field]=(obj[part][item][field]+val if isinstance(val,int) else val)
        try:judge(obj,False)
        except AssertionError:pass
        else:raise AssertionError('forgery accepted: '+key)
    receipt=dict(schema='a14-o1b-third-root-v1',verdict='PASS',result_sha256=sha(raw),
                 referee_sha256=sha(Path(__file__).read_bytes()),forgeries_rejected=len(attacks),**result)
    Path(a.input).with_suffix('.referee.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
