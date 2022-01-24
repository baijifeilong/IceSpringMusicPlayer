# Created by BaiJiFeiLong@gmail.com at 2022/1/23 19:45
import logging
import typing

from IceSpringPathLib import Path
from PySide2 import QtCore, QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils


class PlaylistService(QtCore.QObject):
    musicParsed: QtCore.SignalInstance = QtCore.Signal(int, int, Music)

    def __init__(self, parent: QtCore.QObject = None):
        super().__init__(parent)
        self._logger = logging.getLogger("playlistService")
        self._player = App.instance().getPlayer()

    def addMusicsFromFolderDialog(self):
        self._logger.info("Add musics from folder dialog")
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.addMusicsFromFolder(folder)

    def addMusicsFromFolder(self, folder: str) -> None:
        self._logger.info("Add musics from folder: %s", folder)
        paths = Path(folder).expanduser().glob("**/*.mp3")
        filenames = [str(x) for x in paths]
        self.addMusicsFromFilenames(filenames)

    def addMusicsFromFileDialog(self):
        self._logger.info("Add musics from file dialog")
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self._logger.info("There are %d files to open", len(filenames))
        self.addMusicsFromFilenames(filenames)

    def addMusicsFromFilenames(self, filenames: typing.List[str]) -> None:
        self._logger.info("Add musics from filenames: %d", len(filenames))
        if len(filenames) == 0:
            self._logger.info("No musics to add, return")
            return
        musics = []
        for index, filename in enumerate(filenames):
            music = MusicUtils.parseMusic(filename)
            musics.append(music)
            self.musicParsed.emit(index + 1, len(filenames), music)
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
