# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import enum
import importlib
import typing
from dataclasses import dataclass

from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore, QtGui, QtWidgets

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
    iconSize: int
    applicationFont: QtGui.QFont
    lyricFont: QtGui.QFont
    volume: int
    playbackMode: PlaybackMode
    frontPlaylistIndex: int
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
        elif isinstance(obj, QtGui.QFont):
            return dict(
                family=obj.family(),
                pointSize=obj.pointSize(),
                weight=obj.weight(),
                italic=obj.italic(),
                underline=obj.underline(),
                strikeOut=obj.strikeOut(),
            )
        else:
            return obj.__dict__

    @classmethod
    def fromJson(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]):
        jd = dict()
        for k, v in pairs:
            if k == "geometry" and len(v) == 4:
                v = QtCore.QRect(*v)
            elif k == "clazz" and "." in v:
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
        elif all(x in jd for x in ("geometry", "layout")):
            return Config(**{
                **cls.getDefaultConfig().__dict__,
                **{k: v for k, v in jd.items() if k in Config.__annotations__}
            })
        elif all(x in jd for x in ("family", "pointSize")):
            font = QtGui.QFont()
            font.setFamily(jd["family"])
            font.setPointSize(jd["pointSize"])
            font.setWeight(jd["weight"])
            font.setItalic(jd["italic"])
            font.setUnderline(jd["underline"])
            font.setStrikeOut(jd["strikeOut"])
            return font
        return dict(**jd)

    @classmethod
    def getDefaultConfig(cls) -> Config:
        screenSize = QtGui.QGuiApplication.primaryScreen().size()
        windowSize = screenSize / 1.5
        diffSize = (screenSize - windowSize) / 2
        defaultGeometry = QtCore.QRect(QtCore.QPoint(diffSize.width(), diffSize.height()), windowSize)
        return Config(
            geometry=defaultGeometry,
            iconSize=48,
            applicationFont=QtWidgets.QApplication.font(),
            lyricFont=QtWidgets.QApplication.font(),
            volume=50,
            playbackMode=PlaybackMode.LOOP,
            frontPlaylistIndex=-1,
            layout=cls.getDefaultLayout(),
            playlists=Vector()
        )

    @staticmethod
    def getDefaultLayout() -> Element:
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
        from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        return Element(clazz=SplitterWidget, vertical=False, weight=1, children=[
            Element(clazz=SplitterWidget, vertical=True, weight=1, children=[
                Element(clazz=ControlsWidget, vertical=False, weight=1, children=[]),
                Element(clazz=LyricsWidget, vertical=False, weight=3, children=[]),
                Element(clazz=PlaylistTable, vertical=False, weight=5, children=[]),
            ]),
            Element(clazz=SplitterWidget, vertical=True, weight=2, children=[
                Element(clazz=PlaylistTable, vertical=False, weight=3, children=[]),
                Element(clazz=LyricsWidget, vertical=False, weight=5, children=[]),
                Element(clazz=ControlsWidget, vertical=False, weight=1, children=[]),
            ]),
        ])

    @staticmethod
    def getDemoLayout() -> Element:
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
        from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        from IceSpringMusicPlayer.widgets.configWidget import ConfigWidget
        from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget
        return Element(clazz=SplitterWidget, vertical=False, weight=1, children=[
            Element(clazz=SplitterWidget, vertical=True, weight=1, children=[
                Element(clazz=ControlsWidget, vertical=False, weight=1, children=[]),
                Element(clazz=LyricsWidget, vertical=False, weight=3, children=[]),
                Element(clazz=PlaylistTable, vertical=False, weight=5, children=[]),
            ]),
            Element(clazz=SplitterWidget, vertical=True, weight=1, children=[
                Element(clazz=ConfigWidget, vertical=False, weight=1, children=[]),
                Element(clazz=BlankWidget, vertical=False, weight=3, children=[]),
            ]),
        ])
