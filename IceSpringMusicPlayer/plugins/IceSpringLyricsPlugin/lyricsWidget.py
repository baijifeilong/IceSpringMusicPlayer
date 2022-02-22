# Created by BaiJiFeiLong@gmail.com at 2022/1/12 20:39
import logging
import time
import typing
from typing import Any

from IceSpringPathLib import Path
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtGui, QtCore

import IceSpringLyricsPlugin.lyricsTranslation as tt
from IceSpringLyricsPlugin.lyricsWidgetConfig import LyricsWidgetConfig
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.controls.clickableLabel import ClickableLabel
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringMusicPlayer.utils.lyricUtils import LyricUtils


class LyricsWidget(QtWidgets.QScrollArea, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()
    _app: App
    _widgetConfig: LyricsWidgetConfig
    _player: Player
    _layout: QtWidgets.QVBoxLayout

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return LyricsWidgetConfig

    def getWidgetConfig(self) -> LyricsWidgetConfig:
        return self._widgetConfig

    def __init__(self, config=None):
        super().__init__()
        self._widgetConfig = config or LyricsWidgetConfig.getDefaultObject()
        self._logger = logging.getLogger("lyricsWidget")
        self._logger.setLevel(logging.INFO)
        self._app = App.instance()
        self._player = self._app.getPlayer()
        self._lyrics: typing.Dict[int, str] = dict()
        self._prevLyricIndex = -1
        self._timer = QtCore.QTimer()
        self._loadConfig()
        self._setupView()
        self._resetLayout()
        self._setupLyrics()
        self.horizontalScrollBar().rangeChanged.connect(
            lambda *args, bar=self.horizontalScrollBar(): bar.setValue((bar.maximum() + bar.minimum()) // 2))
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self._player.stateChanged.connect(self.onPlayerStateChanged)
        self._player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        self._player.positionChanged.connect(self._onTick)
        self._timer.timeout.connect(self._onTick)

    def _setupView(self):
        self.setWidget(QtWidgets.QWidget(self))
        layout = QtWidgets.QVBoxLayout(self.widget())
        layout.setMargin(0)
        layout.setSpacing(1)
        self.widget().setLayout(layout)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self._layout = layout
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.setPalette(Just.of(self.palette()).apply(
            lambda x: x.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))).value())

    def onPlayerStateChanged(self, state: PlayerState):
        self._logger.info("On player state changed: %s", state)
        if state.isPlaying():
            self._timer.start(100)
        else:
            self._timer.stop()

    def _loadConfig(self):
        policies = dict(AUTO=QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            ON=QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn, OFF=QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFont(self._widgetConfig.font)
        self.setHorizontalScrollBarPolicy(policies[self._widgetConfig.horizontalScrollBarPolicy])
        self.setVerticalScrollBarPolicy(policies[self._widgetConfig.verticalScrollBarPolicy])

    def _onCustomContextMenuRequested(self) -> None:
        from IceSpringLyricsPlugin.lyricsWidgetConfigDialog import LyricsWidgetConfigDialog
        self._logger.info("On custom context menu requested")
        menu = QtWidgets.QMenu(self)
        menu.addAction(tt.Plugins_ConfigWidget, lambda: LyricsWidgetConfigDialog(self).exec_())
        menu.addAction(tt.Plugins_ToggleFullscreen, lambda: LayoutUtils.toggleFullscreen(self))
        menu.exec_(QtGui.QCursor.pos())

    def _resetLayout(self):
        LayoutUtils.clearLayout(self._layout)
        self._layout.addStretch()
        self._layout.addWidget(QtWidgets.QLabel("Lyrics Show", self.widget()), 0,
            gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self._layout.addStretch()

    def _onWidgetConfigChanged(self):
        self._logger.info("On config changed, Update font to: %s", self._widgetConfig.font)
        self._loadConfig()

    def _onCurrentMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        unused(oldIndex)
        self._logger.info("On current music index changed: %d=>%d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("New music index is -1, clear lyrics")
            self._resetLayout()
        else:
            self._logger.info("New music index not -1, setup lyrics")
            self._setupLyrics()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        if self._layout.count() <= 0:
            return
        self._layout.itemAt(0).spacerItem().changeSize(0, event.size().height() // 2)
        self._layout.itemAt(self._layout.count() - 1).spacerItem().changeSize(0, event.size().height() // 2)
        self._layout.invalidate()

    def _setupLyrics(self):
        self._logger.info(">> Setting up lyrics...")
        if self._player.getCurrentMusic().isAbsent():
            self._logger.info("No music, return")
            return
        currentMusic = self._player.getCurrentMusic().orElseThrow(AssertionError)
        lyricsPath = Path(currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text(encoding="gbk")
        self._logger.info("Parsing lyrics")
        lyrics = LyricUtils.parseLyrics(lyricsText)
        self._logger.info("Lyrics count: %d", len(lyrics))
        self._lyrics = lyrics
        self._prevLyricIndex = -1
        LayoutUtils.clearLayout(self._layout)
        self._layout.addSpacing(self.height() // 2)
        for position, lyric in list(lyrics.items())[:]:
            lyricLabel = ClickableLabel(lyric, self)
            lyricLabel.setAlignment(
                gg(QtCore.Qt.AlignmentFlag.AlignCenter, Any) | QtCore.Qt.AlignmentFlag.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, position=position: self._player.setPosition(position))
            lyricLabel.setMargin(int(2 * self._app.getZoom()))
            self._layout.addWidget(lyricLabel)
        self._layout.addSpacing(self.height() // 2)
        self._logger.info("Lyrics layout has children: %d", self._layout.count())
        self.verticalScrollBar().setValue(0)
        self._logger.info("<< Lyrics set up")

    def _onTick(self):
        self._logger.debug("On tick: %f", time.time())
        if not bool(self._lyrics):
            self._logger.debug("No lyrics, return")
            return
        lyricIndex = LyricUtils.calcLyricIndexAtPosition(self._player.getPosition() + 2, list(self._lyrics.keys()))
        self._logger.debug("Lyric index: %d => %d", self._prevLyricIndex, lyricIndex)
        if lyricIndex == self._prevLyricIndex:
            self._logger.debug("Lyric index no changed, skip refresh")
            return
        self._setLyricIndex(lyricIndex)
        self._prevLyricIndex = lyricIndex

    def _setLyricIndex(self, lyricIndex):
        self._logger.debug("Set lyric index to %d", lyricIndex)
        for index in range(len(self._lyrics)):
            lyricLabel: QtWidgets.QLabel = gg(self._layout.itemAt(index + 1).widget())
            color = QtGui.QColor("#e1413c" if index == lyricIndex else "#23557d")
            palette = lyricLabel.palette()
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, color)
            lyricLabel.setPalette(palette)
            originalValue = self.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.height() // 2 + lyricLabel.height() // 2
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.verticalScrollBar(), gg(b"value"), self): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()
        self._logger.debug("Lyrics refreshed")
