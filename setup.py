"""A setuptools based setup module.

See:

* https://packaging.python.org/en/latest/distributing.html
* https://github.com/pypa/sampleproject

Copyright (C) 2020-2021 Jiri Borovec <...>
"""
from importlib.util import module_from_spec, spec_from_file_location

# Always prefer setuptools over distutils
from os import path

from setuptools import find_packages, setup

_PATH_ROOT = path.abspath(path.dirname(__file__))
_PATH_SOURCE = path.join(_PATH_ROOT, "src")


def _load_requirements(fname="requirements.txt") -> list:
    with open(path.join(_PATH_ROOT, fname), encoding="utf-8") as fp:
        reqs = [rq.rstrip() for rq in fp.readlines()]
    reqs = [ln[: ln.index("#")] if "#" in ln else ln for ln in reqs]
    return [ln for ln in reqs if ln]


def _load_py_module(fname: str, pkg: str = "repo_stats"):
    spec = spec_from_file_location(path.join(pkg, fname), path.join(_PATH_SOURCE, pkg, fname))
    py = module_from_spec(spec)
    spec.loader.exec_module(py)
    return py


about = _load_py_module("__about__.py")


# Get the long description from the README file
# with open(path.join(_PATH_HERE, 'README.md'), encoding='utf-8') as fp:
#     long_description = fp.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    name="repo-stats",
    version=about.__version__,
    url=about.__homepage__,
    author=about.__author__,
    author_email=about.__author_email__,
    license=about.__license__,
    description=about.__doc__,
    long_description=about.__long_doc__,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    keywords="repository stats",
    install_requires=_load_requirements("requirements.txt"),
    include_package_data=True,
    classifiers=[
        "Environment :: Console",
        "Natural Language :: English",
        # How mature is this project? Common values are
        #   3 - Alpha, 4 - Beta, 5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        # Specify the Python versions you support here.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    # entry point from command line
    entry_points={
        "console_scripts": [
            "repostat = repo_stats.__main__:cli_main",
        ],
    },
)
