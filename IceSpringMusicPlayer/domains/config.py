# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import enum
import importlib
import typing
from dataclasses import dataclass

from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore, QtGui

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.domains.plugin import Plugin
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode


@dataclass
class Element(object):
    clazz: typing.Type
    vertical: bool
    weight: float
    config: typing.Any
    children: typing.List[Element]


@dataclass
class Config(object):
    language: str
    geometry: QtCore.QRect
    iconSize: int
    applicationFont: QtGui.QFont
    lyricFont: QtGui.QFont
    volume: int
    playbackMode: PlaybackMode
    frontPlaylistIndex: int
    layout: Element
    plugins: typing.List[Plugin]
    playlists: Vector[Playlist]

    @staticmethod
    def toJson(obj: typing.Any) -> typing.Any:
        if isinstance(obj, QtCore.QRect):
            return dict(left=obj.left(), top=obj.top(), width=obj.width(), height=obj.height())
        elif isinstance(obj, enum.Enum):
            return obj.value
        elif isinstance(obj, type):
            return ".".join((obj.__module__, obj.__name__))
        elif isinstance(obj, set):
            return sorted(obj)
        elif isinstance(obj, QtGui.QFont):
            return dict(
                family=obj.family(),
                pointSize=obj.pointSize(),
                weight=obj.weight(),
                italic=obj.italic(),
                underline=obj.underline(),
                strikeOut=obj.strikeOut(),
            )
        elif isinstance(obj, JsonSupport):
            return obj.__class__.pythonToJson(obj)
        elif isinstance(obj, dict):
            return obj
        else:
            return obj.__dict__

    @classmethod
    def fromJson(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]):
        jd = dict()
        for k, v in pairs:
            if k == "clazz" and "." in v:
                module, clazz = v.rsplit(".", maxsplit=1)
                v = getattr(importlib.import_module(module), clazz)
            elif k in ("musics", "playlists") and isinstance(v, list):
                v = Vector(v)
            elif k == "selectedIndexes":
                v = set(v)
            elif k == "playbackMode":
                v = PlaybackMode(v)
            jd[k] = v
        if all(x in jd for x in ("clazz", "children")):
            return Element(**jd)
        elif all(x in jd for x in ("filename", "filesize")):
            return Music(**jd)
        elif all(x in jd for x in ("name", "musics")):
            return Playlist(**jd)
        elif all(x in jd for x in ("left", "top", "width", "height")):
            return QtCore.QRect(jd["left"], jd["top"], jd["width"], jd["height"])
        elif all(x in jd for x in ("family", "pointSize")):
            font = QtGui.QFont()
            font.setFamily(jd["family"])
            font.setPointSize(jd["pointSize"])
            font.setWeight(jd["weight"])
            font.setItalic(jd["italic"])
            font.setUnderline(jd["underline"])
            font.setStrikeOut(jd["strikeOut"])
            return font
        elif all(x in jd for x in ("clazz", "disabled")):
            return Plugin(**jd)
        return jd
