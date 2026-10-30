"""No-identity, no-import, inert wheel tests for the CMPCT packaging profile."""
import base64
import csv
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate_cmpct_wheel_profile import validate

STEM = 'cmpct-0.30.0'
LOADER = 'cmpct/native_codec.py'
NATIVE = 'cmpct/cmpct_core.cp311-win_amd64.pyd'


def fixture(path, extra=(), before=False):
    files = [(LOADER, b'original loader placeholder'), (NATIVE, b'inert native placeholder')]
    files = list(extra) + files if before else files + list(extra)
    files.extend([(STEM+'.dist-info/WHEEL', b'Wheel-Version: 1.0\nGenerator: J24P08\nRoot-Is-Purelib: false\nTag: py3-none-any\n'),
                  (STEM+'.dist-info/METADATA', b'Metadata-Version: 2.3\nName: cmpct\nVersion: 0.30.0\n')])
    rows=[]
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files:
            # ZipInfo normalizes backslashes on Windows; explicitly preserve the raw
            # filename in the ZIP central directory so the hostile case is real.
            if '\\' in name:
                entry=zipfile.ZipInfo(name)
                entry.filename=name
                entry.orig_filename=name
                entry.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(entry,data)
            else:
                z.writestr(name,data)
            sha=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            rows.append((name,'sha256='+sha,str(len(data))))
        r=STEM+'.dist-info/RECORD'
        rows.append((r,'',''))
        output=io.StringIO();csv.writer(output).writerows(rows)
        z.writestr(r,output.getvalue())
    return path


class StrictProfile(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.dir=Path(t.name);self.wheel=self.dir/(STEM+'-py3-none-any.whl')

    def check(self,extra=(),pass_expected=True,before=False):
        fixture(self.wheel,extra,before)
        if pass_expected:
            self.assertEqual(validate(self.wheel)['result'],'PASS')
        else:
            with self.assertRaises(ValueError):validate(self.wheel)

    def test_01_original(self):self.check()
    def test_02_disjoint_root_now_rejected(self):self.check([('other/data.bin',b'ok')],False)
    def test_03_ordinary_package_asset(self):self.check([('cmpct/assets/metadata.data',b'ok')])
    def test_04_reject_purelib(self):self.check([(STEM+'.data/purelib/'+NATIVE,b'inert')],False)
    def test_05_reject_platlib(self):self.check([(STEM+'.data/platlib/'+LOADER,b'inert')],False)
    def test_06_reject_data(self):self.check([(STEM+'.data/data/lib/python3.11/site-packages/'+LOADER,b'inert')],False)
    def test_07_reject_headers(self):self.check([(STEM+'.data/headers/unrelated.h',b'inert')],False)
    def test_08_reject_scripts(self):self.check([(STEM+'.data/scripts/helper',b'inert')],False)
    def test_09_reject_disjoint_data(self):self.check([(STEM+'.data/purelib/other/unused',b'inert')],False)
    def test_10_reject_data_case(self):self.check([(STEM+'.DATA/purelib/other/unused',b'inert')],False)
    def test_11_reject_data_before(self):self.check([(STEM+'.data/purelib/'+NATIVE,b'inert')],False,True)
    def test_12_reject_casefold(self):self.check([('cmpct/NATIVE_CODEC.PY',b'inert')],False)
    def test_13_reject_unicode_nfd(self):self.check([('cmpct/caf\u00e9.py',b'a'),('cmpct/cafe\u0301.py',b'b')],False)
    def test_14_reject_parent(self):self.check([('cmpct/../'+LOADER,b'inert')],False)
    def test_15_reject_dot(self):self.check([('cmpct/./x',b'inert')],False)
    def test_16_reject_empty_segment(self):self.check([('cmpct//x',b'inert')],False)
    def test_17_reject_backslash(self):self.check([('cmpct\\x',b'inert')],False)
    def test_18_reject_trailing_dot(self):self.check([('cmpct/x.',b'inert')],False)
    def test_19_reject_win_device(self):self.check([('cmpct/COM1.ext',b'inert')],False)
    def test_20_reject_win_device_unicode(self):self.check([('cmpct/COM\u00b9.ext',b'inert')],False)
    def test_21_reject_file_ancestor(self):self.check([('cmpct/file',b'inert'),('cmpct/file/child',b'inert')],False)
    def test_22_reject_duplicate_wheel(self):self.check([(STEM+'.dist-info/WHEEL',b'Wheel-Version: 1.0\n')],False)
    def test_23_accept_unicode_nonalias(self):self.check([('cmpct/caf\u00e9.py',b'a'),('cmpct/cafe.py',b'b')])
    def test_26_win32_dos_device_space_before_extension(self):self.check([('cmpct/CON .txt',b'inert')],False)
    def test_27_win32_com_port_space_before_extension(self):self.check([('cmpct/COM1 .txt',b'inert')],False)
    def test_28_win32_auxiliary_device_multiple_spaces(self):self.check([('cmpct/AUX  .txt',b'inert')],False)
    def test_29_reject_root_pth_startup_execution(self):
        # Real pip host falsifier J24P09b observed this executed pre-import
        # while the earlier post-install cmpct/-only attestor returned PASS.
        self.check([('cmpct_inert_hook.pth',b'import builtins; builtins.TEST=1\n')],False)

    def test_30_reject_root_sitecustomize(self):
        self.check([('sitecustomize.py',b'INERT=1\n')],False)

    def test_31_reject_root_zip_pth_casefold(self):
        self.check([('CMPCT_INERT.PTH',b'import builtins; builtins.TEST=1\n')],False)

    def test_32_reject_other_distribution_metadata(self):
        self.check([('other-1.0.dist-info/METADATA',b'anything')],False)

    def test_33_accept_package_nonalias_assets(self):
        self.check([('cmpct/assets/plain.bin',b'asset'),('cmpct/assets/caf\u00e9.txt',b'caf')])

    def test_24_cli_rejects(self):
        fixture(self.wheel,[(STEM+'.data/data/other/unused',b'no')]);r=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/validate_cmpct_wheel_profile.py'),str(self.wheel)],capture_output=True,text=True)
        self.assertEqual(r.returncode,1)
        self.assertIn('relocation',r.stdout)

    def test_25_real_venv_data_scheme_writes_loader(self):
        # Stronger than a synthetic mapping: normal pip installs inert bytes
        # over a genuine package target through the .data/data scheme.
        venv=self.dir/'venv'
        run=subprocess.run([sys.executable,'-m','venv',str(venv)],capture_output=True,text=True,timeout=80)
        self.assertEqual(run.returncode,0,run.stderr)
        python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        vals=subprocess.check_output([str(python),'-c','import sysconfig;print(sysconfig.get_path("data"));print(sysconfig.get_path("purelib"))'],text=True,timeout=30).splitlines()
        data,purelib=map(Path,vals)
        rel=purelib.relative_to(data).as_posix()
        fixture(self.wheel,[(STEM+'.data/data/'+rel+'/'+LOADER,b'inert data-scheme replacement')])
        with self.assertRaises(ValueError): validate(self.wheel)
        pip=subprocess.run([str(python),'-m','pip','install','--no-index','--no-deps','--disable-pip-version-check',str(self.wheel)],capture_output=True,text=True,timeout=120)
        self.assertEqual(pip.returncode,0,pip.stderr)
        self.assertEqual((purelib/LOADER).read_bytes(),b'inert data-scheme replacement')


if __name__=='__main__':unittest.main()
