#!/usr/bin/env python3
"""Original Actions artifact custody negative controls for J24G31.

Usage: download all four original artifacts to a directory, then
python research/j24g31_transport_controls.py --artifacts DIR
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

p=argparse.ArgumentParser()
p.add_argument('--artifacts',type=Path,required=True)
args=p.parse_args()
source=args.artifacts
spec=importlib.util.spec_from_file_location(
    'j24g31_independent_zip_wire_audit',
    Path(__file__).with_name('j24g31_independent_zip_wire_audit.py'))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
files=[f'j30-{k}-original.zip' for k in ('physical','linux','mac','win')]
control=[]
for name in files:
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        for f in files:shutil.copyfile(source/f,root/f)
        path=root/name
        buf=bytearray(path.read_bytes())
        buf[-9]^=0x01
        path.write_bytes(buf)
        try:m.Audit().execute(root)
        except AssertionError as exc:
            assert 'original GitHub Actions artifact digest' in str(exc),str(exc)
            control.append(name)
        else:raise AssertionError('provider-bound transport mutation accepted '+name)
print(json.dumps({
    'schema':'j24g31-artifact-hash-negative-controls-v1',
    'transport_mutations':control,
    'rejected':len(control),
    'source_head':'8581f1dee427e9ca7359e3c05bd514499471c357'
},indent=2))
