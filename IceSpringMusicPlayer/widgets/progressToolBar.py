# Created by BaiJiFeiLong@gmail.com at 2022/2/15 16:36
import logging

from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.controls.fluentSlider import FluentSlider
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils


class ProgressToolBar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("progressToolBar")
        self._logger.setLevel(logging.INFO)
        self._app = App.instance()
        self._player = self._app.getPlayer()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._player.positionChanged.connect(self._refreshView)
        self._progressSlider.valueChanged.connect(self._onProgressSliderValueChanged)

    def _onProgressSliderValueChanged(self, value: int):
        self._logger.info("On progress slider value changed: %d", value)
        self._player.setRelativePosition(value / self._progressSlider.maximum())

    def _setupView(self):
        self._progressSlider = FluentSlider(QtCore.Qt.Orientation.Horizontal)
        self._progressSlider.setMaximum(10 ** 9)
        self._progressSlider.setPageStep(self._progressSlider.maximum() // 20)
        self._progressSlider.setSingleStep(self._progressSlider.maximum() // 20)
        self.addWidget(WidgetUtils.createHorizontalSpacer(5))
        self.addWidget(self._progressSlider)
        self.addWidget(WidgetUtils.createHorizontalSpacer(5))

    def _refreshView(self):
        position = self._player.getRelativePosition()
        self._logger.debug("Refresh view at position: %f", position)
        self.setWindowTitle("Progress")
        self._progressSlider.blockSignals(True)
        self._progressSlider.setValue(int(position * self._progressSlider.maximum()))
        self._progressSlider.setDisabled(self._player.getState().isStopped())
        self._progressSlider.blockSignals(False)
