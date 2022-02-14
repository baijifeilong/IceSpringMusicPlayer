# Created by BaiJiFeiLong@gmail.com at 2022/1/24 15:41

from __future__ import annotations

import dataclasses

from PySide2 import QtGui, QtWidgets

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class LyricsWidgetConfig(JsonSupport):
    font: QtGui.QFont
    horizontalScrollBarPolicy: str
    verticalScrollBarPolicy: str

    @classmethod
    def getDefaultObject(cls) -> LyricsWidgetConfig:
        return LyricsWidgetConfig(font=QtWidgets.QApplication.font(), horizontalScrollBarPolicy="AUTO",
            verticalScrollBarPolicy="AUTO")
