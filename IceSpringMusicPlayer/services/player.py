# Created by BaiJiFeiLong@gmail.com at 2022/1/9 11:35

from __future__ import annotations

import hashlib
import logging
import threading
import typing

import numpy as np
import pydub
from IceSpringRealOptional.just import Just
from IceSpringRealOptional.maybe import Maybe
from IceSpringRealOptional.vector import Vector
from PySide2 import QtMultimedia, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.domains.music import Music
from IceSpringMusicPlayer.domains.playlist import Playlist
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.enums.playerState import PlayerState
from IceSpringMusicPlayer.utils.listUtils import ListUtils

if typing.TYPE_CHECKING:
    from typing import Dict


class Player(QtCore.QObject):
    frontPlaylistIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    frontPlaylistIndexAboutToBeChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    currentPlaylistIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    currentMusicIndexChanged: QtCore.SignalInstance = QtCore.Signal(int, int)
    selectedMusicIndexesChanged: QtCore.SignalInstance = QtCore.Signal(set)
    playlistInserted: QtCore.SignalInstance = QtCore.Signal(int)
    playlistsRemoved: QtCore.SignalInstance = QtCore.Signal(list)
    musicsInserted: QtCore.SignalInstance = QtCore.Signal(list, dict)
    musicsAboutToBeRemoved: QtCore.SignalInstance = QtCore.Signal(list)
    musicsRemoved: QtCore.SignalInstance = QtCore.Signal(list, dict)
    stateChanged: QtCore.SignalInstance = QtCore.Signal(PlayerState)
    durationChanged: QtCore.SignalInstance = QtCore.Signal(int)
    positionChanged: QtCore.SignalInstance = QtCore.Signal(int)
    playbackModeChanged: QtCore.SignalInstance = QtCore.Signal(PlaybackMode)
    volumeChanged: QtCore.SignalInstance = QtCore.Signal(int)

    _logger: logging.Logger
    _config: Config
    _playbackMode: PlaybackMode
    _playlists: Vector[Playlist]
    _frontPlaylistIndex: int
    _currentPlaylistIndex: int
    _currentMusicIndex: int
    _histories: Dict[int, int]
    _historyPosition: int
    _proxy: QtMultimedia.QMediaPlayer
    _playedCount: int
    _samples: np.ndarray

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self._logger = logging.getLogger("player")
        self._config = App.instance().getConfig()
        self._playbackMode = self._config.playbackMode
        self._playlists = self._config.playlists
        self._frontPlaylistIndex = self._config.frontPlaylistIndex
        self._currentPlaylistIndex = self._config.frontPlaylistIndex
        self._currentMusicIndex = -1
        self._histories = dict()
        self._historyPosition = -1
        self._playedCount = 0
        self._samples = np.array([])
        self._proxy = QtMultimedia.QMediaPlayer(self)
        self._proxy.setVolume(50)
        self._proxy.stateChanged.connect(self._onProxyStateChanged)
        self._proxy.durationChanged.connect(self._onProxyDurationChanged)
        self._proxy.positionChanged.connect(self._onProxyPositionChanged)

    def _onProxyStateChanged(self, qtState):
        self._logger.info("Proxy state changed: %s", qtState)
        state = PlayerState.fromQt(qtState)
        self.stateChanged.emit(state)
        if state.isStopped():
            self._logger.info("    Proxy stopped at position %d / %d", self._proxy.position(), self._proxy.duration())
            self._logger.info("    Player stopped at position %d / %d", self.getPosition(), self.getDuration())
            if self._proxy.position() == self._proxy.duration():
                self._logger.info("Position equals to duration, play next")
                self.playNext()

    def _onProxyDurationChanged(self, duration):
        self._logger.info("Proxy duration changed: %d", duration)
        self.durationChanged.emit(int(duration / self._getBugRateOrOne()))

    def _onProxyPositionChanged(self, position):
        self._logger.debug("Proxy position changed: %d / %d", position, self._proxy.duration())
        self.positionChanged.emit(int(position / self._getBugRateOrOne()))

    def getDuration(self) -> int:
        return int(self._proxy.duration() // self._getBugRateOrOne())

    def getPosition(self) -> int:
        return int(self._proxy.position() // self._getBugRateOrOne())

    def getState(self) -> PlayerState:
        return Just.of(self._proxy.state()).map(PlayerState.fromQt).value()

    def setPosition(self, position: int) -> None:
        qtPosition = int(position * self._getBugRateOrOne())
        self._logger.info("Setting position: %d (qt=%d)", position, qtPosition)
        self._proxy.setPosition(qtPosition)

    def setVolume(self, volume: int) -> None:
        self._proxy.setVolume(volume)
        self._logger.info("> Signal volumeChanged emitting...")
        self.volumeChanged.emit(volume)
        self._logger.info("< Signal volumeChanged emitted.")

    def getVolume(self) -> int:
        return self._proxy.volume()

    def play(self) -> None:
        self._logger.info("Play")
        if self.getPlaylists().isEmpty():
            self._logger.info("No playlist to play, return")
            return
        selectedMusicIndex = sorted(self.getSelectedMusicIndexes())[0] if len(self.getSelectedMusicIndexes()) else -1
        if self.getState().isPlaying():
            self._logger.info("Already in playing, nothing to do")
        elif self.getState().isPaused():
            self._logger.info("Player paused, resume it")
            self._proxy.play()
        elif selectedMusicIndex != -1:
            self._logger.info("Selected music index is not -1, play it")
            self.playMusicAtIndex(selectedMusicIndex)
        else:
            self._logger.info("Selected music index is -1, play next")
            self.playNext()

    def pause(self) -> None:
        self._logger.info("Pausing proxy...")
        self._proxy.pause()
        self._logger.info("Proxy paused.")

    def stop(self) -> None:
        self._logger.info("Stopping proxy...")
        self._proxy.stop()
        self._logger.info("Proxy stopped.")
        self._logger.info("Set current music index to -1")
        self.setCurrentMusicIndex(-1)

    def _resetHistories(self):
        self._logger.info("Resetting histories...")
        if self._currentMusicIndex != -1:
            self._histories = {0: self._currentMusicIndex}
            self._historyPosition = 0
        else:
            self._histories = dict()
            self._historyPosition = -1
        self._logger.info("Histories reset")

    def getPlaybackMode(self) -> PlaybackMode:
        return self._playbackMode

    def setPlaybackMode(self, mode: PlaybackMode) -> None:
        self._logger.info("Set playback mode: %s", mode)
        self._playbackMode = mode
        self._logger.info("> Signal playbackModeChanged emitting...")
        self.playbackModeChanged.emit(mode)
        self._logger.info("< Signal playbackModeChanged emitted.")

    def getPlaylists(self) -> Vector[Playlist]:
        return self._playlists

    def insertPlaylist(self) -> int:
        playlist = Playlist("Playlist {}".format(self._playlists.size() + 1), Vector(), set())
        self._logger.info("Adding playlist: %s ...", playlist.name)
        self._playlists.append(playlist)
        self._logger.info("> Signal playlistInserted emitting...")
        self.playlistInserted.emit(self._playlists.size() - 1)
        self._logger.info("< Signal playlistInserted emitted.")
        if self._frontPlaylistIndex == -1:
            self._logger.info("Front playlist index is -1, set to 0")
            self.setFrontPlaylistIndex(0)
        if self._currentPlaylistIndex == -1:
            self._logger.info("Current playlist index is -1, set to 0")
            self.setCurrentPlaylistIndex(0)
        self._logger.info("Playlist added.")
        return self._playlists.size() - 1

    def removePlaylistsAtIndexes(self, indexes: typing.List[int]) -> None:
        self._logger.info("Removing playlists at indexes: %s", indexes)
        if len(indexes) <= 0:
            self._logger.info("No playlist to remove, return")
            return
        if self.getCurrentPlaylistIndex() in indexes and self.getState().isPlaying():
            self._logger.info("Current playlist in removing list, and player is playing, stop it")
            self.stop()
        self._logger.info("Removing...")
        for index in sorted(set(indexes), reverse=True):
            del self._playlists[index]
        self._logger.info("Removed.")
        self._logger.info("> Signal playlistsRemoved emitting...")
        self.playlistsRemoved.emit(indexes)
        self._logger.info("< Signal playlistsRemoved emitted.")

    def getFrontPlaylistIndex(self) -> int:
        return self._frontPlaylistIndex

    def getFrontPlaylist(self) -> Maybe[Playlist]:
        if self._frontPlaylistIndex < 0:
            return Maybe.empty()
        return Maybe.of(self._playlists[self._frontPlaylistIndex])

    def setFrontPlaylistIndex(self, index: int) -> None:
        assert 0 <= index < len(self._playlists)
        oldFrontPlaylistIndex = self._frontPlaylistIndex
        self._logger.info("Set front playlist at index: %d => %d", oldFrontPlaylistIndex, index)
        if index == oldFrontPlaylistIndex:
            self._logger.info("No change, skip")
            return
        self._logger.info("> Signal frontPlaylistIndexToBeChanged emitting...")
        self.frontPlaylistIndexAboutToBeChanged.emit(oldFrontPlaylistIndex, index)
        self._logger.info("< Signal frontPlaylistIndexToBeChanged emitted.")
        self._frontPlaylistIndex = index
        self._logger.info("> Signal frontPlaylistIndexChanged emitting...")
        self.frontPlaylistIndexChanged.emit(oldFrontPlaylistIndex, index)
        self._logger.info("< Signal frontPlaylistIndexChanged emitted...")

    def setCurrentPlaylistIndex(self, index: int) -> None:
        assert 0 <= index < len(self._playlists)
        oldPlaylistIndex = self._currentPlaylistIndex
        self._logger.info("Set current playlist at index: %d => %d", oldPlaylistIndex, index)
        if index == oldPlaylistIndex:
            self._logger.info("No change, skip")
            return
        self._currentPlaylistIndex = index
        self._logger.info("> Signal currentPlaylistIndexChanged emitting...")
        self.currentPlaylistIndexChanged.emit(oldPlaylistIndex, index)
        self._logger.info("< Signal currentPlaylistIndexChanged emitted...")
        self._logger.info("Reset histories")
        self._resetHistories()
        self._logger.info("Histories reset")

    def getCurrentPlaylistIndex(self) -> int:
        return self._currentPlaylistIndex

    def getCurrentPlaylist(self) -> Maybe[Playlist]:
        return self._playlists.get(self._currentPlaylistIndex)

    def setSelectedMusicIndexes(self, indexes: typing.Set[int]) -> None:
        assert isinstance(indexes, set)
        self._logger.info("Set selected music indexes to %s", indexes)
        self.getFrontPlaylist().orElseThrow(AssertionError).selectedIndexes = indexes
        self._logger.info("Selected music indexes set")
        self._logger.info("> Signal selectedMusicIndexesChanged emitting...")
        self.selectedMusicIndexesChanged.emit(indexes)
        self._logger.info("< Signal selectedMusicIndexesChanged emitted.")

    def getSelectedMusicIndexes(self) -> typing.Set[int]:
        return self.getFrontPlaylist().map(lambda x: x.selectedIndexes).orElse(set())

    def setCurrentMusicIndex(self, index: int) -> None:
        oldIndex = self._currentMusicIndex
        self._logger.info("Set current music at index: %d", index)
        self._currentMusicIndex = index
        self._logger.info("> Signal currentMusicIndexChanged emitting...")
        self.currentMusicIndexChanged.emit(oldIndex, index)
        self._logger.info("< Signal currentMusicIndexChanged emitted.")

    def getCurrentMusicIndex(self) -> int:
        return self._currentMusicIndex

    def getCurrentMusic(self) -> Maybe[Music]:
        return self.getCurrentPlaylist().flatMap(lambda x: x.musics.get(self._currentMusicIndex))

    def _doPlayMusicAtIndex(self, index: int) -> None:
        self._logger.info("Do play music at index: %d", index)
        assert index >= 0
        playlist = self.getCurrentPlaylist().orElseThrow(AssertionError)
        music = playlist.musics[index]
        self._logger.info("Prepare to play music %s : %s", music.artist, music.title)
        self._logger.info("Stop current playing if exist")
        self._proxy.stop()
        self._logger.info("Current playing stopped")
        self._logger.info("Set music content: %s", music.filename)
        self._proxy.blockSignals(True)
        self._proxy.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(music.filename)))
        threading.Thread(target=self._setupSamples, args=(music.filename,)).start()
        self._proxy.blockSignals(False)
        self._logger.info("Music content set to player.")
        self._logger.info("Update current music index")
        self.setCurrentMusicIndex(index)
        self._logger.info("Now start to play music...")
        self._proxy.play()
        self._logger.info("Music play started.")
        self._playedCount += 1
        self._logger.info("Played count now: %d", self._playedCount)

    def _setupSamples(self, filename):
        self._logger.info("Setting up samples...")
        segment = pydub.AudioSegment.from_file(filename)
        samples = np.array(segment.set_channels(1).get_array_of_samples())
        samples = samples / (2 ** (segment.sample_width * 8 - 1))
        self._samples = samples
        self._logger.info("Samples set up.")

    def getSamples(self) -> np.ndarray:
        return self._samples

    def playMusicAtIndex(self, index: int) -> None:
        self._logger.info("Play music at index: %d", index)
        self._logger.info("Set current playlist to front")
        self.setCurrentPlaylistIndex(self._frontPlaylistIndex)
        self._logger.info("Update play history at relative position %d (+1)", index)
        self._updatePlayHistoryAtRelativePosition(index, 1)
        self._logger.info("Play music at index %d", index)
        self._doPlayMusicAtIndex(index)

    def playPrevious(self):
        self._logger.info("Play previous")
        if self.getState().isStopped():
            self._logger.info("Player stopped, set current playlist to front")
            self.setCurrentPlaylistIndex(self._frontPlaylistIndex)
        previousMusicIndex = self._calcPreviousMusicIndex()
        if previousMusicIndex == -1:
            self._logger.info("Calculated previous music index -1, no music to play, skip")
            return
        self._logger.info("Update play history at relative position %d (-1)", previousMusicIndex)
        self._updatePlayHistoryAtRelativePosition(previousMusicIndex, -1)
        self._logger.info("Play music at index %d", previousMusicIndex)
        self._doPlayMusicAtIndex(previousMusicIndex)

    def playNext(self):
        self._logger.info("Play next")
        if self.getState().isStopped():
            self._logger.info("Player stopped, set current playlist to front")
            self.setCurrentPlaylistIndex(self._frontPlaylistIndex)
        nextMusicIndex = self._calcNextMusicIndex()
        if nextMusicIndex == -1:
            self._logger.info("Calculated next music index is -1, no music to play, skip")
            return
        self._logger.info("Update play history at relative position %d (+1)", nextMusicIndex)
        self._updatePlayHistoryAtRelativePosition(nextMusicIndex, 1)
        self._logger.info("Play music at index %d", nextMusicIndex)
        self._doPlayMusicAtIndex(nextMusicIndex)

    def _updatePlayHistoryAtRelativePosition(self, musicIndex: int, relativePosition: int) -> None:
        self._historyPosition += relativePosition
        self._histories[self._historyPosition] = musicIndex

    def _calcNextMusicIndex(self) -> int:
        if not self.getCurrentPlaylist().isPresent():
            return -1
        playlist = self.getCurrentPlaylist().orElseThrow(AssertionError)
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
        playlist = self.getCurrentPlaylist().orElseThrow(AssertionError)
        digest = hashlib.md5(f"{direction}:{self._playedCount}".encode()).hexdigest()
        randomMusicIndex = int(digest, 16) % playlist.musics.size()
        return randomMusicIndex if randomMusicIndex != self._currentMusicIndex \
            else (randomMusicIndex + 1) % len(playlist.musics)

    def _calcPreviousMusicIndex(self) -> int:
        if not self.getCurrentPlaylist().isPresent():
            return -1
        playlist = self.getCurrentPlaylist().orElseThrow(AssertionError)
        if len(playlist.musics) <= 0:
            return -1
        loopPreviousMusicIndex = len(playlist.musics) - 1 if self._currentMusicIndex == -1 \
            else (self._currentMusicIndex - 1) % len(playlist.musics)
        historyPreviousMusicIndex = self._histories.get(self._historyPosition - 1, -1)
        randomPreviousMusicIndex = self._calcRandomMusicIndex("PREVIOUS")
        nonLoopPreviousMusicIndex = historyPreviousMusicIndex if historyPreviousMusicIndex != -1 \
            else randomPreviousMusicIndex
        return loopPreviousMusicIndex if self._playbackMode.isLoop() else nonLoopPreviousMusicIndex

    def _getBugRateOrOne(self):
        if not self.getCurrentMusic().isPresent():
            return 1
        currentMusic = self.getCurrentMusic().orElseThrow(AssertionError)
        return self._proxy.duration() / currentMusic.duration

    def insertMusics(self, musics: typing.List[Music]) -> None:
        self._logger.info("Inserting musics with count %d", len(musics))
        if self._playlists.isEmpty():
            self._logger.info("No playlist, create one")
            self.insertPlaylist()
            self._logger.info("Playlist inserted")
        playlist = self.getFrontPlaylist().orElseThrow(AssertionError)
        oldCount = playlist.musics.size()
        oldMusics = playlist.musics[:]
        indexMap = ListUtils.calcIndexMap(oldMusics, playlist.musics)
        self._logger.info("Inserting...")
        playlist.musics.extend(musics)
        self._logger.info("Inserted")
        self._logger.info("Refresh indexes")
        self._refreshMusicIndexes(indexMap)
        if self._frontPlaylistIndex != self._currentPlaylistIndex:
            self._logger.info("Insertion not in current playlist, skip resetting")
        else:
            self._logger.info("Reset histories")
            self._resetHistories()
        self._logger.info("> musicsInserted signal emitting...")
        insertedIndexes = [x + oldCount for x in range(len(musics))]
        self.musicsInserted.emit(insertedIndexes, ListUtils.calcIndexMap(oldMusics, playlist.musics))
        self._logger.info("< musicsInserted signal emitted...")

    def removeMusicsAtIndexes(self, indexes: typing.List[int]) -> None:
        self._logger.info("Removing musics at indexes: %s", indexes)
        if len(indexes) == 0:
            self._logger.info("No music to remove, skip")
            return
        playlist = self.getFrontPlaylist().orElseThrow(AssertionError)
        oldMusics = playlist.musics[:]
        indexMap = ListUtils.calcIndexMap(oldMusics, playlist.musics)
        if self._frontPlaylistIndex == self._currentPlaylistIndex and self._currentMusicIndex in indexes:
            self._logger.info("Playing music in removed list, stop it")
            self.stop()
        self._logger.info("> Signal musicsAboutToBeRemoved emitting...")
        self.musicsAboutToBeRemoved.emit(indexes)
        self._logger.info("< Signal musicsAboutToBeRemoved emitted.")
        self._logger.info("Removing...")
        for index in sorted(indexes, reverse=True):
            del playlist.musics[index]
        self._logger.info("Removed")
        self._logger.info("Refresh indexes")
        self._refreshMusicIndexes(indexMap)
        if self._frontPlaylistIndex != self._currentPlaylistIndex:
            self._logger.info("Deletion not in current playlist, skip resetting")
        else:
            self._logger.info("Reset histories")
            self._resetHistories()
        self._logger.info("> Signal musicsRemoved emitting...")
        self.musicsRemoved.emit(indexes, ListUtils.calcIndexMap(oldMusics, playlist.musics))
        self._logger.info("< Signal musicsRemoved emitted.")

    def _refreshMusicIndexes(self, indexMap: typing.Mapping[int, int]) -> None:
        self._logger.info("Refreshing indexes")
        refreshedMusicIndex = indexMap.get(self._currentMusicIndex, -1)
        self._logger.info("Refreshed music index: %d", refreshedMusicIndex)
        self._currentMusicIndex = refreshedMusicIndex
        self._logger.info("Current music index updated to %d", self._currentMusicIndex)
