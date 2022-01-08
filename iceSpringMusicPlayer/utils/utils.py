import logging
import typing
from pathlib import Path

import colorlog
import taglib

from iceSpringMusicPlayer.domains import Music


class LogUtils(object):
    @staticmethod
    def initLogging():
        consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-16s %(message)s"
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
        logging.getLogger().setLevel(logging.DEBUG)


class MusicUtils(object):
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


class TypeHintUtils(object):
    @staticmethod
    def gg(x) -> typing.Any:
        return x
