# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40

import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin


class BlankWidget(QtWidgets.QFrame, ReplacerMixin):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        ReplacerMixin.__init__(self)
        self.setLayout(QtWidgets.QGridLayout(self))
        label = QtWidgets.QLabel("BLANK", self)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.layout().addWidget(label)
