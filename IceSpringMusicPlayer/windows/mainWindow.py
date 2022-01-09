# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37

from __future__ import annotations

import logging
import math
import typing
from pathlib import Path

import qtawesome
from IceSpringRealOptional import Option
from PySide2 import QtCore, QtGui, QtMultimedia, QtWidgets

from IceSpringMusicPlayer.controls.clickableLabel import ClickableLabel
from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringMusicPlayer.utils.lyricUtils import LyricUtils
from IceSpringMusicPlayer.utils.musicUtils import MusicUtils
from IceSpringMusicPlayer.utils.timeDeltaUtils import TimeDeltaUtils
from IceSpringMusicPlayer.utils.typeHintUtils import gg
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
from IceSpringMusicPlayer.windows.playlistsDialog import PlaylistsDialog

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
    playlistsDialog: PlaylistsDialog
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
        self.initPlaceholderPlaylistTable()
        playlistsDialog = PlaylistsDialog(self.player.fetchAllPlaylists(), self)
        playlistsDialog.playlistsTable.model().playlistsRemoved.connect(self.onPlaylistsRemovedAtIndexes)
        self.playlistsDialog = playlistsDialog
        self._frontPlaylistIndex = -1
        self.setupPlayer()

    def setupPlayer(self):
        player = self.player
        player.durationChanged.connect(self.onPlayerDurationChanged)
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.volumeChanged.connect(lambda x: logging.debug("Volume changed: %d", x))
        player.positionChanged.connect(self.onPlayerPositionChanged)
        player.playlistAdded.connect(self.onPlaylistAdded)
        player.musicIndexChanged.connect(self.onMusicIndexChanged)

    def initPlaceholderPlaylistTable(self):
        placeholderPlaylist = Playlist("Placeholder")
        placeholderPlaylistTable = PlaylistTable(placeholderPlaylist, self)
        self.playlistWidget.addWidget(placeholderPlaylistTable)

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

    def fetchCurrentPlaylistTable(self) -> Option[PlaylistTable]:
        if not self.player.fetchCurrentPlaylist().isPresent():
            return Option.empty()
        currentPlaylistIndex = self.player.fetchCurrentPlaylistIndex()
        currentPlaylistTable = self.playlistWidget.widget(currentPlaylistIndex)
        return Option.of(gg(currentPlaylistTable, _type=PlaylistTable))

    def fetchFrontPlaylistTable(self) -> Option[PlaylistTable]:
        if self._frontPlaylistIndex < 0:
            return Option.empty()
        frontPlaylistTable = self.playlistWidget.widget(self._frontPlaylistIndex)
        return Option.of(gg(frontPlaylistTable, _type=PlaylistTable))

    def fetchFrontPlaylistIndex(self) -> int:
        return self._frontPlaylistIndex

    def fetchFrontPlaylist(self) -> Option[Playlist]:
        if self._frontPlaylistIndex < 0:
            return Option.empty()
        return Option.of(self.player.fetchAllPlaylists()[self._frontPlaylistIndex])

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self.onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager", lambda: PlaylistsDialog(self.player.fetchAllPlaylists(), self).show())

    def setFrontPlaylistAtIndex(self, index: int) -> None:
        assert index >= 0
        self._frontPlaylistIndex = index
        self.playlistCombo.setCurrentIndex(index)
        self.playlistWidget.setCurrentIndex(index)

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
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        if not musics:
            self.logger.info("No music file to open, return")
            return
        if len(self.player.fetchAllPlaylists()) <= 0:
            self.logger.info("No playlist, create default one")
            self.createAndAppendDefaultPlaylist()
        playlistTable = self.fetchFrontPlaylistTable().orElseThrow(AssertionError)
        beginRow, endRow = playlistTable.model().insertMusics(musics)
        playlistTable.selectRowRange(beginRow, endRow)
        playlistTable.repaint()
        playlistTable.scrollToRowAtCenter(beginRow)

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
        previousButton.clicked.connect(self.player.playPrevious)
        nextButton = QtWidgets.QToolButton(mainWidget)
        nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
        nextButton.clicked.connect(self.player.playNext)
        playbackButton = QtWidgets.QToolButton(mainWidget)
        playbackButton.setIcon(qtawesome.icon("mdi.repeat"))
        playbackButton.clicked.connect(self.togglePlaybackMode)
        for button in playButton, stopButton, previousButton, nextButton, playbackButton:
            button.setIconSize(QtCore.QSize(50, 50))
            button.setAutoRaise(True)
        progressSlider = FluentSlider(QtCore.Qt.Orientation.Horizontal, mainWidget)
        progressSlider.setDisabled(True)
        progressSlider.valueChanged.connect(self.player.setPosition)
        progressLabel = QtWidgets.QLabel("00:00/00:00", mainWidget)
        volumeDial = QtWidgets.QDial(mainWidget)
        volumeDial.setFixedSize(50, 50)
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

    def onPlaylistAdded(self, playlist: Playlist) -> None:
        self.logger.info("On playlist added: %s", playlist.name)
        self.playlistCombo.addItem(playlist.name)
        playlistTable = PlaylistTable(playlist, self)
        playlistTable.model().beforeMusicsRemove.connect(self.doBeforeMusicsRemove)
        self.playlistWidget.addWidget(playlistTable)
        if self._frontPlaylistIndex == -1:
            self.setFrontPlaylistAtIndex(0)

    def doBeforeMusicsRemove(self, indexes: typing.List[int]):
        currentPlaylistIndex = self.player.fetchCurrentPlaylistIndex()
        currentMusicIndex = self.player.fetchCurrentMusicIndex()
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        frontPlaylistIndex = self.fetchFrontPlaylistIndex()
        if frontPlaylistIndex != currentPlaylistIndex:
            return
        if currentMusicIndex in indexes:
            self.logger.info("Stop playing music: %s", currentMusic.filename)
            self.player.stop()
            self.player.resetHistories(keepCurrent=False)
        else:
            self.player.resetHistories(keepCurrent=True)

    def onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        for index in sorted(indexes, reverse=True):
            self.playlistWidget.removeWidget(self.playlistWidget.widget(index))
            self.playlistCombo.removeItem(index)
        if len(self.player.fetchAllPlaylists()) <= 0:
            self.initPlaceholderPlaylistTable()

    def togglePlaybackMode(self):
        self.player.setCurrentPlaybackMode(self.player.fetchCurrentPlaybackMode().next())
        newPlaybackMode = self.player.fetchCurrentPlaybackMode()
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode.name]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        if not self.player.fetchCurrentPlaylist().isPresent():
            self.logger.info("Current playlist is none, return")
            return
        if not self.player.fetchCurrentMusic().isPresent():
            logging.info("Current music is none, play next at playlist %d", self.playlistWidget.currentIndex())
            self.player.playNext()
        elif self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            logging.info("Player is playing, pause it")
            self.player.pause()
        else:
            logging.info("Player is not playing, play it")
            self.player.play()

    def onStopButtonClicked(self):
        logging.info("On stop button clicked")
        self.player.stop()

    def onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        music = self.player.fetchCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        currentPlaylistTable = self.fetchCurrentPlaylistTable().orElseThrow(AssertionError)

        self.setWindowTitle(Path(music.filename).with_suffix("").name)
        currentPlaylistTable.model().refreshRow(oldIndex)
        currentPlaylistTable.model().refreshRow(newIndex)
        currentPlaylistTable.selectRow(newIndex)

    def onPlayerDurationChanged(self, duration):
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        playerDurationText = TimeDeltaUtils.formatDelta(self.player.duration())
        realDurationText = TimeDeltaUtils.formatDelta(currentMusic.duration)
        logging.info("Player duration changed: %d (%s / %s)",
            self.player.duration(), playerDurationText, realDurationText)
        self.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Position changed: %d", position)
        self.progressSlider.blockSignals(True)
        self.progressSlider.setValue(position)
        self.progressSlider.blockSignals(False)
        duration = 0 if self.player.state() == QtMultimedia.QMediaPlayer.StoppedState else self.player.duration()
        progressText = f"{TimeDeltaUtils.formatDelta(position / self.player.fetchCurrentBugRate())}" \
                       f"/{TimeDeltaUtils.formatDelta(duration / self.player.fetchCurrentBugRate())}"
        self.progressLabel.setText(progressText)
        suffix = Path(self.player.currentMedia().canonicalUrl().toLocalFile()).suffix
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        self.player.state() != QtMultimedia.QMediaPlayer.StoppedState and self.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(suffix[1:].upper(), currentMusic.bitrate,
                currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
        position != 0 and self.refreshLyrics(math.ceil(position / self.player.fetchCurrentBugRate()))

    def onPlayerStateChanged(self, state):
        oldState = self.player.property("_state") or QtMultimedia.QMediaPlayer.StoppedState
        self.player.setProperty("_state", state)
        if oldState == QtMultimedia.QMediaPlayer.StoppedState and state == QtMultimedia.QMediaPlayer.PlayingState:
            self.setupLyrics()
        logging.info("Player state changed: %s [%d/%d]", state, self.player.position(), self.player.duration())
        self.playButton.setIcon(qtawesome.icon(["mdi.play", "mdi.pause", "mdi.play"][state]))
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        self.statusLabel.setText("{} - {}".format(currentMusic.artist,
            currentMusic.title) if state == QtMultimedia.QMediaPlayer.StoppedState else "")
        self.statusLabel.setText("" if state == QtMultimedia.QMediaPlayer.StoppedState else "{} - {}".
            format(currentMusic.artist, currentMusic.title))
        self.progressSlider.setDisabled(state == QtMultimedia.QMediaPlayer.StoppedState)
        if state == QtMultimedia.QMediaPlayer.StoppedState:
            if self.player.position() == self.player.duration():
                self.player.playNext()
            else:
                self.statusBar().showMessage("Stopped.")
                LayoutUtils.clearLayout(self.lyricsLayout)
        playlistModel = self.fetchCurrentPlaylistTable().orElseThrow(AssertionError).model()
        playlistModel.refreshRow(self.player.fetchCurrentMusicIndex())

    def setupLyrics(self):
        self.player.setProperty("previousLyricIndex", -1)
        currentMusic = self.player.fetchCurrentMusic().orElseThrow(AssertionError)
        lyricsPath = Path(currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text()
        lyricDict = LyricUtils.parseLyrics(lyricsText)
        self.player.setProperty("lyricDict", lyricDict)
        LayoutUtils.clearLayout(self.lyricsLayout)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self.lyricsContainer)
            lyricLabel.setAlignment(
                gg(QtCore.Qt.AlignmentFlag.AlignCenter, typing.Any) | QtCore.Qt.AlignmentFlag.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, pos=position: self.player.setPosition(pos * self.player.fetchCurrentBugRate()))
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize(18)
            lyricLabel.setFont(font)
            lyricLabel.setMargin(2)
            self.lyricsLayout.addWidget(lyricLabel)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        self.lyricsContainer.verticalScrollBar().setValue(0)
        self.refreshLyrics(0)

    def refreshLyrics(self, position):
        lyricDict = self.player.property("lyricDict")
        previousLyricIndex = self.player.property("previousLyricIndex")
        lyricIndex = LyricUtils.calcLyricIndexAtPosition(position, list(lyricDict.keys()))
        if lyricIndex == previousLyricIndex:
            return
        self.player.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyricDict)):
            lyricLabel: QtWidgets.QLabel = self.lyricsLayout.itemAt(index + 1).widget()
            lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
            originalValue = self.lyricsContainer.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.lyricsContainer.height() // 2 + lyricLabel.height() // 2
            QtCore.QPropertyAnimation().start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            # noinspection PyTypeChecker
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.lyricsContainer.verticalScrollBar(), b"value", self.lyricsContainer): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()
