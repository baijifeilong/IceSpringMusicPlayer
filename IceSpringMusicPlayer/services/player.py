# Created by BaiJiFeiLong@gmail.com at 2022/1/9 11:35

from __future__ import annotations

import logging
import random
import typing

import PySide2.QtCore
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.vector import Vector
from PySide2 import QtMultimedia, QtCore

from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.enums.playerState import PlayerState

if typing.TYPE_CHECKING:
    from typing import Dict, Optional


class Player(QtCore.QObject):
    playlistIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    musicIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    playlistAdded: QtCore.SignalInstance = QtCore.Signal(Playlist)
    stateChanged: QtCore.SignalInstance = QtCore.Signal(PlayerState)
    durationChanged: QtCore.SignalInstance = QtCore.Signal(int)
    positionChanged: QtCore.SignalInstance = QtCore.Signal(int)

    _playbackMode: PlaybackMode
    _playlists: Vector[Playlist]
    _currentPlaylistIndex: int
    _histories: Dict[int, int]
    _historyPosition: int
    _currentMusicIndex: int
    _previousMusicIndex: int
    _nextMusicIndex: int
    _proxy: QtMultimedia.QMediaPlayer

    def __init__(self, parent: PySide2.QtCore.QObject):
        super().__init__(parent)
        self._logger = logging.getLogger("player")
        self._playbackMode = PlaybackMode.LOOP
        self._playlists = Vector()
        self._currentPlaylistIndex = -1
        self._histories = dict()
        self._historyPosition = -1
        self._random = random.Random(0)
        self._previousMusicIndex = -1
        self._currentMusicIndex = -1
        self._nextMusicIndex = -1
        self._proxy = QtMultimedia.QMediaPlayer(self)
        self._proxy.setVolume(50)
        self._proxy.stateChanged.connect(self.onProxyStateChanged)
        self._proxy.positionChanged.connect(self.onProxyPositionChanged)

    def onProxyStateChanged(self, qtState):
        self._logger.info("Proxy state changed: %s", qtState)
        state = PlayerState.fromQt(qtState)
        self.stateChanged.emit(state)
        if state.isStopped():
            self._logger.info("    Proxy stopped at position %d / %d", self._proxy.position(), self._proxy.duration())
            self._logger.info("    Player stopped at position %d / %d", self.fetchPosition(), self.fetchDuration())
            if self._proxy.position() == self._proxy.duration():
                self._logger.info("Position equals to duration, play next")
                self.playNext()

    def onProxyDurationChanged(self, duration):
        self._logger.info("Proxy duration changed: %d", duration)
        self.durationChanged.emit(duration)

    def onProxyPositionChanged(self, position):
        self._logger.debug("Proxy position changed: %d / %d", position, self._proxy.duration())
        self.positionChanged.emit(position // self._fetchBugRateOrOne())

    def fetchDuration(self) -> int:
        return self._proxy.duration() // self._fetchBugRateOrOne()

    def fetchPosition(self) -> int:
        return self._proxy.position() // self._fetchBugRateOrOne()

    def fetchState(self) -> PlayerState:
        return Just.of(self._proxy.state()).map(PlayerState.fromQt).value()

    def setPosition(self, position: int) -> None:
        qtPosition = position * self._fetchBugRateOrOne()
        self._proxy.setPosition(qtPosition)

    def setVolume(self, volume: int) -> None:
        self._proxy.setVolume(volume)

    def play(self) -> None:
        self._proxy.play()

    def pause(self) -> None:
        self._proxy.pause()

    def stop(self) -> None:
        self._proxy.stop()

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

    def fetchAllPlaylists(self) -> Vector[Playlist]:
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

    def fetchCurrentPlaylist(self) -> Maybe[Playlist]:
        return self._playlists.get(self._currentPlaylistIndex)

    def fetchCurrentMusicIndex(self) -> int:
        return self._currentMusicIndex

    def fetchCurrentMusic(self) -> Maybe[Music]:
        return self.fetchCurrentPlaylist().flatMap(lambda x: x.musics.get(self._currentMusicIndex))

    def _doPlayMusicAtIndex(self, musicIndex: int) -> None:
        self._logger.info("Do play music at index: %d", musicIndex)
        assert musicIndex >= 0
        oldMusicIndex = self._currentMusicIndex
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        music = playlist.musics[musicIndex]
        self._logger.info("Prepare to play music %s : %s", music.artist, music.title)
        self._proxy.blockSignals(True)
        self._proxy.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        self._proxy.blockSignals(False)
        self._logger.info("Music content set to player.")
        self._updatePlaybackMusicIndexes(musicIndex)
        self._logger.info(">>> musicIndexChanged signal emitting...")
        self.musicIndexChanged.emit(oldMusicIndex, musicIndex)
        self._logger.info("<<< musicIndexChanged signal emitted...")
        self._logger.info("Now start to play music...")
        self._proxy.play()
        self._logger.info("Music play started.")

    def playMusicAtIndex(self, musicIndex: int) -> None:
        self._logger.info("Play music at index: %d", musicIndex)
        self._updatePlayHistoryAtRelativePosition(musicIndex, 1)
        self._doPlayMusicAtIndex(musicIndex)

    def playMusicAtPlaylistAndIndex(self, playlistIndex: int, musicIndex: int) -> None:
        self._logger.info("Play music at playlist %d and index %d", playlistIndex, musicIndex)
        self.setCurrentPlaylistAtIndex(playlistIndex)
        self.playMusicAtIndex(musicIndex)

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
        self._logger.info("Updating playback music indexes")
        self._logger.info("    Before update: %d => %d = %d",
            self._previousMusicIndex, self._currentMusicIndex, self._nextMusicIndex)
        if currentMusicIndex is not None:
            self._currentMusicIndex = currentMusicIndex
        self._nextMusicIndex = self._calcNextMusicIndex()
        self._previousMusicIndex = self._calcPreviousMusicIndex()
        self._logger.info("    After update: %d => %d = %d",
            self._previousMusicIndex, self._currentMusicIndex, self._nextMusicIndex)

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

    def _fetchBugRateOrOne(self):
        if not self.fetchCurrentMusic().isPresent():
            return 1
        currentMusic = self.fetchCurrentMusic().orElseThrow(AssertionError)
        return self._proxy.duration() / currentMusic.duration
