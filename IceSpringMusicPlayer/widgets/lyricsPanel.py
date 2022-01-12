# Created by BaiJiFeiLong@gmail.com at 2022/1/12 20:39
import logging
from typing import Any

from IceSpringPathLib import Path
from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtGui, QtCore

from IceSpringMusicPlayer.controls.clickableLabel import ClickableLabel
from IceSpringMusicPlayer.services.player import Player
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringMusicPlayer.utils.lyricUtils import LyricUtils


class LyricsPanel(QtWidgets.QScrollArea):
    _player: Player
    _layout: QtWidgets.QVBoxLayout
    _zoom: float

    def __init__(self, player: Player, parent: QtWidgets.QWidget, zoom: float = 1):
        super().__init__(parent)
        self._logger = logging.getLogger("lyricsPanel")
        self._logger.setLevel(logging.INFO)
        self._player = player
        self._player.currentMusicIndexChanged.connect(self._onCurrentMusicIndexChanged)
        self._player.positionChanged.connect(self._onPlayerPositionChanged)
        self._zoom = zoom
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

    def _onPlayerPositionChanged(self, position: int) -> None:
        self._logger.debug("Player position changed: %d", position)
        if self._player.getState().isStopped():
            self._logger.info("Player stopped, skip to refresh lyrics")
        else:
            self._logger.debug("Player not stopped, start to refresh lyrics")
            self._refreshLyrics(position + 2)

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
        self._player.setProperty("previousLyricIndex", -1)
        currentMusic = self._player.getCurrentMusic().orElseThrow(AssertionError)
        lyricsPath = Path(currentMusic.filename).with_suffix(".lrc")
        lyricsText = lyricsPath.read_text(encoding="gbk")
        self._logger.info("Parsing lyrics")
        lyricDict = LyricUtils.parseLyrics(lyricsText)
        self._logger.info("Lyrics count: %d", len(lyricDict))
        self._player.setProperty("lyricDict", lyricDict)
        LayoutUtils.clearLayout(self._layout)
        self._layout.addSpacing(self.height() // 2)
        for position, lyric in list(lyricDict.items())[:]:
            lyricLabel = ClickableLabel(lyric, self)
            lyricLabel.setAlignment(
                gg(QtCore.Qt.AlignmentFlag.AlignCenter, Any) | QtCore.Qt.AlignmentFlag.AlignVCenter)
            lyricLabel.clicked.connect(
                lambda _, position=position: self._player.setPosition(position))
            font = lyricLabel.font()
            font.setFamily("等线")
            font.setPointSize(12 * self._zoom)
            lyricLabel.setFont(font)
            lyricLabel.setMargin(int(2 * self._zoom))
            self._layout.addWidget(lyricLabel)
        self._layout.addSpacing(self.height() // 2)
        self._logger.info("Lyrics layout has children: %d", self._layout.count())
        self.verticalScrollBar().setValue(0)
        self._logger.info("<< Lyrics set up")

    def _refreshLyrics(self, position):
        self._logger.debug("Refreshing lyrics at position: %d", position)
        lyricDict = self._player.property("lyricDict")
        previousLyricIndex = self._player.property("previousLyricIndex")
        lyricIndex = LyricUtils.calcLyricIndexAtPosition(position, list(lyricDict.keys()))
        self._logger.debug("Lyric index: %d => %d", previousLyricIndex, lyricIndex)
        if lyricIndex == previousLyricIndex:
            self._logger.debug("Lyric index no changed, skip refresh")
            return
        else:
            self._logger.debug("Lyric index changed: %d => %d, refreshing...", previousLyricIndex, lyricIndex)
        self._player.setProperty("previousLyricIndex", lyricIndex)
        for index in range(len(lyricDict)):
            lyricLabel: QtWidgets.QLabel = self._layout.itemAt(index + 1).widget()
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