#! /usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='rawsteel-music-player',
    url="https://github.com/baijifeilong/rawsteelp",
    license='GPL3',
    author='BaiJiFeiLong',
    author_email='baijifeilong@gmail.com',
    version='1.0.0',
    description='A minimal music player with lyric show',
    packages=find_packages(),
    long_description=open('README.md').read(),
    zip_safe=False,
    setup_requires=['chardet', 'pytaglib'],
    scripts=['rawsteelp/rawsteelp.py']
)
