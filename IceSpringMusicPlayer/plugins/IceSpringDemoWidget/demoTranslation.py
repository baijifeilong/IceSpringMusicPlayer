# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:23

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


Demo_Name = Text()
Demo_Name.en_US = "Demo Widget"
Demo_Name.zh_CN = "演示插件"
Demo_AboutMe = Text()
Demo_AboutMe.en_US = "About Demo Widget"
Demo_AboutMe.zh_CN = "关于演示插件"
Demo_Description = Text()
Demo_Description.en_US = "This is demo widget"
Demo_Description.zh_CN = "这是演示插件"
Demo_Prefix = Text()
Demo_Prefix.en_US = "Prefix is "
Demo_Prefix.zh_CN = "前缀是 "
Demo_Suffix = Text()
Demo_Suffix.en_US = "Suffix is "
Demo_Suffix.zh_CN = "后缀是 "
