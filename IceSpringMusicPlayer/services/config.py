# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import typing
from dataclasses import dataclass

from IceSpringRealOptional.maybe import Maybe
from PySide2 import QtCore


@dataclass
class Element(object):
    clazz: typing.Type
    weight: float
    children: typing.List[Element]


class Config(QtCore.QObject):
    _geometry: Maybe[QtCore.QRect]
    _fontSize: Maybe[int]
    _iconSize: Maybe[int]
    _lyricSize: Maybe[int]
    _layout: Element

    def __init__(self):
        super().__init__()
        self._geometry = Maybe.empty()
        self._fontSize = Maybe.empty()
        self._iconSize = Maybe.empty()
        self._lyricSize = Maybe.empty()
        self._layout = self._getDefaultLayout()

    def getGeometry(self) -> Maybe[QtCore.QRect]:
        return self._geometry

    def setGeometry(self, geometry: Maybe[QtCore.QRect]) -> None:
        self._geometry = geometry

    def getFontSize(self) -> Maybe[int]:
        return self._fontSize

    def setFontSize(self, size: Maybe[int]) -> None:
        self._fontSize = size

    def getIconSize(self) -> Maybe[int]:
        return self._iconSize

    def setIconSize(self, size: Maybe[int]) -> None:
        self._iconSize = size

    def getLyricSize(self) -> Maybe[int]:
        return self._lyricSize

    def getLyricSizeOrDefault(self) -> int:
        return self._lyricSize.orElse(12)

    def setLyricSize(self, size: Maybe[int]) -> None:
        self._lyricSize = size

    def getLayout(self) -> Element:
        return self._layout

    def setLayout(self, layout: Element) -> None:
        self._layout = layout

    @staticmethod
    def _getDefaultLayout() -> Element:
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        from IceSpringMusicPlayer.widgets.replacerMixin import HorizontalSplitter, VerticalSplitter
        return Element(clazz=HorizontalSplitter, weight=1, children=[
            Element(clazz=VerticalSplitter, weight=1, children=[
                Element(clazz=ControlsPanel, weight=1, children=[]),
                Element(clazz=LyricsPanel, weight=3, children=[]),
                Element(clazz=PlaylistTable, weight=5, children=[]),
            ]),
            Element(clazz=VerticalSplitter, weight=2, children=[
                Element(clazz=PlaylistTable, weight=3, children=[]),
                Element(clazz=LyricsPanel, weight=5, children=[]),
                Element(clazz=ControlsPanel, weight=1, children=[]),
            ]),
        ])
