# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52

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


consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-10s %(message)s"
logging.getLogger().handlers = [logging.StreamHandler()]
logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
logging.getLogger().setLevel(logging.DEBUG)
lyricsLogger = logging.getLogger("lyrics")
lyricsLogger.setLevel(logging.INFO)
positionLogger = logging.getLogger("position")
positionLogger.setLevel(logging.INFO)

app = QtWidgets.QApplication()
app.setApplicationName("Ice Spring Music Player")
app.setApplicationDisplayName(app.applicationName())
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Window, QtGui.QColor.fromRgb(250, 250, 250))
app.setPalette(palette)

mainWindow = QtWidgets.QMainWindow()
mainWindow.resize(1280, 720)
mainWidget = QtWidgets.QWidget(mainWindow)
mainWindow.setCentralWidget(mainWidget)
mainWindow.show()

lines = [QtWidgets.QFrame(mainWindow) for _ in range(2)]
for line in lines:
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Plain)
    line.setStyleSheet("color: #D8D8D8")
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

playlistTable = QtWidgets.QTableView(mainSplitter)
playlistModel = QtGui.QStandardItemModel(0, 3)
playlistModel.setHorizontalHeaderLabels(["", "Artist", "Title"])
playlistTable.setModel(playlistModel)
playlistTable.setColumnWidth(0, 100)
playlistTable.setColumnWidth(1, 200)
playlistTable.setColumnWidth(2, 300)
playlistTable.setColumnHidden(0, True)
playlistTable.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
playlistTable.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
playlistTable.horizontalHeader().setStretchLastSection(True)
playlistTable.doubleClicked.connect(lambda x: playlist.setCurrentIndex(x.row()) or player.play())
playlistTable.setAlternatingRowColors(True)
playlistTable.setStyleSheet("alternate-background-color: rgb(245, 245, 245)")
playlistTable.setFrameShape(QtWidgets.QFrame.NoFrame)
playlistTable.setShowGrid(False)
playlistTable.setItemDelegate(NoFocusDelegate())
playlistTable.horizontalHeader().setStyleSheet(
    "QHeaderView::section { border-top:0px solid #D8D8D8; border-bottom: 1px solid #D8D8D8; "
    "background-color:white; padding:2px; font-weight: light; }")
tablePalette = playlistTable.palette()
tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
    tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight))
tablePalette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText,
    tablePalette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
playlistTable.setPalette(tablePalette)

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
mainSplitter.addWidget(playlistTable)
mainSplitter.addWidget(lyricsContainer)
mainSplitter.setSizes([1, 1])
lyricsContainer.horizontalScrollBar().hide()

playButton = QtWidgets.QToolButton(mainWidget)
playButton.setIcon(qtawesome.icon("mdi.play"))
playButton.clicked.connect(lambda: (
    player.pause() if player.state() == QtMultimedia.QMediaPlayer.PlayingState else player.play()))
stopButton = QtWidgets.QToolButton(mainWidget)
stopButton.setIcon(qtawesome.icon("mdi.stop"))
stopButton.clicked.connect(lambda: player.stop())
previousButton = QtWidgets.QToolButton(mainWidget)
previousButton.setIcon(qtawesome.icon("mdi.step-backward"))
previousButton.clicked.connect(lambda: playlist.previous() or player.play())
nextButton = QtWidgets.QToolButton(mainWidget)
nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
nextButton.clicked.connect(lambda: playlist.next() or player.play())
playbackButton = QtWidgets.QToolButton(mainWidget)
playbackButton.setIcon(qtawesome.icon("mdi.repeat"))
playbackButton.clicked.connect(lambda: playlist.setPlaybackMode(
    QtMultimedia.QMediaPlaylist.PlaybackMode.Random
    if playlist.playbackMode() == QtMultimedia.QMediaPlaylist.PlaybackMode.Loop
    else QtMultimedia.QMediaPlaylist.PlaybackMode.Loop))
for button in playButton, stopButton, previousButton, nextButton, playbackButton:
    button.setIconSize(QtCore.QSize(50, 50))
    button.setAutoRaise(True)

progressSlider = MySlider(QtCore.Qt.Horizontal, mainWidget)
progressSlider.valueChanged.connect(lambda x: [player.blockSignals(True), player.setPosition(x),
    player.blockSignals(False)])
progressLabel = QtWidgets.QLabel("00:00/00:00", mainWidget)
controlsLayout.addWidget(playButton)
controlsLayout.addWidget(stopButton)
controlsLayout.addWidget(previousButton)
controlsLayout.addWidget(nextButton)
controlsLayout.addWidget(progressSlider)
controlsLayout.addWidget(progressLabel)
controlsLayout.addWidget(playbackButton)

playlist = QtMultimedia.QMediaPlaylist()
playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.PlaybackMode.Loop)
player = QtMultimedia.QMediaPlayer(app)
player.setPlaylist(playlist)
playlist.currentIndexChanged.connect(lambda x: onPlaylistIndexChanged(x))
playlist.playbackModeChanged.connect(lambda x: playbackButton.setIcon(qtawesome.icon(
    "mdi.repeat" if x == QtMultimedia.QMediaPlaylist.PlaybackMode.Loop else "mdi.shuffle")))
