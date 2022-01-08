# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:56

from PySide2 import QtWidgets, QtCore, QtGui


class ClickableLabel(QtWidgets.QLabel):
    clicked: QtCore.SignalInstance = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.clicked.emit(ev)
