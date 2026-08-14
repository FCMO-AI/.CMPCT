"""Compatibility facade for the CMPCT v0.24 reference implementation.

Footnote: older chat-local tests imported Builder/CMPCT from cmpct.core. Keep that surface stable while
the canonical project is refactored into modules; removing this facade would create churn with no
format benefit.
"""
from .builder import Builder, Candidate
from .reader import CMPCT
from .transactions import (append_update, append_delete, append_rename, recover_blob_records,
                           compact_archive, tree_digest)
from .cli import main

__all__ = [
    "Builder", "Candidate", "CMPCT", "append_update", "append_delete", "append_rename",
    "recover_blob_records", "compact_archive", "tree_digest", "main",
]
