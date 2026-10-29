#!/usr/bin/env python3
"""Detached r24 signed metadata -> hosted ZIP32 filename/type/mode continuity.

Not a test for xattrs, ownership, hardlinks, POSIX filesystem materialization,
or Windows-file mode mappings. Single regular specimen per r24 source.
"""
import argparse,hashlib,json,stat,struct,subprocess,zipfile
from pathlib import Path
import msgpack
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
root=a.artifacts;H=struct.Struct('<8sHHQQQ32s');C=struct.Struct('<IHHHHHHIIIHHHHHII');E=struct.Struct('<IHHHHIIH')
with zipfile.ZipFile(root/'j30-physical-original.zip') as z:
 manifest=json.loads(z.read('manifest.json'));rows={}
 for case,v in manifest['cases'].items():
  b=z.read(v['archive']);m,ver,flags,cs,us,ds,ih=H.unpack_from(b)
  assert m==b'CMPCT24\0' and ver==24
  raw=subprocess.run(['zstd','-q','-d','-c'],input=b[H.size:H.size+cs],stdout=subprocess.PIPE,check=True).stdout
  assert hashlib.sha256(raw).digest()==ih
  files=msgpack.unpackb(raw,raw=False)['files']; assert len(files)==1
  name,kind,mode,mtime,size,auth,storage=files[0]
  assert kind==0 and mode<=0o7777 and size==833 and mtime==v['mtime_ns']
  rows[case]={'name':name,'mode':mode,'mtime_ns':mtime,'size':size}
checked=0;output=[]
for host in ('linux','mac','win'):
 with zipfile.ZipFile(root/f'j30-{host}-original.zip') as z:
  names=set(z.namelist())
  for mode,prefix in (('baseline','j30-old-out'),('candidate','j30-new-out')):
   for case,e in rows.items():
    key=f'{prefix}/{case}.zip'
    if key not in names:
     assert host=='win' and mode=='baseline' and case=='negative_epoch';continue
    b=z.read(key);eo=E.unpack_from(b,len(b)-E.size);cd_offset=eo[6]
    central=C.unpack_from(b,cd_offset)
    name_len=central[10];name=b[cd_offset+C.size:cd_offset+C.size+name_len]
    assert name==e['name'].encode('utf-8'),(host,mode,case,'name')
    assert central[1]>>8==3,(host,mode,case,'non-Unix creator')
    expected=stat.S_IFREG|e['mode']
    assert central[15]>>16==expected,(host,mode,case,'lost file kind/mode',oct(central[15]>>16),oct(expected))
    assert central[9]==e['size'],(host,mode,case,'logical size')
    output.append({'host':host,'mode':mode,'case':case,'signed_mtime_ns':e['mtime_ns'],
                   'name':e['name'],'mode_octal':oct(e['mode']),'zip_external_attr':hex(central[15]),
                   'zip_method':central[4]})
    checked+=1
assert checked==41
print(json.dumps({'schema':'j24g31-r24-zip-fsmetadata-parity-v1','original_exports':checked,
                  'source':'Independent r24 primary index and original ZIP central directory; no product Reader',
                  'scope':'one regular file per specimen, preserves filename/type/mode/size; not filesystem extraction, ownership, xattrs or hardlink graph',
                  'records':output},indent=2))
