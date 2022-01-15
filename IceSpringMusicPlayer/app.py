# Created by BaiJiFeiLong@gmail.com at 2022-01-03 10:59:13

from __future__ import annotations

import logging
import typing

from IceSpringPathLib import Path
from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.utils.musicUtils import MusicUtils

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.services.config import Config
    from IceSpringMusicPlayer.services.player import Player
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class App(QtWidgets.QApplication):
    requestLocateCurrentMusic: QtCore.SignalInstance = QtCore.Signal()

    _logger: logging.Logger
    _config: Config
    _zoom: float
    _player: Player
    _mainWindow: MainWindow

    def __init__(self):
        from IceSpringMusicPlayer.services.config import Config
        from IceSpringMusicPlayer.services.player import Player
        from IceSpringMusicPlayer.windows.mainWindow import MainWindow
        super().__init__()
        self._logger = logging.getLogger("app")
        self._config = Config()
        self._zoom = 1.0
        self._player = Player(self)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self._mainWindow = MainWindow()

    def exec_(self) -> int:
        fontsize = self.getConfig().getFontSize()
        geometry = self.getConfig().getGeometry()
        self._logger.info("Fontsize: %s", fontsize)
        self._logger.info("Geometry: %s", geometry)
        if fontsize.isPresent():
            self._zoom = fontsize.get() / self.font().pointSize()
            self.setFont(Just.of(self.font()).apply(lambda x: x.setPointSize(fontsize.get())).value())
        self._logger.info("Zoom: %f", self._zoom)
        if geometry.isPresent():
            self._mainWindow.setGeometry(geometry.get())
        else:
            self._mainWindow.resize(1280, 720)
        self._mainWindow.show()
        return super().exec_()

    def getConfig(self) -> Config:
        return self._config

    def getZoom(self) -> float:
        return self._zoom

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
