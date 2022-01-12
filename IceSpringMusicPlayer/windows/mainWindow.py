# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37

from __future__ import annotations

import logging
import typing
from pathlib import Path

import qtawesome
from IceSpringRealOptional.maybe import Maybe
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
from IceSpringMusicPlayer.windows.playlistManagerDialog import PlaylistManagerDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.app import App


class MainWindow(QtWidgets.QMainWindow):
    toolbar: QtWidgets.QToolBar
    mainWidget: QtWidgets.QWidget
    mainSplitter: QtWidgets.QSplitter
    controlsLayout: QtWidgets.QHBoxLayout
    playlistTable: PlaylistTable
    playButton: QtWidgets.QToolButton
    playbackButton: QtWidgets.QToolButton
    progressSlider: QtWidgets.QSlider
    progressLabel: QtWidgets.QLabel
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
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.durationChanged.connect(self.onPlayerDurationChanged)
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
        if isinstance(watched.parent(), QtWidgets.QTableView):
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                assert isinstance(event, QtGui.QMouseEvent)
                if event.button() == QtCore.Qt.RightButton:
                    self.logger.debug("Ignore double click event on playlist table")
                    return True
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
        self.initControlsLayout()

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
        controlsLayout = QtWidgets.QHBoxLayout(mainWidget)
        controlsLayout.setSpacing(5)
        mainLayout.addWidget(lines[0])
        mainLayout.addWidget(mainSplitter, 1)
        mainLayout.addWidget(lines[1])
        mainLayout.addLayout(controlsLayout)
        self.mainWidget = mainWidget
        self.mainSplitter = mainSplitter
        self.controlsLayout = controlsLayout

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

    def initControlsLayout(self):
        mainWidget = self.mainWidget
        controlsLayout = self.controlsLayout
        playButton = QtWidgets.QToolButton(mainWidget)
        playButton.setIcon(qtawesome.icon("mdi.play"))
        playButton.clicked.connect(self.onPlayButtonClicked)
        stopButton = QtWidgets.QToolButton(mainWidget)
        stopButton.setIcon(qtawesome.icon("mdi.stop"))
        stopButton.clicked.connect(self.onStopButtonClicked)
        previousButton = QtWidgets.QToolButton(mainWidget)
        previousButton.setIcon(qtawesome.icon("mdi.step-backward"))
        previousButton.clicked.connect(self.onPlayPreviousButtonClicked)
        nextButton = QtWidgets.QToolButton(mainWidget)
        nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
        nextButton.clicked.connect(self.onPlayNextButtonClicked)
        playbackButton = QtWidgets.QToolButton(mainWidget)
        playbackButton.setIcon(qtawesome.icon("mdi.repeat"))
        playbackButton.clicked.connect(self.togglePlaybackMode)
        iconSize = QtCore.QSize(48, 48) * self.app.zoom
        for button in playButton, stopButton, previousButton, nextButton, playbackButton:
            button.setIconSize(iconSize)
            button.setAutoRaise(True)
        progressSlider = FluentSlider(QtCore.Qt.Orientation.Horizontal, mainWidget)
        progressSlider.setDisabled(True)
        progressSlider.valueChanged.connect(self.onProgressSliderValueChanged)
        progressLabel = QtWidgets.QLabel("00:00/00:00", mainWidget)
        volumeDial = QtWidgets.QDial(mainWidget)
        volumeDial.setFixedSize(iconSize)
        volumeDial.setValue(50)
        volumeDial.valueChanged.connect(self.player.setVolume)
        controlsLayout.addWidget(playButton)
        controlsLayout.addWidget(stopButton)
        controlsLayout.addWidget(previousButton)
        controlsLayout.addWidget(nextButton)
        controlsLayout.addWidget(progressSlider)
        controlsLayout.addWidget(progressLabel)
        controlsLayout.addWidget(playbackButton)
        controlsLayout.addWidget(volumeDial)
        self.playButton = playButton
        self.playbackButton = playbackButton
        self.progressSlider = progressSlider
        self.progressLabel = progressLabel

    def onProgressSliderValueChanged(self, value: int) -> None:
        self.logger.info("On progress slider value changed: %d", value)
        self.player.setPosition(value)

    def onPlaylistAdded(self, playlist: Playlist) -> None:
        self.logger.info("On playlist added: %s", playlist.name)
        self.playlistCombo.addItem(playlist.name)

    def onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        self.logger.info("On playlist removed: %s", indexes)
        for index in sorted(indexes, reverse=True):
            self.playlistCombo.removeItem(index)

    def togglePlaybackMode(self):
        self.player.setPlaybackMode(self.player.getPlaybackMode().next())
        newPlaybackMode = self.player.getPlaybackMode()
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode.name]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayNextButtonClicked(self) -> None:
        self.logger.info("On play next button clicked")
        self.player.playNext()

    def onPlayPreviousButtonClicked(self) -> None:
        self.logger.info("On play previous button clicked")
        self.player.playPrevious()

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        selectedMaybe: Maybe[int] = self.playlistTable.fetchFirstSelectedRow()
        if self.player.getState().isPlaying():
            logging.info("Player is playing, pause it")
            self.player.pause()
        elif self.player.getState().isPaused():
            logging.info("Player is paused, play it")
            self.player.play()
        elif selectedMaybe.isPresent():
            self.logger.info("Play selected music")
            self.player.playMusicAtIndex(selectedMaybe.get())
        else:
            self.logger.info("Play next music")
            self.player.playNext()

    def onStopButtonClicked(self):
        self.logger.info("On stop button clicked")
        if self.player.getState().isStopped():
            self.logger.info("Already stopped")
        else:
            self.logger.info("Stop playing")
            self.player.stop()

    def onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self.logger.info("Music index changed: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self.logger.info("Music index set to -1, player stopped.")
            self.logger.info("Clear status label")
            self.statusLabel.setText("")
            self.logger.info("Notify stopped on status bar")
            self.statusBar().showMessage("Stopped.")
            self.logger.info("Disable progress slider")
            self.progressSlider.setDisabled(True)
            self.logger.info("Reset progress label")
            self.progressLabel.setText("00:00/00:00")
        if oldIndex == -1 and newIndex != -1:
            self.logger.info("Player resumed from stopped state.")
            self.logger.info("Enable progress slider")
            self.progressSlider.setDisabled(False)
        currentMusic = self.player.getCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        self.logger.info("Current music: %s", currentMusic)
        self.logger.info("Update window title")
        self.setWindowTitle(Path(currentMusic.filename).with_suffix("").name)
        self.logger.info("Update status label")
        self.statusLabel.setText("{} - {}".format(currentMusic.artist, currentMusic.title))

    def onPlayerDurationChanged(self, duration: int) -> None:
        self.logger.info("Player duration changed: %d", duration)
        self.logger.info("Update progress slider max value")
        self.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Player position changed: %d / %d", position, self.player.getDuration())
        if self.player.getState().isStopped():
            self.logger.info("Player has been stopped, skip")
            return
        self.progressSlider.blockSignals(True)
        self.progressSlider.setValue(position)
        self.progressSlider.blockSignals(False)
        duration = self.player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        self.positionLogger.debug("Update progress label")
        self.progressLabel.setText(progressText)
        currentMusic = self.player.getCurrentMusic().orElseThrow(AssertionError)
        self.positionLogger.debug("Update status bar")
        self.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(currentMusic.format, currentMusic.bitrate,
                currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))

    def onPlayerStateChanged(self, state: PlayerState):
        self.logger.info("Player state changed: %s ", state)
        self.logger.info("Update play button icon")
        self.playButton.setIcon(qtawesome.icon("mdi.pause" if state.isPlaying() else "mdi.play"))
