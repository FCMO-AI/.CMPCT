#!/usr/bin/env python3
from __future__ import annotations
import argparse,bz2,hashlib,json,os,shutil,subprocess,tarfile,zipfile
from pathlib import Path

EPOCH=946684800
CANTERBURY={
'alice29.txt':152089,'asyoulik.txt':125179,'cp.html':24603,'fields.c':11150,
'grammar.lsp':3721,'kennedy.xls':1029744,'lcet10.txt':426754,'plrabn12.txt':481861,
'ptt5':513216,'sum':38240,'xargs.1':4227}
SILESIA={
'dickens':(10192446,'88334708559f6db57d79096bc0aca07e'),
'mozilla':(51220480,'c7789a2097f1ff944b0c737430a339b3'),
'mr':(9970564,'38e623e3093b7bf2003ca4b1bbc19927'),
'nci':(33553445,'31f85bc8706f3c921104e7c169e2e2e1'),
'ooffice':(6152192,'573c4ae915e36631d8f2dcffb9b9b66d'),
'osdb':(10085684,'e734b0c48e6a982adfb5802da3032ecd'),
'reymont':(6627202,'d8f54d78105079775f32d76dc55fc671'),
'samba':(21606400,'154eaea7ea70e89f6339ff0abf4112ca'),
'sao':(7251944,'79e95a22e18cd82b7e42bf91b380d30b'),
'webster':(41458703,'474931ad907ac27bf962c75ded46c069'),
'xml':(5345280,'9b09c0c80104adb8aae910b7d7db003e'),
'x-ray':(8474240,'9baec32ad14ec3eff487d254382cb91c')}
ENWIK={'enwik8':(100_000_000,'a1fa5ffddb56f4953e226637dabbb36a'),
       'enwik9':(1_000_000_000,'e206c3450ac99950df65bf70ef61a12d')}

def curl(url: str,out: Path,max_time: int=900)->None:
    subprocess.run(['curl','--fail','--location','--retry','4','--retry-all-errors',
                    '--connect-timeout','20','--max-time',str(max_time),url,'-o',str(out)],check=True)

def normalize(root: Path)->None:
    for p in sorted(root.rglob('*'),reverse=True):
        if p.is_file():
            os.chmod(p,0o644);os.utime(p,(EPOCH,EPOCH))
        elif p.is_dir():
            os.chmod(p,0o755);os.utime(p,(EPOCH,EPOCH))
    os.chmod(root,0o755);os.utime(root,(EPOCH,EPOCH))

def get_canterbury(root: Path)->Path:
    dst=root/'canterbury';dst.mkdir(parents=True)
    arc=root/'cantrbry.tar.gz';curl('https://corpus.canterbury.ac.nz/resources/cantrbry.tar.gz',arc,300)
    with tarfile.open(arc,'r:gz') as t:t.extractall(dst,filter='data')
    actual={p.name:p.stat().st_size for p in dst.iterdir() if p.is_file()}
    if actual!=CANTERBURY:raise SystemExit(f'Canterbury identity mismatch: {actual}')
    normalize(dst);return dst

def get_silesia(root: Path)->Path:
    dst=root/'silesia';dst.mkdir(parents=True)
    for name,(size,md5) in SILESIA.items():
        comp=root/f'{name}.bz2';raw=dst/name
        curl(f'https://sun.aei.polsl.pl/~sdeor/corpus/{name}.bz2',comp,300)
        raw.write_bytes(bz2.decompress(comp.read_bytes()));comp.unlink()
        data=raw.read_bytes()
        if len(data)!=size or hashlib.md5(data).hexdigest()!=md5:raise SystemExit(f'Silesia identity mismatch: {name}')
    if sum(p.stat().st_size for p in dst.iterdir())!=211_938_580:raise SystemExit('Silesia aggregate mismatch')
    normalize(dst);return dst

def get_enwik(root: Path,name: str)->Path:
    dst=root/name;dst.mkdir(parents=True)
    arc=root/f'{name}.zip';curl(f'https://www.mattmahoney.net/dc/{name}.zip',arc,1200 if name=='enwik9' else 300)
    with zipfile.ZipFile(arc) as z:z.extract(name,dst)
    raw=dst/name;size,md5=ENWIK[name];data=raw.read_bytes()
    if len(data)!=size or hashlib.md5(data).hexdigest()!=md5:raise SystemExit(f'{name} identity mismatch')
    normalize(dst);return dst

def item(name: str,path: Path,size: int,authority: str,mode: str,reps: int)->dict:
    return {'name':name,'path':str(path),'expected_logical_bytes':size,'authority':authority,'mode':mode,'repetitions':reps}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--suite',choices=['aggregate','members','enwik9'],required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();root=Path(a.root);shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True)
    corpora=[]
    if a.suite in {'aggregate','members'}:
        can=get_canterbury(root);sil=get_silesia(root)
        if a.suite=='aggregate':
            enw=get_enwik(root,'enwik8')
            corpora=[item('canterbury-archive',can,sum(CANTERBURY.values()),'Canterbury Corpus','archive-tree',3),
                     item('silesia-archive',sil,211_938_580,'Silesia Compression Corpus','archive-tree',3),
                     item('enwik8',enw,100_000_000,'Large Text Compression Benchmark / Hutter data','canonical-single-file',3)]
        else:
            views=root/'views';views.mkdir()
            for name,size in CANTERBURY.items():
                d=views/f'canterbury-{name}';d.mkdir();os.link(can/name,d/name);normalize(d)
                corpora.append(item(f'canterbury-{name}',d,size,'Canterbury Corpus','canonical-member',1))
            for name,(size,_) in SILESIA.items():
                d=views/f'silesia-{name}';d.mkdir();os.link(sil/name,d/name);normalize(d)
                corpora.append(item(f'silesia-{name}',d,size,'Silesia Compression Corpus','canonical-member',1))
    else:
        enw=get_enwik(root,'enwik9')
        corpora=[item('enwik9',enw,1_000_000_000,'Large Text Compression Benchmark','canonical-single-file',1)]
    Path(a.out).write_text(json.dumps({'schema':'cmpct-established-corpus-manifest-v2','suite':a.suite,
      'normalization':{'mtime_unix':EPOCH,'file_mode':'0644','directory_mode':'0755'},
      'corpora':corpora},indent=2))
if __name__=='__main__':main()
