#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="rngtest",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "write_to": "src/rngtest/_version.py",
        "fallback_version": "0.0.0",
    },
    description="Generated with cookiecutter-pylibrary.",
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    author="Matthew Barber",
    author_email="quitesimplymatt@gmail.com",
    url="https://github.com/Honno/rngtest",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
    ],
    project_urls={
        "Documentation": "https://rngtest.readthedocs.io/",
        "Changelog": "https://rngtest.readthedocs.io/en/latest/changelog.html",
        "Issue Tracker": "https://github.com/Honno/rngtest/issues",
    },
    keywords=[
        # TODO eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires="!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    install_requires=["click", "numpy", "scipy", "appdirs", "python-slugify", "pandas", "matplotlib"],
    test_requires=["pytest", "hypothesis"],
    setup_requires=["setuptools_scm>=3.3.1"],
    entry_points={"console_scripts": ["rngtest = rngtest.cli:main"]},
)
