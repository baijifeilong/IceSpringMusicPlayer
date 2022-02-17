# Created by BaiJiFeiLong@gmail.com at 2022/1/17 12:40
import logging
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore, QtGui

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.replacerMixin import ReplacerMixin
from IceSpringMusicPlayer.widgets.blankWidget import BlankWidget
from IceSpringMusicPlayer.widgets.splitterWidget import SplitterWidget


class MaskWidget(QtWidgets.QWidget):
    _app: App
    _replaceable: typing.Union[ReplacerMixin, QtWidgets.QWidget, None]

    def __init__(self, parent: QtWidgets.QMainWindow) -> None:
        super().__init__(parent)
        self._parent = parent
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

    def _setReplaceable(self, replaceable: typing.Union[ReplacerMixin, QtWidgets.QWidget, None]) -> None:
        self._replaceable = replaceable
        self.repaint()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        if self._replaceable is not None:
            rect = QtCore.QRect(
                self.mapFromGlobal(self._replaceable.parentWidget().mapToGlobal(self._replaceable.pos())),
                self._replaceable.size())
            QtGui.QPainter(self).fillRect(rect, QtGui.QColor("#55FF0000"))

    def _onCustomContextMenuRequested(self, pos: QtCore.QPoint) -> None:
        self._setReplaceable(self._calcReplaceable(pos))
        menu = QtWidgets.QMenu(self)
        menu.addAction(tt.MaskWidget_ReplaceWithBlankWidget, lambda: self._doReplace(BlankWidget()))
        horizontalMenu = menu.addMenu(tt.MaskWidget_HorizontallySplitTo)
        for i in range(2, 10):
            horizontalMenu.addAction(tt.MaskWidget_NColumns.format(i),
                lambda i=i: self._doReplace(SplitterWidget(False, i)))
        verticalMenu = menu.addMenu(tt.MaskWidget_VerticallySplitTo)
        for i in range(2, 10):
            verticalMenu.addAction(tt.MaskWidget_NRows.format(i),
                lambda i=i: self._doReplace(SplitterWidget(True, i)))
        menu.addSeparator()
        for plugin in self._app.getConfig().plugins:
            replacers = plugin.clazz.getPluginReplacers()
            if (not plugin.disabled) and len(replacers) > 0:
                pluginMenu = menu.addMenu(plugin.clazz.getPluginName())
                for k, v in replacers.items():
                    pluginMenu.addAction(k, lambda v=v: self._doReplace(v()))
        menu.addSeparator()
        menu.addAction(tt.MaskWidget_QuitEditingMode, self._doQuitEditing)
        menu.exec_(QtGui.QCursor.pos())
        self._setReplaceable(None)

    def _doQuitEditing(self):
        self._app.getMainWindow().setLayoutEditing(False)

    def _doReplace(self, widget: ReplacerMixin):
        assert isinstance(widget, QtWidgets.QWidget)
        logger = logging.getLogger("maskWidget")
        parent = self._replaceable.parentWidget()
        logger.info("Replacing %s with %s", self._replaceable, widget)
        assert isinstance(widget, (QtWidgets.QWidget, ReplacerMixin))
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

    def _calcReplaceable(self, pos) -> ReplacerMixin:
        widget = self._parent.centralWidget().childAt(pos)
        while (not isinstance(widget, ReplacerMixin)) and (widget is not None):
            widget = widget.parentWidget()
        if widget is None:
            widget = self._parent.centralWidget()
        assert isinstance(widget, ReplacerMixin)
        return widget
