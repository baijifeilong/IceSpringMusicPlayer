# Created by BaiJiFeiLong@gmail.com at 2022/1/8 22:57

from PySide2 import QtWidgets, QtGui, QtCore

from IceSpringMusicPlayer.utils.typeHintUtils import gg


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        itemOption = QtWidgets.QStyleOptionViewItem(option)
        if gg(option).state & QtWidgets.QStyle.State_HasFocus:
            itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, itemOption, index)
