#!/usr/bin/env python

from setuptools import setup, find_packages
from firewose import __appname__, __version__

with open('requirements.txt') as f:
    install_requires = [l for l in f.read().splitlines()
                        if not l.startswith('#')]

with open('README.txt') as f:
    long_description = f.read()

setup(
    name=__appname__,
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    author="Matthieu Caneill",
    author_email="matthieu.caneill@gmail.com",
    long_description=long_description,
    description='tool to navigate between Firehose results',
    license="AGPL",
    url="http://git.upsilon.cc/?p=firewose.git;a=summary",
    platforms=['any']
)
