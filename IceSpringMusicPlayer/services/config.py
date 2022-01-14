# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import typing
from dataclasses import dataclass

from PySide2.QtCore import QObject

from IceSpringMusicPlayer.widgets.replacerMixin import BlankWidget, HorizontalSplitter, VerticalSplitter


@dataclass
class Element:
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
        self._layout = Element(
            clazz=HorizontalSplitter,
            weight=1,
            children=[
                Element(
                    clazz=BlankWidget,
                    weight=1,
                    children=[]
                ),
                Element(
                    clazz=BlankWidget,
                    weight=2,
                    children=[]
                ),
                Element(
                    clazz=VerticalSplitter,
                    weight=3,
                    children=[
                        Element(
                            clazz=BlankWidget,
                            weight=1,
                            children=[]
                        ),
                        Element(
                            clazz=BlankWidget,
                            weight=2,
                            children=[]
                        ),
                        Element(
                            clazz=BlankWidget,
                            weight=3,
                            children=[]
                        ),
                    ]
                ),
            ]
        )

    def getMiniMode(self) -> bool:
        return self._miniMode

    def getZoom(self) -> float:
        return self._zoom

    def getLayout(self) -> Element:
        return self._layout
