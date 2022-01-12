# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:18:33

from __future__ import annotations

import logging
import typing

from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.domains.playlist import Playlist

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.app import App
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class PlaylistManagerTable(IceTableView):
    def __init__(self, playlists: typing.List[Playlist], parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.mainWindow: MainWindow = self.parent().parent()
        self.app: App = self.mainWindow.app
        self.player = self.app.player
        self.playlists = playlists
        self.logger = logging.getLogger("playlistsTable")
        self.setModel(PlaylistManagerModel(playlists, self))
        self.setColumnWidth(0, 320)
        self.doubleClicked.connect(lambda x: self.onDoubleClickedAtRow(x.row()))

    def model(self) -> PlaylistManagerModel:
        return super().model()

    def onDoubleClickedAtRow(self, row):
        self.logger.info("On double clicked at row: %d", row)
        self.mainWindow.setFrontPlaylistAtIndex(row)

    def contextMenuEvent(self, arg__1: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction("Create", self.onCreatePlaylist)
        menu.addAction("Remove", self.onRemovePlaylists)
        menu.exec_(QtGui.QCursor.pos())

    def onCreatePlaylist(self):
        self.logger.debug("On create playlist")
        if len(self.playlists) == 0:
            self.logger.info("No playlist, create default one")
            self.model().beginInsertRows(QtCore.QModelIndex(), 0, 0)
            self.mainWindow.createAndAppendDefaultPlaylist()
            self.model().endInsertRows()
            return
        name = "Playlist {}".format(len(self.playlists) + 1)
        playlist = Playlist(name)
        self.model().insertPlaylist(playlist)
        self.player.addPlaylist(playlist)

    def onRemovePlaylists(self):
        indexes = sorted({x.row() for x in self.selectedIndexes()})
        self.logger.info("On remove playlists at indexes: %s", indexes)
        if not indexes:
            self.logger.info("No playlists to remove, return.")
            return

        if self.player.fetchCurrentPlaylistIndex() in indexes:
            self.logger.info("Remove playing playlist, stop player first")
            self.player.stop()
        self.model().removePlaylistsAtIndexes(indexes)


class PlaylistManagerModel(QtCore.QAbstractTableModel):
    playlistsRemoved: QtCore.SignalInstance = QtCore.Signal(list)

    def __init__(self, playlists: typing.List[Playlist], parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self.playlists = playlists

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.playlists)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        playlist = self.playlists[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return playlist.name
            elif index.column() == 1:
                return str(len(playlist.musics))

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["Name", "Items"][section]
        return super().headerData(section, orientation, role)

    def insertPlaylist(self, playlist):
        index = len(self.playlists)
        self.beginInsertRows(QtCore.QModelIndex(), index, index)
        self.playlists.append(playlist)
        self.endInsertRows()

    def removePlaylistsAtIndexes(self, indexes: typing.List[int]):
        for index in sorted(indexes, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.playlists[index]
        self.endRemoveRows()
        self.playlistsRemoved.emit(indexes)
