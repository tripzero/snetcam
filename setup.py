#!/usr/bin/env python

from setuptools import setup, Extension

setup(name='snetcam',
      version='1.0',
      description='secure network camera server using opencv and python-wss',
      author='Kevron Rees',
      author_email='tripzero.kev@gmail.com',
      url='https://github.com/tripzero/snetcam',
      packages=["snetcam"],
      install_requires=["wss"]
      )
