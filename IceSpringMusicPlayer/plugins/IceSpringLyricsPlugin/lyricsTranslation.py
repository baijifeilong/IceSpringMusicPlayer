# Created by BaiJiFeiLong@gmail.com at 2022/1/24 10:25

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


LyricsPlugin_Name = Text()
LyricsPlugin_Name.en_US = "Lyrics Plugin"
LyricsPlugin_Name.zh_CN = "歌词插件"
LyricsWidget_Name = Text()
LyricsWidget_Name.en_US = "Lyrics Widget"
LyricsWidget_Name.zh_CN = "歌词组件"
