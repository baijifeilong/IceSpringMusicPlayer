# Created by BaiJiFeiLong@gmail.com at 2022/1/9 11:35

from __future__ import annotations

import hashlib
import logging
import typing

import PySide2.QtCore
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.typingUtils import unused
from IceSpringRealOptional.vector import Vector
from PySide2 import QtMultimedia, QtCore

from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.enums.playerState import PlayerState

if typing.TYPE_CHECKING:
    from typing import Dict


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
    _proxy: QtMultimedia.QMediaPlayer
    _playedCount: int

    def __init__(self, parent: PySide2.QtCore.QObject):
        super().__init__(parent)
        self._logger = logging.getLogger("player")
        self._playbackMode = PlaybackMode.LOOP
        self._playlists = Vector()
        self._currentPlaylistIndex = -1
        self._histories = dict()
        self._historyPosition = -1
        self._currentMusicIndex = -1
        self._playedCount = 0
        self._proxy = QtMultimedia.QMediaPlayer(self)
        self._proxy.setVolume(50)
        self._proxy.stateChanged.connect(self.onProxyStateChanged)
        self._proxy.durationChanged.connect(self.onProxyDurationChanged)
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
        self.durationChanged.emit(int(duration / self._fetchBugRateOrOne()))

    def onProxyPositionChanged(self, position):
        self._logger.debug("Proxy position changed: %d / %d", position, self._proxy.duration())
        self.positionChanged.emit(int(position / self._fetchBugRateOrOne()))

    def fetchDuration(self) -> int:
        return int(self._proxy.duration() // self._fetchBugRateOrOne())

    def fetchPosition(self) -> int:
        return int(self._proxy.position() // self._fetchBugRateOrOne())

    def fetchState(self) -> PlayerState:
        return Just.of(self._proxy.state()).map(PlayerState.fromQt).value()

    def setPosition(self, position: int) -> None:
        qtPosition = int(position * self._fetchBugRateOrOne())
        self._logger.info("Setting position: %d (qt=%d)", position, qtPosition)
        self._proxy.setPosition(qtPosition)

    def setVolume(self, volume: int) -> None:
        self._proxy.setVolume(volume)

    def play(self) -> None:
        self._logger.info("Playing proxy...")
        self._proxy.play()
        self._logger.info("Proxy played.")

    def pause(self) -> None:
        self._logger.info("Pausing proxy...")
        self._proxy.pause()
        self._logger.info("Proxy paused.")

    def stop(self) -> None:
        self._logger.info("Stopping proxy...")
        self._proxy.stop()
        self._logger.info("Proxy stopped.")
        self.setCurrentMusicAtIndex(-1)

    def resetHistories(self):
        self._logger.info("Resetting histories...")
        if self._currentMusicIndex != -1:
            self._histories = {0: self._currentMusicIndex}
            self._historyPosition = 0
        else:
            self._histories = dict()
            self._historyPosition = -1
        self._logger.info("Histories reset")

    def fetchCurrentPlaybackMode(self) -> PlaybackMode:
        return self._playbackMode

    def setCurrentPlaybackMode(self, mode: PlaybackMode) -> None:
        self._playbackMode = mode

    def fetchAllPlaylists(self) -> Vector[Playlist]:
        return self._playlists

    def calcPlaylistIndex(self, playlist: Playlist) -> int:
        return self._playlists.index(playlist)

    def addPlaylist(self, playlist: Playlist) -> None:
        self._logger.info("Adding playlist: %s ...", playlist.name)
        self._playlists.append(playlist)
        self._logger.info("> Signal playlistAdded emitting...")
        self.playlistAdded.emit(playlist)
        self._logger.info("< Signal playlistAdded emitted.")
        if self._currentPlaylistIndex == -1:
            self._logger.info("Current playlist index is -1, set to 0")
            self.setCurrentPlaylistAtIndex(0)
        self._logger.info("Playlist added.")

    def setCurrentPlaylistAtIndex(self, index: int) -> None:
        assert 0 <= index < len(self._playlists)
        oldPlaylistIndex = self._currentPlaylistIndex
        if index == oldPlaylistIndex:
            return
        self._logger.info("Update current playlist index: %d => %d", oldPlaylistIndex, index)
        self._currentPlaylistIndex = index
        self._logger.info("Reset histories")
        self.resetHistories()
        self._logger.info("> Signal playlistIndexChanged emitting...")
        self.playlistIndexChanged.emit(oldPlaylistIndex, index)
        self._logger.info("< Signal playlistIndexChanged emitted...")

    def fetchCurrentPlaylistIndex(self) -> int:
        return self._currentPlaylistIndex

    def fetchCurrentPlaylist(self) -> Maybe[Playlist]:
        return self._playlists.get(self._currentPlaylistIndex)

    def setCurrentMusicAtIndex(self, index: int) -> None:
        oldMusicIndex = self._currentMusicIndex
        self._logger.info("Set current music at index: %d", index)
        self._currentMusicIndex = index
        self._logger.info("> Signal musicIndexChanged emitting...")
        self.musicIndexChanged.emit(oldMusicIndex, index)
        self._logger.info("< Signal musicIndexChanged emitted.")

    def fetchCurrentMusicIndex(self) -> int:
        return self._currentMusicIndex

    def fetchCurrentMusic(self) -> Maybe[Music]:
        return self.fetchCurrentPlaylist().flatMap(lambda x: x.musics.get(self._currentMusicIndex))

    def _doPlayMusicAtIndex(self, musicIndex: int) -> None:
        self._logger.info("Do play music at index: %d", musicIndex)
        assert musicIndex >= 0
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        music = playlist.musics[musicIndex]
        self._logger.info("Prepare to play music %s : %s", music.artist, music.title)
        self._logger.info("Stop current playing if exist")
        self._proxy.stop()
        self._logger.info("Current playing stopped")
        self._logger.info("Set music content: %s", music.filename)
        self._proxy.blockSignals(True)
        self._proxy.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        self._proxy.blockSignals(False)
        self._logger.info("Music content set to player.")
        self._logger.info("Update current music index")
        self.setCurrentMusicAtIndex(musicIndex)
        self._logger.info("Now start to play music...")
        self._proxy.play()
        self._logger.info("Music play started.")
        self._playedCount += 1
        self._logger.info("Played count now: %d", self._playedCount)

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
        previousMusicIndex = self._calcPreviousMusicIndex()
        assert previousMusicIndex >= 0
        self._updatePlayHistoryAtRelativePosition(previousMusicIndex, -1)
        self._doPlayMusicAtIndex(previousMusicIndex)

    def playNext(self):
        self._logger.info("Play next")
        nextMusicIndex = self._calcNextMusicIndex()
        self._updatePlayHistoryAtRelativePosition(nextMusicIndex, 1)
        self._doPlayMusicAtIndex(nextMusicIndex)

    def playNextAtPlaylist(self, playlistIndex: int) -> None:
        self._logger.info("Play next at playlist: %d", playlistIndex)
        self.setCurrentPlaylistAtIndex(playlistIndex)
        self.playNext()

    def playPreviousAtPlaylist(self, playlistIndex: int) -> None:
        self._logger.info("Play previous at playlist: %d", playlistIndex)
        self.setCurrentPlaylistAtIndex(playlistIndex)
        self.playPrevious()

    def _updatePlayHistoryAtRelativePosition(self, musicIndex: int, relativePosition: int) -> None:
        self._historyPosition += relativePosition
        self._histories[self._historyPosition] = musicIndex

    def _calcNextMusicIndex(self) -> int:
        if not self.fetchCurrentPlaylist().isPresent():
            return -1
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        if len(playlist.musics) <= 0:
            return -1
        loopNextMusicIndex = 0 if self._currentMusicIndex == -1 \
            else (self._currentMusicIndex + 1) % len(playlist.musics)
        historyNextMusicIndex = self._histories.get(self._historyPosition + 1, -1)
        randomNextMusicIndex = self._calcRandomMusicIndex("NEXT")
        nonLoopNextMusicIndex = historyNextMusicIndex if historyNextMusicIndex != -1 else randomNextMusicIndex
        return loopNextMusicIndex if self._playbackMode.isLoop() else nonLoopNextMusicIndex

    def _calcRandomMusicIndex(self, direction: str) -> int:
        assert direction in ["PREVIOUS", "NEXT"]
        playlist = self.fetchCurrentPlaylist().orElseThrow(AssertionError)
        digest = hashlib.md5(f"{direction}:{self._playedCount}".encode()).hexdigest()
        randomMusicIndex = int(digest, 16) % playlist.musics.size()
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
        randomPreviousMusicIndex = self._calcRandomMusicIndex("PREVIOUS")
        nonLoopPreviousMusicIndex = historyPreviousMusicIndex if historyPreviousMusicIndex != -1 \
            else randomPreviousMusicIndex
        return loopPreviousMusicIndex if self._playbackMode.isLoop() else nonLoopPreviousMusicIndex

    def _fetchBugRateOrOne(self):
        if not self.fetchCurrentMusic().isPresent():
            return 1
        currentMusic = self.fetchCurrentMusic().orElseThrow(AssertionError)
        return self._proxy.duration() / currentMusic.duration

    def doBeforeRemoveMusics(self, playlistIndex: int, indexes: typing.List[int]):
        self._logger.info("Do before musics remove")
        currentPlaylistIndex = self.fetchCurrentPlaylistIndex()
        currentMusicIndex = self.fetchCurrentMusicIndex()
        if playlistIndex != currentPlaylistIndex:
            self._logger.info("Removed musics not in current playlist, skip")
            return
        if currentMusicIndex in indexes:
            self._logger.info("Playing music in removed musics, stop it")
            self.stop()

    def onMusicsInserted(self, playlistIndex: int, indexes: typing.List[int]):
        self._logger.info("On musics inserted.")
        unused(playlistIndex, indexes)
        self.resetHistories()
        self._logger.info("On musics inserted done.")

    def onMusicsRemoved(self, playlistIndex: int, indexes: typing.List[int], indexMap: typing.Dict[int, int]):
        self._logger.info("On musics removed.")
        unused(playlistIndex, indexes)
        if self._currentMusicIndex == -1:
            self._logger.info("Current music index is -1, skip refresh")
        else:
            self._logger.info("Current music index: %d, refreshing...", self._currentMusicIndex)
            refreshedMusicIndex = indexMap.get(self._currentMusicIndex)
            self._logger.info("Refreshed music index: %d", refreshedMusicIndex)
            self._currentMusicIndex = refreshedMusicIndex
            self._logger.info("Current music index updated to %d", self._currentMusicIndex)
        self.resetHistories()
        self._logger.info("On musics removed done.")
