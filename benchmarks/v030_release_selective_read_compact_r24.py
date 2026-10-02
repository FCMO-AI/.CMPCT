from benchmarks import v030_release_selective_read_product as gate

gate.B.WORKER = gate.B.ROOT / "benchmarks" / "v030_perf_worker_compact_r24.py"

if __name__ == "__main__":
    gate.main()
