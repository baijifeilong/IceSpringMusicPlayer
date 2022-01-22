# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import importlib
import json
import logging
import typing

from IceSpringPathLib import Path
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.domains.plugin import Plugin
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow
    from IceSpringMusicPlayer.common.pluginMixin import PluginMixin


class App(QtWidgets.QApplication):
    requestLocateCurrentMusic: QtCore.SignalInstance = QtCore.Signal()
    configChanged: QtCore.SignalInstance = QtCore.Signal()
    languageChanged: QtCore.SignalInstance = QtCore.Signal(str)
    pluginStateChanged: QtCore.SignalInstance = QtCore.Signal()
    pluginsInserted: QtCore.SignalInstance = QtCore.Signal(list)

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
        self._setupLanguage(self._config.language)
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

    def _setupLanguage(self, language: str):
        self._logger.info("Setup language: %s", language)
        for module in {tt, *{x.getPluginTranslationModule() for x in self.getPluginClasses()}}:
            self._logger.info("Setup language for module: %s", module)
            tt.setupLanguage(language, module=module)

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
        config: Config = json.loads(path.read_text(), object_pairs_hook=Config.fromJson)
        self._logger.info("Process plugin configs (%d plugins)", len(self.getPluginClasses()))
        for plugin in config.plugins:
            self._logger.info("Plugin in config: %s", plugin)
            jd = json.loads(
                json.dumps(plugin.config, default=plugin.clazz.getPluginConfigClass().pythonToJson),
                object_pairs_hook=plugin.clazz.getPluginConfigClass().jsonToPython)
            plugin.config = gg(plugin.clazz.getPluginConfigClass())(**jd)
        self._logger.info("Process plugins not in config")
        loadedClasses = [x.clazz for x in config.plugins]
        for clazz in self.getPluginClasses():
            if clazz not in loadedClasses:
                self._logger.info("Plugin not in config: %s", clazz)
                config.plugins.append(
                    Plugin(clazz=clazz, disabled=False, config=clazz.getPluginConfigClass().getDefaultObject()))
        self._logger.info("Sort plugins")
        config.plugins.sort(key=lambda x: x.clazz.__module__ + "." + x.clazz.__name__)
        self._logger.info("Load layout config")
        self._loadElementConfig(config.layout)
        self._logger.info("Loaded config: %s", config)
        return config

    def _loadElementConfig(self, element: Element):
        from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
        if issubclass(element.clazz, PluginWidgetMixin):
            self._logger.info("Load element config: %s", element)
            elementConfigJd = json.loads(
                json.dumps(element.config, default=element.clazz.getWidgetConfigClass().pythonToJson),
                object_pairs_hook=element.clazz.getWidgetConfigClass().jsonToPython)
            elementConfig = gg(element.clazz.getWidgetConfigClass())(**elementConfigJd)
            self._logger.info("Loaded element config: %s", elementConfig)
            element.config = elementConfig
        for child in element.children:
            self._loadElementConfig(child)

    def changeLanguage(self, language: str):
        self._logger.info("Change language: %s", language)
        if language == self._config.language:
            self._logger.info("Language not changed, return")
            return
        self._config.language = language
        for module in {tt, *{x.getPluginTranslationModule() for x in self.getPluginClasses()}}:
            self._logger.info("Change language for module: %s", module)
            tt.setupLanguage(language, module=module)
        self._logger.info("> Signal app.languageChanged emitting...")
        self.languageChanged.emit(language)
        self._logger.info("< Signal app.languageChanged emitted.")

    def getPluginClasses(self) -> typing.List[typing.Type[PluginMixin]]:
        return self.findPluginClassesInFolder("IceSpringMusicPlayer/plugins")

    def findPluginClassesInFolder(self, folder):
        self._logger.info("Find plugin classes in folder: %s", folder)
        from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
        classes = set()
        pluginRoot = Path("IceSpringMusicPlayer/plugins")
        for path in Path(folder).glob("**/*.py"):
            package = ".".join([x for x in path.relative_to(pluginRoot).parts if x != "__init__.py"]).rstrip(".py")
            for x in importlib.import_module(package).__dict__.values():
                if isinstance(x, type) and issubclass(x, PluginMixin) and x != PluginMixin:
                    classes.add(x)
        return sorted(classes, key=lambda x: x.__module__ + "." + x.__name__)

    def verifyPlugin(self, folder: str) -> typing.List[typing.Type[PluginMixin]]:
        self._logger.info("Verify plugin in folder: %s", folder)
        root = Path(folder)
        if not (root / "__init__.py").exists():
            raise RuntimeError("Plugin folder must contains __init__.py")
        targetPath = Path(f"IceSpringMusicPlayer/plugins/{root.name}")
        if targetPath.exists():
            self._logger.info("Plugin already exists.")
            raise RuntimeError("Plugin Already Exists")
        self._logger.info("Copy plugin folder to plugins dir %s", targetPath)
        root.copytree(targetPath)
        try:
            classes = self.findPluginClassesInFolder(str(targetPath))
        except Exception as e:
            self._logger.info("Exception occurred: %s", e, e)
            self._logger.info("Remove folder: %s", targetPath)
            targetPath.rmtree()
            raise e
        if len(classes) == 0:
            self._logger.info("No plugin found in folder, remove folder")
            targetPath.rmtree()
        return classes

    def registerNewPlugins(self, classes: typing.List[typing.Type[PluginMixin]]) -> None:
        self._logger.info("Register new %d plugins", len(classes))
        for clazz in classes:
            self._logger.info("Register plugin %s", clazz)
            self._config.plugins.append(Plugin(
                clazz=clazz,
                disabled=False,
                config=clazz.getPluginConfigClass().getDefaultObject()
            ))
        self._logger.info("> Signal pluginInserted emitting...")
        self.pluginsInserted.emit(classes)
        self._logger.info("< Signal pluginInserted emitted.")
