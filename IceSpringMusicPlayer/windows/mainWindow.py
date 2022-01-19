# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37
import logging
import typing
from pathlib import Path

from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget
from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
from IceSpringMusicPlayer.windows.playlistManagerDialog import PlaylistManagerDialog


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
        self._config = App.instance().getConfig()
        self._player = App.instance().getPlayer()
        self._layoutEditing = False
        self._maskWidget = None
        self._initPlayer()
        self._initMenu()
        self._initToolbar()
        self._initStatusBar()
        self.layoutChanged.connect(self._onLayoutChanged)
        self.layoutEditingChanged.connect(self._onLayoutEditingChanged)
        self._app.languageChanged.connect(self._onLanguageChanged)

    def getLayoutEditing(self) -> bool:
        return self._layoutEditing

    def _onLayoutChanged(self):
        self._logger.info("On layout changed")
        newLayout = self._widgetToElement(self.centralWidget())
        self._logger.info("New layout: %s", newLayout)
        self._config.layout = newLayout

    def _widgetToElement(self, widget: QtWidgets.QWidget) -> Element:
        from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin
        assert isinstance(widget, (ReplaceableMixin, QtWidgets.QWidget))
        return Element(
            clazz=type(widget),
            vertical=isinstance(widget, QtWidgets.QSplitter) and widget.orientation() == QtCore.Qt.Orientation.Vertical,
            weight=widget.height() if isinstance(widget.parentWidget(), QtWidgets.QSplitter) and gg(
                widget.parentWidget()).orientation() == QtCore.Qt.Orientation.Vertical else widget.width(),
            children=[self._widgetToElement(widget.widget(x)) for x in range(widget.count())] if isinstance(
                widget, QtWidgets.QSplitter) else []
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
        self.centralWidget().setAutoFillBackground(True)
        self.centralWidget().setPalette(Just.of(QtGui.QPalette()).apply(
            lambda x: x.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))).value())

    def _drawElement(self, element: Element, parent: QtWidgets.QWidget) -> None:
        self._logger.info("Draw element: %s to %s", element.clazz, parent)
        widget = element.clazz(parent)
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

    def _initPlayer(self):
        self._player.frontPlaylistIndexChanged.connect(self._onFrontPlaylistChangedAtIndex)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        self._player.playlistInserted.connect(self._onPlaylistInserted)
        self._player.currentMusicIndexChanged.connect(self._onMusicIndexChanged)

    def _initStatusBar(self):
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
        self._logger.info("Refresh view")
        self._fileMenu.setTitle(tt.Menu_File)
        self._fileOpenAction.setText(tt.Menu_File_Open)
        self._viewMenu.setTitle(tt.Menu_View)
        self._viewPlaylistManagerAction.setText(tt.Menu_View_PlaylistManager)
        self._layoutMenu.setTitle(tt.Menu_Layout)
        self._layoutControlsDownAction.setText(tt.Menu_Layout_ControlsDown)
        self._layoutControlsUpAction.setText(tt.Menu_Layout_ControlsUp)
        self._layoutDefaultAction.setText(tt.Menu_Layout_Default)
        self._layoutDemoAction.setText(tt.Menu_Layout_Demo)
        self._languageMenu.setTitle(tt.Menu_Language)
        self._languageEnglishAction.setText(tt.Menu_Language_English)
        self._languageChineseAction.setText(tt.Menu_Language_Chinese)
        self._testMenu.setTitle(tt.Menu_Test)
        self._testOneKeyAddAction.setText(tt.Menu_Test_OneKeyAdd)
        self._testLoadTestDataAction.setText(tt.Menu_Test_LoadTestData)
        self._playlistLabel.setText(tt.Toolbar_Playlist)
        self._editingCheck.setText(tt.Toolbar_Editing)
        self._toggleLanguageAction.setText(tt.Toolbar_ToggleLanguage)
        self._logger.info("View refreshed")

    def _initMenu(self):
        self._fileMenu = self.menuBar().addMenu(tt.Menu_File)
        self._fileOpenAction = self._fileMenu.addAction(tt.Menu_File_Open)
        self._fileOpenAction.triggered.connect(self._app.addMusicsFromFileDialog)

        self._viewMenu = self.menuBar().addMenu(tt.Menu_View)
        self._viewPlaylistManagerAction = self._viewMenu.addAction(
            tt.Menu_View_PlaylistManager, lambda: PlaylistManagerDialog(self).show())

        self._layoutMenu = self.menuBar().addMenu(tt.Menu_Layout)
        self._layoutControlsDownAction = self._layoutMenu.addAction(
            tt.Menu_Layout_ControlsDown, lambda: self._changeLayout(self._config.getControlsDownLayout()))
        self._layoutControlsUpAction = self._layoutMenu.addAction(
            tt.Menu_Layout_ControlsUp, lambda: self._changeLayout(self._config.getControlsUpLayout()))
        self._layoutDefaultAction = self._layoutMenu.addAction(
            tt.Menu_Layout_Default, lambda: self._changeLayout(self._config.getDefaultLayout()))
        self._layoutDemoAction = self._layoutMenu.addAction(
            tt.Menu_Layout_Demo, lambda: self._changeLayout(self._config.getDemoLayout()))

        self._languageMenu = self.menuBar().addMenu(tt.Menu_Language)
        self._languageEnglishAction = self._languageMenu.addAction(
            tt.Menu_Language_English, lambda: self._app.changeLanguage("en_US"))
        self._languageChineseAction = self._languageMenu.addAction(
            tt.Menu_Language_Chinese, lambda: self._app.changeLanguage("zh_CN"))

        self._testMenu = self.menuBar().addMenu(tt.Menu_Test)
        self._testOneKeyAddAction = self._testMenu.addAction(
            tt.Menu_Test_OneKeyAdd, lambda: self._app.addMusicsFromHomeFolder())
        self._testLoadTestDataAction = self._testMenu.addAction(
            tt.Menu_Test_LoadTestData, lambda: self._app.loadTestData())

    def _onPlaylistComboActivated(self, index: int) -> None:
        self._logger.info("On playlist combo activated at index %d", index)
        self._player.setFrontPlaylistIndex(index)

    def _onFrontPlaylistChangedAtIndex(self, oldIndex: int, newIndex: int) -> None:
        self._logger.info("On front playlist changed at index: %d => %d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("Front playlist set to index -1, skip")
        else:
            self._logger.info("Front playlist set to index %d, refreshing main window", newIndex)
            self._logger.info("Updating playlist combo")
            self._playlistCombo.setCurrentIndex(newIndex)
            self._logger.info("Main window refreshed")

    def _initToolbar(self):
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        playlistCombo = QtWidgets.QComboBox(toolbar)
        playlistCombo.addItems([x.name for x in self._player.getPlaylists()])
        playlistCombo.setCurrentIndex(self._player.getFrontPlaylistIndex())
        playlistCombo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        playlistCombo.activated.connect(self._onPlaylistComboActivated)
        self._playlistLabel = QtWidgets.QLabel(tt.Toolbar_Playlist, toolbar)
        toolbar.addWidget(self._playlistLabel)
        toolbar.addWidget(playlistCombo)
        toolbar.addAction(self._testOneKeyAddAction)
        toolbar.addAction(self._testLoadTestDataAction)
        self._editingCheck = QtWidgets.QCheckBox(tt.Toolbar_Editing, self)
        self._editingCheck.stateChanged.connect(self._onEditingCheckBoxStateChanged)
        toolbar.addWidget(self._editingCheck)
        self._toggleLanguageAction = toolbar.addAction(tt.Toolbar_ToggleLanguage)
        self._toggleLanguageAction.triggered.connect(
            lambda: self._app.changeLanguage("zh_CN" if self._config.language == "en_US" else "en_US"))
        self._playlistCombo = playlistCombo

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

    def _onPlaylistInserted(self, index: int) -> None:
        playlist = self._player.getPlaylists()[index]
        self._logger.info("On playlist inserted: %s", playlist.name)
        self._playlistCombo.addItem(playlist.name)

    def _onPlaylistsRemovedAtIndexes(self, indexes: typing.List[int]):
        self._logger.info("On playlist removed: %s", indexes)
        for index in sorted(indexes, reverse=True):
            self._playlistCombo.removeItem(index)

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
