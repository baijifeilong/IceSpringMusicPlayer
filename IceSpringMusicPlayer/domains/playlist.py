# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:16:26

from IceSpringRealOptional.vector import Vector
from PySide2 import QtCore

from IceSpringMusicPlayer.domains.music import Music


class Playlist(QtCore.QObject):
    def __init__(self, name: str, musics=None):
        super().__init__()
        self.name = name
        self.musics: Vector[Music] = musics or Vector()

    def __repr__(self):
        return "<Playlist:name={},size={}>".format(self.name, len(self.musics))