player.durationChanged.connect(lambda x: x != -1 and [
    logging.info("Duration changed: %s (%s)", formatDelta(player.duration()), formatDelta(currentRealDuration())),
    progressSlider.setMaximum(x)])
player.positionChanged.connect(lambda x: onPlayerPositionChanged(x))
player.stateChanged.connect(lambda x: playButton.setIcon(qtawesome.icon(
    "mdi.pause" if x == QtMultimedia.QMediaPlayer.PlayingState else "mdi.play")))

for index, path in enumerate(list(Path("~/Music").expanduser().glob("**/*.mp3"))[:200]):
    parts = [x.strip() for x in path.with_suffix("").name.rsplit("-", maxsplit=1)]
    artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
    indexCell = QtGui.QStandardItem(str(index + 1))
    indexCell.setData(path, QtCore.Qt.UserRole)
    artistCell = QtGui.QStandardItem(artist)
    titleCell = QtGui.QStandardItem(title)
    playlistModel.appendRow([indexCell, artistCell, titleCell])
    playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(str(path))))


def formatDelta(milliseconds):
    seconds = int(milliseconds) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def calcRealDuration(musicPath):
    return musicPath.stat().st_size * 8 // taglib.File(str(musicPath)).bitrate


def currentRealDuration():
    return calcRealDuration(Path(player.currentMedia().canonicalUrl().toLocalFile()))


def currentBugRate():
    filename = playlist.media(playlist.currentIndex()).canonicalUrl().toLocalFile()
    return player.duration() / calcRealDuration(Path(filename))


def clearLayout(layout: QtWidgets.QLayout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() else layout.removeItem(layout.itemAt(i))


def onPlaylistIndexChanged(index):
    musicPath: Path = Path(playlist.media(index).canonicalUrl().toLocalFile())
    logging.info(">>> Playlist index changed: %d => %s", index, musicPath)
    mainWindow.setWindowTitle(musicPath.with_suffix("").name)
    playlistTable.selectRow(index)
    setupLyrics(musicPath)


def onPlayerPositionChanged(position):
    positionLogger.debug("Position changed: %d", position)
    progressSlider.blockSignals(True)
    progressSlider.setValue(position)
    progressSlider.blockSignals(False)
    progressLabel.setText(
        f"{formatDelta(position / currentBugRate())}/{formatDelta(player.duration() / currentBugRate())}")
    refreshLyrics(position)


def setupLyrics(musicPath):
    player.setProperty("previousLyricIndex", -1)
    lyricsPath = musicPath.with_suffix(".lrc")
    lyricsText = lyricsPath.read_text()
    lyricDict = parseLyrics(lyricsText)
    player.setProperty("lyricDict", lyricDict)
    clearLayout(lyricsLayout)
    lyricsLayout.addSpacing(lyricsContainer.height() // 2)
    for position, lyric in list(lyricDict.items())[:]:
        lyricLabel = ClickableLabel(lyric, lyricsContainer)
        lyricLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        lyricLabel.clicked.connect(lambda _, position=position: player.setPosition(position * currentBugRate()))
        font = lyricLabel.font()
        font.setFamily("等线")
        font.setPointSize(12)
        lyricLabel.setFont(font)
        lyricLabel.setMargin(2)
        lyricsLayout.addWidget(lyricLabel)
    lyricsLayout.addSpacing(lyricsContainer.height() // 2)
    lyricsContainer.verticalScrollBar().setValue(0)
    lyricsContainer.horizontalScrollBar().setValue(
        (lyricsContainer.horizontalScrollBar().maximum() + lyricsContainer.horizontalScrollBar().minimum()) // 2)
    refreshLyrics(0)


def refreshLyrics(position):
    lyricDict = player.property("lyricDict")
    previousLyricIndex = player.property("previousLyricIndex")
    lyricIndex = calcPositionIndex(math.ceil(position / currentBugRate()), list(lyricDict.keys()))
    if lyricIndex == previousLyricIndex:
        return
    player.setProperty("previousLyricIndex", lyricIndex)
    for index in range(len(lyricDict)):
        lyricLabel: QtWidgets.QLabel = lyricsLayout.itemAt(index + 1).widget()
        lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
        originalValue = lyricsContainer.verticalScrollBar().value()
        targetValue = lyricLabel.pos().y() - lyricsContainer.height() // 2 + lyricLabel.height() // 2
        QtCore.QPropertyAnimation().start(QtCore.QPropertyAnimation.DeleteWhenStopped)
        index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
            lyricsContainer.verticalScrollBar(), b"value", lyricsContainer): [
            animation.setStartValue(originalValue),
            animation.setEndValue(targetValue),
            animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        ])()


def calcPositionIndex(position, positions):
    for index in range(len(positions) - 1):
        if positions[index] <= position < positions[index + 1]:
            return index
    return 0 if position < positions[0] else len(positions) - 1


def parseLyrics(lyricsText: str) -> Dict[int, str]:
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


app.exec_()
