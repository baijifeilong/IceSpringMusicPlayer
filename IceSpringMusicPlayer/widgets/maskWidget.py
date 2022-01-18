# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40
import logging
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin


class MaskWidget(QtWidgets.QWidget):
    _replacer: typing.Union[ReplacerMixin, QtWidgets.QWidget, None]

    def __init__(self, parent: QtWidgets.QMainWindow) -> None:
        super().__init__(parent)
        self._replacer = None
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self.setGeometry(parent.centralWidget().geometry())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            newReplacer = self._calcReplacer(event.pos())
            if self._replacer is None or self._replacer != newReplacer:
                self._setReplacer(newReplacer)
            else:
                self._setReplacer(None)

    def _setReplacer(self, replacer: typing.Union[ReplacerMixin, QtWidgets.QWidget, None]) -> None:
        self._replacer = replacer
        self.repaint()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        if self._replacer is not None:
            rect = QtCore.QRect(
                self.mapFromGlobal(self._replacer.parent().mapToGlobal(self._replacer.pos())), self._replacer.size())
            QtGui.QPainter(self).fillRect(rect, QtGui.QColor("#55FF0000"))

    def _onCustomContextMenuRequested(self, pos: QtCore.QPoint) -> None:
        self._setReplacer(self._calcReplacer(pos))
        from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
        from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        menu = QtWidgets.QMenu(self)
        menu.addAction("Replace by horizontal splitter", lambda: self._doReplace(SplitterWidget(self, False, 2)))
        menu.addAction("Replace by vertical splitter", lambda: self._doReplace(SplitterWidget(self, True, 2)))
        menu.addAction("Replace by blank widget", lambda: self._doReplace(BlankWidget(self)))
        menu.addAction("Replace by controls widget", lambda: self._doReplace(ControlsWidget(self)))
        menu.addAction("Replace by lyrics widget", lambda: self._doReplace(LyricsWidget(self)))
        menu.addAction("Replace by playlist widget", lambda: self._doReplace(PlaylistTable(self)))
        menu.exec_(QtGui.QCursor.pos())
        self._setReplacer(None)

    def _doReplace(self, widget):
        logger = logging.getLogger("maskWidget")
        logger.info("Replacing %s with %s", self._replacer, widget)
        assert isinstance(widget, (QtWidgets.QWidget, ReplacerMixin))
        parent = self._replacer.parentWidget()
        if isinstance(parent, QtWidgets.QMainWindow):
            logger.info("Parent is main window")
            parent.setCentralWidget(widget)
        elif isinstance(parent, QtWidgets.QSplitter):
            logger.info("Parent is splitter")
            parent.replaceWidget(parent.indexOf(self._replacer), widget)
        else:
            logger.info("Parent is others")
            parent.layout().replaceWidget(self._replacer, widget)
        self._replacer.setParent(gg(None))
        self.raise_()
        App.instance().getMainWindow().layoutChanged.emit()

    def _calcReplacer(self, pos) -> ReplacerMixin:
        widget = self.parent().centralWidget().childAt(pos)
        while (not isinstance(widget, ReplacerMixin)) and (widget is not None):
            widget = widget.parentWidget()
        if widget is None:
            widget = self.parent().centralWidget()
        assert isinstance(widget, ReplacerMixin)
        return widget
