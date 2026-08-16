"""HTTP/object-store range reader for the EntropyGraph-II research grammar.

This is a research proof, not canonical revision-24 remote support. It fetches the authenticated metadata
once, performs O(1) logical-path lookup from that in-memory map, and then requests only the physical
records needed by a member/range. Direct/delta records retain the same decode and integrity ceilings as
the local research reader.

Footnote: the current CMPNX8 metadata is still fetched as one bounded block. This demonstrates in-place
object-store querying and touched-record authentication, but it is not yet the future bucketed index +
O(log N) Merkle-proof design that would keep index transfer sublinear on enormous archives.
"""
from __future__ import annotations

import binascii
import importlib.util
import msgpack
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

from cmpct.resemblance import delta_decode

HERE=Path(__file__).resolve().parent


def _engine():
    path=HERE/'entropygraph_v028.py'
    spec=importlib.util.spec_from_file_location('cmpct_entropygraph_v028_remote_engine',path)
    if spec is None or spec.loader is None:raise RuntimeError('cannot load EntropyGraph-II engine')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module


E=_engine()
MAX_METADATA=64*1024*1024


class HTTPRangeSource:
    """Strict HTTP byte-range source with transfer accounting.

    A server that ignores Range and returns the entire object is rejected. Silent fallback would make a
    range benchmark look correct while secretly downloading the archive, exactly the kind of hidden cost
    CMPCT's engineering standard forbids.
    """
    def __init__(self,url:str,*,timeout:float=30.0):
        self.url=url;self.timeout=timeout;self.transferred=0;self.requests=0
        data,headers=self._request('bytes=0-0')
        match=re.fullmatch(r'bytes\s+0-0/(\d+)',headers.get('Content-Range','').strip(),re.I)
        if len(data)!=1 or not match:raise RuntimeError('HTTP source does not provide strict byte ranges')
        self.size=int(match.group(1))
    def _request(self,range_value:str):
        req=Request(self.url,headers={'Range':range_value,'Accept-Encoding':'identity'})
        with urlopen(req,timeout=self.timeout) as response:
            status=getattr(response,'status',response.getcode())
            if status!=206:raise RuntimeError(f'HTTP range request returned status {status}, expected 206')
            data=response.read();headers=response.headers
        self.requests+=1;self.transferred+=len(data)
        return data,headers
    def read(self,start:int,length:int)->bytes:
        if start<0 or length<0 or start>self.size or length>self.size-start:raise ValueError('range outside object')
        if length==0:return b''
        data,headers=self._request(f'bytes={start}-{start+length-1}')
        expected=f'bytes {start}-{start+length-1}/{self.size}'
        if headers.get('Content-Range','').strip().lower()!=expected.lower() or len(data)!=length:
            raise RuntimeError('HTTP server returned the wrong byte range')
        return data
    def suffix(self,length:int)->bytes:
        if length<=0 or length>self.size:raise ValueError('invalid suffix length')
        data,headers=self._request(f'bytes=-{length}')
        expected_start=self.size-length
        expected=f'bytes {expected_start}-{self.size-1}/{self.size}'
        if headers.get('Content-Range','').strip().lower()!=expected.lower() or len(data)!=length:
            raise RuntimeError('HTTP server returned the wrong suffix range')
        return data


