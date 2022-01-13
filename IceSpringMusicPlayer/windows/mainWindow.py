# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37

from __future__ import annotations

import logging
import typing
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.services.config import Config
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
from IceSpringMusicPlayer.windows.playlistManagerDialog import PlaylistManagerDialog


class MainWindow(QtWidgets.QMainWindow):
    _config: Config
    _player: Player
    _playlistTable: PlaylistTable
    _statusLabel: QtWidgets.QLabel
    _playlistCombo: QtWidgets.QComboBox

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("mainWindow")
        self._positionLogger = logging.getLogger("position")
        self._positionLogger.setLevel(logging.INFO)
        self._config = App.instance().getConfig()
        self._player = App.instance().getPlayer()
        self._initPlayer()
        self._initMenu()
        self._initToolbar()
        self._initLayout()
        self._initStatusBar()

    def _initPlayer(self):
        self._player.frontPlaylistIndexChanged.connect(self._onFrontPlaylistChangedAtIndex)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        self._player.playlistInserted.connect(self._onPlaylistInserted)
        self._player.currentMusicIndexChanged.connect(self._onMusicIndexChanged)

    def _initStatusBar(self):
        statusLabel = QtWidgets.QLabel("", self.statusBar())
        statusLabel.setStyleSheet("margin: 0 15px")
        self.statusBar().addPermanentWidget(statusLabel)
        self.statusBar().showMessage("Ready.")
        self.statusBar().installEventFilter(self)
        self._statusLabel = statusLabel

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.statusBar() and event.type() == QtCore.QEvent.MouseButtonDblClick:
            self._onStatusBarDoubleClicked()
        return super().eventFilter(watched, event)

    def _onStatusBarDoubleClicked(self):
        self._logger.info("On status bar double clocked")
        if not self._player.getCurrentMusic().isPresent():
            return
        currentMusicIndex = self._player.getCurrentMusicIndex()
        self._player.setFrontPlaylistIndex(self._player.getCurrentPlaylistIndex())
        self._playlistTable.selectRow(currentMusicIndex)
        self._playlistTable.scrollToRowAtCenter(currentMusicIndex)

    def _initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self._onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager", lambda: PlaylistManagerDialog(self).show())

    def _onPlaylistComboActivated(self, index: int) -> None:
        self._logger.info("On playlist combo activated at index %d", index)
        self._player.setFrontPlaylistIndex(index)

    def _onFrontPlaylistChangedAtIndex(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("On front playlist changed at index: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("Front playlist set to index -1, skip")
        else:
            self._logger.info("Front playlist set to index %d, refreshing main window", newIndex)
            self._logger.info("Updating playlist combo")
            self._playlistCombo.setCurrentIndex(newIndex)
            self._logger.info("Main window refreshed")

    def _onOpenActionTriggered(self):
        self._logger.info("On open action triggered")
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self._logger.info("There are %d files to open", len(filenames))
        self._addMusicsByFilenames(filenames)

    def _onOneKeyAddActionTriggered(self):
        self._logger.info("On one key add action triggered")
        paths = Path("~/Music").expanduser().glob("**/*.mp3")
        self._addMusicsByFilenames([str(x) for x in paths])

    def _addMusicsByFilenames(self, filenames: typing.List[str]):
        self._logger.info(">> Add musics with count %d", len(filenames))
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        if not musics:
            self._logger.info("No music file to open, return")
            return
        self._logger.info("Inserting musics...")
        self._player.insertMusics(musics)
        self._logger.info("Musics inserted.")
        self._logger.info("<< Musics added")

    def _initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        playlistCombo.activated.connect(self._onPlaylistComboActivated)
        toolbar.addWidget(QtWidgets.QLabel("Playlist: ", toolbar))
        toolbar.addWidget(playlistCombo)
        self._playlistCombo = playlistCombo

    def _initLayout(self):
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setAutoFillBackground(True)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))
        mainWidget.setPalette(palette)
        self.setCentralWidget(mainWidget)
        lines = [QtWidgets.QFrame(self) for _ in range(2)]
        for line in lines:
            line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
            line.setStyleSheet("color: #D8D8D8")
        mainWidget = self.centralWidget()
        mainLayout = QtWidgets.QVBoxLayout(mainWidget)
        mainLayout.setSpacing(0)
        mainLayout.setMargin(0)
        mainWidget.setLayout(mainLayout)
        mainSplitter = QtWidgets.QSplitter(mainWidget)
        mainLayout.addWidget(lines[0])
        mainLayout.addWidget(mainSplitter, 1)
        mainLayout.addWidget(lines[1])
        mainLayout.addWidget(ControlsPanel(self))
        playlistTable = PlaylistTable(mainSplitter)
        playlistTable.actionAddTriggered.connect(self._onOpenActionTriggered)
        playlistTable.actionOneKeyAddTriggered.connect(self._onOneKeyAddActionTriggered)
        lyricsPanel = LyricsPanel(mainSplitter)
        mainSplitter.addWidget(playlistTable)
        mainSplitter.addWidget(lyricsPanel)
        mainSplitter.setSizes([2 ** 31 - 1, 2 ** 31 - 1])
        self._playlistTable = playlistTable

    def _onPlaylistInserted(self, index: int) -> None:
        playlist = self._player.getPlaylists()[index]
        self._logger.info("On playlist inserted: %s", playlist.name)
        self._playlistCombo.addItem(playlist.name)

    def _onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        self._logger.info("On playlist removed: %s", indexes)
        for index in sorted(indexes, reverse=True):
            self._playlistCombo.removeItem(index)

    def _onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("Music index changed: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("Music index set to -1, player stopped.")
            self._logger.info("Clear status label")
            self._statusLabel.setText("")
            self._logger.info("Notify stopped on status bar")
            self.statusBar().showMessage("Stopped.")
        currentMusic = self._player.getCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        self._logger.info("Current music: %s", currentMusic)
        self._logger.info("Update window title")
        self.setWindowTitle(Path(currentMusic.filename).with_suffix("").name)
        self._logger.info("Update status label")
        self._statusLabel.setText("{} - {}".format(currentMusic.artist, currentMusic.title))

    def _onPlayerPositionChanged(self, position):
        self._positionLogger.debug("Player position changed: %d / %d", position, self._player.getDuration())
        if self._player.getState().isStopped():
            self._logger.info("Player has been stopped, skip")
            return
        duration = self._player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        currentMusic = self._player.getCurrentMusic().orElseThrow(AssertionError)
        self._positionLogger.debug("Update status bar")
        self.statusBar().showMessage("{} | {} kbps | {} Hz | {} channels | {}".format(
            currentMusic.format, currentMusic.bitrate,
            currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
