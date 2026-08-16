from __future__ import annotations

import atheris
import os
from pathlib import Path
import tempfile

with atheris.instrument_imports():
    from cmpct.validation import ParserLimits,ValidationError,preflight_archive

PATH=Path(tempfile.gettempdir())/'cmpct-fuzz-preflight.cmpct'
LIMITS=ParserLimits(
    max_index_bytes=2*1024*1024,
    max_generation_bytes=2*1024*1024,
    max_blob_bytes=8*1024*1024,
    max_files=20_000,
    max_blobs=20_000,
    max_recipes=5_000,
    max_path_bytes=64*1024,
    max_delta_depth=32,
)


def TestOneInput(data:bytes)->None:
    # Footnote: keep the target's own filesystem write bounded so fuzzing the parser cannot become a
    # disk-exhaustion workload. ValidationError/ordinary I/O refusal is expected; MemoryError,
    # AssertionError and unexpected parser exceptions are intentionally not swallowed.
    data=data[:8*1024*1024]
    try:
        PATH.write_bytes(data)
        preflight_archive(PATH,limits=LIMITS)
    except (ValidationError,OSError,ValueError,EOFError):
        return


if __name__=='__main__':
    try:
        atheris.Setup(__import__('sys').argv,TestOneInput)
        atheris.Fuzz()
    finally:
        try:os.unlink(PATH)
        except OSError:pass
