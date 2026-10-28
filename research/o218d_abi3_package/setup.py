"""Research-only standalone optional abi3 module. Not shipped as CMPCT."""
from setuptools import Extension, setup

setup(
    name="cmpct-o218d-abi3-research",
    version="0.0.0",
    description="O218d isolated CPython stable ABI research scanner",
    ext_modules=[
        Extension(
            "_o218_fastscan",
            ["o218d_abi3_fastscan.c"],
            py_limited_api=True,
        )
    ],
    options={"bdist_wheel": {"py_limited_api": "cp311"}},
)
