# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from IceSpringPathLib import Path
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.typingUtils import gg
from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.iceTableView import IceTableView

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.domains.music import Music
    from IceSpringMusicPlayer.domains.playlist import Playlist
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class PlaylistTable(IceTableView):
    def __init__(self, playlist: Playlist, mainWindow: MainWindow) -> None:
        super().__init__(mainWindow.playlistWidget)
        self.logger = logging.getLogger("playlistTable")
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = self.mainWindow.app
        self.player = self.app.player
        model = PlaylistModel(playlist, mainWindow)
        self.setModel(model)
        self.setColumnWidth(0, int(35 * self.app.zoom))
        self.setColumnWidth(1, int(150 * self.app.zoom))
        self.doubleClicked.connect(lambda x: self.onDoubleClicked(x.row()))
        self.setIconSize(QtCore.QSize(32, 32) * self.app.zoom)
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self.viewport().installEventFilter(mainWindow)

    def model(self) -> "PlaylistModel":
        return super().model()

    def onDoubleClicked(self, index):
        self.logger.info(">>> On playlist table double clicked at %d", index)
        frontPlaylistIndex = self.mainWindow.fetchFrontPlaylistIndex()
        self.player.playMusicAtPlaylistAndIndex(frontPlaylistIndex, index)

    def scrollToRowAtCenter(self, index):
        self.scrollTo(self.model().index(index, 0), QtWidgets.QTableView.ScrollHint.PositionAtCenter)

    def selectRowRange(self, fromRow, toRow):
        self.clearSelection()
        self.selectionModel().select(
            QtCore.QItemSelection(self.model().index(fromRow, 0), self.model().index(toRow, 0)),
            gg(QtCore.QItemSelectionModel.Select, typing.Any) | QtCore.QItemSelectionModel.Rows)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu()
        menu.addAction("Remove", lambda: self.onRemove(sorted({x.row() for x in self.selectedIndexes()})))
        menu.addAction("Add", self.mainWindow.onOpenActionTriggered)
        menu.addAction("Rapid Add", self.rapidAdd)
        menu.exec_(QtGui.QCursor.pos())

    def rapidAdd(self):
        paths = Path("~/Music").expanduser().glob("**/*.mp3")
        self.mainWindow.addMusicsByFilenames([str(x) for x in paths])

    def onRemove(self, indexes: typing.List[int]):
        self.logger.info("Removing musics at indexes: %s", indexes)
        if not indexes:
            self.logger.info("No music to remove, return.")
            return
        self.model().removeMusicsAtIndexes(indexes)

    def fetchFirstSelectedRow(self) -> Maybe[int]:
        return Vector(self.selectedIndexes()).get(0).map(lambda x: x.row())


class PlaylistModel(QtCore.QAbstractTableModel):
    beforeRemoveMusics: QtCore.SignalInstance = QtCore.Signal(int, list)
    musicsInserted: QtCore.SignalInstance = QtCore.Signal(int, list)
    musicsRemoved: QtCore.SignalInstance = QtCore.Signal(int, list)

    def __init__(self, playlist: Playlist, mainWindow: MainWindow,
            parent: typing.Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistModel")
        self.playlist = playlist
        self.mainWindow = mainWindow
        self.app = mainWindow.app
        self.player = mainWindow.player

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.playlist.musics)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        music = self.playlist.musics[index.row()]
        currentPlaylistIndex = self.player.fetchCurrentPlaylistIndex()
        frontPlaylistIndex = self.mainWindow.fetchFrontPlaylistIndex()
        currentMusicIndex = self.player.fetchCurrentMusicIndex()
        if role == QtCore.Qt.DisplayRole:
            return ["", music.artist, music.title][index.column()]
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and index.row() == currentMusicIndex and currentPlaylistIndex == frontPlaylistIndex:
                playerState = self.app.player.fetchState()
                return qtawesome.icon("mdi.play") if playerState.isPlaying() else qtawesome.icon(
                    "mdi.pause") if playerState.isPaused() else qtawesome.icon()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", "Artist", "Title"][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        if column == 0:
            return
        self.playlist.musics.sort(key=lambda x: x.artist if column == 1 else x.title,
            reverse=order == QtCore.Qt.DescendingOrder)
        self.endResetModel()

    def notifyDataChangedAtRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

    def insertMusics(self, musics: typing.List[Music]) -> (int, int):
        self._logger.info("Inserting musics with count %d", len(musics))
        beginRow, endRow = len(self.playlist.musics), len(self.playlist.musics) + len(musics) - 1
        self.beginInsertRows(QtCore.QModelIndex(), beginRow, endRow)
        self.playlist.musics.extend(musics)
        self.endInsertRows()
        self._logger.info("Musics inserted")
        self._logger.info("> musicsInserted signal emitting...")
        self.musicsInserted.emit(self.player.calcPlaylistIndex(self.playlist), [])
        self._logger.info("< musicsInserted signal emitted...")
        return beginRow, endRow

    def removeMusicsAtIndexes(self, indexes: typing.List[int]) -> None:
        self.beforeRemoveMusics.emit(self.player.calcPlaylistIndex(self.playlist), indexes)
        for index in sorted(indexes, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.playlist.musics[index]
        self.endRemoveRows()
        self.musicsRemoved.emit(self.player.calcPlaylistIndex(self.playlist), indexes)
