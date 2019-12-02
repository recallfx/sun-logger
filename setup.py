from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
   name='sun-logger',
   version='1.0',
   description='SUN2000 inverter logger',
   author='Marius Bieliauskas',
   author_email='mbieliau@gmail.com',
   packages=['sun-logger'],
   install_requires=requirements,
)
