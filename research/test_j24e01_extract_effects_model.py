"""Independent deterministic, valid/hostile effect-model court (not a product test)."""
import copy
import random
import time
import unittest

from research.j24e01_extract_effects_model import (
    UnprovedEffect, planned_logical_bytes,
    K_FILE, K_DIR, K_SYMLINK, K_HARDLINK,
    S_BLOB, S_CHUNKS, S_VZIP, S_SPARSE, S_PACK, S_CDC,
)


def empty():
    return {"files": [], "blobs": [], "recipes": []}


def blob(index, n):
    index["blobs"].append([0, n, n, 0, 0])
    return len(index["blobs"]) - 1


def row(index, name, kind, size, storage):
    index["files"].append([name, kind, 0o644, 0, size, None, storage])


def generated(seed):
    """Generator does not import the effect oracle or call its helpers."""
    rng = random.Random(seed)
    obj = empty()
    oracle_bytes = 0
    regular = []
    n = rng.randint(1, 16)
    for i in range(n):
        name = f"member{i:03d}"
        choices = ["direct", "pack", "chunks", "cdc", "sparse", "vzip", "link", "dir"]
        if regular:
            choices.append("alias")
        mode = rng.choice(choices)
        size = rng.randint(0, 512)
        if mode == "dir":
            row(obj, name, K_DIR, 0, None)
            continue
        if mode == "alias":
            owner_name, owner_size = rng.choice(regular)
            row(obj, name, K_HARDLINK, owner_size, [owner_name])
            oracle_bytes += owner_size
            # Allow a later alias to target an earlier alias deliberately.
            regular.append((name, owner_size))
            continue
        if mode in ("direct", "link"):
            row(obj, name, K_SYMLINK if mode == "link" else K_FILE,
                size, [S_BLOB, blob(obj, size)])
        elif mode == "pack":
            offset = rng.randint(0, 128)
            capacity = offset + size + rng.randint(0, 128)
            row(obj, name, K_FILE, size, [S_PACK, blob(obj, capacity), offset, size])
        elif mode in ("chunks", "cdc"):
            rem, parts = size, []
            while rem:
                k = rng.randint(1, min(rem, 96))
                p = blob(obj, k)
                parts.append(p if mode == "chunks" else [k, p])
                rem -= k
            row(obj, name, K_FILE, size,
                [S_CHUNKS if mode == "chunks" else S_CDC, parts])
        elif mode == "sparse":
            extents = []
            if size:
                start = rng.randint(0, size - 1)
                span = rng.randint(1, size - start)
                extents.append([start, span, [blob(obj, span)]])
            row(obj, name, K_FILE, size, [S_SPARSE, extents])
        elif mode == "vzip":
            obj["recipes"].append([0, 0, 0, None, size])
            row(obj, name, K_FILE, size,
                [S_VZIP, len(obj["recipes"]) - 1])
        oracle_bytes += size
        if mode not in ("link", "dir"):
            regular.append((name, size))
    return obj, oracle_bytes


