"""Package the optional CPython 3.11+ stable-ABI fixed-chunk admission helper.

The existing memory-safe Rust core is independently specified in pyproject.toml.
The optional C predicate never owns archive bytes or becomes a parser contract;
Python 3.10 and wheels without the helper retain the strict Python validator.
"""
import sys
from setuptools import Extension, setup

ext_modules = []
options = {}
if sys.version_info >= (3, 11):
    ext_modules.append(
        Extension(
            "cmpct._fastscan_abi3",
            ["src/cmpct/_fastscan_abi3.c"],
            py_limited_api=True,
            optional=True,
        )
    )
    # The same cp311-abi3 wheel can run under later CPython minors on that host.
    options = {"bdist_wheel": {"py_limited_api": "cp311"}}

setup(ext_modules=ext_modules, options=options)
