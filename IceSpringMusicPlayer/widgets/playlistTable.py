# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from IceSpringRealOptional.typingUtils import gg, unused
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PlaylistTable(IceTableView, ReplaceableMixin):
    _logger: logging.Logger
    _app: App
    _config: Config
    _player: Player

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistTable")
        self._app = App.instance()
        self._config = App.instance().getConfig()
        self._player = App.instance().getPlayer()
        self.setModel(PlaylistModel(self))
        self.setColumnWidth(0, int(35 * self._app.getZoom()))
        self.setColumnWidth(1, int(150 * self._app.getZoom()))
        self.doubleClicked.connect(self._onDoubleClicked)
        self.setIconSize(QtCore.QSize(32, 32) * self._app.getZoom())
        self.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self.selectionModel().selectionChanged.connect(self._onSelectionChanged)
        self._app.requestLocateCurrentMusic.connect(self._onRequestLocateCurrentMusic)
        self._player.stateChanged.connect(self._onPlayerStateChanged)
        self._player.frontPlaylistIndexAboutToBeChanged.connect(self._onFrontPlaylistIndexAboutToBeChanged)
        self._player.frontPlaylistIndexChanged.connect(self._onFrontPlaylistIndexChanged)
        self._player.selectedMusicIndexesChanged.connect(self._onSelectedMusicIndexesChanged)
        self._player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        self._player.musicsInserted.connect(self._onMusicsInserted)
        self._selectAndFollowMusics(self._player.getSelectedMusicIndexes())

    def model(self) -> "PlaylistModel":
        return super().model()

    def _onSelectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        self._logger.info("On selection changed")
        selectedIndexes = {x.row() for x in selected.indexes()}
        deselectedIndexes = {x.row() for x in deselected.indexes()}
        oldSelectedIndexes = self._player.getSelectedMusicIndexes()
        newSelectedIndexes = oldSelectedIndexes.union(selectedIndexes).difference(deselectedIndexes)
        self.blockSignals(True)
        self._player.setSelectedMusicIndexes(newSelectedIndexes)
        self.blockSignals(False)

    def _onSelectedMusicIndexesChanged(self, indexes: typing.Set[int]) -> None:
        self._logger.info("On selected music indexes changed: %s", indexes)
        self._logger.info("Clear all selection and reselect")
        selectedIndexes = {x.row() for x in self.selectedIndexes()}
        if indexes == selectedIndexes:
            self._logger.info("Selection not changed, return")
            return
        self._selectAndFollowMusics(indexes)

    def _selectAndFollowMusics(self, indexes: typing.Set[int]) -> None:
        self._logger.info("Select and follow musics: %s", indexes)
        self.selectionModel().blockSignals(True)
        self.model().endResetModel()
        self._selectRows(indexes)
        self.selectionModel().blockSignals(False)
        self._logger.info("Reselection done")
        if len(indexes) == 0:
            self._logger.info("Selection indexes is empty, no scroll required")
        else:
            firstIndex = sorted(indexes)[0]
            self._logger.info("Scroll to first index: %d", firstIndex)
            self._smartScrollToRow(firstIndex)

    def _onDoubleClicked(self, modelIndex: QtCore.QModelIndex):
        self._logger.info("On double clicked at %d", modelIndex.row())
        self._player.playMusicAtIndex(modelIndex.row())

    def _smartScrollToRow(self, index):
        visible = index in range(self.rowAt(0), self.rowAt(self.height()))
        hint = QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible if visible \
            else QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter
        self.scrollTo(self.model().index(index, 0), hint)

    def _selectRowRange(self, fromRow, toRow):
        self.selectionModel().select(
            QtCore.QItemSelection(self.model().index(fromRow, 0), self.model().index(toRow, 0)),
            gg(QtCore.QItemSelectionModel.Select, typing.Any) | QtCore.QItemSelectionModel.Rows)

    def _selectRows(self, indexes: typing.Iterable[int]) -> None:
        for index in indexes:
            self.selectionModel().select(
                QtCore.QItemSelection(self.model().index(index, 0), self.model().index(index, 2)),
                gg(QtCore.QItemSelectionModel.Select, typing.Any) | QtCore.QItemSelectionModel.Rows)

    def _onCustomContextMenuRequested(self, pos: QtCore.QPoint) -> None:
        unused(pos)
        menu = QtWidgets.QMenu()
        menu.addAction("Remove", self._onRemove)
        menu.addAction("Add", self._app.addMusicsFromFileDialog)
        menu.addAction("One Key Add", self._app.addMusicsFromHomeFolder)
        menu.addAction("Load Test Data", self._app.loadTestData)
        menu.exec_(QtGui.QCursor.pos())

    def _onRequestLocateCurrentMusic(self) -> None:
        self._logger.info("On request locate current music")
        if not self._player.getCurrentMusic().isPresent():
            self._logger.info("No music to locate, return")
            return
        currentMusicIndex = self._player.getCurrentMusicIndex()
        self._logger.info("Locate music: %s", currentMusicIndex)
        self._player.setFrontPlaylistIndex(self._player.getCurrentPlaylistIndex())
        self.selectRow(currentMusicIndex)
        self._smartScrollToRow(currentMusicIndex)

    def _onFrontPlaylistIndexAboutToBeChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("On front playlist index about to be changed: %d => %d", oldIndex, newIndex)
        if oldIndex == -1:
            self._logger.info("Old front playlist index is -1, nothing to save, return")
            return
        playlist = self._player.getFrontPlaylist().orElseThrow(AssertionError)
        scrollLocation = self.verticalScrollBar().value()
        self._logger.info("Save scroll location: %s => %s", playlist.name, scrollLocation)
        self.setProperty(f"scrollLocation_{oldIndex}", scrollLocation)

    def _onFrontPlaylistIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("On front playlist index changed: %d => %d", oldIndex, newIndex)
        self._logger.info("Reset model")
        self.model().endResetModel()
        self._logger.info("Model reset")
        if newIndex == -1:
            self._logger.info("New front playlist index is -1, nothing to recover, return")
            return
        playlist = self._player.getFrontPlaylist().orElseThrow(AssertionError)
        selectedIndexes = self._player.getSelectedMusicIndexes()
        self._logger.info("Recover playlist selections: %s => %s", playlist.name, selectedIndexes)
        self.selectionModel().blockSignals(True)
        self._selectRows(selectedIndexes)
        self.selectionModel().blockSignals(False)
        scrollLocation = self.property(f"scrollLocation_{newIndex}") or 0
        self._logger.info("Recover scroll location: %s => %s", playlist.name, scrollLocation)
        self.verticalScrollBar().setMaximum(playlist.musics.size())
        self.verticalScrollBar().setValue(scrollLocation)

    def _onRemove(self):
        indexes = sorted(set(x.row() for x in self.selectedIndexes()))
        self._logger.info("Remove musics at indexes: %s", indexes)
        self._player.removeMusicsAtIndexes(indexes)

    def _onMusicsInserted(self, indexes: typing.List[int]):
        self._logger.info("On musics inserted with count %d", len(indexes))
        self._logger.info("Notify table new data inserted")
        self.model().beginInsertRows(QtCore.QModelIndex(), indexes[0], indexes[-1])
        self.model().endInsertRows()
        self._logger.info("Clear old selection")
        self.clearSelection()
        self._logger.info("Select inserted rows")
        self._selectRowRange(indexes[0], indexes[-1])
        self._app.getZoom() < 0.8 and self.resizeRowsToContents()
        self._logger.info("Scroll first inserted row to center")
        self._smartScrollToRow(indexes[0])

    def _onCurrentMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("On current music index changed: %d => %d", oldIndex, newIndex)
        if self._player.getFrontPlaylistIndex() != self._player.getCurrentPlaylistIndex():
            self._logger.info("Front playlist not current, return")
            return
        self._logger.info("Select new row")
        self._clearAndSelectRow(newIndex)
        self._logger.info("Scroll to new row")
        self._smartScrollToRow(newIndex)

    def _clearAndSelectRow(self, index: int) -> None:
        self.selectionModel().select(self.model().index(index, 0),
            gg(QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect, typing.Any) |
            QtCore.QItemSelectionModel.SelectionFlag.Rows)

    def _onPlayerStateChanged(self, state: PlayerState) -> None:
        self._logger.info("On player state changed: %s", state)
        self._logger.info("Notify model to refresh current row")
        self.model().notifyDataChangedAtRow(self._player.getCurrentMusicIndex())


class PlaylistModel(QtCore.QAbstractTableModel):
    _logger: logging.Logger
    _player: Player

    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistModel")
        self._player = App.instance().getPlayer()

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
