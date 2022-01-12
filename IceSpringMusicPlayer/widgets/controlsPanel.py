# Created by BaiJiFeiLong@gmail.com at 2022/1/12 21:22
import logging

import qtawesome
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils


class ControlsPanel(QtWidgets.QWidget):
    _logger: logging.Logger
    _player: Player
    _zoom: float
    _layout: QtWidgets.QHBoxLayout
    _playButton: QtWidgets.QToolButton
    _playbackButton: QtWidgets.QToolButton
    _progressSlider: FluentSlider
    _progressLabel: QtWidgets.QLabel

    def __init__(self, player: Player, parent: QtWidgets.QWidget, zoom: float = 1.0) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("controlsPanel")
        self._player = player
        self._zoom = zoom
        player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        player.stateChanged.connect(self._onPlayerStateChanged)
        player.durationChanged.connect(self._onPlayerDurationChanged)
        player.positionChanged.connect(self._onPlayerPositionChanged)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(5)
        playButton = QtWidgets.QToolButton(self)
        playButton.setIcon(qtawesome.icon("mdi.play"))
        playButton.clicked.connect(self._onPlayButtonClicked)
        stopButton = QtWidgets.QToolButton(self)
        stopButton.setIcon(qtawesome.icon("mdi.stop"))
        stopButton.clicked.connect(self._onStopButtonClicked)
        previousButton = QtWidgets.QToolButton(self)
        previousButton.setIcon(qtawesome.icon("mdi.step-backward"))
        previousButton.clicked.connect(self._onPlayPreviousButtonClicked)
        nextButton = QtWidgets.QToolButton(self)
        nextButton.setIcon(qtawesome.icon("mdi.step-forward"))
        nextButton.clicked.connect(self._onPlayNextButtonClicked)
        playbackButton = QtWidgets.QToolButton(self)
        playbackButton.setIcon(qtawesome.icon("mdi.repeat"))
        playbackButton.clicked.connect(self._onPlaybackButtonClicked)
        iconSize = QtCore.QSize(48, 48) * zoom
        for button in playButton, stopButton, previousButton, nextButton, playbackButton:
            button.setIconSize(iconSize)
            button.setAutoRaise(True)
        progressSlider = FluentSlider(QtCore.Qt.Orientation.Horizontal, self)
        progressSlider.setDisabled(True)
        progressSlider.valueChanged.connect(self._onProgressSliderValueChanged)
        progressLabel = QtWidgets.QLabel("00:00/00:00", self)
        volumeDial = QtWidgets.QDial(self)
        volumeDial.setFixedSize(iconSize)
        volumeDial.setValue(50)
        volumeDial.valueChanged.connect(player.setVolume)
        layout.addWidget(playButton)
        layout.addWidget(stopButton)
        layout.addWidget(previousButton)
        layout.addWidget(nextButton)
        layout.addWidget(progressSlider)
        layout.addWidget(progressLabel)
        layout.addWidget(playbackButton)
        layout.addWidget(volumeDial)
        self._playButton = playButton
        self._playbackButton = playbackButton
        self._progressSlider = progressSlider
        self._progressLabel = progressLabel

    def _onProgressSliderValueChanged(self, value: int) -> None:
        self._logger.info("On progress slider value changed: %d", value)
        self._player.setPosition(value)

    def _onPlayNextButtonClicked(self) -> None:
        self._logger.info("On play next button clicked")
        self._player.playNext()

    def _onPlayPreviousButtonClicked(self) -> None:
        self._logger.info("On play previous button clicked")
        self._player.playPrevious()

    def _onPlayButtonClicked(self):
        logging.info("On play button clicked")
        if self._player.getState().isPlaying():
            logging.info("Player is playing, pause it")
            self._player.pause()
        else:
            logging.info("Player is paused, resume it")
            self._player.play()

    def _onStopButtonClicked(self):
        self._logger.info("On stop button clicked")
        if self._player.getState().isStopped():
            self._logger.info("Already stopped")
        else:
            self._logger.info("Stop playing")
            self._player.stop()

    def _onPlaybackButtonClicked(self):
        self._logger.info("On playback button clicked")
        self._player.setPlaybackMode(self._player.getPlaybackMode().next())
        newPlaybackMode = self._player.getPlaybackMode()
        newIconName = dict(LOOP="mdi.repeat", RANDOM="mdi.shuffle")[newPlaybackMode.name]
        self._playbackButton.setIcon(qtawesome.icon(newIconName))

    def _onCurrentMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        if oldIndex == -1 and newIndex != -1:
            self._logger.info("Enter playing")
            self._logger.info("Enable progress slider")
            self._progressSlider.setDisabled(False)
        elif oldIndex != -1 and newIndex == -1:
            self._logger.info("Exit playing")
            self._logger.info("Disable progress slider")
            self._progressSlider.setValue(0)
            self._progressSlider.setMaximum(0)
            self._progressSlider.setDisabled(True)
            self._logger.info("Reset progress label")
            self._progressLabel.setText("00:00/00:00")

    def _onPlayerStateChanged(self, state: PlayerState):
        self._logger.info("Player state changed: %s ", state)
        self._logger.info("Update play button icon")
        self._playButton.setIcon(qtawesome.icon("mdi.pause" if state.isPlaying() else "mdi.play"))

    def _onPlayerDurationChanged(self, duration: int) -> None:
        self._logger.info("Player duration changed: %d", duration)
        self._logger.info("Update progress slider max value")
        self._progressSlider.setMaximum(duration)

    def _onPlayerPositionChanged(self, position):
        if self._player.getState().isStopped():
            self._logger.info("Player has been stopped, skip")
            return
        self._progressSlider.blockSignals(True)
        self._progressSlider.setValue(position)
        self._progressSlider.blockSignals(False)
        duration = self._player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        self._progressLabel.setText(progressText)