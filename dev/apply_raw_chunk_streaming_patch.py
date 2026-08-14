from pathlib import Path

reader = Path('src/cmpct/reader.py')
text = reader.read_text()
old = '''    def _extract_chunked_verified(self,row,full:str):
        """Stream a chunked logical file to disk and commit it only after whole-file verification.

        Footnote: ``read()`` deliberately returns one contiguous ``bytes`` object for API callers, but
        extraction does not need that ownership model. The old extraction path decoded every chunk,
        joined the complete logical file, hashed the joined copy, and only then copied it again into the
        destination. ZIP's streaming extractor never pays that extra whole-file allocation/copy. This
        path preserves CMPCT's stronger SHA-256 check while hashing each decoded chunk as it is written.

        The temporary file is created beside the final destination and atomically replaced only after
        size + SHA verification. That retains the previous corruption behavior: a damaged archive cannot
        truncate a pre-existing destination merely because streaming began before integrity was known.
        """
        rel,k,mode,mt,size,h,storage=row;sk=storage[0]
        if sk==S_CHUNKS:
            ids=list(storage[1]);lengths=[self.blobs[idx][1] for idx in ids]
        elif sk==S_CDC:
            lengths=[int(x[0]) for x in storage[1]];ids=[x[1] for x in storage[1]]
        else:raise ValueError('chunked extraction requires fixed or CDC storage')

        if len(ids)>=4:
            if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
            decoded=self._executor.map(self._blob,ids)
        else:
            decoded=(self._blob(idx) for idx in ids)

        parent=os.path.dirname(full) or '.';prefix=f'.{os.path.basename(full)}.cmpct-part-'
        fd,tmp=tempfile.mkstemp(prefix=prefix,dir=parent);committed=False
        digest=hashlib.sha256();written=0
        try:
            # Match the ordinary extraction path's requested basic mode even though mkstemp starts at
            # 0600. Extended metadata restoration still remains governed by extractall(metadata=...).
            try:os.fchmod(fd,mode or 0o666)
            except OSError:pass
            for expected,b in zip(lengths,decoded):
                if len(b)!=expected:raise IOError(f'chunk length failure while extracting {rel}')
                digest.update(b);written+=len(b);view=memoryview(b)
                while view:
                    n=os.write(fd,view)
                    if n<=0:raise IOError(f'short write while extracting {rel}')
                    view=view[n:]
            if written!=size or h is None or digest.digest()!=bytes(h):
                raise IOError(f'file integrity failure: {rel}')
            os.close(fd);fd=-1
            os.replace(tmp,full);committed=True
        finally:
            if fd>=0:
                try:os.close(fd)
                except OSError:pass
            if not committed:
                try:os.unlink(tmp)
                except FileNotFoundError:pass
'''
new = '''    def _raw_blob_view_for_extract(self,idx:int):
        """Return a zero-copy mmap view for a RAW chunk used by verified extraction.

        Footnote: chunked extraction already authenticates the complete logical file with SHA-256 before
        atomically replacing the destination. Routing RAW chunks through ``_blob`` first copied every
        mmap slice into Python bytes, CRC32-checked it, and retained it in the read cache, only for the
        extractor to hash and write the same bytes again. The whole-file SHA is stronger than that
        redundant per-chunk CRC for this staging path, so RAW chunks can stay mmap-backed while framing
        is still cross-checked against the authenticated index. Ordinary random reads keep `_blob`'s
        CRC/cache behavior unchanged.
        """
        off,us,cs,codec,ml=self.blobs[idx]
        if codec!=CODEC_RAW:raise ValueError('RAW extraction view requested for compressed blob')
        pos=self.record_base+off
        if pos<0 or pos+BHDR.size>len(self.mm):raise IOError('blob header outside archive')
        m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos)
        if m!=BMAGIC or c!=CODEC_RAW or rus!=us or rcs!=cs or rml!=ml or rcs!=rus:
            raise IOError('RAW blob header mismatch')
        start=pos+BHDR.size+rml;end=start+rcs
        if start<0 or end>len(self.mm):raise IOError('RAW blob payload outside archive')
        return memoryview(self.mm)[start:end]

    def _extract_chunked_verified(self,row,full:str):
        """Stream a chunked logical file to disk and commit it only after whole-file verification.

        Footnote: ``read()`` deliberately returns one contiguous ``bytes`` object for API callers, but
        extraction does not need that ownership model. The old extraction path decoded every chunk,
        joined the complete logical file, hashed the joined copy, and only then copied it again into the
        destination. ZIP's streaming extractor never pays that extra whole-file allocation/copy. This
        path preserves CMPCT's stronger SHA-256 check while hashing each decoded chunk as it is written.

        The temporary file is created beside the final destination and atomically replaced only after
        size + SHA verification. That retains the previous corruption behavior: a damaged archive cannot
        truncate a pre-existing destination merely because streaming began before integrity was known.
        """
        rel,k,mode,mt,size,h,storage=row;sk=storage[0]
        if sk==S_CHUNKS:
            ids=list(storage[1]);lengths=[self.blobs[idx][1] for idx in ids]
        elif sk==S_CDC:
            lengths=[int(x[0]) for x in storage[1]];ids=[x[1] for x in storage[1]]
        else:raise ValueError('chunked extraction requires fixed or CDC storage')

        # Fully incompressible chunked files are common in disk images, encrypted data and media. Keep
        # those bytes mmap-backed all the way into SHA-256 + write(2); compressed/mixed files retain the
        # parallel decoder because decompression, rather than copying, dominates their hot path.
        raw_direct=bool(ids) and all(self.blobs[idx][3]==CODEC_RAW for idx in ids)
        if raw_direct:
            decoded=(self._raw_blob_view_for_extract(idx) for idx in ids)
        elif len(ids)>=4:
            if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
            decoded=self._executor.map(self._blob,ids)
        else:
            decoded=(self._blob(idx) for idx in ids)

        parent=os.path.dirname(full) or '.';prefix=f'.{os.path.basename(full)}.cmpct-part-'
        fd,tmp=tempfile.mkstemp(prefix=prefix,dir=parent);committed=False
        digest=hashlib.sha256();written=0
        try:
            # Match the ordinary extraction path's requested basic mode even though mkstemp starts at
            # 0600. Extended metadata restoration still remains governed by extractall(metadata=...).
            try:os.fchmod(fd,mode or 0o666)
            except OSError:pass
            for expected,b in zip(lengths,decoded):
                try:
                    if len(b)!=expected:raise IOError(f'chunk length failure while extracting {rel}')
                    digest.update(b);written+=len(b);view=memoryview(b)
                    try:
                        while view:
                            n=os.write(fd,view)
                            if n<=0:raise IOError(f'short write while extracting {rel}')
                            view=view[n:]
                    finally:
                        try:view.release()
                        except ValueError:pass
                finally:
                    if raw_direct and isinstance(b,memoryview):b.release()
            if written!=size or h is None or digest.digest()!=bytes(h):
                raise IOError(f'file integrity failure: {rel}')
            os.close(fd);fd=-1
            os.replace(tmp,full);committed=True
        finally:
            if fd>=0:
                try:os.close(fd)
                except OSError:pass
            if not committed:
                try:os.unlink(tmp)
                except FileNotFoundError:pass
'''
if old not in text:
    raise SystemExit('target extraction block not found')
