# Created by BaiJiFeiLong@gmail.com at 2022/1/9 10:41

from __future__ import annotations

import enum


class PlaybackMode(enum.Enum):
    LOOP = "LOOP"
    RANDOM = "RANDOM"

    def next(self) -> PlaybackMode:
        return dict(zip(PlaybackMode, list(PlaybackMode)[1:] + list(PlaybackMode)[:1]))[self]
