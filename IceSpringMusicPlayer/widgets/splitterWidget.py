# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40

from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin


class SplitterWidget(QtWidgets.QSplitter, ReplacerMixin):
    def onCustomContextMenuRequested(self, position: QtCore.QPoint):
        pass

    def __init__(self, parent=None, vertical=False):
        orientation = QtCore.Qt.Orientation.Vertical if vertical else QtCore.Qt.Orientation.Horizontal
        super().__init__(orientation, parent)
        ReplacerMixin.__init__(self)
        self.setHandleWidth(2)
