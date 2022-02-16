# Created by BaiJiFeiLong@gmail.com at 2022/2/14 23:14
import logging

import qtawesome
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.toolBarMixin import ToolBarMixin
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.tt import Text


class ControllerToolBar(QtWidgets.QToolBar, ToolBarMixin):

    @classmethod
    def getToolBarTitle(cls) -> Text:
        return tt.ToolBar_Controller

    def __init__(self, parent):
        super().__init__(parent)
        self._logger = logging.getLogger("controllerToolBar")
        self._player = App.instance().getPlayer()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._player.stateChanged.connect(self._refreshView)
        self._player.playbackModeChanged.connect(self._refreshView)
        self._playButton.clicked.connect(self._player.togglePlayPause)
        self._stopButton.clicked.connect(self._player.stop)
        self._prevButton.clicked.connect(self._player.playPrevious)
        self._nextButton.clicked.connect(self._player.playNext)
        self._modeButton.clicked.connect(self._player.togglePlaybackMode)

    def _setupView(self):
        self._playButton = QtWidgets.QToolButton()
        self._stopButton = QtWidgets.QToolButton()
        self._prevButton = QtWidgets.QToolButton()
        self._nextButton = QtWidgets.QToolButton()
        self._modeButton = QtWidgets.QToolButton()
        for button in (self._playButton, self._stopButton, self._prevButton, self._nextButton, self._modeButton):
            button.sizeHint = lambda: QtCore.QSize(25, 25)
            self.addWidget(button)

    def _refreshView(self):
        self.setWindowTitle("Controller")
        mode = self._player.getPlaybackMode()
        playIconName = "mdi.pause" if self._player.getState().isPlaying() else "mdi.play"
        modeIconName = {PlaybackMode.LOOP: "mdi.repeat", PlaybackMode.RANDOM: "mdi.shuffle"}[mode]
        self._playButton.setIcon(qtawesome.icon(playIconName))
        self._stopButton.setIcon(qtawesome.icon("mdi.stop"))
        self._prevButton.setIcon(qtawesome.icon("mdi.step-backward"))
        self._nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
        self._modeButton.setIcon(qtawesome.icon(modeIconName))
