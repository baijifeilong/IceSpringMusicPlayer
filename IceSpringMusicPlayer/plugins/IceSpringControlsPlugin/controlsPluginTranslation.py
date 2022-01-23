# Created by BaiJiFeiLong@gmail.com at 2022/1/23 22:06
import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


ControlsWidget_IconSize = Text()
ControlsWidget_IconSize.en_US = "Icon Size"
ControlsWidget_IconSize.zh_CN = "图标大小"
