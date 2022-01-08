# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:07:03

from __future__ import annotations

import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.widgets.playlistsTable import PlaylistsTable

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.domains.playlist import Playlist


class PlaylistsDialog(QtWidgets.QDialog):
    playlistsTable: PlaylistsTable

    def __init__(self, playlists: typing.List[Playlist], parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.playlists = playlists
        self.setWindowTitle("Playlist Manager")
        self.setLayout(QtWidgets.QGridLayout(self))
        playlistsTable = PlaylistsTable(playlists, self)
        self.layout().addWidget(PlaylistsTable(playlists, self))
        self.resize(640, 360)
        self.playlistsTable = playlistsTable
