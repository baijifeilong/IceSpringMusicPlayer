# Created by BaiJiFeiLong@gmail.com at 2022/1/13 21:27

from PySide2 import QtWidgets


class Line(QtWidgets.QFrame):
    def __init__(self, vertical=False, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.VLine if vertical else QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.setStyleSheet("color: #D8D8D8")
