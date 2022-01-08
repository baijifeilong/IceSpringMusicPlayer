# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:56
from PySide2 import QtWidgets, QtGui, QtCore


class FluentSlider(QtWidgets.QSlider):
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.setValue(
            self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
        super().mousePressEvent(ev)