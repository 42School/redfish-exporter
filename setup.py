import os
from setuptools import setup

setup(
    name = "redfish_exporter",
    version = "1.2",
    author = "bibiche",
    description = ("Exporter for redfish API."),
    keywords = "prometheus exporter idrac redfish",
    url = "https://github.com/42School/redfish_exporter",
    packages=['redfish_exporter'],
    entry_points={
        'console_scripts': [
            'redfish_exporter=redfish_exporter.__main__:main',
        ],
    },
    install_requires=[
        'certifi>=2020.4.5.1',
        'prometheus_client>=0.7.1',
        'pyyaml>=5.3.1',
        'requests>=2.23.0',
        'click>=7.1.2',
        'Jinja2>=2.11.2',
        'logger>=1.4',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
