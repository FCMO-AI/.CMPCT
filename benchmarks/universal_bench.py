#!/usr/bin/env python3
from pathlib import Path
import os, shutil, random, hashlib, json, subprocess, time, zipfile, wave, struct, math, tempfile, statistics
HERE=Path(__file__).resolve().parent
WORK=HERE/'_work'
CORP=WORK/'corpora'; OUT=WORK/'out'
CMPCT_MODULE='cmpct'

def reset():
    shutil.rmtree(WORK, ignore_errors=True); CORP.mkdir(parents=True); OUT.mkdir()

def patterned(n, seed=b'cmpct'):
    block=(seed+b' :: alpha beta gamma delta epsilon 0123456789\n')*64
    return (block*((n+len(block)-1)//len(block)))[:n]

def wav_file(path, sec=3, rate=16000, freq=440):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        frames=bytearray()
        for i in range(sec*rate):
            v=int(22000*math.sin(2*math.pi*freq*i/rate)); frames += struct.pack('<h',v)
        w.writeframes(frames)

def make_corpora():
    # 1) many tiny unique text + duplicates
    d=CORP/'tiny'; d.mkdir()
    for i in range(3000):
        txt=f'file={i}\nkind=tiny\n'+('common configuration directive = value\n'*8)+f'unique={hashlib.sha256(str(i).encode()).hexdigest()}\n'
        (d/f'f{i:04d}.txt').write_text(txt)
    base=(d/'f0000.txt').read_bytes()
    for i in range(200): (d/f'dup{i:04d}.txt').write_bytes(base)

    # 2) source-like tree
    d=CORP/'source'; d.mkdir()
    for i in range(500):
        sub=d/f'pkg{i%20:02d}'; sub.mkdir(exist_ok=True)
        code=('''from __future__ import annotations\n\ndef transform(value):\n    # shared boilerplate for codec/dictionary behavior\n    return {"index": %d, "value": value, "stable": True}\n'''%i)
        (sub/f'mod{i:04d}.py').write_text(code)
    for i in range(100): (d/f'config{i:03d}.json').write_text(json.dumps({'service':'hermes','retry':3,'timeout':15,'idx':i,'features':['a','b','c']},indent=2))

    # 3) mixed media / already compressed + PCM
    d=CORP/'media'; d.mkdir()
    for i in range(8): wav_file(d/f'tone{i}.wav', sec=2+(i%3), freq=220+55*i)
    # zlib-compressed and random pseudo-media should mostly be STORE-like
    import zlib
    for i in range(8):
        raw=os.urandom(512*1024)
        (d/f'already{i}.binz').write_bytes(zlib.compress(raw,9))

    # 4) incompressible + compressible large files
    d=CORP/'binary'; d.mkdir()
    (d/'random16m.bin').write_bytes(os.urandom(16*1024*1024))
    (d/'pattern32m.bin').write_bytes(patterned(32*1024*1024,b'large-pattern'))

    # 5) duplicates and filesystem semantics
    d=CORP/'dedup_links'; d.mkdir()
    payload=patterned(1024*1024,b'duplicate-payload')
    for i in range(24): (d/f'copy{i:02d}.dat').write_bytes(payload)
    (d/'real.dat').write_bytes(payload)
    os.link(d/'real.dat',d/'hardlink.dat')
    os.symlink('real.dat',d/'symlink.dat')

    # 6) sparse disk image, logical 128MiB with 4MiB real data
    d=CORP/'sparse'; d.mkdir()
    p=d/'disk.img'
    with open(p,'wb') as f:
        f.truncate(128*1024*1024)
        for off in (0, 31*1024*1024, 64*1024*1024, 120*1024*1024):
            f.seek(off); f.write(os.urandom(1024*1024))

    # 7) nested archives with shared payloads
    d=CORP/'nested'; d.mkdir(); shared=patterned(256*1024,b'nested-shared')
    for i in range(12):
        zp=d/f'nested{i:02d}.zip'
        with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            z.writestr('shared.dat',shared)
            for j in range(20): z.writestr(f'docs/{j:02d}.txt', patterned(8*1024, f'{i}-{j}'.encode()))
            z.writestr('unique.bin',os.urandom(64*1024))

    # 8) combined realistic universal tree (hardlinks maintained for duplicate base file)
    d=CORP/'combined'; d.mkdir()
    for name in ['tiny','source','media','dedup_links','nested']:
        shutil.copytree(CORP/name,d/name,symlinks=True)
    # modest large files to avoid a giant benchmark while exercising chunking
    shutil.copy2(CORP/'binary'/'pattern32m.bin',d/'pattern32m.bin')
    shutil.copy2(CORP/'binary'/'random16m.bin',d/'random16m.bin')


def timed(cmd, env=None, reps=1):
    vals=[]
    for _ in range(reps):
        t=time.perf_counter(); r=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env); dt=time.perf_counter()-t
        if r.returncode: raise RuntimeError((cmd,r.returncode))
        vals.append(dt)
    return statistics.median(vals)

def archive_cmpct(src,out):
    env=os.environ.copy(); env['CMPCT_DEFLATE_REUSE_MIN']='65536'
    return timed([os.environ.get('PYTHON','python'),'-m',CMPCT_MODULE,'create',str(src),str(out)],env=env)

def archive_zip(src,out):
    # Python deterministic-ish ZIP; symlinks are dereferenced here, like common ZIP tooling.
    t=time.perf_counter()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in sorted(src.rglob('*')):
            rel=p.relative_to(src).as_posix()
            if p.is_dir(): continue
            z.write(p,rel)
    return time.perf_counter()-t

def archive_tarzst(src,out,level=3):
    # GNU tar --sparse preserves sparse extents and hardlinks/symlinks; zstd stream is whole-archive.
    cmd=f"tar --sparse -C {shlex_quote(str(src))} -cf - . | zstd -q -{level} -T0 -o {shlex_quote(str(out))}"
    t=time.perf_counter(); r=subprocess.run(['bash','-lc',cmd],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); dt=time.perf_counter()-t
    if r.returncode: raise RuntimeError(cmd)
    return dt

def archive_tarxz(src,out):
    cmd=f"tar --sparse -C {shlex_quote(str(src))} -cf - . | xz -6 -T0 -c > {shlex_quote(str(out))}"
    t=time.perf_counter(); r=subprocess.run(['bash','-lc',cmd],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); dt=time.perf_counter()-t
    if r.returncode: raise RuntimeError(cmd)
    return dt

def shlex_quote(s):
    import shlex; return shlex.quote(s)

def extract_cmpct(arc,dst):
    shutil.rmtree(dst,ignore_errors=True); dst.mkdir()
    return timed([os.environ.get('PYTHON','python'),'-m',CMPCT_MODULE,'extract',str(arc),str(dst),'--no-metadata'])

def extract_zip(arc,dst):
    shutil.rmtree(dst,ignore_errors=True); dst.mkdir()
    t=time.perf_counter()
    with zipfile.ZipFile(arc) as z:z.extractall(dst)
    return time.perf_counter()-t

def extract_tarzst(arc,dst):
    shutil.rmtree(dst,ignore_errors=True); dst.mkdir()
    return timed(['bash','-lc',f"zstd -q -dc {shlex_quote(str(arc))} | tar -xf - -C {shlex_quote(str(dst))}"])

def extract_tarxz(arc,dst):
    shutil.rmtree(dst,ignore_errors=True); dst.mkdir()
    return timed(['bash','-lc',f"xz -dc {shlex_quote(str(arc))} | tar -xf - -C {shlex_quote(str(dst))}"])

def logical_bytes(root):
    return sum(p.lstat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())

def run():
    reset(); make_corpora(); results={}
    names=['tiny','source','media','binary','dedup_links','sparse','nested','combined']
    for name in names:
        src=CORP/name; print('BENCH',name,flush=True); row={'logical':logical_bytes(src)}
        ca=OUT/f'{name}.cmpct'; za=OUT/f'{name}.zip'; ta=OUT/f'{name}.tar.zst'; xa=OUT/f'{name}.tar.xz'
        for fmt,fn,out in [('cmpct',archive_cmpct,ca),('zip',archive_zip,za),('tarzst',archive_tarzst,ta),('tarxz',archive_tarxz,xa)]:
            try:
                ct=fn(src,out); row[fmt]={'size':out.stat().st_size,'create_s':ct}
            except Exception as e: row[fmt]={'error':repr(e)}
        for fmt,fn,out in [('cmpct',extract_cmpct,ca),('zip',extract_zip,za),('tarzst',extract_tarzst,ta),('tarxz',extract_tarxz,xa)]:
            if 'error' in row.get(fmt,{}): continue
            try: row[fmt]['extract_s']=fn(out,OUT/f'ex_{name}_{fmt}')
            except Exception as e: row[fmt]['extract_error']=repr(e)
        results[name]=row
        (OUT/'results.partial.json').write_text(json.dumps(results,indent=2))
    (OUT/'results.json').write_text(json.dumps(results,indent=2)); print(json.dumps(results,indent=2))
if __name__=='__main__':run()
