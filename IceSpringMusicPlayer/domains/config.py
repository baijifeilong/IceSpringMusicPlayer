# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import enum
import importlib
import typing
from dataclasses import dataclass

from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore

from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode


@dataclass
class Element(object):
    clazz: typing.Type
    vertical: bool
    weight: float
    children: typing.List[Element]


@dataclass
class Config(object):
    geometry: QtCore.QRect
    fontSize: int
    iconSize: int
    lyricSize: int
    volume: int
    playbackMode: PlaybackMode
    frontPlaylistIndex: int
    selectedMusicIndexes: typing.Set[int]
    layout: Element
    playlists: Vector[Playlist]

    @staticmethod
    def toJson(obj: typing.Any) -> typing.Any:
        if isinstance(obj, QtCore.QRect):
            return obj.left(), obj.top(), obj.width(), obj.height()
        elif isinstance(obj, enum.Enum):
            return obj.value
        elif isinstance(obj, type):
            return ".".join((obj.__module__, obj.__name__))
        elif isinstance(obj, set):
            return sorted(obj)
        else:
            return obj.__dict__

    @staticmethod
    def fromJson(pairs: typing.List[typing.Tuple[str, typing.Any]]):
        jd = dict()
        for k, v in pairs:
            if k == "geometry" and len(v) == 4:
                v = QtCore.QRect(*v)
            elif k == "clazz" and "." in v:
                module, clazz = v.rsplit(".", maxsplit=1)
                v = getattr(importlib.import_module(module), clazz)
            elif k in ("musics", "playlists") and isinstance(v, list):
                v = Vector(v)
            elif k == "selectedMusicIndexes":
                v = set(v)
            elif k == "playbackMode":
                v = PlaybackMode(v)
            jd[k] = v
        _type = dict
        if all(x in jd for x in ("clazz", "children")):
            _type = Element
        elif all(x in jd for x in ("filename", "filesize")):
            _type = Music
        elif all(x in jd for x in ("name", "musics")):
            _type = Playlist
        return _type(**jd)
