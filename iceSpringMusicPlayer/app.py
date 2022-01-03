import logging
import math
import re
import typing
from pathlib import Path
from typing import Dict

import colorlog
import qtawesome
import taglib
import typing_extensions
from PySide2 import QtCore, QtMultimedia, QtWidgets

from iceSpringMusicPlayer.domains import Playlist, Music
from iceSpringMusicPlayer.windows import MainWindow


class App(QtWidgets.QApplication):
    playlists: typing.List[Playlist]
    player: QtMultimedia.QMediaPlayer
    currentPlaylist: typing.Optional[Playlist]
    currentPlaybackMode: typing_extensions.Literal["LOOP", "RANDOM"]
    frontPlaylist: typing.Optional[Playlist]

    @staticmethod
    def initLogging():
        consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-16s %(message)s"
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
        logging.getLogger().setLevel(logging.DEBUG)

    def __init__(self):
        super().__init__()
        self.initLogging()
        self.currentPlaybackMode = "LOOP"
        self.logger = logging.getLogger("app")
        self.lyricsLogger = logging.getLogger("lyrics")
        self.lyricsLogger.setLevel(logging.INFO)
        self.positionLogger = logging.getLogger("position")
        self.positionLogger.setLevel(logging.INFO)
        self.setApplicationName("Ice Spring Music Player")
        self.setApplicationDisplayName(self.applicationName())
        self.player = self.initPlayer()
        self.playlists = list()
        self.currentPlaylist = None
        self.frontPlaylist = None
        self.mainWindow = MainWindow(self)

    def exec_(self) -> int:
        self.mainWindow.resize(1280, 720)
        self.mainWindow.show()
        return super().exec_()

    @staticmethod
    def parseMusic(filename) -> Music:
        parts = [x.strip() for x in Path(filename).with_suffix("").name.rsplit("-", maxsplit=1)]
        artist, title = parts if len(parts) == 2 else ["Unknown"] + parts
        info = taglib.File(filename)
        music = Music()
        music.filename = filename
        music.filesize = Path(filename).stat().st_size
        music.album = info.tags.get("ALBUM", [""])[0]
        music.title = info.tags.get("TITLE", [title])[0]
        music.artist = info.tags.get("ARTIST", [artist])[0]
        music.bitrate = info.bitrate
        music.sampleRate = info.sampleRate
        music.channels = info.channels
        music.duration = info.length * 1000
        return music

    def setFrontPlaylist(self, playlist: Playlist):
        if playlist == self.frontPlaylist:
            return
        self.frontPlaylist = playlist
        self.mainWindow.playlistWidget.setCurrentIndex(self.frontPlaylistIndex)
        self.mainWindow.playlistCombo.setCurrentIndex(self.frontPlaylistIndex)

    def setFrontPlaylistAtIndex(self, playlistIndex):
        self.setFrontPlaylist(self.playlists[playlistIndex])

    def initPlayer(self):
        player = QtMultimedia.QMediaPlayer(self)
        player.setVolume(50)
        player.durationChanged.connect(self.onPlayerDurationChanged)
        player.stateChanged.connect(self.onPlayerStateChanged)
        player.volumeChanged.connect(lambda x: logging.debug("Volume changed: %d", x))
        player.positionChanged.connect(self.onPlayerPositionChanged)
        return player

    def parseLyrics(self, lyricsText: str) -> Dict[int, str]:
        lyricsLogger = self.lyricsLogger
        lyricsLogger.info("Parsing lyrics ...")
        lyricRegex = re.compile(r"^((?:\[\d+:[\d.]+])+)(.*)$")
        lyricDict: typing.Dict[int, str] = dict()
        lyricLines = [x.strip() for x in lyricsText.splitlines() if x.strip()]
        for index, line in enumerate(lyricLines):
            lyricsLogger.debug("[%02d/%02d] Lyric line: %s", index + 1, len(lyricLines), line)
            match = lyricRegex.match(line.strip())
            if not match:
                lyricsLogger.debug("Not valid lyric")
                continue
            timespans, content = [x.strip() for x in match.groups()]
            if not content:
                lyricsLogger.debug("Lyric is empty")
                continue
            for timespan in timespans.replace("[", " ").replace("]", " ").split():
                lyricsLogger.debug("Parsed lyric: %s => %s", timespan, content)
                minutes, seconds = [float(x) for x in timespan.split(":")]
                millis = int(minutes * 60000 + seconds * 1000)
                while millis in lyricDict:
                    millis += 1
                lyricDict[millis] = content
        lyricsLogger.info("Total parsed lyric items: %d", len(lyricDict))
        return dict(sorted(lyricDict.items()))

    @staticmethod
    def calcLyricIndexAtPosition(position, positions):
        for index in range(len(positions) - 1):
            if positions[index] <= position < positions[index + 1]:
                return index
        return 0 if position < positions[0] else len(positions) - 1

    @staticmethod
    def formatDelta(milliseconds):
        seconds = int(milliseconds) // 1000
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @property
    def currentPlaylistIndex(self) -> int:
        return self.playlists.index(self.currentPlaylist)

    @property
    def frontPlaylistIndex(self) -> int:
        return self.playlists.index(self.frontPlaylist)

    @property
    def currentRealDuration(self):
        return self.currentPlaylist.currentMusic.filesize * 8 // self.currentPlaylist.currentMusic.bitrate

    @property
    def currentBugRate(self):
        return 1 if self.currentPlaylist.currentMusic is None else self.player.duration() / self.currentRealDuration

    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None) if layout.itemAt(i).widget() \
                else layout.removeItem(layout.itemAt(i))

    def playPrevious(self):
        self.logger.info(">>> Play previous")
        if self.currentPlaylist is None:
            self.logger.info("Current playlist is none, return")
            return
        if not self.currentPlaylist.musics:
            self.logger.info("Current playlist is empty, return")
            return
        self.playMusic(self.currentPlaylist.playPrevious(), dontFollow=self.currentPlaybackMode == "LOOP")

    def playNext(self):
        self.logger.info(">>> Play next")
        if self.currentPlaylist is None:
            self.logger.info("Current playlist is none, return")
            return
        if not self.currentPlaylist.musics:
            self.logger.info("Current playlist is empty, return")
            return
        self.playMusic(self.currentPlaylist.playNext(), dontFollow=self.currentPlaybackMode == "LOOP")

    def playMusic(self, music: Music, dontFollow=False):
        self.logger.info(">>> Play music %s : %s", music.artist, music.title)
        oldMusicIndex = -1 if self.currentPlaylist.lastMusic is None \
            else self.currentPlaylist.musics.index(self.currentPlaylist.lastMusic)
        newMusicIndex = self.currentPlaylist.currentMusicIndex
        self.mainWindow.setWindowTitle(Path(music.filename).with_suffix("").name)
        self.mainWindow.currentPlaylistTable.selectRow(newMusicIndex)
        not dontFollow and self.mainWindow.currentPlaylistTable.scrollToRow(newMusicIndex)
        self.mainWindow.currentPlaylistModel.refreshRow(oldMusicIndex)
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        self.player.play()

    def onPlayerDurationChanged(self, duration):
        playerDurationText = self.formatDelta(self.player.duration())
        realDurationText = self.formatDelta(self.currentRealDuration)
        logging.info("Player duration changed: %d (%s / %s)", self.player.duration(), playerDurationText,
            realDurationText)
        self.mainWindow.progressSlider.setMaximum(duration)

    def onPlayerPositionChanged(self, position):
        self.positionLogger.debug("Position changed: %d", position)
        self.mainWindow.progressSlider.blockSignals(True)
        self.mainWindow.progressSlider.setValue(position)
        self.mainWindow.progressSlider.blockSignals(False)
        duration = 0 if self.player.state() == QtMultimedia.QMediaPlayer.StoppedState else self.player.duration()
        progressText = f"{self.formatDelta(position / self.currentBugRate)}" \
                       f"/{self.formatDelta(duration / self.currentBugRate)}"
        self.mainWindow.progressLabel.setText(progressText)
        suffix = Path(self.player.currentMedia().canonicalUrl().toLocalFile()).suffix
        currentMusic = self.currentPlaylist.currentMusic
        self.player.state() != QtMultimedia.QMediaPlayer.StoppedState and self.mainWindow.statusBar().showMessage(
            "{} | {} kbps | {} Hz | {} channels | {}".format(suffix[1:].upper(), currentMusic.bitrate,
                currentMusic.sampleRate, currentMusic.channels, progressText.replace("/", " / ")))
        position != 0 and self.mainWindow.refreshLyrics(math.ceil(position / self.currentBugRate))

    def onPlayerStateChanged(self, state):
        oldState = self.player.property("_state") or QtMultimedia.QMediaPlayer.StoppedState
        self.player.setProperty("_state", state)
        if oldState == QtMultimedia.QMediaPlayer.StoppedState and state == QtMultimedia.QMediaPlayer.PlayingState:
            self.mainWindow.setupLyrics()
        logging.info("Player state changed: %s [%d/%d]", state, self.player.position(), self.player.duration())
        self.mainWindow.playButton.setIcon(qtawesome.icon(["mdi.play", "mdi.pause", "mdi.play"][state]))
        currentMusic = self.currentPlaylist.currentMusic
        self.mainWindow.statusLabel.setText("{} - {}".format(currentMusic.artist,
            currentMusic.title) if state == QtMultimedia.QMediaPlayer.StoppedState else "")
        self.mainWindow.statusLabel.setText("" if state == QtMultimedia.QMediaPlayer.StoppedState else "{} - {}".
            format(currentMusic.artist, currentMusic.title))
        self.mainWindow.progressSlider.setDisabled(state == QtMultimedia.QMediaPlayer.StoppedState)
        if state == QtMultimedia.QMediaPlayer.StoppedState:
            if self.player.position() == self.player.duration():
                self.playNext()
            else:
                self.mainWindow.statusBar().showMessage("Stopped.")
                self.clearLayout(self.mainWindow.lyricsLayout)
        self.mainWindow.currentPlaylistModel.refreshRow(self.currentPlaylist.currentMusicIndex)
