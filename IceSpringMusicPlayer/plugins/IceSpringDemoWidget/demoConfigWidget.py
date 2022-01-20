# Created by BaiJiFeiLong@gmail.com at 2022/1/20 12:55

from PySide2 import QtWidgets

from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class DemoConfigWidget(QtWidgets.QWidget, ReplaceableMixin):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(QtWidgets.QLabel("DemoConfigWidget", self))
