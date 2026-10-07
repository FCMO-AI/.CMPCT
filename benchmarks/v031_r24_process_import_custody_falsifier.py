"""Reproduce exact-R24-prebuild Python -m import provenance false-green.

Research/custody instrument; uses synthetic output bytes, never product credit.
Actual parent owner source is copied verbatim from current repository into a
controlled fixture and Git blob identity is asserted before any subprocess.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

EXACT_R24_OWNER_BLOB = "e3a5f2a13f8553dcdd87a5f0b566dc00ab9ec2a4"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def court(source: Path) -> dict:
    data = source.read_bytes()
    if git_blob(data) != EXACT_R24_OWNER_BLOB:
        raise ValueError("the evaluated parent must be the exact frozen R24 owner")
    with tempfile.TemporaryDirectory(prefix="cmpct-v031-r24-custody-") as td:
        td = Path(td)
        trusted = td / "trusted"
        foreign = td / "foreign"
        neutral = td / "neutral"
        for root in (trusted, foreign):
            (root / "experiments").mkdir(parents=True)
        neutral.mkdir()
        module_name = "entropygraph_v030_r24_process_prebuild.py"
        (trusted / "experiments" / module_name).write_bytes(data)
        (trusted / "experiments" / "entropygraph_v030_release_product.py").write_text(
            "def _locality_bounded_r24_build(root, out):\n"
            "    out.write_bytes(b'EXACT_OWNER_EXECUTED')\n"
            "    return {'source':'trusted','format_revision':24}\n", encoding="utf-8")
        (foreign / "experiments" / "__init__.py").write_text("", encoding="utf-8")
        (foreign / "experiments" / module_name).write_text(
            "import argparse,json\nfrom pathlib import Path\n"
            "p=argparse.ArgumentParser()\n"
            "p.add_argument('--worker',action='store_true')\n"
            "p.add_argument('--root')\np.add_argument('--out')\na=p.parse_args()\n"
            "Path(a.out).write_bytes(b'FORGED_OUTPUT')\n"
            "print(json.dumps({'schema':'cmpct-v030-r24-prebuild-process-v1',"
            "'stats':{'source':'foreign','format_revision':24}}))\n", encoding="utf-8")
        (td / "source").mkdir()
        (td / "source" / "x").write_bytes(b"source payload")
        driver = '''\
import importlib.util, json, os
from pathlib import Path
source = Path(os.environ['R24_EXACT_SOURCE'])
spec = importlib.util.spec_from_file_location('experiments.entropygraph_v030_r24_process_prebuild',source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.R24PrebuildProcess(Path(os.environ['R24_ROOT']), Path(os.environ['R24_OUT']),timeout_s=15) as p:
    stats = p.result()
print(json.dumps({'stats':stats, 'bytes':Path(os.environ['R24_OUT']).read_bytes().decode()}))
'''
        env = os.environ.copy()
        env["R24_EXACT_SOURCE"] = str(trusted / "experiments" / module_name)
        env["R24_ROOT"] = str(td / "source")
        env["PYTHONPATH"] = str(trusted)
        env["PYTHONNOUSERSITE"] = "1"

        def execute(label: str, cwd: Path) -> dict:
            env["R24_OUT"] = str(td / (label + ".cmpct"))
            p = subprocess.run([sys.executable, "-c", driver], cwd=cwd, env=env,
                               capture_output=True, text=True, timeout=20)
            if p.returncode:
                raise RuntimeError("R24 process failed: " + p.stderr[-1600:])
            return json.loads(p.stdout.strip().splitlines()[-1])

        # Caller cwd remains ahead of injected PYTHONPATH inside -m worker.
        false_green = execute("foreign", foreign)
        # A closed regular package plus neutral cwd rules out this *one*
        # namespace/cwd takeover. It is not comprehensive source custody.
        (trusted / "experiments" / "__init__.py").write_text(
            "__path__ = " + repr([str(trusted / "experiments")]) + "\n", encoding="utf-8")
        control = execute("neutral", neutral)
        return {
            "schema": "cmpct-v031-r24-process-import-false-green-v1",
            "exact_owner_blob": EXACT_R24_OWNER_BLOB,
            "false_green": false_green,
            "controlled": control,
            "false_green_confirmed": false_green == {
                "stats": {"source": "foreign", "format_revision": 24},
                "bytes": "FORGED_OUTPUT"},
            "controlled_exact_owner_confirmed": control == {
                "stats": {"source": "trusted", "format_revision": 24},
                "bytes": "EXACT_OWNER_EXECUTED"},
            "product_credit": False,
            "release_credit": False,
        }


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "experiments" / "entropygraph_v030_r24_process_prebuild.py")
    result = court(source)
    print(json.dumps(result, sort_keys=True, indent=2))
    if not result["false_green_confirmed"] or not result["controlled_exact_owner_confirmed"]:
        raise SystemExit(1)
