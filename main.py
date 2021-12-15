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


def formatDelta(milliseconds):
    seconds = int(milliseconds) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def calcRealDuration(musicPath):
    return musicPath.stat().st_size * 8 // taglib.File(str(musicPath)).bitrate


def currentRealDuration():
    return calcRealDuration(Path(player.currentMedia().canonicalUrl().toLocalFile()))


def currentBugRate():
    return player.duration() / calcRealDuration(Path(player.currentMedia().canonicalUrl().toLocalFile()))


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal(QtGui.QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.clicked.emit(ev)


class MySlider(QtWidgets.QSlider):
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.button() == QtCore.Qt.LeftButton and self.setValue(self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
        super().mousePressEvent(ev)


def clearLayout(layout: QtWidgets.QLayout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() else layout.removeItem(layout.itemAt(i))


def onPlaylistTableDoubleClicked(modelIndex: QtCore.QModelIndex):
    indexCellIndex = playlistModel.index(modelIndex.row(), 0, modelIndex.parent())
    indexCell = playlistModel.itemFromIndex(indexCellIndex)
    musicPath: Path = indexCell.data(QtCore.Qt.UserRole)
    logging.info("Current music file: %s", musicPath)
    setupLyrics(musicPath)
    player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(str(musicPath))))
    player.play()


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
        font.setPointSize(12)
        lyricLabel.setFont(font)
        lyricsLayout.addWidget(lyricLabel)
    lyricsLayout.addSpacing(lyricsContainer.height() // 2)


def refreshLyrics():
    lyricDict = player.property("lyricDict")
    previousLyricIndex = player.property("previousLyricIndex")
    lyricIndex = calcPositionIndex(math.ceil(player.position() / currentBugRate()), list(lyricDict.keys()))
    if lyricIndex == previousLyricIndex:
        return
    player.setProperty("previousLyricIndex", lyricIndex)
    for index in range(len(lyricDict)):
        lyricLabel: QtWidgets.QLabel = lyricsLayout.itemAt(index + 1).widget()
        lyricText = list(lyricDict.values())[index]
        lyricLabel.setText(f"*{lyricText}*" if index == lyricIndex else lyricText)
        originalValue = lyricsContainer.verticalScrollBar().value()
        targetValue = lyricLabel.pos().y() - lyricsContainer.height() // 2 + lyricLabel.height() // 2
        QtCore.QPropertyAnimation().start(QtCore.QPropertyAnimation.DeleteWhenStopped)
        index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(lyricsContainer.verticalScrollBar(), b"value", lyricsContainer): [
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
    logging.info("Parsing lyrics %s...", lyricsText[:50].replace("\n", r"\n"))
    lyricRegex = re.compile(r"^((?:\[\d+:[\d.]+])+)(.*)$")
    lyricDict: Dict[int, str] = dict()
    lyricLines = [x.strip() for x in lyricsText.splitlines() if x.strip()]
    for index, line in enumerate(lyricLines):
        logging.debug("[%02d/%02d] Lyric line: %s", index + 1, len(lyricLines), line)
        match = lyricRegex.match(line.strip())
        if not match:
            logging.debug("Not valid lyric")
            continue
        timespans, content = [x.strip() for x in match.groups()]
        if not content:
            logging.debug("Lyric is empty")
            continue
        for timespan in timespans.replace("[", " ").replace("]", " ").split():
            logging.debug("Parsed lyric: %s => %s", timespan, content)
            minutes, seconds = [float(x) for x in timespan.split(":")]
            millis = int(minutes * 60000 + seconds * 1000)
            while millis in lyricDict:
                millis += 1
            lyricDict[millis] = content
    logging.info("Total parsed lyric items: %d", len(lyricDict))
    return dict(sorted(lyricDict.items()))


consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-10s %(message)s"
logging.getLogger().handlers = [logging.StreamHandler()]
logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
logging.getLogger().setLevel(logging.INFO)

app = QtWidgets.QApplication()
app.setApplicationName("Ice Spring Music Player")
app.setApplicationDisplayName(app.applicationName())

mainWindow = QtWidgets.QMainWindow()
mainWindow.resize(1280, 720)
mainWidget = QtWidgets.QWidget(mainWindow)
mainWindow.setCentralWidget(mainWidget)

mainLayout = QtWidgets.QVBoxLayout(mainWidget)
mainWidget.setLayout(mainLayout)
mainSplitter = QtWidgets.QSplitter(mainWidget)
controlsLayout = QtWidgets.QHBoxLayout(mainWidget)
mainLayout.addWidget(mainSplitter, 1)
mainLayout.addLayout(controlsLayout)

playlistTable = QtWidgets.QTableView(mainSplitter)
playlistModel = QtGui.QStandardItemModel(0, 3)
playlistTable.setModel(playlistModel)
playlistTable.setColumnWidth(0, 100)
playlistTable.setColumnWidth(1, 200)
playlistTable.setColumnWidth(2, 300)
playlistTable.setColumnHidden(0, True)
playlistTable.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
playlistTable.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
playlistTable.horizontalHeader().setStretchLastSection(True)
playlistTable.doubleClicked.connect(onPlaylistTableDoubleClicked)
lyricsContainer = QtWidgets.QScrollArea(mainSplitter)
lyricsWidget = QtWidgets.QWidget(lyricsContainer)
lyricsLayout = QtWidgets.QVBoxLayout(lyricsWidget)
lyricsLayout.setMargin(0)
lyricsLayout.setSpacing(1)
lyricsWidget.setLayout(lyricsLayout)
lyricsContainer.setWidget(lyricsWidget)
lyricsContainer.setWidgetResizable(True)
lyricsContainer.resizeEvent = lambda x: [
    lyricsLayout.count() and lyricsLayout.itemAt(0).spacerItem().changeSize(0, x.size().height() // 2),
    lyricsLayout.count() and lyricsLayout.itemAt(lyricsLayout.count() - 1).spacerItem().changeSize(0, x.size().height() // 2),
    lyricsLayout.invalidate(),
]
mainSplitter.addWidget(playlistTable)
mainSplitter.addWidget(lyricsContainer)
mainSplitter.setSizes([1, 1])

playButton = QtWidgets.QToolButton(mainWidget)
playButton.setIcon(qtawesome.icon("mdi.play"))
playButton.clicked.connect(lambda: player.pause() if player.state() == QtMultimedia.QMediaPlayer.PlayingState else player.play())
stopButton = QtWidgets.QToolButton(mainWidget)
stopButton.setIcon(qtawesome.icon("mdi.stop"))
stopButton.clicked.connect(lambda: player.stop())
for button in playButton, stopButton:
    button.setIconSize(QtCore.QSize(50, 50))
    button.setAutoRaise(True)

progressSlider = MySlider(QtCore.Qt.Horizontal, mainWidget)
progressSlider.valueChanged.connect(lambda x: [player.blockSignals(True), player.setPosition(x), player.blockSignals(False)])
progressLabel = QtWidgets.QLabel("00:00/00:00", mainWidget)
controlsLayout.addWidget(playButton)
controlsLayout.addWidget(stopButton)
controlsLayout.addWidget(progressSlider)
controlsLayout.addWidget(progressLabel)

player = QtMultimedia.QMediaPlayer(app)
player.durationChanged.connect(progressSlider.setMaximum)
player.durationChanged.connect(lambda x: x > 0 and logging.info("Player duration: %s, real duration: %s", formatDelta(player.duration()), formatDelta(currentRealDuration())))
player.positionChanged.connect(lambda x: [progressSlider.blockSignals(True), progressSlider.setValue(x), progressSlider.blockSignals(False)])
player.positionChanged.connect(lambda x: progressLabel.setText(f"{formatDelta(x / currentBugRate())}/{formatDelta(player.duration() / currentBugRate())}"))
player.positionChanged.connect(lambda: refreshLyrics())

player.stateChanged.connect(lambda x: playButton.setIcon(qtawesome.icon("mdi.pause" if x == QtMultimedia.QMediaPlayer.PlayingState else "mdi.play")))

for index, path in enumerate(list(Path("~/Music/tmp").expanduser().glob("**/*.mp3"))[:200]):
    parts = [x.strip() for x in path.with_suffix("").name.rsplit("-", maxsplit=1)]
    artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
    indexCell = QtGui.QStandardItem(str(index + 1))
    indexCell.setData(path, QtCore.Qt.UserRole)
    artistCell = QtGui.QStandardItem(artist)
    titleCell = QtGui.QStandardItem(title)
    playlistModel.appendRow([indexCell, artistCell, titleCell])

mainWindow.show()
app.exec_()
