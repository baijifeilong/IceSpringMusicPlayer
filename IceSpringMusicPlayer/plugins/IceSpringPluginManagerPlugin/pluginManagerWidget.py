# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:33
import logging
import typing

import PySide2
from IceSpringRealOptional.typingUtils import unused
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.utils.classUtils import ClassUtils


class PluginManagerWidget(IceTableView, PluginWidgetMixin):
    def __init__(self, parent: QtWidgets.QWidget = None, config: JsonSupport = None):
        super().__init__(parent)
        unused(config)
        self._logger = logging.getLogger("pluginManagerWidget")
        self._app = App.instance()
        self._model = PluginManagerModel(self)
        self.setModel(self._model)
        self.setColumnWidth(0, 200)
        self._app.languageChanged.connect(self._onLanguageChanged)

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        topLeft = self._model.index(0, 0)
        bottomRight = self._model.index(self._model.rowCount() - 1, self._model.columnCount() - 1)
        self._model.dataChanged.emit(topLeft, bottomRight)


class PluginManagerModel(QtCore.QAbstractTableModel):
    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._plugins = App.instance().getPlugins()
        self._fields = ["Name", "Version", "ID"]

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._plugins)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._fields)

    def headerData(self, section: int, orientation: PySide2.QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self._fields[section]

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return
        row, column = index.row(), index.column()
        plugin = self._plugins[row]
        if column == 0:
            return plugin.getPluginName()
        if column == 1:
            return plugin.getPluginVersion()
        if column == 2:
            return ClassUtils.fullname(self._plugins[row])
        raise RuntimeError("Impossible")
