# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37
import inspect
import logging
import typing
from pathlib import Path

from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils
from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget
from IceSpringMusicPlayer.widgets.playlistSelector import PlaylistSelector
from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
from IceSpringMusicPlayer.windows.configDialog import ConfigDialog


class MainWindow(QtWidgets.QMainWindow):
    layoutChanged: QtCore.SignalInstance = QtCore.Signal()
    layoutEditingChanged: QtCore.SignalInstance = QtCore.Signal(bool)

    _app: App
    _config: Config
    _player: Player
    _statusLabel: QtWidgets.QLabel
    _playlistCombo: QtWidgets.QComboBox
    _layoutEditing: bool
    _editingCheck: QtWidgets.QCheckBox
    _maskWidget: typing.Optional[MaskWidget]
    _fileMenu: QtWidgets.QMenu

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("mainWindow")
        self._positionLogger = logging.getLogger("position")
        self._positionLogger.setLevel(logging.INFO)
        self._app = App.instance()
        self._playlistService = self._app.getPlaylistService()
        self._pluginService = self._app.getPluginService()
        self._configService = self._app.getConfigService()
        self._config = App.instance().getConfig()
        self._player = App.instance().getPlayer()
        self._layoutEditing = False
        self._maskWidget = None
        self._initPalette()
        self._menuToolbar = self.addToolBar("Menu")
        self._playlistToolbar = self.addToolBar("Playlist")
        self._setupMenuToolbar()
        self._setupPlaylistToolbar()
        self._initStatusBar()
        self.layoutChanged.connect(self._onLayoutChanged)
        self.layoutEditingChanged.connect(self._onLayoutEditingChanged)
        self._app.languageChanged.connect(self._onLanguageChanged)
        self._pluginService.pluginEnabled.connect(self._setupPluginMenu)
        self._pluginService.pluginDisabled.connect(self._setupPluginMenu)
        self._pluginService.pluginsInserted.connect(self._setupPluginMenu)
        self._pluginService.pluginsRemoved.connect(self._setupPluginMenu)
        self._playlistService.musicParsed.connect(self._onMusicParsed)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        self._player.currentMusicIndexChanged.connect(self._onMusicIndexChanged)

    def _onMusicParsed(self, progress: int, total: int, music: Music):
        self._logger.info("On music parsed: %d/%d %s", progress, total, music.filename)
        self.statusBar().showMessage("Added %d/%d %s" % (progress, total, music.filename))
        QtCore.QCoreApplication.processEvents()

    def _initPalette(self):
        self.setPalette(Just.of(QtGui.QPalette()).apply(
            lambda x: x.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))).value())

    def getLayoutEditing(self) -> bool:
        return self._layoutEditing

    def _onLayoutChanged(self):
        self._logger.info("On layout changed")
        newLayout = self._widgetToElement(self.centralWidget())
        self._logger.info("New layout: %s", newLayout)
        self._config.layout = newLayout

    def _widgetToElement(self, widget: QtWidgets.QWidget) -> Element:
        from IceSpringMusicPlayer.common.replacerMixin import ReplacerMixin
        assert isinstance(widget, (ReplacerMixin, QtWidgets.QWidget))
        return Element(
            clazz=type(widget),
            vertical=isinstance(widget, QtWidgets.QSplitter) and widget.orientation() == QtCore.Qt.Orientation.Vertical,
            weight=widget.height() if isinstance(widget.parentWidget(), QtWidgets.QSplitter) and gg(
                widget.parentWidget()).orientation() == QtCore.Qt.Orientation.Vertical else widget.width(),
            config=widget.getWidgetConfig() if isinstance(widget, PluginWidgetMixin) else dict(),
            children=[self._widgetToElement(widget.widget(x)) for x in range(widget.count())] if isinstance(
                widget, SplitterWidget) else []
        )

    def calcLayout(self) -> Element:
        return self._widgetToElement(self.centralWidget())

    def _changeLayout(self, layout: Element) -> None:
        self._logger.info("Change layout")
        self._config.layout = layout
        self.loadLayout(self._config.layout)

    def loadLayout(self, layout: Element) -> None:
        self._logger.info("Load layout")
        if self.centralWidget() is not None:
            self._logger.info("Central widget is not none, clear it")
            self.centralWidget().setParent(gg(None))
            assert self.centralWidget() is None
        self._drawElement(layout, self)

    def _drawElement(self, element: Element, parent: QtWidgets.QWidget) -> None:
        self._logger.info("Draw element: %s to %s", element.clazz, parent)
        if issubclass(element.clazz, PluginWidgetMixin) and "config" in inspect.signature(
                element.clazz.__init__).parameters.keys():
            widget = gg(element.clazz)(element.config)
        else:
            widget = element.clazz()
        if isinstance(widget, QtWidgets.QSplitter) and element.vertical:
            widget.setOrientation(QtCore.Qt.Orientation.Vertical)
        if isinstance(parent, QtWidgets.QMainWindow):
            self._logger.info("Parent is main window")
            parent.setCentralWidget(widget)
        elif isinstance(parent, QtWidgets.QSplitter):
            self._logger.info("Parent is splitter")
            parent.addWidget(widget)
            parent.setProperty("iceSizes", (parent.property("iceSizes") or ()) + (element.weight * 2 ** 16,))
            parent.setSizes(parent.property("iceSizes"))
        else:
            raise AssertionError("Unsupported parent: %s" % type(parent))
        for child in element.children:
            self._drawElement(child, widget)

    def _initStatusBar(self):
        self.statusBar().setAutoFillBackground(True)
        self.statusBar().setPalette(Just.of(QtGui.QPalette()).apply(lambda x: x.setColor(QtGui.QPalette.Window,
            QtGui.QPalette().color(QtGui.QPalette.ColorRole.Window))).value())
        statusLabel = QtWidgets.QLabel("", self.statusBar())
        statusLabel.setStyleSheet("margin: 0 15px")
        self.statusBar().addPermanentWidget(statusLabel)
        self.statusBar().showMessage("Ready.")
        self.statusBar().installEventFilter(self)
        self._statusLabel = statusLabel

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.statusBar() and event.type() == QtCore.QEvent.MouseButtonDblClick:
            self._onStatusBarDoubleClicked()
        return super().eventFilter(watched, event)

    def _onStatusBarDoubleClicked(self):
        self._logger.info("On status bar double clicked")
        self._logger.info("> Signal app.requestLocateCurrentMusic emitting...")
        self._app.requestLocateCurrentMusic.emit()
        self._logger.info("> Signal app.requestLocateCurrentMusic emitted.")

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        self._setupMenuToolbar()
        self._setupPlaylistToolbar()

    def _setupPluginMenu(self):
        self._pluginsMenu.clear()
        self._pluginsMenu.setTitle(tt.PluginsMenu)
        for plugin in self._config.plugins:
            items = plugin.clazz.getPluginMenus()
            if not plugin.disabled:
                menu = self._pluginsMenu.addMenu(plugin.clazz.getPluginName())
                menu.addAction(tt.PluginsMenu_AboutPlugin,
                    lambda plugin=plugin: QtWidgets.QMessageBox.about(QtWidgets.QApplication.activeWindow(),
                        tt.PluginsMenu_AboutPlugin, plugin.clazz.getPluginDescription()))
                for item in items:
                    item.setParent(menu)
                    if isinstance(item, QtWidgets.QMenu):
                        menu.addMenu(item)
                    else:
                        assert isinstance(item, QtWidgets.QAction)
                        menu.addAction(item)

    def _setupMenuToolbar(self):
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
        self._menuToolbar.clear()
        self._fileMenu = QtWidgets.QMenu(tt.FileMenu)
        self._fileOpenAction = self._fileMenu.addAction(tt.FileMenu_Open)
        self._fileOpenAction.triggered.connect(self._playlistService.addMusicsFromFileDialog)
        self._fileMenu.addSeparator()
        self._fileConfigAction = self._fileMenu.addAction(tt.FileMenu_Config)
        self._fileConfigAction.triggered.connect(lambda: ConfigDialog().exec_())
        self._viewMenu = QtWidgets.QMenu(tt.ViewMenu)
        self._viewPlaylistManagerAction = self._viewMenu.addAction(
            tt.ViewMenu_PlaylistManager, lambda: DialogUtils.execWidget(PlaylistManagerWidget(), withOk=True))
        self._layoutMenu = QtWidgets.QMenu(tt.LayoutMenu)
        self._layoutControlsDownAction = self._layoutMenu.addAction(
            tt.LayoutMenu_ControlsDown, lambda: self._changeLayout(self._configService.getControlsDownLayout()))
        self._layoutControlsUpAction = self._layoutMenu.addAction(
            tt.LayoutMenu_ControlsUp, lambda: self._changeLayout(self._configService.getControlsUpLayout()))
        self._layoutDefaultAction = self._layoutMenu.addAction(
            tt.LayoutMenu_Default, lambda: self._changeLayout(self._configService.getDefaultLayout()))
        self._editingAction = self._layoutMenu.addAction(tt.Toolbar_Editing)
        self._editingAction.setCheckable(True)
        self._editingAction.setChecked(self._layoutEditing)
        self._editingAction.triggered.connect(lambda: self.setLayoutEditing(not self._layoutEditing))
        self._pluginsMenu = QtWidgets.QMenu(tt.PluginsMenu)
        self._languageMenu = QtWidgets.QMenu(tt.LanguageMenu)
        self._languageEnglishAction = self._languageMenu.addAction(
            tt.LanguageMenu_English, lambda: self._app.changeLanguage("en_US"))
        self._languageChineseAction = self._languageMenu.addAction(
            tt.LanguageMenu_Chinese, lambda: self._app.changeLanguage("zh_CN"))
        self._testMenu = QtWidgets.QMenu(tt.TestMenu)
        self._testOneKeyAddAction = self._testMenu.addAction(
            tt.TestMenu_OneKeyAdd, lambda: self._playlistService.addMusicsFromFolder("~/Music"))
        self._testLoadTestDataAction = self._testMenu.addAction(
            tt.TestMenu_LoadTestData, lambda: self._playlistService.loadTestData())
        self._toggleLanguageAction = self._testMenu.addAction(tt.TestMenu_ToggleLanguage)
        self._toggleLanguageAction.triggered.connect(
            lambda: self._app.changeLanguage("zh_CN" if self._config.language == "en_US" else "en_US"))
        self._setupPluginMenu()
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.FileMenu, self._fileMenu))
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.ViewMenu, self._viewMenu))
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.LayoutMenu, self._layoutMenu))
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.PluginsMenu, self._pluginsMenu))
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.LanguageMenu, self._languageMenu))
        self._menuToolbar.addWidget(WidgetUtils.createMenuButton(tt.TestMenu, self._testMenu))

    def _setupPlaylistToolbar(self):
        self._playlistToolbar.clear()
        self._playlistToolbar.addWidget(WidgetUtils.createHorizontalSpacer(5))
        self._playlistToolbar.addWidget(PlaylistSelector())

    def setLayoutEditing(self, editing: bool) -> None:
        self._layoutEditing = editing
        self._logger.info("> Signal layoutEditingChanged emitting...")
        self.layoutEditingChanged.emit(editing)
        self._logger.info("< Signal layoutEditingChanged emitted...")

    def _onLayoutEditingChanged(self, editing: bool) -> None:
        if editing:
            self._logger.info("Create mask widget")
            self._maskWidget = MaskWidget(self)
            self._maskWidget.show()
        else:
            self._maskWidget.setParent(gg(None))
            self._maskWidget = None
        self._editingCheck.blockSignals(True)
        self._editingCheck.setChecked(editing)
        self._editingCheck.blockSignals(False)
        self._logger.info("Refresh splitter handles")
        for widget in self.findChildren(SplitterWidget):
            gg(widget, SplitterWidget).refreshHandles()

    def _onEditingCheckBoxStateChanged(self, state: QtCore.Qt.CheckState):
        assert self._layoutEditing == (self._maskWidget is not None)
        self._logger.info("On editing check box state changed: %s", state)
        assert state in (QtCore.Qt.CheckState.Checked, QtCore.Qt.CheckState.Unchecked)
        self.setLayoutEditing(state == QtCore.Qt.CheckState.Checked)

    def _onMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("Music index changed: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("Music index set to -1, player stopped.")
            self._logger.info("Clear status label")
            self._statusLabel.setText("")
            self._logger.info("Notify stopped on status bar")
            self.statusBar().showMessage("Stopped.")
        currentMusic = self._player.getCurrentPlaylist().orElseThrow(AssertionError).musics[newIndex]
        self._logger.info("Current music: %s", currentMusic)
        self._logger.info("Update window title")
        self.setWindowTitle(Path(currentMusic.filename).with_suffix("").name)
        self._logger.info("Update status label")
        self._statusLabel.setText("{} - {}".format(currentMusic.artist, currentMusic.title))

    def _onPlayerPositionChanged(self, position):
        self._positionLogger.debug("Player position changed: %d / %d", position, self._player.getDuration())
        if self._player.getState().isStopped():
            self._logger.info("Player has been stopped, skip")
            return
        duration = self._player.getDuration()
        progressText = f"{TimedeltaUtils.formatDelta(position)}/{TimedeltaUtils.formatDelta(duration)}"
        currentMusic = self._player.getCurrentMusic().orElseThrow(AssertionError)
        self._positionLogger.debug("Update status bar")
        self.statusBar().showMessage("{} | {} kbps | {} Hz | {} channels | {}".format(
            currentMusic.format, currentMusic.bitrate,
            currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self._config.geometry = self.geometry()
        if self._maskWidget is not None:
            self._maskWidget.raise_()
            self._maskWidget.setGeometry(self.centralWidget().geometry())

    def moveEvent(self, event: QtGui.QMoveEvent) -> None:
        self._config.geometry = self.geometry()
