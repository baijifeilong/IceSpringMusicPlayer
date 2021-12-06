# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52

from pathlib import Path

from PySide2 import QtWidgets, QtCore, QtGui


def onPlaylistTableDoubleClicked(modelIndex: QtCore.QModelIndex):
    indexCellIndex = playlistModel.index(modelIndex.row(), 0, modelIndex.parent())
    indexCell = playlistModel.itemFromIndex(indexCellIndex)
    musicPath: Path = indexCell.data(QtCore.Qt.UserRole)
    lyricsPath = musicPath.with_suffix(".lrc")
    lyricsText = lyricsPath.read_text()
    print(lyricsText)
    lyricsLabel.setText(lyricsText)


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
progressSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, mainWidget)
controlsLayout.addWidget(playButton)
controlsLayout.addWidget(stopButton)
controlsLayout.addWidget(progressSlider)

for index, path in enumerate(list(Path("~/Music").expanduser().glob("**/*.mp3"))[:20]):
    parts = [x.strip() for x in path.with_suffix("").name.rsplit("-", maxsplit=1)]
    artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
    indexCell = QtGui.QStandardItem(str(index + 1))
    indexCell.setData(path, QtCore.Qt.UserRole)
    artistCell = QtGui.QStandardItem(artist)
    titleCell = QtGui.QStandardItem(title)
    playlistModel.appendRow([indexCell, artistCell, titleCell])

app.exec_()
