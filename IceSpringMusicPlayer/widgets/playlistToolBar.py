# Created by BaiJiFeiLong@gmail.com at 2022/2/14 21:37
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.toolBarMixin import ToolBarMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils


class PlaylistToolBar(QtWidgets.QToolBar, ToolBarMixin):

    @classmethod
    def getToolBarTitle(cls) -> Text:
        return tt.ToolBar_Playlist

    def __init__(self, parent):
        super().__init__(parent)
        self._app = App.instance()
        self._player = self._app.getPlayer()
        self._logger = logging.getLogger("playlistToolBar")
        self._setupView()
        self._refreshView()
        self._app.languageChanged.connect(self._refreshView)
        self._player.frontPlaylistIndexChanged.connect(self._refreshView)
        self._player.playlistInserted.connect(self._refreshView)
        self._player.playlistsRemoved.connect(self._refreshView)

    def _setupView(self):
        self._playlistLabel = QtWidgets.QLabel()
        self._playlistComboBox = QtWidgets.QComboBox()
        self._playlistComboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._playlistComboBox.activated.connect(self._onPlaylistComboBoxActivated)
        self.addWidget(WidgetUtils.createHorizontalSpacer(5))
        self.addWidget(self._playlistLabel)
        self.addWidget(self._playlistComboBox)
        self.addWidget(WidgetUtils.createHorizontalSpacer(5))

    def _refreshView(self):
        self._playlistLabel.setText(tt.Toolbar_PlaylistLabel)
        self._playlistComboBox.blockSignals(True)
        self._playlistComboBox.clear()
        self._playlistComboBox.addItems([x.name for x in self._player.getPlaylists()])
        self._playlistComboBox.setCurrentIndex(self._player.getFrontPlaylistIndex())
        self._playlistComboBox.blockSignals(False)

    def _onPlaylistComboBoxActivated(self, index: int) -> None:
        self._logger.info("On playlist combo activated at index %d", index)
        self._player.setFrontPlaylistIndex(index)
