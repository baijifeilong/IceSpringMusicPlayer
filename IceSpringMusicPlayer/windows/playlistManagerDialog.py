# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:07:03

from __future__ import annotations

import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.widgets.playlistManagerTable import PlaylistManagerTable

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.domains.playlist import Playlist


class PlaylistManagerDialog(QtWidgets.QDialog):
    playlistManagerTable: PlaylistManagerTable

    def __init__(self, playlists: typing.List[Playlist], parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.playlists = playlists
        self.setWindowTitle("Playlist Manager")
        self.setLayout(QtWidgets.QGridLayout(self))
        playlistsTable = PlaylistManagerTable(playlists, self)
        self.layout().addWidget(PlaylistManagerTable(playlists, self))
        self.resize(640, 360)
        self.playlistManagerTable = playlistsTable
