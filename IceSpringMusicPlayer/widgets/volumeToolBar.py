# Created by BaiJiFeiLong@gmail.com at 2022/2/15 17:08
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.widgets.volumeSlider import VolumeSlider


class VolumeToolBar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("volumeToolBar")
        self._app = App.instance()
        self._player = self._app.getPlayer()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._player.volumeChanged.connect(self._refreshView)
        self._volumeSlider.valueChanged.connect(self._player.setVolume)

    def _setupView(self):
        self._volumeSlider = VolumeSlider()
        self._volumeSlider.setPageStep(5)
        self._volumeSlider.setSingleStep(5)
        self.addWidget(self._volumeSlider)

    def _refreshView(self):
        volume = self._player.getVolume()
        self._logger.debug("Refresh view at volume: %d", volume)
        self.setWindowTitle("Volume")
        self._volumeSlider.blockSignals(True)
        self._volumeSlider.setValue(volume)
        self._volumeSlider.blockSignals(False)
