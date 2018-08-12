#! /usr/bin/env sh

if [ "$1" = 'clean' ]; then
    rm -rf build dist rawsteel_music_player.egg-info
    exit
fi

python setup.py sdist bdist_wheel
twine upload dist/*

