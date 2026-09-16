"""Hardened execution entrypoint for the CMPNX14 Geometry IR research archive.

Import order is part of the research safety contract.  CMPNX14 reuses CMPNX13's G0/G1/G2 node audition;
the raw CMPNX13 module predates the later ragged-delimiter cell-work guard.  Importing the safety facade
first patches that shared module object, then loading GIR guarantees both flat delimiter Geometry and the
new hierarchical transforms obey bounded writer/reader work.

Footnote: this indirection is intentionally visible rather than silently copied into a second implementation.
Before any promotion, the safety import should be folded into the final owning module and the direct/raw
entrypoint should be removed or made impossible to invoke without the same guard.
"""
from __future__ import annotations

from experiments import entropygraph_v030_geometry_safe as _geometry_safe  # noqa: F401
from experiments import entropygraph_v030_gir as gir

build = gir.build
_build_gir = gir._build_gir
extract = gir.extract
strong_verify = gir.strong_verify
treehash = gir.treehash
_safe_relpath = gir._safe_relpath
_decode_meta = gir._decode_meta
_open = gir._open
_materialize_files = gir._materialize_files
MAG = gir.MAG
TAIL = gir.TAIL
HDR = gir.HDR
FTR = gir.FTR
H = gir.H
zc = gir.zc
zd = gir.zd
PH = gir.PH
BASE = gir.BASE
MAX_CHUNK = gir.MAX_CHUNK
MAX_DECODE_UNIT = gir.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = gir.MAX_DECODER_MEMORY
HG = gir.HG
G = gir.G

if __name__ == "__main__":
    gir._main()
