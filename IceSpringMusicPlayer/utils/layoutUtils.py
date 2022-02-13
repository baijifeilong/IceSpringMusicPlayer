# Created by BaiJiFeiLong@gmail.com at 2022/1/9 22:08

from __future__ import annotations

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QApplication


class LayoutUtils(object):
    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(gg(None, QtCore.QObject)) if layout.itemAt(i).widget() \
                else layout.removeItem(layout.itemAt(i))

    @classmethod
    def toggleFullscreen(cls, widget: QtWidgets.QWidget):
        if not hasattr(cls, "__fullscreen"):
            setattr(cls, "__fullscreen", dict())
        jd = getattr(cls, "__fullscreen")
        if not widget.isFullScreen():
            parent = widget.parentWidget()
            window = QApplication.activeWindow()
            assert isinstance(parent, QtWidgets.QSplitter)
            jd[id(widget)] = [parent, parent.indexOf(widget), parent.sizes(), QApplication.activeWindow()]
            widget.setParent(gg(None))
            widget.showFullScreen()
            window.hide()
        else:
            parent, index, sizes, window = jd[id(widget)]
            assert isinstance(parent, QtWidgets.QSplitter)
            window.show()
            parent.insertWidget(index, widget)
            parent.setSizes(sizes)
            del jd[id(widget)]
