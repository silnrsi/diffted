#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup


setup(
    name = 'diffted',
    version = 0.1,
    description = 'Utility to edit csv files with differencing and git',
    maintainer = 'NRSI - SIL International',
    url = 'http://github.com/silnrsi/diffted',
    packages = ["diffted",
        ],
    package_dir = {'':'lib'},
    install_requires=[
        'PyQt5', 'PyQt5-sip'
    ],
#    package_data={
#        'oxttools': [
#             'data/*.xml',
#    ]},
    scripts = ['scripts/diffted'],
    license = 'MIT',
    platforms = ['Linux','Win32','Mac OS X'],
    classifiers = [
        "Environment :: Console",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Text Processing :: Linguistic",
        ],
)

