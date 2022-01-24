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
        music = Music(
            filename=filename,
            filesize=Path(filename).stat().st_size,
            album=(info.tags.get("ALBUM") or [""])[0],
            title=(info.tags.get("TITLE") or [title])[0],
            artist=(info.tags.get("ARTIST") or [artist])[0],
            bitrate=info.bitrate,
            sampleRate=info.sampleRate,
            channels=info.channels,
            duration=info.length * 1000,
            format=Path(filename).suffix.strip(".").upper(),
        )
        info.close()
        return music
