#! /usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='rawsteel-music-player',
    url="https://github.com/baijifeilong/rawsteelp",
    license='GPL3',
    author='BaiJiFeiLong',
    author_email='baijifeilong@gmail.com',
    version='1.0.5',
    description='A minimal music player with lyric show',
    packages=find_packages(),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    zip_safe=False,
    setup_requires=['chardet', 'pytaglib'],
    entry_points={
        'console_scripts': [
            'rawsteel-music-player = rawsteelp.rawsteelp:main'
        ]
    }
)
