# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40
import logging
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.widgets.configWidget import ConfigWidget
from IceSpringMusicPlayer.widgets.playlistManagerTable import PlaylistManagerTable
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class MaskWidget(QtWidgets.QWidget):
    _app: App
    _replaceable: typing.Union[ReplaceableMixin, QtWidgets.QWidget, None]

    def __init__(self, parent: QtWidgets.QMainWindow) -> None:
        super().__init__(parent)
        self._app = App.instance()
        self._replaceable = None
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self.setGeometry(parent.centralWidget().geometry())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            newReplaceable = self._calcReplaceable(event.pos())
            if self._replaceable is None or self._replaceable != newReplaceable:
                self._setReplaceable(newReplaceable)
            else:
                self._setReplaceable(None)

    def _setReplaceable(self, replaceable: typing.Union[ReplaceableMixin, QtWidgets.QWidget, None]) -> None:
        self._replaceable = replaceable
        self.repaint()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        if self._replaceable is not None:
            rect = QtCore.QRect(
                self.mapFromGlobal(self._replaceable.parent().mapToGlobal(self._replaceable.pos())),
                self._replaceable.size())
            QtGui.QPainter(self).fillRect(rect, QtGui.QColor("#55FF0000"))

    def _onCustomContextMenuRequested(self, pos: QtCore.QPoint) -> None:
        self._setReplaceable(self._calcReplaceable(pos))
        from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
        from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        menu = QtWidgets.QMenu(self)
        menu.addAction("Replace by horizontal splitter", lambda: self.doReplace(lambda: SplitterWidget(None, False, 2)))
        menu.addAction("Replace by vertical splitter", lambda: self.doReplace(lambda: SplitterWidget(None, True, 2)))
        menu.addAction("Replace by blank widget", lambda: self.doReplace(lambda: BlankWidget(None)))
        menu.addAction("Replace by controls widget", lambda: self.doReplace(lambda: ControlsWidget(None)))
        menu.addAction("Replace by lyrics widget", lambda: self.doReplace(lambda: LyricsWidget(None)))
        menu.addAction("Replace by playlist widget", lambda: self.doReplace(lambda: PlaylistTable(None)))
        menu.addAction("Replace by playlist manager", lambda: self.doReplace(lambda: PlaylistManagerTable(None)))
        menu.addAction("Replace by config widget", lambda: self.doReplace(lambda: ConfigWidget(None)))
        menu.addSeparator()
        for plugin in self._app.getPlugins():
            menu.addMenu(plugin.getLayoutMenu(menu, self))
        menu.addAction("Quit editing", self._doQuitEditing)
        menu.exec_(QtGui.QCursor.pos())
        self._setReplaceable(None)

    def _doQuitEditing(self):
        self._app.getMainWindow().setLayoutEditing(False)

    def doReplace(self, maker: typing.Callable[[], QtWidgets.QWidget]):
        logger = logging.getLogger("maskWidget")
        parent = self._replaceable.parentWidget()
        widget = maker()
        logger.info("Replacing %s with %s", self._replaceable, widget)
        assert isinstance(widget, (QtWidgets.QWidget, ReplaceableMixin))
        if isinstance(parent, QtWidgets.QMainWindow):
            logger.info("Parent is main window")
            parent.setCentralWidget(widget)
        elif isinstance(parent, QtWidgets.QSplitter):
            logger.info("Parent is splitter")
            parent.replaceWidget(parent.indexOf(self._replaceable), widget)
        else:
            logger.info("Parent is others")
            parent.layout().replaceWidget(self._replaceable, widget)
        self._replaceable.setParent(gg(None))
        self.raise_()
        self._app.getMainWindow().layoutChanged.emit()

    def _calcReplaceable(self, pos) -> ReplaceableMixin:
        widget = self.parent().centralWidget().childAt(pos)
        while (not isinstance(widget, ReplaceableMixin)) and (widget is not None):
            widget = widget.parentWidget()
        if widget is None:
            widget = self.parent().centralWidget()
        assert isinstance(widget, ReplaceableMixin)
        return widget
