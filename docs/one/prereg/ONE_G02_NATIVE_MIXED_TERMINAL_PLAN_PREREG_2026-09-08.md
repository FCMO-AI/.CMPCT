# ONE-G0.2 Native Mixed Terminal Plan — preregistration

## Mission lock / falsifiable hypothesis

Prepared terminal plans removed graph walking and Fill-schedule construction but left 1 MiB `long_runs` and `structured` about 17–19% slower than literal reconstruction. The remaining specific hypothesis is that Python-side Surprise scatter plus crossing separate Python/native write paths is now material. If so, lowering the **same validated terminal Surprise/Fill/Concat Program** once into one bounded mixed COPY/FILL schedule and replaying it through one native call per root should remove that penalty.

Disproof: HOLD if any exact semantic/root result changes, any row exceeds 1.05x literal wall or CPU, any row exceeds 1.05x the existing prepared replay, the 1 MiB `long_runs` row does not reach <=0.90x prepared wall+CPU, the 1 MiB `structured` row does not reach <=0.95x prepared wall+CPU, or incremental mixed lowering does not repay within four replays on those two Law-bearing rows.

## Frozen matrix and accounting

- sizes: 64 KiB, 256 KiB, 1 MiB
- families: structured, compressed-like, long-runs, random, near-repeats
- 21 measured repetitions per arm after warm execution
- arms: literal fused control; existing prepared generic terminal replay; prepared + native mixed replay
- native mixed lowering is timed separately and is **not free**
- root allocation, native invocation, SHA-256 root authentication, and output `bytes` freezing remain inside hot replay
- same wire bytes and same modeled traffic; long-runs 1 MiB must retain <=0.55x literal wire and structured <=0.90x
- no selective-range, RSS, portability, or canonical-native-backend claim follows from this experiment

## Promotion boundary

ADVANCE only means a reusable native execution lowering is causally worthwhile for this bounded terminal graph shape. It does not add a ONE opcode or reader-visible mechanism. If this experiment still loses to literal control, terminal-specific micro-optimization stops; the next reader effort must move upward to a general reconstruction-plan/native execution model.
