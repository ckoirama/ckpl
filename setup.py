# -*- coding: utf-8 -*-
# Copyright (C) 2019 Ckoirama team
# Licensed under the MIT licence - see LICENSE.md
# Author: Ckoirama team

from distutils.command.build import build

from setuptools import setup

setup(
    name='ckpl',
    version='0.1',
    packages=['ckpl'],
    entry_points={
        'console_scripts': ['ckpl = ckpl:main']
    },
    install_requires=[
        'numpy', 'matplotlib', 'astropy', 'scipy'
    ],
    package_data={'ckpl': ['ckpl/data/*']},
    author='Ckoirama team',
    author_email='rodrigo.gonzalez@uamail.cl',
    description='Ckoirama Pipeline',
    license='MIT',
    keywords='astronomy instrumentation, observatory, pipeline'
)
