"""J24P09: detached installed-package whole-byte equality controls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile
import os

SOURCE = Path(__file__).resolve().parents[1] / 'tools' / 'attest_installed_cmpct_wheel.py'
spec = importlib.util.spec_from_file_location('installed_cmpct_attest', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstalledWheelCustody(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.package = self.root / 'site-packages' / 'cmpct'
        self.package.mkdir(parents=True)
        self.wheel = self.root / 'cmpct-0.30.0-cp311-none-any.whl'
        self.files = {
            'cmpct/__init__.py': b'__version__ = "0.30.0"\n',
            'cmpct/native_codec.py': b'def native(): return 1\n',
            'cmpct/cmpct_core.so': b'MOCK_ELF_BYTES\x00',
            'cmpct/nested/__init__.py': b'\n',
        }
        self.make_wheel(self.files)
        self.install_synthetic(self.files)

    def tearDown(self):
        self.temp.cleanup()

    def make_wheel(self, members):
        with zipfile.ZipFile(self.wheel, 'w') as z:
            for name, contents in members.items():
                z.writestr(name, contents)
            z.writestr('cmpct-0.30.0.dist-info/WHEEL', 'Wheel-Version: 1.0\nTag: cp311-none-any\n')

    def install_synthetic(self, members):
        for name, contents in members.items():
            if name.startswith('cmpct/'):
                path = self.package.parent / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)

    def attest(self):
        return module.inspect(self.wheel, self.package, source_sha='f' * 40)

    def test_good_complete_byte_set(self):
        receipt = self.attest()
        self.assertEqual(receipt['result'], 'PASS')
        self.assertEqual(receipt['file_count'], len(self.files))
        self.assertEqual(receipt['source_sha'], 'f' * 40)

    def test_legitimate_alternate_wheel_and_matching_install(self):
        changed = dict(self.files)
        changed['cmpct/native_codec.py'] = b'def native(): return 2\n'
        self.make_wheel(changed)
        self.install_synthetic(changed)
        self.assertEqual(self.attest()['result'], 'PASS')

    def test_native_bytes_changed(self):
        (self.package / 'cmpct_core.so').write_bytes(b'OLD_BINARY')
        with self.assertRaisesRegex(ValueError, 'byte mismatch'):
            self.attest()

    def test_loader_bytes_changed(self):
        (self.package / 'native_codec.py').write_bytes(b'different code')
        with self.assertRaisesRegex(ValueError, 'byte mismatch'):
            self.attest()

    def test_stale_second_native(self):
        (self.package / 'cmpct_core_old.so').write_bytes(b'STALE')
        with self.assertRaisesRegex(ValueError, 'extra='):
            self.attest()

    def test_removed_package_member(self):
        (self.package / 'native_codec.py').unlink()
        with self.assertRaisesRegex(ValueError, 'missing='):
            self.attest()

    def test_wheel_modified_after_install(self):
        modified = dict(self.files)
        modified['cmpct/native_codec.py'] = b'wheel alone changed'
        self.make_wheel(modified)
        with self.assertRaisesRegex(ValueError, 'byte mismatch'):
            self.attest()

    def test_generated_bytecode_rejected_before_import(self):
        cache = self.package / '__pycache__'
        cache.mkdir()
        (cache / '__init__.cpython-311.pyc').write_bytes(b'GENERATED')
        with self.assertRaisesRegex(ValueError, 'untrusted installed Python bytecode'):
            self.attest()

    def test_cache_native_not_exempt(self):
        cache = self.package / '__pycache__'
        cache.mkdir()
        (cache / 'cmpct_core_old.so').write_bytes(b'OLD')
        with self.assertRaisesRegex(ValueError, 'untrusted installed Python bytecode'):
            self.attest()

    def test_directory_added_with_regular_file(self):
        extra = self.package / 'old' / 'module.py'
        extra.parent.mkdir()
        extra.write_bytes(b'old')
        with self.assertRaisesRegex(ValueError, 'extra='):
            self.attest()

    def test_noncanonical_member_is_rejected(self):
        changed = dict(self.files)
        changed['cmpct/../outside.py'] = b'bad'
        self.make_wheel(changed)
        with self.assertRaisesRegex(ValueError, 'noncanonical'):
            self.attest()

    def test_missing_all_package_members(self):
        self.make_wheel({'other/__init__.py': b''})
        with self.assertRaisesRegex(ValueError, 'missing or oversized CMPCT'):
            self.attest()

    def test_wheel_bytecode_payload_refused(self):
        changed = dict(self.files)
        changed['cmpct/__pycache__/__init__.cpython-311.pyc'] = b'cached code'
        self.make_wheel(changed)
        with self.assertRaisesRegex(ValueError, 'shipping wheel contains cached Python'):
            self.attest()

    def test_python_cache_different_executable_code_rejected(self):
        # Unexpected falsifier of initial J24P09: a source-identical .py
        # can execute a substituted timestamp-valid .pyc code object.
        import py_compile
        import marshal
        source_path = self.package / '__init__.py'
        py_compile.compile(str(source_path), doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
        cached = list((self.package / '__pycache__').glob('__init__*.pyc'))
        self.assertEqual(len(cached), 1)
        contents = cached[0].read_bytes()
        cached[0].write_bytes(contents[:16] + marshal.dumps(
            compile('UNTRUSTED = 99\n', str(source_path), 'exec')))
        with self.assertRaisesRegex(ValueError, 'untrusted installed Python bytecode'):
            self.attest()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlink unsupported')
    def test_installed_file_symlink_is_rejected(self):
        original = self.package / 'native_codec.py'
        original.unlink()
        try:
            original.symlink_to(self.package / '__init__.py')
        except OSError as e:
            self.skipTest('symlink privilege unavailable: ' + str(e))
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.attest()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlink unsupported')
    def test_installed_directory_symlink_is_rejected(self):
        nested = self.package / 'nested'
        shutil.rmtree(nested)
        try:
            nested.symlink_to(self.root, target_is_directory=True)
        except OSError as e:
            self.skipTest('symlink privilege unavailable: ' + str(e))
        with self.assertRaisesRegex(ValueError, 'directory symlink'):
            self.attest()


if __name__ == '__main__':
    unittest.main()
