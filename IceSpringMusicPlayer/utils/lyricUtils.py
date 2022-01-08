# Created by BaiJiFeiLong@gmail.com at 2022/1/8 23:11

from __future__ import annotations

import logging
import re
import typing

if typing.TYPE_CHECKING:
    from typing import *


class LyricUtils(object):
    @staticmethod
    def parseLyrics(lyricsText: str) -> Dict[int, str]:
        lyricsLogger = logging.getLogger("lyrics")
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
        # noinspection PyTypeChecker
        return dict(sorted(lyricDict.items()))

    @staticmethod
    def calcLyricIndexAtPosition(position, positions):
        for index in range(len(positions) - 1):
            if positions[index] <= position < positions[index + 1]:
                return index
        return 0 if position < positions[0] else len(positions) - 1
