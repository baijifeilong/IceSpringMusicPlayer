# Created by BaiJiFeiLong@gmail.com at 2022/1/12 20:39
import logging
import typing
from typing import Any

from IceSpringPathLib import Path
from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtGui, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.controls.clickableLabel import ClickableLabel
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringMusicPlayer.utils.lyricUtils import LyricUtils
from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin


class LyricsPanel(QtWidgets.QScrollArea, ReplacerMixin):
    _app: App
    _config: Config
    _player: Player
    _layout: QtWidgets.QVBoxLayout

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        ReplacerMixin.__init__(self)
        self._logger = logging.getLogger("lyricsPanel")
        self._logger.setLevel(logging.INFO)
        self._app = App.instance()
        self._config = App.instance().getConfig()
        self._player = App.instance().getPlayer()
        self._player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setMargin(0)
        layout.setSpacing(1)
        widget.setLayout(layout)
        self.setWidget(widget)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.horizontalScrollBar().rangeChanged.connect(
            lambda *args, bar=self.horizontalScrollBar(): bar.setValue((bar.maximum() + bar.minimum()) // 2))
        self._layout = layout
        self._setupLyrics()
        self._app.configChanged.connect(self._onConfigChanged)

    def _onConfigChanged(self):
        self._logger.info("On config changed, force refresh lyrics")
        self._refreshLyrics(forceRefresh=True)

    def _onPlayerPositionChanged(self, position: int) -> None:
        self._logger.debug("Player position changed: %d", position)
        if self._player.getState().isStopped():
            self._logger.info("Player stopped, skip to refresh lyrics")
        else:
            self._logger.debug("Player not stopped, start to refresh lyrics")
            self._refreshLyrics()

    def _onCurrentMusicIndexChanged(self, oldIndex: int, newIndex: int) -> None:
        unused(oldIndex)
        self._logger.info("On current music index changed: %d=>%d", oldIndex, newIndex)
        if newIndex == -1:
            self._logger.info("New music index is -1, clear lyrics")
            LayoutUtils.clearLayout(self._layout)
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
        self.setProperty("lyrics", lyrics)
        self.setProperty("previousLyricIndex", -1)
        LayoutUtils.clearLayout(self._layout)
        self._layout.addSpacing(self.height() // 2)
        for position, lyric in list(lyrics.items())[:]:
            lyricLabel = ClickableLabel(lyric, self)
            lyricLabel.setAlignment(
                gg(QtCore.Qt.AlignmentFlag.AlignCenter, Any) | QtCore.Qt.AlignmentFlag.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, position=position: self._player.setPosition(position))
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize(self._config.lyricSize)
            lyricLabel.setFont(font)
            lyricLabel.setMargin(int(2 * self._app.getZoom()))
            self._layout.addWidget(lyricLabel)
        self._layout.addSpacing(self.height() // 2)
        self._logger.info("Lyrics layout has children: %d", self._layout.count())
        self.verticalScrollBar().setValue(0)
        self._logger.info("<< Lyrics set up")

    def _refreshLyrics(self, forceRefresh=False):
        self._logger.debug("Refresh lyrics")
        if self._player.getState().isStopped():
            self._logger.info("Player stopped, skip refresh, return")
            return
        position = self._player.getPosition()
        self._logger.debug("Refreshing lyrics at position: %d", position)
        lyrics: typing.Dict[int, str] = self.property("lyrics")
        previousLyricIndex = self.property("previousLyricIndex")
        lyricIndex = LyricUtils.calcLyricIndexAtPosition(position + 2, list(lyrics.keys()))
        self._logger.debug("Lyric index: %d => %d", previousLyricIndex, lyricIndex)
        if forceRefresh:
            self._logger.info("Force refresh")
        elif lyricIndex == previousLyricIndex:
            self._logger.debug("Lyric index no changed, skip refresh")
            return
        else:
            self._logger.debug("Lyric index changed: %d => %d, refreshing...", previousLyricIndex, lyricIndex)
        self.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyrics)):
            lyricLabel: QtWidgets.QLabel = self._layout.itemAt(index + 1).widget()
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize(self._config.lyricSize)
            lyricLabel.setFont(font)
            lyricLabel.setStyleSheet("color:rgb(225,65,60)" if index == lyricIndex else "color:rgb(35,85,125)")
            originalValue = self.verticalScrollBar().value()
            targetValue = lyricLabel.pos().y() - self.height() // 2 + lyricLabel.height() // 2
            # noinspection PyTypeChecker
            index == lyricIndex and (lambda animation=QtCore.QPropertyAnimation(
                self.verticalScrollBar(), b"value", self): [
                animation.setStartValue(originalValue),
                animation.setEndValue(targetValue),
                animation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            ])()
        self._logger.debug("Lyrics refreshed")
