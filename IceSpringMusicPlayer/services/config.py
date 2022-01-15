# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from __future__ import annotations

import typing
from dataclasses import dataclass

from PySide2 import QtCore


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
