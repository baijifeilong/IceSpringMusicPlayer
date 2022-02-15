# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import logging
import sys
import typing

import qtawesome
from IceSpringPathLib import Path
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.domains.config import Config

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.services.pluginService import PluginService
    from IceSpringMusicPlayer.services.configService import ConfigService
    from IceSpringMusicPlayer.services.playlistService import PlaylistService
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    requestLocateCurrentMusic: QtCore.SignalInstance = QtCore.Signal()
    configChanged: QtCore.SignalInstance = QtCore.Signal()
    languageChanged: QtCore.SignalInstance = QtCore.Signal(str)

    _logger: logging.Logger
    _config: Config
    _zoom: float
    _player: Player
    _mainWindow: MainWindow

    def getZoom(self) -> float:
        return self._zoom

    def __init__(self):
        from IceSpringMusicPlayer.services.player import Player
        from IceSpringMusicPlayer.windows.mainWindow import MainWindow
        from IceSpringMusicPlayer.services.configService import ConfigService
        from IceSpringMusicPlayer.services.pluginService import PluginService
        from IceSpringMusicPlayer.services.playlistService import PlaylistService
        super().__init__()
        self._logger = logging.getLogger("app")
        self._logger.info("Append plugins folder to sys path")
        sys.path.append(str(Path(__file__).parent / "plugins"))
        self._logger.info("Create recycles folder")
        Path("recycles").mkdir(exist_ok=True)
        self._pluginService = PluginService(self)
        self._configService = ConfigService(self._pluginService, self)
        self._config = self._configService.getConfig()
        self._setupLanguage(self._config.language)
        self._player = Player(self)
        self._player.setVolume(self._config.volume)
        self._playlistService = PlaylistService(self)
        self._zoom = self._config.applicationFont.pointSize() / self.font().pointSize()
        self.setFont(self._config.applicationFont)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.setWindowIcon(qtawesome.icon("mdi.snowflake"))
        self._mainWindow = MainWindow()
        self._mainWindow.setGeometry(self._config.geometry)
        self.aboutToQuit.connect(self._onAboutToQuit)
        self.configChanged.connect(self._onConfigChanged)

    def getPluginService(self) -> PluginService:
        return self._pluginService

    def getConfigService(self) -> ConfigService:
        return self._configService

    def getPlaylistService(self) -> PlaylistService:
        return self._playlistService

    def _setupLanguage(self, language: str):
        self._logger.info("Setup language: %s", language)
        for module in {tt, *{x.getPluginTranslationModule() for x in self._pluginService.getPluginClasses()}}:
            self._logger.info("Setup language for module: %s", module)
            tt.setupLanguage(language, module=module)

    def _onConfigChanged(self):
        self._logger.info("On config changed")
        self.setFont(self._config.applicationFont)

    def _onAboutToQuit(self):
        self._logger.info("On about to quit")
        self._configService.persistConfig()

    def exec_(self) -> int:
        self._logger.info("Exec")
        self._mainWindow.loadLayout(self._config.layout)
        self._mainWindow.show()
        return super().exec_()

    def getConfig(self) -> Config:
        return self._config

    def getPlayer(self) -> Player:
        return self._player

    def getMainWindow(self) -> MainWindow:
        return self._mainWindow

    @staticmethod
    def instance() -> App:
        return gg(QtCore.QCoreApplication.instance())

    def changeLanguage(self, language: str):
        self._logger.info("Change language: %s", language)
        if language == self._config.language:
            self._logger.info("Language not changed, return")
            return
        self._config.language = language
        for module in {tt, *{x.getPluginTranslationModule() for x in self._pluginService.getPluginClasses()}}:
            self._logger.info("Change language for module: %s", module)
            tt.setupLanguage(language, module=module)
        self._logger.info("> Signal app.languageChanged emitting...")
        self.languageChanged.emit(language)
        self._logger.info("< Signal app.languageChanged emitted.")
