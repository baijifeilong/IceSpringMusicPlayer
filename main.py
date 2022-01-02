# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52
import PySide2

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))
import hashlib
import logging
import math
import random
import re
import typing
from pathlib import Path
from typing import Dict

import colorlog
import qtawesome
import taglib
import typing_extensions
from PySide2 import QtCore, QtGui, QtMultimedia, QtWidgets


class App(QtWidgets.QApplication):
    playlists: typing.List["Playlist"]
    player: QtMultimedia.QMediaPlayer
    currentPlaylist: "Playlist"
    currentPlaybackMode: typing_extensions.Literal["LOOP", "RANDOM"]
    frontPlaylist: "Playlist"

    @staticmethod
    def initLogging():
        consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-16s %(message)s"
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
        logging.getLogger().setLevel(logging.DEBUG)

    def __init__(self):
        super().__init__()
        self.initLogging()
        self.currentPlaybackMode = "LOOP"
        self.logger = logging.getLogger("app")
        self.lyricsLogger = logging.getLogger("lyrics")
        self.lyricsLogger.setLevel(logging.INFO)
        self.positionLogger = logging.getLogger("position")
        self.positionLogger.setLevel(logging.INFO)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.mainWindow = MainWindow(self)
        self.initPlayer()
        self.initPlaylists()

    def exec_(self) -> int:
        self.mainWindow.resize(1280, 720)
        self.mainWindow.show()
        return super().exec_()

    @staticmethod
    def parseMusic(filename) -> "Music":
        parts = [x.strip() for x in Path(filename).with_suffix("").name.rsplit("-", maxsplit=1)]
        artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
        info = taglib.File(filename)
        music = Music()
        music.filename = filename
        music.filesize = Path(filename).stat().st_size
        music.album = info.tags.get("ALBUM", [""])[0]
        music.title = info.tags.get("TITLE", [title])[0]
        music.artist = info.tags.get("ARTIST", [artist])[0]
        music.bitrate = info.bitrate
        music.sampleRate = info.sampleRate
        music.channels = info.channels
        music.duration = info.length * 1000
        return music

    def initPlaylists(self):
        playlists: typing.List[Playlist] = [
            Playlist("Playlist 1", self.currentPlaybackMode), Playlist("Playlist 2", self.currentPlaybackMode)]
        paths = list(Path("~/Music").expanduser().glob("**/*.mp3"))[:200]
        random.Random(0).shuffle(paths)
        for index, path in enumerate(paths):
            playlists[0 if index % 3 == 0 else 1].musics.append(self.parseMusic(str(path)))
        self.mainWindow.setupPlaylists(playlists)
        self.playlists = playlists
        self.currentPlaylist = playlists[0]
        self.frontPlaylist = self.currentPlaylist

    def setFrontPlaylist(self, playlist: "Playlist"):
        if playlist == self.frontPlaylist:
            return
        self.frontPlaylist = playlist
        self.mainWindow.playlistWidget.setCurrentIndex(self.frontPlaylistIndex)

    def setFrontPlaylistAtIndex(self, playlistIndex):
        self.setFrontPlaylist(self.playlists[playlistIndex])

    def initPlayer(self):
        player = QtMultimedia.QMediaPlayer(self)
        player.setVolume(50)
        player.durationChanged.connect(self.onPlayerDurationChanged)
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.volumeChanged.connect(lambda x: logging.debug("Volume changed: %d", x))
        player.positionChanged.connect(self.onPlayerPositionChanged)
        self.player = player

    def parseLyrics(self, lyricsText: str) -> Dict[int, str]:
        lyricsLogger = self.lyricsLogger
        lyricsLogger.info("Parsing lyrics ...")
        lyricRegex = re.compile(r"^((?:\[\d+:[\d.]+])+)(.*)$")
        lyricDict: Dict[int, str] = dict()
        lyricLines = [x.strip() for x in lyricsText.splitlines() if x.strip()]
        for index, line in enumerate(lyricLines):
            lyricsLogger.debug("[%02d/%02d] Lyric line: %s", index + 1, len(lyricLines), line)
            match = lyricRegex.match(line.strip())
            if not match:
                lyricsLogger.debug("Not valid lyric")
                continue
            timespans, content = [x.strip() for x in match.groups()]
            if not content:
                lyricsLogger.debug("Lyric is empty")
                continue
            for timespan in timespans.replace("[", " ").replace("]", " ").split():
                lyricsLogger.debug("Parsed lyric: %s => %s", timespan, content)
                minutes, seconds = [float(x) for x in timespan.split(":")]
                millis = int(minutes * 60000 + seconds * 1000)
                while millis in lyricDict:
                    millis += 1
                lyricDict[millis] = content
        lyricsLogger.info("Total parsed lyric items: %d", len(lyricDict))
        return dict(sorted(lyricDict.items()))

    @staticmethod
    def calcLyricIndexAtPosition(position, positions):
        for index in range(len(positions) - 1):
            if positions[index] <= position < positions[index + 1]:
                return index
        return 0 if position < positions[0] else len(positions) - 1

    @staticmethod
    def formatDelta(milliseconds):
        seconds = int(milliseconds) // 1000
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @property
    def currentPlaylistIndex(self) -> int:
        return self.playlists.index(self.currentPlaylist)

    @property
    def frontPlaylistIndex(self) -> int:
        return self.playlists.index(self.frontPlaylist)

    @property
    def currentRealDuration(self):
        return self.currentPlaylist.currentMusic.filesize * 8 // self.currentPlaylist.currentMusic.bitrate

    @property
    def currentBugRate(self):
        return 1 if self.currentPlaylist.currentMusic is None else self.player.duration() / self.currentRealDuration

    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() \
                else layout.removeItem(layout.itemAt(i))

    def playPrevious(self):
        self.logger.info(">>> Play previous")
        if not self.currentPlaylist.musics:
            self.logger.info("No music to play.")
        else:
            self.playMusic(self.currentPlaylist.playPrevious(), dontFollow=self.currentPlaybackMode == "LOOP")

    def playNext(self):
        self.logger.info(">>> Play next")
        if not self.currentPlaylist.musics:
            self.logger.info("No music to play.")
        else:
            self.playMusic(self.currentPlaylist.playNext(), dontFollow=self.currentPlaybackMode == "LOOP")

    def playMusic(self, music: "Music", dontFollow=False):
        self.logger.info(">>> Play music %s : %s", music.artist, music.title)
        oldMusicIndex = -1 if self.currentPlaylist.lastMusic is None \
            else self.currentPlaylist.musics.index(self.currentPlaylist.lastMusic)
        newMusicIndex = self.currentPlaylist.currentMusicIndex
        self.mainWindow.setWindowTitle(Path(music.filename).with_suffix("").name)
        self.mainWindow.currentPlaylistTable.selectRow(newMusicIndex)
        not dontFollow and self.mainWindow.currentPlaylistTable.scrollToRow(newMusicIndex)
        self.mainWindow.currentPlaylistModel.refreshRow(oldMusicIndex)
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        self.player.play()

    def onPlayerDurationChanged(self, duration):
        playerDurationText = self.formatDelta(self.player.duration())
        realDurationText = self.formatDelta(self.currentRealDuration)
        logging.info("Player duration changed: %d (%s / %s)", self.player.duration(), playerDurationText,
            realDurationText)
        self.mainWindow.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Position changed: %d", position)
        self.mainWindow.progressSlider.blockSignals(True)
        self.mainWindow.progressSlider.setValue(position)
        self.mainWindow.progressSlider.blockSignals(False)
        duration = 0 if self.player.state() == QtMultimedia.QMediaPlayer.StoppedState else self.player.duration()
        progressText = f"{self.formatDelta(position / self.currentBugRate)}" \
                       f"/{self.formatDelta(duration / self.currentBugRate)}"
        self.mainWindow.progressLabel.setText(progressText)
        suffix = Path(self.player.currentMedia().canonicalUrl().toLocalFile()).suffix
        currentMusic = self.currentPlaylist.currentMusic
        self.player.state() != QtMultimedia.QMediaPlayer.StoppedState and self.mainWindow.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(suffix[1:].upper(), currentMusic.bitrate,
                currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
        position != 0 and self.mainWindow.refreshLyrics(math.ceil(position / self.currentBugRate))

    def onPlayerStateChanged(self, state):
        oldState = self.player.property("_state") or QtMultimedia.QMediaPlayer.StoppedState
        self.player.setProperty("_state", state)
        if oldState == QtMultimedia.QMediaPlayer.StoppedState and state == QtMultimedia.QMediaPlayer.PlayingState:
            self.mainWindow.setupLyrics()
        logging.info("Player state changed: %s [%d/%d]", state, self.player.position(), self.player.duration())
        self.mainWindow.playButton.setIcon(qtawesome.icon(["mdi.play", "mdi.pause", "mdi.play"][state]))
        currentMusic = self.currentPlaylist.currentMusic
        self.mainWindow.statusLabel.setText("{} - {}".format(currentMusic.artist,
            currentMusic.title) if state == QtMultimedia.QMediaPlayer.StoppedState else "")
        self.mainWindow.statusLabel.setText("" if state == QtMultimedia.QMediaPlayer.StoppedState else "{} - {}".
            format(currentMusic.artist, currentMusic.title))
        self.mainWindow.progressSlider.setDisabled(state == QtMultimedia.QMediaPlayer.StoppedState)
        if state == QtMultimedia.QMediaPlayer.StoppedState:
            if self.player.position() == self.player.duration():
                self.playNext()
            else:
                self.mainWindow.statusBar().showMessage("Stopped.")
                self.clearLayout(self.mainWindow.lyricsLayout)
        self.mainWindow.currentPlaylistModel.refreshRow(self.currentPlaylist.currentMusicIndex)


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
    playlistsDialog: "PlaylistsDialog"

    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger("mainWindow")
        self.initMenu()
        self.initToolbar()
        self.initLayout()
        self.initStatusBar()

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
    def currentPlaylistTable(self) -> "PlaylistTable":
        return self.playlistWidget.widget(self.app.currentPlaylistIndex)

    @property
    def currentPlaylistModel(self) -> "PlaylistModel":
        return self.currentPlaylistTable.model()

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction("Open", self.onOpenActionTriggered)
        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction("Playlist Manager", lambda: self.playlistsDialog.show())

    def onOpenActionTriggered(self):
        musicRoot = str(Path("~/Music").expanduser().absolute())
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open music files", musicRoot, "Audio files (*.mp3 *.wma) ;; All files (*)")[0]
        self.logger.info("There are %d files to open", len(filenames))
        musics = [self.app.parseMusic(x) for x in filenames]
        beginRow, endRow = self.currentPlaylistModel.insertMusics(musics)
        self.currentPlaylistTable.selectRowRange(beginRow, endRow)
        self.currentPlaylistTable.repaint()
        self.currentPlaylistTable.scrollToRow(beginRow)

    def initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.activated.connect(lambda index: self.logger.info("On playlist combobox activated at: %d", index))
        playlistCombo.activated.connect(lambda index: self.app.setFrontPlaylistAtIndex(index))
        toolbar.addWidget(QtWidgets.QLabel("Playlist:", toolbar))
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

    def setupPlaylists(self, playlists):
        for playlist in playlists:
            self.playlistWidget.addWidget(PlaylistTable(playlist, self))
        for playlist in playlists:
            self.playlistCombo.addItem(playlist.name)
        self.playlistsDialog = PlaylistsDialog(playlists, self)

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
        self.app.player.setProperty("previousLyricIndex", -1)
        lyricsPath = Path(self.app.currentPlaylist.currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text()
        lyricDict = self.app.parseLyrics(lyricsText)
        self.app.player.setProperty("lyricDict", lyricDict)
        self.app.clearLayout(self.lyricsLayout)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self.lyricsContainer)
            lyricLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
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
        lyricDict = self.app.player.property("lyricDict")
        previousLyricIndex = self.app.player.property("previousLyricIndex")
        lyricIndex = self.app.calcLyricIndexAtPosition(position, list(lyricDict.keys()))
        if lyricIndex == previousLyricIndex:
            return
        self.app.player.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyricDict)):
            lyricLabel: QtWidgets.QLabel = self.lyricsLayout.itemAt(index + 1).widget()
            lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
            originalValue = self.lyricsContainer.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.lyricsContainer.height() // 2 + lyricLabel.height() // 2
            QtCore.QPropertyAnimation().start(QtCore.QPropertyAnimation.DeleteWhenStopped)
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.lyricsContainer.verticalScrollBar(), b"value", self.lyricsContainer): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()


