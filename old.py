# Created by BaiJiFeiLong@gmail.com at 2018/8/6 0:05

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

import json
import pathlib
import random
import re
import time
from enum import Enum
from typing import List, Dict, Tuple

import chardet
import qtawesome
import taglib
from PySide2 import QtWidgets, QtGui, QtCore, QtMultimedia


class Config(object):
    configPath = pathlib.Path("config.json")

    def __init__(self):
        super().__init__()
        self.playbackMode = MyPlaylist.PlaybackMode.LOOP
        self.playlist: List[MusicEntry] = list()
        self.volume = 50
        self.currentIndex = -1
        self.sortBy = 'ARTIST'
        self.sortOrder = 'ASCENDING'

    @staticmethod
    def load():
        print("Prepare to load config ...")
        config = Config()
        if Config.configPath.exists():
            print("Loading config ...")
            jd = json.loads(Config.configPath.read_text())
            config.playbackMode = MyPlaylist.PlaybackMode(jd['playbackMode'])
            for item in jd['playlist']:
                config.playlist.append(MusicEntry(
                    pathlib.Path(item['path']),
                    item['artist'],
                    item['title'],
                    item['duration']
                ))
            config.volume = jd['volume']
            config.currentIndex = jd['currentIndex']
            config.sortBy = jd['sortBy']
            config.sortOrder = jd['sortOrder']
        else:
            print("Config not exist")
        return config

    def persist(self):
        print("Persisting config ...")
        jd = dict(
            playbackMode=self.playbackMode.value,
            playlist=[dict(path=str(x.path), artist=x.artist, title=x.title, duration=x.duration)
                      for x in self.playlist],
            volume=self.volume,
            currentIndex=self.currentIndex,
            sortBy=self.sortBy,
            sortOrder=self.sortOrder
        )
        jt = json.dumps(jd, indent=4, ensure_ascii=False)
        self.configPath.write_text(jt)


class MusicEntry(object):

    def __init__(self, path, artist, title, duration) -> None:
        self.path: pathlib.PosixPath = path
        self.artist: str = artist
        self.title: str = title
        self.duration: int = duration


def parseLyric(text: str):
    regex = re.compile(r'((\[\d{2}:\d{2}.\d{2}])+)(.+)')
    lyric: Dict[int, str] = dict()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'(\d{2})\d]', '\\1]', line)
        match = regex.match(line)
        if not match:
            continue
        timePart = match.groups()[0]
        lyricPart = match.groups()[2].strip()
        for i in range(0, len(timePart), 10):
            thisTime = timePart[i:i + 10]
            minutes, seconds = thisTime[1:-1].split(':')
            milliseconds = int((int(minutes) * 60 + float(seconds)) * 1000)
            lyric[milliseconds] = lyricPart
    return lyric


class LoadPlaylistTask(QtCore.QThread):
    musicFoundSignal = QtCore.Signal(tuple)
    musicsFoundSignal = QtCore.Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.musicFiles: List[pathlib.Path] = list()

    def run(self) -> None:
        print("Loading playlist...")
        count = len(self.musicFiles)
        musics = list()
        for index, f in enumerate(self.musicFiles):
            artist, title = 'Unknown', 'Unknown'
            if '-' in f.stem:
                artist, title = f.stem.rsplit('-', maxsplit=1)
            file = taglib.File(str(f))
            artist = file.tags.get('ARTIST', [artist])[0]
            title = file.tags.get('TITLE', [title])[0]
            duration = file.length * 1000
            musicEntry = MusicEntry(path=f, artist=artist, title=title, duration=duration)
            time.sleep(0.0001)
            musics.append((musicEntry, count, index + 1))
            if len(musics) == 10:
                self.musicsFoundSignal.emit(musics)
                musics = list()
        if len(musics) > 0:
            self.musicsFoundSignal.emit(musics)


