# Created by BaiJiFeiLong@gmail.com at 2022/1/24 17:12

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


PlaylistPlugin_Name = Text()
PlaylistPlugin_Name.en_US = "Playlist Plugin"
PlaylistPlugin_Name.zh_CN = "播放列表插件"
PlaylistWidget_Name = Text()
PlaylistWidget_Name.en_US = "Playlist Widget"
PlaylistWidget_Name.zh_CN = "播放列表组件"
PlaylistManagerWidget_Name = Text()
PlaylistManagerWidget_Name.en_US = "Playlist Manager Widget"
PlaylistManagerWidget_Name.zh_CN = "播放列表管理器组件"
PlaylistWidget_RowHeight = Text()
PlaylistWidget_RowHeight.en_US = "Row Height"
PlaylistWidget_RowHeight.zh_CN = "行高"
