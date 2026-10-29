#!/usr/bin/env python3
"""External Info-ZIP/UnZip content conformance of 41 original J24G30 hosted exports.

No CMPCT import; zipfile opens the outer GitHub Actions transport only. The
unzip executable handles the original inner ZIP, independently of the product.
"""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);args=ap.parse_args()
root=args.artifacts
with zipfile.ZipFile(root/'j30-physical-original.zip') as z:manifest=json.loads(z.read('manifest.json'))
records=[];failures=[]
for host in ['linux','mac','win']:
 with zipfile.ZipFile(root/f'j30-{host}-original.zip') as z:
  names=set(z.namelist())
  for mode,prefix in [('baseline','j30-old-out'),('candidate','j30-new-out')]:
   for case,e in manifest['cases'].items():
    inner=f'{prefix}/{case}.zip'
    if inner not in names:
     assert host=='win' and mode=='baseline' and case=='negative_epoch'
     continue
    raw=z.read(inner)
    with tempfile.TemporaryDirectory() as d:
     file=Path(d)/'physical.zip';file.write_bytes(raw)
     run=subprocess.run(['unzip','-tq',str(file)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
     if run.returncode!=0:
      failures.append({'host':host,'mode':mode,'case':case,'test_exit':run.returncode,'stderr':run.stderr[:500],'stdout':run.stdout[:500]});continue
     archive_files=subprocess.run(['unzip','-Z1',str(file)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True).stdout.splitlines()
     assert len(archive_files)==1
     data=subprocess.run(['unzip','-p',str(file),archive_files[0]],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
     logical=hashlib.sha256(data).hexdigest()
     assert logical==e['payload_sha256'],(host,mode,case,'wrong decompressed bytes')
     records.append({'host':host,'mode':mode,'case':case,'original_zip_sha256':hashlib.sha256(raw).hexdigest(),'unzip_tq':'PASS','independent_payload_sha256':logical})
assert not failures,failures
assert len(records)==41,len(records)
print(json.dumps({'schema':'j24g31-external-infozip-original-hosted-conformance-v1',
                  'independent_unzip_6_00_zip_exports':len(records),'defects':failures,
                  'scope':'UnZip 6.00 -tq/-p output semantics on exact original hosted ZIP objects; excludes mtime filesystem ownership and >4GiB ZIP64',
                  'records':records},indent=2))