class MyQSlider(QtWidgets.QSlider):

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == QtCore.Qt.LeftButton:
            self.setValue(self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
            ev.accept()
        super().mousePressEvent(ev)


class MyQLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.clicked.emit(ev)


class MyPlaylist(QtCore.QObject):
    currentIndexChanged = QtCore.Signal(int)
    volumeChanged = QtCore.Signal(int)
    playingChanged = QtCore.Signal(bool)
    positionChanged = QtCore.Signal(int)
    durationChanged = QtCore.Signal(int)

    class PlaybackMode(Enum):
        LOOP = 1
        RANDOM = 2

    def __init__(self) -> None:
        super().__init__()
        self.player = QtMultimedia.QMediaPlayer()
        self.playlist = QtMultimedia.QMediaPlaylist()
        self.musics: List[MusicEntry] = list()
        self.currentIndex = -1
        self.playbackMode = MyPlaylist.PlaybackMode.LOOP
        self.playing = False
        self.player.positionChanged.connect(self.positionChanged.emit)
        self.player.durationChanged.connect(self.durationChanged.emit)
        self.player.stateChanged.connect(self.onPlayerStateChanged)
        self.history: Dict[int, int] = dict()
        self.historyIndex = -1

    def onPlayerStateChanged(self, state):
        print("STATE CHANGED")
        if state == QtMultimedia.QMediaPlayer.StoppedState:
            print("STOPPED")
            self.next()
            self.play()

    def addMusic(self, music: MusicEntry):
        self.musics.append(music)

    def removeMusic(self, index):
        del self.musics[index]

    def clear(self):
        self.musics.clear()

    def music(self, index):
        return self.musics[index]

    def play(self):
        if self.musicCount() == 0:
            return
        if self.currentIndex == -1:
            self.setCurrentIndex(0)
        self.player.play()
        self.playing = True
        self.playingChanged.emit(self.playing)

    def pause(self):
        self.player.pause()
        self.playing = False
        self.playingChanged.emit(self.playing)

    def previous(self):
        if self.musicCount() == 0:
            self.setCurrentIndex(-1)
        elif self.playbackMode == self.PlaybackMode.LOOP:
            self.setCurrentIndex(self.currentIndex - 1 if self.currentIndex > 0 else self.musicCount() - 1)
        else:
            self.historyIndex -= 1
            if (self.historyIndex not in self.history) or self.history[self.historyIndex] >= self.musicCount():
                self.history[self.historyIndex] = self.nextRandomIndex()
            self.setCurrentIndex(self.history[self.historyIndex])

    def next(self):
        if self.musicCount() == 0:
            self.setCurrentIndex(-1)
        elif self.playbackMode == self.PlaybackMode.LOOP:
            self.setCurrentIndex(self.currentIndex + 1 if self.currentIndex < self.musicCount() - 1 else 0)
        else:
            self.historyIndex += 1
            if (self.historyIndex not in self.history) or self.history[self.historyIndex] >= self.musicCount():
                self.history[self.historyIndex] = self.nextRandomIndex()
            self.setCurrentIndex(self.history[self.historyIndex])

    def nextRandomIndex(self):
        currentIndex = self.currentIndex
        nextIndex = random.randint(0, self.musicCount() - 1)
        while self.musicCount() > 1 and nextIndex == currentIndex:
            nextIndex = random.randint(0, self.musicCount() - 1)
        return nextIndex

    def musicCount(self):
        return len(self.musics)

    def setCurrentIndex(self, index):
        self.currentIndex = index
        if index > -1:
            music = self.musics[index]
            self.player.blockSignals(True)
            self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(str(music.path))))
            self.player.blockSignals(False)
            if self.historyIndex == -1 and len(self.history) == 0:
                self.history[self.historyIndex] = index
        else:
            self.player.blockSignals(True)
            self.player.stop()
            self.player.blockSignals(False)
        self.currentIndexChanged.emit(index)

    def getPlaybackMode(self):
        return self.playbackMode

    def setPlaybackMode(self, mode):
        self.playbackMode = mode

    def getVolume(self):
        return self.player.volume()

    def setVolume(self, volume):
        self.player.setVolume(volume)
        self.volumeChanged.emit(volume)

    def getPosition(self):
        return self.player.position()

    def setPosition(self, position):
        self.player.setPosition(position)

    def getDuration(self):
        return self.player.duration()

    def isPlaying(self):
        return self.playing

    def indexOf(self, music: MusicEntry):
        return self.musics.index(music)


