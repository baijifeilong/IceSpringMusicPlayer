# Created by BaiJiFeiLong@gmail.com at 2022/2/14 23:14
import logging

import qtawesome
from PySide2 import QtWidgets

from IceSpringMusicPlayer.app import App


class ControllerWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("controllerWidget")
        self._player = App.instance().getPlayer()
        self._setupLayout()
        self._setupEvents()
        self._refreshView()

    def _setupLayout(self):
        self._playButton = QtWidgets.QToolButton()
        self._stopButton = QtWidgets.QToolButton()
        self._prevButton = QtWidgets.QToolButton()
        self._nextButton = QtWidgets.QToolButton()
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setMargin(0)
        for toolButton in (self._playButton, self._stopButton, self._prevButton, self._nextButton):
            toolButton.setAutoRaise(True)
            mainLayout.addWidget(toolButton)
        self.setLayout(mainLayout)

    def _setupEvents(self):
        self._playButton.clicked.connect(self._player.togglePlayPause)
        self._stopButton.clicked.connect(self._player.stop)
        self._prevButton.clicked.connect(self._player.playPrevious)
        self._nextButton.clicked.connect(self._player.playNext)
        self._player.stateChanged.connect(self._refreshView)

    def _refreshView(self):
        playIconName = "mdi.pause" if self._player.getState().isPlaying() else "mdi.play"
        self._playButton.setIcon(qtawesome.icon(playIconName))
        self._stopButton.setIcon(qtawesome.icon("mdi.stop"))
        self._prevButton.setIcon(qtawesome.icon("mdi.step-backward"))
        self._nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
