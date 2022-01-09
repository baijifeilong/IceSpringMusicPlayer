# Created by BaiJiFeiLong@gmail.com at 2022/1/9 22:08

from __future__ import annotations

from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.utils.typeHintUtils import gg


class LayoutUtils(object):
    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(gg(None, QtCore.QObject)) if layout.itemAt(i).widget() \
                else layout.removeItem(layout.itemAt(i))
