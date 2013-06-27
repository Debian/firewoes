#!/usr/bin/env python

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

with open('README.txt') as f:
    long_description = f.read()

setup(
    name="firewose",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    author="Matthieu Caneill",
    author_email="matthieu.caneill@gmail.com",
    long_description=long_description,
    description='tool to navigate between Firehose results',
    license="AGPL",
    url="",
    platforms=['any']
)
