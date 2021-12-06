# Created by BaiJiFeiLong@gmail.com at 2021/12/6 12:52

from PySide2 import QtWidgets, QtCore

app = QtWidgets.QApplication()
app.setApplicationName("Ice Spring Music Player")
app.setApplicationDisplayName(app.applicationName())

mainWindow = QtWidgets.QMainWindow()
mainWindow.show()
mainWindow.resize(640, 360)
mainWidget = QtWidgets.QWidget(mainWindow)
mainWindow.setCentralWidget(mainWidget)

mainLayout = QtWidgets.QVBoxLayout(mainWidget)
mainWidget.setLayout(mainLayout)
mainSplitter = QtWidgets.QSplitter(mainWidget)
controlsLayout = QtWidgets.QHBoxLayout(mainWidget)
mainLayout.addWidget(mainSplitter)
mainLayout.addLayout(controlsLayout)

playlistTable = QtWidgets.QTableWidget(mainSplitter)
lyricsContainer = QtWidgets.QScrollArea(mainSplitter)
mainSplitter.addWidget(playlistTable)
mainSplitter.addWidget(lyricsContainer)
mainSplitter.setSizes([1, 1])

playButton = QtWidgets.QPushButton("Play", mainWidget)
stopButton = QtWidgets.QPushButton("Stop", mainWidget)
progressSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, mainWidget)
controlsLayout.addWidget(playButton)
controlsLayout.addWidget(stopButton)
controlsLayout.addWidget(progressSlider)

app.exec_()
