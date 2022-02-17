# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:08:29

from __future__ import annotations

import logging
import typing

import qtawesome
from IceSpringRealOptional.typingUtils import gg, unused
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.services.playlistService import PlaylistService
from IceSpringPlaylistPlugin.playlistWidgetConfig import PlaylistWidgetConfig


class PlaylistWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[PlaylistWidgetConfig]:
        return PlaylistWidgetConfig

    def getWidgetConfig(self) -> PlaylistWidgetConfig:
        return self._widgetConfig

    def __init__(self, config=None) -> None:
        super().__init__()
        self._widgetConfig = config or self.getWidgetConfigClass().getDefaultObject()
        self._logger = logging.getLogger("playlistWidget")
        self._player = App.instance().getPlayer()
        self._tabBar = QtWidgets.QTabBar()
        self._tabBar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self._playlistTable = PlaylistTable(self._widgetConfig, self)
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self._tabBar)
        mainLayout.addWidget(self._playlistTable)
        mainLayout.setMargin(0)
        self.setLayout(mainLayout)
        self._tabBar.currentChanged.connect(self._onTabBarCurrentChanged)
        self.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self._player.frontPlaylistIndexChanged.connect(self._onFrontPlaylistIndexChanged)
        self._refreshTabBar()

    def _onWidgetConfigChanged(self):
        self._logger.info("On widget config changed")
        self._refreshTabBar()

    def _onTabBarCurrentChanged(self, index):
        self._logger.info("On tab bar current changed: %d", index)
        self._player.setFrontPlaylistIndex(index)

    def _onFrontPlaylistIndexChanged(self, oldIndex, newIndex):
        self._logger.info("On front playlist index changed: %d => %d", oldIndex, newIndex)
        self._tabBar.setCurrentIndex(newIndex)

    def _refreshTabBar(self):
        self._tabBar.blockSignals(True)
        for index in reversed(range(self._tabBar.count())):
            self._tabBar.removeTab(index)
        for playlist in self._player.getPlaylists():
            self._tabBar.addTab(playlist.name)
        self._tabBar.setCurrentIndex(self._player.getFrontPlaylistIndex())
        self._tabBar.setVisible(self._widgetConfig.showTabBar)
        self._tabBar.blockSignals(False)


class PlaylistTable(IceTableView, PluginWidgetMixin):
    _logger: logging.Logger
    _widgetConfig: PlaylistWidgetConfig
    _parent: PlaylistWidget
    _app: App
    _player: Player
    _playlistService: PlaylistService

    def __init__(self, config, parent) -> None:
        super().__init__()
        self._widgetConfig = config
        self._parent = gg(parent)
        self._logger = logging.getLogger("playlistTable")
        self._app = App.instance()
        self._player = App.instance().getPlayer()
        self._playlistService = self._app.getPlaylistService()
        self.setModel(PlaylistModel(self))
        self.setColumnWidth(0, int(35 * self._app.getZoom()))
        self.setColumnWidth(1, int(150 * self._app.getZoom()))
        self.doubleClicked.connect(self._onDoubleClicked)
        self.setIconSize(QtCore.QSize(32, 32) * self._app.getZoom())
        self.horizontalHeader().setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)
        self.setWordWrap(False)
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
        self._player.musicsRemoved.connect(self._onMusicsRemoved)
        self._player.musicsSorted.connect(self._onMusicsSorted)
        self._selectAndFollowMusics(self._player.getSelectedMusicIndexes())
        self._loadConfig()
        self._parent.widgetConfigChanged.connect(self._onWidgetConfigChanged)

    def _onWidgetConfigChanged(self):
        self._logger.info("On widget config changed")
        self._loadConfig()

    def _loadConfig(self):
        policies = dict(AUTO=QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            ON=QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn, OFF=QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._logger.info("Load config")
        self.verticalHeader().setDefaultSectionSize(self._widgetConfig.rowHeight)
        self.setHorizontalScrollBarPolicy(policies[self._widgetConfig.horizontalScrollBarPolicy])
        self.setVerticalScrollBarPolicy(policies[self._widgetConfig.verticalScrollBarPolicy])

    def model(self) -> "PlaylistModel":
        return gg(super().model())

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
        from IceSpringPlaylistPlugin.playlistWidgetConfigDialog import PlaylistWidgetConfigDialog
        unused(pos)
        menu = QtWidgets.QMenu()
        menu.addAction("Add Musics", self._playlistService.addMusicsFromFileDialog)
        menu.addAction("Add Folder", self._playlistService.addMusicsFromFolderDialog)
        menu.addAction("Remove Musics", self._onRemove)
        menu.addAction(tt.Plugins_ConfigWidget, lambda: PlaylistWidgetConfigDialog(self._parent).exec_())
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
        indexes = set(x.row() for x in self.selectedIndexes())
        self._logger.info("Remove musics at indexes: %s", indexes)
        self._player.removeMusicsAtIndexes(indexes)

    def _onMusicsInserted(self):
        self._logger.info("On musics inserted, reset table")
        self.horizontalHeader().setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)
        self._doResetTable()

    def _onMusicsRemoved(self):
        self._logger.info("On musics removed, reset table")
        self.horizontalHeader().setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)
        self._doResetTable()

    def _onMusicsSorted(self):
        self._logger.info("On musics sorted, reset table")
        self._doResetTable()

    def _doResetTable(self):
        self._logger.info("Reset model")
        self.model().endResetModel()
        self._logger.info("Refresh selected rows")
        playlist = self._player.getFrontPlaylist().get()
        self._selectRows(playlist.selectedIndexes)
        if len(playlist.selectedIndexes) > 0:
            self._logger.info("Selected indexes not empty")
            firstSelectedIndex = sorted(playlist.selectedIndexes)[0]
            self._logger.info("Scroll first selected row %d to center", firstSelectedIndex)
            self._smartScrollToRow(firstSelectedIndex)

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
    _app: App
    _player: Player

    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("playlistModel")
        self._app = App.instance()
        self._player = App.instance().getPlayer()
        self._app.languageChanged.connect(self._onLanguageChanged)

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        self.headerDataChanged.emit(QtCore.Qt.Orientation.Horizontal, 0, self.columnCount() - 1)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return self._player.getFrontPlaylist().map(lambda x: x.musics.size()).orElse(0)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 3

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == QtCore.Qt.DisplayRole:
            music = self._player.getFrontPlaylist().orElseThrow(AssertionError).musics[index.row()]
            return ("", music.artist, music.title)[index.column()]
        elif role == QtCore.Qt.DecorationRole:
            currentPlaylistIndex = self._player.getCurrentPlaylistIndex()
            frontPlaylistIndex = self._player.getFrontPlaylistIndex()
            currentMusicIndex = self._player.getCurrentMusicIndex()
            if index.column() == 0 and index.row() == currentMusicIndex and currentPlaylistIndex == frontPlaylistIndex:
                playerState = self._player.getState()
                return qtawesome.icon("mdi.play") if playerState.isPlaying() else qtawesome.icon(
                    "mdi.pause") if playerState.isPaused() else qtawesome.icon()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["", tt.Music_Artist, tt.Music_Title][section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        self._logger.info("Sorting...")
        if column not in [1, 2]:
            self._logger.info("Sort not supported on column %d, skip", column)
            return
        if self._player.getFrontPlaylist().isAbsent():
            self._logger.info("No playlist, skip")
            return
        self._player.sortMusics(key=lambda x: {1: x.artist, 2: x.title}[column],
            reverse=order == QtCore.Qt.DescendingOrder)

    def notifyDataChangedAtRow(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0))
