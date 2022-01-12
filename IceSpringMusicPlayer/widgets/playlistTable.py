# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from IceSpringRealOptional.typingUtils import gg, unused
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player


class PlaylistTable(IceTableView):
    actionAddTriggered: QtCore.SignalInstance = QtCore.Signal()
    actionOneKeyAddTriggered: QtCore.SignalInstance = QtCore.Signal()

    _logger: logging.Logger
    _player: Player

    def __init__(self, player: Player, parent: QtWidgets.QWidget, zoom=1) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistTable")
        self._player = player
        self.setModel(PlaylistModel(player, self))
        self.setColumnWidth(0, int(35 * zoom))
        self.setColumnWidth(1, int(150 * zoom))
        self.clicked.connect(self._onClicked)
        self.doubleClicked.connect(self._onDoubleClicked)
        self.setIconSize(QtCore.QSize(32, 32) * zoom)
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self._player.stateChanged.connect(self._onPlayerStateChanged)
        self._player.currentMusicIndexChanged.connect(self._onMusicIndexChanged)
        self._player.musicsInserted.connect(self._onMusicsInserted)

    def model(self) -> "PlaylistModel":
        return super().model()

    def _onClicked(self, modelIndex: QtCore.QModelIndex):
        index = modelIndex.row()
        self._logger.info("On clicked at %d", index)
        self._logger.info("Set front music index to %d", index)
        self._player.setFrontMusicIndex(index)

    def _onDoubleClicked(self, modelIndex: QtCore.QModelIndex):
        self._logger.info("On double clicked at %d", modelIndex.row())
        self._player.playMusicAtIndex(modelIndex.row())

    def scrollToRowAtCenter(self, index):
        self.scrollTo(self.model().index(index, 0), QtWidgets.QTableView.ScrollHint.PositionAtCenter)

    def _selectRowRange(self, fromRow, toRow):
        self.clearSelection()
        self.selectionModel().select(
            QtCore.QItemSelection(self.model().index(fromRow, 0), self.model().index(toRow, 0)),
            gg(QtCore.QItemSelectionModel.Select, typing.Any) | QtCore.QItemSelectionModel.Rows)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu()
        menu.addAction("Remove", self._onRemove)
        menu.addAction("Add", self.actionAddTriggered.emit)
        menu.addAction("Rapid Add", self.actionOneKeyAddTriggered.emit)
        menu.exec_(QtGui.QCursor.pos())

    def _onRemove(self, modelIndex: typing.List[QtCore.QModelIndex]):
        indexes = sorted(set(x.row() for x in modelIndex))
        self._logger.info("Remove musics at indexes: %s", indexes)
        self._player.removeMusicsAtIndexes(indexes)

    def _onMusicsInserted(self, indexes: typing.List[int]):
        self._logger.info("On musics inserted with count %d", len(indexes))
        self._logger.info("Notify table new data inserted")
        self.model().beginInsertRows(QtCore.QModelIndex(), indexes[0], indexes[-1])
        self.model().endInsertRows()
        self._logger.info("Select inserted rows")
        self._selectRowRange(indexes[0], indexes[-1])
        self.resizeRowsToContents()
        self._logger.info("Scroll first inserted row to center")
        self.scrollToRowAtCenter(indexes[0])

    def _onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("Refresh playlist table")
        self.model().notifyDataChangedAtRow(oldIndex)
        self.model().notifyDataChangedAtRow(newIndex)
        self._logger.info("Select played item in playlist table")
        self.selectRow(newIndex)

    def _onPlayerStateChanged(self, state: PlayerState) -> None:
        unused(state)
        self._logger.info("On player state changed, refresh table")
        self.model().notifyDataChangedAtRow(self._player.getCurrentMusicIndex())


class PlaylistModel(QtCore.QAbstractTableModel):
    _logger: logging.Logger
    _player: Player

    def __init__(self, player: Player, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistModel")
        self._player = player

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return self._player.getFrontPlaylist().map(lambda x: x.musics.size()).orElse(0)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        music = self._player.getFrontPlaylist().orElseThrow(AssertionError).musics[index.row()]
        currentPlaylistIndex = self._player.getCurrentPlaylistIndex()
        frontPlaylistIndex = self._player.getFrontPlaylistIndex()
        currentMusicIndex = self._player.getCurrentMusicIndex()
        if role == QtCore.Qt.DisplayRole:
            return ["", music.artist, music.title][index.column()]
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == 0 and index.row() == currentMusicIndex and currentPlaylistIndex == frontPlaylistIndex:
                playerState = self._player.getState()
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
        if self._player.getFrontPlaylist().isAbsent():
            self._logger.info("No playlist, skip")
            return
        self._player.getFrontPlaylist().orElseThrow(AssertionError).musics.sort(
            key=lambda x: x.artist if column == 1 else x.title, reverse=order == QtCore.Qt.DescendingOrder)
        self.endResetModel()

    def notifyDataChangedAtRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))
