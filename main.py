# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52
import random
import typing

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

import logging
import math
import re
from pathlib import Path
from typing import Dict

import colorlog
import qtawesome
import taglib
from PySide2 import QtCore, QtGui, QtMultimedia, QtWidgets


class App(QtWidgets.QApplication):
    playlists: typing.List["Playlist"]
    player: QtMultimedia.QMediaPlayer
    playHistoryDict: typing.Dict[int, int]

    @staticmethod
    def initLogging():
        consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-10s %(message)s"
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
        logging.getLogger().setLevel(logging.DEBUG)

    def __init__(self):
        super().__init__()
        self.initLogging()
        self.logger = logging.getLogger("app")
        self.lyricsLogger = logging.getLogger("lyrics")
        self.lyricsLogger.setLevel(logging.INFO)
        self.positionLogger = logging.getLogger("position")
        self.positionLogger.setLevel(logging.INFO)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.mainWindow = MainWindow(self)

    def exec_(self) -> int:
        self.initPlaylists()
        self.initPlayer()
        self.mainWindow.show()
        return super().exec_()

    def initPlaylists(self):
        playlists: typing.List[Playlist] = [Playlist("Alpha"), Playlist("Beta")]
        for index, path in enumerate(list(Path("~/Music").expanduser().glob("**/*.mp3"))[:200]):
            parts = [x.strip() for x in path.with_suffix("").name.rsplit("-", maxsplit=1)]
            artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
            info = taglib.File(str(path))
            music = Music()
            music.filename = str(path)
            music.filesize = path.stat().st_size
            music.album = info.tags.get("ALBUM", [""])[0]
            music.title = info.tags.get("TITLE", [title])[0]
            music.artist = info.tags.get("ARTIST", [artist])[0]
            music.bitrate = info.bitrate
            music.sampleRate = info.sampleRate
            music.channels = info.channels
            music.duration = info.length * 1000
            playlists[0 if index % 3 == 0 else 1].musics.append(music)
        self.playlists = playlists
        self.mainWindow.initPlaylistTables(self.playlists)
        self.playHistoryDict = dict()

    def initPlayer(self):
        player = QtMultimedia.QMediaPlayer(self)
        player.setVolume(50)
        player.durationChanged.connect(self.onPlayerDurationChanged)
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.volumeChanged.connect(lambda x: logging.debug("Volume changed: %d", x))
        player.positionChanged.connect(self.onPlayerPositionChanged)
        player.setProperty(CURRENT_PLAYLIST_INDEX, 0)
        player.setProperty(CURRENT_MUSIC_INDEX, -1)
        player.setProperty(PLAYBACK_MODE, "LOOP")
        player.setProperty(PLAY_HISTORY_INDEX, -1)
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

    def currentRealDuration(self):
        currentPlaylistIndex = self.player.property(CURRENT_PLAYLIST_INDEX)
        currentMusicIndex = self.player.property(CURRENT_MUSIC_INDEX)
        currentMusic = self.playlists[currentPlaylistIndex].musics[currentMusicIndex]
        realDuration = currentMusic.filesize * 8 // currentMusic.bitrate
        return realDuration

    def currentBugRate(self):
        return self.player.duration() / self.currentRealDuration()

    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() else layout.removeItem(
                layout.itemAt(i))

    def playPrevious(self):
        logging.info(">>> Play previous")
        previousHistoryIndex = self.player.property(PLAY_HISTORY_INDEX) - 1
        previousMusicIndex = self.playHistoryDict.get(previousHistoryIndex, -1)
        logging.info("Previous music index: %d", previousMusicIndex)
        playbackMode = self.player.property(PLAYBACK_MODE)
        currentPlaylist = self.playlists[self.player.property(CURRENT_PLAYLIST_INDEX)]
        currentMusicIndex = self.player.property(CURRENT_MUSIC_INDEX)
        currentPlaylistLength = len(currentPlaylist.musics)
        if previousMusicIndex == -1:
            if playbackMode == "LOOP":
                previousMusicIndex = (currentMusicIndex - 1) % currentPlaylistLength
            else:
                previousMusicIndex = random.randint(0, currentPlaylistLength - 1)
            self.playHistoryDict[previousHistoryIndex] = previousMusicIndex
        logging.info("Final previous music index: %d", previousMusicIndex)
        self.player.setProperty(PLAY_HISTORY_INDEX, previousHistoryIndex)
        self.playMusicAtIndex(previousMusicIndex)

    def playNext(self):
        logging.info(">>> Play next")
        nextHistoryIndex = self.player.property(PLAY_HISTORY_INDEX) + 1
        nextMusicIndex = self.playHistoryDict.get(nextHistoryIndex, -1)
        logging.info("Next music index: %d", nextMusicIndex)
        playbackMode = self.player.property(PLAYBACK_MODE)
        currentPlaylist = self.playlists[self.player.property(CURRENT_PLAYLIST_INDEX)]
        currentMusicIndex = self.player.property(CURRENT_MUSIC_INDEX)
        currentPlaylistLength = len(currentPlaylist.musics)
        if nextMusicIndex == -1:
            if playbackMode == "LOOP":
                nextMusicIndex = (currentMusicIndex + 1) % currentPlaylistLength
            else:
                nextMusicIndex = random.randint(0, currentPlaylistLength - 1)
            self.playHistoryDict[nextHistoryIndex] = nextMusicIndex
        logging.info("Final next music index: %d", nextMusicIndex)
        self.player.setProperty(PLAY_HISTORY_INDEX, nextHistoryIndex)
        self.playMusicAtIndex(nextMusicIndex)

    def playMusicAtIndex(self, index):
        previousMusicIndex = self.player.property(CURRENT_MUSIC_INDEX)
        self.player.setProperty(CURRENT_MUSIC_INDEX, index)
        filename = self.playlists[self.player.property(CURRENT_PLAYLIST_INDEX)].musics[index].filename
        logging.info("Play music: %d => %d %s", previousMusicIndex, index, filename)
        currentPlaylistTable = self.mainWindow.playlistTables[self.player.property(CURRENT_PLAYLIST_INDEX)]
        currentPlaylistTable.selectRow(index)
        previousMusicIndex != -1 and currentPlaylistTable.model().item(previousMusicIndex, 1).setIcon(QtGui.QIcon())
        currentPlaylistTable.model().item(index, 1).setIcon(qtawesome.icon("mdi.play"))
        self.mainWindow.setupLyrics(filename)
        self.mainWindow.setWindowTitle(Path(filename).with_suffix("").name)
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filename)))
        self.player.play()

    def onPlayerDurationChanged(self, duration):
        playerDurationText = self.formatDelta(self.player.duration())
        realDurationText = self.formatDelta(self.currentRealDuration())
        logging.info("Player duration changed: %d (%s / %s)", self.player.duration(), playerDurationText,
            realDurationText)
        self.mainWindow.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Position changed: %d", position)
        self.mainWindow.progressSlider.setValue(position)
        progressText = f"{self.formatDelta(position / self.currentBugRate())}" \
                       f"/{self.formatDelta(self.player.duration() / self.currentBugRate())}"
        self.mainWindow.progressLabel.setText(progressText)
        music = self.playlists[self.player.property(CURRENT_PLAYLIST_INDEX)].musics[
            self.player.property(CURRENT_MUSIC_INDEX)]
        suffix = Path(self.player.currentMedia().canonicalUrl().toLocalFile()).suffix
        self.player.state() != QtMultimedia.QMediaPlayer.StoppedState and self.mainWindow.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(suffix[1:].upper(), music.bitrate, music.sampleRate,
                music.channels, progressText.replace("/", " / ")))
        self.mainWindow.refreshLyrics(math.ceil(position / self.currentBugRate()))

    def onPlayerStateChanged(self, state):
        logging.info("Player state changed: %s [%d/%d]", state, self.player.position(), self.player.duration())
        self.mainWindow.playButton.setIcon(qtawesome.icon(["mdi.play", "mdi.pause", "mdi.play"][state]))
        currentPlaylistTable = self.mainWindow.playlistTables[self.player.property(CURRENT_PLAYLIST_INDEX)]
        stateIcon = [QtGui.QIcon(), qtawesome.icon("mdi.play"), qtawesome.icon("mdi.pause")][state]
        currentPlaylistTable.model().item(self.player.property(CURRENT_MUSIC_INDEX), 1).setIcon(stateIcon)
        finished = state == QtMultimedia.QMediaPlayer.StoppedState and self.player.position() == self.player.duration()
        finished and self.playNext()


