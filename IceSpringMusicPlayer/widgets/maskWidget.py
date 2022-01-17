# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40

from PySide2 import QtWidgets, QtCore, QtGui


class MaskWidget(QtWidgets.QFrame):
    def __init__(self, above: QtWidgets.QFrame):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(QtCore.QRect(self.mapFromGlobal(above.mapToGlobal(above.rect().topLeft())), above.size()))

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        QtGui.QPainter(self).fillRect(self.rect(), QtGui.QColor("#55FF0000"))
