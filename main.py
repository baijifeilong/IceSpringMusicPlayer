# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52
import random
import typing

import typing_extensions

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
    currentPlaylistIndex: int
    currentPlaybackMode: typing_extensions.Literal["LOOP", "RANDOM"]

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
        paths = list(Path("~/Music").expanduser().glob("**/*.mp3"))[:200]
        random.seed(0)
        random.shuffle(paths)
        for index, path in enumerate(paths):
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
        self.mainWindow.setupPlaylistTables(playlists)
        self.playlists = playlists

    def initPlayer(self):
        player = QtMultimedia.QMediaPlayer(self)
        player.setVolume(50)
        player.durationChanged.connect(self.onPlayerDurationChanged)
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.volumeChanged.connect(lambda x: logging.debug("Volume changed: %d", x))
        player.positionChanged.connect(self.onPlayerPositionChanged)
        self.player = player
        self.currentPlaylistIndex = 0
        self.currentPlaybackMode = "LOOP"

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
    def currentPlaylist(self) -> "Playlist":
        return self.playlists[self.currentPlaylistIndex]

    @property
    def currentMusic(self) -> "Music":
        return self.currentPlaylist.musics[self.currentPlaylist.currentMusicIndex]

    @property
    def currentRealDuration(self):
        return self.currentMusic.filesize * 8 // self.currentMusic.bitrate

    @property
    def currentBugRate(self):
        return self.player.duration() / self.currentRealDuration

    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() else layout.removeItem(
                layout.itemAt(i))

    def playPrevious(self):
        logging.info(">>> Play previous")
        previousHistoryIndex = self.currentPlaylist.currentHistoryIndex - 1
        previousMusicIndex = self.currentPlaylist.playHistoryDict.get(previousHistoryIndex, -1)
        logging.info("Previous music index: %d", previousMusicIndex)
        currentPlaylistLength = len(self.currentPlaylist.musics)
        if previousMusicIndex == -1:
            if self.currentPlaybackMode == "LOOP":
                previousMusicIndex = (self.currentPlaylist.currentMusicIndex - 1) % currentPlaylistLength
            else:
                previousMusicIndex = random.randint(0, currentPlaylistLength - 1)
            self.currentPlaylist.playHistoryDict[previousHistoryIndex] = previousMusicIndex
        logging.info("Final previous music index: %d", previousMusicIndex)
        self.currentPlaylist.currentHistoryIndex = previousHistoryIndex
        self.playMusicAtIndex(previousMusicIndex)

    def playNext(self):
        logging.info(">>> Play next")
        nextHistoryIndex = self.currentPlaylist.currentHistoryIndex + 1
        nextMusicIndex = self.currentPlaylist.playHistoryDict.get(nextHistoryIndex, -1)
        logging.info("Next music index: %d", nextMusicIndex)
        currentPlaylistLength = len(self.currentPlaylist.musics)
        if nextMusicIndex == -1:
            if self.currentPlaybackMode == "LOOP":
                nextMusicIndex = (self.currentPlaylist.currentMusicIndex + 1) % currentPlaylistLength
            else:
                nextMusicIndex = random.randint(0, currentPlaylistLength - 1)
            self.currentPlaylist.playHistoryDict[nextHistoryIndex] = nextMusicIndex
        logging.info("Final next music index: %d", nextMusicIndex)
        self.currentPlaylist.currentHistoryIndex = nextHistoryIndex
        self.playMusicAtIndex(nextMusicIndex)

    def playMusicAtIndex(self, index):
        previousMusicIndex = self.currentPlaylist.currentMusicIndex
        self.currentPlaylist.currentMusicIndex = index
        filename = self.currentMusic.filename
        logging.info("Play music: %d => %d %s", previousMusicIndex, index, filename)
        self.mainWindow.currentPlaylistTable.selectRow(index)
        self.mainWindow.currentPlaylistTable.scrollTo(self.mainWindow.currentPlaylistModel.index(index, 0),
            QtWidgets.QTableView.PositionAtCenter)
        self.mainWindow.setupLyrics(filename)
        self.mainWindow.setWindowTitle(Path(filename).with_suffix("").name)
        previousStateIndex = self.mainWindow.currentPlaylistModel.createIndex(previousMusicIndex, 0)
        self.mainWindow.currentPlaylistModel.dataChanged.emit(previousStateIndex, previousStateIndex)
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filename)))
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
        progressText = f"{self.formatDelta(position / self.currentBugRate)}" \
                       f"/{self.formatDelta(self.player.duration() / self.currentBugRate)}"
        self.mainWindow.progressLabel.setText(progressText)
        suffix = Path(self.player.currentMedia().canonicalUrl().toLocalFile()).suffix
        self.player.state() != QtMultimedia.QMediaPlayer.StoppedState and self.mainWindow.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(suffix[1:].upper(), self.currentMusic.bitrate,
                self.currentMusic.sampleRate, self.currentMusic.channels, progressText.replace("/", " / ")))
        self.mainWindow.refreshLyrics(math.ceil(position / self.currentBugRate))

    def onPlayerStateChanged(self, state):
        logging.info("Player state changed: %s [%d/%d]", state, self.player.position(), self.player.duration())
        self.mainWindow.playButton.setIcon(qtawesome.icon(["mdi.play", "mdi.pause", "mdi.play"][state]))
        finished = state == QtMultimedia.QMediaPlayer.StoppedState and self.player.position() == self.player.duration()
        finished and self.playNext()


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

    def __init__(self, app: App):
        super().__init__()
        self.logger = logging.getLogger("mainWindow")
        self.app = app
        self.resize(1280, 720)
        self.initToolbar()
        self.initLayout()
        self.statusBar().showMessage("Ready.")
        self.statusBar().installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.statusBar() and event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.onStatusBarDoubleClicked()
        return super().eventFilter(watched, event)

    def onStatusBarDoubleClicked(self):
        self.logger.info("On status bar double clocked")
        if self.app.currentPlaylist.currentMusicIndex == -1:
            return
        self.playlistWidget.setCurrentIndex(self.app.currentPlaylistIndex)
        self.currentPlaylistTable.selectRow(self.app.currentPlaylist.currentMusicIndex)
        self.currentPlaylistTable.scrollTo(self.currentPlaylistModel.index(
            self.app.currentPlaylist.currentMusicIndex, 0), QtWidgets.QTableView.PositionAtCenter)

    @property
    def currentPlaylistTable(self) -> QtWidgets.QTableView:
        return self.playlistWidget.widget(self.app.currentPlaylistIndex)

    @property
    def currentPlaylistModel(self) -> QtGui.QStandardItemModel:
        return self.currentPlaylistTable.model()

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

    def generatePlaylistTable(self, playlist: "Playlist") -> QtWidgets.QTableView:
        playlistTable = QtWidgets.QTableView(self.playlistWidget)
        playlistTable.setModel(PlaylistModel(playlist, self))
        playlistTable.setColumnWidth(0, 30)
        playlistTable.setColumnWidth(1, 200)
        playlistTable.setColumnWidth(2, 300)
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
        playlistTable.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        playlistTable.setSortingEnabled(True)
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

    def setupPlaylistTables(self, playlists):
        for playlist in playlists:
            self.playlistWidget.addWidget(self.generatePlaylistTable(playlist))

    def togglePlaybackMode(self):
        oldPlaybackMode = self.app.currentPlaybackMode
        newPlaybackMode = dict(LOOP="RANDOM", RANDOM="LOOP")[oldPlaybackMode]
        self.app.currentPlaybackMode = newPlaybackMode
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode]
        self.playbackButton.setIcon(qtawesome.icon(newIconName))

    def onPlayButtonClicked(self):
        logging.info("On play button clicked")
        if self.app.currentPlaylist.currentMusicIndex == -1:
            self.app.currentPlaylistIndex = self.playlistWidget.currentIndex()
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
        self.app.currentPlaylistIndex = self.playlistWidget.currentIndex()
        logging.info("Play music at index %d", index)
        nextHistoryIndex = self.app.currentPlaylist.currentHistoryIndex + 1
        playHistoryDict = self.app.currentPlaylist.playHistoryDict
        logging.info("Before history dict clean: %s", playHistoryDict)
        [playHistoryDict.pop(key) for key in list(playHistoryDict) if key > nextHistoryIndex]
        logging.info("After history dict clean: %s", playHistoryDict)
        playHistoryDict[nextHistoryIndex] = index
        self.app.currentPlaylist.currentHistoryIndex = nextHistoryIndex
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
                lambda _, position=position: self.app.player.setPosition(position * self.app.currentBugRate))
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
                return [qtawesome.icon("mdi.stop"), qtawesome.icon("mdi.play"),
                    qtawesome.icon("mdi.pause")][self.app.player.state()]

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", "Artist", "Title"][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        if column == 0:
            return
        self.playlist.musics = sorted(self.playlist.musics,
            key=lambda x: x.artist if column == 1 else x.title, reverse=order == QtCore.Qt.DescendingOrder)
        self.endResetModel()


class Playlist(object):
    def __init__(self, name: str):
        self.name = name
        self.musics: typing.List[Music] = []
        self.playHistoryDict = dict()
        self.currentMusicIndex = -1
        self.currentHistoryIndex = -1


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


if __name__ == '__main__':
    App().exec_()