reader.write_text(text.replace(old,new))

# Add a focused regression proving the fast path is genuinely zero-copy/cache-free and still SHA-safe.
test = Path('tests/test_streaming_extract.py')
t = test.read_text()
append = '''\n\ndef test_raw_chunk_extract_uses_mmap_without_populating_blob_cache(tmp_path: Path):\n    src = tmp_path / "src"\n    src.mkdir()\n    # Deterministic high-entropy bytes avoid an os.urandom-dependent regression while defeating the\n    # current Zstd candidate threshold strongly enough to select RAW chunks.\n    import random\n    rng = random.Random(0xC0DEC7)\n    payload = rng.randbytes(3 * 1024 * 1024)\n    (src / "random.bin").write_bytes(payload)\n    archive = tmp_path / "random.cmpct"\n    Builder(src).build(archive)\n\n    out = tmp_path / "out"\n    with CMPCT(archive) as ar:\n        storage = ar.by["random.bin"][6]\n        assert storage[0] in (S_CHUNKS, S_CDC)\n        ids = storage[1] if storage[0] == S_CHUNKS else [entry[1] for entry in storage[1]]\n        assert ids and all(ar.blobs[idx][3] == 0 for idx in ids)\n        ar.extractall(out, metadata=False)\n        # The extraction-only RAW path must not retain every chunk in the general random-read cache.\n        assert not any(idx in ar.cache for idx in ids)\n\n    assert (out / "random.bin").read_bytes() == payload\n'''
if 'test_raw_chunk_extract_uses_mmap_without_populating_blob_cache' not in t:
    test.write_text(t+append)
