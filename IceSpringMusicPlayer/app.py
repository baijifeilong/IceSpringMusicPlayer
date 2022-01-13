# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import typing

from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtCore

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.config import Config
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    _config: Config
    _player: Player
    _mainWindow: MainWindow

    def __init__(self):
        from IceSpringMusicPlayer.services.config import Config
        from IceSpringMusicPlayer.services.player import Player
        from IceSpringMusicPlayer.windows.mainWindow import MainWindow
        super().__init__()
        self._config = Config()
        self._player = Player(self)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self._mainWindow = MainWindow()

    def exec_(self) -> int:
        self.setFont(
            Just.of(self.font()).apply(lambda x: x.setPointSize(x.pointSize() * self._config.getZoom())).value())
        self._mainWindow.resize(QtCore.QSize(640, 360) if self._config.getMiniMode() else QtCore.QSize(1280, 720))
        diff = self.primaryScreen().availableSize() - self._mainWindow.size()
        titleBarHeight = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_TitleBarHeight)
        self._config.getMiniMode() and self._mainWindow.move(diff.width() - 5, diff.height() - titleBarHeight - 10)
        self._mainWindow.show()
        return super().exec_()

    def getConfig(self) -> Config:
        return self._config

    def getPlayer(self) -> Player:
        return self._player

    @staticmethod
    def instance() -> App:
        return QtCore.QCoreApplication.instance()