class ModelCourt(unittest.TestCase):
    def test_seven_valid_storage_families(self):
        obj = empty()
        row(obj, "direct", K_FILE, 33, [S_BLOB, blob(obj, 33)])
        row(obj, "symlink", K_SYMLINK, 8, [S_BLOB, blob(obj, 8)])
        row(obj, "pack", K_FILE, 9, [S_PACK, blob(obj, 40), 7, 9])
        row(obj, "chunks", K_FILE, 6, [S_CHUNKS, [blob(obj, 2), blob(obj, 4)]])
        row(obj, "cdc", K_FILE, 12, [S_CDC, [[5, blob(obj, 5)], [7, blob(obj, 7)]]])
        row(obj, "sparse", K_FILE, 2048, [S_SPARSE, [[512, 7, [blob(obj, 7)]]]])
        obj["recipes"].append([0, 0, 0, None, 61])
        row(obj, "vzip", K_FILE, 61, [S_VZIP, 0])
        row(obj, "dir", K_DIR, 0, None)
        row(obj, "hardlink", K_HARDLINK, 33, ["direct"])
        # The valid VZIP description cannot certify actual generated ZIP bytes:
        # independently signed recipe-total agreement was falsified in #623.
        with self.assertRaisesRegex(UnprovedEffect, "virtual stream length unproven"):
            planned_logical_bytes(obj)
        obj["files"] = [x for x in obj["files"] if x[0] != "vzip"]
        self.assertEqual(planned_logical_bytes(obj), 33 + 8 + 9 + 6 + 12 + 2048 + 33)

    def test_four_published_signed_index_failure_classes(self):
        # No archive-index signatures are forged; these are just the structures
        # of published cases #688/#693/#697/#700 against a pure proof model.
        cases = []
        obj = empty()
        row(obj, "regular", K_FILE, 8192, [S_BLOB, blob(obj, 8192)])
        row(obj, "negative-sym", K_SYMLINK, -8192, [S_BLOB, blob(obj, 11)])
        cases.append(("J24B06-negative-symlink", obj, 0, 8203))
        obj = empty()
        row(obj, "regular", K_FILE, 8192, [S_BLOB, blob(obj, 8192)])
        row(obj, "alias", K_HARDLINK, 0, ["regular"])
        cases.append(("J24B07-hardlink", obj, 8192, 16384))
        obj = empty()
        row(obj, "regular", K_FILE, 8192, [S_BLOB, blob(obj, 8192)])
        row(obj, "symlink", K_SYMLINK, 0, [S_BLOB, blob(obj, 11)])
        cases.append(("J24B09-symlink", obj, 8192, 8203))
        obj = empty()
        row(obj, "sparse", K_FILE, 16384,
            [S_SPARSE, [[16383, 1, [blob(obj, 8192)]]]])
        cases.append(("J24B10-sparse", obj, 16384, 24575))
        for case_name, index, weak_budget, actual_effect in cases:
            with self.subTest(case=case_name):
                declared = sum(x[4] for x in index["files"] if x[1] != K_DIR)
                self.assertEqual(declared, weak_budget)
                self.assertGreater(actual_effect, weak_budget)
                with self.assertRaises(UnprovedEffect):
                    planned_logical_bytes(index)

    def test_held_out_2000_valid_graphs_with_mutants(self):
        certified = uncertified_vzip = 0
        for seed in range(20261028, 20263028):
            obj, want = generated(seed)
            with self.subTest(seed=seed):
                if any(x[1] == K_FILE and x[6][0] == S_VZIP for x in obj["files"]):
                    # No silent exclusion: these seeds are prospectively valid
                    # but H1 fails to prove exact projection without physical work.
                    uncertified_vzip += 1
                    with self.assertRaisesRegex(UnprovedEffect, "virtual stream length unproven"):
                        planned_logical_bytes(obj)
                else:
                    certified += 1
                    self.assertEqual(planned_logical_bytes(obj), want)
                mod = copy.deepcopy(obj)
                target = next((x for x in mod["files"] if x[1] != K_DIR), None)
                if target:
                    # A longer sparse logical file may simply have a valid trailing hole.
                    # A negative size is hostile for every member kind, without exception.
                    target[4] = -1
                    with self.assertRaisesRegex(UnprovedEffect, "declared size"):
                        planned_logical_bytes(mod)
                direct = next((x for x in obj["files"]
                    if x[1] in (K_FILE, K_SYMLINK) and x[6][0] == S_BLOB), None)
                if direct:
                    # Isolate this specific physical disagreement: an earlier
                    # uncertified VZIP must not accidentally pass the falsifier.
                    isolated = {
                        "files": [copy.deepcopy(direct)],
                        "blobs": copy.deepcopy(obj["blobs"]),
                        "recipes": [],
                    }
                    isolated["files"][0][4] += 1
                    with self.assertRaisesRegex(UnprovedEffect,
                        "direct size/owner disagreement|symlink size/owner disagreement"):
                        planned_logical_bytes(isolated)
        self.assertEqual(certified + uncertified_vzip, 2000)
        self.assertGreater(certified, 0)
        self.assertGreater(uncertified_vzip, 0)
        print(f"J24E01_HELDOUT total=2000 proven={certified} vzip_unproved={uncertified_vzip}", flush=True)

    def test_alias_of_alias_and_nonregular_owner(self):
        obj = empty()
        row(obj, "late", K_HARDLINK, 8, ["middle"])
        row(obj, "early", K_HARDLINK, 8, ["middle"])
        row(obj, "middle", K_HARDLINK, 8, ["owner"])
        row(obj, "owner", K_FILE, 8, [S_BLOB, blob(obj, 8)])
        self.assertEqual(planned_logical_bytes(obj), 32)
        bad = copy.deepcopy(obj)
        bad["files"][-1][1] = K_DIR
        bad["files"][-1][4] = 0
        bad["files"][-1][6] = None
        with self.assertRaises(UnprovedEffect):
            planned_logical_bytes(bad)

    def test_long_forward_hardlink_chain_without_recursion(self):
        obj = empty()
        n = 50000
        for i in range(n):
            row(obj, f"link{i}", K_HARDLINK, 8, [f"link{i+1}" if i+1 < n else "owner"])
        row(obj, "owner", K_FILE, 8, [S_BLOB, blob(obj, 8)])
        started_wall, started_cpu = time.perf_counter(), time.process_time()
        self.assertEqual(planned_logical_bytes(obj), (n+1)*8)
        elapsed_wall = time.perf_counter() - started_wall
        elapsed_cpu = time.process_time() - started_cpu
        print(f"J24E01_CHAIN aliases={n} bytes={(n+1)*8} wall_s={elapsed_wall:.6f} cpu_s={elapsed_cpu:.6f}", flush=True)
        self.assertLess(elapsed_wall, 12.0, "unexpected superlinear alias walk")

    def test_cycle_bad_types_and_unknown_owners(self):
        cases = []
        obj = empty()
        row(obj, "self", K_HARDLINK, 1, ["self"])
        cases.append(obj)
        obj = empty()
        row(obj, "bad", K_FILE, True, [S_BLOB, blob(obj, 1)])
        cases.append(obj)
        obj = empty()
        row(obj, "bad", K_FILE, 1, [S_BLOB, 200])
        cases.append(obj)
        obj = empty()
        row(obj, "bad", K_FILE, 1, [77, 0])
        cases.append(obj)
        obj = empty()
        row(obj, "dir", K_DIR, 0, None)
        row(obj, "alias", K_HARDLINK, 0, ["dir"])
        cases.append(obj)
        for obj in cases:
            with self.subTest(case=obj):
                with self.assertRaises(UnprovedEffect):
                    planned_logical_bytes(obj)


if __name__ == "__main__":
    unittest.main()
