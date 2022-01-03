from __future__ import annotations

import logging
import typing
from pathlib import Path

import qtawesome
from PySide2 import QtCore, QtGui, QtMultimedia, QtWidgets

from iceSpringMusicPlayer.controls import FluentSlider, ClickableLabel
from iceSpringMusicPlayer.domains import Playlist
from iceSpringMusicPlayer.widgets import PlaylistTable, PlaylistModel
from iceSpringMusicPlayer.windows import PlaylistsDialog
from iceSpringMusicPlayer.utils import MusicUtils

if typing.TYPE_CHECKING:
    from iceSpringMusicPlayer.app import App


class MainWindow(QtWidgets.QMainWindow):
    toolbar: QtWidgets.QToolBar
    mainWidget: QtWidgets.QWidget
    mainSplitter: QtWidgets.QSplitter
    controlsLayout: QtWidgets.QHBoxLayout
    playlistWidget: QtWidgets.QStackedWidget
    lyricsContainer: QtWidgets.QScrollArea
    lyricsLayout: QtWidgets.QVBoxLayout
    playButton: QtWidgets.QPushButton
    playbackButton: QtWidgets.QPushButton
    progressSlider: QtWidgets.QSlider
    progressLabel: QtWidgets.QLabel
    statusLabel: QtWidgets.QLabel
    playlistCombo: QtWidgets.QComboBox
    playlistsDialog: PlaylistsDialog

    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger("mainWindow")
        self.initMenu()
        self.initToolbar()
        self.initLayout()
        self.initStatusBar()
        self.initPlaceholderPlaylistTable()
        self.playlistsDialog = PlaylistsDialog(self.app.playlists, self)

    def initPlaceholderPlaylistTable(self):
        placeholderPlaylist = Playlist("Placeholder", self.app.currentPlaybackMode)
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
        if self.app.currentPlaylist.currentMusic is None:
            return
        self.playlistWidget.setCurrentIndex(self.app.currentPlaylistIndex)
        self.currentPlaylistTable.selectRow(self.app.currentPlaylist.currentMusicIndex)
        self.currentPlaylistTable.scrollTo(self.currentPlaylistModel.index(
            self.app.currentPlaylist.currentMusicIndex, 0), QtWidgets.QTableView.PositionAtCenter)

    @property
    def currentPlaylistTable(self) -> PlaylistTable:
        return self.playlistWidget.widget(self.app.currentPlaylistIndex)

    @property
    def frontPlaylistTable(self) -> PlaylistTable:
        return self.playlistWidget.widget(self.app.frontPlaylistIndex)

    @property
    def currentPlaylistModel(self) -> PlaylistModel:
        return self.currentPlaylistTable.model()

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self.onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager", lambda: PlaylistsDialog(self.app.playlists, self).show())

    def createDefaultPlaylist(self):
        self.logger.info("Create default playlist")
        placeholderPlaylistTable: PlaylistTable = self.playlistWidget.widget(0)
        playlist = placeholderPlaylistTable.playlist
        playlist.name = "Playlist 1"
        self.app.playlists.append(playlist)
        self.playlistCombo.addItem(playlist.name)
        if len(self.app.playlists) == 1:
            self.app.currentPlaylist = playlist
            self.app.frontPlaylist = playlist

    def onOpenActionTriggered(self):
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self.logger.info("There are %d files to open", len(filenames))
        musics = [MusicUtils.parseMusic(x) for x in filenames]
        if not musics:
            self.logger.info("No music file to open, return")
            return
        if not self.app.playlists:
            self.logger.info("No playlist, create default one")
            self.createDefaultPlaylist()
        beginRow, endRow = self.frontPlaylistTable.model().insertMusics(musics)
        self.frontPlaylistTable.selectRowRange(beginRow, endRow)
        self.frontPlaylistTable.repaint()
        self.frontPlaylistTable.scrollToRow(beginRow)

    def initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        playlistCombo.activated.connect(lambda index: self.logger.info("On playlist combobox activated at: %d", index))
        playlistCombo.activated.connect(lambda index: self.app.setFrontPlaylistAtIndex(index))
        toolbar.addWidget(QtWidgets.QLabel("Playlist: ", toolbar))
        toolbar.addWidget(playlistCombo)
        self.toolbar = toolbar
        self.playlistCombo = playlistCombo

    def initLayout(self):
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setAutoFillBackground(True)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor("white"))
        mainWidget.setPalette(palette)
        self.setCentralWidget(mainWidget)
        self.initMainLayout()
        self.initMainSplitter()
        self.initControlsLayout()

    def initMainLayout(self):
        lines = [QtWidgets.QFrame(self) for _ in range(2)]
        for line in lines:
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Plain)
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
        lyricsContainer.setFrameShape(QtWidgets.QFrame.NoFrame)
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
        previousButton.clicked.connect(lambda: self.app.playPrevious())
        nextButton = QtWidgets.QToolButton(mainWidget)
        nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
        nextButton.clicked.connect(lambda: self.app.playNext())
        playbackButton = QtWidgets.QToolButton(mainWidget)
        playbackButton.setIcon(qtawesome.icon("mdi.repeat"))
        playbackButton.clicked.connect(self.togglePlaybackMode)
        for button in playButton, stopButton, previousButton, nextButton, playbackButton:
            button.setIconSize(QtCore.QSize(50, 50))
            button.setAutoRaise(True)
        progressSlider = FluentSlider(QtCore.Qt.Horizontal, mainWidget)
        progressSlider.setDisabled(True)
        progressSlider.valueChanged.connect(lambda x: self.app.player.setPosition(x))
        progressLabel = QtWidgets.QLabel("00:00/00:00", mainWidget)
        volumeDial = QtWidgets.QDial(mainWidget)
        volumeDial.setFixedSize(50, 50)
        volumeDial.setValue(50)
        volumeDial.valueChanged.connect(lambda x: self.app.player.setVolume(x))
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

    def addPlaylist(self, playlist: Playlist):
        self.logger.info("Add playlist: %s", playlist)
        self.playlistWidget.addWidget(PlaylistTable(playlist, self))
        self.playlistCombo.addItem(playlist.name)
        if len(self.app.playlists) == 1:
            self.app.currentPlaylist = playlist
            self.app.frontPlaylist = playlist

    def removePlaylistsAtIndexes(self, indexes: typing.List[int]):
        for index in sorted(indexes, reverse=True):
            self.playlistWidget.removeWidget(self.playlistWidget.widget(index))
            self.playlistCombo.removeItem(index)

    def togglePlaybackMode(self):
        oldPlaybackMode = self.app.currentPlaybackMode
        newPlaybackMode = dict(LOOP="RANDOM", RANDOM="LOOP")[oldPlaybackMode]
        self.app.currentPlaybackMode = newPlaybackMode
        for playlist in self.app.playlists:
            playlist.playbackMode = newPlaybackMode
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        if self.app.currentPlaylist is None:
            self.logger.info("Current playlist is none, return")
            return
        if self.app.currentPlaylist.currentMusic is None:
            self.app.currentPlaylist = self.app.playlists[self.playlistWidget.currentIndex()]
            logging.info("Current music is none, play next at playlist %d", self.playlistWidget.currentIndex())
            self.app.playNext()
        elif self.app.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            logging.info("Player is playing, pause it")
            self.app.player.pause()
        else:
            logging.info("Player is not playing, play it")
            self.app.player.play()

    def onStopButtonClicked(self):
        logging.info("On stop button clicked")
        self.app.player.stop()

    def setupLyrics(self):
        # noinspection PyTypeChecker
        self.app.player.setProperty("previousLyricIndex", -1)
        lyricsPath = Path(self.app.currentPlaylist.currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text()
        lyricDict = self.app.parseLyrics(lyricsText)
        # noinspection PyTypeChecker
        self.app.player.setProperty("lyricDict", lyricDict)
        self.app.clearLayout(self.lyricsLayout)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self.lyricsContainer)
            lyricLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            # noinspection PyShadowingNames
            lyricLabel.clicked.connect(
                lambda _, position=position: self.app.player.setPosition(position * self.app.currentBugRate))
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
        # noinspection PyTypeChecker
        lyricDict = self.app.player.property("lyricDict")
        # noinspection PyTypeChecker
        previousLyricIndex = self.app.player.property("previousLyricIndex")
        lyricIndex = self.app.calcLyricIndexAtPosition(position, list(lyricDict.keys()))
        if lyricIndex == previousLyricIndex:
            return
        # noinspection PyTypeChecker
        self.app.player.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyricDict)):
            lyricLabel: QtWidgets.QLabel = self.lyricsLayout.itemAt(index + 1).widget()
            lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
            originalValue = self.lyricsContainer.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.lyricsContainer.height() // 2 + lyricLabel.height() // 2
            QtCore.QPropertyAnimation().start(QtCore.QPropertyAnimation.DeleteWhenStopped)
            # noinspection PyTypeChecker
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.lyricsContainer.verticalScrollBar(), b"value", self.lyricsContainer): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()
