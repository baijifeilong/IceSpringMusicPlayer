# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:23
import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *

Demo_Prefix = Text()
Demo_Prefix.en_US = "Prefix is "
Demo_Prefix.zh_CN = "前缀是"
Demo_Suffix = Text()
Demo_Suffix.en_US = "Suffix is "
Demo_Suffix.zh_CN = "后缀是"


def __getattr__(name):
    return globals().get(name, getattr(tt, name))
