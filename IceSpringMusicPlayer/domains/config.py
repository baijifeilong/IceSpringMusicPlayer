# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import typing
from dataclasses import dataclass

from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore

from IceSpringMusicPlayer.domains.playlist import Playlist


@dataclass
class Element(object):
    clazz: typing.Type
    weight: float
    children: typing.List[Element]


@dataclass
class Config(object):
    zoom: float
    geometry: QtCore.QRect
    fontSize: int
    iconSize: int
    lyricSize: int
    layout: Element
    frontPlaylistIndex: int
    playlists: Vector[Playlist]

    @staticmethod
    def toJson(obj: typing.Any) -> typing.Any:
        if isinstance(obj, QtCore.QRect):
            return obj.left(), obj.top(), obj.width(), obj.height()
        elif isinstance(obj, type):
            return ".".join((obj.__module__, obj.__name__))
        else:
            return obj.__dict__
