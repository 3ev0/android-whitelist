__author__ = 'ivo'

from setuptools import setup, find_packages

setup(
    name="blackswan",
    version="0.1",
    packages=find_packages(),
    entry_points={
                  "console_scripts":["explore = blackswan.modules.explore:main"]
    }
)

