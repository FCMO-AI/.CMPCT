#!/usr/bin/env python3
"""J24F07 cross-source verification of unchanged J24F05 source-writer hostile court.

The inherited J24F05 evaluator pins the *old* Reader blob. The ONLY adjusted
identity is the composed Reader blob, authenticated both here and by CI. Its
inherited eight hostile cases and pass/fail rules execute unchanged. This
wrapper does not patch test outcomes, subprocess race hooks, source or Reader.
"""
from __future__ import annotations
import sys
from pathlib import Path
import j24f05_raw_window_court as inherited

SOURCE_BLOB = "a29421456c7c8d46157490fa03594a4c620a483d"
assert inherited.READER_BLOB == "41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e"
inherited.READER_BLOB = SOURCE_BLOB
if __name__ == "__main__":
    assert "--output" in sys.argv
    inherited.main()
