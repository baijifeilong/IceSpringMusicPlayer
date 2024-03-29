# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:33
import logging
import typing

import PySide2
from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.controls.humanLabel import HumanLabel
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.domains.plugin import Plugin
from IceSpringMusicPlayer.utils.classUtils import ClassUtils


class PluginManagerWidget(QtWidgets.QSplitter):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("pluginManagerWidget")
        self._app = App.instance()
        self._pluginService = self._app.getPluginService()
        self._plugins = self._app.getConfig().plugins
        self._table = IceTableView()
        self._model = PluginManagerModel(self._plugins, self._table)
        self._table.setModel(self._model)
        self._table.setColumnWidth(0, 200)
        self._nameLabel = HumanLabel()
        self._versionLabel = HumanLabel()
        self._idLabel = HumanLabel()
        self._statusLabel = HumanLabel()
        self._systemLabel = HumanLabel()
        formLayout = QtWidgets.QFormLayout()
        formLayout.setMargin(10)
        formLayout.addRow("ID:", self._idLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Name:", self._nameLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Version:", self._versionLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Status:", self._statusLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("System:", self._systemLabel)
        widget = QtWidgets.QWidget()
        widget.setLayout(formLayout)
        self.addWidget(self._table)
        self.addWidget(widget)
        self.setHandleWidth(2)
        self.setSizes((2 ** 16 * 2, 2 ** 16))
        for i in range(self.count()):
            self.handle(i).setPalette(Just.of(QtGui.QPalette()).apply(
                lambda x: x.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#EEEEEE"))).value())
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.selectionModel().currentRowChanged.connect(self._onCurrentRowChanged)
        self._app.languageChanged.connect(self._onLanguageChanged)
        self._pluginService.pluginEnabled.connect(self._onPluginStateChanged)
        self._pluginService.pluginDisabled.connect(self._onPluginStateChanged)
        self._pluginService.pluginsInserted.connect(self._onPluginsInserted)
        self._pluginService.pluginsRemoved.connect(self._onPluginsRemoved)
        self._table.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self._table.selectRow(0)

    def _onPluginStateChanged(self, plugin: Plugin):
        self._logger.info("On plugin state changed: %s", plugin)
        self._refreshTable()
        self._refreshLabels()

    def _onPluginsInserted(self, classes):
        self._logger.info("On plugins inserted: %s", classes)
        self._model.endResetModel()
        self._refreshLabels()

    def _onPluginsRemoved(self, plugins: typing.List[Plugin]) -> None:
        self._logger.info("On plugin removed: %s", plugins)
        self._model.endResetModel()
        self._refreshLabels()

    def _onCustomContextMenuRequested(self):
        self._logger.info("On custom context menu requested")
        row = [x.row() for x in self._table.selectionModel().selectedIndexes()][0]
        plugin = self._plugins[row]
        menu = QtWidgets.QMenu(self)
        menu.addAction("Add Plugin", self._onAddPlugin)
        menu.addAction("Enable Plugin" if plugin.disabled else "Disable Plugin",
            lambda: self._onEnableOrDisablePlugin(plugin))
        menu.addAction("Remove Plugin", lambda: self._onRemovePlugin(plugin))
        menu.exec_(QtGui.QCursor.pos())

    def _onRemovePlugin(self, plugin: Plugin):
        self._logger.info("On remove plugin %s", plugin.clazz)
        if plugin.clazz.isSystemPlugin():
            QtWidgets.QMessageBox.warning(self, "Warning", "System plugins are not allowed to be removed")
            return
        if self._pluginService.isPluginUsedInMainWindow(plugin):
            self._logger.info("Plugin is used in main window, can not be removed, return")
            QtWidgets.QMessageBox.warning(self, "Warning", "Plugin is used in main window, can not be removed")
            return
        self._logger.info("Do remove plugin")
        try:
            self._pluginService.removePlugin(plugin)
        except Exception as e:
            self._logger.info("Exception occurred: %s", e, e)
            QtWidgets.QMessageBox.warning(self, "Warning", "Remove plugin failed: %s" % e)
            return
        self._logger.info("Plugin removed")

    def _onAddPlugin(self):
        self._logger.info("On add plugin")
        filename = QtWidgets.QFileDialog.getExistingDirectory(self)
        if filename == "":
            self._logger.info("No folder selected, return")
            return
        try:
            self._pluginService.addPlugin(filename)
        except Exception as e:
            self._logger.info("Plugin parse failure: %s", e, e)
            QtWidgets.QMessageBox.warning(self, "Plugin Parse Failure", str(e))

    def _onEnableOrDisablePlugin(self, plugin: Plugin):
        self._logger.info("On enable or disable plugin")
        self._doEnablePlugin(plugin) if plugin.disabled else self._doDisablePlugin(plugin)

    def _doEnablePlugin(self, plugin: Plugin):
        self._logger.info("Do enable plugin")
        self._pluginService.enablePlugin(plugin)

    def _doDisablePlugin(self, plugin: Plugin):
        self._logger.info("Do disable plugin")
        if plugin.clazz.isSystemPlugin():
            QtWidgets.QMessageBox.warning(self, "Warning", "System plugins are not allowed to be disabled")
            return
        if self._pluginService.isPluginUsedInMainWindow(plugin):
            self._logger.info("Plugin used in main window, can not disable.")
            QtWidgets.QMessageBox.warning(self, "Warning", "Plugin used in main window, can not disable it.")
            return
        self._pluginService.disablePlugin(plugin)

    def _onCurrentRowChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        self._logger.info("On current row changed: %d -> %d", previous.row(), current.row())
        self._refreshLabels()

    def _refreshLabels(self):
        row = self._table.selectionModel().currentIndex().row()
        plugin = self._plugins[row]
        self._nameLabel.setText(plugin.clazz.getPluginName())
        self._versionLabel.setText(plugin.clazz.getPluginVersion())
        self._idLabel.setText(ClassUtils.fullname(plugin.clazz))
        self._statusLabel.setText("Disabled" if plugin.disabled else "Enabled")
        self._systemLabel.setText("YES" if plugin.clazz.isSystemPlugin() else "NO")

    def _refreshTable(self):
        topLeft = self._model.index(0, 0)
        bottomRight = self._model.index(self._model.rowCount() - 1, self._model.columnCount() - 1)
        self._model.dataChanged.emit(topLeft, bottomRight)

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        self._refreshTable()
        self._refreshLabels()


class PluginManagerModel(QtCore.QAbstractTableModel):
    def __init__(self, plugins: typing.List[Plugin], parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._plugins = plugins
        self._fields = ["Name", "Version", "System", "State"]

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
            return plugin.clazz.getPluginName()
        if column == 1:
            return plugin.clazz.getPluginVersion()
        if column == 2:
            return "YES" if plugin.clazz.isSystemPlugin() else "NO"
        if column == 3:
            return "Disabled" if plugin.disabled else "Enabled"
        raise RuntimeError("Impossible")
