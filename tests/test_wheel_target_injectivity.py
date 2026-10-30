"""Standalone inert-wheel tests. No CMPCT runtime/native import."""
import base64
import csv
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate_wheel_target_injectivity import validate

DIST = 'cmpct-0.30.0'
NATIVE = 'cmpct/cmpct_core.cp311-win_amd64.pyd'
PYMOD = 'cmpct/native_codec.py'


def make_wheel(path, extras=(), order='after'):
    # Synthetic self-consistent RECORD, not an assertion of publisher trust.
    base = [(NATIVE, b'authentic native placeholder'), (PYMOD, b'authentic Python placeholder')]
    items = list(base + list(extras)) if order == 'after' else list(extras) + base
    items.append((DIST + '.dist-info/WHEEL', b'Wheel-Version: 1.0\nGenerator: J24P07\nRoot-Is-Purelib: false\nTag: py3-none-any\n'))
    items.append((DIST + '.dist-info/METADATA', b'Metadata-Version: 2.3\nName: cmpct\nVersion: 0.30.0\n'))
    rows = []
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in items:
            out.writestr(name, data)
            sha = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode('ascii')
            rows.append((name, 'sha256=' + sha, str(len(data))))
        record_name = DIST + '.dist-info/RECORD'
        rows.append((record_name, '', ''))
        record = io.StringIO()
        csv.writer(record).writerows(rows)
        out.writestr(record_name, record.getvalue().encode('utf-8'))
    return path


class WheelDestInjectivity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.wheel = Path(self.tmp.name) / (DIST + '-py3-none-any.whl')

    def check(self, additions=(), expected=True, order='after'):
        make_wheel(self.wheel, additions, order)
        if expected:
            self.assertEqual(validate(self.wheel)['result'], 'PASS')
        else:
            with self.assertRaises(ValueError):
                validate(self.wheel)

    def test_01_original(self): self.check()
    def test_02_disjoint_root(self): self.check([('other/data.bin', b'disjoint')])
    def test_03_disjoint_data(self): self.check([(DIST + '.data/purelib/other/data.bin', b'disjoint')])
    def test_04_spread_purelib_after(self): self.check([(DIST + '.data/purelib/' + NATIVE, b'altered')], False)
    def test_05_spread_purelib_before(self): self.check([(DIST + '.data/purelib/' + NATIVE, b'altered')], False, 'before')
    def test_06_spread_platlib_python(self): self.check([(DIST + '.data/platlib/' + PYMOD, b'altered')], False)
    def test_07_cross_scheme(self): self.check([(DIST + '.data/purelib/other/x.py', b'a'), (DIST + '.data/platlib/other/x.py', b'b')], False)
    def test_08_casefold_root(self): self.check([(NATIVE.upper(), b'alias')], False)
    def test_09_unicode_nfd(self): self.check([('some/caf\u00e9.py', b'a'), ('some/cafe\u0301.py', b'b')], False)
    def test_10_traversal(self): self.check([('cmpct/../' + NATIVE, b'alias')], False)
    def test_11_dot(self): self.check([('cmpct/./x', b'alias')], False)
    def test_12_double_slash(self): self.check([('cmpct//x', b'alias')], False)
    def test_13_backslash(self): self.check([('cmpct\\x', b'alias')], False)
    def test_14_trailing_dot(self): self.check([('cmpct/x.', b'alias')], False)
    def test_15_device(self): self.check([('cmpct/NUL.txt', b'alias')], False)
    def test_16_unsupported_data_section(self): self.check([(DIST + '.data/unknown/x', b'alias')], False)
    def test_17_unrecognized_data_root(self): self.check([('other-1.0.data/purelib/cmpct/x', b'alias')], False)
    def test_18_file_shadows_directory(self): self.check([('some', b'file'), ('some/child', b'child')], False)
    def test_19_unicode_noncollision(self): self.check([('some/caf\u00e9.py', b'a'), ('some/cafe.py', b'b')])
    def test_20_repeated_terminal_slash(self): self.check([('cmpct/other///', b'')], False)

    def test_21_cli_reports_rejection(self):
        make_wheel(self.wheel, [(DIST + '.data/purelib/' + NATIVE, b'alias')])
        cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / 'tools' / 'validate_wheel_target_injectivity.py'), str(self.wheel)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn('installed target collision', p.stdout)

    def test_22_real_pip_overwrite_control(self):
        # Real pip executes the originally observed PEP427 spread on inert data.
        make_wheel(self.wheel, [(DIST + '.data/purelib/' + PYMOD, b'changed only after pip spread')])
        self.assertRaises(ValueError, validate, self.wheel)
        target = Path(self.tmp.name) / 'site'
        p = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps',
                            '--disable-pip-version-check', '--target', str(target), str(self.wheel)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual((target / PYMOD).read_bytes(), b'changed only after pip spread')
        self.assertEqual((target / NATIVE).read_bytes(), b'authentic native placeholder')


if __name__ == '__main__':
    unittest.main()
