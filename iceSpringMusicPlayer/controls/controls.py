# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:22:43

import typing

from PySide2 import QtWidgets, QtGui, QtCore

from iceSpringMusicPlayer.utils import gg


class IceTableView(QtWidgets.QTableView):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(gg(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers))
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("alternate-background-color: rgb(245, 245, 245)")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setShowGrid(False)
        self.setItemDelegate(NoFocusDelegate())
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section { border-top:0px solid #D8D8D8; border-bottom: 1px solid #D8D8D8; "
            "background-color:white; padding:2px; font-weight: light; }")
        self.horizontalHeader().setHighlightSections(False)
        tablePalette = self.palette()
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight))
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        self.setPalette(tablePalette)


class ClickableLabel(QtWidgets.QLabel):
    clicked: QtCore.SignalInstance = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.clicked.emit(ev)


class FluentSlider(QtWidgets.QSlider):
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.setValue(
            self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
        super().mousePressEvent(ev)


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        itemOption = QtWidgets.QStyleOptionViewItem(option)
        if gg(option).state & QtWidgets.QStyle.State_HasFocus:
            itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, itemOption, index)