class RemoteGraph:
    def __init__(self,source:HTTPRangeSource):
        self.source=source;self.record_cache={};self.node_cache={}
        self.meta,self.record_start,self.offsets,self.merkle=self._open()
        self.files=self.meta['files'];self.nodes=self.meta['nodes']
    def _decode_meta(self,comp:bytes,raw_size:int,expected_sha:bytes,expected_merkle:bytes,
                     expected_count:int|None=None,declared_decode:int|None=None,declared_memory:int|None=None):
        if raw_size<0 or raw_size>MAX_METADATA:raise RuntimeError('remote metadata exceeds limit')
        raw=E.zd(comp,raw_size)
        if E.H(raw)!=expected_sha:raise RuntimeError('remote metadata authentication')
        meta=msgpack.unpackb(raw,raw=False,strict_map_key=False)
        if meta.get('v')!=1 or int(meta.get('max_dependency_depth',99))>1:raise RuntimeError('unsupported remote graph metadata')
        decode=int(meta.get('max_decode_unit',E.MAX_DECODE_UNIT+1));memory=int(meta.get('max_decoder_memory',E.MAX_DECODER_MEMORY+1))
        if decode>E.MAX_DECODE_UNIT or (declared_decode is not None and decode!=declared_decode):raise RuntimeError('remote decode ceiling')
        if memory>E.MAX_DECODER_MEMORY or (declared_memory is not None and memory!=declared_memory):raise RuntimeError('remote decoder-memory ceiling')
        leaves=list(meta.get('record_leaf_sha256',[]));offsets=list(meta.get('record_rel_offsets',[]))
        if expected_count is not None and len(leaves)!=expected_count:raise RuntimeError('remote record count')
        if len(offsets)!=len(leaves) or E._merkle_root(leaves)!=expected_merkle:raise RuntimeError('remote Merkle metadata')
        return meta,offsets
    def _open(self):
        primary_error=None
        try:
            header=self.source.read(0,E.HDR.size)
            magic,mcs,mus,count,max_decode,max_memory,meta_sha,merkle=E.HDR.unpack(header)
            if magic!=E.MAG:raise RuntimeError('not EntropyGraph-II')
            if mcs>MAX_METADATA or mus>MAX_METADATA:raise RuntimeError('remote metadata exceeds limit')
            if max_decode>E.MAX_DECODE_UNIT or max_memory>E.MAX_DECODER_MEMORY:raise RuntimeError('remote resource declaration')
            comp=self.source.read(E.HDR.size,mcs)
            meta,offsets=self._decode_meta(comp,mus,meta_sha,merkle,count,max_decode,max_memory)
            return meta,E.HDR.size+mcs,offsets,merkle
        except Exception as exc:primary_error=exc
        try:
            footer=E.FTR.unpack(self.source.suffix(E.FTR.size))
            magic,mcs,mus,meta_sha,merkle=footer
            if magic!=E.TAIL or mcs>MAX_METADATA or mus>MAX_METADATA:raise RuntimeError('invalid remote tail metadata')
            footer_start=self.source.size-E.FTR.size;meta_start=footer_start-mcs
            if meta_start<E.HDR.size:raise RuntimeError('remote tail metadata offset')
            comp=self.source.read(meta_start,mcs)
            meta,offsets=self._decode_meta(comp,mus,meta_sha,merkle)
            return meta,E.HDR.size+mcs,offsets,merkle
        except Exception as tail_error:
            raise RuntimeError(f'no authenticated remote metadata copy: primary={primary_error!r}; tail={tail_error!r}') from tail_error
    def _record(self,record_id:int)->bytes:
        if record_id in self.record_cache:return self.record_cache[record_id]
        if not 0<=record_id<len(self.offsets):raise RuntimeError('remote record id out of range')
        start=self.record_start+self.offsets[record_id]
        header=self.source.read(start,E.PH.size)
        codec,usize,csize,crc,logical_sha=E.PH.unpack(header)
        if usize>E.MAX_DECODE_UNIT or csize>E.MAX_DECODER_MEMORY:raise RuntimeError('remote physical record exceeds resource limit')
        payload=self.source.read(start+E.PH.size,csize)
        if E.H(payload)!=self.meta['record_leaf_sha256'][record_id]:raise RuntimeError('remote physical Merkle leaf mismatch')
        if codec==E.CODEC_RAW:raw=payload
        elif codec==E.CODEC_ZSTD:raw=E.zd(payload,usize)
        elif codec==E.CODEC_PREFLATE:raw=E._preflate_unpack(payload,usize)
        else:raise RuntimeError('unknown remote physical codec')
        if len(raw)!=usize or (binascii.crc32(raw)&0xffffffff)!=crc or E.H(raw)!=logical_sha:raise RuntimeError('remote physical record integrity')
        self.record_cache[record_id]=raw;return raw
    def _node(self,node_id:int)->bytes:
        if node_id in self.node_cache:return self.node_cache[node_id]
        if not 0<=node_id<len(self.nodes):raise RuntimeError('remote node id out of range')
        desc=self.nodes[node_id]
        if desc[0]=='direct':
            _,record_id,offset,length,expected=desc;pack=self._record(record_id)
            if offset>len(pack) or length>len(pack)-offset:raise RuntimeError('remote direct slice bounds')
            raw=pack[offset:offset+length]
        elif desc[0]=='delta':
            _,base_id,record_id,length,expected=desc
            if self.nodes[base_id][0]!='direct':raise RuntimeError('remote delta dependency depth')
            raw=delta_decode(self._node(base_id),self._record(record_id),expected_size=length,max_output=E.MAX_CHUNK)
        else:raise RuntimeError('unknown remote node description')
        if E.H(raw)!=expected:raise RuntimeError('remote node SHA-256 mismatch')
        self.node_cache[node_id]=raw;return raw
    def read_range(self,path:str,start:int,length:int)->bytes:
        desc=self.files.get(path)
        if desc is None:raise KeyError(path)
        size=int(desc[2])
        if start<0 or length<0 or start>size:raise ValueError('logical range outside member')
        end=min(size,start+length)
        if end<=start:return b''
        if desc[0]=='preflate':
            raw=self._record(desc[1])
            if len(raw)!=size or E.H(raw)!=desc[3]:raise RuntimeError('remote preflate file identity')
            return raw[start:end]
        if desc[0]!='nodes':raise RuntimeError('unknown remote file description')
        out=bytearray();logical=0
        for node_id in desc[1]:
            node_desc=self.nodes[node_id];node_len=int(node_desc[3])
            node_end=logical+node_len
            if node_end>start and logical<end:
                raw=self._node(node_id);left=max(start,logical)-logical;right=min(end,node_end)-logical
                out.extend(raw[left:right])
            logical=node_end
            if logical>=end:break
        if logical<size and end==size:
            # A full-to-EOF request must prove the node table accounts for the authenticated file size.
            for node_id in desc[1][len(desc[1]):]:logical+=int(self.nodes[node_id][3])
        if len(out)!=end-start:raise RuntimeError('remote node accounting mismatch')
        return bytes(out)
    def read(self,path:str)->bytes:
        desc=self.files.get(path)
        if desc is None:raise KeyError(path)
        raw=self.read_range(path,0,int(desc[2]))
        if E.H(raw)!=desc[3]:raise RuntimeError('remote complete-file SHA-256 mismatch')
        return raw
    def stats(self)->dict:
        return {'http_requests':self.source.requests,'bytes_transferred':self.source.transferred,'archive_bytes':self.source.size,
                'transfer_ratio':self.source.transferred/max(1,self.source.size)}
