# Created by BaiJiFeiLong@gmail.com at 2022/1/21 22:20

from PySide2 import QtWidgets, QtCore


class DialogUtils(object):
    @staticmethod
    def execWidget(widget: QtWidgets.QWidget, parent: QtWidgets.QWidget = None, size: QtCore.QSize = None):
        dialog = QtWidgets.QDialog(parent)
        dialog.setLayout(QtWidgets.QGridLayout(dialog))
        dialog.layout().addWidget(widget)
        size is not None and dialog.resize(size)
        dialog.exec_()
