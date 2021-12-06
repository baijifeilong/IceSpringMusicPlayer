# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52
import logging
import re
from pathlib import Path
from typing import Dict

import colorlog
from PySide2 import QtWidgets, QtCore, QtGui, QtMultimedia


class MySlider(QtWidgets.QSlider):
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        event.button() == QtCore.Qt.LeftButton and self.setValue(self.minimum() + (self.maximum() - self.minimum()) * event.x() // self.width())
        super().mousePressEvent(event)


def onPlaylistTableDoubleClicked(modelIndex: QtCore.QModelIndex):
    indexCellIndex = playlistModel.index(modelIndex.row(), 0, modelIndex.parent())
    indexCell = playlistModel.itemFromIndex(indexCellIndex)
    musicPath: Path = indexCell.data(QtCore.Qt.UserRole)
    lyricsPath = musicPath.with_suffix(".lrc")
    lyricsText = lyricsPath.read_text()
    lyricDict = parseLyrics(lyricsText)
    lyricsLabel.setText("\n".join(lyricDict.values()))
    player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(str(musicPath))))
    player.play()


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


consolePattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-10s %(message)s"
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().handlers[-1].setFormatter(colorlog.ColoredFormatter(consolePattern))
logging.getLogger().setLevel(logging.DEBUG)

app = QtWidgets.QApplication()
app.setApplicationName("Ice Spring Music Player")
app.setApplicationDisplayName(app.applicationName())

mainWindow = QtWidgets.QMainWindow()
mainWindow.show()
mainWindow.resize(1280, 720)
mainWidget = QtWidgets.QWidget(mainWindow)
mainWindow.setCentralWidget(mainWidget)

mainLayout = QtWidgets.QVBoxLayout(mainWidget)
mainWidget.setLayout(mainLayout)
mainSplitter = QtWidgets.QSplitter(mainWidget)
controlsLayout = QtWidgets.QHBoxLayout(mainWidget)
mainLayout.addWidget(mainSplitter)
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
lyricsLabel = QtWidgets.QLabel("Ready.", lyricsContainer)
lyricsContainer.setWidget(lyricsLabel)
lyricsContainer.setWidgetResizable(True)
mainSplitter.addWidget(playlistTable)
mainSplitter.addWidget(lyricsContainer)
mainSplitter.setSizes([1, 1])

playButton = QtWidgets.QPushButton("Play", mainWidget)
stopButton = QtWidgets.QPushButton("Stop", mainWidget)
progressSlider = MySlider(QtCore.Qt.Horizontal, mainWidget)
progressSlider.valueChanged.connect(lambda x: [player.blockSignals(True), player.setPosition(x), player.blockSignals(False)])
controlsLayout.addWidget(playButton)
controlsLayout.addWidget(stopButton)
controlsLayout.addWidget(progressSlider)

player = QtMultimedia.QMediaPlayer(app)
player.durationChanged.connect(progressSlider.setMaximum)
player.positionChanged.connect(lambda x: [progressSlider.blockSignals(True), progressSlider.setValue(x), progressSlider.blockSignals(False)])

for index, path in enumerate(list(Path("~/Music").expanduser().glob("**/*.mp3"))[:20]):
    parts = [x.strip() for x in path.with_suffix("").name.rsplit("-", maxsplit=1)]
    artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
    indexCell = QtGui.QStandardItem(str(index + 1))
    indexCell.setData(path, QtCore.Qt.UserRole)
    artistCell = QtGui.QStandardItem(artist)
    titleCell = QtGui.QStandardItem(title)
    playlistModel.appendRow([indexCell, artistCell, titleCell])

app.exec_()
