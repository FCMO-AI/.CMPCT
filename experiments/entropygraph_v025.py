"""
CMPCT EntropyGraph v0.25 research engine.

This executable prototype is deliberately separate from the canonical revision-24 reader/writer.
It exists to make the EntropyGraph representation experiments reproducible on public/synthetic
corpora before any reader-visible storage semantics are promoted into the canonical format.

Footnote: source/archive paths are caller-supplied.  No private corpus name, machine path, or
project-external provenance is part of this public experiment.
"""
from __future__ import annotations
from pathlib import Path
import struct,binascii,ctypes,ctypes.util,hashlib,zipfile,shutil,time,statistics,msgpack,os,json,zlib,gzip,lzma,bz2,argparse,tempfile
ROOT=Path('.');OUT=Path('entropygraph-experimental.cmpct');TARGET=512*1024
MAG=b'CMPNX5\0\0';TAIL=b'CMNXT5T\0';HDR=struct.Struct('<8sQQI32s');FTR=struct.Struct('<8sQQ32s');PH=struct.Struct('<BQQI32s') # codec, usize, csize, hot CRC32, strong SHA-256
z=ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so');sz=ctypes.c_size_t
z.ZSTD_compressBound.argtypes=[sz];z.ZSTD_compressBound.restype=sz;z.ZSTD_compress.argtypes=[ctypes.c_void_p,sz,ctypes.c_void_p,sz,ctypes.c_int];z.ZSTD_compress.restype=sz;z.ZSTD_decompress.argtypes=[ctypes.c_void_p,sz,ctypes.c_void_p,sz];z.ZSTD_decompress.restype=sz
def zc(b,l=19):
 if not b:return b''
 s=ctypes.create_string_buffer(b);cap=int(z.ZSTD_compressBound(len(b)));d=ctypes.create_string_buffer(cap);n=int(z.ZSTD_compress(d,cap,s,len(b),l));return d.raw[:n]
def zd(b,n):
 if not n:return b''
 s=ctypes.create_string_buffer(b);d=ctypes.create_string_buffer(n);g=int(z.ZSTD_decompress(d,n,s,len(b)));assert g==n;return d.raw[:g]
def H(b):return hashlib.sha256(b).digest()

def treehash(root):
 h=hashlib.sha256()
 for p in sorted(q for q in root.rglob('*') if q.is_file()):
  r=p.relative_to(root).as_posix().encode();d=p.read_bytes();h.update(len(r).to_bytes(4,'little'));h.update(r);h.update(len(d).to_bytes(8,'little'));h.update(d)
 return h.hexdigest()

