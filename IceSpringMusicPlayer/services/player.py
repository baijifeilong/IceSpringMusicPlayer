# Created by BaiJiFeiLong@gmail.com at 2022/1/9 11:35

from __future__ import annotations

import logging
import random
from typing import *

import PySide2.QtCore
from IceSpringRealOptional import Option
from PySide2 import QtMultimedia, QtCore

from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode


class Player(QtMultimedia.QMediaPlayer):
    playlistIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    musicIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    playlistAdded: QtCore.SignalInstance = QtCore.Signal(Playlist)

    _playbackMode: PlaybackMode
    _playlists: List[Playlist]
    _currentPlaylistIndex: int
    _histories: Dict[int, int]
    _historyPosition: int
    _currentMusicInt: int
    _previousMusicIndex: int
    _nextMusicIndex: int

    def __init__(self, parent: PySide2.QtCore.QObject):
        super().__init__(parent)
        self._logger = logging.getLogger("player")
        self._playbackMode = PlaybackMode.LOOP
        self._playlists = []
        self._currentPlaylistIndex = -1
        self._histories = dict()
        self._historyPosition = -1
        self._random = random.Random(0)
        self.setVolume(50)
        self._updatePlaybackMusicIndexes(-1)

    def resetHistories(self, keepCurrent: bool):
        if keepCurrent:
            currentMusicIndex: int = self._histories.get(self._historyPosition, -1)
            assert currentMusicIndex != -1
            self._histories = {0: currentMusicIndex}
            self._historyPosition = 0
        else:
            self._histories = dict()
            self._historyPosition = -1
        self._updatePlaybackMusicIndexes()

    def fetchCurrentPlaybackMode(self) -> PlaybackMode:
        return self._playbackMode

    def setCurrentPlaybackMode(self, mode: PlaybackMode) -> None:
        self._playbackMode = mode
        self._updatePlaybackMusicIndexes()

    def fetchAllPlaylists(self) -> List[Playlist]:
        return self._playlists[:]

    def addPlaylist(self, playlist: Playlist) -> None:
        self._playlists.append(playlist)
        self.playlistAdded.emit(playlist)
        if len(self._playlists) == 1:
            self.setCurrentPlaylistAtIndex(0)

    def setCurrentPlaylistAtIndex(self, index: int) -> None:
        assert 0 <= index < len(self._playlists)
        oldPlaylistIndex = self._currentPlaylistIndex
        if index == oldPlaylistIndex:
            return
        self._currentPlaylistIndex = index
        self.resetHistories(keepCurrent=False)
        self.playlistIndexChanged.emit(oldPlaylistIndex, index)

    def fetchCurrentPlaylistIndex(self) -> int:
        return self._currentPlaylistIndex

    def fetchCurrentPlaylist(self) -> Option[Playlist]:
        if self._currentPlaylistIndex < 0:
            return Option.empty()
        currentPlaylist = self._playlists[self._currentPlaylistIndex]
        return Option.of(currentPlaylist)

    def fetchCurrentMusicIndex(self) -> int:
        return self._currentMusicIndex

    def fetchCurrentMusic(self) -> Option[Music]:
        if not self.fetchCurrentPlaylist().isPresent():
            return Option.empty()
        if self._currentMusicIndex < 0:
            return Option.empty()
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        return Option.of(playlist.musics[self._currentMusicIndex])

    def _doPlayMusicAtIndex(self, musicIndex: int) -> None:
        assert musicIndex >= 0
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        music = playlist.musics[musicIndex]
        self._logger.info("Play music %s : %s", music.artist, music.title)
        self.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        self.play()
        oldMusicIndex = self._currentMusicIndex
        self._updatePlaybackMusicIndexes(musicIndex)
        self.musicIndexChanged.emit(oldMusicIndex, musicIndex)

    def playMusicAtIndex(self, musicIndex: int) -> None:
        self._updatePlayHistoryAtRelativePosition(musicIndex, 1)
        self._doPlayMusicAtIndex(musicIndex)

    def playPrevious(self):
        self._logger.info("Play previous")
        assert self._previousMusicIndex >= 0
        self._updatePlayHistoryAtRelativePosition(self._previousMusicIndex, 1)
        self._doPlayMusicAtIndex(self._previousMusicIndex)

    def playNext(self):
        self._logger.info("Play next")
        assert self._nextMusicIndex >= 0
        self._updatePlayHistoryAtRelativePosition(self._nextMusicIndex, 1)
        self._doPlayMusicAtIndex(self._nextMusicIndex)

    def _updatePlayHistoryAtRelativePosition(self, musicIndex: int, relativePosition: int) -> None:
        self._historyPosition += relativePosition
        self._histories[self._historyPosition] = musicIndex

    def _updatePlaybackMusicIndexes(self, currentMusicIndex: Optional[int] = None) -> None:
        if currentMusicIndex is not None:
            self._currentMusicIndex = currentMusicIndex
        self._nextMusicIndex = self._calcNextMusicIndex()
        self._previousMusicIndex = self._calcPreviousMusicIndex()

    def _calcNextMusicIndex(self) -> int:
        if not self.fetchCurrentPlaylist().isPresent():
            return -1
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        if len(playlist.musics) <= 0:
            return -1
        loopNextMusicIndex = 0 if self._currentMusicIndex == -1 \
            else (self._currentMusicIndex + 1) % len(playlist.musics)
        historyNextMusicIndex = self._histories.get(self._historyPosition + 1, -1)
        randomNextMusicIndex = self._calcRandomMusicIndex()
        nonLoopNextMusicIndex = historyNextMusicIndex if historyNextMusicIndex != -1 else randomNextMusicIndex
        return loopNextMusicIndex if self._playbackMode.isLoop() else nonLoopNextMusicIndex

    def _calcRandomMusicIndex(self) -> int:
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        randomMusicIndex = self._random.randint(0, len(playlist.musics) - 1)
        return randomMusicIndex if randomMusicIndex != self._currentMusicIndex \
            else (randomMusicIndex + 1) % len(playlist.musics)

    def _calcPreviousMusicIndex(self) -> int:
        if not self.fetchCurrentPlaylist().isPresent():
            return -1
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        if len(playlist.musics) <= 0:
            return -1
        loopPreviousMusicIndex = len(playlist.musics) - 1 if self._currentMusicIndex == -1 \
            else (self._currentMusicIndex - 1) % len(playlist.musics)
        historyPreviousMusicIndex = self._histories.get(self._historyPosition - 1, -1)
        randomPreviousMusicIndex = self._calcRandomMusicIndex()
        nonLoopPreviousMusicIndex = historyPreviousMusicIndex if historyPreviousMusicIndex != -1 \
            else randomPreviousMusicIndex
        return loopPreviousMusicIndex if self._playbackMode.isLoop() else nonLoopPreviousMusicIndex

    def fetchCurrentBugRate(self):
        if not self.fetchCurrentMusic().isPresent():
            return 1
        currentMusic = self.fetchCurrentMusic().orElseThrow(AssertionError)
        return self.duration() / currentMusic.duration
