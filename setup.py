"""A setuptools based setup module.

See:

* https://packaging.python.org/en/latest/distributing.html
* https://github.com/pypa/sampleproject

Copyright (C) 2020-2020 Jiri Borovec <jiri.borovec@fel.cvut.cz>
"""

# Always prefer setuptools over distutils
from os import path
from setuptools import setup, find_packages

import repostats

PATH_HERE = path.abspath(path.dirname(__file__))


def load_requirements(fname='requirements.txt'):
    with open(path.join(PATH_HERE, fname), encoding='utf-8') as fp:
        reqs = [rq.rstrip() for rq in fp.readlines()]
    reqs = [ln[:ln.index('#')] if '#' in ln else ln for ln in reqs]
    reqs = [ln for ln in reqs if ln]
    return reqs


# Get the long description from the README file
# with open(path.join(PATH_HERE, 'README.md'), encoding='utf-8') as fp:
#     long_description = fp.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    name='repo-stats',
    version=repostats.__version__,
    url=repostats.__homepage__,

    author=repostats.__author__,
    author_email=repostats.__author_email__,
    license=repostats.__license__,
    description=repostats.__doc__,

    long_description=repostats.__long_doc__,
    long_description_content_type='text/markdown',

    packages=find_packages(exclude=['tests', 'tests/*']),

    keywords='repository stats',
    install_requires=load_requirements('requirements.txt'),
    include_package_data=True,
    classifiers=[
        'Environment :: Console',
        'Natural Language :: English',
        # How mature is this project? Common values are
        #   3 - Alpha, 4 - Beta, 5 - Production/Stable
        'Development Status :: 4 - Beta',
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        # Pick your license as you wish
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        # Specify the Python versions you support here.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # entry point from command line
    entry_points={
        'console_scripts': [
            'repostat = repostats.cli:cli_main',
        ],
    }
)
