# Created by BaiJiFeiLong@gmail.com at 2022/1/9 10:41

from __future__ import annotations

import enum


class PlaybackMode(enum.Enum):
    LOOP = "LOOP"
    RANDOM = "RANDOM"
    REPEAT = "REPEAT"

    def next(self) -> PlaybackMode:
        return dict(zip(PlaybackMode, list(PlaybackMode)[1:] + list(PlaybackMode)[:1]))[self]

    def isLoop(self) -> bool:
        return self == self.__class__.LOOP

    def isRandom(self) -> bool:
        return self == self.__class__.RANDOM

    def isRepeat(self) -> bool:
        return self == self.__class__.REPEAT
