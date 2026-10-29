# J24I05: compaction and filesystem symlink preservation — preregistration

Scope: research only, published main `80c358f8824ec1b20d349c92ed94c898090969b0`, revision 24. Initial source-derived hypothesis is filed in issue #718. Record this prediction before implementation or measurement.

Prediction: the published Builder can create an authentic archive containing an absolute or parent-relative symlink target; Reader and verify accept its exact target bytes; compaction rejects these archives because its temporary reconstruction uses the ordinary safe extraction policy. Positive controls are an archive containing a safe relative link and one containing only regular files. Preserve source hashes, exact outputs, exception classes and an external sentinel.

Disproof: Builder/read/verify reject the source, compaction accepts/reconstructs both restricted targets, or positive controls fail for unrelated reasons. The experiment only establishes compatibility behavior on the measured host; it does not authorize disabling the normal extraction guard or changing archive format and release gates.

Alternatives: no change to product in this court. A later design could reconstruct inert link targets as bytes, or use a carefully isolated extraction root after evaluating symlink parent and filesystem mutation risks. Keep all security invariants and coordinate with existing Reader, hardlink and compaction owners.

Evidence rung: direct installed-source hosted Ubuntu experiment, with a source-authentic physical archive, a separate comparator for target bytes, and explicit positive and negative controls. Scientific finding only; no product improvement, CI victory or release claimed until measurements are observed. No Discovery STATE mutation.
