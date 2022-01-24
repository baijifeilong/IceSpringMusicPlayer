# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40

from PySide2 import QtWidgets

from IceSpringMusicPlayer.common.replacerMixin import ReplacerMixin


class BlankWidget(QtWidgets.QFrame, ReplacerMixin):
    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout(self))
        label = QtWidgets.QLabel("BLANK", self)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.layout().addWidget(label)
