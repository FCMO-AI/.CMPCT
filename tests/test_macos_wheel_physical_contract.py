"""Deterministic offline red/green controls for the CMPCT wheel ABI admission guard."""
import base64
import csv
import hashlib
import importlib.util
import io
import pathlib
import struct
import tempfile
import unittest
import zipfile

MODULE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "validate_macos_wheel_abi.py"
spec = importlib.util.spec_from_file_location("cmpct_mac_wheel_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

X86, ARM = 0x01000007, 0x0100000C


def thin(cpu, minos=(11, 0), use_build=False, platform=1, subtype=None):
    if subtype is None:
        subtype = 3 if cpu == X86 else 0
    packed = (minos[0] << 16) | (minos[1] << 8)
    cmd = (struct.pack("<IIIIII", 0x32, 24, platform, packed, packed, 0) if use_build
           else struct.pack("<IIII", 0x24, 16, packed, packed))
    return b"\xcf\xfa\xed\xfe" + struct.pack("<IIIIIII", cpu, subtype, 6, 1, len(cmd), 0, 0) + cmd


def fat(parts):
    n = len(parts)
    offset = 8 + 20 * n
    table, payload = bytearray(), bytearray()
    for cpu, b in parts:
        alignment = 2
        padding = (-offset) % (1 << alignment)
        payload.extend(b"\x00" * padding)
        offset += padding
        subtype = 3 if cpu == X86 else 0
        table.extend(struct.pack(">IIIII", cpu, subtype, offset, len(b), alignment))
        payload.extend(b)
        offset += len(b)
    return b"\xca\xfe\xba\xbe" + struct.pack(">I", n) + bytes(table) + bytes(payload)


def good_fat():
    return fat([(X86, thin(X86, (10, 12))), (ARM, thin(ARM, (11, 0), use_build=True))])


def wheel(path, native, platform="macosx_10_12_universal2", metadata_platform=None, broken_record=False, metadata_python_tags=None):
    base = "cmpct-0.30.0.dist-info"
    lib = "cmpct/cmpct_core.cpython-311-darwin.so"
    tag = metadata_platform or platform
    tag_lines = "".join(f"Tag: {py}-cp311-{tag}\n" for py in (metadata_python_tags or ["cp311"]))
    entries = {
        lib: native,
        f"{base}/WHEEL": (f"Wheel-Version: 1.0\nRoot-Is-Purelib: false\n" + tag_lines).encode(),
        f"{base}/METADATA": b"Metadata-Version: 2.1\nName: cmpct\nVersion: 0.30.0\n",
    }
    records = []
    for name, data in entries.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        records.append([name, "sha256=" + digest, str(len(data))])
    if broken_record:
        records[0][1] = "sha256=" + "A" * 43
    records.append([f"{base}/RECORD", "", ""])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(records)
    entries[f"{base}/RECORD"] = buf.getvalue().encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return path


class TestPhysicalWheelGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

    def path(self, label="macosx_10_12_universal2"):
        return self.root / f"cmpct-0.30.0-cp311-cp311-{label}.whl"

    def test_prospective_authentic_dual_arch_control(self):
        data = gate.inspect(wheel(self.path(), good_fat()))
        self.assertTrue(data["pass"])
        self.assertEqual(set(data["physical"]), {"arm64", "x86_64"})
        self.assertEqual(data["physical"]["x86_64"]["min_os"], (10, 12, 0))

    def test_false_universal2_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing physical architecture"):
            gate.inspect(wheel(self.path(), thin(ARM, use_build=True)))

    def test_forged_deployment_min_after_valid_record_is_rejected(self):
        bad = fat([(X86, thin(X86, (11, 0))), (ARM, thin(ARM, use_build=True))])
        # This passes a simple lipo-like architecture presence control.
        self.assertEqual(set(gate.physical_slices(bad)), {"arm64", "x86_64"})
        with self.assertRaisesRegex(ValueError, "x86_64 minimum macOS"):
            gate.inspect(wheel(self.path(), bad))

    def test_later_arm_target_is_rejected(self):
        bad = fat([(X86, thin(X86, (10, 12))), (ARM, thin(ARM, (12, 0), use_build=True))])
        with self.assertRaisesRegex(ValueError, "arm64 minimum macOS"):
            gate.inspect(wheel(self.path(), bad))

    def test_record_hash_enforced(self):
        with self.assertRaisesRegex(ValueError, "RECORD"):
            gate.inspect(wheel(self.path(), good_fat(), broken_record=True))

    def test_internal_wheel_tag_enforced(self):
        with self.assertRaisesRegex(ValueError, "WHEEL platform"):
            gate.inspect(wheel(self.path(), good_fat(), metadata_platform="macosx_11_0_arm64"))

    def test_thin_x86_and_arm(self):
        for platform, binary in [
            ("macosx_10_12_x86_64", thin(X86, (10, 12))),
            ("macosx_11_0_arm64", thin(ARM, (11, 0), use_build=True)),
        ]:
            with self.subTest(platform=platform):
                self.assertTrue(gate.inspect(wheel(self.path(platform), binary, platform=platform))["pass"])

    def test_subset_wheel_tags_rejected_even_with_forged_valid_record(self):
        # A wheel filename claims cp310 and cp311. RECORD may be valid while WHEEL
        # intentionally omits cp310; minimum-OS and lipo-like checks still pass.
        p = self.root / "cmpct-0.30.0-cp310.cp311-cp311-macosx_10_12_universal2.whl"
        self.assertTrue(gate.inspect(wheel(p, good_fat(), metadata_python_tags=["cp310", "cp311"]))["pass"])
        with self.assertRaisesRegex(ValueError, "WHEEL tag coverage"):
            gate.inspect(wheel(p, good_fat(), metadata_python_tags=["cp311"]))

    def test_non_macos_build_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "not for macOS"):
            gate.inspect(wheel(self.path("macosx_11_0_arm64"), thin(ARM, use_build=True, platform=2), platform="macosx_11_0_arm64"))

    def test_restricted_cpu_subtypes_rejected(self):
        for cpu, bad_subtype in [(ARM, 2), (X86, 8)]:
            with self.subTest(cpu=cpu):
                with self.assertRaisesRegex(ValueError, "restricted"):
                    gate.parse_thin(thin(cpu, subtype=bad_subtype))

    def test_fat_header_mismatch_rejected(self):
        b = bytearray(good_fat())
        struct.pack_into(">I", b, 8, ARM)  # Fat header now lies about embedded x86 slice.
        with self.assertRaisesRegex(ValueError, "disagree"):
            gate.physical_slices(bytes(b))

    def test_overlapping_fat_slices_rejected(self):
        b = bytearray(good_fat())
        first_off = struct.unpack_from(">I", b, 16)[0]
        struct.pack_into(">I", b, 36, first_off)  # Second slice offset alias.
        with self.assertRaises(ValueError):
            gate.physical_slices(bytes(b))

    def test_truncated_load_command_rejected(self):
        b = bytearray(thin(ARM, use_build=True))
        struct.pack_into("<I", b, 36, 0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError, "size"):
            gate.parse_thin(bytes(b))

    def test_multiple_min_commands_rejected(self):
        b = bytearray(thin(ARM, use_build=True))
        b.extend(struct.pack("<IIII", 0x24, 16, (11 << 16), (11 << 16)))
        struct.pack_into("<I", b, 16, 2)  # ncmds
        struct.pack_into("<I", b, 20, 40)  # sizeofcmds
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            gate.parse_thin(bytes(b))

    def test_non_regular_64bit_magic_is_refused(self):
        with self.assertRaisesRegex(ValueError, "not Mach-O"):
            gate.physical_slices(b"\x00" * 128)

    def test_fat64_has_valid_portable_path(self):
        b1, b2 = thin(X86, (10, 12)), thin(ARM, use_build=True)
        n, first_offset = 2, 8 + 32 * 2
        rec1 = struct.pack(">IIQQII", X86, 3, first_offset, len(b1), 2, 0)
        rec2 = struct.pack(">IIQQII", ARM, 0, first_offset + len(b1), len(b2), 2, 0)
        b = b"\xca\xfe\xba\xbf" + struct.pack(">I", n) + rec1 + rec2 + b1 + b2
        self.assertEqual(set(gate.physical_slices(b)), {"x86_64", "arm64"})


if __name__ == "__main__":
    unittest.main()
