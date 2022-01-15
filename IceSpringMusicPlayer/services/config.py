# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import typing
from dataclasses import dataclass

from PySide2.QtCore import QObject

from IceSpringMusicPlayer.widgets.replacerMixin import HorizontalSplitter, VerticalSplitter


@dataclass
class Element(object):
    clazz: typing.Type
    weight: float
    children: typing.List[Element]


class Config(QObject):
    _miniMode: bool
    _zoom: float
    _layout: Element

    def __init__(self):
        super().__init__()
        self._miniMode = False
        self._zoom = 1.25
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        self._layout = Element(
            clazz=HorizontalSplitter,
            weight=1,
            children=[
                Element(clazz=PlaylistTable, weight=1, children=[]),
                Element(clazz=LyricsPanel, weight=2, children=[]),
                Element(clazz=VerticalSplitter, weight=3, children=[
                    Element(clazz=ControlsPanel, weight=1, children=[]),
                    Element(clazz=LyricsPanel, weight=2, children=[]),
                    Element(clazz=PlaylistTable, weight=3, children=[])]
                )])

    def getMiniMode(self) -> bool:
        return self._miniMode

    def getZoom(self) -> float:
        return self._zoom

    def getLayout(self) -> Element:
        return self._layout
