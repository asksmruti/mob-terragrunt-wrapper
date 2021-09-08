#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements.txt') as f:
    requirements = f.readlines()

test_requirements = ['pytest>=3', ]

setup(
    author="Smruti Sahoo",
    author_email='ssahoo@mobiquityinc.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Terragrunt wrapper for AWS infra deployment",
    entry_points={
        'console_scripts': [
            'tgwrapper=tgwrapper.tgwrapper:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='tgwrapper',
    name='tgwrapper',
    packages=find_packages(include=['tgwrapper', 'tgwrapper.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/smruti-21/tgwrapper',
    version='0.1.1',
    zip_safe=False,
)
