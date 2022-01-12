# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37

from __future__ import annotations

import logging
import typing
from pathlib import Path

import qtawesome
from IceSpringMusicPlayer.windows.playlistsDialog import PlaylistManagerDialog
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.clickableLabel import ClickableLabel
from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringMusicPlayer.utils.lyricUtils import LyricUtils
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.utils.timeDeltaUtils import TimeDeltaUtils
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
from IceSpringMusicPlayer.windows.playlistManagerDialog import PlaylistManagerDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.app import App


class MainWindow(QtWidgets.QMainWindow):
    toolbar: QtWidgets.QToolBar
    mainWidget: QtWidgets.QWidget
    mainSplitter: QtWidgets.QSplitter
    controlsLayout: QtWidgets.QHBoxLayout
    playlistWidget: QtWidgets.QStackedWidget
    lyricsContainer: QtWidgets.QScrollArea
    lyricsLayout: QtWidgets.QVBoxLayout
    playButton: QtWidgets.QToolButton
    playbackButton: QtWidgets.QToolButton
    progressSlider: QtWidgets.QSlider
    progressLabel: QtWidgets.QLabel
    statusLabel: QtWidgets.QLabel
    playlistCombo: QtWidgets.QComboBox
    playlistsDialog: PlaylistManagerDialog
    _frontPlaylistIndex: int
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
        self.insertPlaceholderTableIfNecessary()
        playlistsDialog = PlaylistManagerDialog(self.player.fetchAllPlaylists(), self)
        playlistsDialog.playlistManagerTable.model().playlistsRemoved.connect(self.onPlaylistsRemovedAtIndexes)
        self.playlistsDialog = playlistsDialog
        self._frontPlaylistIndex = -1
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
        if not self.player.fetchCurrentMusic().isPresent():
            return
        currentPlaylistIndex = self.player.fetchCurrentPlaylistIndex()
        currentMusicIndex = self.player.fetchCurrentMusicIndex()
        currentPlaylistTable = self.fetchCurrentPlaylistTable().orElseThrow(AssertionError)
        self.playlistWidget.setCurrentIndex(currentPlaylistIndex)
        currentPlaylistTable.selectRow(currentMusicIndex)
        currentPlaylistTable.scrollToRowAtCenter(currentMusicIndex)

    def fetchCurrentPlaylistTable(self) -> Maybe[PlaylistTable]:
        if not self.player.fetchCurrentPlaylist().isPresent():
            return Maybe.empty()
        currentPlaylistIndex = self.player.fetchCurrentPlaylistIndex()
        currentPlaylistTable = self.playlistWidget.widget(currentPlaylistIndex)
        return Maybe.of(gg(currentPlaylistTable, _type=PlaylistTable))

    def fetchFrontPlaylistTable(self) -> Maybe[PlaylistTable]:
        if self._frontPlaylistIndex < 0:
            return Maybe.empty()
        frontPlaylistTable = self.playlistWidget.widget(self._frontPlaylistIndex)
        return Maybe.of(gg(frontPlaylistTable, _type=PlaylistTable))

    def fetchFrontPlaylistIndex(self) -> int:
        return self._frontPlaylistIndex

    def fetchFrontPlaylist(self) -> Maybe[Playlist]:
        if self._frontPlaylistIndex < 0:
            return Maybe.empty()
        return Maybe.of(self.player.fetchAllPlaylists()[self._frontPlaylistIndex])

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self.onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager",
            lambda: PlaylistManagerDialog(self.player.fetchAllPlaylists(), self).show())

    def setFrontPlaylistAtIndex(self, index: int) -> None:
        self.logger.info("Setting front playlist at index %d", index)
        assert index >= 0
        self._frontPlaylistIndex = index
        self.logger.info("Updating playlist combo")
        self.playlistCombo.setCurrentIndex(index)
        self.logger.info("Updating playlist widget")
        self.playlistWidget.setCurrentIndex(index)
        self.logger.info("Front playlist set to index %d", index)

    def onCurrentPlaylistIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        if oldIndex == -1:
            assert newIndex >= 0
            self.setFrontPlaylistAtIndex(newIndex)

    def createAndAppendDefaultPlaylist(self):
        self.logger.info("Create default playlist")
        placeholderPlaylistTable: PlaylistTable = gg(self.playlistWidget.widget(0), _type=PlaylistTable)
        playlist = placeholderPlaylistTable.playlist
        playlist.name = "Playlist 1"
        self.player.addPlaylist(playlist)

    def onOpenActionTriggered(self):
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self.logger.info("There are %d files to open", len(filenames))
        self.addMusicsByFilenames(filenames)

    def addMusicsByFilenames(self, filenames: typing.List[str]):
        self.logger.info(">> Add musics with count %d", len(filenames))
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        if not musics:
            self.logger.info("No music file to open, return")
            return
        if len(self.player.fetchAllPlaylists()) <= 0:
            self.logger.info("No playlist, create one")
            self.createAndAppendDefaultPlaylist()
        playlistTable = self.fetchFrontPlaylistTable().orElseThrow(AssertionError)
        beginRow, endRow = playlistTable.model().insertMusics(musics)
        playlistTable.selectRowRange(beginRow, endRow)
        self.app.miniMode and playlistTable.resizeRowsToContents()
        playlistTable.scrollToRowAtCenter(beginRow)
        self.logger.info("<< Musics added")

    def initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        playlistCombo.activated.connect(self.setFrontPlaylistAtIndex)
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
        playlistWidget = QtWidgets.QStackedWidget(mainSplitter)
        lyricsContainer = QtWidgets.QScrollArea(mainSplitter)
        lyricsWidget = QtWidgets.QWidget(lyricsContainer)
        lyricsLayout = QtWidgets.QVBoxLayout(lyricsWidget)
        lyricsLayout.setMargin(0)
        lyricsLayout.setSpacing(1)
        lyricsWidget.setLayout(lyricsLayout)
        lyricsContainer.setWidget(lyricsWidget)
        lyricsContainer.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        lyricsContainer.setWidgetResizable(True)
        lyricsContainer.resizeEvent = self.onLyricsContainerResize
        lyricsContainer.horizontalScrollBar().rangeChanged.connect(lambda *args, bar=lyricsContainer.
            horizontalScrollBar(): bar.setValue((bar.maximum() + bar.minimum()) // 2))
        mainSplitter.addWidget(playlistWidget)
        mainSplitter.addWidget(lyricsContainer)
        mainSplitter.setSizes([2 ** 31 - 1, 2 ** 31 - 1])
        self.playlistWidget = playlistWidget
        self.lyricsContainer = lyricsContainer
        self.lyricsLayout = lyricsLayout

    def onLyricsContainerResize(self, event):
        if self.lyricsLayout.count() <= 0:
            return
        self.lyricsLayout.itemAt(0).spacerItem().changeSize(0, event.size().height() // 2)
        self.lyricsLayout.itemAt(self.lyricsLayout.count() - 1).spacerItem().changeSize(0, event.size().height() // 2)
        self.lyricsLayout.invalidate()

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

    def insertPlaceholderTableIfNecessary(self):
        self.logger.info("Insert placeholder table if necessary")
        if self.player.fetchAllPlaylists().isEmpty():
            assert self.playlistWidget.count() == 0
            self.logger.info("No playlist now, insert placeholder table")
            self.playlistWidget.addWidget(PlaylistTable(Playlist("Placeholder"), self))

    def removePlaceholderTableIfExists(self) -> None:
        self.logger.info("Remove placeholder table if exists")
        if self.player.fetchAllPlaylists().size() == 1:
            assert self.playlistWidget.count() == 1
            self.logger.info("No playlist before, remove placeholder table")
            self.playlistWidget.removeWidget(self.playlistWidget.widget(0))
            self.logger.info("Placeholder table removed")

    def onPlaylistAdded(self, playlist: Playlist) -> None:
        self.logger.info("On playlist added: %s", playlist.name)
        self.removePlaceholderTableIfExists()
        self.logger.info("Creating playlist table...")
        playlistTable = PlaylistTable(playlist, self)
        playlistTable.model().beforeRemoveMusics.connect(self.player.doBeforeRemoveMusics)
        playlistTable.model().musicsInserted.connect(self.player.onMusicsInserted)
        playlistTable.model().musicsRemoved.connect(self.player.onMusicsRemoved)
        self.logger.info("Playlist table created.")
        self.playlistCombo.addItem(playlist.name)
        self.playlistWidget.addWidget(playlistTable)
        assert self.playlistWidget.count() == self.player.fetchAllPlaylists().size()
        self.logger.info("Playlist table added.")
        if self._frontPlaylistIndex == -1:
            self.logger.info("Front playlist index is -1, setting to 0...")
            self.setFrontPlaylistAtIndex(0)

    def onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        self.logger.info("On playlist removed: %s", indexes)
        for index in sorted(indexes, reverse=True):
            self.playlistWidget.removeWidget(self.playlistWidget.widget(index))
            self.playlistCombo.removeItem(index)
        self.insertPlaceholderTableIfNecessary()

    def togglePlaybackMode(self):
        self.player.setCurrentPlaybackMode(self.player.fetchCurrentPlaybackMode().next())
        newPlaybackMode = self.player.fetchCurrentPlaybackMode()
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode.name]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayNextButtonClicked(self) -> None:
        self.logger.info("On play next button clicked")
        if self.fetchFrontPlaylist().isAbsent():
            self.logger.info("No playlist to play")
        elif self.fetchFrontPlaylist().get().musics.isEmpty():
            self.logger.info("No music to play")
        else:
            self.logger.info("Play next at front playlist")
            self.player.playNextAtPlaylist(self._frontPlaylistIndex)

    def onPlayPreviousButtonClicked(self) -> None:
        self.logger.info("On play previous button clicked")
        if self.fetchFrontPlaylist().isAbsent():
            self.logger.info("No playlist to play")
        elif self.fetchFrontPlaylist().get().musics.isEmpty():
            self.logger.info("No music to play")
        else:
            self.logger.info("Play previous at front playlist")
            self.player.playPreviousAtPlaylist(self._frontPlaylistIndex)

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        selectedMaybe: Maybe[int] = self.fetchFrontPlaylistTable().flatMap(lambda x: x.fetchFirstSelectedRow())
        if self.player.fetchState().isPlaying():
            logging.info("Player is playing, pause it")
            self.player.pause()
        elif self.player.fetchState().isPaused():
            logging.info("Player is paused, play it")
            self.player.play()
        elif self.fetchFrontPlaylist().isAbsent():
            self.logger.info("No playlist to play")
        elif self.fetchFrontPlaylist().get().musics.isEmpty():
            self.logger.info("No music to play")
        elif selectedMaybe.isPresent():
            self.logger.info("Play selected music")
            self.player.playMusicAtPlaylistAndIndex(self._frontPlaylistIndex, selectedMaybe.get())
        else:
            self.logger.info("Play next music")
            self.player.playNextAtPlaylist(self._frontPlaylistIndex)

    def onStopButtonClicked(self):
        self.logger.info("On stop button clicked")
        if self.player.fetchState().isStopped():
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
            self.logger.info("Clear lyrics layout")
            LayoutUtils.clearLayout(self.lyricsLayout)
            return
        if oldIndex == -1 and newIndex != -1:
            self.logger.info("Player resumed from stopped state.")
            self.logger.info("Enable progress slider")
            self.progressSlider.setDisabled(False)
        currentMusic = self.player.fetchCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        self.logger.info("Current music: %s", currentMusic)
        self.logger.info("Update window title")
        self.setWindowTitle(Path(currentMusic.filename).with_suffix("").name)
        self.logger.info("Refresh playlist table")
        currentPlaylistTable = self.fetchCurrentPlaylistTable().orElseThrow(AssertionError)
        currentPlaylistTable.model().notifyDataChangedAtRow(oldIndex)
        currentPlaylistTable.model().notifyDataChangedAtRow(newIndex)
        self.logger.info("Select played item in playlist table")
        currentPlaylistTable.selectRow(newIndex)
        self.logger.info("Setup lyrics")
        self.setupLyrics()
        self.logger.info("Update status label")
        self.statusLabel.setText("{} - {}".format(currentMusic.artist, currentMusic.title))

    def onPlayerDurationChanged(self, duration: int) -> None:
        self.logger.info("Player duration changed: %d", duration)
        self.logger.info("Update progress slider max value")
        self.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Player position changed: %d / %d", position, self.player.fetchDuration())
        if self.player.fetchState().isStopped():
            self.logger.info("Player has been stopped, skip")
            return
        self.progressSlider.blockSignals(True)
        self.progressSlider.setValue(position)
        self.progressSlider.blockSignals(False)
        duration = self.player.fetchDuration()
        progressText = f"{TimeDeltaUtils.formatDelta(position)}/{TimeDeltaUtils.formatDelta(duration)}"
        self.positionLogger.debug("Update progress label")
        self.progressLabel.setText(progressText)
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        self.positionLogger.debug("Update status bar")
        self.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(currentMusic.format, currentMusic.bitrate,
                currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
        self.positionLogger.debug("Position not zero, try to refresh lyrics")
        self.refreshLyrics(position + 2)  # 1 milli for bug rate, 1 milli for double language lyrics

    def onPlayerStateChanged(self, state: PlayerState):
        self.logger.info("Player state changed: %s ", state)
        self.logger.info("Update play button icon")
        self.playButton.setIcon(qtawesome.icon("mdi.pause" if state.isPlaying() else "mdi.play"))
        self.logger.info("Update playlist table icon")
        self.fetchCurrentPlaylistTable().orElseThrow(AssertionError).model().notifyDataChangedAtRow(
            self.player.fetchCurrentMusicIndex())

    def setupLyrics(self):
        self.lyricsLogger.info(">> Setting up lyrics...")
        self.player.setProperty("previousLyricIndex", -1)
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        lyricsPath = Path(currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text()
        self.lyricsLogger.info("Parsing lyrics")
        lyricDict = LyricUtils.parseLyrics(lyricsText)
        self.lyricsLogger.info("Lyrics count: %d", len(lyricDict))
        self.player.setProperty("lyricDict", lyricDict)
        LayoutUtils.clearLayout(self.lyricsLayout)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self.lyricsContainer)
            lyricLabel.setAlignment(
                gg(QtCore.Qt.AlignmentFlag.AlignCenter, typing.Any) | QtCore.Qt.AlignmentFlag.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, position=position: self.player.setPosition(position))
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize((12 if self.app.miniMode else 16) * self.app.zoom)
            lyricLabel.setFont(font)
            lyricLabel.setMargin(int(2 * self.app.zoom))
            self.lyricsLayout.addWidget(lyricLabel)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        self.lyricsLogger.info("Lyrics layout has children: %d", self.lyricsLayout.count())
        self.lyricsContainer.verticalScrollBar().setValue(0)
        self.lyricsLogger.info("<< Lyrics set up")

    def refreshLyrics(self, position):
        self.lyricsLogger.debug("Refreshing lyrics at position: %d", position)
        lyricDict = self.player.property("lyricDict")
        previousLyricIndex = self.player.property("previousLyricIndex")
        lyricIndex = LyricUtils.calcLyricIndexAtPosition(position, list(lyricDict.keys()))
        self.lyricsLogger.debug("Lyric index: %d => %d", previousLyricIndex, lyricIndex)
        if lyricIndex == previousLyricIndex:
            self.lyricsLogger.debug("Lyric index no changed, skip refresh")
            return
        else:
            self.lyricsLogger.debug("Lyric index changed: %d => %d, refreshing...", previousLyricIndex, lyricIndex)
        self.player.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyricDict)):
            lyricLabel: QtWidgets.QLabel = self.lyricsLayout.itemAt(index + 1).widget()
            lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
            originalValue = self.lyricsContainer.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.lyricsContainer.height() // 2 + lyricLabel.height() // 2
            # noinspection PyTypeChecker
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.lyricsContainer.verticalScrollBar(), b"value", self.lyricsContainer): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()
        self.lyricsLogger.debug("Lyrics refreshed")
