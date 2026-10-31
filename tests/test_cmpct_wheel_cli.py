"""Inert source-bound final-wheel console script admission controls (J24P14)."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate_cmpct_wheel_cli import inspect

STEM = 'cmpct-0.30.0'
EP = STEM + '.dist-info/entry_points.txt'
GENUINE = b'[console_scripts]\ncmpct = cmpct.cli:main\n'


def make_wheel(path: Path, entry: bytes | None = GENUINE, extra=(), version='0.30.0'):
    files = [('cmpct/__init__.py', b''), ('cmpct/cli.py', b'def main(): return 0\n'),
             (STEM+'.dist-info/WHEEL', b'Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: py3-none-any\n'),
             (STEM+'.dist-info/METADATA', b'Metadata-Version: 2.3\nName: cmpct\nVersion: 0.30.0\n')]
    if entry is not None:
        files += [(EP, entry)]
    files += list(extra)
    rows = []
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as wheel:
        for name, blob in files:
            wheel.writestr(name, blob)
            h = base64.urlsafe_b64encode(hashlib.sha256(blob).digest()).rstrip(b'=').decode()
            rows.append((name, 'sha256='+h, str(len(blob))))
        r = STEM + '.dist-info/RECORD'
        rows.append((r, '', ''))
        out = io.StringIO(); csv.writer(out).writerows(rows)
        wheel.writestr(r, out.getvalue())
    return path


class FinalWheelCliContract(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.wheel = self.root / (STEM + '-py3-none-any.whl')
        self.manifest = self.root / 'pyproject.toml'
        self.write_manifest()

    def write_manifest(self, target='cmpct.cli:main', script='cmpct', version='0.30.0', more=''):
        self.manifest.write_text(f'[project]\nname = "cmpct"\nversion = "{version}"\n'
                                 f'[project.scripts]\n{script} = "{target}"\n{more}', encoding='utf-8')

    def assert_accept(self, entry=GENUINE, extra=()):
        make_wheel(self.wheel, entry, extra)
        receipt = inspect(self.wheel, self.manifest)
        self.assertEqual(receipt['result'], 'PASS')
        self.assertEqual(receipt['wheel_sha256'], hashlib.sha256(self.wheel.read_bytes()).hexdigest())
        self.assertEqual(receipt['console_script'], {'name': 'cmpct', 'target': 'cmpct.cli:main'})

    def assert_reject(self, entry=GENUINE, extra=(), pattern=None):
        make_wheel(self.wheel, entry, extra)
        with self.assertRaises(ValueError) as exception:
            inspect(self.wheel, self.manifest)
        if pattern:
            self.assertIn(pattern, str(exception.exception))

    def test_01_original(self): self.assert_accept()
    def test_02_benign_comments_do_not_change_semantics(self): self.assert_accept(b'# note\n[console_scripts]\ncmpct=cmpct.cli:main\n')
    def test_03_changed_target_with_fully_consistent_record_rejected(self):
        self.assert_reject(b'[console_scripts]\ncmpct = sys:exit\n', pattern='differs')
    def test_04_changed_target_to_other_cmpct_module_rejected(self):
        self.assert_reject(b'[console_scripts]\ncmpct = cmpct.other:main\n')
    def test_05_missing_metadata_rejected(self): self.assert_reject(None, pattern='exactly one')
    def test_06_multiple_metadata_entries_rejected(self):
        self.assert_reject(GENUINE, [(STEM+'.dist-info/entry_points.txt', GENUINE)], 'exactly one')
    def test_07_second_distinfo_metadata_rejected(self):
        self.assert_reject(GENUINE, [('other-1.0.dist-info/entry_points.txt', GENUINE)], 'exactly one')
    def test_08_unexpected_console_command_rejected(self):
        self.assert_reject(GENUINE+b'other = cmpct.cli:main\n', pattern='differs')
    def test_09_gui_script_rejected(self): self.assert_reject(GENUINE+b'[gui_scripts]\nother = cmpct.cli:main\n', pattern='section')
    def test_10_unknown_metadata_section_rejected(self):
        self.assert_reject(GENUINE+b'[x]\nother = cmpct.cli:main\n', pattern='section')
    def test_11_uppercase_script_rejected(self):
        self.assert_reject(b'[console_scripts]\nCMPCT = cmpct.cli:main\n', pattern='differs')
    def test_12_missing_console_script_rejected(self):
        self.assert_reject(b'[console_scripts]\n', pattern='differs')
    def test_13_duplicate_section_rejected(self):
        self.assert_reject(GENUINE+b'[console_scripts]\nother = cmpct.cli:main\n', pattern='invalid')
    def test_14_duplicate_script_rejected(self):
        self.assert_reject(GENUINE+b'cmpct = cmpct.cli:main\n', pattern='invalid')
    def test_15_default_section_rejected(self):
        self.assert_reject(b'[DEFAULT]\nfoo = bar\n'+GENUINE, pattern='section')
    def test_16_bad_utf8_rejected(self):
        self.assert_reject(b'[console_scripts]\ncmpct = \xff\n', pattern='UTF-8')
    def test_17_oversized_entrypoint_rejected(self):
        self.assert_reject(GENUINE + b'#' * 70000, pattern='bound')
    def test_18_malformed_metadata_rejected(self):
        self.assert_reject(b'garbage without section\n', pattern='invalid')
    def test_19_wrong_wheel_version_rejected(self):
        self.write_manifest(version='0.31.0')
        self.assert_reject(pattern='filename')
    def test_20_wrong_project_name_rejected(self):
        self.manifest.write_text('[project]\nname="other"\nversion="0.30.0"\n[project.scripts]\ncmpct="cmpct.cli:main"\n')
        self.assert_reject(pattern='project name')
    def test_21_extra_source_script_rejected(self):
        self.write_manifest(more='other = "cmpct.cli:main"\n')
        self.assert_reject(pattern='exactly')
    def test_22_external_source_target_rejected(self):
        self.write_manifest(target='sys:exit')
        self.assert_reject(pattern='local qualified')
    def test_23_invalid_source_target_rejected(self):
        self.write_manifest(target='cmpct.cli:main [extra]')
        self.assert_reject(pattern='local qualified')
    def test_24_matching_source_and_wheel_evolution_permitted(self):
        self.write_manifest(target='cmpct.cli:future')
        make_wheel(self.wheel, b'[console_scripts]\ncmpct = cmpct.cli:future\n')
        self.assertEqual(inspect(self.wheel, self.manifest)['console_script']['target'], 'cmpct.cli:future')
    def test_25_matching_wrong_external_source_and_wheel_still_rejected(self):
        self.write_manifest(target='sys:exit')
        self.assert_reject(b'[console_scripts]\ncmpct = sys:exit\n', pattern='local qualified')
    def test_26_not_a_zip_rejected(self):
        self.wheel.write_bytes(b'not a wheel')
        with self.assertRaises(zipfile.BadZipFile): inspect(self.wheel, self.manifest)
    def test_27_other_wheel_filename_rejected(self):
        make_wheel(self.wheel)
        other=self.root/'other-0.30.0-py3-none-any.whl';other.write_bytes(self.wheel.read_bytes())
        with self.assertRaisesRegex(ValueError,'filename'):inspect(other,self.manifest)
    def test_28_source_gui_scripts_rejected(self):
        self.manifest.write_text(self.manifest.read_text()+'[project.gui-scripts]\nfoo="cmpct.cli:main"\n')
        self.assert_reject(pattern='GUI')
    def test_29_partial_unicode_case_script_rejected(self):
        self.assert_reject('[console_scripts]\ncmрct = cmpct.cli:main\n'.encode('utf-8'), pattern='differs') # Cyrillic p
    def test_30_whitespace_only_value_rejected(self):
        self.assert_reject(b'[console_scripts]\ncmpct =    \n', pattern='differs')

    def test_31_source_checkout_line_endings_preserve_semantic_identity(self):
        # On real hosted Windows builds pyproject may be CRLF while Linux/macOS
        # checkouts are LF. Raw source SHA differs; entrypoint meaning does not.
        make_wheel(self.wheel)
        source_bytes = self.manifest.read_bytes()
        baseline = inspect(self.wheel, self.manifest)
        self.manifest.write_bytes(source_bytes.replace(b'\\n', b'\\r\\n'))
        translated = inspect(self.wheel, self.manifest)
        self.assertNotEqual(baseline['source_manifest_sha256'], translated['source_manifest_sha256'])
        self.assertEqual(baseline['source_semantic_sha256'], translated['source_semantic_sha256'])
        self.assertEqual(baseline['wheel_sha256'], translated['wheel_sha256'])


if __name__ == '__main__': unittest.main()
