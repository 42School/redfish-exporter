import os
from setuptools import find_packages
from setuptools import setup

setup(
    name = "redfish_exporter",
    version = "1.0",
    author = "bibiche",
    description = ("Exporter for redfish API."),
    keywords = "prometheus exporter idrac redfish",
    url = "https://github.com/42School/redfish_exporter",
    #package_dir={"": "redfish_exporter"},
    packages=find_packages('redfish_exporter'),
    entry_points={
        'console_scripts': [
            'redfish_exporter=redfish_exporter.cli:main',
        ],
    },
    #test_suite="tests",
    install_requires=[
        'prometheus_client>=0.7.1',
        'redfish>=2.1.5',
        'pyyaml',
        'requests',
        'click>=7.1.2',
        'Jinja2>=2.11.2',
        'logger>=1.4',
    ],
    classifiers=[
    ],
)
