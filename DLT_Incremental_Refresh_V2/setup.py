"""
setup.py configuration script describing how to build and package this project.

This file is primarily used by the setuptools library and typically should not
be executed directly. See README.md for how to deploy, test, and run
the DLT_Incremental_Refresh_V2 project.
"""

from setuptools import setup, find_packages

import sys

sys.path.append("./src")

import datetime
import DLT_Incremental_Refresh_V2

local_version = datetime.datetime.utcnow().strftime("%Y%m%d.%H%M%S")

setup(
    name="pipeline-events-analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "databricks-sdk>=0.12.0",
        "pyspark>=3.4.0",
        "delta-spark>=2.4.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to analyze Databricks pipeline events and store them in Unity Catalog",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
