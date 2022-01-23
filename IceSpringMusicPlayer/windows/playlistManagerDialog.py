# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:07:03

from __future__ import annotations

from PySide2 import QtWidgets

from IceSpringMusicPlayer.widgets.playlistManagerTable import PlaylistManagerTable


class PlaylistManagerDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setWindowTitle("Playlist Manager")
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(PlaylistManagerTable())
        self.resize(640, 360)
