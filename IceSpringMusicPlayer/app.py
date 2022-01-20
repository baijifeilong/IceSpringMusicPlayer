# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import importlib
import json
import logging
import sys
import typing

from IceSpringPathLib import Path
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow
    from IceSpringMusicPlayer.common.pluginMixin import PluginMixin


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
        super().__init__()
        self._logger = logging.getLogger("app")
        self._config = self._loadConfig()
        tt.setupLanguage(self._config.language)
        self._player = Player(self)
        self._player.setVolume(self._config.volume)
        self._zoom = self._config.applicationFont.pointSize() / self.font().pointSize()
        self.setFont(self._config.applicationFont)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self._mainWindow = MainWindow()
        self._mainWindow.setGeometry(self._config.geometry)
        self.aboutToQuit.connect(self._onAboutToQuit)
        self.configChanged.connect(self._onConfigChanged)

    def _onConfigChanged(self):
        self._logger.info("On config changed")
        self.setFont(self._config.applicationFont)

    def _onAboutToQuit(self):
        self._logger.info("On about to quit")
        self._persistConfig()

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
        return QtCore.QCoreApplication.instance()

    def addMusicsFromFileDialog(self):
        self._logger.info("Add musics from file dialog")
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self._logger.info("There are %d files to open", len(filenames))
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        self._player.insertMusics(musics)

    def addMusicsFromHomeFolder(self):
        self._logger.info("Add musics from home folder")
        paths = Path("~/Music").expanduser().glob("**/*.mp3")
        musics = [MusicUtils.parseMusic(str(x)) for x in paths]
        self._player.insertMusics(musics)

    def loadTestData(self):
        self._logger.info("Load test data")
        paths = Path("~/Music").expanduser().glob("**/*.mp3")
        musics = [MusicUtils.parseMusic(str(x)) for x in paths]
        self._player.setFrontPlaylistIndex(self._player.insertPlaylist())
        self._player.insertMusics([x for i, x in enumerate(musics) if i % 6 in (0, 1, 2)])
        self._player.setFrontPlaylistIndex(self._player.insertPlaylist())
        self._player.insertMusics([x for i, x in enumerate(musics) if i % 6 in (3, 4)])
        self._player.setFrontPlaylistIndex(self._player.insertPlaylist())
        self._player.insertMusics([x for i, x in enumerate(musics) if i % 6 in (5,)])

    def _persistConfig(self):
        self._logger.info("Persist, refresh current config")
        self._config.layout = self._mainWindow.calcLayout()
        self._config.volume = self._player.getVolume()
        self._config.playbackMode = self._player.getPlaybackMode()
        self._config.frontPlaylistIndex = self._player.getFrontPlaylistIndex()
        self._logger.info("Save to config.json")
        Path("config.json").write_text(json.dumps(self._config, indent=4, ensure_ascii=False, default=Config.toJson))

    def _loadConfig(self) -> Config:
        self._logger.info("Load config")
        path = Path("config.json")
        if not path.exists():
            self._logger.info("No config.json file, return default config")
            return Config.getDefaultConfig()
        config = json.loads(path.read_text(), object_pairs_hook=Config.fromJson)
        plugins = self.getPlugins()
        self._logger.info("Process plugin configs (%d plugins)", len(plugins))
        for plugin in plugins:
            _id = ".".join((plugin.__module__, plugin.__name__))
            self._logger.info("Current plugin: %s", _id)
            if _id in config.plugins:
                self._logger.info("Plugin have config, load it")
                pluginConfig = json.loads(
                    json.dumps(config.plugins[_id], default=plugin.getMasterConfigType().pythonToJson),
                    object_pairs_hook=plugin.getMasterConfigType().jsonToPython)
                self._logger.info("Plugin config: %s", pluginConfig)
                config.plugins[_id] = pluginConfig
            else:
                self._logger.info("Plugin have not config, load default one")
                config.plugins[_id] = plugin.getMasterConfigType().getDefaultInstance()
                self._logger.info("Plugin config: %s", config.plugins[_id])
        self._logger.info("Load layout config")
        self._loadElementConfig(config.layout)
        self._logger.info("Loaded config: %s", config)
        return config

    def _loadElementConfig(self, element: Element):
        from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
        if issubclass(element.clazz, PluginMixin):
            self._logger.info("Load element config: %s", element)
            element.config = json.loads(
                json.dumps(element.config, default=element.clazz.getSlaveConfigType().pythonToJson),
                object_pairs_hook=element.clazz.getSlaveConfigType().jsonToPython)
        for child in element.children:
            self._loadElementConfig(child)

    def changeLanguage(self, language: str):
        self._logger.info("Change language: %s", language)
        if language == self._config.language:
            self._logger.info("Language not changed, return")
            return
        self._config.language = language
        tt.setupLanguage(language)
        self._logger.info("> Signal app.languageChanged emitting...")
        self.languageChanged.emit(language)
        self._logger.info("< Signal app.languageChanged emitted.")

    @staticmethod
    def getPlugins() -> typing.List[typing.Type[PluginMixin]]:
        sys.path.append("IceSpringMusicPlayer/plugins")
        demoWidgetType = getattr(importlib.import_module("IceSpringDemoWidget.demoWidget"), "DemoWidget")
        return [demoWidgetType]
