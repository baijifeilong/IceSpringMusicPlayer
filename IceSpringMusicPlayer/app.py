# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

from PySide2 import QtWidgets

from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    player: Player

    def __init__(self):
        super().__init__()
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.player = Player(self)
        self.mainWindow = MainWindow(self, self.player)

    def exec_(self) -> int:
        self.mainWindow.resize(1280, 720)
        self.mainWindow.show()
        return super().exec_()
