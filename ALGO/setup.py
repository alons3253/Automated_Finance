#!/usr/bin/env python

import setuptools

with open("README.md", 'r') as fr:
    long_description = fr.read()

setuptools.setup(
    license="MIT",
    name='automated-finance',
    version='0.9',
    description='Used for stock trading with the Alpaca API',
    authors='Anthony Lonsdale',
    long_description=long_description,
    url='https://github.com/alons3253/Automated_Finance',
    author_email='alons3253@gmail.com',
    packages=setuptools.find_packages(),

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: GPU :: NVIDIA CUDA :: 11.6",
        "Intended Audience :: Financial and Insurance Industry",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires='>=3.0',
)