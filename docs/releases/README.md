# CMPCT core releases

Numeric CMPCT project versions are intentionally scarce. A new numeric version is reserved for a material improvement to CMPCT itself: archive/engine capability, compression or speed, reliability, recovery, portability/interoperability, or another product-level behavior that materially advances the format.

Website polish, documentation cleanup, repository presentation, workflow ergonomics, and other non-format surface work do **not** receive a new numeric project version. Those changes use the alphabetic `SURFACE_REVISION` track (`x.x.a`, `x.x.b`, …) attached to the current major/minor core line.

Core releases still require a release note in this directory and fresh benchmark evidence under `benchmarks/history/`. Surface revisions do not manufacture release notes or benchmark records merely to justify presentation work.

Historical notes remain immutable evidence of the policy that existed when they were created. In particular, legacy patch releases such as v0.27.1 are not rewritten; the scarce-version policy applies prospectively.

Footnote: the Python package keeps a numeric `MAJOR.MINOR.PATCH` field for packaging compatibility. After the legacy 0.27.1 checkpoint, normal core advancement moves the `MAJOR.MINOR` line and uses `PATCH=0`; presentation-only work stays on `SURFACE_REVISION`.
