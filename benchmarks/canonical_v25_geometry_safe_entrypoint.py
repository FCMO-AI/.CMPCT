"""Production-hardening entrypoint for the canonical r25 Geometry focused gate.

The historical benchmark imports ``canonical_v25_geometry`` directly.  Import this module instead so the
same frozen corpus/threshold logic runs against the successor footer contract whose tail index carries and
validates ``record_base`` independently of the primary header.

Footnote: the wrapper patches only the r25 evidence writer/reader names consumed by the benchmark.  The
benchmark identities and frozen size thresholds remain exactly those already committed; recovery hardening
cannot improve a failing compression result by changing the workload or gate.
"""
from experiments import canonical_v25_geometry as V25
from experiments import canonical_v25_geometry_recovery as SAFE

V25.compile_r24_to_r25 = SAFE.compile_r24_to_r25
V25.CMPCTV25 = SAFE.CMPCTV25
V25.build_candidate = SAFE.build_candidate

from benchmarks import canonical_v25_geometry_probe as IMPL  # noqa: E402


if __name__ == "__main__":
    IMPL.main()
