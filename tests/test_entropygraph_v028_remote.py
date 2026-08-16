from __future__ import annotations

from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import importlib.util
from pathlib import Path
import random
import re
import sys
import threading

import pytest

ROOT=Path(__file__).resolve().parents[1]


def _load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def _source(root:Path)->Path:
    src=root/'source';src.mkdir();rng=random.Random(0xA11CE028)
    # Several independent bounded objects ensure one remote read does not need the whole archive.
    for i in range(24):
        (src/f'object-{i:02d}.bin').write_bytes(bytes(rng.getrandbits(8) for _ in range(180_000+i*101)))
    return src


class _RangeHandler(BaseHTTPRequestHandler):
    archive:Path
    def log_message(self,*args):pass
    def do_GET(self):
        data=self.archive.read_bytes();value=self.headers.get('Range','')
        match=re.fullmatch(r'bytes=(\d+)-(\d+)',value)
        suffix=re.fullmatch(r'bytes=-(\d+)',value)
        if match:
            start,end=map(int,match.groups())
        elif suffix:
            length=int(suffix.group(1));start=max(0,len(data)-length);end=len(data)-1
        else:
            self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if start<0 or end<start or end>=len(data):self.send_response(416);self.end_headers();return
        body=data[start:end+1]
        self.send_response(206);self.send_header('Content-Length',str(len(body)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{len(data)}');self.send_header('Accept-Ranges','bytes')
        self.end_headers();self.wfile.write(body)


def _serve(archive:Path):
    handler=type('RangeHandler',(_RangeHandler,),{'archive':archive})
    server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    return server,f'http://127.0.0.1:{server.server_port}/archive.cmpct'


def test_http_range_reader_fetches_only_touched_records(tmp_path:Path):
    engine=_load(ROOT/'experiments'/'entropygraph_v028.py','cmpct_remote_test_engine')
    remote_mod=_load(ROOT/'experiments'/'entropygraph_v028_remote.py','cmpct_remote_test_reader')
    src=_source(tmp_path);archive=tmp_path/'remote.cmpct';engine._build_graph(src,archive)
    server,url=_serve(archive)
    try:
        source=remote_mod.HTTPRangeSource(url);graph=remote_mod.RemoteGraph(source)
        target=(src/'object-07.bin').read_bytes();got=graph.read_range('object-07.bin',31_337,4096)
        assert got==target[31_337:31_337+4096]
        stats=graph.stats()
        # Footnote: this proves the server really transferred less than the archive, not merely that the
        # API exposed a `range()` method while a hidden HTTP client downloaded everything underneath it.
        assert stats['bytes_transferred']<stats['archive_bytes']
        assert stats['transfer_ratio']<0.40
    finally:server.shutdown();server.server_close()


def test_remote_physical_leaf_corruption_fails_before_returning_bytes(tmp_path:Path):
    engine=_load(ROOT/'experiments'/'entropygraph_v028.py','cmpct_remote_corrupt_engine')
    remote_mod=_load(ROOT/'experiments'/'entropygraph_v028_remote.py','cmpct_remote_corrupt_reader')
    src=_source(tmp_path);archive=tmp_path/'corrupt-remote.cmpct';engine._build_graph(src,archive)
    stream,meta,record_start,offsets,_=engine._open_graph(archive);stream.close();assert offsets
    payload=bytearray(archive.read_bytes());header_at=record_start+offsets[0]
    codec,usize,csize,crc,logical_sha=engine.PH.unpack(payload[header_at:header_at+engine.PH.size]);assert csize>0
    payload[header_at+engine.PH.size+csize//2]^=1;archive.write_bytes(payload)
    server,url=_serve(archive)
    try:
        graph=remote_mod.RemoteGraph(remote_mod.HTTPRangeSource(url))
        with pytest.raises(RuntimeError,match='Merkle leaf'):
            graph._record(0)
    finally:server.shutdown();server.server_close()


def test_server_without_range_support_is_rejected(tmp_path:Path):
    archive=tmp_path/'x';archive.write_bytes(b'x'*100)
    class NoRange(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            body=archive.read_bytes();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),NoRange);threading.Thread(target=server.serve_forever,daemon=True).start()
    remote_mod=_load(ROOT/'experiments'/'entropygraph_v028_remote.py','cmpct_remote_strict_reader')
    try:
        with pytest.raises(RuntimeError,match='status 200'):
            remote_mod.HTTPRangeSource(f'http://127.0.0.1:{server.server_port}/x')
    finally:server.shutdown();server.server_close()
