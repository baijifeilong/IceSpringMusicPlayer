# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from PySide2 import QtCore, QtGui, QtWidgets

from iceSpringMusicPlayer.controls import IceTableView
from iceSpringMusicPlayer.utils import gg

if typing.TYPE_CHECKING:
    from iceSpringMusicPlayer.domains import Playlist, Music
    from iceSpringMusicPlayer.windows import MainWindow


class PlaylistTable(IceTableView):
    def __init__(self, playlist: Playlist, mainWindow: MainWindow) -> None:
        super().__init__(mainWindow.playlistWidget)
        self.logger = logging.getLogger("playlistTable")
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = self.mainWindow.app
        self.setModel(PlaylistModel(playlist, mainWindow))
        self.setColumnWidth(0, 35)
        self.setColumnWidth(1, 200)
        self.doubleClicked.connect(lambda x: self.onDoubleClicked(x.row()))
        self.setIconSize(QtCore.QSize(32, 32))
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self.viewport().installEventFilter(mainWindow)

    def model(self) -> "PlaylistModel":
        return super().model()

    def onDoubleClicked(self, index):
        self.logger.info(">>> On playlist table double clicked at %d", index)
        self.app.currentPlaylist = self.app.playlists[self.mainWindow.playlistWidget.currentIndex()]
        self.logger.info("Play music at index %d", index)
        self.app.playMusic(self.app.currentPlaylist.playMusic(self.app.currentPlaylist.musics[index]), True)

    def scrollToRow(self, index):
        self.scrollTo(self.model().index(index, 0), QtWidgets.QTableView.ScrollHint.PositionAtCenter)

    def selectRowRange(self, fromRow, toRow):
        self.clearSelection()
        self.selectionModel().select(
            QtCore.QItemSelection(self.model().index(fromRow, 0), self.model().index(toRow, 0)),
            gg(QtCore.QItemSelectionModel.Select) | QtCore.QItemSelectionModel.Rows)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu()
        menu.addAction(f"Remove", lambda: self.onRemove(sorted({x.row() for x in self.selectedIndexes()})))
        menu.exec_(QtGui.QCursor.pos())

    def onRemove(self, indexes: typing.List[int]):
        self.logger.info("Removing musics at indexes: %s", indexes)
        if not indexes:
            self.logger.info("No music to remove, return.")
            return
        if self.playlist == self.app.currentPlaylist and self.playlist.currentMusicIndex in indexes:
            self.logger.info("Stop playing music: %s", self.playlist.currentMusic)
            self.app.player.stop()
        self.playlist.resetHistory(
            keepCurrent=self.playlist == self.app.currentPlaylist and self.playlist.currentMusicIndex not in indexes)
        self.model().removeMusicsAtIndexes(indexes)


class PlaylistModel(QtCore.QAbstractTableModel):
    def __init__(self, playlist: Playlist, mainWindow: MainWindow,
            parent: typing.Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = self.mainWindow.app

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.playlist.musics)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        music = self.playlist.musics[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return ["", music.artist, music.title][index.column()]
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and index.row() == self.app.currentPlaylist.currentMusicIndex \
                    and self.app.currentPlaylistIndex == self.mainWindow.playlistWidget.currentIndex():
                # noinspection PyTypeChecker
                return [QtGui.QIcon(), qtawesome.icon("mdi.play"), qtawesome.icon("mdi.pause")][self.app.player.state()]

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", "Artist", "Title"][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        if column == 0:
            return
        self.playlist.musics = sorted(self.playlist.musics,
            key=lambda x: x.artist if column == 1 else x.title, reverse=order == QtCore.Qt.DescendingOrder)
        if self.playlist.currentMusic is not None:
            self.mainWindow.currentPlaylistTable.selectRow(self.playlist.currentMusicIndex)
            self.mainWindow.currentPlaylistTable.scrollToRow(self.playlist.currentMusicIndex)
        else:
            self.endResetModel()

    def refreshRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

    def insertMusics(self, musics: typing.List[Music]) -> (int, int):
        beginRow, endRow = len(self.playlist.musics), len(self.playlist.musics) + len(musics) - 1
        self.beginInsertRows(QtCore.QModelIndex(), beginRow, endRow)
        self.playlist.musics.extend(musics)
        self.endInsertRows()
        return beginRow, endRow

    def removeMusicsAtIndexes(self, indexes: typing.List[int]) -> None:
        for index in sorted(indexes, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.playlist.musics[index]
        self.endRemoveRows()
