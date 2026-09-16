from __future__ import annotations

"""Fresh-process phase-labelled live-RSS worker for frozen r25 product-lifetime attribution."""

import argparse
import hashlib
import json
import resource
import threading
import time
from functools import wraps
from pathlib import Path

SAMPLE_INTERVAL_S = 0.010


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _vmrss_kib() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("VmRSS unavailable from /proc/self/status")


class _Monitor:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.active: dict[str, int] = {}
        self.events: list[dict] = []
        self.combo_peaks: dict[str, dict] = {}
        self.sample_count = 0
        self.errors: list[str] = []
        self.stop_event = threading.Event()
        self.started = time.perf_counter()
        self.baseline_vmrss_kib = _vmrss_kib()
        self.global_peak = {"vmrss_kib": self.baseline_vmrss_kib, "active": [], "at_s": 0.0}
        self.thread = threading.Thread(target=self._sample_loop, name="cmpct-rss-phase-sampler", daemon=True)

    def _active_names(self) -> list[str]:
        return sorted(name for name, count in self.active.items() if count > 0)

    def _observe(self, vmrss: int) -> None:
        active = self._active_names()
        now = time.perf_counter() - self.started
        combo = "+".join(active) if active else "<none>"
        row = self.combo_peaks.get(combo)
        if row is None or vmrss > int(row["vmrss_kib"]):
            self.combo_peaks[combo] = {"vmrss_kib": vmrss, "active": active, "at_s": now}
        if vmrss > int(self.global_peak["vmrss_kib"]):
            self.global_peak = {"vmrss_kib": vmrss, "active": active, "at_s": now}

    def _sample_loop(self) -> None:
        try:
            while not self.stop_event.wait(SAMPLE_INTERVAL_S):
                vmrss = _vmrss_kib()
                with self.lock:
                    self.sample_count += 1
                    self._observe(vmrss)
        except Exception as exc:
            with self.lock:
                self.errors.append(repr(exc))

    def start(self) -> None:
        self.thread.start()

    def enter(self, phase: str) -> None:
        vmrss = _vmrss_kib()
        with self.lock:
            self.active[phase] = self.active.get(phase, 0) + 1
            active = self._active_names()
            self.events.append({"phase": phase, "event": "enter", "vmrss_kib": vmrss, "active": active,
                                "at_s": time.perf_counter() - self.started})
            self._observe(vmrss)

    def exit(self, phase: str) -> None:
        vmrss = _vmrss_kib()
        with self.lock:
            count = self.active.get(phase, 0)
            if count < 1:
                self.errors.append(f"unbalanced phase exit: {phase}")
            else:
                self.active[phase] = count - 1
            active = self._active_names()
            self.events.append({"phase": phase, "event": "exit", "vmrss_kib": vmrss, "active": active,
                                "at_s": time.perf_counter() - self.started})
            self._observe(vmrss)

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=2.0)
        if self.thread.is_alive():
            self.errors.append("sampler thread failed to stop")
        with self.lock:
            if any(self.active.values()):
                self.errors.append(f"active phases remain: {self.active!r}")


def _install_wrapper(obj, attr: str, phase: str, monitor: _Monitor, restorations: list) -> None:
    original = getattr(obj, attr)

    @wraps(original)
    def observed(*args, **kwargs):
        monitor.enter(phase)
        try:
            return original(*args, **kwargs)
        finally:
            monitor.exit(phase)

    setattr(obj, attr, observed)
    restorations.append((obj, attr, original))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")

    research_tree = str(canonical.RC.treehash(args.source))
    expected_product_tree = str(product.treehash(args.source))
    eligible, reason = canonical.RC._prefixgraph_eligibility(args.source, research_tree)
    if not eligible:
        raise RuntimeError(f"preregistered Shifted target unexpectedly PrefixGraph-ineligible: {reason}")

    monitor = _Monitor()
    restorations: list[tuple[object, str, object]] = []
    # Patch exact shipping resolution objects only. In particular, the r24 prebuild future resolves the helper in
    # release_product_base, while the canonical-final outer tournament resolves the public canonical functions.
    _install_wrapper(canonical, "_prepare_profile_tree", "profile-prepare", monitor, restorations)
    _install_wrapper(product._BASE_IMPL, "_locality_bounded_r24_build", "r24-prebuild", monitor, restorations)
    _install_wrapper(canonical, "_r24_build", "r24-consume", monitor, restorations)
    _install_wrapper(canonical, "_r25_build", "r25-tournament", monitor, restorations)
    _install_wrapper(canonical.RC.G04, "build", "g04-build", monitor, restorations)
    _install_wrapper(canonical.RC.PG, "build", "prefixgraph-build", monitor, restorations)
    _install_wrapper(canonical, "strong_verify", "strong-verify", monitor, restorations)

    baseline_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    monitor.start()
    monitor.enter("shipping-product")
    started = time.perf_counter()
    try:
        stats = dict(product.build(args.source, args.archive))
        wall = time.perf_counter() - started
    finally:
        monitor.exit("shipping-product")
        monitor.stop()
        for obj, attr, original in reversed(restorations):
            setattr(obj, attr, original)
    peak_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    verify = dict(product.strong_verify(args.archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != expected_product_tree:
        raise RuntimeError(f"shipping strong verification mismatch: expected={expected_product_tree} actual={verified_tree}")

    restored = all(getattr(obj, attr) is original for obj, attr, original in restorations)
    print(json.dumps({
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha(args.archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "r25_attempted": stats.get("r25_attempted"),
        "tree_sha256": verified_tree,
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": expected_product_tree,
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "research_identity_domain": "research-content-tree-v1",
        "wall_s": wall,
        "baseline_ru_maxrss_kib": baseline_ru,
        "peak_ru_maxrss_kib": peak_ru,
        "baseline_vmrss_kib": monitor.baseline_vmrss_kib,
        "sampled_global_peak": monitor.global_peak,
        "sample_count": monitor.sample_count,
        "sample_interval_ms": int(SAMPLE_INTERVAL_S * 1000),
        "sampler_errors": monitor.errors,
        "phase_events": monitor.events,
        "phase_combo_peaks": monitor.combo_peaks,
        "wrappers_restored": restored,
        "semantic_owners": {
            "pg": canonical.RC.PG.__name__,
            "g04": canonical.RC.G04.__name__,
            "reader": canonical.RC.READER.__name__,
            "identity_exact": True,
        },
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
