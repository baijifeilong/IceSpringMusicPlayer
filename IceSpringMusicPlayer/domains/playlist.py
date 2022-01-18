# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:16:26
import dataclasses
import typing

from IceSpringRealOptional.vector import Vector

from IceSpringMusicPlayer.domains.music import Music


@dataclasses.dataclass
class Playlist(object):
    name: str
    musics: Vector[Music]
    selectedIndexes: typing.Set[int]

    def __repr__(self):
        return "<Playlist:name={},size={}>".format(self.name, len(self.musics))
