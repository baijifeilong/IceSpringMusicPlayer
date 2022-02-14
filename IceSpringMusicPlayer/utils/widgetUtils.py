# Created by BaiJiFeiLong@gmail.com at 2022/1/24 0:26
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets


class WidgetUtils(object):
    @staticmethod
    def createExpandingSpacer():
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(gg(QtWidgets.QSizePolicy.Expanding), gg(QtWidgets.QSizePolicy.Expanding))
        return spacer

    @staticmethod
    def createButtonBox(ok=False, cancel=False, apply=False):
        flag = 0
        if ok:
            flag |= QtWidgets.QDialogButtonBox.StandardButton.Ok
        if cancel:
            flag |= QtWidgets.QDialogButtonBox.StandardButton.Cancel
        if apply:
            flag |= QtWidgets.QDialogButtonBox.StandardButton.Apply
        return QtWidgets.QDialogButtonBox(gg(flag))

    @staticmethod
    def createHorizontalExpander():
        return Just.of(QtWidgets.QWidget()).apply(
            lambda x: x.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)).value()

    @staticmethod
    def createHorizontalSpacer(width):
        return Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedWidth(width)).value()

    @staticmethod
    def createMenuButton(text: str, menu: QtWidgets.QMenu) -> QtWidgets.QToolButton:
        toolButton = QtWidgets.QToolButton()
        toolButton.setText(text)
        toolButton.setMenu(menu)
        toolButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        toolButton.setStyleSheet("QToolButton::menu-indicator { image: none; } QToolButton { padding-left: -15px }")
        return toolButton
