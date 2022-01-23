# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40

from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.replaceableMixin import ReplaceableMixin
from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget


class SplitterWidget(QtWidgets.QSplitter, ReplaceableMixin):
    _app: App

    def __init__(self, vertical=False, children=0):
        orientation = QtCore.Qt.Orientation.Vertical if vertical else QtCore.Qt.Orientation.Horizontal
        super().__init__(orientation)
        self._app = App.instance()
        self.setHandleWidth(2)
        for _ in range(children):
            self.addWidget(BlankWidget())
        self.setSizes([2 ** 16 for _ in range(children)])

    def refreshHandles(self):
        color = QtGui.QColor("red" if self._app.getMainWindow().getLayoutEditing() else "#EEEEEE")
        for i in range(self.count()):
            handle = self.handle(i)
            palette = handle.palette()
            palette.setColor(QtGui.QPalette.ColorRole.Window, color)
            handle.setPalette(palette)

    def addWidget(self, widget: QtWidgets.QWidget) -> None:
        super().addWidget(widget)
        self.refreshHandles()
