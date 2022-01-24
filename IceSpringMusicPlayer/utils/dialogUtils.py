# Created by BaiJiFeiLong@gmail.com at 2022/1/21 22:20

from PySide2 import QtWidgets, QtCore


class DialogUtils(object):
    @staticmethod
    def execWidget(widget: QtWidgets.QWidget, size: QtCore.QSize = None, withOk=False):
        dialog = QtWidgets.QDialog(QtWidgets.QApplication.activeWindow())
        dialog.setLayout(QtWidgets.QGridLayout(dialog))
        dialog.layout().addWidget(widget)
        if withOk:
            buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
            buttonBox.accepted.connect(lambda: QtWidgets.QApplication.activeModalWidget().close())
            dialog.layout().addWidget(buttonBox)
        dialog.resize(size or QtCore.QSize(854, 480))
        dialog.exec_()
