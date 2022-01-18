# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:55

import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtGui, QtCore

from IceSpringMusicPlayer.controls.noFocusDelegate import NoFocusDelegate


class IceTableView(QtWidgets.QTableView):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(gg(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers,
            QtWidgets.QAbstractItemView.EditTriggers))
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(
            gg(QtCore.Qt.AlignmentFlag.AlignLeft) | QtCore.Qt.AlignmentFlag.AlignVCenter)
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
