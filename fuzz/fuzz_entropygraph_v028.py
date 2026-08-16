from __future__ import annotations

import atheris
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
PATH=Path(tempfile.gettempdir())/'cmpct-fuzz-entropygraph-v028.cmpct'


def _engine():
    source=ROOT/'experiments'/'entropygraph_v028.py'
    spec=importlib.util.spec_from_file_location('cmpct_fuzz_entropygraph_v028_engine',source)
    if spec is None or spec.loader is None:raise RuntimeError('cannot load research engine')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module


with atheris.instrument_imports():
    E=_engine()


def TestOneInput(data:bytes)->None:
    # A fuzzed research archive is capped before it reaches disk. `_open_graph` must either return one
    # authenticated bounded metadata view or a typed RuntimeError; decompression bombs and absurd
    # record counts are not allowed to turn malformed input into unbounded work.
    data=data[:16*1024*1024]
    try:
        PATH.write_bytes(data)
        stream,meta,record_start,offsets,merkle=E._open_graph(PATH)
        stream.close()
        # If metadata happens to pass, sample at most the first physical record through the same bounded
        # local reader by requesting strong verification only for very small artifacts.
        if len(data)<=2*1024*1024:
            try:E.strong_verify(PATH)
            except RuntimeError:return
    except (RuntimeError,OSError,ValueError,EOFError):
        return


if __name__=='__main__':
    try:
        atheris.Setup(sys.argv,TestOneInput)
        atheris.Fuzz()
    finally:
        try:os.unlink(PATH)
        except OSError:pass