# Build returns full artifact. Footnote: all representation choices are reversible and size-competed;
# no source bytes are discarded. Strong identity is carried by authenticated pack hashes + the authenticated reconstruction graph.
def build():
 t0=time.perf_counter();files=sorted(p for p in ROOT.rglob('*') if p.is_file());rels={p:p.relative_to(ROOT).as_posix() for p in files};raws={p:p.read_bytes() for p in files}
 # 1) Federate ZIP-like compressed member streams across the *whole archive*, not just inside one file.
 # Footnote: the old gate asked "does this container alone contain >=512 KiB of duplicated streams?".
 # That misses realistic document families where DOCX/PPTX/XLSX packages share assets and boilerplate
 # across sibling files.  We first inspect candidates without committing bytes, then accept a container
 # only if it has strong local duplication OR participates in a profitable cross-container stream graph.
 special={};stream_pool=bytearray();stream_slot={};stream_meta=[];zip_probe={};stream_containers={};member_plain={}
 for p in files:
  raw=raws[p]
  if not raw.startswith(b'PK\x03\x04') or len(raw)<4096:continue
  try:
   with zipfile.ZipFile(p) as ar: infos=sorted([i for i in ar.infolist() if not i.is_dir()],key=lambda x:x.header_offset);plain_by_offset={i.header_offset:ar.read(i) for i in infos if i.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED)}
   spans=[];sids=[];local={};members=[]
   for zi in infos:
    v=struct.unpack_from('<IHHHHHIIIHH',raw,zi.header_offset);nl,xl=v[-2],v[-1];s=zi.header_offset+30+nl+xl;e=s+zi.compress_size;b=raw[s:e];hh=H(b)
    local.setdefault(hh,b);sids.append(hh);spans.append((s,e));stream_containers.setdefault(hh,set()).add(p)
    # Footnote: record only a content hash and the cheap inverse transform.  The member bytes are not
    # retained here, so inspection cannot accidentally turn into hidden duplicate payload.
    if zi.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED):
     pb=plain_by_offset[zi.header_offset];ph=H(pb);member_plain.setdefault(ph,[]).append((p,hh,zi.compress_type,len(pb),len(b)));members.append((ph,hh,zi.compress_type,len(pb),len(b)))
   local_dup=sum(e-s for s,e in spans)-sum(len(b) for b in local.values())
   lits=[];lens=[];cur=0
   for s,e in spans:lits.append(raw[cur:s]);lens.append(s-cur);cur=e
   lits.append(raw[cur:]);lens.append(len(raw)-cur)
   zip_probe[p]={'local':local,'local_dup':local_dup,'sids':sids,'spans':spans,'skeleton':b''.join(lits),'literal_lens':lens,'members':members}
  except Exception:pass
 top_by_hash={}
 for tp in files:top_by_hash.setdefault(H(raws[tp]),[]).append(tp)
 for p,zp in zip_probe.items():
  shared_unique=sum(len(b) for hh,b in zp['local'].items() if len(stream_containers.get(hh,()))>1)
  seen_plain=set();external_match=0
  for ph,hh,method,usize,csize in zp['members']:
   if ph in seen_plain:continue
   seen_plain.add(ph)
   if any(tp!=p for tp in top_by_hash.get(ph,())):external_match+=csize
  # Footnote: a container can now earn virtualization in three independent ways: local stream dedup,
  # cross-container stream dedup, or cross-representation reuse with loose files.  The latter is what
  # makes ordinary backups with both `folder/` and `folder.zip` visible to the optimizer.
  if zp['local_dup'] < 512*1024 and shared_unique < 32*1024 and external_match < 32*1024:continue
  for hh,b in zp['local'].items():
   if hh not in stream_slot:
    off=len(stream_pool);stream_pool+=b;stream_slot[hh]=(off,len(b));stream_meta.append([hh,off,len(b)])
  special[p]={'type':'zipstreams','skeleton':zp['skeleton'],'literal_lens':zp['literal_lens'],'stream_hashes':zp['sids'],
              'local_dup':zp['local_dup'],'shared_unique':shared_unique,'external_match':external_match}
 # 1b) Entropy-oriented representation inversion.
 # A standalone object that is byte-identical to a member plaintext need not be stored if the exact
 # compressed member stream is already required by an accepted container.  Store the lower-entropy
 # stream and derive the raw file by the *cheap* inverse transform (inflate), never by recompression.
 retained_streams=set(stream_slot);derived={}
 for p in files:
  if p in special or len(raws[p])<32*1024:continue
  opts=[]
  for cp,hh,method,usize,csize in member_plain.get(H(raws[p]),[]):
   if cp in special and hh in retained_streams and usize==len(raws[p]):opts.append((csize,hh,method,usize))
  if opts:
   csize,hh,method,usize=min(opts)
   # Footnote: the stream already exists for another logical file, so this representation has zero
   # new payload bytes.  The 32 KiB floor keeps tiny objects from buying dependency metadata for crumbs.
   derived[p]={'stream_hash':hh,'method':method,'usize':usize,'csize':csize}
 # 1c) Generic inverse-transform edges for ordinary compressed sidecars.
 # Footnote: if `file.log.gz` is already a required logical file and inflates exactly to `file.log`,
 # storing the loose file again is redundant.  We only admit transforms with a standard, deterministic,
 # cheap inverse and an exact SHA-256 equality proof.  No filename assumption is trusted by itself.
 decode_derived={};raw_hash_paths={}
 for tp in files:raw_hash_paths.setdefault(H(raws[tp]),[]).append(tp)
 decoder_rank={'zstd':0,'gzip':1,'bzip2':2,'xz':3}
 for cp in files:
  suf=cp.suffix.lower();codec=None;plain=None
  try:
   if suf=='.gz':codec='gzip';plain=gzip.decompress(raws[cp])
   elif suf=='.xz':codec='xz';plain=lzma.decompress(raws[cp])
   elif suf=='.bz2':codec='bzip2';plain=bz2.decompress(raws[cp])
   elif suf=='.zst':
    # Zstandard frame size is not needed for detection; the matching loose file provides the exact output size.
    codec='zstd'
    for tp in files:
     if tp==cp or len(raws[tp])<32*1024:continue
     try:
      cand=zd(raws[cp],len(raws[tp]))
      if H(cand)==H(raws[tp]):plain=cand;break
     except Exception:pass
   if plain is None or len(plain)<32*1024:continue
   ph=H(plain)
   for tp in raw_hash_paths.get(ph,()):
    if tp==cp or tp in special or tp in derived:continue
    opt=(decoder_rank[codec],len(raws[cp]),cp,codec)
    if tp not in decode_derived or opt[:2] < decode_derived[tp][:2]:decode_derived[tp]=opt
  except Exception:pass
 # 2) Generic exact sub-file references among remaining top-level files. Use whole-object matches >=32 KiB;
 # this discovers the QA PDF's embedded JPEGs without a PDF-specific parser.
 splice={};candidates=[p for p in files if p not in special and len(raws[p])>=32*1024]
 for parent in candidates:
  pr=raws[parent];hits=[]
  for child in candidates:
   if child==parent or len(raws[child])>=len(pr):continue
   pos=pr.find(raws[child])
   if pos>=0:hits.append((pos,pos+len(raws[child]),child))
  hits.sort(key=lambda x:(x[0],-(x[1]-x[0])))
  chosen=[];end=-1
  for h in hits:
   if h[0]>=end:chosen.append(h);end=h[1]
  if sum(e-s for s,e,_ in chosen)>=128*1024:splice[parent]=chosen
 # Internal objects to bounded packs. Special containers contribute skeletons, spliced parents contribute residual literals.
 objs=[];obj_by_key={};file_desc={};special_skel_key={};splice_res_key={};splice_lens={}
 def addobj(key,fam,b):
  if key not in obj_by_key:obj_by_key[key]=len(objs);objs.append([key,fam,b])
  return obj_by_key[key]
 for p in files:
  if p in special:
   k=('skel',rels[p]);special_skel_key[p]=k;addobj(k,'.zip-skeleton',special[p]['skeleton']);continue
  if p in derived:
   continue
  if p in decode_derived:
   continue
  if p in splice:
   hits=splice[p];cur=0;lits=[];lens=[]
   for s,e,ch in hits:lits.append(raws[p][cur:s]);lens.append(s-cur);cur=e
   lits.append(raws[p][cur:]);lens.append(len(raws[p])-cur)
   res=b''.join(lits);k=('splice',rels[p]);splice_res_key[p]=k;splice_lens[p]=lens;addobj(k,p.suffix.lower(),res);continue
  k=('file',rels[p]);addobj(k,p.suffix.lower(),raws[p])
 # Pack by family with <=512 KiB physical decode units. Oversize objects are independently chunked.
 # Similar path order preserves local context; cryptographic hash order is intentionally avoided.
 # 3) Exact object interning across logical files and residual objects.
 # Footnote: prior revisions content-addressed *relationships* but still stored identical top-level
 # objects independently.  Here identical bytes are interned once before physical packing.  This is
 # family-agnostic because equality is stronger than a filename/extension hint; aliases keep their own
 # logical paths while sharing one authenticated physical representation.
 content_owner={};aliases={};unique=[]
 for key,ff,b in objs:
  hh=H(b)
  if hh in content_owner:
   aliases[key]=content_owner[hh]
  else:
   content_owner[hh]=key;unique.append([key,ff,b])
 objs=unique
 objs.sort(key=lambda x:(x[1],str(x[0])))
 # 4) Adaptive bounded-context audition.
 # Footnote: a fixed 32 KiB solid threshold protects locality but throws away cross-file context in source trees.
 # A global 512 KiB threshold fixes ratio by harming unrelated workloads.  Instead, each file family auditions
 # 32/64/128/256/512 KiB packs with cheap Zstd-3 probes.  Wider context is promoted only when it proves a
 # material byte win, and 512 KiB is a hard ceiling -- never worse than CMPCT's existing large-file decode unit.
 def probe_cost(group,limit):
  cost=0;buf=bytearray()
  def emit():
   nonlocal cost,buf
   if not buf:return
   raw=bytes(buf);comp=zc(raw,3);cost+=min(len(raw),len(comp))+PH.size;buf=bytearray()
  for key,ff,b in group:
   if len(b)>limit:
    emit()
    # Objects above the candidate solid limit are unchanged by this decision, so omit their common cost.
    continue
   if buf and len(buf)+len(b)>limit:emit()
   buf+=b
  emit();return cost
 family_limits={};families={}
 for row in objs:families.setdefault(row[1],[]).append(row)
 for ff,group in families.items():
  eligible=[r for r in group if len(r[2])<=TARGET]
  if len(eligible)<2:family_limits[ff]=32*1024;continue
  trials=[]
  for lim in (32,64,128,256,512):trials.append((probe_cost(eligible,lim*1024),lim*1024))
  base=trials[0][0];best=min(trials)
  # Footnote: require both an absolute and relative win so probe noise/metadata crumbs cannot buy locality debt.
  family_limits[ff]=best[1] if base-best[0]>=max(2048,int(base*0.005)) else 32*1024
 packs=[];objmap={};cur=bytearray();slots=[];fam=None
 def flush():
  nonlocal cur,slots,fam
  if not cur:return
  raw=bytes(cur);comp=zc(raw,19);codec=1 if len(comp)+8<len(raw) else 0;payload=comp if codec else raw;pi=len(packs);packs.append([codec,len(raw),payload,binascii.crc32(raw)&0xffffffff,H(raw)])
  for key,off,ln in slots:objmap[key]=[['slice',pi,off,ln]]
  cur=bytearray();slots=[];fam=None
 for key,ff,b in objs:
  solid_limit=family_limits.get(ff,32*1024)
  if len(b)>solid_limit:
   flush();refs=[]
   for o in range(0,len(b),TARGET):
    part=b[o:o+TARGET];comp=zc(part,19);codec=1 if len(comp)+8<len(part) else 0;payload=comp if codec else part;pi=len(packs);packs.append([codec,len(part),payload,binascii.crc32(part)&0xffffffff,H(part)]);refs.append(['whole',pi,len(part)])
   objmap[key]=refs;continue
  if cur and (ff!=fam or len(cur)+len(b)>solid_limit):flush()
  if fam is None:fam=ff
  off=len(cur);cur+=b;slots.append((key,off,len(b)))
 flush()
 # Footnote: aliases are metadata-only logical views; no duplicate payload or duplicate pack header is emitted.
 for alias,owner in aliases.items():objmap[alias]=objmap[owner]
 # Compressed-stream pools are usually entropy-dense, but 'already compressed' is only a hypothesis.
 # They therefore compete against a cheap secondary Zstd pass rather than receiving a hard STORE exemption.
 stream_packs=[];hot_hashes={dd['stream_hash'] for dd in derived.values()};hot_stream_slabs=0
 if stream_pool:
  # Footnote: derived loose files are latency-sensitive inverse views.  Their source Deflate stream is
  # therefore a *hot root*: it gets stream-aligned <=TARGET slabs and STORE by default, avoiding a second
  # decompression layer before inflate.  Cold container-only streams may share bounded slabs and compete
  # with cheap Zstd-3.  The logical global offsets remain unchanged, so existing recipes stay compact.
  entries=sorted((off,hh,n) for hh,off,n in stream_meta);cold=[]
  def emit_range(so,part,hot=False):
   nonlocal hot_stream_slabs
   if hot:codec=0;payload=part;hot_stream_slabs+=1
   else:
    comp=zc(part,3);codec=1 if len(comp)+8<len(part) else 0;payload=comp if codec else part
   pi=len(packs);packs.append([codec,len(part),payload,binascii.crc32(part)&0xffffffff,H(part)]);stream_packs.append([so,pi,len(part)])
  def flush_cold():
   nonlocal cold
   if not cold:return
   so=cold[0][0];end=cold[-1][0]+cold[-1][2];raw=bytes(stream_pool[so:end])
   for o in range(0,len(raw),TARGET):emit_range(so+o,raw[o:o+TARGET],False)
   cold=[]
  for off,hh,n in entries:
   if hh in hot_hashes:
    flush_cold();raw=bytes(stream_pool[off:off+n])
    for o in range(0,n,TARGET):emit_range(off+o,raw[o:o+TARGET],True)
   else:
    if cold and off+n-cold[0][0]>TARGET:flush_cold()
    cold.append((off,hh,n))
  flush_cold();stream_packs.sort(key=lambda x:x[0])
 # Build logical file recipes.
 path_index={rels[p]:i for i,p in enumerate(files)}
 for p in files:
  if p in special:
   ss=special[p];file_desc[rels[p]]=['zipstreams',objmap[special_skel_key[p]],ss['literal_lens'],[[stream_slot[h][0],stream_slot[h][1]] for h in ss['stream_hashes']],len(raws[p])]
   # Footnote: stream slices inherit integrity from the SHA-256-authenticated stream pool pack and
   # authenticated metadata offsets; repeating a random 32-byte hash for every slice adds no protection.
  elif p in derived:
   dd=derived[p];o,n=stream_slot[dd['stream_hash']];file_desc[rels[p]]=['inflate_stream',o,n,dd['method'],dd['usize']]
   # Footnote: the derived file is cryptographically determined by authenticated recipe + stream-pool SHA.
  elif p in decode_derived:
   rank,src_size,cp,codec=decode_derived[p];file_desc[rels[p]]=['decode_file',rels[cp],codec,len(raws[p])]
   # Footnote: source compressed file remains a normal logical file; this edge removes only duplicate payload.
  elif p in splice:
   file_desc[rels[p]]=['splice',objmap[splice_res_key[p]],splice_lens[p],[rels[ch] for s,e,ch in splice[p]],len(raws[p])]
   # Footnote: source byte offsets were dead metadata; residual literal lengths already define reconstruction positions.
  else:file_desc[rels[p]]=['plain',objmap[('file',rels[p])],len(raws[p])]
 # Footnote: per-file SHA-256 values were redundant random metadata. Pack SHA-256 + metadata authentication +
 # the tree root already form a proof-carrying reconstruction graph, so deleting them preserves strong integrity.
 # 5) Implicit micro-pack index.
 # Footnote: when a pack is exactly the concatenation of independently named small files, offsets are
 # mathematical consequences of the preceding lengths.  Encoding nested `plain/slice/pack/offset`
 # recipes per file is redundant and especially punitive on tiny-file trees.
 micro=[];by_pi={}
 for path,d in list(file_desc.items()):
  if d[0]=='plain' and len(d[1])==1 and d[1][0][0]=='slice':
   _,pi,o,n=d[1][0];by_pi.setdefault(pi,[]).append((o,n,path))
 for pi,ents in by_pi.items():
  ents.sort();cur=0;ok=True
  for o,n,path in ents:
   if o!=cur:ok=False;break
   cur+=n
  if ok and cur==packs[pi][1]:
   micro.append([pi,[[path,n] for o,n,path in ents]])
   for o,n,path in ents:del file_desc[path]
 meta={'v':4,'target':TARGET,'stream_packs':stream_packs,'files':[[r,file_desc[r]] for r in sorted(file_desc)],'micro':micro,'pack_count':len(packs),'tree_sha256':treehash(ROOT)}
 mb=msgpack.packb(meta,use_bin_type=True);mc=zc(mb,12)
 with open(OUT,'wb') as f:
  # Footnote: the benchmark candidate keeps CMPCT's recovery semantics in the byte count.
  # The primary metadata is authenticated, and a second authenticated copy is stored at the tail.
  # This intentionally spends real bytes rather than waiving recovery overhead for a prettier ratio.
  mh=H(mb);f.write(HDR.pack(MAG,len(mc),len(mb),len(packs),mh));f.write(mc)
  for codec,u,pay,crc,hh in packs:f.write(PH.pack(codec,u,len(pay),crc,hh));f.write(pay)
  f.write(mc);f.write(FTR.pack(TAIL,len(mc),len(mb),mh))
 return {'create_s':time.perf_counter()-t0,'meta_raw':len(mb),'meta_comp':len(mc),'packs':len(packs),'stream_pool':len(stream_pool),'stream_slabs':len(stream_packs),'hot_stream_slabs':hot_stream_slabs,'special':len(special),'derived':len(derived),'decode_derived':len(decode_derived),'object_aliases':len(aliases),'micro_groups':len(micro),'splices':len(splice),'family_solid_limits':{k:v for k,v in family_limits.items() if v>32*1024}}

