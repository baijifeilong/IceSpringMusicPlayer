# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:16:26

from __future__ import annotations

import typing

from IceSpringRealOptional.vector import Vector

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.domains.music import Music


class Playlist(object):
    def __init__(self, name: str):
        self.name = name
        self.musics: Vector[Music] = Vector()

    def __repr__(self):
        return "<Playlist:name={},size={}>".format(self.name, len(self.musics))
