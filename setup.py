#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.extension import Extension


setup(
    name="coilsnake",
    version="2.3.1",
    description="CoilSnake",
    url="https://kiij.github.io/CoilSnake",
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        "Pillow>=3.0.0",
        "PyYAML>=3.11",
        "CCScriptWriter>=1.1",
        "ccscript>=1.337"
    ],
    dependency_links=[
        "https://github.com/Lyrositor/CCScriptWriter/tarball/master#egg=CCScriptWriter-1.1",
        "https://github.com/mraccident/ccscript_legacy/tarball/master#egg=ccscript-1.337"
    ],
    ext_modules=[
        Extension("coilsnake.util.eb.native_comp", ["coilsnake/util/eb/native_comp.c"])
    ],
    entry_points={
        "console_scripts": [
            "coilsnake = coilsnake.ui.gui:main",
            "coilsnake-cli = coilsnake.ui.cli:main"
        ]
    },

    test_suite="nose.collector",
    tests_require=[
        "nose>=1.0",
        "mock>=1.0.1"
    ],
)
