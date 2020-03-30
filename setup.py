#!/usr/bin/env python3
"""ManualBox project"""
from setuptools import find_packages, setup

setup(
    name="manualbox",
    version="0.2.0",
    description="A secure storage as file system which requires user input to access files.",
    long_description="A simple testing system which can be maintained.",
    platforms=["Linux", "Darwin"],
    author="Kushal Das",
    author_email="mail@kushaldas.in",
    url="https://manualbox.org",
    license="GPLv3+",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "manualbox = manualbox:main",
            "manualboxinput = manualbox.manualinput:main",
        ]
    },
)
