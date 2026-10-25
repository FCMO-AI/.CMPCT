#!/usr/bin/env python3
"""O78 prospective installed-Builder destination semantics court (research only)."""
import hashlib, json, os, platform, stat, subprocess, sys, tempfile, types
from pathlib import Path
BASE='4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b'
BASE_BLOB='663ef0922992b1fbb8f19e6eea88d55c10a56044'
O75_BLOB='d92c78119e9613b2c3ae1886a8fba841dc313fca'
PREREG='100bdcb6944e7429431874071612c3d2ecdc7998'
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def sha(data): return hashlib.sha256(data).hexdigest()
def historical():
    raw=subprocess.check_output(['git','show',f'{BASE}:src/cmpct/builder.py'])
    blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    assert blob==BASE_BLOB
    name='cmpct._o78_true_historical_builder';m=types.ModuleType(name)
    m.__file__='<git-blob:'+blob+'>';m.__package__='cmpct';sys.modules[name]=m
    exec(compile(raw,m.__file__,'exec'),m.__dict__)
    return m.Builder
def main():
    assert os.name=='posix' and sys.platform.startswith('linux') and os.geteuid()!=0
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    import cmpct.builder as installed
    assert 'site-packages' in str(Path(installed.__file__).resolve()),installed.__file__
    head=git('rev-parse','HEAD')
    assert head==os.environ['EXACT_HEAD']
    assert git('rev-parse',f'{PREREG}^{{commit}}')==PREREG
    assert git('hash-object','src/cmpct/builder.py')==O75_BLOB
    Old=historical()
    cases=[]
    with tempfile.TemporaryDirectory(prefix='cmpct-o78-') as tmp:
        home=Path(tmp);src=home/'source';src.mkdir()
        (src/'a.txt').write_bytes(b'alpha-A'*100)
        (src/'b.bin').write_bytes(b'beta-A'*111)
        beforepath=home/'before.cmpct';Old(src,reproducible=True,workers=1).build(beforepath)
        before=beforepath.read_bytes()
        (src/'a.txt').write_bytes(b'alpha-B'*110)
        (src/'b.bin').write_bytes(b'beta-B'*118)
        afterpath=home/'after.cmpct';Old(src,reproducible=True,workers=1).build(afterpath)
        after=afterpath.read_bytes();assert before!=after
        with CMPCT(afterpath) as ar:
            assert ar.verify()==2 and ar.read('a.txt')==b'alpha-B'*110
        for kind in ('ordinary','symlink','hardlink','xattr','readonly'):
            arms={};unsupported=False
            for label,cls in (('old',Old),('o75',Builder)):
                d=home/(kind+'-'+label);d.mkdir()
                dest=d/'archive.cmpct';alias=d/'alias.cmpct'
                if kind=='symlink':
                    alias.write_bytes(before);dest.symlink_to(alias.name)
                else:
                    dest.write_bytes(before)
                    if kind=='hardlink':os.link(dest,alias)
                    elif kind=='readonly':dest.chmod(0o444)
                    elif kind=='xattr':
                        try:os.setxattr(dest,b'user.cmpct_o78',b'keep-me')
                        except (OSError,AttributeError) as exc:
                            cases.append({'kind':kind,'status':'SKIP','cause':repr(exc)})
                            unsupported=True;break
                inode=dest.lstat().st_ino;mode=stat.S_IMODE(dest.lstat().st_mode)
                error=None
                try:cls(src,reproducible=True,workers=1).build(dest)
                except OSError as exc:error=type(exc).__name__
                raw=dest.read_bytes()
                aliasraw=alias.read_bytes() if kind in ('symlink','hardlink') else None
                xattr=None
                if kind=='xattr':
                    try:xattr=os.getxattr(dest,b'user.cmpct_o78').decode()
                    except OSError:xattr='<MISSING>'
                arms[label]={
                    'error':error,'archive_sha256':sha(raw),'is_new':raw==after,
                    'same_inode':dest.lstat().st_ino==inode,
                    'same_mode':stat.S_IMODE(dest.lstat().st_mode)==mode,
                    'still_symlink':dest.is_symlink(),
                    'alias_new':aliasraw==after if aliasraw is not None else None,
                    'alias_old':aliasraw==before if aliasraw is not None else None,
                    'xattr':xattr,'stage_orphans':len(list(d.glob('.*.cmpct-stage-*')))}
                if error is None:
                    assert raw==after,(kind,label)
                    with CMPCT(dest) as reader:
                        assert reader.verify()==2 and reader.read('a.txt')==b'alpha-B'*110
            if unsupported:continue
            a,b=arms['old'],arms['o75']
            if kind=='ordinary':assert a['same_inode'] and not b['same_inode']
            if kind=='symlink':assert a['still_symlink'] and a['alias_new'] and not b['still_symlink'] and b['alias_old']
            if kind=='hardlink':assert a['alias_new'] and b['alias_old']
            if kind=='xattr':assert a['xattr']=='keep-me' and b['xattr']=='<MISSING>'
            if kind=='readonly':assert a['error']=='PermissionError' and not a['is_new'] and b['error'] is None and b['is_new'] and b['same_mode']
            assert b['stage_orphans']==0
            cases.append({'kind':kind,'status':'PASS','arms':arms})
    return {'head':head,'builder_blob':O75_BLOB,'old_blob':BASE_BLOB,'platform':platform.platform(),
            'uid':os.geteuid(),'source_archive_sha256':sha(after),'cases':cases,
            'scope':'Linux installed real Builder, not release/performance/portability'}
if __name__=='__main__':
    out=main()
    path=Path(os.environ.get('O78_JSON','o78-evidence/result.json'))
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'head':out['head'],'cases':[(x['kind'],x['status']) for x in out['cases']]}))
