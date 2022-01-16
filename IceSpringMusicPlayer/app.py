# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import importlib
import json
import logging
import typing

import pydash
from IceSpringPathLib import Path
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.vector import Vector
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.widgets.replacerMixin import BlankWidget

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    requestLocateCurrentMusic: QtCore.SignalInstance = QtCore.Signal()
    configChanged: QtCore.SignalInstance = QtCore.Signal()

    _logger: logging.Logger
    _config: Config
    _player: Player
    _mainWindow: MainWindow

    def __init__(self):
        from IceSpringMusicPlayer.services.player import Player
        from IceSpringMusicPlayer.windows.mainWindow import MainWindow
        super().__init__()
        self._logger = logging.getLogger("app")
        self._config = self._loadConfig()
        self._player = Player(self)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self._mainWindow = MainWindow()
        self.aboutToQuit.connect(self._onAboutToQuit)
        self.configChanged.connect(self._onConfigChanged)

    def _onConfigChanged(self):
        self._logger.info("On config changed")
        self.setFont(Just.of(self.font()).apply(lambda x: x.setPointSize(self._config.fontSize)).value())

    def _onAboutToQuit(self):
        self._logger.info("On about to quit")
        self._persistConfig()

    def exec_(self) -> int:
        self._logger.info("Exec")
        self.setFont(Just.of(self.font()).apply(lambda x: x.setPointSize(self._config.fontSize)).value())
        self._mainWindow.setGeometry(self._config.geometry)
        self._mainWindow.show()
        return super().exec_()

    def getConfig(self) -> Config:
        return self._config

    def getPlayer(self) -> Player:
        return self._player

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
        self._logger.info("Persist")
        Path("config.json").write_text(json.dumps(self._config, indent=4, ensure_ascii=False, default=Config.toJson))

    def _parseLayout(self, jd: dict) -> Element:
        module, clazz = jd["clazz"].rsplit(".", maxsplit=1)
        return Element(
            clazz=getattr(importlib.import_module(module), clazz),
            weight=jd["weight"],
            children=[self._parseLayout(x) for x in jd["children"]]
        )

    def _loadConfig(self) -> Config:
        self._logger.info("Load config")
        jd = json.loads(Path("config.json").read_text()) if Path("config.json").exists() else dict()
        self._logger.info("Config json: %s", pydash.truncate(json.dumps(jd, ensure_ascii=False)))
        screenSize = QtGui.QGuiApplication.primaryScreen().size()
        windowSize = screenSize / 1.5
        diffSize = (screenSize - windowSize) / 2
        defaultGeometry = QtCore.QRect(QtCore.QPoint(diffSize.width(), diffSize.height()), windowSize)
        config = Config(
            zoom=-1,
            geometry=QtCore.QRect(*jd.get("geometry")) if "geometry" in jd else defaultGeometry,
            fontSize=jd.get("fontSize", QtWidgets.QApplication.font().pointSize()),
            iconSize=jd.get("iconSize", 48),
            lyricSize=jd.get("lyricSize", 16),
            layout=self._parseLayout(jd["layout"]) if "layout" in jd else self.getDefaultLayout(),
            frontPlaylistIndex=-1,
            playlists=Vector(Playlist(
                name=playlistJd["name"],
                musics=Vector(Music(**musicJd) for musicJd in playlistJd["musics"])
            ) for playlistJd in jd.get("playlists", [])),
        )
        config.zoom = config.fontSize / QtWidgets.QApplication.font().pointSize()
        config.frontPlaylistIndex = jd.get("frontPlaylistIndex", -1 if len(config.playlists) == 0 else 0)
        config.layout = self.getDemoLayout()
        self._logger.info("Loaded config: %s", config)
        return config

    @staticmethod
    def getDefaultLayout() -> Element:
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        from IceSpringMusicPlayer.widgets.replacerMixin import HorizontalSplitter, VerticalSplitter
        return Element(clazz=HorizontalSplitter, weight=1, children=[
            Element(clazz=VerticalSplitter, weight=1, children=[
                Element(clazz=ControlsPanel, weight=1, children=[]),
                Element(clazz=LyricsPanel, weight=3, children=[]),
                Element(clazz=PlaylistTable, weight=5, children=[]),
            ]),
            Element(clazz=VerticalSplitter, weight=2, children=[
                Element(clazz=PlaylistTable, weight=3, children=[]),
                Element(clazz=LyricsPanel, weight=5, children=[]),
                Element(clazz=ControlsPanel, weight=1, children=[]),
            ]),
        ])

    @staticmethod
    def getDemoLayout() -> Element:
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        from IceSpringMusicPlayer.widgets.replacerMixin import HorizontalSplitter, VerticalSplitter
        from IceSpringMusicPlayer.widgets.configWidget import ConfigWidget
        return Element(clazz=HorizontalSplitter, weight=1, children=[
            Element(clazz=VerticalSplitter, weight=1, children=[
                Element(clazz=ControlsPanel, weight=1, children=[]),
                Element(clazz=LyricsPanel, weight=3, children=[]),
                Element(clazz=PlaylistTable, weight=5, children=[]),
            ]),
            Element(clazz=VerticalSplitter, weight=1, children=[
                Element(clazz=ConfigWidget, weight=1, children=[]),
                Element(clazz=BlankWidget, weight=3, children=[]),
            ]),
        ])
