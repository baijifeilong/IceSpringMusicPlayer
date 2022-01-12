# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37

from __future__ import annotations

import logging
import typing
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
from IceSpringMusicPlayer.windows.playlistManagerDialog import PlaylistManagerDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.app import App


class MainWindow(QtWidgets.QMainWindow):
    toolbar: QtWidgets.QToolBar
    mainWidget: QtWidgets.QWidget
    mainSplitter: QtWidgets.QSplitter
    playlistTable: PlaylistTable
    statusLabel: QtWidgets.QLabel
    playlistCombo: QtWidgets.QComboBox
    playlistsDialog: PlaylistManagerDialog
    player: Player

    def __init__(self, app: App, player: Player):
        super().__init__()
        self.logger = logging.getLogger("mainWindow")
        self.app = app
        self.lyricsLogger = logging.getLogger("lyrics")
        self.lyricsLogger.setLevel(logging.INFO)
        self.positionLogger = logging.getLogger("position")
        self.positionLogger.setLevel(logging.INFO)
        self.player = player
        self.initMenu()
        self.initToolbar()
        self.initLayout()
        self.initStatusBar()
        playlistsDialog = PlaylistManagerDialog(self.player.getPlaylists(), self)
        playlistsDialog.playlistManagerTable.model().playlistsRemoved.connect(self.onPlaylistsRemovedAtIndexes)
        self.playlistsDialog = playlistsDialog
        self.setupPlayer()

    def setupPlayer(self):
        player = self.player
        player.positionChanged.connect(self.onPlayerPositionChanged)
        player.playlistAdded.connect(self.onPlaylistAdded)
        player.currentMusicIndexChanged.connect(self.onMusicIndexChanged)

    def initStatusBar(self):
        statusLabel = QtWidgets.QLabel("", self.statusBar())
        statusLabel.setStyleSheet("margin: 0 15px")
        self.statusBar().addPermanentWidget(statusLabel)
        self.statusBar().showMessage("Ready.")
        self.statusBar().installEventFilter(self)
        self.statusLabel = statusLabel

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.statusBar() and event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.onStatusBarDoubleClicked()
        return super().eventFilter(watched, event)

    def onStatusBarDoubleClicked(self):
        self.logger.info("On status bar double clocked")
        if not self.player.getCurrentMusic().isPresent():
            return
        currentMusicIndex = self.player.getCurrentMusicIndex()
        self.player.setFrontPlaylistIndex(self.player.getCurrentPlaylistIndex())
        self.playlistTable.selectRow(currentMusicIndex)
        self.playlistTable.scrollToRowAtCenter(currentMusicIndex)

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self.onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager",
            lambda: PlaylistManagerDialog(self.player.getPlaylists(), self).show())

    def onPlaylistComboActivated(self, index: int) -> None:
        self.logger.info("On playlist combo activated at index %d", index)
        self.player.setFrontPlaylistIndex(index)

    def onFrontPlaylistChangedAtIndex(self, oldIndex: int, newIndex: int) -> None:
        self.logger.info("On front playlist changed at index: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self.logger.info("Front playlist set to index -1, skip")
        else:
            self.logger.info("Front playlist set to index %d, refreshing main window", newIndex)
            self.logger.info("Updating playlist combo")
            self.playlistCombo.setCurrentIndex(newIndex)
            self.logger.info("Main window refreshed")

    def createAndAppendDefaultPlaylist(self):
        self.player.insertPlaylist(Playlist("Playlist 1"))

    def onOpenActionTriggered(self):
        self.logger.info("On open action triggered")
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self.logger.info("There are %d files to open", len(filenames))
        self.addMusicsByFilenames(filenames)

    def onOneKeyAddActionTriggered(self):
        self.logger.info("On one key add action triggered")
        paths = Path("~/Music").expanduser().glob("**/*.mp3")
        self.addMusicsByFilenames([str(x) for x in paths])

    def addMusicsByFilenames(self, filenames: typing.List[str]):
        self.logger.info(">> Add musics with count %d", len(filenames))
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        if not musics:
            self.logger.info("No music file to open, return")
            return
        self.logger.info("Inserting musics...")
        self.player.insertMusics(musics)
        self.logger.info("Musics inserted.")
        self.logger.info("<< Musics added")

    def initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        playlistCombo.activated.connect(self.onPlaylistComboActivated)
        toolbar.addWidget(QtWidgets.QLabel("Playlist: ", toolbar))
        toolbar.addWidget(playlistCombo)
        self.toolbar = toolbar
        self.playlistCombo = playlistCombo

    def initLayout(self):
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setAutoFillBackground(True)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))
        mainWidget.setPalette(palette)
        self.setCentralWidget(mainWidget)
        self.initMainLayout()
        self.initMainSplitter()

    def initMainLayout(self):
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
        mainLayout.addWidget(ControlsPanel(self.player, self, self.app.zoom))
        self.mainWidget = mainWidget
        self.mainSplitter = mainSplitter

    def initMainSplitter(self):
        mainSplitter = self.mainSplitter
        playlistTable = PlaylistTable(self.player, self)
        playlistTable.actionAddTriggered.connect(self.onOpenActionTriggered)
        playlistTable.actionOneKeyAddTriggered.connect(self.onOneKeyAddActionTriggered)
        lyricsPanel = LyricsPanel(self.player, self, self.app.zoom)
        mainSplitter.addWidget(playlistTable)
        mainSplitter.addWidget(lyricsPanel)
        mainSplitter.setSizes([2 ** 31 - 1, 2 ** 31 - 1])
        self.playlistTable = playlistTable

    def onPlaylistAdded(self, playlist: Playlist) -> None:
        self.logger.info("On playlist added: %s", playlist.name)
        self.playlistCombo.addItem(playlist.name)

    def onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        self.logger.info("On playlist removed: %s", indexes)
        for index in sorted(indexes, reverse=True):
            self.playlistCombo.removeItem(index)

    def onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self.logger.info("Music index changed: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self.logger.info("Music index set to -1, player stopped.")
            self.logger.info("Clear status label")
            self.statusLabel.setText("")
            self.logger.info("Notify stopped on status bar")
            self.statusBar().showMessage("Stopped.")
        currentMusic = self.player.getCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        self.logger.info("Current music: %s", currentMusic)
        self.logger.info("Update window title")
        self.setWindowTitle(Path(currentMusic.filename).with_suffix("").name)
        self.logger.info("Update status label")
        self.statusLabel.setText("{} - {}".format(currentMusic.artist, currentMusic.title))

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Player position changed: %d / %d", position, self.player.getDuration())
        if self.player.getState().isStopped():
            self.logger.info("Player has been stopped, skip")
            return
        duration = self.player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        currentMusic = self.player.getCurrentMusic().orElseThrow(AssertionError)
        self.positionLogger.debug("Update status bar")
        self.statusBar().showMessage("{} | {} kbps | {} Hz | {} channels | {}".format(
            currentMusic.format, currentMusic.bitrate,
            currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
