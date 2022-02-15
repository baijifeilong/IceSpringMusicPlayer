# Created by BaiJiFeiLong@gmail.com at 2022/2/15 20:33
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider


class VolumeSlider(FluentSlider):
    def __init__(self):
        super().__init__(QtCore.Qt.Orientation.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
        self.setStyleSheet("""
            QSlider {
                height: 22px;
            }
            QSlider::groove {
                border: 0px solid;
            }
            QSlider::handle {
                background-color: #007AD9;
                width: 12px;
                margin: -3px 0 1px 0;
            }
            QSlider::handle:hover {
                background-color: black;
            }""")

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        pen = painter.pen()
        pen.setColor(QtGui.QColor("#A6A6A6"))
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        topRight = self.rect().topRight()
        topRight.setY(round(self.rect().height() * 0.25))
        bottomLeft = self.rect().bottomLeft()
        bottomLeft.setY(round(self.rect().height() * 0.8))
        painter.drawLine(bottomLeft, topRight)
        super().paintEvent(ev)
