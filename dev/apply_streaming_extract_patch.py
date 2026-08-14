from pathlib import Path

p = Path("src/cmpct/reader.py")
s = p.read_text()

# Footnote: Builder is an encoder dependency and is unused by the reader. Keeping this import made
# read-only CLI startup initialize encoder-only machinery before archive open.
s = s.replace(
    "from .codec import _hash_sparse, _wav_parts, _ld, _sz, _z, _zck\nfrom .builder import Builder\n",
    "from .codec import _hash_sparse, _wav_parts, _ld, _sz, _z, _zck\n",
)

needle = """        if storage[0]==S_VZIP:return range_vzip(self.recipes[storage[1]],self._blob,self._stream,start,length)\n        return self.read(name)[start:end]\n    def _restore_extra_metadata(self,clean):\n"""
insert = """        if storage[0]==S_VZIP:return range_vzip(self.recipes[storage[1]],self._blob,self._stream,start,length)\n        return self.read(name)[start:end]\n\n    def _extract_chunked_verified(self,row,full:str):\n        \"\"\"Stream a chunked logical file to disk and commit it only after whole-file verification.\n\n        Footnote: ``read()`` deliberately returns one contiguous ``bytes`` object for API callers, but\n        extraction does not need that ownership model. The old extraction path decoded every chunk,\n        joined the complete logical file, hashed the joined copy, and only then copied it again into the\n        destination. ZIP's streaming extractor never pays that extra whole-file allocation/copy. This\n        path preserves CMPCT's stronger SHA-256 check while hashing each decoded chunk as it is written.\n\n        The temporary file is created beside the final destination and atomically replaced only after\n        size + SHA verification. That retains the previous corruption behavior: a damaged archive cannot\n        truncate a pre-existing destination merely because streaming began before integrity was known.\n        \"\"\"\n        rel,k,mode,mt,size,h,storage=row;sk=storage[0]\n        if sk==S_CHUNKS:\n            ids=list(storage[1]);lengths=[self.blobs[idx][1] for idx in ids]\n        elif sk==S_CDC:\n            lengths=[int(x[0]) for x in storage[1]];ids=[x[1] for x in storage[1]]\n        else:raise ValueError('chunked extraction requires fixed or CDC storage')\n\n        if len(ids)>=4:\n            if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))\n            decoded=self._executor.map(self._blob,ids)\n        else:\n            decoded=(self._blob(idx) for idx in ids)\n\n        parent=os.path.dirname(full) or '.';prefix=f'.{os.path.basename(full)}.cmpct-part-'\n        fd,tmp=tempfile.mkstemp(prefix=prefix,dir=parent);committed=False\n        digest=hashlib.sha256();written=0\n        try:\n            # Match the ordinary extraction path's requested basic mode even though mkstemp starts at\n            # 0600. Extended metadata restoration still remains governed by extractall(metadata=...).\n            try:os.fchmod(fd,mode or 0o666)\n            except OSError:pass\n            for expected,b in zip(lengths,decoded):\n                if len(b)!=expected:raise IOError(f'chunk length failure while extracting {rel}')\n                digest.update(b);written+=len(b);view=memoryview(b)\n                while view:\n                    n=os.write(fd,view)\n                    if n<=0:raise IOError(f'short write while extracting {rel}')\n                    view=view[n:]\n            if written!=size or h is None or digest.digest()!=bytes(h):\n                raise IOError(f'file integrity failure: {rel}')\n            os.close(fd);fd=-1\n            os.replace(tmp,full);committed=True\n        finally:\n            if fd>=0:\n                try:os.close(fd)\n                except OSError:pass\n            if not committed:\n                try:os.unlink(tmp)\n                except FileNotFoundError:pass\n\n    def _restore_extra_metadata(self,clean):\n"""
if needle not in s:
    raise SystemExit("reader insertion point no longer matches; refuse blind rewrite")
s = s.replace(needle, insert, 1)

needle = """            if storage and storage[0]==S_SPARSE:\n                # Create the logical length first, then write only allocated data extents. The gaps\n                # remain filesystem holes instead of consuming disk blocks full of zeros.\n"""
replace = """            if storage and storage[0] in (S_CHUNKS,S_CDC):\n                self._extract_chunked_verified(row,full)\n            elif storage and storage[0]==S_SPARSE:\n                # Create the logical length first, then write only allocated data extents. The gaps\n                # remain filesystem holes instead of consuming disk blocks full of zeros.\n"""
if needle not in s:
    raise SystemExit("extractall branch no longer matches; refuse blind rewrite")
s = s.replace(needle, replace, 1)

p.write_text(s)
