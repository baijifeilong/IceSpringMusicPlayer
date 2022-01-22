# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:33
import logging
import typing

import PySide2
from IceSpringRealOptional.typingUtils import unused
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.humanLabel import HumanLabel
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.utils.classUtils import ClassUtils


class PluginManagerWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent: QtWidgets.QWidget = None, config: JsonSupport = None):
        super().__init__(parent)
        unused(config)
        self._logger = logging.getLogger("pluginManagerWidget")
        self._app = App.instance()
        self._plugins = self._app.getPlugins()
        self._table = IceTableView()
        self._model = PluginManagerModel(self._plugins, self._table)
        self._table.setModel(self._model)
        self._table.setColumnWidth(0, 200)
        form = QtWidgets.QFormLayout()
        form.setMargin(10)
        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self._table, stretch=1)
        layout.addLayout(form, stretch=1)
        self.setLayout(layout)
        self._nameLabel = HumanLabel()
        self._versionLabel = HumanLabel()
        self._idLabel = HumanLabel()
        form.addRow("ID", self._idLabel)
        form.addRow("Name", self._nameLabel)
        form.addRow("Version", self._versionLabel)
        self._table.selectionModel().currentRowChanged.connect(self._onCurrentRowChanged)
        self._app.languageChanged.connect(self._onLanguageChanged)
        self._table.selectRow(0)

    def _onCurrentRowChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        self._logger.info("On current row changed: %d -> %d", previous.row(), current.row())
        self._refreshLabels()

    def _refreshLabels(self):
        row = self._table.selectionModel().currentIndex().row()
        plugin = self._plugins[row]
        self._nameLabel.setText(plugin.getPluginName())
        self._versionLabel.setText(plugin.getPluginVersion())
        self._idLabel.setText(ClassUtils.fullname(plugin))

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        topLeft = self._model.index(0, 0)
        bottomRight = self._model.index(self._model.rowCount() - 1, self._model.columnCount() - 1)
        self._model.dataChanged.emit(topLeft, bottomRight)
        self._refreshLabels()


class PluginManagerModel(QtCore.QAbstractTableModel):
    def __init__(self, plugins: typing.List[typing.Type[PluginMixin]], parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._plugins = plugins
        self._fields = ["Name", "Version"]

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
        raise RuntimeError("Impossible")