def open_ar():
 # Footnote: CMPNX5 makes the redundant tail metadata operational rather than decorative.  The primary
 # copy is attempted first; if its header, compressed bytes, or authentication hash fail, the reader
 # recovers the same metadata from the commit footer and derives the original pack-table start from it.
 f=open(OUT,'rb');primary_error=None;m=None;mcs=None
 try:
  f.seek(0);hb=f.read(HDR.size)
  if len(hb)!=HDR.size:raise RuntimeError('short header')
  magic,pmcs,pmus,pnp,pmh=HDR.unpack(hb)
  if magic!=MAG:raise RuntimeError('primary magic')
  mc=f.read(pmcs);mb=zd(mc,pmus)
  if H(mb)!=pmh:raise RuntimeError('primary metadata authentication')
  m=msgpack.unpackb(mb,raw=False);mcs=pmcs
 except Exception as e:
  primary_error=e
 if m is None:
  try:
   f.seek(-FTR.size,os.SEEK_END);fb=f.read(FTR.size)
   if len(fb)!=FTR.size:raise RuntimeError('short footer')
   tail,tmcs,tmus,tmh=FTR.unpack(fb)
   if tail!=TAIL:raise RuntimeError('tail magic')
   footer_off=f.tell()-FTR.size;meta_off=footer_off-tmcs
   if meta_off < HDR.size:raise RuntimeError('tail metadata offset')
   f.seek(meta_off);mc=f.read(tmcs);mb=zd(mc,tmus)
   if H(mb)!=tmh:raise RuntimeError('tail metadata authentication')
   m=msgpack.unpackb(mb,raw=False);mcs=tmcs
  except Exception as tail_error:
   f.close();raise RuntimeError(f'no authenticated metadata copy: primary={primary_error!r}; tail={tail_error!r}')
 if m.get('v')!=4:
  f.close();raise RuntimeError('unsupported CMPNX5 metadata version')
 np=int(m['pack_count']);pack_start=HDR.size+mcs;f.seek(pack_start);po=[]
 for _ in range(np):
  hb=f.read(PH.size)
  if len(hb)!=PH.size:f.close();raise RuntimeError('truncated pack header')
  codec,u,c,crc,hh=PH.unpack(hb);off=f.tell();po.append((off,codec,u,c,crc,hh));f.seek(c,1)
 return f,m,po

