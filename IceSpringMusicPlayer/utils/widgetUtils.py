# Created by BaiJiFeiLong@gmail.com at 2022/1/24 0:26

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
