# Created by BaiJiFeiLong@gmail.com at 2022/1/23 19:28
import json
import logging

from IceSpringPathLib import Path
from IceSpringRealOptional.typingUtils import gg
from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.domains.plugin import Plugin
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.services.pluginService import PluginService


class ConfigService(QtCore.QObject):
    def __init__(self, pluginService: PluginService, parent: QtCore.QObject = None):
        super().__init__(parent)
        self._logger = logging.getLogger("configService")
        self._app = App.instance()
        self._pluginService = pluginService
        self._config = self._loadConfig()

    def getConfig(self):
        return self._config

    def persistConfig(self):
        self._logger.info("Persist, refresh current config")
        self._config.layout = self._app.getMainWindow().calcLayout()
        self._config.volume = self._app.getPlayer().getVolume()
        self._config.playbackMode = self._app.getPlayer().getPlaybackMode()
        self._config.frontPlaylistIndex = self._app.getPlayer().getFrontPlaylistIndex()
        self._logger.info("Save to config.json")
        Path("config.json").write_text(json.dumps(self._config, indent=4, ensure_ascii=False, default=Config.toJson))

    def _loadConfig(self) -> Config:
        self._logger.info("Load config")
        path = Path("config.json")
        if not path.exists():
            self._logger.info("No config.json file, return default config")
            return self.getDefaultConfig()
        jd = json.loads(path.read_text(), object_pairs_hook=Config.fromJson)
        config = Config(**{
            **self.getDefaultConfig().__dict__,
            **{k: v for k, v in jd.items() if k in Config.__annotations__}
        })
        self._logger.info("Process plugin configs (%d plugins)", len(self._pluginService.getPluginClasses()))
        for plugin in config.plugins:
            self._logger.info("Plugin in config: %s", plugin)
            jd = json.loads(
                json.dumps(plugin.config, default=plugin.clazz.getPluginConfigClass().pythonToJson),
                object_pairs_hook=plugin.clazz.getPluginConfigClass().jsonToPython)
            plugin.config = gg(plugin.clazz.getPluginConfigClass())(**jd)
        self._logger.info("Process plugins not in config")
        loadedClasses = [x.clazz for x in config.plugins]
        for clazz in self._pluginService.getPluginClasses():
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
            elementConfig = gg(element.clazz.getWidgetConfigClass())(**{
                **element.clazz.getWidgetConfigClass().getDefaultObject().__dict__,
                **elementConfigJd
            })
            self._logger.info("Loaded element config: %s", elementConfig)
            element.config = elementConfig
        for child in element.children:
            self._loadElementConfig(child)

    @classmethod
    def getDefaultConfig(cls) -> Config:
        screenSize = QtGui.QGuiApplication.primaryScreen().size()
        windowSize = gg(screenSize) / 1.5
        diffSize = (screenSize - windowSize) / 2
        defaultGeometry = QtCore.QRect(QtCore.QPoint(diffSize.width(), diffSize.height()), windowSize)
        from IceSpringMusicPlayer.app import App
        plugins = []
        for clazz in App.instance().getPluginService().getPluginClasses():
            plugins.append(Plugin(
                clazz=clazz,
                disabled=False,
                config=clazz.getPluginConfigClass().getDefaultObject()
            ))
        return Config(
            language="en_US",
            geometry=defaultGeometry,
            iconSize=48,
            applicationFont=QtWidgets.QApplication.font(),
            lyricFont=QtWidgets.QApplication.font(),
            volume=50,
            playbackMode=PlaybackMode.LOOP,
            frontPlaylistIndex=-1,
            layout=cls.getDefaultLayout(),
            plugins=plugins,
            playlists=Vector()
        )

    @staticmethod
    def getDefaultLayout() -> Element:
        from IceSpringPlaylistPlugin.playlistWidget import PlaylistWidget
        from IceSpringLyricsPlugin.lyricsWidget import LyricsWidget
        from IceSpringSpectrumPlugin.spectrumWidget import SpectrumWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        return Element(clazz=SplitterWidget, vertical=False, weight=1, config=dict(), children=[
            Element(clazz=SplitterWidget, vertical=True, weight=2, config=dict(), children=[
                Element(clazz=PlaylistWidget, vertical=False, weight=3, config=dict(), children=[]),
                Element(clazz=SpectrumWidget, vertical=False, weight=1, config=dict(), children=[]),
            ]),
            Element(clazz=LyricsWidget, vertical=False, weight=3, config=dict(), children=[]),
        ])
