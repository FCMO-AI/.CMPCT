"""J24R04b parent-only diagnostic wrapper for unchanged J24R01 script.

Re-raises all original CalledProcessError statuses; changes no child command,
measurement, control input, benchmark order, or subprocess timeout.
"""
from __future__ import annotations

import runpy
import subprocess
import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: wrapper.py original-script.py [original args...]")
    script = sys.argv[1]
    sys.argv = [script, *sys.argv[2:]]
    inherited = subprocess.run

    def transparent_run(*args, **kwargs):
        try:
            return inherited(*args, **kwargs)
        except subprocess.CalledProcessError as exc:
            print("J24R04B_ORIGINAL_CHILD_FAILED", file=sys.stderr, flush=True)
            print("J24R04B_EXIT_CODE="+str(exc.returncode), file=sys.stderr, flush=True)
            print("J24R04B_CHILD_CMD="+repr(exc.cmd), file=sys.stderr, flush=True)
            print("J24R04B_CHILD_STDOUT="+repr(exc.stdout), file=sys.stderr, flush=True)
            print("J24R04B_CHILD_STDERR="+repr(exc.stderr), file=sys.stderr, flush=True)
            raise

    subprocess.run = transparent_run
    runpy.run_path(script, run_name="__main__")


if __name__=="__main__":
    main()
