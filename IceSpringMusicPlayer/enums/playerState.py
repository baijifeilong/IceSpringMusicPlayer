# Created by BaiJiFeiLong@gmail.com at 2022/1/10 21:35

from __future__ import annotations

import enum

from PySide2 import QtMultimedia


class PlayerState(enum.Enum):
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

    def isPlaying(self):
        return self == self.__class__.PLAYING

    def isPaused(self):
        return self == self.__class__.PAUSED

    def isStopped(self):
        return self == self.__class__.STOPPED

    @classmethod
    def fromQt(cls, qtState: QtMultimedia.QMediaPlayer.State) -> PlayerState:
        return {
            QtMultimedia.QMediaPlayer.State.PlayingState: cls.PLAYING,
            QtMultimedia.QMediaPlayer.State.PausedState: cls.PAUSED,
            QtMultimedia.QMediaPlayer.State.StoppedState: cls.STOPPED,
        }[qtState]
