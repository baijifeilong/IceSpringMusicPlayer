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
LyricsWidget_Font = Text()
LyricsWidget_Font.en_US = "Lyrics Font"
LyricsWidget_Font.zh_CN = "歌词字体"
LyricsWidget_HorizontalScrollBarPolicy = Text()
LyricsWidget_HorizontalScrollBarPolicy.en_US = "Horizontal Scroll Bar Policy"
LyricsWidget_HorizontalScrollBarPolicy.zh_CN = "水平滚动条策略"
LyricsWidget_VerticalScrollBarPolicy = Text()
LyricsWidget_VerticalScrollBarPolicy.en_US = "Vertical Scroll Bar Policy"
LyricsWidget_VerticalScrollBarPolicy.zh_CN = "垂直滚动条策略"
