# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:18:33

from __future__ import annotations

import logging
import typing

from IceSpringRealOptional.typingUtils import unused
from PySide2 import QtCore, QtWidgets, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PlaylistManagerTable(IceTableView, ReplaceableMixin):
    _logger: logging.Logger
    _player: Player

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget]) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistsTable")
        self._player = App.instance().getPlayer()
        self.setModel(PlaylistManagerModel(self))
        self.setColumnWidth(0, 320)
        self.doubleClicked.connect(self._onDoubleClicked)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self._player.playlistInserted.connect(self._onPlaylistInserted)

    def model(self) -> PlaylistManagerModel:
        return super().model()

    def _onDoubleClicked(self, modelIndex: QtCore.QModelIndex) -> None:
        index = modelIndex.row()
        self._logger.info("On double clicked at row: %d", index)
        self._player.setFrontPlaylistIndex(index)

    def _onCustomContextMenuRequested(self, position: QtCore.QPoint) -> None:
        unused(position)
        menu = QtWidgets.QMenu(self)
        menu.addAction("Create", self._onCreatePlaylist)
        menu.addAction("Remove", self._onRemovePlaylists)
        menu.exec_(QtGui.QCursor.pos())

    def _onCreatePlaylist(self):
        self._logger.debug("On create playlist")
        self._player.insertPlaylist()

    def _onPlaylistInserted(self, index: int) -> None:
        unused(index)
        self._logger.info("On playlist inserted")
        self._logger.info("Resetting model")
        self.model().endResetModel()
        self._logger.info("Model reset")

    def _onRemovePlaylists(self):
        indexes = sorted({x.row() for x in self.selectedIndexes()})
        self._logger.info("On remove playlists")
        self._logger.info(">> Remove playlists at indexes: %s", indexes)
        self._player.removePlaylistsAtIndexes(indexes)
        self._logger.info("<< Remove playlists done")


class PlaylistManagerModel(QtCore.QAbstractTableModel):
    _player: Player

    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._player = App.instance().getPlayer()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return self._player.getPlaylists().size()

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        playlist = self._player.getPlaylists()[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return playlist.name
            elif index.column() == 1:
                return str(len(playlist.musics))

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["Name", "Items"][section]
        return super().headerData(section, orientation, role)
