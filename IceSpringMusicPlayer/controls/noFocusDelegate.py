# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:57

import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtGui, QtCore


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        itemOption = QtWidgets.QStyleOptionViewItem(option)
        if gg(option, typing.Any).state & QtWidgets.QStyle.State_HasFocus:
            itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, itemOption, index)
