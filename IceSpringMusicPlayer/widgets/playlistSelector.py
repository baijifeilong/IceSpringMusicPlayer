# Created by BaiJiFeiLong@gmail.com at 2022/2/14 21:37
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App


class PlaylistSelector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._player = App.instance().getPlayer()
        self._logger = logging.getLogger("playlistSelector")
        self._playlistLabel = QtWidgets.QLabel(tt.Toolbar_Playlist)
        self._playlistComboBox = QtWidgets.QComboBox()
        self._playlistComboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._playlistComboBox.activated.connect(self._onPlaylistComboBoxActivated)
        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self._playlistLabel)
        layout.addWidget(self._playlistComboBox)
        self.setLayout(layout)
        self._player.frontPlaylistIndexChanged.connect(self._onFrontPlaylistIndexChanged)
        self._player.playlistInserted.connect(self._onPlaylistInserted)
        self._player.playlistsRemoved.connect(self._onPlaylistsRemoved)
        self._setupPlaylistComboBox()

    def _onPlaylistComboBoxActivated(self, index: int) -> None:
        self._logger.info("On playlist combo activated at index %d", index)
        self._player.setFrontPlaylistIndex(index)

    def _setupPlaylistComboBox(self):
        self._playlistComboBox.blockSignals(True)
        self._playlistComboBox.clear()
        self._playlistComboBox.addItems([x.name for x in self._player.getPlaylists()])
        self._playlistComboBox.setCurrentIndex(self._player.getFrontPlaylistIndex())
        self._playlistComboBox.blockSignals(False)

    def _onFrontPlaylistIndexChanged(self, oldIndex, newIndex):
        self._logger.info("On front playlist index changed: %d => %d", oldIndex, newIndex)
        self._setupPlaylistComboBox()

    def _onPlaylistInserted(self, index):
        self._logger.info("On playlist inserted: %d", index)
        self._setupPlaylistComboBox()

    def _onPlaylistsRemoved(self, indexes):
        self._logger.info("On playlists removed: %s", indexes)
        self._setupPlaylistComboBox()
