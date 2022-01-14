# Created by BaiJiFeiLong@gmail.com at 2022/1/14 15:01
import logging
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtWidgets, QtGui


class ReplacerMixin(object):
    base = typing.Union[QtWidgets.QFrame, "ReplacerMixin"]
    _replacerLogger: logging.Logger

    def __init__(self: base):
        self._replacerLogger = logging.getLogger("replacerMixin")
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self.setMinimumWidth(30)
        self.setMinimumHeight(30)

    def _setStylesheetOnlySelf(self: base, stylesheet: str) -> None:
        objectName = self.objectName() if self.objectName() != "" else str(id(self))
        self.setObjectName(objectName)
        self.setStyleSheet("#%s {%s}" % (objectName, stylesheet))
        self.setStyleSheet(stylesheet)

    def _onCustomContextMenuRequested(self: base):
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        from IceSpringMusicPlayer.widgets.playlistTable import PlaylistTable
        oldStylesheet = self.styleSheet()
        self._setStylesheetOnlySelf(oldStylesheet + "* {background: pink}")
        menu = QtWidgets.QMenu()
        menu.addAction("Replace by horizontal splitter", lambda: self._doReplace(HorizontalSplitter(self, 2)))
        menu.addAction("Replace by vertical splitter", lambda: self._doReplace(VerticalSplitter(self, 2)))
        menu.addAction("Replace by button widget", lambda: self._doReplace(ButtonWidget(self)))
        menu.addAction("Replace by blank widget", lambda: self._doReplace(BlankWidget(self)))
        menu.addAction("Replace by controls widget", lambda: self._doReplace(ControlsPanel(self)))
        menu.addAction("Replace by lyrics widget", lambda: self._doReplace(LyricsPanel(self)))
        menu.addAction("Replace by playlist widget", lambda: self._doReplace(PlaylistTable(self)))
        # menu.addAction("Replace by controls widget", self._doReplaceControlsWidget)
        menu.exec_(QtGui.QCursor.pos())
        self._setStylesheetOnlySelf(oldStylesheet)

    def _doReplaceControlsWidget(self: base):
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        widget = ControlsPanel(self)
        self._doReplace(widget)

    def _doReplace(self: base, widget):
        self._replacerLogger.info("Replacing %s with %s", self, widget)
        parent = self.parentWidget()
        if isinstance(parent, QtWidgets.QMainWindow):
            self._replacerLogger.info("Parent is main window")
            parent.setCentralWidget(widget)
        elif isinstance(parent, QtWidgets.QSplitter):
            self._replacerLogger.info("Parent is splitter")
            parent.replaceWidget(parent.indexOf(self), widget)
        else:
            self._replacerLogger.info("Parent is others")
            self.parentWidget().layout().replaceWidget(self, ButtonWidget(self.parentWidget()))
        self.setParent(gg(None))


class BlankWidget(QtWidgets.QFrame, ReplacerMixin):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        ReplacerMixin.__init__(self)
        self.setLayout(QtWidgets.QGridLayout(self))
        label = QtWidgets.QLabel("BLANK", self)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.layout().addWidget(label)


class ButtonWidget(QtWidgets.QFrame, ReplacerMixin):
    def __init__(self, parent):
        super().__init__(parent)
        ReplacerMixin.__init__(self)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(Button("CLICK", self))


class SplitterWidget(QtWidgets.QSplitter, ReplacerMixin):
    def __init__(self, parent=None, vertical=False, children=0):
        orientation = QtCore.Qt.Orientation.Vertical if vertical else QtCore.Qt.Orientation.Horizontal
        super().__init__(orientation, parent)
        ReplacerMixin.__init__(self)
        self.setHandleWidth(3)
        self.setStyleSheet("QSplitter::handle { background: red }")
        self.setSizes([2 ** 16 for _ in range(children)])
        for _ in range(children):
            self.addWidget(BlankWidget(self))


class HorizontalSplitter(SplitterWidget):
    def __init__(self, parent=None, children=0):
        super().__init__(parent, False, children)


class VerticalSplitter(SplitterWidget):
    def __init__(self, parent=None, children=0):
        super().__init__(parent, True, children)


class Button(QtWidgets.QPushButton):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
