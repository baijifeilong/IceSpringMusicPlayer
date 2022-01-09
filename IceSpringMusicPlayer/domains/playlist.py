# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:16:26

from __future__ import annotations

import hashlib
import random
import typing

import typing_extensions

from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.domains.music import Music


class Playlist(object):
    def __init__(self, name: str, playbackMode: PlaybackMode):
        self.name = name
        self.playbackMode = playbackMode
        self.musics: typing.List[Music] = []
        self.historyDict: typing.Dict[int, Music] = dict()
        self.historyPosition = -1
        self.lastMusic: typing.Optional[Music] = None
        self.random = random.Random(0)

    def __repr__(self):
        return "<Playlist:name={},size={}>".format(self.name, len(self.musics))

    def resetHistory(self, keepCurrent: bool) -> None:
        currentMusic = self.currentMusic
        self.historyDict.clear()
        self.historyPosition = -1
        if keepCurrent:
            self.historyDict[0] = currentMusic
            self.historyPosition = 0

    @property
    def currentMusic(self) -> typing.Optional[Music]:
        return self.historyDict.get(self.historyPosition, None)

    @property
    def currentMusicIndex(self) -> int:
        return -1 if self.currentMusic is None else self.musics.index(self.currentMusic)

    def playNext(self) -> Music:
        return self.playMusicAtRelativePosition(self.nextMusic(), 1)

    def playPrevious(self) -> Music:
        return self.playMusicAtRelativePosition(self.previousMusic(), -1)

    def playMusic(self, music: Music) -> Music:
        return self.playMusicAtRelativePosition(music, 1)

    def playMusicAtRelativePosition(self, music: Music, relativePosition) -> Music:
        self.lastMusic = self.currentMusic
        self.historyPosition += relativePosition
        self.historyDict[self.historyPosition] = music
        return music

    def nextMusic(self) -> Music:
        historyNextMusic = self.historyDict.get(self.historyPosition + 1, None)
        randomNextMusic = self.musics[self.memorizedNextRandomMusicIndex()]
        loopNextMusic = self.musics[0] if self.currentMusic is None \
            else self.musics[(self.currentMusicIndex + 1) % len(self.musics)]
        return loopNextMusic if self.playbackMode == PlaybackMode.LOOP else historyNextMusic or randomNextMusic

    def previousMusic(self) -> Music:
        historyPreviousMusic = self.historyDict.get(self.historyPosition - 1, None)
        randomPreviousMusic = self.musics[self.memorizedPreviousRandomMusicIndex()]
        loopPreviousMusic = self.musics[-1] if self.currentMusic is None \
            else self.musics[(self.currentMusicIndex - 1) % len(self.musics)]
        return loopPreviousMusic if self.playbackMode == PlaybackMode.LOOP else historyPreviousMusic or randomPreviousMusic

    def memorizedNextRandomValue(self) -> float:
        oldMemoryFlag = getattr(Playlist.memorizedNextRandomValue, "flag", "-1/-1")
        newMemoryFlag = "{}/{}".format(self.historyPosition, len(self.musics))
        if newMemoryFlag != oldMemoryFlag:
            setattr(Playlist.memorizedNextRandomValue, "flag", newMemoryFlag)
            setattr(Playlist.memorizedNextRandomValue, "value", self.random.random())
        assert hasattr(Playlist.memorizedNextRandomValue, "value")
        return getattr(Playlist.memorizedNextRandomValue, "value")

    def memorizedPreviousRandomMusicIndex(self):
        index = int(hashlib.md5(f"P/{self.memorizedNextRandomValue()}".encode()).hexdigest(), 16) % len(self.musics)
        return index if index != self.currentMusicIndex else (index - 1) % len(self.musics)

    def memorizedNextRandomMusicIndex(self):
        index = int(hashlib.md5(f"N/{self.memorizedNextRandomValue()}".encode()).hexdigest(), 16) % len(self.musics)
        return index if index != self.currentMusicIndex else (index + 1) % len(self.musics)