class MainWindow(QtWidgets.QMainWindow):
    toolbar: QtWidgets.QToolBar
    mainWidget: QtWidgets.QWidget
    mainSplitter: QtWidgets.QSplitter
    controlsLayout: QtWidgets.QHBoxLayout
    playlistWidget: QtWidgets.QStackedWidget
    playlistTables: typing.List[QtWidgets.QTableView]
    lyricsContainer: QtWidgets.QScrollArea
    lyricsLayout: QtWidgets.QVBoxLayout
    playButton: QtWidgets.QPushButton
    playbackButton: QtWidgets.QPushButton
    progressSlider: QtWidgets.QSlider
    progressLabel: QtWidgets.QLabel

    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.resize(1280, 720)
        self.initToolbar()
        self.initLayout()
        self.statusBar().showMessage("Ready.")

    def initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        actionOne = QtWidgets.QAction("Playlist One", toolbar)
        actionTwo = QtWidgets.QAction("Playlist Two", toolbar)
        actionOne.triggered.connect(lambda: self.playlistWidget.setCurrentIndex(0))
        actionTwo.triggered.connect(lambda: self.playlistWidget.setCurrentIndex(1))
        toolbar.addAction(actionOne)
        toolbar.addAction(actionTwo)
        self.toolbar = toolbar

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

    def generatePlaylistTable(self) -> QtWidgets.QTableView:
        playlistTable = QtWidgets.QTableView(self.playlistWidget)
        playlistModel = QtGui.QStandardItemModel(0, 3)
        playlistModel.setHorizontalHeaderLabels(["", "", "Artist", "Title"])
        playlistModel.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        playlistModel.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        playlistTable.setModel(playlistModel)
        playlistTable.setColumnWidth(0, 100)
        playlistTable.setColumnWidth(1, 30)
        playlistTable.setColumnWidth(2, 200)
        playlistTable.setColumnWidth(3, 300)
        playlistTable.setColumnHidden(0, True)
        playlistTable.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        playlistTable.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
        playlistTable.horizontalHeader().setStretchLastSection(True)
        playlistTable.doubleClicked.connect(lambda x: self.onPlaylistTableDoubleClicked(x.row()))
        playlistTable.setAlternatingRowColors(True)
        playlistTable.setStyleSheet("alternate-background-color: rgb(245, 245, 245)")
        playlistTable.setFrameShape(QtWidgets.QFrame.NoFrame)
        playlistTable.setShowGrid(False)
        playlistTable.setItemDelegate(NoFocusDelegate())
        playlistTable.horizontalHeader().setStyleSheet(
            "QHeaderView::section { border-top:0px solid #D8D8D8; border-bottom: 1px solid #D8D8D8; "
            "background-color:white; padding:2px; font-weight: light; }")
        playlistTable.horizontalHeader().setHighlightSections(False)
        tablePalette = playlistTable.palette()
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight))
        tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText,
            tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        playlistTable.setPalette(tablePalette)
        playlistTable.setIconSize(QtCore.QSize(32, 32))
        return playlistTable

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
        lyricsContainer.resizeEvent = lambda x: [
            lyricsLayout.count() and lyricsLayout.itemAt(0).spacerItem().changeSize(0, x.size().height() // 2),
            lyricsLayout.count() and lyricsLayout.itemAt(lyricsLayout.count() - 1).spacerItem()
                .changeSize(0, x.size().height() // 2),
            lyricsLayout.invalidate(),
        ]
        mainSplitter.addWidget(playlistWidget)
        mainSplitter.addWidget(lyricsContainer)
        mainSplitter.setSizes([2 ** 31 - 1, 2 ** 31 - 1])
        lyricsContainer.horizontalScrollBar().hide()
        self.playlistWidget = playlistWidget
        self.lyricsContainer = lyricsContainer
        self.lyricsLayout = lyricsLayout

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
        progressSlider = MySlider(QtCore.Qt.Horizontal, mainWidget)
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

    def initPlaylistTables(self, playlists):
        playlistTables = list()
        for playlistIndex, playlist in enumerate(playlists):
            table = self.generatePlaylistTable()
            playlistTables.append(table)
            self.playlistWidget.addWidget(table)
            for musicIndex, music in enumerate(playlist.musics):
                indexCell = QtGui.QStandardItem(str(musicIndex + 1))
                indexCell.setData(Path(music.filename), QtCore.Qt.UserRole)
                stateCell = QtGui.QStandardItem("")
                artistCell = QtGui.QStandardItem(music.artist)
                titleCell = QtGui.QStandardItem(music.title)
                table.model().appendRow([indexCell, stateCell, artistCell, titleCell])
        self.playlistTables = playlistTables

    def togglePlaybackMode(self):
        oldPlaybackMode = self.app.player.property(PLAYBACK_MODE)
        newPlaybackMode = dict(LOOP="RANDOM", RANDOM="LOOP")[oldPlaybackMode]
        self.app.player.setProperty(PLAYBACK_MODE, newPlaybackMode)
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        currentMusicIndex = self.app.player.property(CURRENT_MUSIC_INDEX)
        if currentMusicIndex == -1:
            self.app.player.setProperty(CURRENT_PLAYLIST_INDEX, self.playlistWidget.currentIndex())
            logging.info("Current music index is -1, play next at playlist %d", self.playlistWidget.currentIndex())
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
        self.statusBar().showMessage("Stopped.")

    def onPlaylistTableDoubleClicked(self, index):
        logging.info(">>> On playlist table double clicked at %d", index)
        previousPlaylistIndex = self.app.player.property(CURRENT_PLAYLIST_INDEX)
        currentPlaylistIndex = self.playlistWidget.currentIndex()
        logging.info("Playlist index: %d => %d", previousPlaylistIndex, currentPlaylistIndex)
        if currentPlaylistIndex != previousPlaylistIndex:
            logging.info("Toggle playlist from %d to %d", previousPlaylistIndex, currentPlaylistIndex)
            previousPlaylistTable = self.playlistTables[previousPlaylistIndex]
            previousMusicIndex = self.app.player.property(CURRENT_MUSIC_INDEX)
            previousMusicIndex != -1 and previousPlaylistTable.model().item(previousMusicIndex, 1).setIcon(
                QtGui.QIcon())
            self.app.player.setProperty(CURRENT_PLAYLIST_INDEX, currentPlaylistIndex)
            self.app.player.setProperty(CURRENT_MUSIC_INDEX, -1)
            self.app.player.setProperty(PLAY_HISTORY_INDEX, -1)
            self.app.playHistoryDict.clear()
        logging.info("Play music at index %d", index)
        nextHistoryIndex = self.app.player.property(PLAY_HISTORY_INDEX) + 1
        logging.info("Before history dict clean: %s", self.app.playHistoryDict)
        [self.app.playHistoryDict.pop(key) for key in list(self.app.playHistoryDict) if key > nextHistoryIndex]
        logging.info("After history dict clean: %s", self.app.playHistoryDict)
        self.app.playHistoryDict[nextHistoryIndex] = index
        self.app.player.setProperty(PLAY_HISTORY_INDEX, nextHistoryIndex)
        self.app.playMusicAtIndex(index)

    def setupLyrics(self, filename):
        self.app.player.setProperty("previousLyricIndex", -1)
        lyricsPath = Path(filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text()
        lyricDict = self.app.parseLyrics(lyricsText)
        self.app.player.setProperty("lyricDict", lyricDict)
        self.app.clearLayout(self.lyricsLayout)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self.lyricsContainer)
            lyricLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, position=position: self.app.player.setPosition(position * self.app.currentBugRate()))
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize(12)
            lyricLabel.setFont(font)
            lyricLabel.setMargin(2)
            self.lyricsLayout.addWidget(lyricLabel)
        self.lyricsLayout.addSpacing(self.lyricsContainer.height() // 2)
        self.lyricsContainer.verticalScrollBar().setValue(0)
        self.lyricsContainer.horizontalScrollBar().setValue(
            (self.lyricsContainer.horizontalScrollBar().maximum()
             + self.lyricsContainer.horizontalScrollBar().minimum()) // 2)
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


class Playlist(object):
    def __init__(self, name: str):
        self.name = name
        self.musics: typing.List[Music] = []


class Music(object):
    def __init__(self):
        self.filename = ""
        self.filesize = 0
        self.album = ""
        self.artist = ""
        self.title = ""
        self.duration = 0
        self.bitrate = 0
        self.sampleRate = 0
        self.channels = 0


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.clicked.emit(ev)


class MySlider(QtWidgets.QSlider):
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


CURRENT_PLAYLIST_INDEX = "currentPlaylistIndex"
CURRENT_MUSIC_INDEX = "currentMusicIndex"
PLAYBACK_MODE = "playbackMode"
PLAY_HISTORY_INDEX = "playHistoryIndex"
App().exec_()