# noinspection PyAttributeOutsideInit
class PlayerWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.playButton: QtWidgets.QToolButton
        self.prevButton: QtWidgets.QToolButton
        self.nextButton: QtWidgets.QToolButton
        self.playbackModeButton: QtWidgets.QToolButton
        self.progressSlider: MyQSlider
        self.progressLabel: QtWidgets.QLabel
        self.volumeDial: QtWidgets.QDial
        self.playlistWidget: QtWidgets.QTableWidget
        self.lyricWrapper: QtWidgets.QScrollArea
        self.lyricLabel: MyQLabel
        self.progressDialog: QtWidgets.QProgressDialog
        self.myPlaylist: MyPlaylist = MyPlaylist()
        self.loadPlaylistTask = LoadPlaylistTask()
        self.musics: List[MusicEntry] = list()
        self.lyric: Dict[int, str] = dict()
        self.prevLyricIndex = -1
        self.config: Config
        self.realRow = -1
        self.mimeDb = QtCore.QMimeDatabase()
        self.setupLayout()
        self.setupEvents()
        self.setupPlayer()

    def generateToolButton(self, iconName: str) -> QtWidgets.QToolButton:
        button = QtWidgets.QToolButton(parent=self)
        button.setIcon(qtawesome.icon(iconName))
        button.setIconSize(QtCore.QSize(50, 50))
        button.setAutoRaise(True)
        return button

    # noinspection DuplicatedCode
    def setupEvents(self):
        self.loadPlaylistTask.musicFoundSignal.connect(self.addMusic)
        self.loadPlaylistTask.musicsFoundSignal.connect(self.addMusics)
        self.playButton.clicked.connect(self.togglePlay)
        self.prevButton.clicked.connect(self.onPlayPrevious)
        self.nextButton.clicked.connect(self.onPlayNext)
        self.playbackModeButton.clicked.connect(lambda: self.onPlaybackModeButtonClicked())
        self.progressSlider.valueChanged.connect(self.onProgressSliderValueChanged)
        self.volumeDial.valueChanged.connect(self.onVolumeDialValueChange)
        self.myPlaylist.playingChanged.connect(self.onPlayingChanged)
        self.myPlaylist.positionChanged.connect(self.onPlayerPositionChanged)
        self.myPlaylist.durationChanged.connect(self.onPlayerDurationChanged)
        self.myPlaylist.currentIndexChanged.connect(self.onPlaylistCurrentIndexChanged)
        self.playlistWidget.doubleClicked.connect(self.dblClicked)
        self.lyricLabel.clicked.connect(self.onLyricClicked)

    # noinspection PyUnresolvedReferences
    def onLyricClicked(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            if self.lyric is None:
                return
            loc = self.lyricLabel.mapFromGlobal(self.lyricLabel.cursor().pos())
            line = len(self.lyric) * loc.y() // self.lyricLabel.height()
            print("clicked", line)
            position = sorted(self.lyric.items())[line][0]
            self.myPlaylist.setPosition(position)

    def onPlayNext(self):
        self.myPlaylist.next()
        self.myPlaylist.play()

    def onPlayPrevious(self):
        self.myPlaylist.previous()
        self.myPlaylist.play()

    def onVolumeDialValueChange(self, value):
        self.setVolume(value)
        self.config.volume = value
        self.config.persist()

    def setVolume(self, volume):
        self.volumeDial.blockSignals(True)
        self.myPlaylist.setVolume(volume)
        self.volumeDial.setValue(volume)
        self.volumeDial.blockSignals(False)

    def onPlaybackModeButtonClicked(self):
        if self.myPlaylist.getPlaybackMode() == MyPlaylist.PlaybackMode.RANDOM:
            self.setPlaybackMode(MyPlaylist.PlaybackMode.LOOP)
        else:
            self.setPlaybackMode(MyPlaylist.PlaybackMode.RANDOM)
        self.config.persist()

    def setPlaybackMode(self, playbackMode: MyPlaylist.PlaybackMode):
        self.config.playbackMode = playbackMode
        if playbackMode == MyPlaylist.PlaybackMode.LOOP:
            self.myPlaylist.setPlaybackMode(MyPlaylist.PlaybackMode.LOOP)
            self.playbackModeButton.setIcon(qtawesome.icon("mdi.repeat"))
        else:
            self.myPlaylist.setPlaybackMode(MyPlaylist.PlaybackMode.RANDOM)
            self.playbackModeButton.setIcon(qtawesome.icon("mdi.shuffle"))

    def onProgressSliderValueChanged(self, value):
        self.myPlaylist.setPosition(value * 1000)

    def onPlayingChanged(self, playing: bool):
        if playing:
            self.playButton.setIcon(qtawesome.icon("mdi.pause"))
        else:
            self.playButton.setIcon(qtawesome.icon("mdi.play"))

    def onPlayerPositionChanged(self, position: int):
        current = position // 1000
        total = self.myPlaylist.getDuration() // 1000
        self.progressLabel.setText(
            '{:02d}:{:02d}/{:02d}:{:02d}'.format(current // 60, current % 60, total // 60, total % 60))
        self.progressSlider.blockSignals(True)
        self.progressSlider.setValue(current)
        self.progressSlider.blockSignals(False)
        self.refreshLyric()

    def onPlayerDurationChanged(self, duration: int):
        total = duration // 1000
        self.progressSlider.setMaximum(total)

    def onPlaylistCurrentIndexChanged(self, index):
        print("Playlist index changed: {}".format(index))
        self.config.currentIndex = index
        self.config.persist()
        if index == -1:
            self.lyric = None
            self.lyricLabel.setText("<center><em>No music</em></center>")
            self.setWindowTitle('')
            return
        self.progressSlider.setValue(0)
        self.playlistWidget.selectRow(index)
        self.prevLyricIndex = -1
        music = self.myPlaylist.music(index)
        self.setWindowTitle('{} - {}'.format(music.artist, music.title))
        musicFile = music.path
        lyricFile: pathlib.PosixPath = musicFile.parent / (musicFile.stem + '.lrc')
        if lyricFile.exists():
            bys = lyricFile.read_bytes()
            encoding = chardet.detect(bys)['encoding']
            try:
                lyricText = str(bys, encoding='GB18030')
            except UnicodeDecodeError:
                lyricText = str(bys, encoding=encoding)
            self.lyric = parseLyric(lyricText)
            if len(self.lyric) > 0:
                self.refreshLyric()
            else:
                self.lyric = None
        else:
            self.lyric = None
            print("Lyric file not found.")

    def refreshLyric(self):
        hbar = self.lyricWrapper.horizontalScrollBar()
        hbar.hide()
        self.lyricWrapper.horizontalScrollBar().setValue((hbar.maximum() + hbar.minimum()) // 2)
        if self.lyric is None:
            self.lyricLabel.setText("<center><em>Lyric not found or not supported</em></center>")
            return
        currentLyricIndex = self.calcCurrentLyricIndex()
        if currentLyricIndex == self.prevLyricIndex:
            return
        self.prevLyricIndex = currentLyricIndex
        text = ''
        for i, (k, v) in enumerate(sorted(self.lyric.items())):
            if i == currentLyricIndex:
                text += '<center><b>{}</b></center>'.format(v)
            else:
                text += '<center>{}</center>'.format(v)
        self.lyricLabel.setText(text)
        self.lyricWrapper.verticalScrollBar().setValue(
            self.lyricLabel.height() * currentLyricIndex // len(self.lyric)
            - self.lyricWrapper.height() // 2
        )
        self.lyricWrapper.horizontalScrollBar().setValue((hbar.maximum() + hbar.minimum()) // 2)

    # noinspection PyTypeChecker
    def calcCurrentLyricIndex(self):
        entries: List[Tuple[int, str]] = sorted(self.lyric.items())
        currentPosition = self.myPlaylist.getPosition()
        if currentPosition < entries[0][0]:
            return 0
        for i in range(len(self.lyric) - 1):
            entry = entries[i]
            nextEntry = entries[i + 1]
            if entry[0] <= currentPosition < nextEntry[0]:
                return i
        return len(self.lyric) - 1

    def togglePlay(self):
        if self.myPlaylist.isPlaying():
            self.myPlaylist.pause()
        else:
            self.myPlaylist.play()

    def setupPlayer(self):
        self.config = Config.load()
        self.setPlaybackMode(self.config.playbackMode)
        self.setVolume(self.config.volume)
        sortBy = dict(ARTIST=0, TITLE=1, DURATION=2)[self.config.sortBy]
        sortOrder = QtCore.Qt.AscendingOrder if self.config.sortOrder == 'ASCENDING' else QtCore.Qt.DescendingOrder
        self.playlistWidget.horizontalHeader().setSortIndicator(sortBy, sortOrder)
        for index, music in enumerate(self.config.playlist):
            self.addMusic((music, len(self.config.playlist), index + 1))
        if len(self.config.playlist) > 0 and self.config.currentIndex >= 0:
            self.myPlaylist.setCurrentIndex(self.config.currentIndex)

    def addMusics(self, musics):
        for music in musics:
            self.addMusic(music)

    def addMusic(self, entry):
        music: MusicEntry = entry[0]
        total: int = entry[1]
        current: int = entry[2]
        self.progressDialog.show()
        if total < 300 or current % 3 == 0:
            self.progressDialog.setMaximum(total)
            self.progressDialog.setValue(current)
            self.progressDialog.setLabelText(music.path.stem + music.path.suffix)
        row = self.playlistWidget.rowCount()
        self.playlistWidget.setSortingEnabled(False)
        self.playlistWidget.insertRow(row)
        self.playlistWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row + 1)))
        self.playlistWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(music.artist))
        self.playlistWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(music.title))
        self.playlistWidget.setItem(row, 3, QtWidgets.QTableWidgetItem(
            '{:02d}:{:02d}'.format(music.duration // 60000, music.duration // 1000 % 60)))
        self.playlistWidget.item(row, 0).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.playlistWidget.item(row, 3).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.playlistWidget.item(row, 0).setData(QtCore.Qt.UserRole, music)
        self.myPlaylist.addMusic(music)
        if current == total:
            self.progressDialog.setValue(total)
            self.playlistWidget.scrollToBottom()
            self.playlistWidget.setSortingEnabled(True)
            lastMusic: MusicEntry = self.playlistWidget.item(current - 1, 0).data(QtCore.Qt.UserRole)
            print("current: {}, last: {}".format(music.title, lastMusic.title))
            self.onSortEnded()

    def dblClicked(self, item: QtCore.QModelIndex):
        self.myPlaylist.setCurrentIndex(item.row())
        self.myPlaylist.play()

    def setupLayout(self):
        self.playButton = self.generateToolButton('mdi.play')
        self.prevButton = self.generateToolButton('mdi.step-backward')
        self.nextButton = self.generateToolButton('mdi.step-forward')
        self.playbackModeButton = self.generateToolButton('mdi.shuffle')
        self.progressSlider = MyQSlider(QtCore.Qt.Horizontal, self)
        self.progressLabel = QtWidgets.QLabel('00:00/00:00', self)
        self.volumeDial = QtWidgets.QDial(self)
        self.volumeDial.setFixedSize(50, 50)
        self.playlistWidget = QtWidgets.QTableWidget(0, 4, self)
        self.playlistWidget.setHorizontalHeaderLabels(('Index', 'Artist', 'Title', 'Duration'))
        self.playlistWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.playlistWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.playlistWidget.horizontalHeader().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.playlistWidget.horizontalHeader().sectionClicked.connect(self.onSortEnded)
        self.playlistWidget.horizontalHeader().setHighlightSections(False)
        self.playlistWidget.horizontalHeader().setStretchLastSection(True)
        self.playlistWidget.horizontalHeader().setStyleSheet(HEADER_STYLE)
        self.playlistWidget.verticalHeader().hide()
        self.playlistWidget.setColumnWidth(0, 50)
        self.playlistWidget.setColumnWidth(1, 150)
        self.playlistWidget.setColumnWidth(2, 250)
        self.playlistWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.playlistWidget.customContextMenuRequested.connect(self.onRequestContextMenu)
        self.playlistWidget.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.playlistWidget.setShowGrid(False)
        self.playlistWidget.setAlternatingRowColors(True)
        self.lyricWrapper = QtWidgets.QScrollArea(self)
        self.lyricLabel = MyQLabel('<center>Hello, World!</center>')
        font = self.lyricLabel.font()
        font.setPointSize(18)
        self.lyricLabel.setFont(font)
        self.lyricWrapper.setWidget(self.lyricLabel)
        self.lyricWrapper.setWidgetResizable(True)
        self.lyricWrapper.verticalScrollBar().hide()
        self.lyricWrapper.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.initProgressDialog()

        contentLayout = QtWidgets.QSplitter()
        contentLayout.addWidget(self.playlistWidget)
        contentLayout.addWidget(self.lyricWrapper)
        contentLayout.setSizes([1, 1])

        controllerLayout = QtWidgets.QHBoxLayout()
        controllerLayout.setSpacing(5)
        controllerLayout.addWidget(self.playButton)
        controllerLayout.addWidget(self.prevButton)
        controllerLayout.addWidget(self.nextButton)
        controllerLayout.addWidget(self.progressSlider)
        controllerLayout.addWidget(self.progressLabel)
        controllerLayout.addWidget(self.playbackModeButton)
        controllerLayout.addWidget(self.volumeDial)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Plain)
        line.setStyleSheet("color: #D8D8D8")
        line2 = QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setFrameShadow(QtWidgets.QFrame.Plain)
        line2.setStyleSheet("color: #D8D8D8")

        rootLayout = QtWidgets.QVBoxLayout(self)
        rootLayout.setSpacing(0)
        rootLayout.addWidget(line)
        rootLayout.addWidget(contentLayout)
        rootLayout.addWidget(line2)
        rootLayout.addLayout(controllerLayout)
        rootLayout.setMargin(0)
        self.setLayout(rootLayout)
        self.resize(1280, 720)
        self.setAcceptDrops(True)

    def onRequestContextMenu(self):
        print("Requesting...")
        menu = QtWidgets.QMenu()
        menu.addAction("Delete")
        menu.triggered.connect(self.removeMusic)
        menu.exec_(QtGui.QCursor.pos())
        menu.clear()

    def removeMusic(self):
        currentIndex = self.myPlaylist.currentIndex
        playing = self.myPlaylist.isPlaying()
        indices = sorted(list(set([x.row() for x in self.playlistWidget.selectedIndexes()])), reverse=True)
        for index in indices:
            self.myPlaylist.removeMusic(index)
            self.playlistWidget.removeRow(index)
            print("Removing index={}, currentIndex={}".format(index, currentIndex))
        self.config.persist()
        if currentIndex in indices:
            if self.myPlaylist.musicCount() > 0:
                self.myPlaylist.next()
            else:
                self.myPlaylist.setCurrentIndex(-1)
            if playing:
                self.myPlaylist.play()

    def initProgressDialog(self):
        self.progressDialog = QtWidgets.QProgressDialog(self)
        # noinspection PyTypeChecker
        self.progressDialog.setCancelButton(None)
        self.progressDialog.setWindowTitle("Loading music")
        self.progressDialog.setFixedSize(444, 150)
        self.progressDialog.setModal(True)
        self.progressDialog.setValue(100)

    def onSortEnded(self):
        self.myPlaylist.clear()
        for row in range(self.playlistWidget.rowCount()):
            music: MusicEntry = self.playlistWidget.item(row, 0).data(QtCore.Qt.UserRole)
            self.myPlaylist.addMusic(music)
        self.config.playlist = self.myPlaylist.musics
        self.config.sortBy = {0: 'ARTIST', 1: 'TITLE', 2: 'DURATION'}[
            self.playlistWidget.horizontalHeader().sortIndicatorSection()]
        self.config.sortOrder = 'ASCENDING' if \
            self.playlistWidget.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder else 'DESCENDING'
        self.config.persist()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        if self.lyric:
            self.prevLyricIndex = -1
            self.refreshLyric()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        urls: List[QtCore.QUrl] = event.mimeData().urls()
        paths = [pathlib.Path(x.toLocalFile()) for x in urls if
                 self.mimeDb.mimeTypeForUrl(x).name().startswith('audio/')]
        self.loadPlaylistTask.musicFiles = paths
        self.loadPlaylistTask.start()
        self.initProgressDialog()


HEADER_STYLE = """
QHeaderView::section {
    border-top:0px solid #D8D8D8;
    border-left:1px solid #D8D8D8;
    border-right:0px solid #D8D8D8;
    border-bottom: 1px solid #D8D8D8;
    background-color:white;
    padding:2px;
    font-weight: light;
}
""".strip()


def main():
    app = QtWidgets.QApplication()
    app.setApplicationName('Ice Spring Music Player')
    app.setApplicationDisplayName('Ice Spring Music Player')
    app.setWindowIcon(qtawesome.icon("mdi.music"))
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor.fromRgb(255, 255, 255))
    app.setPalette(palette)
    window = PlayerWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
