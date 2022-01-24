# Created by BaiJiFeiLong@gmail.com at 2022/1/12 21:22
import logging
import typing

import qtawesome
from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringControlsPlugin.controlsWidgetConfig import ControlsWidgetConfig
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils


class ControlsWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()
    _logger: logging.Logger
    _config: Config
    _app: App
    _player: Player
    _layout: QtWidgets.QHBoxLayout
    _playButton: QtWidgets.QToolButton
    _playbackButton: QtWidgets.QToolButton
    _progressSlider: FluentSlider
    _progressLabel: QtWidgets.QLabel
    _volumeDial: QtWidgets.QDial
    _widgetConfig: ControlsWidgetConfig

    def __init__(self, config=None) -> None:
        super().__init__()
        self._widgetConfig = config or self.getWidgetConfigClass().getDefaultObject()
        self._logger = logging.getLogger("controlsWidget")
        self._config = App.instance().getConfig()
        self._app = App.instance()
        self._player = App.instance().getPlayer()
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
        for button in playButton, stopButton, previousButton, nextButton, playbackButton:
            button.setAutoRaise(True)
        progressSlider = FluentSlider(QtCore.Qt.Orientation.Horizontal, self)
        progressSlider.valueChanged.connect(self._onProgressSliderValueChanged)
        progressLabel = QtWidgets.QLabel("00:00/00:00", self)
        volumeDial = QtWidgets.QDial(self)
        volumeDial.valueChanged.connect(self._onVolumeDialValueChanged)
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
        self._volumeDial = volumeDial
        self._refreshIcons()
        self._refreshView()
        self._player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        self._player.stateChanged.connect(self._onPlayerStateChanged)
        self._player.durationChanged.connect(self._onPlayerDurationChanged)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        self._player.playbackModeChanged.connect(self._onPlaybackModeChanged)
        self._player.volumeChanged.connect(self._onPlayerVolumeChanged)
        self.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)

    def _onCustomContextMenuRequested(self):
        from IceSpringControlsPlugin.controlsWidgetConfigWidget import ControlsWidgetConfigWidget
        self._logger.info("On custom context menu requested")
        menu = QtWidgets.QMenu(self)
        menu.addAction("Widget Config",
            lambda: DialogUtils.execWidget(ControlsWidgetConfigWidget(self), self, QtCore.QSize(854, 480)))
        menu.exec_(QtGui.QCursor.pos())

    def _refreshIcons(self):
        iconSize = self._widgetConfig.iconSize
        size = QtCore.QSize(iconSize, iconSize)
        for widget in self.findChildren(QtWidgets.QWidget):
            if isinstance(widget, QtWidgets.QToolButton):
                widget.setIconSize(size)
            elif isinstance(widget, QtWidgets.QDial):
                widget.setFixedSize(size)

    def _onWidgetConfigChanged(self):
        self._logger.info("On widget config changed")
        self._refreshIcons()

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
            logging.info("Player is not playing, play it")
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
        oldMode = self._player.getPlaybackMode()
        newMode = oldMode.next()
        self._logger.info("Update playback mode %s => %s", oldMode, newMode)
        self._player.setPlaybackMode(newMode)

    def _onPlaybackModeChanged(self, mode: PlaybackMode) -> None:
        self._logger.info("On playback mode changed: %s", mode)
        self._logger.info("Update playback button icon")
        self._refreshPlaybackButton()

    def _refreshPlaybackButton(self):
        mode = self._player.getPlaybackMode()
        iconName = {PlaybackMode.LOOP: "mdi.repeat", PlaybackMode.RANDOM: "mdi.shuffle"}[mode]
        self._playbackButton.setIcon(qtawesome.icon(iconName))

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
        self._refreshPlayButton()

    def _refreshPlayButton(self):
        self._playButton.setIcon(qtawesome.icon("mdi.pause" if self._player.getState().isPlaying() else "mdi.play"))

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
        self._refreshProgressLabel()

    def _refreshProgressLabel(self):
        if self._player.getState().isStopped():
            self._progressLabel.setText("00:00/00:00")
            return
        position = self._player.getPosition()
        duration = self._player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        self._progressLabel.setText(progressText)

    def _onVolumeDialValueChanged(self, value: int) -> None:
        self._logger.info("On volume dial value changed: %d", value)
        self._player.setVolume(value)

    def _onPlayerVolumeChanged(self, value: int) -> None:
        self._logger.info("On player volume changed: %d", value)
        self._player.blockSignals(True)
        self._volumeDial.setValue(value)
        self._player.blockSignals(False)

    def _refreshView(self):
        self._refreshPlayButton()
        self._refreshPlaybackButton()
        self._progressSlider.blockSignals(True)
        if self._player.getState().isStopped():
            self._progressSlider.setMaximum(100)
            self._progressSlider.setValue(0)
            self._progressSlider.setDisabled(True)
        else:
            self._progressSlider.setMaximum(self._player.getDuration())
            self._progressSlider.setValue(self._player.getPosition())
            self._progressSlider.setDisabled(False)
        self._progressSlider.blockSignals(False)
        self._volumeDial.blockSignals(True)
        self._volumeDial.setValue(self._player.getVolume())
        self._volumeDial.blockSignals(False)
        self._refreshProgressLabel()

    def paintEvent(self, evt):
        self.style().drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_Widget,
            Just.of(QtWidgets.QStyleOption()).apply(lambda x: x.init(self)).value(), QtGui.QPainter(self), self)

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[ControlsWidgetConfig]:
        return ControlsWidgetConfig

    def getWidgetConfig(self) -> ControlsWidgetConfig:
        return self._widgetConfig
