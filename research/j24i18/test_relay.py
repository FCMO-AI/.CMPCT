"""J24I18 hosted result-bearing court for physical-record relay.

Generate authentic Builder and append-update artifacts. Do not rely solely on the
relay's own index parser: compare real CMPCT Reader bytes/metadata and independent
physical header/record SHA checks. This court does not certify secure publication.
"""
import hashlib, os, pathlib, subprocess, sys, tempfile, unittest
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_update
from physical_relay import read_index, read_blobs, sha

class PhysicalRelayCourt(unittest.TestCase):
    def test_genuine_updated_archive(self):
        with tempfile.TemporaryDirectory() as td:
            home=pathlib.Path(td);root=home/'tree';root.mkdir()
            old=b'FROZEN-BASE-OWNER-'*1024
            new=b'NEW-OWNER-CONTENT-'*1024
            (root/'b-owner.bin').write_bytes(old)
            (root/'note.txt').write_text('real metadata and archive data',encoding='utf8')
            os.link(root/'b-owner.bin',root/'alias.bin')
            archive=home/'original.cmpct'
            Builder(root,reproducible=True).build(archive)
            changed=home/'changed.bin';changed.write_bytes(new)
            append_update(archive,'b-owner.bin',changed)
            result_dir=home/'out';result_dir.mkdir()
            script=pathlib.Path(__file__).with_name('live_blob_relay.py')
            proc=subprocess.run([sys.executable,str(script),'--output-dir',str(result_dir),str(archive)],
                                check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            print('J24I18_RESULT',proc.stdout.strip(),flush=True)
            result=result_dir/'original.cmpct'
            with CMPCT(archive) as a, CMPCT(result) as b:
                self.assertEqual([row[0] for row in a.files],[row[0] for row in b.files])
                self.assertEqual(a.index['fsmeta'],b.index['fsmeta'])
                self.assertEqual(a.index['features'],b.index['features'])
                self.assertEqual(a.read('b-owner.bin'),new)
                self.assertEqual(a.read('alias.bin'),new)
                for row in a.files:
                    self.assertEqual(row[:6],b.by[row[0]][:6],'preserve signed member metadata and topology')
                    if row[1]==3:self.assertEqual(row[6],b.by[row[0]][6],'preserve hardlink target')
                    if row[1] != 1:
                        self.assertEqual(a.read(row[0]),b.read(row[0]))
            original_data=archive.read_bytes();result_data=result.read_bytes()
            ai,ab,ad=read_index(original_data);bi,bb,bd=read_index(result_data)
            self.assertEqual(ad,1)
            self.assertEqual(bd,0)
            original_records=read_blobs(original_data,ai,ab)
            result_records=read_blobs(result_data,bi,bb)
            self.assertTrue(len(result_records)<len(original_records),'dead original blob must be pruned')
            self.assertEqual(sha(result_data),hashlib.sha256(result_data).digest())
            print('J24I18_PHYSICAL',{
                'original_bytes':len(original_data),'relay_bytes':len(result_data),
                'source_sha256':sha(original_data).hex(),'result_sha256':sha(result_data).hex(),
                'all_live_blobs_authenticated':True,
                'original_count':len(original_records),'relay_count':len(result_records)},flush=True)

if __name__=='__main__':
    unittest.main()
