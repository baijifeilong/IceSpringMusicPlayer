# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:55

import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtGui, QtCore


class IceTableView(QtWidgets.QTableView):
    class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
        def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem,
                index: QtCore.QModelIndex) -> None:
            itemOption = QtWidgets.QStyleOptionViewItem(option)
            if gg(option, typing.Any).state & QtWidgets.QStyle.State_HasFocus:
                itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
            super().paint(painter, itemOption, index)

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
        self.setItemDelegate(self.NoFocusDelegate())
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section { border-top:0px solid #D8D8D8; border-bottom: 1px solid #D8D8D8; "
            "background-color:white; padding:2px; font-weight: light; }")
        self.horizontalHeader().setHighlightSections(False)
        tablePalette = self.palette()
        tablePalette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight,
            tablePalette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight))
        tablePalette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText,
            tablePalette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText))
        self.setPalette(tablePalette)
