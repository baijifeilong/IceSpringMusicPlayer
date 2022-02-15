# Created by BaiJiFeiLong@gmail.com at 2022/2/14 23:14
import logging

import qtawesome
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.app import App


class ControllerToolBar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("controllerToolBar")
        self._player = App.instance().getPlayer()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._player.stateChanged.connect(self._refreshView)
        self._playButton.clicked.connect(self._player.togglePlayPause)
        self._stopButton.clicked.connect(self._player.stop)
        self._prevButton.clicked.connect(self._player.playPrevious)
        self._nextButton.clicked.connect(self._player.playNext)

    def _setupView(self):
        self._playButton = QtWidgets.QToolButton()
        self._stopButton = QtWidgets.QToolButton()
        self._prevButton = QtWidgets.QToolButton()
        self._nextButton = QtWidgets.QToolButton()
        for button in (self._playButton, self._stopButton, self._prevButton, self._nextButton):
            button.sizeHint = lambda: QtCore.QSize(25, 25)
            self.addWidget(button)

    def _refreshView(self):
        self.setWindowTitle("Controller")
        playIconName = "mdi.pause" if self._player.getState().isPlaying() else "mdi.play"
        self._playButton.setIcon(qtawesome.icon(playIconName))
        self._stopButton.setIcon(qtawesome.icon("mdi.stop"))
        self._prevButton.setIcon(qtawesome.icon("mdi.step-backward"))
        self._nextButton.setIcon(qtawesome.icon("mdi.step-forward"))