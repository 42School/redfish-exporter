from setuptools import setup

setup(
   name='redfish-exporter',
   version='0.1',
   description='IDRAC / ILO redfish api exporter for prometheus',
   python_requires='>=3.5, <4',
   author='bibiche',
   author_email='bibiche@42network.org',
   packages=['redfish_exporter'],
)
