# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:33
import logging
import typing

import PySide2
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import unused
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.humanLabel import HumanLabel
from IceSpringMusicPlayer.controls.iceTableView import IceTableView
from IceSpringMusicPlayer.domains.config import Element
from IceSpringMusicPlayer.domains.plugin import Plugin
from IceSpringMusicPlayer.utils.classUtils import ClassUtils


class PluginManagerWidget(QtWidgets.QSplitter, PluginWidgetMixin):
    def __init__(self, parent: QtWidgets.QWidget = None, config: JsonSupport = None):
        super().__init__(parent)
        unused(config)
        self._logger = logging.getLogger("pluginManagerWidget")
        self._app = App.instance()
        self._mainWindow = self._app.getMainWindow()
        self._plugins = self._app.getConfig().plugins
        self._table = IceTableView()
        self._model = PluginManagerModel(self._plugins, self._table)
        self._table.setModel(self._model)
        self._table.setColumnWidth(0, 200)
        self._nameLabel = HumanLabel()
        self._versionLabel = HumanLabel()
        self._idLabel = HumanLabel()
        self._statusLabel = HumanLabel()
        formLayout = QtWidgets.QFormLayout()
        formLayout.setMargin(10)
        formLayout.addRow("ID:", self._idLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Name:", self._nameLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Version:", self._versionLabel)
        formLayout.addWidget(Just.of(QtWidgets.QWidget()).apply(lambda x: x.setFixedHeight(5)).value())
        formLayout.addRow("Status:", self._statusLabel)
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
        self._app.pluginStateChanged.connect(self._onPluginStateChanged)
        self._app.pluginsInserted.connect(self._onPluginsInserted)
        self._app.pluginRemoved.connect(self._onPluginRemoved)
        self._table.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self._table.selectRow(0)

    def _onPluginStateChanged(self):
        self._logger.info("On plugin state changed")
        self._refreshTable()
        self._refreshLabels()

    def _onPluginsInserted(self, classes):
        self._logger.info("On plugins inserted: %s", classes)
        self._model.endResetModel()
        self._refreshLabels()

    def _onPluginRemoved(self, plugin):
        self._logger.info("On plugin removed: %s", plugin.clazz)
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
        if self._isPluginUsedInMainWindow(plugin):
            self._logger.info("Plugin is used in main window, can not be removed, return")
            QtWidgets.QMessageBox.warning(self, "Warning", "Plugin is used in main window, can not be removed")
            return
        self._logger.info("Do remove plugin")
        try:
            self._app.removePlugin(plugin)
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
            classes = self._app.verifyPlugin(filename)
        except Exception as e:
            self._logger.info("Plugin parse failure: %s", e)
            QtWidgets.QMessageBox.warning(self, "Plugin Parse Failure", str(e))
            return
        if len(classes) == 0:
            self._logger.info("No Plugin Found")
            QtWidgets.QMessageBox.warning(self, "No Plugin Found", "No PluginMixin Found")
        self._logger.info("Found %d plugins: %s", len(classes), classes)
        self._logger.info("Register found plugins")
        self._app.registerNewPlugins(classes)

    def _onEnableOrDisablePlugin(self, plugin: Plugin):
        usedInMainWindow = self._isPluginUsedInMainWindow(plugin)
        self._logger.info("Plugin %s used in mainWindow: %s", plugin.clazz, usedInMainWindow)
        if not plugin.disabled:
            self._logger.info("Plugin enabled, disable it")
            if usedInMainWindow:
                self._logger.info("Plugin used in main window, can not disable.")
                QtWidgets.QMessageBox.warning(self, "Warning", "Plugin used in main window, can not disable it.")
                return
        else:
            self._logger.info("Plugin disabled, enable it")
        plugin.disabled = not plugin.disabled
        self._logger.info("> Signal app.pluginStateChanged emitting...")
        self._app.pluginStateChanged.emit()
        self._logger.info("> Signal app.pluginStateChanged emitted.")

    def _isPluginUsedInMainWindow(self, plugin: Plugin):
        layout = self._mainWindow.calcLayout()
        return self._isPluginUsedInElement(plugin, layout)

    def _isPluginUsedInElement(self, plugin: Plugin, element: Element):
        classes = plugin.clazz.getPluginWidgetClasses()
        usedInSelf = element.clazz in classes
        usedInChildren = any(self._isPluginUsedInElement(plugin, x) for x in element.children)
        return usedInSelf or usedInChildren

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
        self._fields = ["Name", "Version", "State"]

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
            return "Disabled" if plugin.disabled else "Enabled"
        raise RuntimeError("Impossible")
