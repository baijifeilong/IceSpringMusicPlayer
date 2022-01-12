# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.typingUtils import gg, unused
from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player


class PlaylistTable(IceTableView):
    actionAddTriggered: QtCore.SignalInstance = QtCore.Signal()
    actionOneKeyAddTriggered: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self, player: Player, parent: QtWidgets.QWidget, zoom=1) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger("playlistTable")
        self.player = player
        model = PlaylistModel(player, self)
        self.setModel(model)
        self.setColumnWidth(0, int(35 * zoom))
        self.setColumnWidth(1, int(150 * zoom))
        self.doubleClicked.connect(self.onDoubleClicked)
        self.setIconSize(QtCore.QSize(32, 32) * zoom)
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self.player.stateChanged.connect(self.onPlayerStateChanged)
        self.player.currentMusicIndexChanged.connect(self.onMusicIndexChanged)
        self.player.musicsInserted.connect(self.onMusicsInserted)

    def model(self) -> "PlaylistModel":
        return super().model()

    def onDoubleClicked(self, modelIndex: QtCore.QModelIndex):
        self.logger.info(">>> On playlist table double clicked at %d", modelIndex.row())
        self.player.playMusicAtIndex(modelIndex.row())

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
        menu.addAction("Add", self.actionAddTriggered.emit)
        menu.addAction("Rapid Add", self.actionOneKeyAddTriggered.emit)
        menu.exec_(QtGui.QCursor.pos())

    def onRemove(self, indexes: typing.List[int]):
        self.logger.info("Removing musics at indexes: %s", indexes)
        if not indexes:
            self.logger.info("No music to remove, return.")
            return
        self.player.removeMusicsAtIndexes(indexes)

    def fetchFirstSelectedRow(self) -> Maybe[int]:
        return Vector(self.selectedIndexes()).get(0).map(lambda x: x.row())

    def onMusicsInserted(self, indexes: typing.List[int]):
        self.logger.info("On musics inserted with count %d", len(indexes))
        self.logger.info("Notify table new data inserted")
        self.model().beginInsertRows(QtCore.QModelIndex(), indexes[0], indexes[-1])
        self.model().endInsertRows()
        self.logger.info("Select inserted rows")
        self.selectRowRange(indexes[0], indexes[-1])
        self.resizeRowsToContents()
        self.logger.info("Scroll first inserted row to center")
        self.scrollToRowAtCenter(indexes[0])

    def onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self.logger.info("Refresh playlist table")
        self.model().notifyDataChangedAtRow(oldIndex)
        self.model().notifyDataChangedAtRow(newIndex)
        self.logger.info("Select played item in playlist table")
        self.selectRow(newIndex)

    def onPlayerStateChanged(self, state: PlayerState) -> None:
        unused(state)
        self.model().notifyDataChangedAtRow(self.player.getCurrentMusicIndex())


class PlaylistModel(QtCore.QAbstractTableModel):
    def __init__(self, player: Player, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistModel")
        self.player = player

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return self.player.getFrontPlaylist().map(lambda x: x.musics.size()).orElse(0)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        music = self.player.getFrontPlaylist().orElseThrow(AssertionError).musics[index.row()]
        currentPlaylistIndex = self.player.getCurrentPlaylistIndex()
        frontPlaylistIndex = self.player.getFrontPlaylistIndex()
        currentMusicIndex = self.player.getCurrentMusicIndex()
        if role == QtCore.Qt.DisplayRole:
            return ["", music.artist, music.title][index.column()]
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and index.row() == currentMusicIndex and currentPlaylistIndex == frontPlaylistIndex:
                playerState = self.player.getState()
                return qtawesome.icon("mdi.play") if playerState.isPlaying() else qtawesome.icon(
                    "mdi.pause") if playerState.isPaused() else qtawesome.icon()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", "Artist", "Title"][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        self._logger.info("Sorting...")
        if column == 0:
            self._logger.info("Column is zero, skip")
            return
        if self.player.getFrontPlaylist().isAbsent():
            self._logger.info("No playlist, skip")
            return
        self.player.getFrontPlaylist().orElseThrow(AssertionError).musics.sort(
            key=lambda x: x.artist if column == 1 else x.title, reverse=order == QtCore.Qt.DescendingOrder)
        self.endResetModel()

    def notifyDataChangedAtRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))
