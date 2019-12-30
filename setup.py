#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()


setup(
    author="David Straub",
    author_email="straub@protonmail.com",
    python_requires=">=3.6",
    description="Standalone history browser for Home Assistant",
    install_requires=[
        "Click>=7.0",
        "dash",
        "pyyaml",
        "sqlalchemy",
        "voluptuous",
        "pandas",
    ],
    long_description=README,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="hibro",
    name="hibro",
    packages=find_packages(include=["hibro", "hibro.*"]),
    entry_points={"console_scripts": ["hibro=hibro.__main__:main"]},
    test_suite="tests",
    version="0.1.0",
    zip_safe=False,
)
