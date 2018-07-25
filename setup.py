#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="José María Domínguez Moreno",
    author_email='miso.0b11@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    description="A command line tool to handle changelogs using Git commit messages",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='braulio',
    name='braulio',
    packages=find_packages(include=['braulio']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/mbarakaja/braulio',
    version='0.2.0',
    zip_safe=False,
    entry_points='''
        [console_scripts]
        brau=braulio.cli:cli
    ''',
)
