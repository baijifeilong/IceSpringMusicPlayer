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

    def _onCustomContextMenuRequested(self: base):
        from IceSpringMusicPlayer.widgets.controlsPanel import ControlsPanel
        from IceSpringMusicPlayer.widgets.lyricsPanel import LyricsPanel
        oldBackgroundColor = self.palette().color(self.backgroundRole())
        self._setStylesheetOnlySelf("background: pink")
        menu = QtWidgets.QMenu(self)
        menu.addAction("Replace by horizontal splitter", lambda: self._doReplace(SplitterWidget(False, self)))
        menu.addAction("Replace by vertical splitter", lambda: self._doReplace(SplitterWidget(True, self)))
        menu.addAction("Replace by button widget", lambda: self._doReplace(ButtonWidget(self)))
        menu.addAction("Replace by blank widget", lambda: self._doReplace(BlankWidget(self)))
        menu.addAction("Replace by controls widget", lambda: self._doReplace(ControlsPanel(self)))
        menu.addAction("Replace by lyrics widget", lambda: self._doReplace(LyricsPanel(self)))
        # menu.addAction("Replace by controls widget", self._doReplaceControlsWidget)
        menu.exec_(QtGui.QCursor.pos())
        self._setStylesheetOnlySelf(f"background: {oldBackgroundColor.name()}")

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
        if isinstance(parent, QtWidgets.QSplitter):
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


class ButtonWidget(QtWidgets.QFrame, ReplacerMixin):
    def __init__(self, parent):
        super().__init__(parent)
        ReplacerMixin.__init__(self)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(Button("CLICK", self))


class SplitterWidget(QtWidgets.QSplitter, ReplacerMixin):
    def __init__(self, vertical=False, parent=None):
        orientation = QtCore.Qt.Orientation.Vertical if vertical else QtCore.Qt.Orientation.Horizontal
        super().__init__(orientation, parent)
        ReplacerMixin.__init__(self)
        self.setHandleWidth(3)
        self.setSizes([2 ** 16, 2 ** 16])
        self.setStyleSheet("QSplitter::handle { background: red }")
        self.addWidget(BlankWidget(self))
        self.addWidget(BlankWidget(self))


class Button(QtWidgets.QPushButton):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
