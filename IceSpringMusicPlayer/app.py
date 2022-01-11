# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    player: Player
    zoom: float

    def __init__(self):
        super().__init__()
        self.zoom = 1.25
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.player = Player(self)
        self.mainWindow = MainWindow(self, self.player)

    def exec_(self) -> int:
        self.setFont(Just.of(self.font()).apply(lambda x: x.setPointSize(x.pointSize() * self.zoom)).value())
        self.mainWindow.resize(QtCore.QSize(1280, 720))
        diff = self.primaryScreen().availableSize() - self.mainWindow.size()
        titleBarHeight = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_TitleBarHeight)
        # self.mainWindow.move(diff.width() - 5, diff.height() - titleBarHeight - 10)
        self.mainWindow.show()
        return super().exec_()