class IceTableView(QtWidgets.QTableView):
    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("alternate-background-color: rgb(245, 245, 245)")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setShowGrid(False)
        self.setItemDelegate(NoFocusDelegate())
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section { border-top:0px solid #D8D8D8; border-bottom: 1px solid #D8D8D8; "
            "background-color:white; padding:2px; font-weight: light; }")
        self.horizontalHeader().setHighlightSections(False)
        tablePalette = self.palette()
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight))
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        self.setPalette(tablePalette)


class PlaylistTable(IceTableView):
    def __init__(self, playlist: "Playlist", mainWindow: "MainWindow") -> None:
        super().__init__(mainWindow.playlistWidget)
        self.logger = logging.getLogger("playlistTable")
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = self.mainWindow.app
        self.setModel(PlaylistModel(playlist, mainWindow))
        self.setColumnWidth(0, 35)
        self.setColumnWidth(1, 200)
        self.doubleClicked.connect(lambda x: self.onDoubleClicked(x.row()))
        self.setIconSize(QtCore.QSize(32, 32))
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self.viewport().installEventFilter(mainWindow)

    def model(self) -> "PlaylistModel":
        return super().model()

    def onDoubleClicked(self, index):
        self.logger.info(">>> On playlist table double clicked at %d", index)
        self.app.currentPlaylist = self.app.playlists[self.mainWindow.playlistWidget.currentIndex()]
        self.logger.info("Play music at index %d", index)
        self.app.playMusic(self.app.currentPlaylist.playMusic(self.app.currentPlaylist.musics[index]), True)

    def scrollToRow(self, index):
        self.scrollTo(self.model().index(index, 0), QtWidgets.QTableView.PositionAtCenter)

    def selectRowRange(self, fromRow, toRow):
        self.clearSelection()
        self.selectionModel().select(
            QtCore.QItemSelection(self.model().index(fromRow, 0), self.model().index(toRow, 0)),
            QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu()
        menu.addAction(f"Remove", lambda: self.onRemove(sorted({x.row() for x in self.selectedIndexes()})))
        menu.exec_(QtGui.QCursor.pos())

    def onRemove(self, indexes: typing.List[int]):
        self.logger.info("Removing musics at indexes: %s", indexes)
        if self.playlist == self.app.currentPlaylist and self.playlist.currentMusicIndex in indexes:
            self.logger.info("Stop playing music: %s", self.playlist.currentMusic)
            self.app.player.stop()
        self.playlist.resetHistory(
            keepCurrent=self.playlist == self.app.currentPlaylist and self.playlist.currentMusicIndex not in indexes)
        self.model().removeMusicsByIndexes(indexes)


class PlaylistModel(QtCore.QAbstractTableModel):
    def __init__(self, playlist: "Playlist", mainWindow: MainWindow,
            parent: typing.Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = self.mainWindow.app

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.playlist.musics)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        music = self.playlist.musics[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return ["", music.artist, music.title][index.column()]
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and index.row() == self.app.currentPlaylist.currentMusicIndex \
                    and self.app.currentPlaylistIndex == self.mainWindow.playlistWidget.currentIndex():
                return [QtGui.QIcon(), qtawesome.icon("mdi.play"), qtawesome.icon("mdi.pause")][self.app.player.state()]

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", "Artist", "Title"][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        if column == 0:
            return
        self.playlist.musics = sorted(self.playlist.musics,
            key=lambda x: x.artist if column == 1 else x.title, reverse=order == QtCore.Qt.DescendingOrder)
        if self.playlist.currentMusic is not None:
            self.mainWindow.currentPlaylistTable.selectRow(self.playlist.currentMusicIndex)
            self.mainWindow.currentPlaylistTable.scrollToRow(self.playlist.currentMusicIndex)
        else:
            self.endResetModel()

    def refreshRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

    def insertMusics(self, musics: typing.List["Music"]) -> (int, int):
        beginRow, endRow = len(self.playlist.musics), len(self.playlist.musics) + len(musics) - 1
        self.beginInsertRows(QtCore.QModelIndex(), beginRow, endRow)
        self.playlist.musics.extend(musics)
        self.endInsertRows()
        return beginRow, endRow

    def removeMusicsByIndexes(self, indexes: typing.List[int]) -> None:
        for index in sorted(indexes, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.playlist.musics[index]
        self.endRemoveRows()


class Playlist(object):
    def __init__(self, name: str, playbackMode: typing_extensions.Literal["LOOP", "RANDOM"]):
        self.name = name
        self.playbackMode = playbackMode
        self.musics: typing.List[Music] = []
        self.historyDict: typing.Dict[int, Music] = dict()
        self.historyPosition = -1
        self.lastMusic: typing.Optional[Music] = None
        self.random = random.Random(0)

    def resetHistory(self, keepCurrent: bool) -> None:
        currentMusic = self.currentMusic
        self.historyDict.clear()
        self.historyPosition = -1
        if keepCurrent:
            self.historyDict[0] = currentMusic
            self.historyPosition = 0

    @property
    def currentMusic(self) -> typing.Optional["Music"]:
        return self.historyDict.get(self.historyPosition, None)

    @property
    def currentMusicIndex(self) -> int:
        return -1 if self.currentMusic is None else self.musics.index(self.currentMusic)

    def playNext(self) -> "Music":
        return self.playMusicAtRelativePosition(self.nextMusic(), 1)

    def playPrevious(self) -> "Music":
        return self.playMusicAtRelativePosition(self.previousMusic(), -1)

    def playMusic(self, music: "Music") -> "Music":
        return self.playMusicAtRelativePosition(music, 1)

    def playMusicAtRelativePosition(self, music: "Music", relativePosition) -> "Music":
        self.lastMusic = self.currentMusic
        self.historyPosition += relativePosition
        self.historyDict[self.historyPosition] = music
        return music

    def nextMusic(self) -> "Music":
        historyNextMusic = self.historyDict.get(self.historyPosition + 1, None)
        randomNextMusic = self.musics[self.memorizedNextRandomMusicIndex()]
        loopNextMusic = self.musics[0] if self.currentMusic is None \
            else self.musics[(self.currentMusicIndex + 1) % len(self.musics)]
        return loopNextMusic if self.playbackMode == "LOOP" else historyNextMusic or randomNextMusic

    def previousMusic(self) -> "Music":
        historyPreviousMusic = self.historyDict.get(self.historyPosition - 1, None)
        randomPreviousMusic = self.musics[self.memorizedPreviousRandomMusicIndex()]
        loopPreviousMusic = self.musics[-1] if self.currentMusic is None \
            else self.musics[(self.currentMusicIndex - 1) % len(self.musics)]
        return loopPreviousMusic if self.playbackMode == "LOOP" else historyPreviousMusic or randomPreviousMusic

    def memorizedNextRandomValue(self) -> float:
        oldMemoryFlag = getattr(Playlist.memorizedNextRandomValue, "flag", "-1/-1")
        newMemoryFlag = "{}/{}".format(self.historyPosition, len(self.musics))
        if newMemoryFlag != oldMemoryFlag:
            setattr(Playlist.memorizedNextRandomValue, "flag", newMemoryFlag)
            setattr(Playlist.memorizedNextRandomValue, "value", self.random.random())
        assert hasattr(Playlist.memorizedNextRandomValue, "value")
        return getattr(Playlist.memorizedNextRandomValue, "value")

    def memorizedPreviousRandomMusicIndex(self):
        index = int(hashlib.md5(f"P/{self.memorizedNextRandomValue()}".encode()).hexdigest(), 16) % len(self.musics)
        return index if index != self.currentMusicIndex else (index - 1) % len(self.musics)

    def memorizedNextRandomMusicIndex(self):
        index = int(hashlib.md5(f"N/{self.memorizedNextRandomValue()}".encode()).hexdigest(), 16) % len(self.musics)
        return index if index != self.currentMusicIndex else (index + 1) % len(self.musics)


class Music(object):
    filename: str
    filesize: int
    album: str
    artist: str
    title: str
    duration: int
    bitrate: int
    sampleRate: int
    channels: int


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.clicked.emit(ev)


class FluentSlider(QtWidgets.QSlider):
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.setValue(
            self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
        super().mousePressEvent(ev)


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        itemOption = QtWidgets.QStyleOptionViewItem(option)
        if option.state & QtWidgets.QStyle.State_HasFocus:
            itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, itemOption, index)


class PlaylistsDialog(QtWidgets.QDialog):
    def __init__(self, playlists: typing.List[Playlist], parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.playlists = playlists
        self.setWindowTitle("Playlist Manager")
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(PlaylistsTable(playlists, self))
        self.resize(640, 360)


class PlaylistsTable(IceTableView):
    def __init__(self, playlists: typing.List[Playlist], parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.app: App = self.parent().parent().app
        self.logger = logging.getLogger("playlistsTable")
        self.setModel(PlaylistsModel(playlists, self))
        self.setColumnWidth(0, 320)
        self.doubleClicked.connect(lambda x: self.onDoubleClickedAtRow(x.row()))

    def onDoubleClickedAtRow(self, row):
        self.logger.info("On double clicked at row: %d", row)
        self.app.setFrontPlaylistAtIndex(row)


class PlaylistsModel(QtCore.QAbstractTableModel):
    def __init__(self, playlists: typing.List[Playlist], parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self.playlists = playlists

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.playlists)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        playlist = self.playlists[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return playlist.name
            elif index.column() == 1:
                return str(len(playlist.musics))

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["Name", "Items"][section]
        return super().headerData(section, orientation, role)


if __name__ == '__main__':
    App().exec_()
