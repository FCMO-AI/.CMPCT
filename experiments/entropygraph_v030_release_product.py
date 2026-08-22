"""CMPCT v0.30 promoted release-product front door.

The mature r24/r25 selector implementation is retained byte-for-byte in
``entropygraph_v030_release_product_base``.  This public module first exposes that exact implementation, then
binds the structurally admitted logs-inverse profile that earned all-15 shadow, native production-dispatch and
Android/JNI promotion evidence on the parent fingerprint.  Non-logs sources therefore execute the frozen mature
delegates captured by the promoted wrapper; no benchmark name participates in dispatch.

Release authority remains the ordinary v0.30 authority.  This module does not weaken the v0.29 floor, ZIP/Zstd
per-workload size/create requirements, locality/decode ceilings, integrity, recovery, native or Android gates.
"""
from __future__ import annotations

from experiments import entropygraph_v030_release_product_base as _BASE_IMPL

# Populate the public module with the exact mature implementation before importing the logs wrapper.  The wrapper
# imports this module and captures these delegates at import time; that capture is what prevents recursive fallback
# after the public operations below are rebound to the promoted selector.
for _name in dir(_BASE_IMPL):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_BASE_IMPL, _name)

from experiments import entropygraph_v030_release_product_logs_candidate as _LOGS_PROMOTED

# Only product operations/classification are rebound.  Constants, ablation machinery and mature helper functions
# remain the exact base implementation, preserving every non-logs byte path while making C25LG12 a real product
# profile rather than a shadow facade.
build = _LOGS_PROMOTED.build
strong_verify = _LOGS_PROMOTED.strong_verify
list_members = _LOGS_PROMOTED.list_members
read_member_with_stats = _LOGS_PROMOTED.read_member_with_stats
read_member = _LOGS_PROMOTED.read_member
extract = _LOGS_PROMOTED.extract
_revision_for_archive = _LOGS_PROMOTED._revision_for_archive

LOGS = _LOGS_PROMOTED.LOGS
LOGS_MAGIC = _LOGS_PROMOTED.LOGS_MAGIC
LOGS_TAIL = _LOGS_PROMOTED.LOGS_TAIL
LOGS_PROFILE = _LOGS_PROMOTED.LOGS_PROFILE
logs_source_prefilter = _LOGS_PROMOTED.logs_source_prefilter

PROMOTED_LOGS_INVERSE = True
PROMOTED_LOGS_EVIDENCE = (
    "all-15 structural admission + external/v0.29 selector shadows + native production dispatch + Android/JNI"
)
