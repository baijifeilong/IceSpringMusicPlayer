# Created by BaiJiFeiLong@gmail.com at 2022-01-08 09:05:45

from pathlib import Path

import taglib

from IceSpringMusicPlayer.domains.music import Music


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
