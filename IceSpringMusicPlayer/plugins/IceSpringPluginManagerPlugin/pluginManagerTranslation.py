# Created by BaiJiFeiLong@gmail.com at 2022/1/24 13:26

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


PluginManagerPlugin_Name = Text()
PluginManagerPlugin_Name.en_US = "Plugin Manager Plugin"
PluginManagerPlugin_Name.zh_CN = "插件管理器插件"
PluginManagerWidget_Name = Text()
PluginManagerWidget_Name.en_US = "Plugin Manager Widget"
PluginManagerWidget_Name.en_US = "插件管理器组件"