def extract(dst):
 shutil.rmtree(dst,ignore_errors=True);dst.mkdir(parents=True);f,m,po=open_ar();cache={};fd=dict(m['files']);stream_packs=m.get('stream_packs',[]);building=set();fcache={}
 for pi,ents in m.get('micro',[]):
  off=0
  for path,n in ents:fd[path]=['plain',[['slice',pi,off,n]],n];off+=n
 # Footnote: expansion is in-memory only; the compact on-disk form still preserves direct path lookup after open.
 def pack(i):
  if i in cache:return cache[i]
  off,codec,u,c,crc,hh=po[i];f.seek(off);p=f.read(c);b=zd(p,u) if codec==1 else p
  # Footnote: ordinary extraction mirrors CMPCT's intended hot integrity tier: CRC32 is checked while
  # SHA-256 remains stored and authoritative for explicit strong verification. This matches ZIP's
  # normal CRC semantics instead of charging CMPCT a full cryptographic verify on every normal read.
  if len(b)!=u or (binascii.crc32(b)&0xffffffff)!=crc:raise RuntimeError('pack integrity')
  cache[i]=b;return b
 def stream_slice(o,n):
  # Footnote: logical stream offsets remain stable even though physical slabs are bounded.  A slice may
  # cross at most the slabs it geometrically overlaps; no unrelated multi-megabyte pool is materialized.
  e=o+n;out=[]
  for so,pi,sn in stream_packs:
   se=so+sn
   if se<=o:continue
   if so>=e:break
   a=max(o,so)-so;b=min(e,se)-so;out.append(pack(pi)[a:b])
  raw=b''.join(out)
  if len(raw)!=n:raise RuntimeError('stream slice')
  return raw
 def obj(refs):
  out=[]
  for r in refs:
   if r[0]=='slice':_,pi,o,n=r;out.append(pack(pi)[o:o+n])
   else:_,pi,n=r;out.append(pack(pi)[:n])
  return b''.join(out)
 def filebytes(path):
  if path in fcache:return fcache[path]
  if path in building:raise RuntimeError('cycle')
  building.add(path);d=fd[path];typ=d[0]
  if typ=='plain':b=obj(d[1]);ln=d[2]
  elif typ=='zipstreams':
   sk=obj(d[1]);lens=d[2];streams=d[3];parts=[];q=0
   for i,(o,n) in enumerate(streams):parts.append(sk[q:q+lens[i]]);q+=lens[i];parts.append(stream_slice(o,n))
   parts.append(sk[q:q+lens[-1]]);b=b''.join(parts);ln=d[4]
  elif typ=='inflate_stream':
   o,n,method,ln=d[1],d[2],d[3],d[4];sb=stream_slice(o,n)
   b=zlib.decompress(sb,-15) if method==zipfile.ZIP_DEFLATED else sb
  elif typ=='decode_file':
   src=filebytes(d[1]);codec=d[2];ln=d[3]
   if codec=='gzip':b=gzip.decompress(src)
   elif codec=='xz':b=lzma.decompress(src)
   elif codec=='bzip2':b=bz2.decompress(src)
   elif codec=='zstd':b=zd(src,ln)
   else:raise ValueError(codec)
  elif typ=='splice':
   res=obj(d[1]);lens=d[2];hits=d[3];parts=[];q=0
   for i,child in enumerate(hits):parts.append(res[q:q+lens[i]]);q+=lens[i];parts.append(filebytes(child))
   parts.append(res[q:q+lens[-1]]);b=b''.join(parts);ln=d[4]
  else:raise ValueError(typ)
  if len(b)!=ln:raise RuntimeError('file length '+path)
  building.remove(path);fcache[path]=b;return b
 for path in sorted(fd):
  b=filebytes(path);q=dst/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 f.close()

