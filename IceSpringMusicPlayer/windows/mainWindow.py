# Created by BaiJiFeiLong@gmail.com at 2022-01-03 11:06:37
import copy
import logging
import typing
from pathlib import Path

from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtGui, QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config, Element
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.timedeltaUtils import TimedeltaUtils
from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget
from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
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
    _maskWidget: typing.Optional[MaskWidget]

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
        self.setStyleSheet("QSplitterHandle { background: #EEEEEE }")
        self.layoutChanged.connect(self._onLayoutChanged)

    def getLayoutEditing(self) -> bool:
        return self._layoutEditing

    def _onLayoutChanged(self):
        self._logger.info("On layout changed")
        newLayout = self._widgetToElement(self.centralWidget())
        self._logger.info("New layout: %s", newLayout)
        self._config.layout = newLayout

    def _widgetToElement(self, widget: QtWidgets.QWidget) -> Element:
        from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin
        assert isinstance(widget, (ReplacerMixin, QtWidgets.QWidget))
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

    def _initMenu(self):
        fileMenu = self.menuBar().addMenu("&File")
        fileMenu.addAction("&Open", self._app.addMusicsFromFileDialog)
        viewMenu = self.menuBar().addMenu("&View")
        viewMenu.addAction("&Playlist Manager", lambda: PlaylistManagerDialog(self).show())

        controlsDownLayout = Element(clazz=SplitterWidget, vertical=True, weight=1, children=[
            Element(clazz=SplitterWidget, vertical=False, weight=7, children=[
                Element(clazz=PlaylistTable, vertical=False, weight=1, children=[]),
                Element(clazz=LyricsWidget, vertical=False, weight=1, children=[]),
            ]),
            Element(clazz=ControlsWidget, vertical=False, weight=1, children=[]),
        ])
        controlsUpLayout = Just.of(copy.deepcopy(controlsDownLayout)).apply(lambda x: x.children.reverse()).value()
        layoutMenu = self.menuBar().addMenu("&Layout")
        layoutMenu.addAction("&Playlist+Lyrics+Controls", lambda: self._changeLayout(controlsDownLayout))
        layoutMenu.addAction("&Controls+Playlist+Lyrics", lambda: self._changeLayout(controlsUpLayout))
        layoutMenu.addAction("&Default Layout", lambda: self._changeLayout(self._app.getDefaultLayout()))
        layoutMenu.addAction("De&mo Layout", lambda: self._changeLayout(self._app.getDemoLayout()))

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
        toolbar.addWidget(QtWidgets.QLabel("Playlist: ", toolbar))
        toolbar.addWidget(playlistCombo)
        toolbar.addAction(*gg(("One Key Add", self._app.addMusicsFromHomeFolder)))
        toolbar.addAction(*gg(("Play", self._player.play)))
        editingCheck = QtWidgets.QCheckBox("Editing", self)
        editingCheck.stateChanged.connect(self._onEditingCheckBoxStateChanged)
        toolbar.addWidget(editingCheck)
        self._playlistCombo = playlistCombo

    def _onEditingCheckBoxStateChanged(self, state: QtCore.Qt.CheckState):
        assert self._layoutEditing == (self._maskWidget is not None)
        self._logger.info("On editing check box state changed: %s", state)
        assert state in (QtCore.Qt.CheckState.Checked, QtCore.Qt.CheckState.Unchecked)
        self._layoutEditing = state == QtCore.Qt.CheckState.Checked
        if self._layoutEditing:
            self._logger.info("Create mask widget")
            self._maskWidget = MaskWidget(self)
            self._maskWidget.show()
            self.setStyleSheet("QSplitterHandle { background: red }")
        else:
            self._maskWidget.setParent(gg(None))
            self._maskWidget = None
            self.setStyleSheet("QSplitterHandle { background: #EEEEEE }")
        self._logger.info("> Signal layoutEditingChanged emitting...")
        self.layoutEditingChanged.emit(self._layoutEditing)
        self._logger.info("< Signal layoutEditingChanged emitted...")

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
