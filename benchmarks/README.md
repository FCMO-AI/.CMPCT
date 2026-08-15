# Universal benchmark

`universal_bench.py` generates heterogeneous local corpora and compares CMPCT with ordinary ZIP.
The generated corpora and outputs are ignored by git.

Run from an editable installation:

```bash
python -m pip install -e .[audio,test]
python benchmarks/universal_bench.py
```

Do not turn a threshold discovered here into a format rule until it survives multiple corpus classes.
