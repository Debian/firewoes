#!/usr/bin/env python

from setuptools import setup, find_packages
from firewoes import __appname__, __version__

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
    scripts=["firewoes/bin/firewoes_fill_db.py"],
    install_requires=install_requires,
    zip_safe=False,
    author="Matthieu Caneill",
    author_email="matthieu.caneill@gmail.com",
    long_description=long_description,
    description='Web application to navigate between Firehose results',
    license="AGPL",
    url="http://git.upsilon.cc/?p=firewose.git;a=summary",
    platforms=['any']
)