def strong_verify():
 # Footnote: ordinary reads intentionally use CRC32 for ZIP-comparable hot corruption detection.  Strong
 # verification is explicit: authenticate metadata, SHA-256 every decoded physical pack, then reconstruct
 # the logical tree and compare its canonical tree hash to the authenticated root.
 f,m,po=open_ar()
 try:
  for i,(off,codec,u,c,crc,hh) in enumerate(po):
   f.seek(off);payload=f.read(c)
   if len(payload)!=c:raise RuntimeError(f'truncated pack {i}')
   b=zd(payload,u) if codec==1 else payload
   if len(b)!=u or (binascii.crc32(b)&0xffffffff)!=crc:raise RuntimeError(f'pack CRC {i}')
   if H(b)!=hh:raise RuntimeError(f'pack SHA-256 {i}')
  expected=m['tree_sha256']
 finally:f.close()
 with tempfile.TemporaryDirectory(prefix='cmpct-verify-') as td:
  extract(Path(td));got=treehash(Path(td))
 if got!=expected:raise RuntimeError(f'logical tree SHA-256 mismatch: {got} != {expected}')
 return {'ok':True,'tree_sha256':got,'packs':len(po),'metadata_version':m['v']}

def _bench():
 builds=[];info=None
 for _ in range(3):info=build();builds.append(info['create_s'])
 with tempfile.TemporaryDirectory(prefix='cmpct-bench-') as td:
  dst=Path(td);ext=[]
  for _ in range(5):t=time.perf_counter();extract(dst);ext.append(time.perf_counter()-t)
  if treehash(dst)!=treehash(ROOT):raise RuntimeError('benchmark tree mismatch')
 r=dict(info);r.update({'bytes':OUT.stat().st_size,'create_median_s':statistics.median(builds),'extract_median_s':statistics.median(ext),'tree_sha256':treehash(ROOT),'extract_raw':ext})
 return r

def _main():
 global ROOT,OUT
 ap=argparse.ArgumentParser(description='CMPCT EntropyGraph v0.25 experimental benchmark engine (CMPNX5)')
 sp=ap.add_subparsers(dest='cmd',required=True)
 p=sp.add_parser('pack');p.add_argument('source',type=Path);p.add_argument('archive',type=Path)
 p=sp.add_parser('extract');p.add_argument('archive',type=Path);p.add_argument('destination',type=Path)
 p=sp.add_parser('verify');p.add_argument('archive',type=Path)
 p=sp.add_parser('bench');p.add_argument('source',type=Path);p.add_argument('archive',type=Path)
 a=ap.parse_args()
 if a.cmd=='pack':ROOT=a.source;OUT=a.archive;print(json.dumps(build(),indent=2,default=str))
 elif a.cmd=='extract':OUT=a.archive;extract(a.destination);print(json.dumps({'ok':True,'destination':str(a.destination)},indent=2))
 elif a.cmd=='verify':OUT=a.archive;print(json.dumps(strong_verify(),indent=2))
 elif a.cmd=='bench':ROOT=a.source;OUT=a.archive;print(json.dumps(_bench(),indent=2,default=str))

if __name__=='__main__':_main()
