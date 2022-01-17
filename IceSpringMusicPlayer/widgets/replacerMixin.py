# Created by BaiJiFeiLong@gmail.com at 2022/1/14 15:01

import logging
import typing

from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtWidgets, QtGui

from IceSpringMusicPlayer.app import App


class ReplacerMixin(object):
    base = typing.Union[QtWidgets.QFrame, "ReplacerMixin"]

    def __init__(self: base):
        for target in self._calcTargets():
            target.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.setMinimumWidth(30)
        self.setMinimumHeight(30)
        if App.instance().getMainWindow().getLayoutEditing():
            for target in self._calcTargets():
                target.customContextMenuRequested.connect(self._replacerOnContextMenuRequested)
        App.instance().getMainWindow().layoutEditingChanged.connect(self._replacerOnLayoutEditingChanged)

    def _calcTargets(self) -> typing.List[typing.Union["ReplacerMixin", QtWidgets.QWidget, QtWidgets.QTableView]]:
        if isinstance(self, QtWidgets.QTableView):
            return [self, self.horizontalHeader(), self.verticalHeader()]
        return [self]

    def _replacerOnLayoutEditingChanged(self: base, editing: bool) -> None:
        logger = logging.getLogger("replacerMixin")
        logger.info("On layout editing changed: %s", editing)
        if editing:
            for target in self._calcTargets():
                target.customContextMenuRequested.connect(self._replacerOnContextMenuRequested)
        else:
            for target in self._calcTargets():
                target.customContextMenuRequested.disconnect(self._replacerOnContextMenuRequested)

    def _replacerOnContextMenuRequested(self: base):
        from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget
        from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget
        from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget
        from IceSpringMusicPlayer.widgets.controlsWidget import ControlsWidget
        from IceSpringMusicPlayer.widgets.lyricsWidget import LyricsWidget
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        Just.of(MaskWidget(self)).apply(lambda x: x.deleteLater()).value().show()
        menu = QtWidgets.QMenu(self)
        menu.addAction("Replace by horizontal splitter", lambda: self._doReplace(SplitterWidget(self, False, 2)))
        menu.addAction("Replace by vertical splitter", lambda: self._doReplace(SplitterWidget(self, True, 2)))
        menu.addAction("Replace by blank widget", lambda: self._doReplace(BlankWidget(self)))
        menu.addAction("Replace by controls widget", lambda: self._doReplace(ControlsWidget(self)))
        menu.addAction("Replace by lyrics widget", lambda: self._doReplace(LyricsWidget(self)))
        menu.addAction("Replace by playlist widget", lambda: self._doReplace(PlaylistTable(self)))
        menu.exec_(QtGui.QCursor.pos())

    def _doReplace(self: base, widget):
        logger = logging.getLogger("replacerMixin")
        logger.info("Replacing %s with %s", self, widget)
        assert isinstance(widget, (QtWidgets.QWidget, ReplacerMixin))
        parent = self.parentWidget()
        if isinstance(parent, QtWidgets.QMainWindow):
            logger.info("Parent is main window")
            parent.setCentralWidget(widget)
        elif isinstance(parent, QtWidgets.QSplitter):
            logger.info("Parent is splitter")
            parent.replaceWidget(parent.indexOf(self), widget)
        else:
            logger.info("Parent is others")
            parent.layout().replaceWidget(self, widget)
        self.setParent(gg(None))
        App.instance().getMainWindow().layoutChanged.emit()
